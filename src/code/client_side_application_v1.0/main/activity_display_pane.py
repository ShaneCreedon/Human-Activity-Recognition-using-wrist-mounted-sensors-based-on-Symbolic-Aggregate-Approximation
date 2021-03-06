import sys
import threading
from concurrent.futures import ProcessPoolExecutor

try:
    from PyQt5.Qt import *
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
    from PyQt5.QtGui import *
except:
    pass

from mqtt_protocol_module.client_connect import Client
from tkinter import filedialog
from tkinter import *
from movie_player import Movie_Player
import base64

class Activity_Display_Pane(Client, QtWidgets.QWidget):

    # Dynamic GUI variables
    activity_shift = 0
    exercise_time = 0

    # Current activity performed
    activity = "Idle"

    # Animations
    movie_screen = None
    graph_pane = None

    # Widgets
    widgets = []

    # Resources
    activities = []
    exercise_times = []
    prediction_accuracies = []

    # Define a new signal called 'trigger' that has no arguments.
    # Trigger can only signal via strings
    # Slots and Signals
    trigger = pyqtSignal(str)
    progressChanged = pyqtSignal(int)

    def __init__(self, logger):
        # Logger
        self.logger = logger

        super(Activity_Display_Pane, self).__init__(self.logger.logger_path)
        QtWidgets.QWidget.__init__(self)
        
        # Join Client topic
        self.client.on_message = self.on_message

    # Setter method - important to set and not pass in via constructor to ensure window panes align
    # how we want.
    def set_graph(self, graph_pane):
        self.graph_pane = graph_pane

    def layout_widgets(self, layout):

        # Widget Adds
        self.widget_2 = QtWidgets.QWidget()
        self.widget_2.setStyleSheet("background-color: rgb(0, 140, 180);")
        self.widget_2.setObjectName("widget_2")

        # Accuracy, Exercise Time, Activity Class
        self.label_pane_1 = QtWidgets.QLabel(self.widget_2)
        self.label_pane_2 = QtWidgets.QLabel(self.widget_2)
        self.label_pane_3 = QtWidgets.QLabel(self.widget_2)

        self.activities.append(self.label_pane_1)
        self.exercise_times.append(self.label_pane_2)
        self.prediction_accuracies.append(self.label_pane_3)

        # Put default movie here
        self.movie_screen = Movie_Player(self.widget_2)

        # Connect the trigger signal to a slot.
        self.trigger.connect(self.movie_screen.set_animation)

        # Draw activity text
        self.draw_activity_text()
        self.widgets.append(self.widget_2)
        layout.addWidget(self.widget_2)

    # Resolve connection entirely when this method is called.
    def stop_display(self):
        self.client.publish("disconnections", str(self.client_id))
        self.disconnect()
        self.prevent_publish_mechanism()
        self.graph_pane.playback_graph_active = False

    # Try connect to the broker, this class extends Client therefore, it contains the send method.
    def connect_to_broker(self):
        try:
            self.reset_publish_mechanism()
            self.broker_connection_thread = threading.Thread(target=self.send)
            self.broker_connection_thread.start()
        except RuntimeError: # Occurs if thread is dead
            self.broker_connection_thread = threading.Thread(target=self.send) # Create new instance if thread is dead
            self.broker_connection_thread.start() # Start thread

    # Spin up threads for sending the data and for initializing the graph.
    def send_activity_string_data_to_broker(self, file_path):
        try:
            self.simulate_thread = threading.Thread(target=self.convert_and_send, args=[file_path], daemon=True)
            self.simulate_thread.start()
            self.playback_graph_monitor = threading.Thread(target=self.graph_pane.start_playback_graph)
            self.playback_graph_monitor.start()
        except RuntimeError: # Occurs if thread is dead
            self.simulate_thread = threading.Thread(target=self.convert_and_send, args=[file_path], daemon=True)
            self.simulate_thread.start() # Start thread

    # emit to the controller pane what activity is being displayed.
    def display_activity_animation(self, activity):
        self.logger.info("Activity Detected {} - sending to animation player...".format(activity))

        # Emit the signal.
        self.trigger.emit(activity)

    # The callback for when a PUBLISH message is received from the server.
    # Used by MQTT Client class
    def on_message(self, client, userdata, msg):
        if (msg.topic == "prediction_receive"):
            encoded_prediction = base64.decodestring(msg.payload)
            decoded_prediction = encoded_prediction.decode("utf-8", "ignore")
            prediction = (self.replaceMultiple(decoded_prediction, ['[', ']', ',', '\''] , "")).split()
            self.exercise_time += 1
            self.activity_shift += 256

            # When message received, update UI
            self.logger.info("Client with ID {} received message: {}".format(self.client_id, decoded_prediction))
            
            # Update UI Here
            self.update_activity_user_interface(prediction)

        elif(msg.topic == "clock_reset"):
            self.logger.info("Received Clock Reset Notification...")
            self.reset_display_parameters()

    # Reset details in display window
    def reset_display_parameters(self):
        self.exercise_time = 0
        self.label_pane_2.setText("Exercise Time: {}s".format(self.exercise_time))
        self.update_activity_user_interface(("idle", 0))

    # Helper Function - Maybe move to new class (Helper)
    def replaceMultiple(self, mainString, toBeReplaces, newString):
        # Iterate over the strings to be replaced
        for elem in toBeReplaces:
            # Check if string is in the main string
            if elem in mainString:
                # Replace the string
                mainString = mainString.replace(elem, newString)
        return  mainString

    # @Function - Used for Simulating Activity Recognition implementation.
    # Update UI to adjust for results - Avatar + predictive data. 
    def update_activity_user_interface(self, prediction_message):
        if (prediction_message[0] == "walk"):
            activity_prediction = prediction_message[0]            
        elif (prediction_message[0] == "run"):
            activity_prediction = prediction_message[0]
        elif (prediction_message[0] == "lowresistancebike"):
            activity_prediction = "Slow Cycle"
        elif (prediction_message[0] == "highresistancebike"):
            activity_prediction = "Fast Cycle"
        else:
            activity_prediction = "idle"

        self.display_activity_animation(prediction_message[0])
        prediction_accuracy = (round(float(prediction_message[1]), 4)) * 100
        self.update_display_text(activity_prediction, prediction_accuracy)

        if self.graph_pane.playback_graph_active:
            progress = round(self.activity_shift / self.document_length_for_playback)
            self.progressChanged.emit(progress)

            # Update Graph
            microvolt_values = self.get_data_vector_properties()[self.exercise_time * 64:256 + self.exercise_time * 64]
            self.graph_pane.microvolts = microvolt_values

        self.graph_pane.update_graph_event.set()

    # Update display text with new details.
    def update_display_text(self, activity_prediction, prediction_accuracy):
        for activity_label in self.activities:
            activity_label.setText("Activity: {}".format(activity_prediction))

        for exercise_time_label in self.exercise_times:
            exercise_time_label.setText("Exercise Time: {}s".format(self.exercise_time))

        for accuracy_label in self.prediction_accuracies:
            accuracy_label.setText("Accuracy: {:.2f}%".format(prediction_accuracy))

    # Method called to instantiate the text in the display pane.
    def draw_activity_text(self):
        self.label_pane_1.setGeometry(QtCore.QRect(15, 10, 125, 15))
        self.label_pane_2.setGeometry(QtCore.QRect(15, 35, 125, 15))
        self.label_pane_3.setGeometry(QtCore.QRect(15, 60, 125, 15))

        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(30)

        self.label_pane_1.setFont(font)
        self.label_pane_1.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_pane_1.setStyleSheet("color: rgb(255, 255, 255)")
        self.label_pane_1.setObjectName("label")
        self.label_pane_1.setText("Activity: {}".format(self.activity))

        self.label_pane_2.setFont(font)
        self.label_pane_2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_pane_2.setStyleSheet("color: rgb(255, 255, 255)")
        self.label_pane_2.setObjectName("label")
        self.label_pane_2.setText("Exercise Time: {}s".format(self.exercise_time))

        self.label_pane_3.setFont(font)
        self.label_pane_3.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_pane_3.setStyleSheet("color: rgb(255, 255, 255)")
        self.label_pane_3.setObjectName("label")
        self.label_pane_3.setText("Accuracy: {}%".format("0.00"))

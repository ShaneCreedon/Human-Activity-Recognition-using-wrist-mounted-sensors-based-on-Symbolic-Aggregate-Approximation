import sys
import threading
import serial
import time
import numpy as np

from functools import partial
try:
    from PyQt5.Qt import *
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
    from PyQt5.QtGui import *
except:
    pass

from repeated_timer import Repeated_Timer
from tkinter import filedialog
from tkinter import *

sys.path.append('../../')

class Activity_Controller_Pane(QtWidgets.QWidget):

    # Boolean flags
    display = None
    real_time_recognition_alive = False
    recording_mode_active = False

    # Global imperatives
    image_size = 32 * 32
    recording_file_counter = 0

    # PyQt5 offers no way to utilise the same widget across multiple
    # different window panes. Therefore, I am required to store multiple
    # identical widgets in order to get the congruency that I need for my design philosophy.
    loading_widgets = []
    playback_buttons = []
    stop_play_back_buttons = []
    real_time_playback_buttons = []
    recording_buttons = []
    ppg_connection_widgets = []
    broker_connection_widgets = []
    ppg_connection_icons = []
    broker_connection_icons = []
    loaders = []
    progress_bars = []

    # PyQt5 signal object between other classes.
    graph_trigger = pyqtSignal()

    def __init__(self, logger, graph_control):
        super(Activity_Controller_Pane, self).__init__()
        QtWidgets.QWidget.__init__(self)

        # Logger Initialize
        self.logger = logger

        # Controller has access to graph
        self.graph_control = graph_control
        self.graph_trigger.connect(graph_control.reset_data_on_graph)

        # Warning Message box
        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Critical)
        self.msg.setWindowIcon(QtGui.QIcon("../assets/desktop-icon.png"))

        self.msg.setText("Arduino PPG has not been connected - An active connection stream is required for recording mode and real-time activity recognition")
        self.msg.setWindowTitle("Arduino PPG Connection Warning")
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Cancel)
        
    # Build widgets on screen for particular layout.
    def layout_widgets(self, layout):
        self.widget_3 = QtWidgets.QWidget()
        self.widget_3.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.widget_3.setObjectName("widget_controller")
        layout.addWidget(self.widget_3)
        self.build()

    # Controller has access to display
    def set_display(self, display):
        self.display = display

    @pyqtSlot(int)
    def on_progressChanged(self, value):
        for progressBar in self.progress_bars:
            progressBar.setValue(value)

    # TODO: Refactor
    def build(self):
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(8.5)

        self.progressBar = QtWidgets.QProgressBar(self.widget_3)
        self.progressBar.setGeometry(QtCore.QRect(30, 80, 180, 23))
        self.progressBar.setTextVisible(True)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setStyleSheet("background-color: rgb(0, 70, 150); color: black;")
        self.progressBar.setFont(font)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setRange(0, 100)
        self.progress_bars.append(self.progressBar)
        self.display.progressChanged.connect(self.on_progressChanged)

        # Playback/Simulate Button
        self.simulate_button = QtWidgets.QPushButton(self.widget_3)
        self.simulate_button.setGeometry(QtCore.QRect(30, 20, 180, 23))

        self.simulate_button.setFont(font)
        self.simulate_button.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.simulate_button.setAcceptDrops(False)
        self.simulate_button.setStyleSheet("background-color: rgb(0, 180, 30); color: white;")
        self.simulate_button.setIcon(QIcon(QPixmap("../assets/playback-2.png")))
        self.simulate_button.resize(180, 40)

        self.simulate_button.setObjectName("simulate_button")
        self.simulate_button.setText("Activity Recognition Playback")
        self.simulate_button.clicked.connect(self.submit_ppg_files)
        self.playback_buttons.append(self.simulate_button)

        # Cancel Simulation in-progress button
        self.cancel_simulation_button = QtWidgets.QPushButton(self.widget_3)
        self.cancel_simulation_button.setGeometry(QtCore.QRect(30, 120, 180, 23))
        
        self.cancel_simulation_button.setFont(font)
        self.cancel_simulation_button.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.cancel_simulation_button.setAcceptDrops(False)
        self.cancel_simulation_button.setStyleSheet("background-color: rgb(220, 30, 30); color: white;")
        self.cancel_simulation_button.setIcon(QIcon(QPixmap("../assets/cancel_playback.png")))
        self.cancel_simulation_button.resize(180, 40)

        self.cancel_simulation_button.setObjectName("cancel_simulation_button")
        self.cancel_simulation_button.setText("Cancel Recognition Playback")
        self.cancel_simulation_button.clicked.connect(self.cancel_button_sequence_start)

        self.stop_play_back_buttons.append(self.cancel_simulation_button)
        self.update_playback_button_state(self.stop_play_back_buttons, False, "background-color: rgb(200, 200, 200); color: black;")

        # Real Time Mode Initialize button
        self.real_time_mode_button = QtWidgets.QPushButton(self.widget_3)
        self.real_time_mode_button.setGeometry(QtCore.QRect(260, 120, 180, 23))

        self.real_time_mode_button.setFont(font)
        self.real_time_mode_button.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.real_time_mode_button.setAcceptDrops(False)
        self.real_time_mode_button.setStyleSheet("background-color: rgb(0, 128, 128); color: white;")
        self.real_time_mode_button.setIcon(QIcon(QPixmap("../assets/real_time.png")))
        self.real_time_mode_button.resize(180, 40)

        self.real_time_mode_button.setObjectName("real_time_mode_button")
        self.real_time_mode_button.setText("Real-Time Activity Playback")
        self.real_time_mode_button.clicked.connect(partial(self.engage_real_time_activity_recognition))
        self.real_time_playback_buttons.append(self.real_time_mode_button)
        
        # Recording Mode Initialize button
        self.recording_mode_button = QtWidgets.QPushButton(self.widget_3)
        self.recording_mode_button.setGeometry(QtCore.QRect(260, 20, 180, 23))

        self.recording_mode_button.setFont(font)
        self.recording_mode_button.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.recording_mode_button.setAcceptDrops(False)
        self.recording_mode_button.setStyleSheet("background-color: rgb(220, 120, 20); color: white;")
        self.recording_mode_button.setIcon(QIcon(QPixmap("../assets/real_time.png")))
        self.recording_mode_button.resize(180, 40)

        self.recording_mode_button.setObjectName("recording_mode_button")
        self.recording_mode_button.setText("Recording Mode Activate")
        self.recording_mode_button.clicked.connect(partial(self.initialize_recording_mode))
        self.recording_buttons.append(self.recording_mode_button)

        # Bottom Widgets Icons/Connections
        self.widget_5 = QtWidgets.QWidget(self.widget_3)
        self.widget_5.setGeometry(QtCore.QRect(45, 207, 171, 31))
        self.widget_5.setStyleSheet("color: black;")
        self.widget_5.setObjectName("widget_5")
        self.widget_5.setFont(font)

        self.ppg_connection = QtWidgets.QLabel(self.widget_5)
        self.ppg_connection.setGeometry(QtCore.QRect(15, 5, 161, 20))
        self.ppg_connection.setObjectName("ppg_connection")
        self.ppg_connection.setFont(font)
        self.ppg_connection_widgets.append(self.ppg_connection)

        self.widget_8 = QtWidgets.QWidget(self.widget_3)
        self.widget_8.setGeometry(QtCore.QRect(235, 207, 200, 31))
        self.widget_8.setStyleSheet("color: black;")
        self.widget_8.setObjectName("widget_5")
        self.widget_8.setFont(font)

        self.broker_connection = QtWidgets.QLabel(self.widget_8)
        self.broker_connection.setGeometry(QtCore.QRect(55, 5, 161, 20))
        self.broker_connection.setObjectName("broker_connection")
        self.broker_connection.setFont(font)
        self.broker_connection_widgets.append(self.broker_connection)

        self.create_ppg_connection_box_area(self.widget_3)
        self.create_broker_connection_box_area(self.widget_3)

        # loading icon widget container
        self.widget_7 = QtWidgets.QWidget(self.widget_3)
        self.widget_7.setGeometry(QtCore.QRect(235, 60, 100, 60))
        self.widget_7.setAutoFillBackground(False)
        self.widget_7.setObjectName("widget_7")

        self.loading = QtGui.QMovie("../assets/loader.gif")
        self.loader = QtWidgets.QLabel(self.widget_7)
        self.loader.setGeometry(QtCore.QRect(0, 0, 100, 60))
        self.loader.setAlignment(Qt.AlignCenter)
        self.loader.setMovie(self.loading)
        self.loader.setLayout(QtWidgets.QHBoxLayout())
        self.loaders.append(self.loader)

        self.loading_widgets.append(self.loading)

    def create_ppg_connection_box_area(self, widget):
         # Red dot widget container
        widget_6 = QtWidgets.QWidget(widget)
        widget_6.setGeometry(QtCore.QRect(5, 205, 50, 31))
        widget_6.setAutoFillBackground(False)
        widget_6.setObjectName("widget_6")

        # Connection Icon
        connection_icon = QtWidgets.QLabel(widget_6)
        connection_icon.setGeometry(QtCore.QRect(5, 8, 40, 40))

        connection_icon.setLayout(QtWidgets.QHBoxLayout())
        self.ppg_connection_icons.append(connection_icon)

        # Check every X seconds for Arduino connection/disconnection
        self.arduino_connection_timer = Repeated_Timer(5, self.is_arduino_connected) # it auto-starts, no need of arduino_connection_timer.start()

        # Call initially for instantaneous UI clarity
        self.is_arduino_connected()

    def create_broker_connection_box_area(self, widget):
        # Red dot widget container
        widget_6 = QtWidgets.QWidget(widget)
        widget_6.setGeometry(QtCore.QRect(235, 205, 50, 31))
        widget_6.setAutoFillBackground(False)
        widget_6.setObjectName("widget_6")

        # Connection Icon
        connection_icon = QtWidgets.QLabel(widget_6)
        connection_icon.setGeometry(QtCore.QRect(5, 8, 40, 40))

        connection_icon.setLayout(QtWidgets.QHBoxLayout())
        self.broker_connection_icons.append(connection_icon)

        # Check every X seconds for Arduino connection/disconnection
        self.broker_connection = Repeated_Timer(5, self.is_broker_connected) # it auto-starts, no need of is_broker_connected.start()

        # Call initially for instantaneous UI clarity
        self.is_broker_connected()

    # Once cancel button is clicked, ensure activity playback comes to a stop.
    # We need to stop the graph sequence as well as the display pane avatar and activity details.
    def cancel_button_sequence_start(self):
        if (self.loading != None):
            for loading_widget in self.loading_widgets:
                loading_widget.stop()            
            for loader in self.loaders:
                loader.setMovie(None)

        for i in range(len(self.loaders)):
            loading_widget = QtGui.QMovie("../assets/loader.gif")
            self.loading_widgets[i] = loading_widget
            self.loaders[i].setMovie(loading_widget)

        # emit to graph to stop
        self.graph_trigger.emit()

        # Stop display, reset parameters, and reconnect to broker.
        # Also set progress bar back to zero.
        self.display.stop_display()
        self.display.reset_display_parameters()
        self.display.connect_to_broker()
        self.on_progressChanged(0)

        self.update_playback_button_state(self.playback_buttons, True, "background-color: rgb(0, 180, 30); color: white;")
        self.update_playback_button_state(self.stop_play_back_buttons, False, "background-color: rgb(200, 200, 200); color: black;")

    # 1. Disable all other buttons
    # 2. Switch recording mode button to be red + clickable.
    # 3. Start reading arduino via graph_pane class.
    # 4. Store PPG recordings in voltages.csv but on specific location on desktop
    # - Perhaps a path like: C:/Program Files/ActivityRecognitionSoftware/recordings/voltages.csv
    # TODO: Refactor this + real-time recognition - button turning off/on should be common
    def initialize_recording_mode(self):
        self.logger.info("Initializing Recording Mode for client: {}".format(self.display.client))
        if not self.recording_mode_active:
            if self.graph_control.check_arduino_connection():
                self.recording_mode_active = True
                self.update_playback_button_state(self.playback_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
                self.update_playback_button_state(self.stop_play_back_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
                self.update_playback_button_state(self.real_time_playback_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
                self.update_playback_button_state(self.recording_buttons, True, "background-color: rgb(220, 30, 30); color: white;")
                file_path = str(QFileDialog.getExistingDirectory(self, "Select Directory")) + "/voltages_{}.csv".format(self.recording_file_counter)
                self.graph_control.stop_graph_temporarily()

                self.recording_thread = threading.Thread(target=self.graph_control.read_from_ppg, args=[file_path])
                self.recording_thread.start()
            else:
                # Pop up dialog box that the Arduino PPG is not connected
                choice = self.msg.exec_()
                if choice == QtWidgets.QMessageBox.Retry:
                    # Try to engage real time activity recognition again.
                    self.initialize_recording_mode()
        else:
            self.recording_mode_active = False
            self.graph_control.stop_graph_temporarily()
            self.graph_trigger.emit()
            self.update_playback_button_state(self.playback_buttons, True, "background-color: rgb(0, 180, 30); color: white;")
            self.update_playback_button_state(self.stop_play_back_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
            self.update_playback_button_state(self.real_time_playback_buttons, True, "background-color: rgb(0, 128, 128); color: white;")
            self.update_playback_button_state(self.recording_buttons, True, "background-color: rgb(220, 120, 20); color: white;")

    def engage_real_time_activity_recognition(self, debug_mode_active=False):
        if self.graph_control.check_arduino_connection() or debug_mode_active:
            # If PPG is connected via Arduino port on COM3
            # Change button state colour to be 'active' as opposed to the blue inactive state
            # Disable all other buttons 
            # Start real-time activity recognition
            if not self.real_time_recognition_alive:
                self.real_time_recognition_alive = True
                self.update_playback_button_state(self.playback_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
                self.update_playback_button_state(self.stop_play_back_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
                self.update_playback_button_state(self.real_time_playback_buttons, True, "background-color: rgb(220, 30, 30); color: white;")

                self.real_time_recognition_thread = threading.Thread(target=self.read_from_ppg_with_double_buffer)
                self.real_time_recognition_thread.start()
            else:
                self.real_time_recognition_alive = False
                self.display.stop_real_time_connection()
        else:
            # Pop up dialog box that the Arduino PPG is not connected
            choice = self.msg.exec_()
            if choice == QtWidgets.QMessageBox.Retry:
                # Try to engage real time activity recognition again.
                self.engage_real_time_activity_recognition()

    # Step #1: Read from active PPG device
    # Step #2: Send each individual microvolt sample over in a stream, perhaps some arbitrary amount per second, IE 256 samples/s
    # - MQTT will require a unique topic for real-time recognition as the processing is different in texture.
    # Step #3: Store data in an unbounded buffer server-side (double buffering?)
    # step #4: Once buffer contains enough data to build an image (1024 - 3x32), build the image and then predict
    # After each image creation, remove previous image and remove 1 character from the buffer such that we shift along it. (Similar to the window sliding idea)
    # Step #5: Return prediction to client, client should automatically update if published to correct topic.
    # Note: Some of the parameters will need to be changed IE The exercise time
    def read_from_ppg_with_double_buffer(self):
        try:
            image_properties = []
            while(self.real_time_recognition_alive):
                if len(image_properties) == self.image_size:
                    # TODO: No need to np.array() here as its done in next function in call-loop
                    data_read_from_ppg = np.array(image_properties)
                    # Convert data to Pandas series object
                    self.display.convert_and_send_real_time(data_read_from_ppg)

                    # TODO: Find ideal image property size here
                    image_properties = image_properties[256:]
                else:
                    image_properties.append(self.graph_control.get_microvolt_reading())                
                time.sleep(0.001)
        finally:
            # Stop Real Time Recognition
            self.real_time_recognition_alive = False
            # Update button states
            self.update_playback_button_state(self.playback_buttons, True, "background-color: rgb(0, 180, 30); color: white;")
            self.update_playback_button_state(self.stop_play_back_buttons, False, "background-color: rgb(200, 200, 200); color: black;")
            self.update_playback_button_state(self.real_time_playback_buttons, True, "background-color: rgb(0, 128, 128); color: white;")
            # log to file/console
            self.logger.warning("Real-Time Activity Recognition Function Active Finished...")
            # Reset Display
            self.display.reset_display_parameters()
            
    def resolve(self):
        if (self.arduino_connection_timer.is_running):
            self.arduino_connection_timer.stop()
        self.real_time_recognition_alive = False

    # Update indicator widgets based on broker and arduino connection
    def is_arduino_connected(self):
        if self.graph_control.check_arduino_connection():
            for connection_icon in self.ppg_connection_icons:
                green_symbol = QtGui.QMovie("../assets/ppg_connected.gif")
                connection_icon.setMovie(green_symbol)
                connection_icon.setAlignment(Qt.AlignRight)
                green_symbol.start()
            for connection_widget in self.ppg_connection_widgets:
                connection_widget.setText("Arduino PPG Connected")
        else: 
            for connection_icon in self.ppg_connection_icons:
                red_cross = QtGui.QMovie("../assets/red-cross.gif")
                connection_icon.setMovie(red_cross)
                connection_icon.setAlignment(Qt.AlignRight)
                red_cross.start()
            for connection_widget in self.ppg_connection_widgets:
                connection_widget.setText("Arduino PPG Not Connected")

    # Update indicator widgets based on broker and arduino connection
    def is_broker_connected(self):
        if self.display.is_connected_to_broker():
            for connection_icon in self.broker_connection_icons:
                green_symbol = QtGui.QMovie("../assets/ppg_connected.gif")
                connection_icon.setMovie(green_symbol)
                connection_icon.setAlignment(Qt.AlignRight)
                green_symbol.start()
            for connection_widget in self.broker_connection_widgets:
                connection_widget.setText("Broker Connection Active")
        else: 
            for connection_icon in self.broker_connection_icons:
                red_cross = QtGui.QMovie("../assets/red-cross.gif")
                connection_icon.setMovie(red_cross)
                connection_icon.setAlignment(Qt.AlignRight)
                red_cross.start()
            for connection_widget in self.broker_connection_widgets:
                connection_widget.setText("Broker Connection Inactive")

    # IMPORTANT: This method is called in a thread whenever the activity playback function is pressed.
    # If a successful csv file is submitted, we can send perform SAX on the time series then subsequently
    # encode the data with Base64 and send the activity string across the MQTT network to our processing server.
    def submit_ppg_files(self):
        try:
            root = Tk().withdraw()
            file_path = filedialog.askopenfilename(initialdir = "/",title = "Select file", filetypes = (("timestamp & PPG recordings CSV","*.csv"), ("all files","*.*")))
            if (file_path != ""):
                self.logger.debug("Simulating Activity Recognition for file: {" + str(file_path) + "}")
                self.display.send_activity_string_data_to_broker(file_path)               

                if (len(self.loaders) > 0):
                    for loading_widget in self.loading_widgets:
                        loading_widget.start()
                    self.update_playback_button_state(self.playback_buttons, False,"background-color: rgb(200, 200, 200); color: black;")
                    self.update_playback_button_state(self.stop_play_back_buttons, True, "background-color: rgb(220, 30, 30); color: white;")

        except Exception as error:
            self.logger.error("Error: " + repr(error))

    # Set all buttons state, relative to the current state they're in.
    def update_playback_button_state(self, buttons, enabled=True, stylesheet="background-color: rgb(0, 180, 30); color: white"):
        for button in buttons:
            button.setEnabled(enabled) 
            button.setStyleSheet(stylesheet)
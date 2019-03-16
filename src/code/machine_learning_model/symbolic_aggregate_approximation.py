import pandas as pd
from sax_module.time_series_to_string_via_sax import Time_series_to_string_via_sax

class SymbolicAggregateApproximation:

    exercise_path = "../../resources/exercise-datasets/"

    def __init__(self):
        self.sax_obj = Time_series_to_string_via_sax()

    def generate_walk(self, file_no):
        walk_path = self.exercise_path + "Walk0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(walk_path, 20, 1)
        return exercise_results

    def generate_run(self, file_no):
        run_path = self.exercise_path + "Run0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(run_path, 20, 1)
        return exercise_results

    def generate_low_bike(self, file_no):
        low_bike_path = self.exercise_path + "LowResistanceBike0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(low_bike_path, 20, 1)
        return exercise_results

    def generate_high_bike(self, file_no):
        high_bike_path = self.exercise_path + "HighResistanceBike0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(high_bike_path, 20, 1)
        return exercise_results

def main():
    sax_obj = SymbolicAggregateApproximation()
    print_demo(sax_obj, 1)

def print_demo(sax_obj, file_no):

    try:
        print(" -- Walk Results --")
        print(sax_obj.generate_walk(file_no))

        print(" -- Run Results --")
        print(sax_obj.generate_run(file_no))

        print(" -- Low Resistance Bike Results --")
        print(sax_obj.generate_low_bike(file_no))

        print(" -- High Resistance Bike Results --")
        print(sax_obj.generate_high_bike(file_no))

    except FileNotFoundError:
        print("File with ID: 0" + str(file_no) + " Not Found")

if __name__ == "__main__":
    main()
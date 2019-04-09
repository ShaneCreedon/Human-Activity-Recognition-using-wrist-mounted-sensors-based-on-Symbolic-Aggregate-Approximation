import sys

sys.path.append("../../")
from logger_module.Logger import Logger

from sax_module.time_series_to_string_via_sax import Time_series_to_string_via_sax

class SymbolicAggregateApproximation:

    training_exercise_path = "../../resources/exercise-datasets/"
    letter_size = 20

    def __init__(self, logger=True):
        if (logger):
            self.logger = Logger("../", "logs/Symbolic")
            self.logger.info("Symbolic Aggregate Approximation Object Created...")
        self.sax_obj = Time_series_to_string_via_sax()

    # General Abstract Generate method; unsure of the activity; useful for server.
    def generate(self, filename):
        return self.sax_obj.generate_string_from_time_series(filename, self.letter_size, 1)

    def generate_walk(self, file_no):
        walk_path = self.training_exercise_path + "Walk0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(walk_path, self.letter_size, 1)
        return exercise_results

    def generate_run(self, file_no):
        run_path = self.training_exercise_path + "Run0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(run_path, self.letter_size, 1)
        return exercise_results

    def generate_low_bike(self, file_no):
        low_bike_path = self.training_exercise_path + "LowResistanceBike0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(low_bike_path, self.letter_size, 1)
        return exercise_results

    def generate_high_bike(self, file_no):
        high_bike_path = self.training_exercise_path + "HighResistanceBike0" + str(file_no) + ".csv"
        exercise_results = self.sax_obj.generate_string_from_time_series(high_bike_path, self.letter_size, 1)
        return exercise_results

def main():
    sax_obj = SymbolicAggregateApproximation(True)
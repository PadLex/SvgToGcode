"""
Do you want to run a test on a specific example? If so, this is the script for you.
Modify as you please, just remember not to commit your changes.
"""

import os
import importlib

from testing.comparison_tests import compare_files


if __name__ == "__main__":
    example = "ellipse"
    test_name = "basic_usage"
    test_type = ["comparison", "other"][0]

    if test_type == "comparison":
        run_test = importlib.import_module(f"testing.comparison_tests.{test_name}.test").run_test

        input_path = os.path.join("examples", f"{example}.svg")
        correct_path = os.path.join("comparison_tests", test_name, f"{example}.gcode")
        output_path = os.path.join("comparison_tests", test_name, f"{example}-unverified.gcode")

        with open(input_path, 'rb') as svg_file:
            svg_string = svg_file.read()

        with open(output_path, 'w') as gcode_file:
            gcode_file.write(run_test(svg_string))

        print(f"Saved output to {output_path}")

        if os.path.isfile(correct_path):
            if compare_files(correct_path, output_path):
                print("Success, outputs are within operational tolerance")
            else:
                print("Ups, the outputs are different")

    if test_type == "other":
        run_test = importlib.import_module(f"testing.other_tests.{test_name}.test").run_test

        debug_file_name = os.path.join("other_tests", "linear_approximation", f"{example}.svg")
        print(run_test(example, debug_file_name))

# Do you want to run a test on a specific example? If so, this is the script for you.
# Modify as you please, just remember not to commit your changes.

from testing.other_tests.linear_approximation.test import run_test


if __name__ == "__main__":
    svg_file_name = f"examples\\cubic_bazier.svg"
    test_type = ["comparison", "other"][1]

    if test_type == "comparison":
        with open(svg_file_name, 'rb') as svg_file:
            svg_string = svg_file.read()

        print(run_test(svg_string))

    if test_type == "other":
        debug_file_name = f"other_tests\\linear_approximation\\cubic_bazier.svg"
        print(run_test(svg_file_name, debug_file_name))

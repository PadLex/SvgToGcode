import os
import importlib

from svg_to_gcode import TOLERANCES

verbose = True


def run_tests(test_name, examples):

    conflicts = []
    missing_results = []
    for svg_name in examples:
        svg_file_name = os.path.join(os.getcwd(), "examples", f"{svg_name}.svg")
        correct_file_name = os.path.join(os.getcwd(), "comparison_tests", test_name, f"{svg_name}.gcode")
        output_file_name = os.path.join(os.getcwd(), "comparison_tests", test_name, f"{svg_name}-unverified.gcode")

        run_test = importlib.import_module(f"testing.comparison_tests.{test_name}.test").run_test
        with open(svg_file_name, 'rb') as svg_file:
            output = run_test(svg_file.read())

        with open(output_file_name, 'w') as gcode_file:
            gcode_file.write(output)

        if os.path.isfile(correct_file_name):
            identical = compare_files(correct_file_name, output_file_name)
            if identical:
                os.remove(output_file_name)
            else:
                conflicts.append(svg_name)
        else:
            missing_results.append(svg_name)

    return conflicts, missing_results


# Compare two gcode like files. Return True if the two are identical or if they are within operational tolerances.
def compare_files(correct_file_name, output_file_name):
    with open(correct_file_name, 'r') as correct_file:
        correct_code = correct_file.readlines()

    with open(output_file_name, 'r') as output_file:
        output_code = output_file.readlines()

    # If there are a different number of lines then don't bother checking
    if len(correct_code) != len(output_code):
        debug(correct_file_name, output_file_name, "Have different lengths")
        return False

    # Find differing lines
    for i in range(len(correct_code)):
        correct_line = correct_code[i]
        output_line = output_code[i]

        if correct_line == output_line:
            continue

        # Since the lines are different, check if the values are within operational tolerance
        correct_fragments = correct_line.replace(';', '').split()
        output_fragments = output_line.replace(';', '').split()

        if len(correct_fragments) != len(output_fragments):
            debug(correct_line, output_line, "Have different lengths")
            return False

        for j in range(len(correct_fragments)):
            correct_fragment = correct_fragments[j].strip()
            output_fragment = output_fragments[j].strip()

            if correct_fragment == output_fragment:
                continue

            try:
                # If two values are not within operational tolerances they need to be manually compared
                if abs(float(correct_fragment) - float(output_fragment)) > TOLERANCES["operation"]:
                    debug(correct_line, output_line, "Are not within operational tolerance")
                    return False
            except ValueError:
                # If two commands are different they need to be manually compared
                debug(correct_line, output_line, "Have different commands:", correct_fragment, output_fragment)
                return False

    return True


def debug(*args):
    if verbose:
        print(*args)

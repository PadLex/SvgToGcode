import os
import importlib
import filecmp


def run_tests(test_name, examples):

    conflicts = []
    missing_results = []
    for svg_name in examples:
        svg_file_name = f"{os.getcwd()}\\examples\\{svg_name}.svg"
        correct_file_name = f"{os.getcwd()}\\comparison_tests\\{test_name}\\{svg_name}.gcode"
        output_file_name = f"{os.getcwd()}\\comparison_tests\\{test_name}\\{svg_name}-unverified.gcode"

        run_test = importlib.import_module(f"testing.comparison_tests.{test_name}.test").run_test
        with open(svg_file_name, 'rb') as svg_file:
            output = run_test(svg_file.read())

        with open(output_file_name, 'w') as gcode_file:
            gcode_file.write(output)

        if os.path.isfile(correct_file_name):
            identical = filecmp.cmp(correct_file_name, output_file_name)
            if identical:
                os.remove(output_file_name)
            else:
                conflicts.append(svg_name)
        else:
            missing_results.append(svg_name)

    return conflicts, missing_results

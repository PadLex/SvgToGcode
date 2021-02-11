import os
import importlib


def run_tests(test_name, examples):

    conflicts = []
    for svg_name in examples:
        svg_file_name = os.path.join("examples", f"{svg_name}.svg")
        debug_file_name = os.path.join("other_tests", test_name, f"{svg_name}.svg")

        run_test = importlib.import_module(f"testing.other_tests.{test_name}.test").run_test
        success = run_test(svg_file_name, debug_file_name)

        if not success:
            conflicts.append(svg_name)

    return conflicts

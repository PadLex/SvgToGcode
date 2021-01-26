import os
from testing import comparison_tests, other_tests


if __name__ == "__main__":
    svg_dir = f"{os.getcwd()}\\examples\\"
    svg_names = {name[:-4] for name in os.listdir(svg_dir) if name[0] != '_'}

    comparison_dir = f"{os.getcwd()}\\comparison_tests\\"
    comparison_names = {name for name in os.listdir(comparison_dir) if os.path.isdir(comparison_dir + name)
                        and name[0] != '_'}

    other_dir = f"{os.getcwd()}\\other_tests\\"
    other_names = {name for name in os.listdir(other_dir) if os.path.isdir(other_dir + name) and name[0] != '_'}

    print("\nExecuting comparison tests...")
    for test_name in comparison_names:

        conflicts, missing_results = comparison_tests.run_tests(test_name, svg_names)

        comparisons = len(svg_names) - len(missing_results)

        if len(conflicts) > 0:
            print(
                f"{test_name} failed with the following examples as input {len(conflicts)}/{comparisons}: {conflicts}")
            print("Resolve conflicting outputs by manual revision.")
            print("If you want to update a test or if the two gcode files are equivalent, delete the original "
                  "test_name.gcode and rename test_name_unverified.gcode to test_name.gcode.")
            print("If the -unverified output is incorrect, fix the bug and the next automated review will override or "
                  "delete -unverified outputs\n")
        else:
            print(f"{test_name} passed {comparisons} out of {len(svg_names)} examples.")

        if len(missing_results):
            print(f"{test_name} is missing the following verified test results:")
            print(f"The following examples are missing a verified result for the {test_name} test: {missing_results}")
            print(f"After verifying that the example-unverified.gcode is correct, rename it to example.gcode.\n")

    print("\nExecuting other tests...")
    for test_name in other_names:
        conflicts = other_tests.run_tests(test_name, svg_names)

        if len(conflicts) > 0:
            print(f"{test_name} failed with the following examples as input {len(conflicts)}/{len(svg_names)}:"
                  f" {conflicts}\n")
        else:
            print(f"{test_name} passed with all {len(svg_names)} examples.")

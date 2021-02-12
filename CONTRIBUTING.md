# Contribution Guidelines

Thank you for taking an interest in contributing, any help is always appreciated!

If you would like to request a feature, you can create a new issue with the "feature request" tag, detailing why 
the feature is worth adding and suggesting a possible implementation. That being said, directly creating a pull request 
for small features is totally okay. Just make sure to follow 


* [Best Coding Practices](#Best-Coding-Practices)
* [Testing](#Testing)
    * [Running tests](#Running-tests)
    * [Creating tests](#Creating-tests)
* [To-Do List](#To-Do-List)


## Best Coding Practices
Try to conform to PEP styleguides. When in doubt, remember to **prioritise code readability**, even if it leads to less 
efficient code.

If you notice that a snippet of code violates PEP guidelines or is otherwise unclear, I would invite you to create a 
quick pull request.

Here's a quick list of common pit-falls:
* **Variable names should be self descriptive.** If you use a contraction, make sure it's meaning is clear. 
`max_distance` is self descriptive and clearly means `maximum_distance`. `der` is not a good short-hand for `derivative`.

* **Shorter code is not better code.** One-liners are awesome, just make sure you are using them to increase 
readability, the length of your code does not matter.

* **Remember to write docstrings** for classes and methods. [PEP 257](https://www.python.org/dev/peps/pep-0257/)

* **Raise your own exception before something goes wrong.** Sometimes it's good to check if you're method received valid
 arguments so that you can raise a descriptive exception before, say, dividing by zero.

## Testing
### Running tests
Before creating a pull request, make sure you run the `automated_testing.py` script. If all tests pass you're good 
to go.

Each test is a script which is run with different input svg files (internally referred to as examples). 
Any test may fail for one or more examples. The automated_testing script will tell you exactly which examples led to a failure.

`comparison_tests` are integrated tests. They simulate different ways this library can be used. When you run a comparison test, the output 
for each example is compared to the expected output of each test-example pair. Meaning that if it fails, you either broke
something, or you intentionally want to change the expected gcode output. You can find the expected 
output under `testing\comparison_tests\{test_name}\{example_name}.gcode`. The output from the last test (if it failed) can 
be found in the same directory as `{example_name}-unverified.gcode`. If you are trying to change the expected output,
you can rename the unverified file and commit your changes. Just remember to use a gcode emulator to insure the output
is valid.

`other_tests` simply return a boolean to confirm whether or not the test was successful.

There aren't any `unit tests` yet.

### Creating Tests
Creating a test is actually quite simple. Just copy an existing test and modify `test.py`'s `run_test` method.

If you're creating a `comparison_test`, `run_test` will receive an example in the form of an svg byte-string and must 
return a .gcode output. Remember to rename `{example_name}-unverified.gcode` to establish an expected output for each 
example.

`other_tests` are a little more flexible. `run_test` receives two filepaths, the first is the location of the example, 
the second is the location where the test can optionally save debug files. Return `True` or `False` depending on whether
or not the test succeeded.

## To-Do List
There are a number of ToDo markers left around the code base. Feel free to resolve any of them.

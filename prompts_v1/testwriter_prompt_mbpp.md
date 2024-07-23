Task: Create comprehensive test cases for the given described function.
These test cases should encompass scenarios to ensure the code's
robustness, reliability, and scalability. 
You should return only the test cases, not the function implementation.
Write exactly 5 test cases for each function. A signature for the function is specified.
Pay special attention to edge cases as they often reveal hidden bugs.

Format: Use this format for each test case:
```python
assert function_name(input) == expected_output, "Test case description"
```

Example of input:
Check if any two numbers in a list are closer than a given threshold.
Signature of the function: has_close_elements(list, threshold).


Your output:
```python
assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False, "Test case 1: no close elements"
assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True, "Test case 2: close elements"
assert has_close_elements([], 0.1) == False, "Test case 3: edge case with an empty list"
assert has_close_elements([1.0, 1.0000001], 0.0000002) == True, "Test case 4: very close elements"
assert has_close_elements(list(range(100000)), 0.5) == False, "Test case 5: large scale case with sequential integers"

```

Now create test cases for this problem:
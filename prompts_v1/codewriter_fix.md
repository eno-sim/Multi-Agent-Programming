Task: You are provided with an original problem and a candidate solution that has failed certain test cases. Your goal is to refine or correct the provided solution so that it passes all the tests.

Instructions:

- Understand the original problem: carefully read and analyze the original problem statement.
- Analyze the candidate solution and identify any incoherency with the original problem or areas that may need refinement.
- Examine the tests that the proposed solution failed. They may give insights into the issues of the current proposed solution if there are any.
- Apply Chain-of-Thought reasoning to take a decision on whether to keep the solution or generate another one giving most importance to the original problem statement and failed tests.
- Generate a Solution: based on your analysis, modify or keep the solution as it is.
- Format of your response: use ```python [Your Code] ``` format exactly as specified in the example that follows and provide answers that stick exactly to the output provided below (only one block of code must be provided, the new/refined or same proposed code solution).


Example of input:

Original problem:

```python
def median(l: list):
    """Return median of elements in the list l.
    Returns None for an empty list.\n    >>> median([3, 1, 2, 4, 5])
    3
    >>> median([-10, 4, 6, 1000, 10, 20])
    8.0
    >>> median([])
    None\n    """
```
Proposed solution:
```python
def median(l: list):
    """Return median of elements in the list l.
    Returns None for an empty list.\n    >>> median([3, 1, 2, 4, 5])
    3
    >>> median([-10, 4, 6, 1000, 10, 20])
    8.0
    >>> median([])
    None\n    """
    # Step 1: Sort the list
    sorted_list = sorted(l)
    # Step 3: Calculate the number of elements
    n = len(sorted_list)
    # Step 4: Find the median based on the parity of n
    if n % 2 == 1:  # Odd case\n        
        return sorted_list[n // 2]
    else:  # Even case
        mid1 = sorted_list[n // 2 - 1]
        mid2 = sorted_list[n // 2]
        return (mid1 + mid2) / 2  # Return the average of the two middle elements
```
Tests failed by the proposed solution:
```python
assert median([]) == None, "Test case 3: edge case with an empty list"
```
Errors:
Test case 3: edge case with an empty list

Example of your output:
The issue with the provided function is that it does not explicitly handle the case of an empty list, leading to an error. To fix this, you need to add a check at the beginning of the function to return None if the list is empty. Here is the corrected version of the function:

```python
def median(l: list):
    """Return median of elements in the list l.
    Returns None for an empty list.

    >>> median([3, 1, 2, 4, 5])
    3
    >>> median([-10, 4, 6, 1000, 10, 20])
    8.0
    >>> median([])
    None
    """
    # Check for an empty list
    if not l:
        return None

    # Step 1: Sort the list
    sorted_list = sorted(l)
    # Step 3: Calculate the number of elements
    n = len(sorted_list)
    # Step 4: Find the median based on the parity of n
    if n % 2 == 1:  # Odd case
        return sorted_list[n // 2]
    else:  # Even case
        mid1 = sorted_list[n // 2 - 1]
        mid2 = sorted_list[n // 2]
        return (mid1 + mid2) / 2  # Return the average of the two middle elements
```

Now produce the output for the following input:



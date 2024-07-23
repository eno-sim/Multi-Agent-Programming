A candidate code solution for a problem is provided and it is followed by tests it failed and the relative errors. Modify or refine the code to make it pass the tests using Chain-of-Thought. Use ```python [Your Code] ``` format. 
IMPORTANT: 
- do not write other test cases but just correct the code solution;
- if you find out the failed tests are wrong and the code correct you have to regenerate the code as it is and modify nothing.

Example of input:
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
ERRORS:
assert median([]) == None, "Test case 3: edge case with an empty list"
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

Example of input 2:

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
assert median([2, 5, -10, 3, -2]) == 0, "Test case 2: edge case with odd length"
assert median([1, 5, 0.5, 3]) == 0.75, "Test case 4: basic case with even length "
ERRORS:
Test case 2: edge case with odd length
Test case 4: basic case with even length



Example of your output 2:
The provided solution for the specified is correct, therefore no modification is to be made. Therefore the solution remains the same:
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
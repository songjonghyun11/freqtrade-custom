def find_first_true(arr):
    """Return the index of the first True value in a list, or -1 if none found."""
    for i, x in enumerate(arr):
        if x:
            return i
    return -1

def find_first_max(arr):
    """Return the index of the first maximum value in a list, or -1 if empty."""
    if not arr:
        return -1
    max_val = max(arr)
    for i, x in enumerate(arr):
        if x == max_val:
            return i
    return -1

def find_first_min(arr):
    """Return the index of the first minimum value in a list, or -1 if empty."""
    if not arr:
        return -1
    min_val = min(arr)
    for i, x in enumerate(arr):
        if x == min_val:
            return i
    return -1


def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    Returns the index of target if found, else -1.
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Example usage
sorted_array = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
result = binary_search(sorted_array, 7)
print(f"Found 7 at index: {result}")  # Output: Found 7 at index: 3
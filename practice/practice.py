def binary_Practice(arr, target):
    left , right = 0, len(arr)-1
    
    while left<=right:
        mid = (left+right)//2
        if arr[mid]==target:
            return mid
        elif arr[mid]<target:
            left = mid+1
        else:
            right = mid-1
            
    return -1

array=[1, 3, 5, 7, 9, 11]
result = binary_Practice(array, 2)
print(result)
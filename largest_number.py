#largest number
numbers = [3,6,2,5,7,10]
max = numbers[0]

for i in numbers:
    if max < i:
        max = i
print(max)
    
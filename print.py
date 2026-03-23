print(1)
print(2)
print(3)
print(4)
print(5)
print(6)
print(7)
print(8)
print(9)
print(10)

#old
nums = [3,4,5]

for i in nums:
    print(i)

#input for loop
digit = int(input("Enter a number: "))

for i in range(digit):
    print(i+1)

#new
num = [1,2,3,4,5,6,7,8,9]
x = 0

for i in num:
    x += num[i-1]
    print(x)

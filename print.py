#print(1)
#print(2)
#print(3)
#print(4)
#print(5)
#print(6)
#print(7)
#print(8)
#print(9)
#print(10)
#print(11)
#print(12) - I didn't know what to do as well today
#print(13)
#print(14)
print(15)
print(16)
print(17)
print(18)
print(19)
print(20)

#library
age = int(input("Enter your age: "))

status = {
    (age < 18): "Too Young",
    (age == 18): "Still too Young",
    (18 < age <20): "Old enough now",
    (20 <= age < 40): "Perfect",
    (age >= 40): "Welcome"
}[True]

print(status)


print(range(10))

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

#Failed class... need fixing
class Calculating:
    def __init__(self , a, b):
        self.a = a
        self.b = b
    
    def adding():
        c = a+b
        return c
    def multiplying():
        c = a*b
        return c
C1 = Calculating(2, 4)
print(C1)



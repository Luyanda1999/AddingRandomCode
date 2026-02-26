#Hello World
print('Hello, World')

#Calculator Method
a = int(input("Enter the first number: "))
b = int(input("Enter the second number: "))

c = a + b
print(c)

#If Statement Temperature
temperature = 30
if  temperature >= 25:
  print("It is hot out there.")
  print("Drink Water!")
elif temperature < 25 and temperature >=20:
  print("It is nice day.")
else:
  print("It is cold")

#For loop numbers
numbers = [9,5,3,4,8,2]
for i in numbers:
  print (i)

counting = 1000000
for i in range(counting):
    print(i+1)

#While loop
digit = 50
i = 0
while i<= digit:
    print(i)
    i+=1

#Function Practice
def hello(name):
  return ("Hello " + name)

print(hello("Glen"))

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
numbers = [45,26,48,76,12]
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

#Practice sun function
def totally(a,b):
    total = a + b
    return total
    
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))

print("The sum of 2 digits is: " + str(totally(a,b)))

#duplicate remover
numbers=[2,2,4,6,3,6,1]
unique=[]

for i in numbers:
    if i not in unique:
        unique.append(i)
print(unique)

#class
class Person:
    def __init__(self, name):
        self.name = name
    def talk(self):
        print(f"Hello {self.name}")

person = Person(input("Name: "))
person.talk()

#Never mind

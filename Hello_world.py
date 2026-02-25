print('Hello, World')
a = int(input("Enter the first number: "))
b = int(input("Enter the second number: "))

c = a + b
print(c)

temperature = 30
if  temperature >= 25:
  print("It is hot out there.")
  print("Drink Water!")
elif temperature < 25 and temperature >=20:
  print("It is nice day.")
else:
  print("It is cold")

numbers = [9,5,3,4,8,2]
for i in numbers:
  print (i)

def hello(name):
  return ("Hello " + name)

print(hello("Glen"))

print("Hello, World")
a = "2"
b= "2"

c=a+b
print(c)

numbers= [1,2,3,4,5]
i=0
#for
for items in numbers:
    print(items)
#while
while i<len(numbers):
    print(numbers[i])
    i+=1

#Hospital: this code house different variables
name = "Luyanda"
print("Hello, " + name)
name = input("What is your name? ")
age = 35
In_Hospital= True

print("Name of the Patient is: " + name)
print("Age of the Patient: " + str(age))
print("Is the Patient in the Hospital: " + str(In_Hospital))

#sum of 2 numbers
First_Number = input("First number: ") #initial inputs can only take strings and hence why we convert them to number int or float
Second_NUmber = input("Second Number: ")

Total_Sum = float(First_Number) + float(Second_NUmber)
print(Total_Sum)#this is a  number
print("The total sum of 2 Number is: " + str(Total_Sum))#this is a string
#parameters and Key argument
def greet_user(name, surname):#arguements will not run when both values have not been placed in the program
    print(f"Hello {name} {surname}")
    print("welcome aboard")


print("Start text")
greet_user(name = "Luyanda", surname = "Ndwandwe")#keyword arguments define exactly what the is even when switched around
print("End text")

def two_values(a,b):
    total = a + b
    print(total)
    
value_a = float(input("First value: "))
value_b = float(input("Second value: "))

two_values(value_a, value_b)
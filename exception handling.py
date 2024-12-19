try:
    age = int(input("Age: "))
    income = 2000
    risk = income / age
    print(age)
    print(risk)
except ZeroDivisionError:
    print("Age can not be Zero!")
except ValueError:
    print("Invalid value")

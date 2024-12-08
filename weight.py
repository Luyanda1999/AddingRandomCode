weight = input("Weight: ")
unit= input("(K)gs or (L)bs: ")

if unit == "K" or unit == "k":
    size = float(weight)*0.454
    print("Weight is " + str(size) + "in Kgs")
elif unit == "L" or unit == "l":
    size = float(weight)
    print("Weight is " + str(weight) + " in Pounds")
else:
    print('Could not computer')
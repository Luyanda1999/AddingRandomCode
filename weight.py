try:
    weight = input("Weight: ")
    unit= input("(K)gs or (L)bs: ")

    if unit== "L" or unit == "l":
        size = float(weight)/2.205
        print("Weight is " + str(size) + " in Kgs")
    elif unit == "K" or unit =="k":
        size = float(weight)*2.205
        print("Weight is " + str(size) + " in Pounds")
    elif unit != "L" or unit !="l" or unit != "K" or unit !="k":
        print("Can not compute unit type please use 'l' or 'k'")
except ValueError:
    print("Please use number when typing the weight")
except Exception:
    print("Something is not right")
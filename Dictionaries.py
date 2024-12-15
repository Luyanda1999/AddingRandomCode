numbers={
    "1" : "One",
    "2" : "Two",
    "3" : "Three",
    "4" : "Four",
    "5" : "Five",
    "6" : "Six",
    "7" : "Seven",
    "8" : "Eight",
    "9" : "Nine",
    "0" : "Zero"
}
output=""
phone = input("Phone: ")
for i in phone:
    output += numbers.get(i,"!")+" "
print(output)

customer = {
    "name" : "Jaden Smith",
    "age" : 27,
    "Job" : "American Rapper / Actor"
}
customer2 = customer["name"]
customer["name"] = "John Smith"
print(customer["name"] + " & " + customer2)

NPS =[10,10,10,10,10,9,9,0,0,2,3,4,5,8,8]
summing = 0
index = 0
while index < len(NPS):
    summing += NPS[index]
    index += 1
average = summing/index
print(average)

#packages code
######################################################

import ecommerce.shipping

ecommerce.shipping.calc_shipping()

######################################################

from ecommerce import shipping

shipping.calc_shipping()

######################################################
#another example is:
######################################################

from ecommerce.shipping import calc_shipping

calc_shipping()

######################################################

import random # randon generator comes addition with a python extension

for i in range(1):
    print(random.randint(1,6))#rand it pick a random number that has been generated from the rage.

#Random choice
#import random #random generator already imported

brothers= ["Glen","Joko","Trinco","Zolani"]

Rand_Bro= random.choice(brothers)
print(Rand_Bro)

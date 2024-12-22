class Mammal:
    def walk(self):
        print("Walk")


class Dog(Mammal):
    def bark(self):
        print("Bark")
    #def walk(self):      this cause code duplication. Inheritence limits code dupication
        #print("Walk")
class Cat(Mammal):
    def cat(self):
        print("Meow")
    #def walk(self):      this cause code duplication. Inheritence limits code dupication
        #print("Walk")


dog1 = Dog()
cat1 = Cat()

cat1.cat()
dog1.walk()
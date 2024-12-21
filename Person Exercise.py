#person
class Person:
    def __init__(self, name):
        self.name = name
    def talk(self):
        print(f"Hi, I am {self.name} Nice to meet you")


person = Person(input("Enter your name: "))
#person.name = input("Enter your name: ")
person.talk()
    

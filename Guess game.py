secret_num = 9
guess_value = 0
guess_limit = 3

while guess_value <= guess_limit - 1:
    guess = float(input("Guess the value: "))
    if guess == secret_num:
        print("Great")
        break
    guess_value +=1
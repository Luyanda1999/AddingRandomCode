def emojie(message):
    words = message.split(" ")
    emojies = {
        ":)" : "😃",
        ":(" : "🥺"
    }
    output = ""
    for word in words:
        output += emojies.get(word, word) + " "
    return output

message =  input(">")

print(emojie(message))
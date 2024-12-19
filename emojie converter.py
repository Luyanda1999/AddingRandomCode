message =  input(">")
words = message.split(" ")
emojies = {
    ":)" : "😃",
    ":(" : "🥺"
}
output = ""
for word in words:
    output += emojies.get(word, word) + " "
print(output)
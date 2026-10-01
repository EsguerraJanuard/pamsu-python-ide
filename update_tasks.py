import re

with open("/home/errol/.gemini/antigravity/brain/b0d5c315-10f0-4a89-a847-ff69f5cb1629/task.md", "r") as f:
    content = f.read()

content = content.replace("- [ ]", "- [x]")

with open("/home/errol/.gemini/antigravity/brain/b0d5c315-10f0-4a89-a847-ff69f5cb1629/task.md", "w") as f:
    f.write(content)

print("Tasks updated")

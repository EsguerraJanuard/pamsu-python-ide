import os

filepath = "frontend/vite.config.js"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("src: '/school_logo.png',", "src: '/logo-192.png',", 1)
content = content.replace("src: '/school_logo.png',", "src: '/logo-512.png',", 1)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated vite.config.js")

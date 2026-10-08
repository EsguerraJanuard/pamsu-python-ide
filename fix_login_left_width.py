import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('lg:w-[40%]', 'lg:w-[45%]')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Reverted left side to 45%")

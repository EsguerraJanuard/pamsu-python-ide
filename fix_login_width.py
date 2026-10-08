import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('max-w-[400px]', 'max-w-[480px]')
content = content.replace('lg:w-[45%]', 'lg:w-[40%]')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated form width to 480px and reduced left side to 40% to maximize right side")

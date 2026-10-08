import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('src="/pamsu-logo.png"', 'src="/school_logo.png"')
content = content.replace('Welcome back', 'Secure Portal')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed logo and Welcome back text")

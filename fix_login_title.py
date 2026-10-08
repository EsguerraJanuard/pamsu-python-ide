import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('<h2 className="text-2xl font-black text-text-main">\n              Secure Portal\n            </h2>', '<h2 className="text-2xl font-black text-text-main">\n              Sign in\n            </h2>')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Changed Secure Portal to Sign in")

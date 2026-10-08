import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('<h2 className="text-2xl font-black text-text-main">\n              Sign in\n            </h2>', '<h2 className="text-2xl font-black text-text-main">\n              Sign in to your workspace\n            </h2>')
content = content.replace('<p className="mt-2 text-sm text-text-muted">\n              Sign in to your university workspace\n            </p>', '<p className="mt-2 text-sm text-text-muted">\n              Use your verified university account\n            </p>')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Changed to Sign in to your workspace")

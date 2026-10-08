import os
import re

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Just remove everything from {/* TEMP SEED BUTTON FOR DEMO */} down to </button>
pattern = r"\s*\{\/\* TEMP SEED BUTTON FOR DEMO \*\/\}.*?Initialize Admin Account \(Demo\)\s*</button>"
content = re.sub(pattern, "", content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed demo button correctly")

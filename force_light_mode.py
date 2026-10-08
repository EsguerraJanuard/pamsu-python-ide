import os
import re

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove the Theme Toggle button UI
theme_toggle_regex = r'\{/\* Theme Toggle \*/\}.*?</button>\n        </div>'
content = re.sub(theme_toggle_regex, '', content, flags=re.DOTALL)

# 2. Modify useEffect to force light mode
effect_injection = """  useEffect(() => {
    // Force light mode on login page
    document.documentElement.classList.remove("dark");
    
    const handleModifier = (e) => {"""
content = content.replace("  useEffect(() => {\n    const handleModifier = (e) => {", effect_injection)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed theme toggle and forced light mode")

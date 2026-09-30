import os

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_text = "The Reference Code Analyzer automatically selects the difficulty and checks required AST rules for you."
new_text = "The Analyzer will suggest the difficulty and AST rules, but you can freely customize them in the checklist below."

if old_text in content:
    content = content.replace(old_text, new_text)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated text.")
else:
    print("Could not find text.")

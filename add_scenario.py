import re

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the "Overview / Description" label and placeholder to explicitly ask for Real-world Scenario
content = content.replace(
    '<label htmlFor="description" className="block text-xs font-semibold text-text-muted mb-1.5">Overview / Description</label>',
    '<label htmlFor="description" className="block text-xs font-semibold text-text-muted mb-1.5">Problem Context / Real-world Scenario</label>'
)

content = content.replace(
    'placeholder="Provide a brief overview of what this activity is about..."',
    'placeholder="Provide a real-world scenario or problem context for this activity (e.g. \'You are a software engineer building a POS system...\')"'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated Activity Editor labels to require Real-world Scenarios.")

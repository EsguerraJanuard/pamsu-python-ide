import os

filepath = "frontend/src/features/settings/EditorSettings.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace focus-within borders
content = content.replace(
    'focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500',
    'focus-within:border-psu-maroon focus-within:ring-1 focus-within:ring-psu-maroon/20'
)

# Replace Font Size text color
content = content.replace(
    'text-primary-500',
    'text-text-brand'
)

# Replace Slider accent color
content = content.replace(
    'accent-primary-500',
    'accent-psu-maroon dark:accent-psu-gold'
)

# Replace Toggle switch bg color
content = content.replace(
    'peer-checked:bg-primary-500',
    'peer-checked:bg-psu-maroon group-hover:bg-psu-red/50 peer-checked:group-hover:bg-psu-red'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Editor Settings fixed.")

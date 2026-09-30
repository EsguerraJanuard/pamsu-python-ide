import os

filepath = "frontend/src/features/instructor/ActivityEditor.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Title and Icon
content = content.replace(
    'text-sm font-bold uppercase tracking-wider text-psu-gold',
    'text-sm font-bold uppercase tracking-wider text-text-brand'
)
content = content.replace(
    'className="h-4 w-4 text-psu-gold"',
    'className="h-4 w-4 text-text-brand"'
)
content = content.replace(
    'className="h-5 w-5 text-psu-gold"',
    'className="h-5 w-5 text-text-brand"'
)

# Fix Textarea focus border
content = content.replace(
    'focus:border-psu-gold',
    'focus:border-psu-maroon dark:focus:border-psu-gold'
)

# Fix Button (Make it Maroon in light, Gold in dark)
content = content.replace(
    'bg-psu-gold px-4 py-2 text-xs font-semibold text-black shadow-md shadow-psu-gold/20',
    'bg-psu-maroon dark:bg-psu-gold px-4 py-2 text-xs font-semibold text-white dark:text-black shadow-md shadow-psu-maroon/20 dark:shadow-psu-gold/20'
)
content = content.replace(
    'text-black" xmlns="http://www.w3.org/2000/svg"',
    'text-white dark:text-black" xmlns="http://www.w3.org/2000/svg"'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Authoring UI Contrast fixed.")

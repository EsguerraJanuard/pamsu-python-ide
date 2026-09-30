import os
import re

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original = content

    # Fix hardcoded green and blue text/borders left over
    content = re.sub(r'text-emerald-\d00', r'text-psu-maroon dark:text-psu-gold', content)
    content = re.sub(r'border-l-emerald-\d00', r'border-l-psu-maroon dark:border-l-psu-gold', content)
    
    content = re.sub(r'text-blue-\d00', r'text-psu-maroon dark:text-psu-gold', content)
    content = re.sub(r'border-l-blue-\d00', r'border-l-psu-maroon dark:border-l-psu-gold', content)

    # Fix Hex Colors
    content = content.replace('#10b981', 'var(--color-psu-gold, #eeb319)') # Used for Donut chart and progress bars
    content = content.replace('#3b82f6', 'var(--color-psu-red, #ce0000)')

    # Upgrade existing text-psu-maroon to be responsive
    # We only want to replace it if it doesn't already have dark:text-psu-gold
    content = re.sub(r'text-psu-maroon(?!\s*dark:text-psu-gold)', r'text-psu-maroon dark:text-psu-gold', content)
    
    # Improve buttons (bg-psu-maroon) in dark mode by adding a glowing border or making them slightly brighter
    # We can add dark:shadow-psu-red/20 dark:border-psu-red/30
    
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed", filepath)

for root, dirs, files in os.walk("frontend/src"):
    for file in files:
        if file.endswith(".jsx") or file.endswith(".js"):
            process_file(os.path.join(root, file))

print("Dark Mode fix complete!")

import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace broken backgrounds
    content = content.replace('bg-[var(--color-psu-gold, #eeb319)]', 'bg-psu-gold')
    content = content.replace('bg-[var(--color-psu-red, #ce0000)]', 'bg-psu-red')
    
    # Replace broken borders
    content = content.replace('border-[var(--color-psu-gold, #eeb319)]', 'border-psu-gold')
    content = content.replace('border-[var(--color-psu-red, #ce0000)]', 'border-psu-red')

    # Replace broken text
    content = content.replace('text-[var(--color-psu-gold, #eeb319)]', 'text-psu-gold')
    content = content.replace('text-[var(--color-psu-red, #ce0000)]', 'text-psu-red')

    # I also notice there was hover:bg-[#2563eb] (blue-600). Change to hover:bg-psu-maroon or psu-red
    content = content.replace('hover:bg-[#2563eb]', 'hover:bg-psu-maroon')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed syntax in", filepath)

for root, dirs, files in os.walk("frontend/src"):
    for file in files:
        if file.endswith(".jsx"):
            process_file(os.path.join(root, file))

print("Invalid Tailwind syntax fixed!")

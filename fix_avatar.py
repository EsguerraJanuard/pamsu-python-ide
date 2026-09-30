import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Avatar circles: bg-psu-gold text-white -> bg-psu-maroon text-white
    content = re.sub(
        r'className="([^"]*)bg-psu-gold([^"]*)text-white([^"]*)rounded-full', 
        r'className="\1bg-psu-maroon\2text-white\3rounded-full', 
        content
    )
    # Also if order is reversed
    content = re.sub(
        r'rounded-full bg-psu-gold([^"]*)text-white', 
        r'rounded-full bg-psu-maroon\1text-white', 
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed avatar in", filepath)

for root, dirs, files in os.walk("frontend/src"):
    for file in files:
        if file.endswith(".jsx"):
            process_file(os.path.join(root, file))

print("Avatar fix complete!")

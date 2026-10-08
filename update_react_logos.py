import os
import glob

jsx_files = glob.glob('frontend/src/**/*.jsx', recursive=True)

for filepath in jsx_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "school_logo.png" in content:
        content = content.replace("school_logo.png", "logo-192.png")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")

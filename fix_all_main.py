import os
import glob

# Walk all jsx files
for root, _, files in os.walk("frontend/src"):
    for file in files:
        if file.endswith(".jsx"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find all <main tags
            if "<main" in content and "flex-1" in content and "min-w-0" not in content:
                # Add min-w-0 to the className if flex-1 is there
                content = content.replace('className="flex-1', 'className="min-w-0 flex-1')
                content = content.replace('className="assignments-page flex-1', 'className="assignments-page min-w-0 flex-1')
                content = content.replace('className="settings-page flex-1', 'className="settings-page min-w-0 flex-1')
                content = content.replace('className="submissions-page flex-1', 'className="submissions-page min-w-0 flex-1')
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

print("Added min-w-0 to all <main> tags")

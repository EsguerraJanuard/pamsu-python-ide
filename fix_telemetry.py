import os

filepath = "backend/app/routers/users.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove the deduction logic
    import re
    # We will just replace the body of update_integrity_score
    pattern = r'(def update_integrity_score.*?:)(.*?)(return \{)'
    replacement = r'\1\n    # Panel Requirement: Telemetry no longer deducts points.\n    \3'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed users.py telemetry deduction")

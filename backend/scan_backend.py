import os
import glob
import re

backend_dir = "app"
py_files = glob.glob(f"{backend_dir}/**/*.py", recursive=True)

findings = {
    "print_statements": [],
    "bare_excepts": [],
    "todos": [],
    "hardcoded_secrets": []
}

secret_patterns = re.compile(r'(password|secret|key)\s*=\s*[\'"][^\'"]+[\'"]', re.IGNORECASE)

for filepath in py_files:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        
        # Skip comments for prints and excepts
        if stripped.startswith("#") and "TODO" not in stripped and "FIXME" not in stripped:
            continue
            
        if "print(" in stripped:
            findings["print_statements"].append(f"{filepath}:{line_num} - {stripped}")
            
        if re.search(r'except\s*(Exception|BaseException)?\s*:', stripped) or "except:" in stripped:
            findings["bare_excepts"].append(f"{filepath}:{line_num} - {stripped}")
            
        if "TODO" in stripped or "FIXME" in stripped:
            findings["todos"].append(f"{filepath}:{line_num} - {stripped}")
            
        if secret_patterns.search(stripped) and "os.getenv" not in stripped and "environ.get" not in stripped:
            findings["hardcoded_secrets"].append(f"{filepath}:{line_num} - {stripped}")

print("=== BACKEND SCAN REPORT ===")
for category, items in findings.items():
    print(f"\n[{category.upper()}] ({len(items)} found)")
    for item in items[:15]:  # Limit output to first 15 per category
        print("  " + item)
    if len(items) > 15:
        print(f"  ... and {len(items) - 15} more.")


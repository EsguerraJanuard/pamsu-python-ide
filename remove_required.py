import os
import re

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    # Remove required attribute
    content = re.sub(r'\s+required(\s|>)', r'\1', content)
    # Remove required={} attribute
    content = re.sub(r'\s+required={.*?}(\s|>)', r'\1', content)

    # In ActivityEditor.jsx, disable the submit button until required fields are filled
    if "ActivityEditor.jsx" in filepath:
        # formData.title and formData.description are the minimum required
        content = re.sub(
            r'disabled={loading}',
            r'disabled={loading || !formData.title.trim() || !formData.description.trim()}',
            content
        )
        
    if "EditClassModal.jsx" in filepath:
        content = re.sub(
            r'disabled={isLoading}',
            r'disabled={isLoading || !formData.name.trim() || !formData.subject_code.trim() || !formData.section.trim()}',
            content
        )

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated", filepath)

for root, dirs, files in os.walk("frontend/src"):
    for file in files:
        if file.endswith(".jsx") and file not in ["Login.jsx", "Register.jsx"]:
            process_file(os.path.join(root, file))

print("Validation refactor complete!")

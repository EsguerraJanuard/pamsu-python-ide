# coding=utf-8
import os
import re

filepath = "frontend/src/components/modals/StudentGradebookModal.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r"ID Unknown'\} . \{student\?\.email\}", "ID Unknown'} \u2022 {student?.email}", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed dot")

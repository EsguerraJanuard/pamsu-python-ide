import os
import re

filepath = "frontend/src/features/practice/PracticeWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("console.error(\"Submission failed\", err);", "console.error(\"Submission failed\", err);\n        setFeedback({\n          is_successful: false,\n          message: 'Submission failed: ' + (err.message || 'Network error'),\n          ast_feedback: []\n        });")

content = content.replace("console.error(\"Failed to load task:\", err);", "console.error(\"Failed to load task:\", err);\n        setFeedback({\n          is_successful: false,\n          message: 'Failed to load task: ' + (err.message || 'Network error'),\n          ast_feedback: []\n        });")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed PracticeWorkspace.jsx error handling")

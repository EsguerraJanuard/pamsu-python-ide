import os
import re

filepath = "frontend/src/features/submissions/Submissions.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_config = """const STATUS_CONFIG = {
  awaiting_review: {
    label: "Awaiting review",
    badgeClass: "border-border-strong bg-bg-glass text-text-muted",
    accentClass: "border-l-border-strong",
  },
  graded: {
    label: "Graded",
    badgeClass: "border-psu-maroon bg-psu-maroon text-white dark:border-psu-gold dark:bg-psu-gold dark:text-black",
    accentClass: "border-l-psu-maroon dark:border-l-psu-gold",
  },
};"""

config_pattern = re.compile(r'const STATUS_CONFIG = \{.*?\n  \};\n', re.DOTALL)
content = re.sub(config_pattern, new_config + "\n", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed Submissions STATUS_CONFIG")

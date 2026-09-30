import os
import re

filepath = "frontend/src/features/assignments/Assignments.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_config = """const STATUS_CONFIG = {
  due_today: {
    label: "Due today",
    badgeClass: "border-psu-red/30 bg-psu-red/10 text-psu-red",
    accentClass: "border-l-psu-red",
    progressClass: "bg-psu-red",
    buttonClass: "border border-psu-red/40 bg-transparent text-psu-red hover:bg-psu-red/10",
  },
  in_progress: {
    label: "In progress",
    badgeClass: "border-border-strong bg-bg-glass text-text-muted",
    accentClass: "border-l-border-strong",
    progressClass: "bg-border-strong",
    buttonClass: "border border-border-strong bg-transparent text-text-muted hover:bg-bg-glass hover:text-text-main",
  },
  submitted: {
    label: "Submitted",
    badgeClass: "border-psu-maroon/30 bg-psu-maroon/10 text-text-brand dark:border-psu-gold/30 dark:bg-psu-gold/10",
    accentClass: "border-l-psu-maroon dark:border-l-psu-gold",
    progressClass: "bg-psu-maroon dark:bg-psu-gold",
    buttonClass: "border border-psu-maroon/40 bg-transparent text-text-brand hover:bg-psu-maroon/10 dark:border-psu-gold/40 dark:hover:bg-psu-gold/10",
  },
  graded: {
    label: "Graded",
    badgeClass: "border-psu-maroon bg-psu-maroon text-white dark:border-psu-gold dark:bg-psu-gold dark:text-black",
    accentClass: "border-l-psu-maroon dark:border-l-psu-gold",
    progressClass: "bg-psu-maroon dark:bg-psu-gold",
    buttonClass: "border border-psu-maroon bg-transparent text-text-brand hover:bg-psu-maroon/10 dark:border-psu-gold dark:hover:bg-psu-gold/10",
  },
};"""

# Replace the STATUS_CONFIG block
config_pattern = re.compile(r'const STATUS_CONFIG = \{.*?\n  \};\n', re.DOTALL)
content = re.sub(config_pattern, new_config + "\n", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed STATUS_CONFIG")

import os

filepath = "frontend/src/features/submissions/SubmissionDetails.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('awaiting_review: "text-text-brand border-blue-400/30 bg-blue-400/10"', 'awaiting_review: "text-text-brand border-border-strong bg-bg-glass"')
content = content.replace('graded: "text-violet-400 border-violet-400/30 bg-violet-400/10"', 'graded: "text-white dark:text-black border-psu-maroon dark:border-psu-gold bg-psu-maroon dark:bg-psu-gold"')
content = content.replace('submitted: "text-text-brand border-emerald-400/30 bg-emerald-400/10"', 'submitted: "text-text-brand border-psu-maroon/30 dark:border-psu-gold/30 bg-psu-maroon/10 dark:bg-psu-gold/10"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed Submission Details.")

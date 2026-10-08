import os

filepath = "frontend/src/features/practice/PracticeWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix indigo to psu-gold
content = content.replace('border-indigo-500/40 bg-indigo-500/10 p-5 shadow-[0_0_15px_rgba(99,102,241,0.15)]', 'border-psu-gold/40 bg-psu-gold/10 p-5 shadow-[0_0_15px_rgba(238,179,25,0.15)]')
content = content.replace('text-indigo-400', 'text-psu-gold')
content = content.replace('text-indigo-300', 'text-psu-gold/80')
content = content.replace('border-indigo-400/20 border-t-indigo-400', 'border-psu-gold/20 border-t-psu-gold')
content = content.replace('text-indigo-900 dark:text-indigo-100', 'text-psu-gold dark:text-psu-gold')

# Fix border-white/5
content = content.replace('border-b border-white/5 bg-bg-panel', 'border-b border-border-subtle bg-bg-panel')

# Fix redundant hover
content = content.replace('hover:bg-psu-maroon', 'hover:bg-psu-red')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored PracticeWorkspace")

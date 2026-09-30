import os
import re

filepath = "frontend/src/features/dashboard/InstructorDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 'View all' link
content = content.replace(
    'className="text-[10px] text-psu-gold hover:underline"',
    'className="text-[10px] text-text-brand hover:underline"'
)

# Fix 'NEW' badge
content = content.replace(
    'bg-psu-maroon/20 px-1.5 py-0.5 text-[9px] font-bold text-psu-gold',
    'bg-psu-maroon/10 dark:bg-psu-gold/10 px-1.5 py-0.5 text-[9px] font-bold text-psu-maroon dark:text-psu-gold'
)

# Fix 'Grade Now' button
content = content.replace(
    'text-[10px] bg-psu-gold/10 hover:bg-psu-gold/20 text-psu-gold',
    'text-[10px] bg-psu-maroon/10 hover:bg-psu-maroon/20 text-psu-maroon dark:bg-psu-gold/10 dark:hover:bg-psu-gold/20 dark:text-psu-gold'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Contrast fixed.")

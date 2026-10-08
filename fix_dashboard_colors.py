import os

filepath = "frontend/src/features/dashboard/StudentDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the progress ring color
content = content.replace('stroke="var(--color-psu-red, #ce0000)"', 'stroke="var(--color-text-brand)"')

# Fix the "Details" buttons colors
content = content.replace('text-psu-red transition-colors hover:text-[#60a5fa]', 'text-text-brand transition-colors hover:text-text-brand/80')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed StudentDashboard.jsx")

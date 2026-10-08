import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Masterlist Card Gradient
content = content.replace(
    'bg-gradient-to-r from-emerald-500 to-emerald-400',
    'bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500'
)

# Fix Upload Icon
content = content.replace(
    'group-hover:text-emerald-500',
    'group-hover:text-psu-maroon dark:group-hover:text-psu-gold'
)

# Fix Search Icon
content = content.replace(
    'group-focus-within:text-emerald-500',
    'group-focus-within:text-psu-maroon dark:group-focus-within:text-psu-gold'
)

# Fix Search Input Border
content = content.replace(
    'focus:border-emerald-500',
    'focus:border-psu-maroon dark:focus:border-psu-gold'
)

# Update Stats Colors to be more theme aligned (optional, but good)
content = content.replace(
    'colorClass="text-blue-500"',
    'colorClass="text-psu-maroon dark:text-psu-gold"'
)
content = content.replace(
    'colorClass="text-emerald-500"',
    'colorClass="text-psu-maroon dark:text-psu-gold"'
)
content = content.replace(
    'colorClass="text-purple-500"',
    'colorClass="text-psu-maroon dark:text-psu-gold"'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed theme colors")

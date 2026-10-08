import os

filepath = "frontend/src/features/dashboard/Analytics.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('to-purple-500/5', 'to-psu-gold/5')
content = content.replace('bg-purple-500/10 rounded-lg text-purple-400', 'bg-psu-gold/10 rounded-lg text-psu-gold')
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

filepath = "frontend/src/features/instructor/LiveMonitoring.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('bg-purple-500/10 px-2 py-1 text-xs font-medium text-text-violet ring-1 ring-inset ring-purple-500/20', 'bg-psu-gold/10 px-2 py-1 text-xs font-medium text-psu-gold ring-1 ring-inset ring-psu-gold/20')
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored Analytics and LiveMonitoring")

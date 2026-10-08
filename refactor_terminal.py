import os

filepath = "frontend/src/features/workspace/InteractiveTerminal.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("`w-full h-full p-2 rounded overflow-hidden relative ${resolvedTheme === 'dark' ? 'bg-[#0f1117]' : 'bg-slate-50'}`", '"w-full h-full p-2 rounded overflow-hidden relative bg-bg-base"')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Refactored InteractiveTerminal")

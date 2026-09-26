import re

with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    content = f.read()

# Replace the entire InteractiveTerminal block
pattern = r'<div className="w-full h-full min-h-\[300px\] bg-slate-900/50.*?/>'
replacement = '{output}'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Let's just do a simpler regex targeting the exact lines
import sys
lines = content.split('\n')
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if '{activePanel === "output" && (' in line:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if ')}' in lines[i] and 'activePanel === "analysis"' in lines[i+2]:
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    lines = lines[:start_idx] + [
        '                {activePanel === "output" && (',
        '                  <div className="w-full h-full min-h-[300px] bg-slate-900/50 p-4 rounded font-mono text-sm text-slate-300 whitespace-pre-wrap overflow-auto border border-slate-700/50">',
        '                    {output}',
        '                  </div>',
        '                )}'
    ] + lines[end_idx+1:]
    with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
        f.write('\n'.join(lines))
    print("Fixed Workspace.jsx")
else:
    print("Could not find block in Workspace.jsx")


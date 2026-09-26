with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    lines = f.read().split('\n')

for i in range(len(lines)):
    if '  useEffect(() => {' in lines[i] and 'const token = localStorage.getItem("token");' in lines[i+1] and '// Create coding session on load' in lines[i+2]:
        lines[i] = ""
        lines[i+1] = ""
        break

with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
    f.write('\n'.join(lines))
print("Fixed open useEffect")

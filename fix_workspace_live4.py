import re
with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    content = f.read()

content = content.replace('const activityId = searchParams.get("activity");', 'const activityId = searchParams.get("activity");\n  const [sessionId, setSessionId] = useState(null);')

with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
    f.write(content)
print("Added sessionId successfully")

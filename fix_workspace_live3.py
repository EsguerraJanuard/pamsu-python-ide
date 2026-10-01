with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    content = f.read()

content = content.replace('const [activityId, setActivityId] = useState(null);', 'const [activityId, setActivityId] = useState(null);\n  const [sessionId, setSessionId] = useState(null);')

with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
    f.write(content)
print("Added sessionId")

with open('frontend/src/features/workspace/Workspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('const activityId = searchParams.get("activity");', 'const activityId = searchParams.get("activity");\n  const [sessionId, setSessionId] = useState(null);')
c = c.replace('<Statusbar pythonVersion="Python 3" />', '<Statusbar sessionStatus={sessionId ? "active" : "connecting"} pythonVersion="Python 3" />')

with open('frontend/src/features/workspace/Workspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
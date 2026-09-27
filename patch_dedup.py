import re
with open('frontend/src/features/workspace/Workspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace duplicate lines
while 'const [sessionId, setSessionId] = useState(null);\n  const [sessionId, setSessionId] = useState(null);' in c:
    c = c.replace('const [sessionId, setSessionId] = useState(null);\n  const [sessionId, setSessionId] = useState(null);', 'const [sessionId, setSessionId] = useState(null);')

while 'const [sessionId, setSessionId] = useState(null);\r\n  const [sessionId, setSessionId] = useState(null);' in c:
    c = c.replace('const [sessionId, setSessionId] = useState(null);\r\n  const [sessionId, setSessionId] = useState(null);', 'const [sessionId, setSessionId] = useState(null);')

with open('frontend/src/features/workspace/Workspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
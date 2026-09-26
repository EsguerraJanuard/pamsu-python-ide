import re

with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    content = f.read()

# Add sessionId state
if "const [sessionId, setSessionId] = useState(null);" not in content:
    content = content.replace('const [activityId, setActivityId] = useState(null);', 'const [activityId, setActivityId] = useState(null);\n  const [sessionId, setSessionId] = useState(null);')

# Replace WebSocket useEffect with REST initialization and heartbeat
ws_use_effect_pattern = r'  useEffect\(\(\) => \{\n    const token = localStorage\.getItem\("token"\);\n    if \(!token\) return;\n    \n    // Connect to WebSocket\n    const wsUrl = `ws://localhost:8000/api/v1/ws/student\?token=\$\{token\}`;\n    ws\.current = new WebSocket\(wsUrl\);\n\n    ws\.current\.onopen = \(\) => \{\n      console\.log\("WebSocket connected"\);\n    \};\n\n    ws\.current\.onerror = \(error\) => \{\n      console\.error\("WebSocket error:", error\);\n    \};\n\n    ws\.current\.onclose = \(\) => \{\n      console\.log\("WebSocket disconnected"\);\n    \};\n\n    const interval = setInterval\(\(\) => \{\n      if \(ws\.current\?\.readyState === WebSocket\.OPEN\) \{\n        ws\.current\.send\(JSON\.stringify\(\{ \n          event_type: "heartbeat",\n          task_id: activityId \? parseInt\(activityId\) : null,\n          tab_switch_count: stateRefs\.current\.tabSwitchCount,\n          blocked_paste_count: stateRefs\.current\.blockedPasteCount,\n          mouseleave_count: stateRefs\.current\.mouseLeaveCount\n        \}\)\);\n      \}\n    \}, 5000\);\n\n    return \(\) => \{\n      clearInterval\(interval\);\n      if \(ws\.current\) \{\n        ws\.current\.close\(\);\n      \}\n    \};\n  \}, \[activityId\]\);'

rest_implementation = """  // Create coding session on load
  useEffect(() => {
    if (!activityId) return;
    let mounted = true;
    const startSession = async () => {
      try {
        const res = await api.post("/activities/coding-sessions/", { task_id: parseInt(activityId) });
        if (mounted && res && res.session_id) {
          setSessionId(res.session_id);
        }
      } catch (err) {
        console.error("Failed to start coding session", err);
      }
    };
    startSession();
    return () => { mounted = false; };
  }, [activityId]);

  // Handle telemetry interval
  const lastCounts = useRef({ tab: 0, paste: 0, idle: 0 });
  useEffect(() => {
    if (!sessionId) return;
    const interval = setInterval(async () => {
      const currentTab = stateRefs.current.tabSwitchCount;
      const currentPaste = stateRefs.current.blockedPasteCount;
      
      const tabInc = Math.max(0, currentTab - lastCounts.current.tab);
      const pasteInc = Math.max(0, currentPaste - lastCounts.current.paste);
      
      try {
        await api.patch(`/activities/coding-sessions/${sessionId}/activity`, {
          tab_switch_increment: tabInc,
          blocked_paste_increment: pasteInc,
          idle_seconds_increment: 0 // Simplification for now
        });
        
        lastCounts.current.tab = currentTab;
        lastCounts.current.paste = currentPaste;
      } catch (err) {
        console.error("Failed to send heartbeat", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId]);"""

content = re.sub(ws_use_effect_pattern, rest_implementation, content)

with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
    f.write(content)
print("Updated Workspace.jsx")

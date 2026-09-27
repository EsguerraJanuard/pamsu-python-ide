import re
with open('frontend/src/features/workspace/Workspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add sessionId state
c = c.replace('const activityId = searchParams.get("activity");', 'const activityId = searchParams.get("activity");\n  const [sessionId, setSessionId] = useState(null);')

# Replace WebSocket telemetry with REST telemetry
ws_telemetry = """useEffect(() => {
    const token = localStorage.getItem("token");
    
    // Connect to WebSocket
    const wsUrl = `ws://localhost:8000/api/v1/ws/student?token=${token}`;
    ws.current = new WebSocket(wsUrl);
    
    // Heartbeat
    const interval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ 
          event_type: "heartbeat",
          task_id: activityId ? parseInt(activityId) : null,
          tab_switch_count: stateRefs.current.tabSwitchCount,
          blocked_paste_count: stateRefs.current.blockedPasteCount,
          mouseleave_count: stateRefs.current.mouseLeaveCount
        }));
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [activityId]);"""

rest_telemetry = """// Create coding session on load
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
          idle_seconds_increment: 0
        });
        
        lastCounts.current.tab = currentTab;
        lastCounts.current.paste = currentPaste;
      } catch (err) {
        console.error("Failed to send heartbeat", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId]);"""

if ws_telemetry in c:
    c = c.replace(ws_telemetry, rest_telemetry)
else:
    print("Could not find exact WS telemetry block")

# Replace Statusbar connection status
c = c.replace('<Statusbar pythonVersion="Python 3" />', '<Statusbar sessionStatus={sessionId ? "active" : "connecting"} pythonVersion="Python 3" />')

with open('frontend/src/features/workspace/Workspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
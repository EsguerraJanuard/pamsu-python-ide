import re
with open('frontend/src/features/workspace/Workspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

pattern = re.compile(r'useEffect\(\(\) => \{\n\s*const token = localStorage\.getItem\("token"\);\n\s*if \(!token\) return;\n.*?\}\n\s*\}, \[activityId\]\);', re.DOTALL)

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

if pattern.search(c):
    c = pattern.sub(rest_telemetry, c)
    print("Replaced WS telemetry successfully")
else:
    print("Regex failed to match WS telemetry")

with open('frontend/src/features/workspace/Workspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
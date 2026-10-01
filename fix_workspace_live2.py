with open("frontend/src/features/workspace/Workspace.jsx", "r") as f:
    lines = f.read().split('\n')

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'const wsUrl = `ws://localhost:8000/api/v1/ws/student?token=${token}`;' in line:
        start_idx = i - 3
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if '}, [activityId]);' in lines[i]:
            end_idx = i
            break

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

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + rest_implementation.strip('\n').split('\n') + lines[end_idx+1:]
    with open("frontend/src/features/workspace/Workspace.jsx", "w") as f:
        f.write('\n'.join(new_lines))
    print("Replaced ws block")
else:
    print("Could not find block")

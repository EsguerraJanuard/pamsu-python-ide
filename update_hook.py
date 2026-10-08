import os

filepath = "frontend/src/hooks/useBehaviorTracking.js"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

replacement = """  // Telemetry heartbeat - sends increments every 5 seconds
  const lastCounts = useRef({ tab: 0, paste: 0, mouse: 0 });
  useEffect(() => {
    const interval = setInterval(async () => {
      const currentTab = stateRefs.current.tabSwitchCount;
      const currentPaste = stateRefs.current.blockedPasteCount;
      const currentMouse = stateRefs.current.mouseLeaveCount;

      const tabInc = Math.max(0, currentTab - lastCounts.current.tab);
      const pasteInc = Math.max(0, currentPaste - lastCounts.current.paste);
      const mouseInc = Math.max(0, currentMouse - lastCounts.current.mouse);

      if (tabInc === 0 && pasteInc === 0 && mouseInc === 0) return;

      try {
        if (sessionId) {
          await api.patch(`/activities/coding-sessions/${sessionId}/activity`, {
            tab_switch_increment: tabInc,
            blocked_paste_increment: pasteInc,
            mouseleave_increment: mouseInc,
            idle_duration_increment_seconds: 0,
          }).catch(() => {});
        }
        
        // Also deduct integrity points globally!
        await api.patch('/users/me/integrity', {
            is_graded: !!sessionId,
            tab_switch_increment: tabInc,
            blocked_paste_increment: pasteInc,
            mouseleave_increment: mouseInc,
        }).catch(() => {});

        lastCounts.current.tab = currentTab;
        lastCounts.current.paste = currentPaste;
        lastCounts.current.mouse = currentMouse;
      } catch (err) {
        console.error("Failed to send heartbeat", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId]);"""

# Replace the old useEffect
import re
pattern = r"  // Telemetry heartbeat.*?return \(\) => clearInterval\(interval\);\n  \}, \[sessionId\]\);"
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated hook")

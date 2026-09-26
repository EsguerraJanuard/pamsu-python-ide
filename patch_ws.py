import re
with open('frontend/src/features/workspace/Workspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'const ws = useRef(null);',
    """const ws = useRef(null);
  
  const stateRefs = useRef({ tabSwitchCount: 0, blockedPasteCount: 0, mouseLeaveCount: 0 });
  useEffect(() => {
    stateRefs.current = { tabSwitchCount, blockedPasteCount, mouseLeaveCount };
  }, [tabSwitchCount, blockedPasteCount, mouseLeaveCount]);"""
)

c = c.replace(
    'tab_switch_count: tabSwitchCount,',
    'tab_switch_count: stateRefs.current.tabSwitchCount,'
)
c = c.replace(
    'blocked_paste_count: blockedPasteCount,',
    'blocked_paste_count: stateRefs.current.blockedPasteCount,'
)
c = c.replace(
    'mouseleave_count: mouseLeaveCount',
    'mouseleave_count: stateRefs.current.mouseLeaveCount'
)

c = c.replace(
    '}, [activityId, tabSwitchCount, blockedPasteCount, mouseLeaveCount]);',
    '}, [activityId]);'
)

with open('frontend/src/features/workspace/Workspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
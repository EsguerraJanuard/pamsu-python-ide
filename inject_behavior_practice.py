import os
import re

filepath = "frontend/src/features/practice/PracticeWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Import
if "useBehaviorTracking" not in content:
    content = content.replace('import { useAuth } from "../../features/auth/AuthContext";', 
        'import { useAuth } from "../../features/auth/AuthContext";\nimport { useBehaviorTracking } from "../../hooks/useBehaviorTracking";')

# 2. Hook call & handler
hook_injection = """  const { user } = useAuth();
  
  const { tabSwitchCount, mouseLeaveCount, blockedPasteCount, setBlockedPasteCount, showBehaviorNotice, setShowBehaviorNotice } = useBehaviorTracking({ sessionId: null });
  
  const recordBlockedPaste = () => {
    setBlockedPasteCount((currentCount) => currentCount + 1);
  };
  
  const handleNativePaste = (event) => {
    event.preventDefault();
    recordBlockedPaste();
  };"""
content = content.replace('  const { user } = useAuth();', hook_injection)

# 3. UI Banner
ui_banner = """      </header>

      {showBehaviorNotice && (
        <div
          className="flex shrink-0 items-center justify-between gap-3 border-b border-amber-500/20 bg-amber-500/[0.07] px-4 py-2 text-[10px] text-text-amber select-none"
          role="status"
        >
          <span className="truncate">
            Recorded: {tabSwitchCount} tab {tabSwitchCount === 1 ? "switch" : "switches"}, {blockedPasteCount} blocked {blockedPasteCount === 1 ? "paste" : "pastes"}, and {mouseLeaveCount} mouse {mouseLeaveCount === 1 ? "exit" : "exits"}.
          </span>
          <button
            type="button"
            onClick={() => setShowBehaviorNotice(false)}
            className="shrink-0 font-semibold text-text-amber hover:text-text-main transition-colors cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">"""
content = content.replace('      </header>\n\n      <div className="flex flex-1 overflow-hidden">', ui_banner)
# Fallback if different formatting
content = content.replace('      </header>\n      <div className="flex flex-1 overflow-hidden">', ui_banner)

# 4. onPasteCapture
content = content.replace('<div className="min-w-0 flex-1 overflow-hidden">', '<div className="min-w-0 flex-1 overflow-hidden" onPasteCapture={handleNativePaste}>')

# 5. Editor onMount
old_onmount = "onMount={(editor, monaco) => { editorRef.current = editor; monacoRef.current = monaco; }}"
new_onmount = """onMount={(editor, monaco) => { 
                editorRef.current = editor; 
                monacoRef.current = monaco; 
                editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyV, () => recordBlockedPaste());
              }}"""
content = content.replace(old_onmount, new_onmount)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected behavior tracking into PracticeWorkspace.jsx")

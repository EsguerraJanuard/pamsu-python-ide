import os
import re

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Make columns flex columns
content = re.sub(r'<div>\s*<h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">AST Analysis</h4>', r'<div className="flex flex-col h-full">\n                                 <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">AST Analysis</h4>', content)

content = re.sub(r'<div>\s*<h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Execution Logs</h4>', r'<div className="flex flex-col h-full">\n                                 <h4 className="text-xs font-bold text-text-muted mb-2 uppercase tracking-wider">Execution Logs</h4>', content)

# Make inner divs flex-1
content = re.sub(r'<div className="bg-bg-panel p-4 rounded-lg border border-border-strong min-h-\[120px\] max-h-\[250px\] overflow-y-auto shadow-inner">', r'<div className="flex-1 bg-bg-panel p-4 rounded-lg border border-border-strong min-h-[120px] max-h-[250px] overflow-y-auto shadow-inner">', content)

content = re.sub(r'<div className="bg-\[#0a0a0f\] p-4 rounded-lg border border-border-strong min-h-\[120px\] max-h-\[250px\] overflow-y-auto font-mono text-\[11px\] leading-relaxed shadow-inner">', r'<div className="flex-1 bg-[#0a0a0f] p-4 rounded-lg border border-border-strong min-h-[120px] max-h-[250px] overflow-y-auto font-mono text-[11px] leading-relaxed shadow-inner">', content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed height regex")

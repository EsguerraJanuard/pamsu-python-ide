import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

import re
old_search = r'<input type="text" placeholder="Search logs[^>]+w-64" />'
new_search = '<div className="relative group"><svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-psu-maroon transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg><input type="text" placeholder="Search logs..." value={searchAudit} onChange={(e) => setSearchAudit(e.target.value)} className="w-full pl-9 pr-4 py-2.5 bg-bg-glass border border-border-strong rounded-xl text-sm focus:outline-none focus:border-psu-maroon transition-colors shadow-sm" /></div>'
content = re.sub(old_search, new_search, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

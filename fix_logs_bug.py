import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    """        const res = await api.get(`/admin/audit-logs?skip=${newSkip}&limit=50`);
        if (res.data.length < 50) setHasMoreLogs(false);
        setAuditLogs(prev => [...prev, ...resData]);""",
    """        const res = await api.get(`/admin/audit-logs?skip=${newSkip}&limit=50`);
        const resData = res.data || res;
        if (resData.length < 50) setHasMoreLogs(false);
        setAuditLogs(prev => [...prev, ...resData]);"""
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

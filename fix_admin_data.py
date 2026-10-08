import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix loadMoreUsers
content = content.replace(
    'if (res.data.length < 50) setHasMoreUsers(false);',
    'const resData = res.data || res;\n      if (resData.length < 50) setHasMoreUsers(false);'
)
content = content.replace(
    'setUsers(prev => [...prev, ...res.data]);',
    'setUsers(prev => [...prev, ...resData]);'
)

# Fix loadMoreLogs
content = content.replace(
    'setAuditLogs(prev => [...prev, ...res.data]);',
    'setAuditLogs(prev => [...prev, ...resData]);'
)

# Fix fetchData array length checks
content = content.replace(
    'if (usersRes.data.length < 50) setHasMoreUsers(false);',
    'const usersList = usersRes.data || usersRes;\n        if (usersList.length < 50) setHasMoreUsers(false);'
)
content = content.replace(
    'if (logsRes.data.length < 50) setHasMoreLogs(false);',
    'const logsList = logsRes.data || logsRes;\n        if (logsList.length < 50) setHasMoreLogs(false);'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed data parsing")

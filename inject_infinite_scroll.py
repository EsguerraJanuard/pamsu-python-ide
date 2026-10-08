import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import
if "react-intersection-observer" not in content:
    content = content.replace("import React, { useState, useEffect } from 'react';", "import React, { useState, useEffect } from 'react';\nimport { useInView } from 'react-intersection-observer';")

# 2. Add states
state_addition = """
  const [activeTab, setActiveTab] = useState('overview');
  
  const [usersSkip, setUsersSkip] = useState(0);
  const [logsSkip, setLogsSkip] = useState(0);
  const [hasMoreUsers, setHasMoreUsers] = useState(true);
  const [hasMoreLogs, setHasMoreLogs] = useState(true);
  
  const { ref: userRef, inView: userInView } = useInView();
  const { ref: logRef, inView: logInView } = useInView();
  
  const loadMoreUsers = async () => {
    if (!hasMoreUsers) return;
    const newSkip = usersSkip + 50;
    try {
      const res = await api.get(`/admin/users?skip=${newSkip}&limit=50`);
      if (res.data.length < 50) setHasMoreUsers(false);
      setUsers(prev => [...prev, ...res.data]);
      setUsersSkip(newSkip);
    } catch (err) {
      console.error(err);
    }
  };
  
  const loadMoreLogs = async () => {
    if (!hasMoreLogs) return;
    const newSkip = logsSkip + 50;
    try {
      const res = await api.get(`/admin/audit-logs?skip=${newSkip}&limit=50`);
      if (res.data.length < 50) setHasMoreLogs(false);
      setAuditLogs(prev => [...prev, ...res.data]);
      setLogsSkip(newSkip);
    } catch (err) {
      console.error(err);
    }
  };
  
  useEffect(() => {
    if (userInView) loadMoreUsers();
  }, [userInView]);
  
  useEffect(() => {
    if (logInView) loadMoreLogs();
  }, [logInView]);
"""
content = re.sub(r"\s*const \[activeTab, setActiveTab\] = useState\('overview'\);", state_addition, content)

# 3. Update fetchData
fetch_replacement = """        const [statsRes, usersRes, logsRes, settingsRes] = await Promise.all([
          api.get("/admin/stats").catch(() => ({ data: { total_instructors: 0, total_students: 0, total_classrooms: 0 }})),
          api.get("/admin/users?skip=0&limit=50").catch(() => ({ data: [] })),
          api.get("/admin/audit-logs?skip=0&limit=50").catch(() => ({ data: [] })),
          api.get("/admin/settings").catch(() => ({ data: { maintenance_mode: false, default_ast_strictness: 'moderate' } }))
        ]);
        if (usersRes.data.length < 50) setHasMoreUsers(false);
        if (logsRes.data.length < 50) setHasMoreLogs(false);"""
        
content = re.sub(r"\s*const \[statsRes, usersRes, logsRes, settingsRes\] = await Promise\.all\(\[\n\s*api\.get\(\"/admin/stats\"\).*?\n\s*api\.get\(\"/admin/users\"\).*?\n\s*api\.get\(\"/admin/audit-logs\"\).*?\n\s*api\.get\(\"/admin/settings\"\).*?\n\s*\]\);", fetch_replacement, content, flags=re.DOTALL)

# 4. Add refs to tables
# Find </tbody> for faculty/students
# Actually, the users are split into masterlist and faculty in the render logic:
# filteredFaculty.map
# filteredStudents.map
# But they all use `users` array!
# We can just put `<tr ref={userRef}></tr>` at the end of both tables!
content = content.replace("</tbody>\n                  </table>", "  {hasMoreUsers && <tr ref={userRef}><td colSpan=\"5\" className=\"text-center py-4 text-slate-500\">Loading more...</td></tr>}\n                  </tbody>\n                  </table>")
content = content.replace("</tbody>\n                      </table>", "  {hasMoreLogs && <tr ref={logRef}><td colSpan=\"3\" className=\"text-center py-4 text-slate-500\">Loading more...</td></tr>}\n                      </tbody>\n                      </table>")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated AdminDashboard.jsx")

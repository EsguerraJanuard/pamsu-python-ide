import os
import re

def replace_in_file(filepath, old, new):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Submissions.jsx
# Add error state
s_path = "frontend/src/features/submissions/Submissions.jsx"
replace_in_file(s_path, 'const [filter, setFilter] = useState("all");', 'const [filter, setFilter] = useState("all");\n  const [error, setError] = useState(null);')
# Replace console.error with setError
replace_in_file(s_path, 'console.error("Failed to load submissions", err);', 'setError("Failed to load submissions. Please try again later.");')
replace_in_file(s_path, 'console.error("Failed to fetch grades page", e);', 'setError("Failed to fetch grades page.");')
# Render error if it exists
replace_in_file(s_path, '<div className="mb-6 flex items-center justify-between">', '{error && <div className="mb-4 rounded-lg bg-psu-maroon/10 p-4 text-sm text-text-brand border border-psu-maroon/20">{error}</div>}\n        <div className="mb-6 flex items-center justify-between">')

# 2. NotificationsPage.jsx
n_path = "frontend/src/pages/NotificationsPage.jsx"
replace_in_file(n_path, 'catch (err) {\n      setNotifications([]);', 'catch {\n      setNotifications([]);')
replace_in_file(n_path, 'catch (err) {\n        console.error("Failed to mark all as read:", err);', 'catch {\n        // Error suppressed')
replace_in_file(n_path, 'catch (err) {\n        console.error("Failed to mark as read:", err);', 'catch {\n        // Error suppressed')

# Wrap fetchNotifications in useCallback
replace_in_file(n_path, 'import { useState, useEffect } from "react";', 'import { useState, useEffect, useCallback } from "react";')
replace_in_file(n_path, 'const fetchNotifications = async (currentPage = 1) => {', 'const fetchNotifications = useCallback(async (currentPage = 1) => {')
replace_in_file(n_path, '  };\n\n  useEffect(() => {\n    fetchNotifications(page);\n  }, [page]);', '  }, []);\n\n  useEffect(() => {\n    fetchNotifications(page);\n  }, [page, fetchNotifications]);')

# 3. AuditLogsPage.jsx
a_path = "frontend/src/pages/AuditLogsPage.jsx"
replace_in_file(a_path, 'catch (err) {\n      setLogs([]);', 'catch {\n      setLogs([]);')
replace_in_file(a_path, 'import { useState, useEffect } from "react";', 'import { useState, useEffect, useCallback } from "react";')
replace_in_file(a_path, 'const fetchAuditLogs = async (currentPage = 1, currentFilter = "all") => {', 'const fetchAuditLogs = useCallback(async (currentPage = 1, currentFilter = "all") => {')
replace_in_file(a_path, '  };\n\n  useEffect(() => {\n    fetchAuditLogs(page, actionFilter);\n  }, [page, actionFilter]);', '  }, []);\n\n  useEffect(() => {\n    fetchAuditLogs(page, actionFilter);\n  }, [page, actionFilter, fetchAuditLogs]);')

# api.js console.log removal
api_path = "frontend/src/services/api.js"
replace_in_file(api_path, 'console.error("API call failed:", error);', '')
replace_in_file(api_path, 'console.log("Token removed");', '')
replace_in_file(api_path, 'console.error("Refresh token failed", refreshError);', '')
replace_in_file(api_path, 'console.error("API error format:", error.response.data);', '')
replace_in_file(api_path, 'console.log(`Setting up API interceptors...`);', '')
replace_in_file(api_path, 'console.log(`Setting up interceptors`);', '')
replace_in_file(api_path, 'console.error("Network or generic error:", error);', '')

# Login.jsx console.error removal
login_path = "frontend/src/features/auth/Login.jsx"
replace_in_file(login_path, 'console.error("Login failed:", err);', '')

print("Secondary replacements complete.")

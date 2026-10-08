import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix Instructors empty state
faculty_empty_state = """                      {instructors.length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-4 py-16 text-center text-text-muted">
                            <div className="flex flex-col items-center justify-center">
                              <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                              <p className="font-semibold text-text-main">No faculty members found</p>
                              <p className="text-xs mt-1">Provision an instructor to see them here.</p>
                            </div>
                          </td>
                        </tr>
                      )}
                      {instructors.map"""
content = content.replace("                      {instructors.map", faculty_empty_state)

# Fix Students empty state
students_empty_state = """                      {students.length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-4 py-16 text-center text-text-muted">
                            <div className="flex flex-col items-center justify-center">
                              <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                              <p className="font-semibold text-text-main">No students found</p>
                              <p className="text-xs mt-1">Upload a masterlist to provision students.</p>
                            </div>
                          </td>
                        </tr>
                      )}
                      {students.map"""
content = content.replace("                      {students.map", students_empty_state)

# Fix Audit empty state
import re
old_audit_empty = r'\{filteredLogs\.length === 0 && \(\s*<tr>\s*<td colSpan="5"[^>]+>No logs found matching your search\.</td>\s*</tr>\s*\)\}'
audit_empty_state = """{filteredLogs.length === 0 && (
                        <tr>
                          <td colSpan="5" className="px-4 py-16 text-center text-text-muted">
                            <div className="flex flex-col items-center justify-center">
                              <svg className="w-10 h-10 mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
                              <p className="font-semibold text-text-main">No audit logs available</p>
                              <p className="text-xs mt-1">Actions taken on the system will appear here.</p>
                            </div>
                          </td>
                        </tr>
                      )}"""
content = re.sub(old_audit_empty, audit_empty_state, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

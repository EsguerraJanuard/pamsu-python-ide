import os
import re

filepath = "frontend/src/features/dashboard/ClassRosterView.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add th
content = content.replace('<th className="px-6 py-4 text-center">Submissions</th>', '<th className="px-6 py-4 text-center">Submissions</th>\n                        <th className="px-6 py-4 text-center">Integrity</th>')

content = content.replace('colSpan="5"', 'colSpan="6"')

td_to_add = """                            <td className="px-6 py-4 text-center">
                              <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold ring-1 ring-inset ${
                                (student.academic_integrity_score ?? 100) >= 90 ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20" : 
                                (student.academic_integrity_score ?? 100) >= 70 ? "bg-amber-500/10 text-amber-400 ring-amber-500/20" : 
                                "bg-rose-500/10 text-rose-400 ring-rose-500/20"
                              }`}>
                                {Math.round(student.academic_integrity_score ?? 100)}%
                              </span>
                            </td>"""

search_str = '                            <td className="px-6 py-4 text-center">\n                              {student.completed_submissions || 0} / {classroom?.task_count || 0}\n                            </td>'
replace_str = search_str + "\n" + td_to_add

content = content.replace(search_str, replace_str)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated ClassRosterView.jsx")

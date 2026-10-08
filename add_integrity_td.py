import os

filepath = "frontend/src/features/dashboard/ClassRosterView.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

td_to_add = """                            <td className="px-6 py-4 text-center font-mono text-text-muted">0</td>
                            <td className="px-6 py-4 text-center">
                              <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold ring-1 ring-inset ${
                                (student.academic_integrity_score ?? 100) >= 90 ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20" : 
                                (student.academic_integrity_score ?? 100) >= 70 ? "bg-amber-500/10 text-amber-400 ring-amber-500/20" : 
                                "bg-rose-500/10 text-rose-400 ring-rose-500/20"
                              }`}>
                                {Math.round(student.academic_integrity_score ?? 100)}%
                              </span>
                            </td>"""

content = content.replace('                            <td className="px-6 py-4 text-center font-mono text-text-muted">0</td>', td_to_add)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated td")

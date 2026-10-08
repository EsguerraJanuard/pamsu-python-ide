import os
import re

filepath = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

badge_html = """                  <p className="text-sm text-text-muted mt-0.5">Student ID: {selectedStudent.student_id || selectedStudent.id}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Global Integrity:</span>
                    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold ring-1 ring-inset ${
                      (selectedStudent.academic_integrity_score ?? 100) >= 90 ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20" : 
                      (selectedStudent.academic_integrity_score ?? 100) >= 70 ? "bg-amber-500/10 text-amber-400 ring-amber-500/20" : 
                      "bg-rose-500/10 text-rose-400 ring-rose-500/20"
                    }`}>
                      {Math.round(selectedStudent.academic_integrity_score ?? 100)}%
                    </span>
                  </div>"""

pattern = r'<p className="text-sm text-text-muted mt-0\.5">Student ID: \{selectedStudent\.student_id \|\| \s*selectedStudent\.id\}</p>'
content = re.sub(pattern, badge_html, content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated Grading Workspace")

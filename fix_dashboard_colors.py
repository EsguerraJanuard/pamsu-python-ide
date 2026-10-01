import os

filepath = "frontend/src/features/dashboard/InstructorDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_badge = """                            <span className="shrink-0 rounded bg-psu-maroon/10 dark:bg-psu-gold/10 px-1.5 py-0.5 text-[9px] font-bold text-psu-maroon dark:text-psu-gold uppercase">"""
new_badge = """                            <span className="shrink-0 rounded bg-psu-maroon/10 px-1.5 py-0.5 text-[9px] font-bold text-text-brand uppercase">"""
content = content.replace(old_badge, new_badge)

old_button = """                            <button
                              onClick={() => navigate(`/instructor/submissions/${sub.id}`)}
                              className="text-[10px] bg-psu-maroon/10 hover:bg-psu-maroon/20 text-psu-maroon dark:bg-psu-gold/10 dark:hover:bg-psu-gold/20 dark:text-psu-gold px-2 py-1 rounded transition-colors font-semibold"
                            >"""
new_button = """                            <button
                              onClick={() => navigate(`/instructor/submissions/${sub.id}`)}
                              className="text-[10px] bg-psu-maroon/10 hover:bg-psu-maroon/20 text-text-brand px-2 py-1 rounded transition-colors font-semibold"
                            >"""
content = content.replace(old_button, new_button)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated InstructorDashboard.jsx badge and button classes")

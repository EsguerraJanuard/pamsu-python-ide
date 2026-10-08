import os

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
mid_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if '<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full max-w-xl shadow-sm relative overflow-hidden">' in line:
        start_idx = i
    if '<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">' in line and 'CS Department Faculty' in lines[i+1]:
        mid_idx = i
    if '</table>' in line and start_idx != -1 and i > start_idx and i < start_idx + 100:
        end_idx = i + 5

lines[start_idx] = """                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 w-full">
                    <div className="xl:col-span-1">
                      <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm relative overflow-hidden sticky top-6">\n"""

lines[start_idx + 1] = """                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500"></div>\n"""

lines[mid_idx - 1] = """                      </div>
                    </div>
                    <div className="xl:col-span-2">\n"""

lines[mid_idx] = """                      <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">\n"""

for i in range(mid_idx, mid_idx + 50):
    if '</table>' in lines[i]:
        lines[i] = """                        </table>
                      </div>
                    </div>
                  </div>\n"""
        break

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed with lines")

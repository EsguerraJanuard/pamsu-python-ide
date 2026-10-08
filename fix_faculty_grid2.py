import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the first div
content = re.sub(
    r'<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full max-w-xl shadow-sm relative overflow-hidden">',
    '<div className="grid grid-cols-1 xl:grid-cols-3 gap-8 w-full">\n                  <div className="xl:col-span-1">\n                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm relative overflow-hidden sticky top-6">',
    content
)

# Replace the gradient line to dark mode one
content = re.sub(
    r'<div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red"></div>',
    '<div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500"></div>',
    content
)

# Close the first col and open the second col before the second glass pane
content = re.sub(
    r'</form>\s*</div>\s*<div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">\s*<h3 className="text-lg font-black mb-6 tracking-tight">CS Department Faculty</h3>',
    '</form>\n                    </div>\n                  </div>\n\n                  <div className="xl:col-span-2">\n                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">\n                      <h3 className="text-lg font-black mb-6 tracking-tight">CS Department Faculty</h3>',
    content
)

# Add closing div for the grid after the table
content = re.sub(
    r'</table>\s*</div>\s*</div>\s*</div>\s*\)\}',
    '</table>\n                    </div>\n                  </div>\n                </div>\n              </div>\n            )}',
    content
)


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed faculty grid with targeted regex")

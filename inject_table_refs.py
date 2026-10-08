import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Find all occurrences of </tbody>\s*</table>
matches = list(re.finditer(r"(\s*)</tbody>\s*</table>", content))

if len(matches) >= 3:
    # 1. Faculty
    span1 = matches[0].span()
    # 2. Students
    span2 = matches[1].span()
    # 3. Audit
    span3 = matches[2].span()
    
    # We replace from back to front to not mess up indices
    part3 = content[span3[0]:span3[1]]
    content = content[:span3[0]] + part3.replace("</tbody>", "  {hasMoreLogs && <tr ref={logRef}><td colSpan=\"3\" className=\"text-center py-4 text-slate-500\">Loading more logs...</td></tr>}\n                      </tbody>") + content[span3[1]:]
    
    part2 = content[span2[0]:span2[1]]
    content = content[:span2[0]] + part2.replace("</tbody>", "  {hasMoreUsers && <tr ref={userRef}><td colSpan=\"5\" className=\"text-center py-4 text-slate-500\">Loading more students...</td></tr>}\n                      </tbody>") + content[span2[1]:]
    
    part1 = content[span1[0]:span1[1]]
    content = content[:span1[0]] + part1.replace("</tbody>", "  {hasMoreUsers && <tr ref={userRef}><td colSpan=\"5\" className=\"text-center py-4 text-slate-500\">Loading more faculty...</td></tr>}\n                      </tbody>") + content[span1[1]:]
    
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected refs into tables")

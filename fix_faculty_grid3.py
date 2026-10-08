import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target1 = """                  <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full max-w-xl shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500"></div>"""

repl1 = """                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 w-full">
                  <div className="xl:col-span-1">
                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm relative overflow-hidden sticky top-6">
                      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-psu-maroon to-psu-red dark:from-psu-gold dark:to-yellow-500"></div>"""

content = content.replace(target1, repl1, 1)

target2 = """                      </button>
                    </form>
                  </div>
  
                  <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">
                    <h3 className="text-lg font-black mb-6 tracking-tight">CS Department Faculty</h3>"""

repl2 = """                      </button>
                    </form>
                  </div>
                  </div>
  
                  <div className="xl:col-span-2">
                    <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl w-full shadow-sm">
                      <h3 className="text-lg font-black mb-6 tracking-tight">CS Department Faculty</h3>"""

content = content.replace(target2, repl2, 1)

target3 = """                      </table>
                    </div>
                  </div>
                </div>
              )}"""

repl3 = """                      </table>
                    </div>
                  </div>
                </div>
                </div>
              )}"""

content = content.replace(target3, repl3, 1)


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed faculty grid securely")

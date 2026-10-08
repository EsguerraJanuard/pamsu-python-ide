import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix layout: remove max-w-[1600px] and let it fill screen to match header
content = content.replace('className="w-full max-w-[1600px] lg:px-8 mx-auto"', 'className="w-full lg:px-4 mx-auto"')

# Fix text contrast for input labels
content = content.replace('text-[10px] font-bold text-text-muted', 'text-[10px] font-bold text-slate-400')
content = content.replace('text-xs font-bold text-psu-gold', 'text-xs font-black text-psu-gold')
content = content.replace('text-xs font-bold text-text-muted', 'text-xs font-bold text-slate-400')

# Fix input field blending
content = content.replace('bg-bg-base px-4 py-3', 'bg-[#0f1117] px-4 py-3')
content = content.replace('bg-bg-base border border-border-subtle shadow-sm', 'bg-bg-base border border-border-strong shadow-md')

# Fix AST Strictness Card blending when unselected
content = content.replace("className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'lenient' ? 'border-emerald-500 bg-emerald-500/5 shadow-sm' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}", 
                          "className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'lenient' ? 'border-emerald-500 bg-emerald-500/5 shadow-sm' : 'border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]'}`}")
content = content.replace("className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon bg-psu-maroon/5 shadow-sm' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}",
                          "className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'moderate' ? 'border-psu-maroon bg-psu-maroon/5 shadow-sm' : 'border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]'}`}")
content = content.replace("className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'strict' ? 'border-red-500 bg-red-500/5 shadow-sm' : 'border-border-subtle hover:border-border-strong hover:bg-bg-base'}`}",
                          "className={`cursor-pointer rounded-2xl border-2 p-5 transition-all ${settings.default_ast_strictness === 'strict' ? 'border-red-500 bg-red-500/5 shadow-sm' : 'border-border-strong bg-[#0f1117]/50 hover:border-slate-500 hover:bg-[#0f1117]'}`}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Basic UI fixes applied.")

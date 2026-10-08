import os

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Container and Headings
content = content.replace('max-w-[480px]', 'max-w-[540px]')
content = content.replace('mb-8 text-center sm:text-left', 'mb-10 text-center sm:text-left')
content = content.replace('text-2xl font-black text-slate-900', 'text-3xl lg:text-4xl font-black text-slate-900 tracking-tight')
content = content.replace('mt-2 text-sm text-slate-500', 'mt-3 text-base text-slate-500')

# Forms wrapper
content = content.replace('space-y-5', 'space-y-6')

# Labels
content = content.replace('mb-1.5 block text-xs font-bold', 'mb-2 block text-xs font-bold')
content = content.replace('text-xs font-bold text-slate-500 uppercase tracking-wider', 'text-xs font-bold text-slate-500 uppercase tracking-widest') # just checking the label style

# Inputs containers
content = content.replace('rounded-xl border border-slate-200 bg-slate-50 px-4 py-3', 'rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4')

# Input fonts
content = content.replace('bg-transparent text-sm', 'bg-transparent text-base')

# Submit button
content = content.replace('rounded-xl bg-gradient-to-r from-psu-maroon to-[#6b0f0f] px-4 py-3 text-sm font-bold', 'rounded-2xl bg-gradient-to-r from-psu-maroon to-[#6b0f0f] px-5 py-4 text-base font-bold')

# Guest button
content = content.replace('rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm font-bold', 'rounded-2xl border border-slate-300 bg-slate-50 px-5 py-4 text-base font-bold')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Scaled up Login.jsx UI")

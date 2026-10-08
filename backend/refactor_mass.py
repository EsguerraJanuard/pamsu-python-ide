import os

def replace_in_file(filepath, old_text, new_text):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if old_text in content:
        content = content.replace(old_text, new_text)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            print(f"Refactored {filepath}: replaced '{old_text}'")

# ForgotPassword.jsx
f = "frontend/src/features/auth/ForgotPassword.jsx"
replace_in_file(f, 'bg-cyan-500/10', 'bg-psu-maroon/10 dark:bg-psu-gold/10')
replace_in_file(f, 'shadow-[0_0_30px_rgba(16,185,129,0.5)]', 'shadow-psu-maroon/50')
replace_in_file(f, 'shadow-[0_0_20px_rgba(16,185,129,0.3)]', 'shadow-psu-maroon/30')
replace_in_file(f, 'bg-white/5', 'bg-border-subtle')

# NotFound.jsx
f = "frontend/src/pages/NotFound.jsx"
replace_in_file(f, 'focus:ring-offset-slate-900', 'focus:ring-offset-bg-base')

# Unauthorized.jsx
f = "frontend/src/pages/Unauthorized.jsx"
replace_in_file(f, 'selection:text-white', 'selection:text-text-main')

# CustomSelect.jsx
f = "frontend/src/components/ui/CustomSelect.jsx"
replace_in_file(f, 'hover:bg-white/5 hover:text-white', 'hover:bg-bg-glass-hover hover:text-text-main')

# Pagination.jsx
f = "frontend/src/components/ui/Pagination.jsx"
replace_in_file(f, 'dark:text-black', 'dark:text-bg-base')

# Navbar.jsx
f = "frontend/src/components/layout/Navbar.jsx"
replace_in_file(f, 'bg-psu-gold font-mono text-xs font-bold text-white', 'bg-psu-gold font-mono text-xs font-bold text-text-main')
replace_in_file(f, 'ring-white/10', 'ring-border-subtle')

# Sidebar.jsx
f = "frontend/src/components/layout/Sidebar.jsx"
replace_in_file(f, 'ring-white/10', 'ring-border-subtle')

# InstructorSidebar.jsx
f = "frontend/src/components/layout/InstructorSidebar.jsx"
replace_in_file(f, 'ring-white/10', 'ring-border-subtle')

# Statusbar.jsx
f = "frontend/src/components/layout/Statusbar.jsx"
replace_in_file(f, 'bg-white/30', 'bg-border-strong')

# StudentDashboard.jsx
f = "frontend/src/features/dashboard/StudentDashboard.jsx"
replace_in_file(f, 'hover:text-[#60a5fa]', 'hover:text-text-brand')
replace_in_file(f, 'bg-white/[0.06]', 'bg-border-subtle')
replace_in_file(f, 'bg-white/[0.01]', 'bg-bg-glass')

# MyClasses.jsx
f = "frontend/src/features/classes/MyClasses.jsx"
replace_in_file(f, 'bg-white/[0.06]', 'bg-border-subtle')

# ClassDetails.jsx
f = "frontend/src/features/classes/ClassDetails.jsx"
replace_in_file(f, 'bg-white/[0.06]', 'bg-border-subtle')

# Assignments.jsx
f = "frontend/src/features/assignments/Assignments.jsx"
replace_in_file(f, 'dark:text-black', 'dark:text-bg-base')
replace_in_file(f, 'border-violet-500/20 bg-violet-500/10 px-2.5 py-1 text-[10px] font-bold tracking-wide text-text-violet', 'border-border-subtle bg-bg-glass px-2.5 py-1 text-[10px] font-bold tracking-wide text-text-muted')

# Workspace.jsx
f = "frontend/src/features/workspace/Workspace.jsx"
replace_in_file(f, 'dark:text-black', 'dark:text-bg-base')
replace_in_file(f, 'hover:to-yellow-500', 'hover:to-psu-gold')

# SoloPractice.jsx
f = "frontend/src/features/practice/SoloPractice.jsx"
replace_in_file(f, 'bg-bg-alt text-text-muted border-border-subtle', 'bg-bg-panel text-text-muted border-border-subtle')

# InstructorDashboard.jsx
f = "frontend/src/features/dashboard/InstructorDashboard.jsx"
replace_in_file(f, 'bg-amber-500 text-white hover:bg-amber-400', 'bg-amber-500 text-bg-base hover:bg-amber-400')

# ActivityDetails.jsx
f = "frontend/src/features/instructor/ActivityDetails.jsx"
replace_in_file(f, 'bg-white/[0.06]', 'bg-border-subtle')
replace_in_file(f, 'bg-white/10', 'bg-border-strong')
replace_in_file(f, 'group-hover:bg-white/20', 'group-hover:bg-border-strong')
replace_in_file(f, 'peer-disabled:group-hover:bg-white/10', 'peer-disabled:group-hover:bg-border-subtle')
replace_in_file(f, 'after:bg-white', 'after:bg-bg-glass')

# ClassManagement.jsx
f = "frontend/src/features/instructor/ClassManagement.jsx"
replace_in_file(f, 'bg-white/5 text-text-muted hover:bg-red-500/10', 'bg-bg-glass text-text-muted hover:bg-red-500/10')

# SplitPaneGradingWorkspace.jsx
f = "frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx"
replace_in_file(f, 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border border-yellow-500/20', 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20')
replace_in_file(f, 'bg-[#0a0a0f]', 'bg-bg-base')

# Submissions.jsx
f = "frontend/src/features/submissions/Submissions.jsx"
replace_in_file(f, 'border-violet-500/30 bg-violet-500/10 text-violet-400', 'border-border-subtle bg-bg-glass text-text-muted')
replace_in_file(f, 'border-l-violet-500', 'border-l-border-strong')
replace_in_file(f, 'bg-white/[0.05]', 'bg-border-subtle')
replace_in_file(f, 'border-violet-500/20 bg-violet-500/10', 'border-border-subtle bg-bg-glass')
replace_in_file(f, 'border-violet-500/30 bg-violet-500/[0.05]', 'border-border-subtle bg-bg-glass')

# SubmissionDetails.jsx
f = "frontend/src/features/submissions/SubmissionDetails.jsx"
replace_in_file(f, 'dark:text-black', 'dark:text-bg-base')

# BulkEnrollModal.jsx
f = "frontend/src/components/modals/BulkEnrollModal.jsx"
replace_in_file(f, 'hover:text-white', 'hover:text-text-main')
replace_in_file(f, 'border-brand-primary', 'border-psu-maroon dark:border-psu-gold')
replace_in_file(f, 'text-brand-primary', 'text-text-brand')
replace_in_file(f, 'hover:border-brand-primary/50', 'hover:border-border-strong')
replace_in_file(f, 'focus:border-brand-primary', 'focus:border-border-strong')
replace_in_file(f, 'focus:ring-brand-primary', 'focus:ring-border-strong')
replace_in_file(f, 'bg-brand-primary', 'bg-psu-maroon text-white')
replace_in_file(f, 'hover:bg-brand-primary-hover', 'hover:bg-psu-maroon/90')
replace_in_file(f, 'text-white mb-2', 'text-text-main mb-2')

# CreateClassModal.jsx
f = "frontend/src/components/modals/CreateClassModal.jsx"
replace_in_file(f, 'bg-white/[0.06]', 'bg-border-subtle')

# Settings.jsx
f = "frontend/src/features/settings/Settings.jsx"
replace_in_file(f, 'to-[#2563eb]', 'to-psu-gold')
replace_in_file(f, 'bg-white/5', 'bg-border-subtle')

# AdminDashboard.jsx
f = "frontend/src/features/admin/AdminDashboard.jsx"
replace_in_file(f, 'dark:to-yellow-500', 'dark:to-psu-gold')
replace_in_file(f, 'from-slate-400 to-slate-300 dark:from-slate-600 dark:to-slate-500', 'from-border-subtle to-border-strong')
replace_in_file(f, 'border-emerald-500 bg-emerald-500/5', 'border-psu-gold bg-psu-gold/5')
replace_in_file(f, 'border-emerald-500', 'border-psu-gold')
replace_in_file(f, 'bg-emerald-500', 'bg-psu-gold')

print("All replacements attempted.")

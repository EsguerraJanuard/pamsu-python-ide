import os

replacements = {
    'border-white/[0.04]': 'border-border-subtle',
    'border-white/[0.05]': 'border-border-subtle',
    'border-white/[0.1]': 'border-border-strong',
    'border-white/[0.12]': 'border-border-strong',
    'border-white/[0.15]': 'border-border-strong',
    'border-white/[0.2]': 'border-border-strong',
    'text-slate-400': 'text-text-muted',
    'bg-slate-400/10': 'bg-border-subtle',
    'ring-slate-400/20': 'ring-border-strong',
    'bg-slate-500/10': 'bg-border-subtle',
    'ring-slate-500/5': 'ring-border-subtle',
    'hover:bg-black/60': 'hover:bg-bg-glass-hover',
    'hover:shadow-black/20': 'hover:shadow-border-strong',
    'shadow-black/20': 'shadow-border-strong'
}

base_dir = r"C:\Users\ACER\Documents\Codes\pamsu-python-ide\frontend\src"

files_to_check = [
    r"features\assignments\Assignments.jsx",
    r"features\classes\ClassDetails.jsx",
    r"features\classes\MyClasses.jsx",
    r"features\dashboard\StudentDashboard.jsx",
    r"features\instructor\ActivityEditor.jsx",
    r"features\instructor\GradingWorkspace.jsx",
    r"features\instructor\InstructorGradebook.jsx",
    r"features\instructor\LiveMonitoring.jsx",
    r"features\practice\SoloPractice.jsx",
    r"features\submissions\Submissions.jsx",
    r"features\workspace\Workspace.jsx",
    r"pages\AuditLogsPage.jsx"
]

for file_rel in files_to_check:
    file_path = os.path.join(base_dir, file_rel)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for k, v in replacements.items():
            new_content = new_content.replace(k, v)
            
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_rel}")

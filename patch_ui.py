import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replacements
    content = content.replace('text-white/80', 'text-text-main')
    content = content.replace('text-white', 'text-text-main')
    content = content.replace('text-slate-400', 'text-text-muted')
    content = content.replace('text-slate-500', 'text-text-muted')
    content = content.replace('bg-slate-900/50', 'bg-bg-glass')
    content = content.replace('bg-slate-900/30', 'bg-bg-panel')
    content = content.replace('hover:bg-slate-800/80', 'hover:bg-bg-glass-hover')
    content = content.replace('border-slate-800/50', 'border-border-subtle')
    content = content.replace('border-slate-800', 'border-border-subtle')
    content = content.replace('hover:border-slate-700', 'hover:border-border-hover')
    
    # GradingClassView specific
    content = content.replace('text-blue-400 hover:text-blue-300', 'text-text-muted hover:text-emerald-500')
    content = content.replace('bg-blue-600 hover:bg-blue-700 text-text-main', 'bg-emerald-600 hover:bg-emerald-500 text-white')
    content = content.replace('bg-blue-600 hover:bg-blue-700 text-white', 'bg-emerald-600 hover:bg-emerald-500 text-white')

    with open(filepath, 'w') as f:
        f.write(content)

process_file('frontend/src/features/instructor/grading/GradingBenchRoot.jsx')
process_file('frontend/src/features/instructor/grading/GradingClassView.jsx')

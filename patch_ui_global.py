import re
import glob

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generic Replacements
    content = content.replace('text-white/80', 'text-text-main')
    content = content.replace('text-slate-400', 'text-text-muted')
    content = content.replace('text-slate-500', 'text-text-muted')
    content = content.replace('text-gray-300', 'text-text-muted')
    content = content.replace('bg-slate-900/50', 'bg-bg-glass')
    content = content.replace('bg-slate-900/30', 'bg-bg-panel')
    content = content.replace('bg-slate-800/80', 'bg-bg-glass-hover')
    content = content.replace('hover:bg-slate-800/50', 'hover:bg-bg-glass')
    content = content.replace('hover:bg-slate-800/80', 'hover:bg-bg-glass-hover')
    content = content.replace('bg-[#0f1117]', 'bg-bg-base')
    content = content.replace('bg-[#0b0c10]', 'bg-bg-panel')
    content = content.replace('border-slate-800', 'border-border-subtle')
    content = content.replace('border-slate-700', 'border-border-subtle')
    content = content.replace('hover:border-slate-700', 'hover:border-border-hover')
    
    # Specific buttons and focuses
    content = content.replace('bg-blue-600 hover:bg-blue-500 text-white', 'bg-emerald-600 hover:bg-emerald-500 text-white')
    content = content.replace('bg-blue-600 hover:bg-blue-700 text-white', 'bg-emerald-600 hover:bg-emerald-500 text-white')
    content = content.replace('focus:border-blue-500', 'focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500')
    content = content.replace('text-blue-300', 'text-emerald-400')
    content = content.replace('text-blue-400 hover:text-blue-300', 'text-text-muted hover:text-emerald-500')

    # Replace text-white except when preceded by specific button classes
    content = content.replace('text-white', 'text-text-main')
    content = content.replace('bg-emerald-600 hover:bg-emerald-500 text-text-main', 'bg-emerald-600 hover:bg-emerald-500 text-white')
    content = content.replace('bg-emerald-600 px-6 py-3 font-semibold text-text-main', 'bg-emerald-600 px-6 py-3 font-semibold text-white')
    content = content.replace('bg-emerald-500 text-text-main', 'bg-emerald-500 text-white')
    content = content.replace('bg-violet-500 text-text-main', 'bg-violet-500 text-white')
    content = content.replace('bg-[#3b82f6] text-text-main', 'bg-blue-500 text-white')
    content = content.replace('bg-violet-600 px-4 py-1.5 text-sm font-semibold text-text-main', 'bg-violet-600 px-4 py-1.5 text-sm font-semibold text-white')
    content = content.replace('bg-violet-600 text-text-main', 'bg-violet-600 text-white')
    content = content.replace('text-text-main shadow-lg', 'text-white shadow-lg')
    content = content.replace('text-text-main shadow-sm', 'text-white shadow-sm')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

process_file('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx')
process_file('frontend/src/features/practice/PracticeWorkspace.jsx')
process_file('frontend/src/features/practice/SoloPractice.jsx')

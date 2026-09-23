import re

def rewrite_layout(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The typical structure in these files right now:
    # return (
    #   <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
    #     <InstructorSidebar />
    #     <div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto">
    #       <main className="min-h-screen p-8 bg-transparent">
    #         <div className="max-w-6xl mx-auto">

    old_layout_1 = '<div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto">'
    new_layout_1 = '<div className="animate-page-fade flex min-w-0 flex-1 flex-col">\n        <div className="flex min-h-0 flex-1">'
    
    old_layout_2 = '<main className="min-h-screen p-8 bg-transparent">'
    new_layout_2 = '<main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">'

    content = content.replace(old_layout_1, new_layout_1)
    content = content.replace(old_layout_2, new_layout_2)
    
    # We also need to add a closing </div> for new_layout_1.
    # Currently it ends with:
    #         </div>
    #       </main>
    #     </div>
    #   </div>
    # );
    
    content = content.replace('</main>\n      </div>\n    </div>', '</main>\n        </div>\n      </div>\n    </div>')

    # Card fixes
    if "GradingBenchRoot" in filepath:
        content = content.replace('className="group cursor-pointer bg-bg-glass hover:bg-bg-glass-hover transition-all duration-200 rounded-xl border border-border-subtle hover:border-emerald-500/50 overflow-hidden flex flex-col h-48"',
                                  'className="dashboard-card group cursor-pointer bg-bg-glass hover:bg-bg-glass-hover transition-all duration-200 rounded-xl border border-border-subtle hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10 overflow-hidden flex flex-col h-48"')
    elif "GradingClassView" in filepath:
        content = content.replace('className="p-6 border border-border-subtle rounded-lg mb-4 bg-bg-glass hover:bg-bg-glass-hover transition-colors flex justify-between items-center cursor-pointer"',
                                  'className="dashboard-card p-6 border border-border-subtle rounded-xl mb-4 bg-bg-glass hover:bg-bg-glass-hover hover:shadow-lg transition-all flex justify-between items-center cursor-pointer"')
        content = content.replace('className="p-6 border-b border-border-subtle bg-bg-glass mb-6 rounded-lg"',
                                  'className="dashboard-card p-8 border border-border-subtle bg-bg-glass mb-8 rounded-xl shadow-sm"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

rewrite_layout('frontend/src/features/instructor/grading/GradingBenchRoot.jsx')
rewrite_layout('frontend/src/features/instructor/grading/GradingClassView.jsx')

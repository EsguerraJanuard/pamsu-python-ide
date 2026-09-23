import re

# 1. Fix GradingBenchRoot Layout
filepath = 'frontend/src/features/instructor/grading/GradingBenchRoot.jsx'
with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('className="max-w-6xl mx-auto"', 'className="max-w-6xl mx-auto w-full"')
with open(filepath, 'w', encoding='utf-8') as f: f.write(content)

# 2. Fix GradingClassView Layout, UX, and Wording
filepath = 'frontend/src/features/instructor/grading/GradingClassView.jsx'
with open(filepath, 'r', encoding='utf-8') as f: content = f.read()

# Padding / Layout container
content = content.replace('className="max-w-4xl mx-auto animate-pulse"', 'className="max-w-6xl mx-auto w-full animate-pulse"')
content = content.replace('className="max-w-4xl mx-auto"', 'className="max-w-6xl mx-auto w-full"')

# Wording
content = content.replace('Back to Classes', 'Back to Class')

# Card UX Refactor
old_card = """<div 
                key={activity.task_id} 
                className="p-6 bg-bg-glass border border-border-subtle rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-border-hover transition-colors"
              >
                <div>
                  <h3 className="text-lg font-medium text-text-main">{activity.title}</h3>
                  <p className="text-sm text-text-muted mt-1">{activity.description || 'No description provided'}</p>
                  {activity.due_date && (
                    <p className="text-xs text-text-muted mt-2 font-mono">
                      Due: {new Date(activity.due_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="w-full sm:w-auto">
                  <button 
                    onClick={() => navigate(`/instructor/bench/${classId}/${activity.task_id}`)}
                    className="w-full sm:w-auto rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500"
                  >
                    View details &gt;
                  </button>
                </div>
              </div>"""

new_card = """<div 
                key={activity.task_id} 
                onClick={() => navigate(`/instructor/bench/${classId}/${activity.task_id}`)}
                className="p-6 bg-bg-glass border border-border-subtle rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-emerald-500/50 hover:shadow-lg cursor-pointer transition-all group relative overflow-hidden"
              >
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-transparent group-hover:bg-emerald-500 transition-colors"></div>
                <div>
                  <h3 className="text-lg font-bold text-text-main group-hover:text-emerald-400 transition-colors">{activity.title}</h3>
                  <p className="text-sm text-text-muted mt-1">{activity.description || 'No description provided'}</p>
                  {activity.due_date && (
                    <p className="text-xs text-text-muted mt-2 font-mono">
                      Due: {new Date(activity.due_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="w-full sm:w-auto">
                  <button 
                    className="w-full sm:w-auto rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-2 text-sm font-semibold transition group-hover:bg-emerald-600 group-hover:text-white group-hover:border-transparent group-hover:shadow-lg group-hover:shadow-emerald-500/20"
                  >
                    View details &gt;
                  </button>
                </div>
              </div>"""
content = content.replace(old_card, new_card)

with open(filepath, 'w', encoding='utf-8') as f: f.write(content)

# 3. Fix SplitPaneGradingWorkspace Layout and Green Accents
filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f: content = f.read()

# Layout wrapper: Replace `<div className="animate-page-fade flex min-w-0 flex-1 flex-col p-6 sm:p-8">` with the proper wrapper
old_layout_start_loading = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col p-6 sm:p-8">
          <div className="mb-6">"""
new_layout_start_loading = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8 flex flex-col">
              <div className="max-w-6xl mx-auto w-full flex-1 flex flex-col">
                <div className="mb-6">"""
content = content.replace(old_layout_start_loading, new_layout_start_loading)

old_layout_end_loading = """</div>
          </div>
        </div>
      </div>
    );"""
new_layout_end_loading = """</div>
              </div>
            </main>
          </div>
        </div>
      </div>
    );"""
content = content.replace(old_layout_end_loading, new_layout_end_loading)

old_layout_start_render = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col p-6 sm:p-8">
    <div className="mb-6 flex justify-between items-start shrink-0">"""
new_layout_start_render = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col">
    <div className="flex min-h-0 flex-1">
      <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8 flex flex-col">
        <div className="max-w-6xl mx-auto w-full flex-1 flex flex-col">
          <div className="mb-6 flex justify-between items-start shrink-0">"""
content = content.replace(old_layout_start_render, new_layout_start_render)

old_layout_end_render = """</div>
    </div>
  </div>
);"""
new_layout_end_render = """</div>
        </div>
      </main>
    </div>
  </div>
</div>
);"""
content = content.replace(old_layout_end_render, new_layout_end_render)

# Green accents for active student item
old_student_item = """<div 
                  key={student.student_id}
                  onClick={() => handleSelectStudent(student)}
                  className={`p-4 border-b border-border-subtle cursor-pointer hover:bg-bg-glass transition-colors flex justify-between items-center ${selectedStudent?.student_id === student.student_id ? 'bg-bg-glass-hover' : ''}`}
                >
                  <div>
                    <p className="font-medium text-text-main">{student.name || student.email || `Student ${student.student_id}`}</p>
                    <p className="text-sm text-text-muted">{student.email}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${badgeColor}`}>
                    {badgeText}
                  </span>
                </div>"""

new_student_item = """<div 
                  key={student.student_id}
                  onClick={() => handleSelectStudent(student)}
                  className={`p-4 border-b border-border-subtle cursor-pointer transition-all flex justify-between items-center relative group ${
                    selectedStudent?.student_id === student.student_id 
                      ? 'bg-emerald-500/5 hover:bg-emerald-500/10' 
                      : 'hover:bg-bg-glass'
                  }`}
                >
                  {selectedStudent?.student_id === student.student_id && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500 rounded-r shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                  )}
                  <div className="pl-1">
                    <p className={`font-medium transition-colors ${
                      selectedStudent?.student_id === student.student_id 
                        ? 'text-emerald-400' 
                        : 'text-text-main group-hover:text-emerald-400/80'
                    }`}>
                      {student.name || student.email || `Student ${student.student_id}`}
                    </p>
                    <p className="text-sm text-text-muted">{student.email}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${badgeColor}`}>
                    {badgeText}
                  </span>
                </div>"""
content = content.replace(old_student_item, new_student_item)

with open(filepath, 'w', encoding='utf-8') as f: f.write(content)

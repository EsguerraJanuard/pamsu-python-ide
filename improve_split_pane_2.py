import re

filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()


# 4. Add header to actual render state
old_render_inner = """  <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
    <div className="flex min-h-0 flex-1 flex-row">
      {/* Left Panel: Master List */}"""

new_render_inner = """  <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
    <header className="h-[72px] border-b border-border-subtle bg-bg-glass px-6 flex items-center justify-between shrink-0 shadow-sm z-10 relative">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2.5 -ml-3 rounded-lg text-text-muted hover:text-text-main hover:bg-white/5 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500/50">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </button>
        <div>
          <h1 className="font-semibold text-text-main text-lg leading-tight">Activity Grading Workspace</h1>
          <p className="text-xs text-text-muted font-mono mt-0.5">Class {classId} • Task {taskId}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button 
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-emerald-500/10 text-text-main hover:text-emerald-400 border border-border-subtle hover:border-emerald-500/30 rounded-lg text-sm font-medium transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export Grades
        </button>
      </div>
    </header>
    <div className="flex min-h-0 flex-1 flex-row">
      {/* Left Panel: Master List */}"""
content = content.replace(old_render_inner, new_render_inner)

# Remove the old Export button from the left panel header since we moved it to the top bar
old_left_header = """<div className="p-4 border-b border-border-subtle flex justify-between items-center bg-bg-glass">
          <h2 className="text-lg font-semibold text-text-main">Students</h2>
          <button 
            onClick={handleExport}
            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-sm transition-colors"
          >
            Export Submissions
          </button>
        </div>"""

new_left_header = """<div className="px-5 py-4 border-b border-border-subtle flex justify-between items-center bg-bg-glass shadow-sm z-0">
          <h2 className="text-sm font-bold tracking-wider text-text-muted uppercase">Student Submissions</h2>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">{students.length}</span>
        </div>"""
content = content.replace(old_left_header, new_left_header)

# Make right panel look nicer and more contained
old_right_empty = """<div className="flex-1 flex items-center justify-center text-text-muted">
            Select a student from the left panel to view their submission.
          </div>"""

new_right_empty = """<div className="flex-1 flex flex-col items-center justify-center text-text-muted bg-bg-base bg-blend-overlay">
            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4 border border-border-subtle shadow-lg">
              <svg className="w-8 h-8 text-emerald-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
            </div>
            <h3 className="text-lg font-medium text-text-main mb-1">No Submission Selected</h3>
            <p className="text-sm max-w-sm text-center">Select a student from the left panel to review their code and provide a grade.</p>
          </div>"""
content = content.replace(old_right_empty, new_right_empty)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

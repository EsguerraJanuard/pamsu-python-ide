import re

filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Loading header
old_loading_header = """<header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between shrink-0">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <button onClick={() => navigate(-1)} className="text-text-muted hover:text-text-emerald transition-colors" title="Go back">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                </button>
                <p className="font-mono text-xs font-semibold tracking-wider text-text-emerald uppercase">MONITORING & GRADING</p>
              </div>
              <h1 className="text-2xl font-bold">Activity Grading Workspace</h1>
              <p className="mt-1 text-sm text-text-muted">
                Task ID: {taskId} • Loading data...
              </p>
            </div>
          </header>"""

new_loading_header = """<div className="mb-6">
            <button onClick={() => navigate(-1)} className="text-sm text-text-muted hover:text-text-main flex items-center gap-2 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
              Back to Class
            </button>
          </div>
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-text-main mb-2">Activity Grading Workspace</h1>
            <p className="text-text-muted">Task ID: {taskId} • Loading data...</p>
          </header>"""
content = content.replace(old_loading_header, new_loading_header)


# Replace Render header
old_render_header = """<header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between shrink-0">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <button onClick={() => navigate(-1)} className="text-text-muted hover:text-text-emerald transition-colors" title="Go back">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          </button>
          <p className="font-mono text-xs font-semibold tracking-wider text-text-emerald uppercase">MONITORING & GRADING</p>
        </div>
        <h1 className="text-2xl font-bold">Activity Grading Workspace</h1>
        <p className="mt-1 text-sm text-text-muted">
          Class {classId} • Task {taskId}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button 
          onClick={handleExport}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-lg transition-all hover:bg-emerald-500 hover:shadow-emerald-500/20 active:scale-95 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export Grades
        </button>
      </div>
    </header>"""


new_render_header = """<div className="mb-6 flex justify-between items-start shrink-0">
      <div>
        <button onClick={() => navigate(-1)} className="text-sm text-text-muted hover:text-text-main flex items-center gap-2 transition-colors mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Back to Class
        </button>
        <header className="mb-4">
          <h1 className="text-3xl font-bold text-text-main mb-2">Activity Grading Workspace</h1>
          <p className="text-text-muted">Class {classId} • Task {taskId}</p>
        </header>
      </div>
      <div className="mt-10">
        <button 
          onClick={handleExport}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:bg-emerald-500 hover:shadow-emerald-500/20 active:scale-95 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export Grades
        </button>
      </div>
    </div>"""

content = content.replace(old_render_header, new_render_header)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

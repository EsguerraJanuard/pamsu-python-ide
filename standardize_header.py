import re

filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_loading_header = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <header className="h-[72px] border-b border-border-subtle bg-bg-glass px-6 flex items-center justify-between shrink-0 shadow-sm z-10 relative">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate(-1)} className="p-2.5 -ml-3 rounded-lg text-text-muted hover:text-text-main hover:bg-white/5 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500/50">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
              </button>
              <div>
                <h1 className="font-semibold text-text-main text-lg leading-tight">Activity Grading Workspace</h1>
                <p className="text-xs text-text-muted font-mono mt-0.5">Task ID: {taskId} • Loading data...</p>
              </div>
            </div>
          </header>
          <div className="flex min-h-0 flex-1 flex-row">"""

new_loading_header = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col p-6 sm:p-8">
          <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between shrink-0">
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
          </header>
          <div className="flex min-h-0 flex-1 flex-row border border-border-subtle rounded-xl overflow-hidden shadow-sm">"""

content = content.replace(old_loading_header, new_loading_header)


old_render_header = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col">
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
    <div className="flex min-h-0 flex-1 flex-row">"""


new_render_header = """<div className="animate-page-fade flex min-w-0 flex-1 flex-col p-6 sm:p-8">
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between shrink-0">
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
    </header>
    <div className="flex min-h-0 flex-1 flex-row border border-border-subtle rounded-xl overflow-hidden shadow-sm bg-bg-base">"""
content = content.replace(old_render_header, new_render_header)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

import re

filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace loading return
old_loading = 'return <div className="p-6 text-text-main bg-bg-base h-screen">Loading workspace...</div>;'
new_loading = """return (
  <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
    <InstructorSidebar />
    <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading workspace...</p>
        </div>
      </div>
    </div>
  </div>
);"""
content = content.replace(old_loading, new_loading)

# Replace main return wrapper
old_return_start = '<div className="flex flex-row h-screen bg-bg-base text-text-main">'
new_return_start = """<div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
  <InstructorSidebar />
  <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
    <div className="flex min-h-0 flex-1 flex-row">"""
content = content.replace(old_return_start, new_return_start)

# Add closing divs to the end of main return
old_return_end = """        )}
      </div>
    
      <AlertModal """

new_return_end = """        )}
      </div>
    </div>
  </div>
  <AlertModal """
content = content.replace(old_return_end, new_return_end)

# Also change left panel background from bg-bg-base to bg-bg-panel/50 to make it contrast with right panel
content = content.replace('<div className="w-1/3 border-r border-border-subtle flex flex-col bg-bg-base">', '<div className="w-1/3 border-r border-border-subtle flex flex-col bg-bg-panel/30">')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

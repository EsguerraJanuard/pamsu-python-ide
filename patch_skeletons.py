import re

def replace_loading_bench():
    filepath = 'frontend/src/features/instructor/grading/GradingBenchRoot.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    old_code = r"""if \(loading\) \{
    return \(
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="flex min-w-0 flex-1 items-center justify-center min-h-screen text-text-main bg-transparent">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading classes...</p>
        </div>
      </div>
      </div>
    \);
  \}"""
    
    new_code = """if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
              <div className="max-w-6xl mx-auto">
                <header className="mb-8 animate-pulse">
                  <div className="h-8 bg-border-subtle rounded w-48 mb-4"></div>
                  <div className="h-4 bg-border-subtle rounded w-72"></div>
                </header>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div key={i} className="dashboard-card bg-bg-glass rounded-xl border border-border-subtle overflow-hidden flex flex-col h-48 animate-pulse">
                      <div className="p-6 flex-grow">
                        <div className="h-6 bg-border-subtle rounded w-3/4 mb-4"></div>
                        <div className="h-4 bg-border-subtle rounded w-full mb-2"></div>
                        <div className="h-4 bg-border-subtle rounded w-2/3"></div>
                      </div>
                      <div className="px-6 py-4 border-t border-border-subtle bg-bg-panel flex justify-between items-center">
                        <div className="h-4 bg-border-subtle rounded w-32"></div>
                        <div className="h-5 w-5 bg-border-subtle rounded-full"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>
    );
  }"""
    
    content = re.sub(old_code, new_code, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def replace_loading_class_view():
    filepath = 'frontend/src/features/instructor/grading/GradingClassView.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = r"""if \(loading\) \{
    return \(<div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none"><InstructorSidebar /><div className="flex min-w-0 flex-1 items-center justify-center min-h-screen text-text-main bg-transparent">Loading class details...</div></div>\);
  \}"""

    new_code = """if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
              <div className="max-w-4xl mx-auto animate-pulse">
                <div className="w-24 h-4 bg-border-subtle rounded mb-6"></div>
                <div className="dashboard-card p-8 border border-border-subtle bg-bg-glass mb-8 rounded-xl shadow-sm">
                  <div className="h-8 bg-border-subtle rounded w-64 mb-4"></div>
                  <div className="h-4 bg-border-subtle rounded w-48"></div>
                </div>
                <div className="h-6 bg-border-subtle rounded w-32 mb-6"></div>
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="dashboard-card p-6 border border-border-subtle rounded-xl bg-bg-glass flex justify-between items-center">
                      <div className="flex-1">
                        <div className="h-6 bg-border-subtle rounded w-48 mb-2"></div>
                        <div className="h-4 bg-border-subtle rounded w-1/3"></div>
                      </div>
                      <div className="w-28 h-10 bg-border-subtle rounded-lg"></div>
                    </div>
                  ))}
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>
    );
  }"""
  
    content = re.sub(old_code, new_code, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def replace_loading_split_pane():
    filepath = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = r"""if \(loading\) \{
    return \(
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
\);
  \}"""

    new_code = """if (loading) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
          <div className="flex min-h-0 flex-1 flex-row">
            {/* Left Panel Skeleton */}
            <div className="w-1/3 border-r border-border-subtle flex flex-col bg-bg-panel/30">
              <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-bg-glass animate-pulse">
                <div className="h-6 bg-border-subtle rounded w-24"></div>
                <div className="h-8 bg-border-subtle rounded w-32"></div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-4 animate-pulse">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="p-4 border border-border-subtle rounded-lg flex justify-between items-center">
                    <div>
                      <div className="h-5 bg-border-subtle rounded w-32 mb-2"></div>
                      <div className="h-4 bg-border-subtle rounded w-40"></div>
                    </div>
                    <div className="h-6 w-16 bg-border-subtle rounded-full"></div>
                  </div>
                ))}
              </div>
            </div>
            {/* Right Panel Skeleton */}
            <div className="w-2/3 p-6 flex flex-col gap-6 bg-bg-base animate-pulse">
              <div className="h-8 bg-border-subtle rounded w-64 mb-4"></div>
              <div className="bg-bg-glass border border-border-subtle rounded-lg p-4 h-64">
                <div className="h-6 bg-border-subtle rounded w-40 mb-4"></div>
                <div className="h-4 bg-border-subtle rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-border-subtle rounded w-1/2"></div>
              </div>
              <div className="bg-bg-glass border border-border-subtle rounded-lg p-4 h-48">
                <div className="h-6 bg-border-subtle rounded w-48 mb-4"></div>
                <div className="h-4 bg-border-subtle rounded w-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }"""
  
    content = re.sub(old_code, new_code, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replace_loading_bench()
replace_loading_class_view()
replace_loading_split_pane()

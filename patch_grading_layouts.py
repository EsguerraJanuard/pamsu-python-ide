import re

def add_layout(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add TopNav import if not present
    if "TopNav" not in content:
        content = content.replace(
            "import InstructorSidebar from '../../../components/layout/InstructorSidebar';", 
            "import InstructorSidebar from '../../../components/layout/InstructorSidebar';\nimport { TopNav } from '../../../components/layout/TopNav';"
        )
    
    # State for sidebar if not present
    if "const [isSidebarOpen" not in content:
        content = re.sub(
            r"(const \[[a-zA-Z]+, set[a-zA-Z]+\] = useState\([^)]*\);)",
            r"\1\n  const [isSidebarOpen, setIsSidebarOpen] = useState(true);",
            content,
            count=1
        )
    
    # Update InstructorSidebar
    content = content.replace(
        "<InstructorSidebar />",
        "<InstructorSidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />"
    )

    # Add TopNav before <main> or <div className="flex-1 ... overflow-y-auto">
    if "<TopNav" not in content:
        content = re.sub(
            r'(<div className="flex min-w-0 flex-1 flex-col overflow-y-auto">)',
            r'\1\n        <TopNav toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />',
            content
        )
        content = re.sub(
            r'(<div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto">)',
            r'\1\n        <TopNav toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />',
            content
        )

    # For SplitPane, it doesn't have the standard flex layout wrapper at all!
    if "SplitPaneGradingWorkspace.jsx" in filepath:
        # It currently starts with <div className="flex flex-row h-screen bg-bg-base text-text-main">
        old_return = '<div className="flex flex-row h-screen bg-bg-base text-text-main">'
        new_return = """<div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto">
        <TopNav toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
        <main className="flex-1 flex flex-row h-full">"""
        content = content.replace(old_return, new_return)
        
        # We need to close the tags at the bottom.
        # Find the AlertModal and the closing </div>
        content = content.replace('      <AlertModal ', '        </main>\n      </div>\n      <AlertModal ')
        
        # Also need to add InstructorSidebar and TopNav to loading states
        old_loading = 'return <div className="p-6 text-text-main bg-bg-base h-screen">Loading workspace...</div>;'
        new_loading = """return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
        <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
          <TopNav toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
          <div className="p-6 text-text-main bg-bg-base flex-1">Loading workspace...</div>
        </div>
      </div>
    );"""
        content = content.replace(old_loading, new_loading)

    # Refine GradingBenchRoot card
    if "GradingBenchRoot.jsx" in filepath:
        old_card = 'className="group cursor-pointer bg-bg-glass hover:bg-bg-glass-hover transition-all duration-200 rounded-xl border border-border-subtle hover:border-emerald-500/50 overflow-hidden flex flex-col h-48"'
        new_card = 'className="dashboard-card group cursor-pointer bg-bg-glass hover:bg-bg-glass-hover transition-all duration-200 rounded-xl border border-border-subtle hover:border-emerald-500/50 overflow-hidden flex flex-col h-48 shadow-sm"'
        content = content.replace(old_card, new_card)

    # Refine GradingClassView card
    if "GradingClassView.jsx" in filepath:
        old_card = 'className="p-6 border border-border-subtle rounded-lg mb-4 bg-bg-glass hover:bg-bg-glass-hover transition-colors flex justify-between items-center cursor-pointer"'
        new_card = 'className="dashboard-card p-6 border border-border-subtle rounded-xl mb-4 bg-bg-glass hover:bg-bg-glass-hover transition-all flex justify-between items-center cursor-pointer shadow-sm"'
        content = content.replace(old_card, new_card)
        old_header = 'className="p-6 border-b border-border-subtle bg-bg-glass mb-6 rounded-lg"'
        new_header = 'className="p-8 border border-border-subtle bg-bg-glass mb-8 rounded-xl shadow-sm dashboard-card"'
        content = content.replace(old_header, new_header)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

add_layout('frontend/src/features/instructor/grading/GradingBenchRoot.jsx')
add_layout('frontend/src/features/instructor/grading/GradingClassView.jsx')
add_layout('frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx')

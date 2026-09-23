import os

def patch_workspace(filepath, is_practice=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Imports
    if "import ReactMarkdown from 'react-markdown'" not in content:
        content = content.replace(
            'import { useTheme } from "../theme/ThemeContext";',
            'import { useTheme } from "../theme/ThemeContext";\nimport ReactMarkdown from "react-markdown";\nimport remarkGfm from "remark-gfm";'
        )

    # 2. Add state
    if 'const [viewMode, setViewMode] = useState("lesson");' not in content:
        content = content.replace(
            'const [loading, setLoading] = useState(true);',
            'const [loading, setLoading] = useState(true);\n  const [viewMode, setViewMode] = useState("lesson");'
        )

    # 3. Replace simple text rendering with ReactMarkdown
    old_instructions = """<div className="prose prose-invert prose-sm max-w-none text-text-main whitespace-pre-wrap">
              {taskDetails.instructions}
            </div>"""
    new_instructions = """<div className="prose prose-invert prose-sm max-w-none text-text-main">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{taskDetails.instructions || ''}</ReactMarkdown>
            </div>"""
    content = content.replace(old_instructions, new_instructions)

    # 4. Insert Lesson View logic
    # Right before `return (` for the main render (after `if (!taskDetails) { ... }`)
    lesson_view = """
  if (viewMode === "lesson") {
    return (
      <div className="flex h-screen flex-col overflow-hidden bg-bg-base text-text-main">
        <header className="flex h-14 shrink-0 items-center border-b border-border-subtle bg-bg-base px-4">
          <button 
            onClick={() => navigate("/student/practice")}
            className="flex items-center gap-2 rounded-md px-2 py-1 text-sm font-medium text-text-muted hover:bg-bg-alt hover:text-text-main transition-colors"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Modules
          </button>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-12 flex justify-center animate-fade-in">
          <div className="max-w-3xl w-full">
            <div className="mb-4 inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
              Lesson
            </div>
            <h1 className="text-4xl font-extrabold mb-8 text-text-main tracking-tight">{taskDetails.title}</h1>
            
            <div className="prose prose-invert prose-emerald max-w-none mb-12">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{taskDetails.instructions || 'No instructions provided.'}</ReactMarkdown>
            </div>
            
            <div className="border-t border-border-subtle pt-8 flex justify-end pb-24">
              <button 
                onClick={() => setViewMode("coding")} 
                className="flex items-center gap-2 rounded-xl bg-violet-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-violet-500/20 transition-all hover:bg-violet-500 hover:scale-[1.02]"
              >
                Start Coding Challenge
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }
"""
    # Find the main return
    main_return_idx = content.find('  return (\n    <div className="flex h-screen flex-col')
    if main_return_idx != -1 and 'if (viewMode === "lesson")' not in content:
        content = content[:main_return_idx] + lesson_view + content[main_return_idx:]

    # 5. Add "Back to Lesson" button in split pane
    back_btn = """<h2 className="text-lg font-bold text-text-main">Instructions</h2>
              <button onClick={() => setViewMode("lesson")} className="text-xs text-violet-400 hover:text-violet-300 font-medium">Read Full Lesson</button>"""
    
    content = content.replace('<h2 className="mb-4 text-lg font-bold text-text-main border-b border-border-subtle pb-2">Instructions</h2>',
        '<div className="mb-4 flex items-center justify-between border-b border-border-subtle pb-2">' + back_btn + '</div>')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_workspace('frontend/src/features/practice/PracticeWorkspace.jsx', is_practice=True)

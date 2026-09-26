with open("frontend/src/features/practice/PracticeWorkspace.jsx", "r") as f:
    lines = f.read().split('\n')

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if '<p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>' in line:
        start_idx = i
        break

for i in range(start_idx, len(lines)):
    if '{feedback.ast_feedback' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    good_block = """
                <p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>
                {feedback.is_successful && (
                  nextTaskId ? (
                    <button
                      onClick={() => {
                        setTaskDetails(null);
                        setFeedback(null);
                        setAiHint(null);
                        setCode("");
                        navigate(`/student/practice/workspace?task=${nextTaskId}`);
                      }}
                      className="mt-2 w-full flex justify-center items-center gap-2 rounded-md bg-emerald-600 px-6 py-2.5 text-sm font-bold text-white shadow-lg transition-all hover:bg-emerald-500 hover:-translate-y-0.5 active:translate-y-0"
                    >
                      Proceed to Next Task
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate('/student/practice')}
                      className="mt-2 w-full flex justify-center items-center gap-2 rounded-md bg-slate-700 px-6 py-2.5 text-sm font-bold text-white shadow-lg transition-all hover:bg-slate-600 hover:-translate-y-0.5 active:translate-y-0"
                    >
                      Module Complete! Return to Modules
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                    </button>
                  )
                )}
"""
    new_lines = lines[:start_idx] + good_block.strip('\n').split('\n') + lines[end_idx:]
    with open("frontend/src/features/practice/PracticeWorkspace.jsx", "w") as f:
        f.write('\n'.join(new_lines))
    print("Fixed buttons array slicing")

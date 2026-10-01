import re

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "r") as f:
    content = f.read()

replacement = """
                <p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>
                {feedback.is_successful && nextTaskId && (
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
                )}
"""

# Find the exact `<p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>` and replace it
content = content.replace('<p className="text-sm font-medium mb-4">{feedback.message}</p>', replacement)
content = content.replace('<p className="text-sm font-medium mb-4 text-text-main">{feedback.message}</p>', replacement)

with open("frontend/src/features/practice/PracticeWorkspace.jsx", "w") as f:
    f.write(content)
print("Updated Workspace feedback UI")

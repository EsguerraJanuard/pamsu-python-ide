with open('frontend/src/features/practice/PracticeWorkspace.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

target = """{feedback?.is_successful && nextTaskId && (
              <button
                onClick={() => {
                  setTaskDetails(null); // trigger re-fetch/loading
                  setFeedback(null);
                  setAiHint(null);
                  setCode("");
                  navigate(`/student/practice/workspace?task=${nextTaskId}`);
                }}
                className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-emerald-500"
              >
                Next Task ?
              </button>
            )}"""

c = c.replace(target, "")

with open('frontend/src/features/practice/PracticeWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
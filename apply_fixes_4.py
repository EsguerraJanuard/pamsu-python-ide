import re

# Fix GradingClassView
filepath = 'frontend/src/features/instructor/grading/GradingClassView.jsx'
with open(filepath, 'r', encoding='utf-8') as f: content = f.read()

# Add error state
old_state = """  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);"""
new_state = """  const [classroom, setClassroom] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);"""
content = content.replace(old_state, new_state)

# Fix fetchData
old_fetch = """        const tasksRes = await api.get('/instructors/tasks/');
        // Filter by class_id
        const filteredTasks = tasksRes.filter(task => String(task.class_id) === String(classId));
        setActivities(filteredTasks);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {"""
new_fetch = """        const tasksRes = await api.get('/instructors/tasks/');
        // Filter by class_id
        const safeTasks = Array.isArray(tasksRes) ? tasksRes : (tasksRes?.data || []);
        const filteredTasks = safeTasks.filter(task => String(task.class_id) === String(classId));
        setActivities(filteredTasks);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error?.message || 'Failed to load class data from server.');
      } finally {"""
content = content.replace(old_fetch, new_fetch)

# Fix error render
old_error_render = """  if (!classroom) {
    return (<div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none"><InstructorSidebar /><div className="flex min-w-0 flex-1 items-center justify-center min-h-screen text-red-400 bg-transparent">Class not found.</div></div>);
  }"""
new_error_render = """  if (error || !classroom) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
        <InstructorSidebar />
        <div className="flex min-w-0 flex-1 flex-col items-center justify-center text-center p-8">
          <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mb-4 border border-red-500/20">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          </div>
          <h2 className="text-xl font-bold text-red-400 mb-2">Failed to load class</h2>
          <p className="text-text-muted max-w-md">{error || "The class could not be found or you don't have access to it."}</p>
          <button onClick={() => navigate('/instructor/bench')} className="mt-6 px-4 py-2 bg-bg-panel hover:bg-bg-glass border border-border-subtle rounded-lg text-text-main transition-colors">
            Back to Grading Bench
          </button>
        </div>
      </div>
    );
  }"""
content = content.replace(old_error_render, new_error_render)

# Wording
content = content.replace('Back to Class\n        </button>', 'Back to Classes\n        </button>')

with open(filepath, 'w', encoding='utf-8') as f: f.write(content)

# Fix SplitPaneGradingWorkspace Wording
filepath_split = 'frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx'
with open(filepath_split, 'r', encoding='utf-8') as f: split_content = f.read()
split_content = split_content.replace('Back to Class\n            </button>', 'Back to Activities\n            </button>')
split_content = split_content.replace('Back to Class\n        </button>', 'Back to Activities\n        </button>')
with open(filepath_split, 'w', encoding='utf-8') as f: f.write(split_content)

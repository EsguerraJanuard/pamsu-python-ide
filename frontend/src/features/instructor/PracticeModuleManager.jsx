import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from '../../components/layout/InstructorSidebar';

export default function PracticeModuleManager() {
  const navigate = useNavigate();
  const [modules, setModules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [isModuleModalOpen, setIsModuleModalOpen] = useState(false);
  const [editingModule, setEditingModule] = useState(null);
  
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [selectedModuleId, setSelectedModuleId] = useState(null);

  // Form states
  const [moduleForm, setModuleForm] = useState({ title: '', description: '', order_index: 0 });
  const [taskForm, setTaskForm] = useState({ 
    title: '', instructions: '', starter_code: '', expected_output: '', order_index: 0, expected_ast_patterns: ''
  });

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    try {
      setIsLoading(true);
      const data = await api.get('/practice/instructor/modules');
      setModules(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch modules');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModuleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingModule) {
        await api.put(`/practice/modules/${editingModule.module_id}`, moduleForm);
      } else {
        await api.post('/practice/modules', moduleForm);
      }
      setIsModuleModalOpen(false);
      fetchModules();
    } catch (err) {
      alert(err.message || 'Failed to save module');
    }
  };

  const handleDeleteModule = async (moduleId) => {
    if (!confirm('Are you sure you want to delete this module and ALL its tasks?')) return;
    try {
      await api.delete(`/practice/modules/${moduleId}`);
      fetchModules();
    } catch (err) {
      alert(err.message || 'Failed to delete module');
    }
  };

  const handleTaskSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...taskForm,
        expected_ast_patterns: taskForm.expected_ast_patterns ? JSON.parse(taskForm.expected_ast_patterns) : null
      };

      if (editingTask) {
        await api.put(`/practice/tasks/${editingTask.task_id}`, payload);
      } else {
        await api.post(`/practice/modules/${selectedModuleId}/tasks`, payload);
      }
      setIsTaskModalOpen(false);
      fetchModules();
    } catch (err) {
      alert(err.message || 'Failed to save task (check JSON formatting)');
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.delete(`/practice/tasks/${taskId}`);
      fetchModules();
    } catch (err) {
      alert(err.message || 'Failed to delete task');
    }
  };

  const openModuleModal = (mod = null) => {
    if (mod) {
      setEditingModule(mod);
      setModuleForm({ title: mod.title, description: mod.description || '', order_index: mod.order_index });
    } else {
      setEditingModule(null);
      setModuleForm({ title: '', description: '', order_index: modules.length });
    }
    setIsModuleModalOpen(true);
  };

  const openTaskModal = (moduleId, task = null) => {
    setSelectedModuleId(moduleId);
    if (task) {
      setEditingTask(task);
      setTaskForm({
        title: task.title,
        instructions: task.instructions,
        starter_code: task.starter_code || '',
        expected_output: task.expected_output,
        order_index: task.order_index,
        expected_ast_patterns: task.expected_ast_patterns ? JSON.stringify(task.expected_ast_patterns, null, 2) : ''
      });
    } else {
      setEditingTask(null);
      const mod = modules.find(m => m.module_id === moduleId);
      setTaskForm({
        title: '',
        instructions: '',
        starter_code: '',
        expected_output: '',
        order_index: mod ? mod.tasks.length : 0,
        expected_ast_patterns: ''
      });
    }
    setIsTaskModalOpen(true);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto bg-bg-base p-6 sm:p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-6">
            <div>
              <h1 className="text-2xl font-bold text-text-main">Practice Modules</h1>
              <p className="mt-1 text-sm text-text-muted">
                Manage solo practice modules and tasks for students.
              </p>
            </div>
            <button
              onClick={() => openModuleModal()}
              className="rounded-lg bg-brand-primary px-4 py-2 text-xs font-semibold text-white shadow transition hover:bg-brand-primary-hover"
            >
              + Create Module
            </button>
          </header>

          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-primary border-t-transparent"></div>
            </div>
          ) : error ? (
            <div className="rounded-lg bg-red-900/20 p-4 text-red-400 border border-red-900/50">
              {error}
            </div>
          ) : (
            <div className="space-y-6">
              {modules.map((mod) => (
                <div key={mod.module_id} className="rounded-xl border border-border-subtle bg-bg-panel p-6 shadow-sm">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-lg font-bold text-text-main">
                        {mod.order_index}. {mod.title}
                        {mod.instructor_id === null && (
                          <span className="ml-2 rounded-full bg-brand-primary/20 px-2 py-0.5 text-xs text-brand-primary">
                            Default Seeded
                          </span>
                        )}
                      </h2>
                      {mod.description && <p className="text-sm text-text-muted mt-1">{mod.description}</p>}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openModuleModal(mod)}
                        className="rounded bg-bg-glass px-3 py-1.5 text-xs font-medium text-text-main hover:bg-bg-glass-hover"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteModule(mod.module_id)}
                        className="rounded bg-red-900/20 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-900/40"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {mod.tasks.map((task) => (
                      <div key={task.task_id} className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-base p-4">
                        <div>
                          <h3 className="font-semibold text-text-main text-sm">{task.order_index}. {task.title}</h3>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => openTaskModal(mod.module_id, task)}
                            className="text-xs text-text-muted hover:text-brand-primary"
                          >
                            Edit Task
                          </button>
                          <button
                            onClick={() => handleDeleteTask(task.task_id)}
                            className="text-xs text-text-muted hover:text-red-400"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                    <button
                      onClick={() => openTaskModal(mod.module_id)}
                      className="w-full flex items-center justify-center gap-2 rounded-lg border border-dashed border-border-subtle p-3 text-sm text-text-muted hover:border-brand-primary hover:text-brand-primary transition"
                    >
                      + Add Task
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Module Modal */}
      {isModuleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-panel p-6 shadow-2xl">
            <h2 className="mb-4 text-lg font-bold text-text-main">
              {editingModule ? 'Edit Module' : 'Create Module'}
            </h2>
            <form onSubmit={handleModuleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Title</label>
                <input required type="text" value={moduleForm.title} onChange={e => setModuleForm({...moduleForm, title: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary" />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Description</label>
                <textarea value={moduleForm.description} onChange={e => setModuleForm({...moduleForm, description: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary" rows="3" />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Order Index</label>
                <input required type="number" value={moduleForm.order_index} onChange={e => setModuleForm({...moduleForm, order_index: parseInt(e.target.value)})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary" />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setIsModuleModalOpen(false)} className="rounded-lg bg-bg-glass px-4 py-2 text-sm text-text-main hover:bg-bg-glass-hover">Cancel</button>
                <button type="submit" className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white hover:bg-brand-primary-hover">Save Module</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Task Modal */}
      {isTaskModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-border-subtle bg-bg-panel p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="mb-4 text-lg font-bold text-text-main">
              {editingTask ? 'Edit Task' : 'Create Task'}
            </h2>
            <form onSubmit={handleTaskSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Title</label>
                  <input required type="text" value={taskForm.title} onChange={e => setTaskForm({...taskForm, title: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Order Index</label>
                  <input required type="number" value={taskForm.order_index} onChange={e => setTaskForm({...taskForm, order_index: parseInt(e.target.value)})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none" />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Instructions (Markdown)</label>
                <textarea required value={taskForm.instructions} onChange={e => setTaskForm({...taskForm, instructions: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none font-mono" rows="4" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Starter Code</label>
                  <textarea value={taskForm.starter_code} onChange={e => setTaskForm({...taskForm, starter_code: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none font-mono" rows="5" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Expected Output (Exact string)</label>
                  <textarea required value={taskForm.expected_output} onChange={e => setTaskForm({...taskForm, expected_output: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none font-mono" rows="5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Expected AST Patterns (JSON format)</label>
                <textarea value={taskForm.expected_ast_patterns} onChange={e => setTaskForm({...taskForm, expected_ast_patterns: e.target.value})} className="w-full rounded-lg border border-border-subtle bg-bg-base p-2 text-sm text-text-main focus:border-brand-primary focus:outline-none font-mono" rows="5" placeholder='{"FunctionDef": 1}' />
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setIsTaskModalOpen(false)} className="rounded-lg bg-bg-glass px-4 py-2 text-sm text-text-main hover:bg-bg-glass-hover">Cancel</button>
                <button type="submit" className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white hover:bg-brand-primary-hover">Save Task</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

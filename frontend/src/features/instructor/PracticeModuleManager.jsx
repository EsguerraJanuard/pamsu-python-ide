import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from '../../components/layout/InstructorSidebar';
import AlertModal from '../../components/modals/AlertModal';
import ConfirmationModal from '../../components/modals/ConfirmationModal';



function InfoTooltip({ title, children, align = 'left', position = 'bottom' }) {
  const [isOpen, setIsOpen] = useState(false);
  
  // Determine alignment classes to prevent horizontal clipping
  const alignmentClass = align === 'center' 
    ? 'left-1/2 -translate-x-1/2' 
    : align === 'right' 
      ? 'right-0' 
      : 'left-0';

  // Determine vertical positioning to prevent vertical clipping in scrollable modals
  const positionStyle = position === 'top' 
    ? { bottom: '100%', marginBottom: '0.5rem' } 
    : { top: '100%', marginTop: '0.5rem' };

  return (
    <div className="relative inline-flex items-center ml-2 align-middle">
      <button 
        type="button"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onClick={(e) => { e.preventDefault(); setIsOpen(!isOpen); }}
        className="text-text-muted hover:text-emerald-400 focus:outline-none transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
      
      {isOpen && (
        <div 
          className={`absolute w-64 md:w-80 p-4 bg-bg-panel border border-border-subtle rounded-lg shadow-2xl z-50 text-xs font-normal normal-case text-text-main leading-relaxed ${alignmentClass}`} 
          style={positionStyle}
        >
          <div className="font-bold text-emerald-400 mb-2 border-b border-border-subtle pb-1">{title}</div>
          {children}
        </div>
      )}
    </div>
  );
}


const AST_GROUPS = [
  {
    title: "Output & Input",
    rules: [
      { id: "require_print_call", label: "Require print() call" },
      { id: "require_input_call", label: "Require input() call" }
    ]
  },
  {
    title: "Control Flow",
    rules: [
      { id: "require_if_statement", label: "Require if statement" },
      { id: "require_for_loop", label: "Require for loop" },
      { id: "require_while_loop", label: "Require while loop" },
      { id: "require_break_statement", label: "Require break statement" },
      { id: "require_continue_statement", label: "Require continue statement" },
      { id: "require_with_statement", label: "Require with statement" },
      { id: "require_pass_statement", label: "Require pass statement" }
    ]
  },
  {
    title: "Functions",
    rules: [
      { id: "require_function_def", label: "Require function definition" },
      { id: "require_function_call", label: "Require function call" },
      { id: "require_return_statement", label: "Require return statement" },
      { id: "require_global", label: "Require global keyword" },
      { id: "require_nonlocal", label: "Require nonlocal keyword" }
    ]
  },
  {
    title: "Data Structures",
    rules: [
      { id: "require_list", label: "Require list literal" },
      { id: "require_dict", label: "Require dictionary literal" },
      { id: "require_tuple", label: "Require tuple literal" },
      { id: "require_set", label: "Require set literal" },
      { id: "require_list_comprehension", label: "Require list comprehension" },
      { id: "require_dict_comprehension", label: "Require dictionary comprehension" },
      { id: "require_del_statement", label: "Require del statement" }
    ]
  },
  {
    title: "File Handling",
    rules: [
      { id: "require_open_call", label: "Require open() call" }
    ]
  },
  {
    title: "OOP & Advanced",
    rules: [
      { id: "require_class_def", label: "Require class definition" },
      { id: "require_try_except", label: "Require try/except block" },
      { id: "require_lambda", label: "Require lambda function" },
      { id: "require_import", label: "Require import statement" },
      { id: "require_match_statement", label: "Require match statement" },
      { id: "require_yield", label: "Require yield (Generator)" },
      { id: "require_assert_statement", label: "Require assert statement" },
      { id: "require_raise_statement", label: "Require raise statement" },
      { id: "require_decorator", label: "Require decorator (@)" },
      { id: "require_async_function", label: "Require async def" },
      { id: "require_await", label: "Require await" }
    ]
  }
];

const ASTCategoryAccordion = ({ category, requirements, onToggleRule, onToggleCategory }) => {
  const [isOpen, setIsOpen] = useState(false);
  const checkedCount = category.rules.filter(r => requirements[r.id]).length;
  const allSelected = checkedCount === category.rules.length;

  return (
    <div className="bg-bg-base border border-border-subtle rounded-xl overflow-hidden mb-3 shadow-sm">
      <div 
        className="flex items-center p-4 cursor-pointer hover:bg-bg-glass transition-colors group gap-4"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-sm font-bold text-text-main group-hover:text-emerald-500 transition-colors flex-1">
          {category.title}
        </span>
        
        <div className="flex items-center gap-3">
          {checkedCount > 0 && (
            <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs px-2.5 py-0.5 rounded-full font-bold shadow-sm whitespace-nowrap">
              {checkedCount} selected
            </span>
          )}
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
            className={`text-text-muted transition-transform duration-300 ${isOpen ? 'rotate-180 text-emerald-500' : ''}`}
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
      </div>
      
      {isOpen && (
        <div className="p-2 border-t border-border-subtle bg-bg-panel flex flex-col gap-1">
          <label className="flex justify-between items-center px-3 py-2.5 mb-1 border-b border-border-subtle/50 bg-bg-base/30 rounded-t-lg cursor-pointer group">
            <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted group-hover:text-text-main transition-colors">
              Select All Rules
            </span>
            <div className="relative inline-flex items-center">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => onToggleCategory(category, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400 shadow-inner"></div>
            </div>
          </label>
          {category.rules.map(rule => {
            const isChecked = !!requirements[rule.id];
            
            return (
              <label 
                key={rule.id} 
                className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all border ${
                  isChecked 
                    ? 'bg-emerald-500/10 border-emerald-500/30 shadow-sm' 
                    : 'bg-transparent border-transparent hover:bg-bg-glass'
                }`}
              >
                <div className="flex flex-col gap-0.5">
                  <span className={`text-sm font-semibold transition-colors ${isChecked ? 'text-emerald-400' : 'text-text-main'}`}>
                    {rule.label}
                  </span>
                </div>
                <div className="relative inline-flex items-center">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={(e) => onToggleRule(rule.id, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400 shadow-inner"></div>
                </div>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default function PracticeModuleManager() {
    const [modules, setModules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [isModuleModalOpen, setIsModuleModalOpen] = useState(false);
  const [editingModule, setEditingModule] = useState(null);
  
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [selectedModuleId, setSelectedModuleId] = useState(null);
  const [alertConfig, setAlertConfig] = useState(null);
  const [confirmConfig, setConfirmConfig] = useState(null);

  // Form states
  const [moduleForm, setModuleForm] = useState({ title: '', description: '', order_index: 0 });
  const [taskForm, setTaskForm] = useState({ 
    title: '', instructions: '', starter_code: '', expected_output: '', order_index: 0, expected_ast_patterns: {}
  });

  const handleToggleRule = (ruleId, isEnabled) => {
    setTaskForm(prev => {
      const newReqs = { ...prev.expected_ast_patterns };
      if (isEnabled) {
        newReqs[ruleId] = true;
      } else {
        delete newReqs[ruleId];
      }
      return { ...prev, expected_ast_patterns: newReqs };
    });
  };

  const handleToggleCategory = (category, isEnabled) => {
    setTaskForm(prev => {
      const newReqs = { ...prev.expected_ast_patterns };
      category.rules.forEach(rule => {
        if (isEnabled) {
          newReqs[rule.id] = true;
        } else {
          delete newReqs[rule.id];
        }
      });
      return { ...prev, expected_ast_patterns: newReqs };
    });
  };

  const allVisibleRules = AST_GROUPS.flatMap(group => group.rules);
  const allVisibleSelected = allVisibleRules.length > 0 && allVisibleRules.every(rule => taskForm.expected_ast_patterns[rule.id]);

  const handleSelectAllVisible = (isSelected) => {
    setTaskForm(prev => {
      const newReqs = { ...prev.expected_ast_patterns };
      allVisibleRules.forEach(rule => {
        if (isSelected) {
          newReqs[rule.id] = true;
        } else {
          delete newReqs[rule.id];
        }
      });
      return { ...prev, expected_ast_patterns: newReqs };
    });
  };

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

  useEffect(() => {
    fetchModules();
  }, []);


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
      setAlertConfig({ title: 'Error', message: err.message || 'Failed to save module', isError: true });
    }
  };

  const handleDeleteModule = (moduleId) => {
    setConfirmConfig({
      title: 'Delete Module',
      message: 'Are you sure you want to delete this module and ALL its tasks? This action cannot be undone.',
      isDanger: true,
      onConfirm: async () => {
        setConfirmConfig(null);
        try {
          await api.delete(`/practice/modules/${moduleId}`);
          fetchModules();
        } catch (err) {
          setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete module', isError: true });
        }
      }
    });
  };

  const handleTaskSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...taskForm,
        expected_ast_patterns: Object.keys(taskForm.expected_ast_patterns).length > 0 ? taskForm.expected_ast_patterns : null
      };

      if (editingTask) {
        await api.put(`/practice/tasks/${editingTask.task_id}`, payload);
      } else {
        await api.post(`/practice/modules/${selectedModuleId}/tasks`, payload);
      }
      setIsTaskModalOpen(false);
      fetchModules();
    } catch (err) {
      setAlertConfig({ title: 'Error', message: err.message || 'Failed to save task. Ensure Expected AST Patterns is valid JSON (e.g. {"FunctionDef": 1})', isError: true });
    }
  };

  const handleDeleteTask = (taskId) => {
    setConfirmConfig({
      title: 'Delete Task',
      message: 'Are you sure you want to delete this task?',
      isDanger: true,
      onConfirm: async () => {
        setConfirmConfig(null);
        try {
          await api.delete(`/practice/tasks/${taskId}`);
          fetchModules();
        } catch (err) {
          setAlertConfig({ title: 'Error', message: err.message || 'Failed to delete task', isError: true });
        }
      }
    });
  };

  const openModuleModal = (mod = null) => {
    if (mod) {
      setEditingModule(mod);
      setModuleForm({ title: mod.title, description: mod.description || '', order_index: mod.order_index });
    } else {
      setEditingModule(null);
      setModuleForm({ title: '', description: '', order_index: modules.length + 1 });
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
        expected_ast_patterns: task.expected_ast_patterns || {}
      });
    } else {
      setEditingTask(null);
      const mod = modules.find(m => m.module_id === moduleId);
      setTaskForm({
        title: '',
        instructions: '',
        starter_code: '',
        expected_output: '',
        order_index: mod ? mod.tasks.length + 1 : 1,
        expected_ast_patterns: {}
      });
    }
    setIsTaskModalOpen(true);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col overflow-y-auto px-5 py-6 sm:px-8">
        <div className="mx-auto max-w-6xl w-full space-y-6">
          <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
            <div>
              <p className="mb-1 font-mono text-xs font-semibold tracking-wider text-text-emerald uppercase">MANAGEMENT</p>
              <h1 className="text-2xl font-bold flex items-center gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-text-emerald"><path d="M2 6h4"/><path d="M2 10h4"/><path d="M2 14h4"/><path d="M2 18h4"/><rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9.5 8h5"/><path d="M9.5 12H16"/><path d="M9.5 16H14"/></svg>
                Practice Modules
              </h1>
              <p className="mt-1 text-sm text-text-muted">
                Create and manage structured solo practice modules and coding tasks for students.
              </p>
            </div>
            <button
              onClick={() => openModuleModal()}
              className="rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white shadow-lg transition-all hover:bg-emerald-500 hover:shadow-emerald-500/20 active:scale-95"
            >
              + Create New Module
            </button>
          </header>

          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>
                <p className="text-sm text-text-muted">Loading practice modules...</p>
              </div>
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-900/50 bg-red-900/10 p-6 text-center text-sm text-red-400">
              <svg className="mx-auto mb-2 h-8 w-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {error}
            </div>
          ) : modules.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-border-subtle p-12 text-center">
              <div className="mb-4 rounded-full bg-bg-glass p-4 text-emerald-500">
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <h3 className="mb-1 text-lg font-bold text-text-main">No Modules Found</h3>
              <p className="mb-4 text-sm text-text-muted">Get started by creating your first practice module.</p>
              <button onClick={() => openModuleModal()} className="text-sm font-semibold text-emerald-400 hover:text-emerald-300">
                + Create Module
              </button>
            </div>
          ) : (
            <div className="space-y-6 pb-12">
              {modules.map((mod) => (
                <div key={mod.module_id} className="overflow-hidden rounded-xl border border-border-subtle bg-bg-panel shadow-sm transition-all hover:border-border-hover">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle bg-bg-base/50 p-5">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-bg-glass text-xs font-bold text-text-muted">
                          {mod.order_index}
                        </span>
                        <h2 className="text-lg font-bold text-text-main tracking-tight">
                          {mod.title}
                        </h2>
                        {mod.instructor_id === null && (
                          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-400 shadow-sm">
                            Protected Base
                          </span>
                        )}
                      </div>
                      {mod.description && (
                        <p className="mt-1.5 pl-9 text-sm text-text-muted leading-relaxed">
                          {mod.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 pl-9 sm:pl-0">
                      <button
                        onClick={() => openModuleModal(mod)}
                        className="rounded-lg bg-bg-glass px-3 py-1.5 text-xs font-semibold text-text-main transition hover:bg-bg-glass-hover"
                      >
                        Edit Module
                      </button>
                      <button
                        onClick={() => handleDeleteModule(mod.module_id)}
                        disabled={mod.instructor_id === null}
                        className="rounded-lg border border-red-900/30 bg-red-900/10 px-3 py-1.5 text-xs font-semibold text-red-400 transition hover:bg-red-900/30 disabled:opacity-30 disabled:cursor-not-allowed"
                        title={mod.instructor_id === null ? "Protected baseline modules cannot be deleted" : "Delete Module"}
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="p-5">
                    {mod.tasks.length > 0 ? (
                      <div className="space-y-3">
                        {mod.tasks.map((task) => (
                          <div key={task.task_id} className="group relative flex items-center justify-between overflow-hidden rounded-lg border border-border-subtle bg-bg-base p-3 pl-4 transition hover:border-border-hover">
                            <div className="flex items-center gap-4 min-w-0">
                              <span className="text-sm font-mono text-text-muted shrink-0">
                                {mod.order_index}.{task.order_index}
                              </span>
                              <div className="min-w-0 flex-1">
                                <h3 className="truncate font-semibold text-text-main text-sm">
                                  {task.title}
                                </h3>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => openTaskModal(mod.module_id, task)}
                                className="rounded-md p-1.5 text-text-muted hover:bg-bg-glass hover:text-text-main transition"
                                title="Edit Task"
                              >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleDeleteTask(task.task_id)}
                                disabled={mod.instructor_id === null}
                                className="rounded-md p-1.5 text-text-muted hover:bg-red-900/20 hover:text-red-400 transition disabled:opacity-30 disabled:cursor-not-allowed"
                                title={mod.instructor_id === null ? "Cannot delete tasks in protected modules" : "Delete Task"}
                              >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center rounded-lg border border-dashed border-border-subtle p-6 text-sm text-text-muted">
                        No tasks yet. Create a task to populate this module.
                      </div>
                    )}
                    
                    <button
                      onClick={() => openTaskModal(mod.module_id)}
                      className="mt-4 w-full flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border-subtle p-2.5 text-xs font-semibold text-text-muted hover:border-emerald-500/50 hover:bg-emerald-500/5 hover:text-emerald-400 transition"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add Task to Module
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
          <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-panel shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
            <button 
              onClick={() => setIsModuleModalOpen(false)}
              className="absolute right-4 top-4 text-text-muted hover:text-text-main transition"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <div className="border-b border-border-subtle p-5">
              <h2 className="text-lg font-bold text-text-main">
                {editingModule ? 'Edit Module Details' : 'Create New Module'}
              </h2>
            </div>
            
            <form onSubmit={handleModuleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-main mb-1.5">Module Title</label>
                <input required type="text" value={moduleForm.title} onChange={e => setModuleForm({...moduleForm, title: e.target.value})} placeholder="e.g. Introduction to Python" className="w-full rounded-xl border border-border-subtle bg-bg-base px-3 py-2 text-sm text-text-main placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-main mb-1.5">Description (Optional)</label>
                <textarea value={moduleForm.description} onChange={e => setModuleForm({...moduleForm, description: e.target.value})} placeholder="Briefly describe what this module covers..." className="w-full rounded-xl border border-border-subtle bg-bg-base px-3 py-2 text-sm text-text-main placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition" rows="3" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-main mb-1.5">Sort Order Index</label>
                <div className="flex items-center rounded-xl border border-border-subtle bg-bg-base overflow-hidden focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500 transition">
                  <button 
                    type="button" 
                    onClick={() => setModuleForm({...moduleForm, order_index: Math.max(1, moduleForm.order_index - 1)})}
                    className="px-3 py-2 text-text-muted hover:bg-bg-glass hover:text-text-main transition border-r border-border-subtle"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>
                  </button>
                  <input 
                    required 
                    type="number" 
                    min="1" 
                    value={moduleForm.order_index} 
                    onChange={e => setModuleForm({...moduleForm, order_index: parseInt(e.target.value) || 1})} 
                    className="w-full bg-transparent px-3 py-2 text-sm text-center text-text-main focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none" 
                  />
                  <button 
                    type="button" 
                    onClick={() => setModuleForm({...moduleForm, order_index: moduleForm.order_index + 1})}
                    className="px-3 py-2 text-text-muted hover:bg-bg-glass hover:text-text-main transition border-l border-border-subtle"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                  </button>
                </div>
                <p className="mt-1.5 text-[10px] text-text-muted">Lower numbers appear first in the curriculum.</p>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-border-subtle mt-6">
                <button type="button" onClick={() => setIsModuleModalOpen(false)} className="rounded-lg border border-border-subtle bg-transparent px-4 py-2 text-sm font-semibold text-text-main hover:bg-bg-glass transition">Cancel</button>
                <button type="submit" className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 transition">Save Module</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Task Modal */}
      {isTaskModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-3xl rounded-2xl border border-border-subtle bg-bg-panel shadow-2xl flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-border-subtle p-5 shrink-0">
              <h2 className="text-lg font-bold text-text-main">
                {editingTask ? 'Edit Practice Task' : 'Create Practice Task'}
              </h2>
              <button onClick={() => setIsTaskModalOpen(false)} className="text-text-muted hover:text-text-main transition">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <div className="overflow-y-auto p-5 shrink">
              <form id="task-form" onSubmit={handleTaskSubmit} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                  <div className="sm:col-span-3">
                    <label className="block text-xs font-semibold text-text-main mb-1.5">Task Title</label>
                    <input required type="text" value={taskForm.title} onChange={e => setTaskForm({...taskForm, title: e.target.value})} placeholder="e.g. Printing Hello World" className="w-full rounded-xl border border-border-subtle bg-bg-base px-3 py-2 text-sm text-text-main placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition" />
                  </div>
                  <div className="sm:col-span-1">
                    <label className="block text-xs font-semibold text-text-main mb-1.5">Order Index</label>
                    <div className="flex items-center rounded-xl border border-border-subtle bg-bg-base overflow-hidden focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500 transition">
                      <button 
                        type="button" 
                        onClick={() => setTaskForm({...taskForm, order_index: Math.max(1, taskForm.order_index - 1)})}
                        className="px-3 py-2 text-text-muted hover:bg-bg-glass hover:text-text-main transition border-r border-border-subtle"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>
                      </button>
                      <input 
                        required 
                        type="number" 
                        min="1" 
                        value={taskForm.order_index} 
                        onChange={e => setTaskForm({...taskForm, order_index: parseInt(e.target.value) || 1})} 
                        className="w-full bg-transparent px-3 py-2 text-sm text-center text-text-main focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none" 
                      />
                      <button 
                        type="button" 
                        onClick={() => setTaskForm({...taskForm, order_index: taskForm.order_index + 1})}
                        className="px-3 py-2 text-text-muted hover:bg-bg-glass hover:text-text-main transition border-l border-border-subtle"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                      </button>
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs font-semibold text-text-main mb-1.5 flex items-center">
                  Instructions
                  <InfoTooltip title="Markdown Support">
                    <p>You can use standard Markdown to format the instructions.</p>
                    <ul className="mt-1 ml-4 list-disc text-text-muted">
                      <li><code className="text-emerald-400">**bold**</code></li>
                      <li><code className="text-emerald-400">`code blocks`</code></li>
                      <li><code className="text-emerald-400"># Headers</code></li>
                    </ul>
                  </InfoTooltip>
                </label>
                  <textarea required value={taskForm.instructions} onChange={e => setTaskForm({...taskForm, instructions: e.target.value})} placeholder="Write the prompt for the student here..." className="w-full rounded-xl border border-border-subtle bg-bg-base px-3 py-2 text-sm text-text-main placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition font-mono" rows="4" />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-text-main mb-1.5">Starter Code (Optional)</label>
                    <textarea value={taskForm.starter_code} onChange={e => setTaskForm({...taskForm, starter_code: e.target.value})} placeholder="# Write your code below" className="w-full rounded-xl border border-border-subtle bg-bg-base px-3 py-2 text-sm text-emerald-400 placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition font-mono whitespace-pre" rows="5" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-text-main mb-1.5 flex items-center">
                      Expected Output
                      <InfoTooltip title="Expected Output">
                        The exact console output the student's code must produce to pass. Trailing whitespaces and empty newlines at the end are ignored, but exact casing and spelling are required.
                      </InfoTooltip>
                    </label>
                    <textarea required value={taskForm.expected_output} onChange={e => setTaskForm({...taskForm, expected_output: e.target.value})} placeholder="Hello World" className="w-full rounded-xl border border-border-subtle bg-bg-base px-3 py-2 text-sm text-amber-400 placeholder-text-muted focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition font-mono whitespace-pre" rows="5" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-text-main mb-1.5 flex items-center justify-between">
                    <div className="flex items-center">
                      AST Checklist Requirements
                      <InfoTooltip title="Abstract Syntax Tree Patterns" position="top">
                        <p className="mb-2">Enforce specific Python constructs in the student's code without writing complex tests.</p>
                        <p className="text-text-muted">For example, if you toggle "Require for loop", the student's submission will be automatically rejected if they don't use a for loop.</p>
                      </InfoTooltip>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer group">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-text-emerald group-hover:text-emerald-400 transition-colors">
                          Toggle All
                        </span>
                        <div className="relative inline-flex items-center">
                          <input
                            type="checkbox"
                            checked={allVisibleSelected}
                            onChange={(e) => handleSelectAllVisible(e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-8 h-4 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400 shadow-inner"></div>
                        </div>
                      </label>
                      <span className="text-text-muted font-normal text-[10px]">{Object.keys(taskForm.expected_ast_patterns).length} active</span>
                    </div>
                  </label>
                  
                  <div className="flex flex-col h-full transition-opacity duration-300">
                    {AST_GROUPS.map((group) => (
                      <ASTCategoryAccordion 
                        key={group.title}
                        category={group}
                        requirements={taskForm.expected_ast_patterns}
                        onToggleRule={handleToggleRule}
                        onToggleCategory={handleToggleCategory}
                      />
                    ))}
                  </div>
                </div>
              </form>
            </div>

            <div className="flex justify-end gap-3 p-5 border-t border-border-subtle shrink-0">
              <button type="button" onClick={() => setIsTaskModalOpen(false)} className="rounded-lg border border-border-subtle bg-transparent px-4 py-2 text-sm font-semibold text-text-main hover:bg-bg-glass transition">Cancel</button>
              <button type="submit" form="task-form" className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 transition">Save Task</button>
            </div>
          </div>
        </div>
      )}
    
      <AlertModal 
        isOpen={!!alertConfig} 
        title={alertConfig?.title} 
        message={alertConfig?.message} 
        isError={alertConfig?.isError} 
        onClose={() => setAlertConfig(null)} 
      />

      <ConfirmationModal 
        isOpen={!!confirmConfig} 
        title={confirmConfig?.title} 
        message={confirmConfig?.message} 
        onConfirm={confirmConfig?.onConfirm}
        onCancel={() => setConfirmConfig(null)} 
        isDanger={confirmConfig?.isDanger}
        confirmText="Confirm"
      />
</div>
  );
}

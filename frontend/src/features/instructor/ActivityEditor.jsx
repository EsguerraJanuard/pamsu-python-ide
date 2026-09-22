/* eslint-disable react-hooks/set-state-in-effect */
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Flatpickr from 'react-flatpickr';
import 'flatpickr/dist/themes/dark.css';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const AST_GROUPS = [
  {
    title: "Output & Input",
    levels: ["beginner", "intermediate", "expert"],
    rules: [
      { id: "require_print_call", label: "Require print() call" },
      { id: "require_input_call", label: "Require input() call" }
    ]
  },
  {
    title: "Control Flow",
    levels: ["beginner", "intermediate", "expert"],
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
    levels: ["intermediate", "expert"],
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
    levels: ["intermediate", "expert"],
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
    levels: ["intermediate", "expert"],
    rules: [
      { id: "require_open_call", label: "Require open() call" }
    ]
  },
  {
    title: "OOP & Advanced",
    levels: ["expert"],
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

const DIFFICULTY_SUGGESTIONS = {
  beginner: ["require_print_call", "require_input_call", "require_if_statement"],
  intermediate: ["require_if_statement", "require_for_loop", "require_function_def", "require_return_statement"],
  expert: ["require_class_def", "require_try_except", "require_list_comprehension"]
};

// Accordion for AST Category
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
                    ? 'bg-emerald-500/5 border-emerald-500/20' 
                    : 'bg-transparent border-transparent hover:bg-bg-glass hover:border-border-subtle'
                }`}
              >
                <span className={`text-sm font-medium transition-colors ${isChecked ? 'text-emerald-600 dark:text-emerald-400' : 'text-text-main'}`}>
                  {rule.label}
                </span>
                
                <div className="relative inline-flex items-center group ml-4">
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

ASTCategoryAccordion.propTypes = {
  category: PropTypes.shape({
    title: PropTypes.string.isRequired,
    rules: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
      })
    ).isRequired,
  }).isRequired,
  requirements: PropTypes.object.isRequired,
  onToggleRule: PropTypes.func.isRequired,
  onToggleCategory: PropTypes.func.isRequired,
};

const ActivityEditor = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialClassId = searchParams.get('class');
  
  const [classrooms, setClassrooms] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    class_ids: initialClassId ? [parseInt(initialClassId)] : [],
    due_at: null,
    scheduled_publish_at: null,
    description: '',
    instructions: '',
    expected_output: '',
    requirements: {},
    starter_code: '',
    activity_type: 'laboratory',
    difficulty: '',
    is_published: false,
    allow_paste: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleDifficultyChange = (newDifficulty) => {
    const suggestions = DIFFICULTY_SUGGESTIONS[newDifficulty];
    const newReqs = { ...formData.requirements };
    
    // Add missing suggestions with default count 1
    suggestions.forEach(ruleId => {
      if (!newReqs[ruleId]) {
        newReqs[ruleId] = { required: true, min_count: 1 };
      }
    });

    // Prune requirements that are no longer available in the new difficulty
    const allowedGroups = AST_GROUPS.filter(g => g.levels.includes(newDifficulty));
    const allowedRuleIds = new Set(allowedGroups.flatMap(g => g.rules).map(r => r.id));
    
    Object.keys(newReqs).forEach(ruleId => {
      if (!allowedRuleIds.has(ruleId)) {
        delete newReqs[ruleId];
      }
    });

    setFormData(prev => ({
      ...prev,
      difficulty: newDifficulty,
      requirements: newReqs
    }));
  };

  const handleToggleRule = (ruleId, isChecked) => {
    setFormData(prev => {
      const newReqs = { ...prev.requirements };
      if (isChecked) {
        newReqs[ruleId] = { required: true, min_count: 1 };
      } else {
        delete newReqs[ruleId];
      }
      return { ...prev, requirements: newReqs };
    });
  };

  const handleToggleCategory = (category, isChecked) => {
    setFormData(prev => {
      const newReqs = { ...prev.requirements };
      category.rules.forEach(rule => {
        if (isChecked) {
          newReqs[rule.id] = { required: true, min_count: 1 };
        } else {
          delete newReqs[rule.id];
        }
      });
      return { ...prev, requirements: newReqs };
    });
  };

  const handleSelectAllVisible = (isChecked) => {
    const visibleGroups = AST_GROUPS.filter(group => group.levels.includes(formData.difficulty || 'expert'));
    const allVisibleRules = visibleGroups.flatMap(g => g.rules);

    setFormData(prev => {
      const newReqs = { ...prev.requirements };
      if (!isChecked) {
        allVisibleRules.forEach(r => delete newReqs[r.id]);
      } else {
        allVisibleRules.forEach(r => newReqs[r.id] = { required: true, min_count: 1 });
      }
      return { ...prev, requirements: newReqs };
    });
  };

  useEffect(() => {
    const fetchClassrooms = async () => {
      try {
        const response = await api.get('/classrooms/');
        setClassrooms(response || []);
      } catch (err) {
        console.error('Failed to fetch classrooms', err);
      }
    };
    fetchClassrooms();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.class_ids || formData.class_ids.length === 0) {
      setError('Please select at least one classroom.');
      return;
    }
    if (!formData.difficulty) {
      setError('Please select a difficulty level.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        class_ids: formData.class_ids.map(id => parseInt(id, 10)),
        paste_policy: formData.allow_paste ? "internal_only" : "disabled",
        due_at: formData.due_at ? new Date(formData.due_at).toISOString() : null,
        scheduled_publish_at: (!formData.is_published && formData.scheduled_publish_at) 
          ? new Date(formData.scheduled_publish_at).toISOString() 
          : null,
        required_ast_rules: formData.requirements,
      };

      delete payload.requirements;
      delete payload.expected_output;
      delete payload.is_published;
      delete payload.allow_paste;

      const response = await api.post('/instructors/tasks/', payload);
      
      // If expected output was provided, automatically convert it into a global test case
      if (formData.expected_output && formData.expected_output.trim() !== "") {
        const tasks = Array.isArray(response) ? response : [response];
        for (const task of tasks) {
          try {
            await api.post(`/instructors/tasks/${task.task_id}/test-cases`, {
              name: "Expected Output (Global)",
              expected_output: formData.expected_output,
              is_hidden: false
            });
          } catch (tcErr) {
            console.error("Failed to save expected output test case:", tcErr);
          }
        }
      }
      
      // If single classroom was selected, navigate directly to that activity's page
      if (response && Array.isArray(response) && response.length === 1) {
        navigate(`/instructor/activities/${response[0].task_id}`);
      } else {
        // Multiple activities were created, navigate to dashboard
        navigate('/instructor/dashboard');
      }
    } catch (err) {
      console.error('Error creating activity:', err);
      setError(err.message || 'Failed to create activity. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const visibleGroups = AST_GROUPS.filter(group => group.levels.includes(formData.difficulty || 'expert'));
  const allVisibleRules = visibleGroups.flatMap(g => g.rules);
  const allVisibleSelected = allVisibleRules.length > 0 && allVisibleRules.every(r => formData.requirements[r.id]);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <div className="hidden lg:flex h-full">
        <InstructorSidebar />
      </div>
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <div className="w-full">
            <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
              <div>
                <p className="mb-1 font-mono text-xs font-bold uppercase tracking-widest text-text-emerald">MANAGEMENT</p>
                <h1 className="text-2xl font-bold tracking-tight text-text-main">Create New Activity</h1>
                <p className="mt-1 text-sm text-text-muted">
                  Author new laboratory activities, code templates, and automated AST testing guidelines.
                </p>
              </div>
            </header>
            
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-text-rose p-4 rounded-xl mb-6 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Details & Instructions (7 cols) */}
              <div className="lg:col-span-7 space-y-5 bg-bg-glass p-6 rounded-2xl border border-border-subtle">
                <h2 className="text-sm font-bold uppercase tracking-wider text-text-emerald pb-2 border-b border-border-subtle">
                  Activity Details
                </h2>

                <div>
                  <label htmlFor="title" className="block text-xs font-semibold text-text-muted mb-1.5">
                    Activity Title <span className="text-text-emerald">*</span>
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                    placeholder="e.g. Lab Activity 3 — Fibonacci Sequence"
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-text-muted mb-1.5">
                    Target Classroom(s) <span className="text-text-emerald">*</span>
                  </label>
                  <div className="bg-bg-glass border border-border-subtle rounded-xl p-3 max-h-56 overflow-y-auto custom-scrollbar flex flex-col gap-2">
                    {classrooms.length === 0 ? (
                      <div className="text-sm text-text-muted italic py-2 text-center">No classrooms available</div>
                    ) : (
                      classrooms.map(cls => {
                        const isSelected = formData.class_ids.includes(cls.class_id);
                        return (
                          <label 
                            key={cls.class_id} 
                            className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                              isSelected
                                ? 'bg-emerald-500/10 border-emerald-500/30 shadow-sm'
                                : 'bg-bg-base border-border-subtle hover:border-border-strong'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-medium select-none ${isSelected ? 'text-text-emerald' : 'text-text-main'}`}>
                                {cls.subject_code} - {cls.section}
                              </span>
                            </div>
                            <div className={`w-5 h-5 rounded flex items-center justify-center transition-colors ${
                              isSelected
                                ? 'bg-emerald-500 border-emerald-500 text-bg-panel'
                                : 'border border-border-strong bg-transparent'
                            }`}>
                              {isSelected && (
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                              )}
                            </div>
                            <input 
                              type="checkbox" 
                              className="sr-only"
                              checked={isSelected}
                              onChange={(e) => {
                                const checked = e.target.checked;
                                setFormData(prev => ({
                                  ...prev,
                                  class_ids: checked 
                                    ? [...prev.class_ids, cls.class_id]
                                    : prev.class_ids.filter(id => id !== cls.class_id)
                                }));
                              }}
                            />
                          </label>
                        );
                      })
                    )}
                  </div>
                </div>
                


                <div>
                  <label htmlFor="description" className="block text-xs font-semibold text-text-muted mb-1.5">Overview / Description</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={4}
                    placeholder="Brief overview of the activity goals..."
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div>
                  <label htmlFor="instructions" className="block text-xs font-semibold text-text-muted mb-1.5">Detailed Student Instructions</label>
                  <textarea
                    id="instructions"
                    name="instructions"
                    value={formData.instructions}
                    onChange={handleChange}
                    rows={8}
                    placeholder="Step-by-step instructions for completing the task..."
                    className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
                  <div>
                    <label htmlFor="expected_output" className="block text-xs font-semibold text-text-muted mb-1.5">Expected Output</label>
                    <textarea
                      id="expected_output"
                      name="expected_output"
                      value={formData.expected_output}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Target output string..."
                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 font-mono text-xs text-text-emerald focus:outline-none focus:border-emerald-500 transition-colors h-full"
                    />
                  </div>

                  <div className="relative h-full flex flex-col gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-text-muted mb-1.5">
                        Difficulty Level <span className="text-text-emerald">*</span>
                      </label>
                      <div className="flex bg-bg-base border border-border-subtle rounded-xl p-1">
                        {['beginner', 'intermediate', 'expert'].map(level => (
                          <button
                            key={level}
                            type="button"
                            onClick={() => handleDifficultyChange(level)}
                            className={`flex-1 py-2 text-xs font-semibold capitalize rounded-lg transition-colors ${
                              formData.difficulty === level 
                                ? 'bg-bg-glass text-emerald-600 dark:text-emerald-400 shadow-sm border border-border-subtle' 
                                : 'text-text-muted hover:text-text-main hover:bg-bg-glass/50'
                            }`}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="flex-1 relative min-h-[200px]">
                      <label className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center justify-between">
                        <span>AST Checklist Requirements</span>
                        <div className="flex items-center gap-4">
                          {formData.difficulty && (
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
                          )}
                          <span className="text-text-muted font-normal text-[10px]">{Object.keys(formData.requirements).length} active</span>
                        </div>
                      </label>
                      <div className={`flex flex-col h-full transition-opacity duration-300 ${!formData.difficulty ? 'opacity-30 pointer-events-none blur-[2px]' : ''}`}>
                        {AST_GROUPS.filter(group => group.levels.includes(formData.difficulty || 'expert')).map((group) => (
                          <ASTCategoryAccordion 
                            key={group.title}
                            category={group}
                            requirements={formData.requirements}
                            onToggleRule={handleToggleRule}
                            onToggleCategory={handleToggleCategory}
                          />
                        ))}
                      </div>
                      {!formData.difficulty && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center z-10 p-4 text-center mt-6">
                          <div className="bg-bg-panel/90 backdrop-blur-sm border border-border-strong rounded-xl p-4 shadow-lg shadow-black/20">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-text-emerald">
                              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            <p className="text-xs font-bold text-text-main mb-1">Requirements Locked</p>
                            <p className="text-[10px] text-text-muted">Select a Difficulty Level first to configure AST requirements.</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Code Template & Settings (5 cols) */}
              <div className="lg:col-span-5 flex flex-col gap-5">
                <div className="flex-1 bg-bg-glass p-6 rounded-2xl border border-border-subtle flex flex-col">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-text-emerald pb-2 border-b border-border-subtle mb-4">
                    Starter Code Template
                  </h2>

                  <div className="flex-1 min-h-[220px]">
                    <textarea
                      id="starter_code"
                      name="starter_code"
                      value={formData.starter_code}
                      onChange={handleChange}
                      rows={12}
                      placeholder="# Write initial starter code template for students..."
                      className="w-full h-full bg-bg-base border border-border-subtle rounded-xl p-4 text-text-main font-mono text-xs focus:outline-none focus:border-emerald-500 transition-colors resize-none"
                    />
                  </div>
                </div>

                <div className="bg-bg-glass p-6 rounded-2xl border border-border-subtle space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">Options & Controls</h3>
                  
                  <div className="flex flex-col gap-6">
                    <div className="flex items-center gap-8">
                      <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            name="is_published"
                            checked={formData.is_published}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400"></div>
                        </div>
                        <span className="text-xs font-semibold text-text-main select-none group-hover:text-text-main transition-colors">Publish immediately</span>
                      </label>

                      <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            name="allow_paste"
                            checked={formData.allow_paste}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500 group-hover:bg-text-muted/30 peer-checked:group-hover:bg-emerald-400"></div>
                        </div>
                        <span className="text-xs font-semibold text-text-main select-none group-hover:text-text-main transition-colors">Allow Paste</span>
                      </label>
                    </div>

                    <div className="flex flex-col gap-4">
                      
                        <div className={`animate-fade-in transition-opacity ${formData.is_published ? 'opacity-30 pointer-events-none' : ''} ${formData.class_ids.length > 1 ? 'opacity-50' : ''}`}>
                          <label htmlFor="scheduled_publish_at" className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center justify-between">
                            <span>Scheduled Publish Date <span className="text-text-muted font-normal ml-1">(Optional)</span></span>
                          </label>
                          <div className="relative group flex">
                            <Flatpickr
                              data-enable-time
                              value={formData.scheduled_publish_at}
                              onChange={([date]) => setFormData(prev => ({ ...prev, scheduled_publish_at: date }))}
                              disabled={formData.is_published || formData.class_ids.length > 1}
                              className={`w-full bg-bg-glass border border-border-subtle rounded-xl pl-4 pr-10 py-2.5 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-border-strong shadow-inner ${formData.class_ids.length > 1 ? 'text-text-muted cursor-not-allowed' : 'text-text-main cursor-pointer'}`}
                              placeholder="Select date and time"
                              options={{
                                dateFormat: "Y-m-d H:i",
                                time_24hr: false,
                                altInput: true,
                                altFormat: "M j, Y h:i K"
                              }}
                            />
                            {/* Calendar icon */}
                            <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none text-text-muted">
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            </div>
                          </div>
                          {formData.class_ids.length > 1 && (
                            <p className="mt-2 text-xs text-text-amber flex items-center gap-1.5">
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                              Scheduling is disabled when assigning to multiple classrooms.
                            </p>
                          )}
                        </div>
                      
                      <div>
                        <label htmlFor="due_at" className="block text-xs font-semibold text-text-muted mb-1.5 flex items-center justify-between">
                          <span>Deadline / Due Date <span className="text-text-muted font-normal ml-1">(Optional)</span></span>
                        </label>
                        <div className="relative group flex">
                          <Flatpickr
                            data-enable-time
                            value={formData.due_at}
                            onChange={([date]) => setFormData(prev => ({ ...prev, due_at: date }))}
                            className="w-full bg-bg-glass border border-border-subtle rounded-xl pl-4 pr-10 py-2.5 text-sm text-text-main focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-border-strong shadow-inner cursor-pointer"
                            placeholder="Select deadline"
                            options={{
                              dateFormat: "Y-m-d H:i",
                              time_24hr: false,
                              altInput: true,
                              altFormat: "M j, Y h:i K"
                            }}
                          />
                          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-text-muted group-hover:text-text-emerald transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-3 border-t border-border-subtle">
                    <button
                      type="button"
                      onClick={() => navigate(-1)}
                      className="px-4 py-2 text-xs font-semibold text-text-muted hover:text-text-main transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>

                      <button
                      type="submit"
                      disabled={loading}
                      className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer disabled:opacity-50"
                    >
                      {loading ? "Creating..." : "Create Activity"}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ActivityEditor;

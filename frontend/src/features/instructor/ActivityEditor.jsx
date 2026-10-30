import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import Flatpickr from 'react-flatpickr';
import 'flatpickr/dist/flatpickr.css';
import api, { getErrorMessage } from '../../services/api';
import { classLabel } from '../../utils/format';
import {
  AST_GROUPS,
  DIFFICULTY_LEVELS,
  levelForRules,
  requiredRuleIds,
  ruleLabel,
  ruleLevel,
  ruleMinCount,
} from '../../utils/astRules';
import { ErrorState, InlineAlert, LoadingState } from '../../components/ui/StateViews';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

// Suggested starting rules when a difficulty is picked by hand.
const DIFFICULTY_SUGGESTIONS = {
  beginner: ["require_print_call", "require_input_call", "require_if_statement"],
  intermediate: ["require_if_statement", "require_for_loop", "require_function_def", "require_return_statement"],
  expert: ["require_class_def", "require_try_except", "require_list_comprehension"]
};

const LEVEL_ORDER = DIFFICULTY_LEVELS.map((level) => level.id);
const MAX_MIN_COUNT = 20;
const LEGACY_RULE_IDS = { require_function: "require_function_def", require_class: "require_class_def" };
const KNOWN_RULE_IDS = new Set(AST_GROUPS.flatMap((group) => group.rules.map((rule) => rule.id)));

const levelName = (levelId) => DIFFICULTY_LEVELS.find((level) => level.id === levelId)?.label ?? levelId;

const LABEL_CLASS = "block text-sm font-semibold text-text-main mb-1.5";
const INPUT_CLASS = "w-full bg-bg-base border border-border-subtle rounded-xl p-3 text-sm text-text-main focus:outline-none focus:border-psu-maroon transition-colors";

/** Whether a rule may be required at this difficulty (see astRules.js). */
const levelAllows = (difficulty, ruleId) =>
  LEVEL_ORDER.indexOf(ruleLevel(ruleId)) <= LEVEL_ORDER.indexOf(difficulty || 'expert');

/**
 * Stored rules -> editor state: { rule_id: { required: true, min_count } }.
 * Unknown rule names are dropped: the editor cannot show them, the grader
 * fails every submission on them, and the backend no longer saves them.
 */
function toEditorRequirements(rules) {
  const requirements = {};
  requiredRuleIds(rules).forEach((ruleId) => {
    const id = LEGACY_RULE_IDS[ruleId] || ruleId;
    if (!KNOWN_RULE_IDS.has(id)) return;
    requirements[id] = { required: true, min_count: Math.max(1, ruleMinCount(rules[ruleId])) };
  });
  return requirements;
}

const sortedJson = (value) =>
  JSON.stringify(Object.keys(value).sort().map((key) => [key, value[key]]));

const timeOf = (value) => (value ? new Date(value).getTime() : null);
const optionalText = (value) => (value && value.trim() ? value.trim() : null);

// Accordion for AST Category
const ASTCategoryAccordion = ({ category, requirements, onToggleRule, onToggleCategory, onCountChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const checkedCount = category.rules.filter(r => requirements[r.id]).length;
  const allSelected = checkedCount === category.rules.length;

  return (
    <div className="bg-bg-base border border-border-subtle rounded-xl overflow-hidden mb-3 shadow-sm">
      <button
        type="button"
        className="flex w-full items-center p-4 cursor-pointer hover:bg-bg-glass transition-colors group gap-4 text-left"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className="text-sm font-bold text-text-main group-hover:text-text-brand transition-colors flex-1">
          {category.title}
        </span>

        <span className="flex items-center gap-3">
          {checkedCount > 0 && (
            <span className="bg-psu-maroon/10 border border-psu-maroon/20 text-text-brand text-xs px-2.5 py-0.5 rounded-full font-bold shadow-sm whitespace-nowrap">
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
            className={`text-text-muted transition-transform duration-300 ${isOpen ? 'rotate-180 text-text-brand' : ''}`}
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="p-2 border-t border-border-subtle bg-bg-panel flex flex-col gap-1">
          <label className="flex justify-between items-center px-3 py-2.5 mb-1 border-b border-border-subtle/50 bg-bg-base/30 rounded-t-lg cursor-pointer group">
            <span className="text-xs font-bold uppercase tracking-wider text-text-muted group-hover:text-text-main transition-colors">
              Select all rules
            </span>
            <div className="relative inline-flex items-center">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => onToggleCategory(category, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-psu-maroon group-hover:bg-text-muted/30 peer-checked:group-hover:bg-psu-maroon-dark shadow-inner"></div>
            </div>
          </label>
          {category.rules.map(rule => {
            const isChecked = !!requirements[rule.id];
            const countId = `min-count-${rule.id}`;

            return (
              <div
                key={rule.id}
                className={`rounded-lg border p-3 transition-all ${
                  isChecked
                    ? 'bg-psu-maroon/5 border-psu-maroon/20'
                    : 'bg-transparent border-transparent hover:bg-bg-glass hover:border-border-subtle'
                }`}
              >
                <label className="flex cursor-pointer items-center justify-between">
                  <span className={`text-sm font-medium transition-colors ${isChecked ? 'text-text-brand' : 'text-text-main'}`}>
                    {rule.label}
                  </span>

                  <div className="relative inline-flex items-center group ml-4">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => onToggleRule(rule.id, e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-psu-maroon group-hover:bg-text-muted/30 peer-checked:group-hover:bg-psu-maroon-dark shadow-inner"></div>
                  </div>
                </label>
                {isChecked && (
                  <div className="mt-2 flex items-center gap-2">
                    <label htmlFor={countId} className="text-xs font-medium text-text-muted">
                      Required at least
                    </label>
                    <input
                      id={countId}
                      type="number"
                      min={1}
                      max={MAX_MIN_COUNT}
                      value={requirements[rule.id].min_count ?? 1}
                      onChange={(e) => onCountChange(rule.id, e.target.value)}
                      className="w-16 rounded-lg border border-border-subtle bg-bg-base px-2 py-1 text-sm text-text-main focus:border-psu-maroon focus:outline-none"
                    />
                    <span className="text-xs text-text-muted">time(s)</span>
                  </div>
                )}
              </div>
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
  onCountChange: PropTypes.func.isRequired,
};

const SOURCE_TEXT = {
  solution: "in the reference solution",
  description: "in the problem text",
  both: "in the solution and the problem text",
};

/** Result of the activity analyzer, shown after it has been applied. */
function AnalysisSummary({ analysis }) {
  const level = DIFFICULTY_LEVELS.find((l) => l.id === analysis.difficulty_level);
  return (
    <div role="status" className="mt-3 rounded-xl border border-psu-gold/40 bg-psu-gold/[0.06] p-4 text-sm">
      <p className="font-semibold text-text-main">
        Difficulty set to {level ? level.label : analysis.difficulty_level}
      </p>
      <p className="mt-0.5 text-xs text-text-muted">{analysis.difficulty_reason}</p>
      {analysis.constructs.length > 0 ? (
        <ul className="mt-3 space-y-1.5">
          {analysis.constructs.map((construct) => (
            <li key={construct.rule} className="flex flex-wrap items-baseline gap-x-2 text-xs">
              <span className="font-semibold text-text-main">{ruleLabel(construct.rule)}</span>
              <span className="text-text-muted">
                {SOURCE_TEXT[construct.source]}
                {construct.solution_count > 1 ? ` (${construct.solution_count}×)` : ""}
                {construct.description_terms.length > 0 ? ` — “${construct.description_terms.join("”, “")}”` : ""}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-xs text-text-muted">No specific constructs were detected.</p>
      )}
      {analysis.skipped.length > 0 && (
        <p className="mt-3 text-xs text-text-muted">
          Not added because they need a higher difficulty: {analysis.skipped.map(ruleLabel).join(", ")}.
        </p>
      )}
      <p className="mt-3 text-xs text-text-muted">
        These are suggestions. Review the difficulty and checklist below before saving.
      </p>
    </div>
  );
}

AnalysisSummary.propTypes = {
  analysis: PropTypes.shape({
    difficulty_level: PropTypes.string.isRequired,
    difficulty_reason: PropTypes.string,
    constructs: PropTypes.array.isRequired,
    skipped: PropTypes.array.isRequired,
  }).isRequired,
};

/**
 * Live comparison of the chosen difficulty with the level the checked AST
 * rules need (the highest level among them). Updates on every toggle.
 */
function DifficultyStatus({ difficulty, source, checklistLevel, ruleCount, rulesAbove, onUseChecklistLevel, onRemoveRulesAbove }) {
  if (!difficulty) return null;

  // Only possible for activities saved before the check existed.
  if (rulesAbove.length > 0) {
    const plural = rulesAbove.length > 1;
    return (
      <div role="status" className="mt-2 rounded-lg border border-psu-gold/50 bg-psu-gold/[0.06] p-3 text-xs text-text-main">
        <p>
          <span className="font-semibold text-text-amber">Below the checklist:</span>{' '}
          {rulesAbove.map(ruleLabel).join(', ')} {plural ? 'need' : 'needs'} {levelName(checklistLevel)}, above
          this activity&apos;s {levelName(difficulty)} level. Raise the difficulty or remove {plural ? 'these rules' : 'this rule'}.
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button type="button" onClick={onUseChecklistLevel} className="btn-secondary btn-sm">
            Raise to {levelName(checklistLevel)}
          </button>
          <button type="button" onClick={onRemoveRulesAbove} className="btn-secondary btn-sm">
            Remove {plural ? 'these rules' : 'this rule'}
          </button>
        </div>
      </div>
    );
  }

  const detected = (
    <>
      Detected from the checklist: <span className="font-semibold text-text-main">{levelName(checklistLevel)}</span>
      {ruleCount === 0 ? ' (no rules required yet)' : ''}.
    </>
  );

  if (difficulty === checklistLevel) {
    return (
      <p role="status" className="mt-1.5 text-xs text-text-muted">
        {detected} {source === 'analyzer' ? 'Set automatically by the analysis.' : 'Matches the selected level.'}
      </p>
    );
  }

  return (
    <p role="status" className="mt-1.5 text-xs text-text-muted">
      {detected}{' '}
      <span className="font-semibold text-text-amber">Manual override:</span> this activity stays {levelName(difficulty)}.{' '}
      <button type="button" onClick={onUseChecklistLevel} className="font-semibold text-text-brand underline">
        Use {levelName(checklistLevel)}
      </button>
    </p>
  );
}

DifficultyStatus.propTypes = {
  difficulty: PropTypes.string,
  source: PropTypes.oneOf(['manual', 'analyzer', 'checklist', 'saved']),
  checklistLevel: PropTypes.string.isRequired,
  ruleCount: PropTypes.number.isRequired,
  rulesAbove: PropTypes.arrayOf(PropTypes.string).isRequired,
  onUseChecklistLevel: PropTypes.func.isRequired,
  onRemoveRulesAbove: PropTypes.func.isRequired,
};

// The page scrolls inside <main>, not the window.
const scrollFormToTop = () => document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' });

const EMPTY_FORM = {
  title: '',
  class_ids: [],
  due_at: null,
  scheduled_publish_at: null,
  description: '',
  scenario: '',
  instructions: '',
  solution_explanation: '',
  expected_output: '',
  requirements: {},
  starter_code: '',
  activity_type: 'laboratory',
  difficulty: '',
  is_published: false,
  allow_paste: false,
};

const ActivityEditor = () => {
  const navigate = useNavigate();
  const { id: editId } = useParams();
  const isEdit = Boolean(editId);
  const [searchParams] = useSearchParams();
  const initialClassId = searchParams.get('class');

  const [classrooms, setClassrooms] = useState([]);
  const [formData, setFormData] = useState(() => ({
    ...EMPTY_FORM,
    class_ids: initialClassId ? [parseInt(initialClassId, 10)] : [],
  }));
  const [original, setOriginal] = useState(null);
  const [isLoadingTask, setIsLoadingTask] = useState(isEdit);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdTaskId, setCreatedTaskId] = useState(null);

  // Who set the difficulty: 'manual' (a level button), 'analyzer',
  // 'checklist' (Use/Raise to the detected level) or 'saved' (edit mode).
  const [difficultySource, setDifficultySource] = useState(null);
  const [referenceCode, setReferenceCode] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // A level picked by hand. Raising it (or the first pick) adds that level's
  // starting rules; lowering it only removes rules above the new level.
  // Clicking the current level changes nothing: it used to re-add starting
  // rules, e.g. an input() requirement the analysis had not suggested.
  const handleDifficultyChange = (newDifficulty) => {
    if (newDifficulty === formData.difficulty) return;
    setFormData((prev) => {
      const raising = !prev.difficulty || LEVEL_ORDER.indexOf(newDifficulty) > LEVEL_ORDER.indexOf(prev.difficulty);
      const requirements = {};
      Object.entries(prev.requirements).forEach(([ruleId, configuration]) => {
        if (levelAllows(newDifficulty, ruleId)) requirements[ruleId] = configuration;
      });
      if (raising) {
        DIFFICULTY_SUGGESTIONS[newDifficulty].forEach((ruleId) => {
          if (!requirements[ruleId]) requirements[ruleId] = { required: true, min_count: 1 };
        });
      }
      return { ...prev, difficulty: newDifficulty, requirements };
    });
    setDifficultySource('manual');
  };

  // Sets the difficulty to the level the checked rules need. No rules are
  // added or removed: every checked rule fits that level by definition.
  const handleUseChecklistLevel = () => {
    setFormData((prev) => ({ ...prev, difficulty: levelForRules(Object.keys(prev.requirements)) }));
    setDifficultySource('checklist');
  };

  const handleRemoveRulesAbove = () => {
    setFormData((prev) => {
      const requirements = {};
      Object.entries(prev.requirements).forEach(([ruleId, configuration]) => {
        if (levelAllows(prev.difficulty, ruleId)) requirements[ruleId] = configuration;
      });
      return { ...prev, requirements };
    });
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

  const handleCountChange = (ruleId, rawValue) => {
    const parsed = parseInt(rawValue, 10);
    const count = Number.isNaN(parsed) ? 1 : Math.min(MAX_MIN_COUNT, Math.max(1, parsed));
    setFormData(prev => ({
      ...prev,
      requirements: { ...prev.requirements, [ruleId]: { required: true, min_count: count } },
    }));
  };

  const handleToggleCategory = (category, isChecked) => {
    setFormData(prev => {
      const newReqs = { ...prev.requirements };
      category.rules.forEach(rule => {
        if (isChecked) {
          newReqs[rule.id] = newReqs[rule.id] || { required: true, min_count: 1 };
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
        allVisibleRules.forEach(r => { newReqs[r.id] = newReqs[r.id] || { required: true, min_count: 1 }; });
      }
      return { ...prev, requirements: newReqs };
    });
  };

  // Suggests the difficulty and required constructs from the problem text
  // and an optional reference solution, then applies them to the form.
  const handleAnalyze = async () => {
    const problemText = [formData.description, formData.scenario, formData.instructions]
      .filter((part) => part && part.trim())
      .join('\n\n');

    if (!referenceCode.trim() && !problemText) {
      setAnalyzeError('Write the problem description or paste a reference solution first.');
      return;
    }

    setAnalyzeError('');
    setIsAnalyzing(true);
    try {
      const result = await api.post('/instructors/tasks/analyze-solution', {
        reference_code: referenceCode.trim() ? referenceCode : null,
        description: problemText || null,
      });

      const level = result.difficulty_level;
      const suggested = result.suggested_ast_rules || {};
      const skipped = Object.keys(suggested).filter((ruleId) => !levelAllows(level, ruleId));

      setFormData((prev) => {
        const requirements = {};
        Object.entries(prev.requirements).forEach(([ruleId, configuration]) => {
          if (levelAllows(level, ruleId)) requirements[ruleId] = configuration;
        });
        Object.entries(suggested).forEach(([ruleId, configuration]) => {
          if (levelAllows(level, ruleId) && !requirements[ruleId]) {
            requirements[ruleId] = { required: true, min_count: configuration.min_count || 1 };
          }
        });
        return { ...prev, difficulty: level, requirements };
      });
      setDifficultySource('analyzer');
      setAnalysis({ ...result, constructs: result.constructs || [], skipped });
    } catch (err) {
      setAnalysis(null);
      setAnalyzeError(getErrorMessage(err, 'The activity could not be analyzed. Please try again.'));
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    if (isEdit) return;
    const fetchClassrooms = async () => {
      try {
        const response = await api.get('/classrooms/');
        setClassrooms(response || []);
      } catch (err) {
        setError(`Your classes could not be loaded, so no target class can be selected. ${getErrorMessage(err)}`);
      }
    };
    fetchClassrooms();
  }, [isEdit]);

  useEffect(() => {
    if (!isEdit) return undefined;
    let cancelled = false;
    const loadTask = async () => {
      setIsLoadingTask(true);
      setLoadError(null);
      try {
        const [task, classList] = await Promise.all([
          api.get(`/instructors/tasks/${editId}`),
          api.get('/classrooms/').catch(() => []),
        ]);
        if (cancelled) return;
        const requirements = toEditorRequirements(task.required_ast_rules);
        setOriginal({ ...task, editorRequirements: requirements });
        setClassrooms(classList || []);
        setFormData({
          ...EMPTY_FORM,
          title: task.title || '',
          class_ids: task.class_id ? [task.class_id] : [],
          due_at: task.due_at ? new Date(task.due_at) : null,
          scheduled_publish_at: task.scheduled_publish_at ? new Date(task.scheduled_publish_at) : null,
          description: task.description || '',
          scenario: task.scenario || '',
          instructions: task.instructions || '',
          solution_explanation: task.solution_explanation || '',
          requirements,
          starter_code: task.starter_code || '',
          activity_type: task.activity_type || 'laboratory',
          difficulty: task.difficulty || '',
          allow_paste: task.paste_policy !== 'disabled',
        });
        setDifficultySource('saved');
      } catch (err) {
        if (!cancelled) setLoadError(err);
      } finally {
        if (!cancelled) setIsLoadingTask(false);
      }
    };
    loadTask();
    return () => {
      cancelled = true;
    };
  }, [editId, isEdit]);

  const missingFields = [];
  if (!formData.title.trim()) missingFields.push('a title');
  if (!isEdit && formData.class_ids.length === 0) missingFields.push('a classroom');
  if (!formData.difficulty) missingFields.push('a difficulty level');

  /** Only the fields that differ from the saved activity. */
  const buildUpdatePayload = () => {
    const payload = {};
    if (formData.title.trim() !== original.title) payload.title = formData.title;
    ['description', 'scenario', 'instructions', 'solution_explanation'].forEach((field) => {
      if (optionalText(formData[field]) !== (original[field] ?? null)) payload[field] = formData[field];
    });
    if (formData.starter_code !== (original.starter_code || '')) payload.starter_code = formData.starter_code;
    if (formData.difficulty !== original.difficulty) payload.difficulty = formData.difficulty;
    const pastePolicy = formData.allow_paste ? 'internal_only' : 'disabled';
    if (pastePolicy !== original.paste_policy) payload.paste_policy = pastePolicy;
    if (sortedJson(formData.requirements) !== sortedJson(original.editorRequirements)) {
      payload.required_ast_rules = formData.requirements;
    }
    if (timeOf(formData.due_at) !== timeOf(original.due_at)) {
      payload.due_at = formData.due_at ? new Date(formData.due_at).toISOString() : null;
    }
    if (!original.is_published && timeOf(formData.scheduled_publish_at) !== timeOf(original.scheduled_publish_at)) {
      payload.scheduled_publish_at = formData.scheduled_publish_at ? new Date(formData.scheduled_publish_at).toISOString() : null;
    }
    return payload;
  };

  const handleUpdate = async () => {
    const payload = buildUpdatePayload();
    if (Object.keys(payload).length === 0) {
      navigate(`/instructor/activities/${editId}`);
      return;
    }
    setLoading(true);
    try {
      await api.patch(`/instructors/tasks/${editId}`, payload);
      navigate(`/instructor/activities/${editId}`, { state: { saved: true } });
    } catch (err) {
      setError(getErrorMessage(err, 'The activity could not be saved. Please try again.'));
      scrollFormToTop();
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.title || !formData.title.trim()) {
      setError('Activity title is required.');
      scrollFormToTop();
      return;
    }
    if (!isEdit && (!formData.class_ids || formData.class_ids.length === 0)) {
      setError('Please select at least one classroom.');
      return;
    }
    if (!formData.difficulty) {
      setError('Please select a difficulty level.');
      return;
    }

    if (isEdit) {
      await handleUpdate();
      return;
    }

    setLoading(true);

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
      const tasks = Array.isArray(response) ? response : [response];
      const problems = [];

      // Expected output becomes a visible sample test case on each created activity.
      if (formData.expected_output && formData.expected_output.trim() !== "") {
        for (const task of tasks) {
          try {
            await api.post(`/instructors/tasks/${task.task_id}/test-cases`, {
              name: "Expected output",
              standard_input: "",
              expected_output: formData.expected_output,
              is_hidden: false,
            });
          } catch (tcErr) {
            problems.push(`the sample test case for "${task.title}" (${getErrorMessage(tcErr)})`);
          }
        }
      }

      // Activities are always created as drafts; publish afterwards when requested.
      if (formData.is_published) {
        for (const task of tasks) {
          try {
            await api.patch(`/instructors/tasks/${task.task_id}/publication`, { is_published: true });
          } catch (pubErr) {
            problems.push(`publishing "${task.title}" (${getErrorMessage(pubErr)})`);
          }
        }
      }

      if (problems.length > 0) {
        setError(`The activity was created, but these steps failed: ${problems.join("; ")}. You can finish them from the activity page.`);
        scrollFormToTop();
        if (tasks.length === 1) {
          setCreatedTaskId(tasks[0].task_id);
        }
        return;
      }

      if (tasks.length === 1) {
        navigate(`/instructor/activities/${tasks[0].task_id}`);
      } else {
        navigate('/instructor/dashboard');
      }
    } catch (err) {
      setError(getErrorMessage(err, 'The activity could not be created. Please try again.'));
      scrollFormToTop();
    } finally {
      setLoading(false);
    }
  };

  const visibleGroups = AST_GROUPS.filter(group => group.levels.includes(formData.difficulty || 'expert'));
  const allVisibleRules = visibleGroups.flatMap(g => g.rules);
  const allVisibleSelected = allVisibleRules.length > 0 && allVisibleRules.every(r => formData.requirements[r.id]);
  const selectedLevel = DIFFICULTY_LEVELS.find((level) => level.id === formData.difficulty);
  const checkedRuleIds = Object.keys(formData.requirements);
  const checklistLevel = levelForRules(checkedRuleIds);
  const rulesAboveLevel = formData.difficulty
    ? checkedRuleIds.filter((ruleId) => !levelAllows(formData.difficulty, ruleId))
    : [];
  const isPublishedTask = Boolean(original?.is_published);
  const editedClass = isEdit ? classrooms.find((cls) => cls.class_id === original?.class_id) : null;

  const shell = (content) => (
    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">
      <div className="flex h-full">
        <InstructorSidebar />
      </div>
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <main className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <div className="w-full">{content}</div>
        </main>
      </div>
    </div>
  );

  if (isEdit && isLoadingTask) return shell(<LoadingState label="Loading activity…" />);
  if (isEdit && loadError) {
    return shell(<ErrorState error={loadError} resource="this activity" onRetry={() => window.location.reload()} />);
  }

  return shell(
    <>
            <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">
              <div>
                <p className="mb-1 font-mono text-xs font-bold uppercase tracking-widest text-text-brand">MANAGEMENT</p>
                <h1 className="text-2xl font-bold tracking-tight text-text-main">{isEdit ? "Edit Activity" : "Create New Activity"}</h1>
                <p className="mt-1 text-sm text-text-muted">
                  {isEdit
                    ? "Change the problem, requirements or deadline. Students are notified when a published activity's deadline changes."
                    : "Author new laboratory activities, code templates, and automated AST testing guidelines."}
                </p>
              </div>
            </header>

            {error && (
              <InlineAlert tone="error" className="mb-6">
                {error}
                {createdTaskId && (
                  <button type="button" onClick={() => navigate(`/instructor/activities/${createdTaskId}`)} className="ml-2 font-semibold underline">
                    Open the activity
                  </button>
                )}
              </InlineAlert>
            )}

            <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-6" noValidate>
              {/* Left Column: Details & Instructions (7 cols) */}
              <div className="lg:col-span-7 space-y-5 bg-bg-glass p-6 rounded-2xl border border-border-subtle">
                <h2 className="text-sm font-bold uppercase tracking-wider text-text-brand pb-2 border-b border-border-subtle">
                  Activity Details
                </h2>

                <div>
                  <label htmlFor="title" className={LABEL_CLASS}>
                    Activity Title <span className="text-text-brand">*</span>
                  </label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                    maxLength={200}
                    placeholder="e.g. Lab Activity 3 — Fibonacci Sequence"
                    className={INPUT_CLASS}
                  />
                </div>

                {isEdit ? (
                  <div>
                    <p className={LABEL_CLASS}>Classroom</p>
                    <p className="rounded-xl border border-border-subtle bg-bg-base px-3 py-2.5 text-sm text-text-main">
                      {editedClass ? classLabel(editedClass) : `Class ${original?.class_id ?? ''}`}
                    </p>
                  </div>
                ) : (
                <div>
                  <p className={LABEL_CLASS}>
                    Target Classroom(s) <span className="text-text-brand">*</span>
                  </p>
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
                                ? 'bg-psu-maroon/10 border-psu-maroon/30 shadow-sm'
                                : 'bg-bg-base border-border-subtle hover:border-border-strong'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-medium select-none ${isSelected ? 'text-text-brand' : 'text-text-main'}`}>
                                {classLabel(cls)}
                              </span>
                            </div>
                            <div className={`w-5 h-5 rounded flex items-center justify-center transition-colors ${
                              isSelected
                                ? 'bg-psu-maroon border-psu-maroon text-bg-panel'
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
                )}

                <div>
                  <label htmlFor="description" className={LABEL_CLASS}>Problem Description</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={4}
                    maxLength={5000}
                    placeholder="What problem must the program solve? e.g. Compute the average of a list of quiz scores and report the highest one."
                    className={INPUT_CLASS}
                  />
                </div>

                <div>
                  <label htmlFor="scenario" className={LABEL_CLASS}>Real-world Scenario / Context <span className="font-normal text-text-muted">(optional)</span></label>
                  <textarea
                    id="scenario"
                    name="scenario"
                    value={formData.scenario}
                    onChange={handleChange}
                    rows={3}
                    maxLength={5000}
                    placeholder="Where does this problem come up? e.g. A canteen cashier needs to total each customer's order and give change."
                    className={INPUT_CLASS}
                  />
                </div>

                <div>
                  <label htmlFor="instructions" className={LABEL_CLASS}>Detailed Student Instructions</label>
                  <textarea
                    id="instructions"
                    name="instructions"
                    value={formData.instructions}
                    onChange={handleChange}
                    rows={7}
                    maxLength={10000}
                    placeholder="Step-by-step instructions for completing the task..."
                    className={INPUT_CLASS}
                  />
                </div>

                <div>
                  <label htmlFor="solution_explanation" className={LABEL_CLASS}>
                    Explanation of the Solution <span className="font-normal text-text-muted">(optional)</span>
                  </label>
                  <textarea
                    id="solution_explanation"
                    name="solution_explanation"
                    value={formData.solution_explanation}
                    onChange={handleChange}
                    rows={4}
                    maxLength={10000}
                    placeholder="Why does a correct solution work? Students see this only after their grade is released."
                    className={INPUT_CLASS}
                  />
                  <p className="mt-1 text-xs text-text-muted">Shown to each student only after their grade for this activity is released.</p>
                </div>

                <section className="rounded-xl border border-border-subtle bg-bg-base p-4" aria-labelledby="analyzer-heading">
                  <h3 id="analyzer-heading" className="text-sm font-bold text-text-main">Analyze the activity</h3>
                  <p className="mt-0.5 text-xs text-text-muted">
                    Reads the problem text above and an optional reference solution, then suggests the difficulty and the required constructs (loops, functions, file handling, …). The solution is parsed, never run, and is not saved.
                  </p>
                  <label htmlFor="reference_code" className="mt-3 block text-xs font-semibold text-text-main">
                    Reference solution <span className="font-normal text-text-muted">(optional)</span>
                  </label>
                  <textarea
                    id="reference_code"
                    value={referenceCode}
                    onChange={(e) => setReferenceCode(e.target.value)}
                    rows={6}
                    maxLength={100000}
                    spellCheck={false}
                    placeholder="# Paste a working solution here..."
                    className="mt-1 w-full resize-y rounded-xl border border-border-subtle bg-bg-panel p-3 font-mono text-xs text-text-main focus:border-psu-maroon focus:outline-none"
                  />
                  {analyzeError && <p className="mt-2 text-xs text-text-rose">{analyzeError}</p>}
                  <div className="mt-3 flex justify-end">
                    <button type="button" onClick={handleAnalyze} disabled={isAnalyzing} className="btn-secondary btn-sm">
                      {isAnalyzing ? "Analyzing…" : "Analyze and suggest"}
                    </button>
                  </div>
                  {analysis && <AnalysisSummary analysis={analysis} />}
                </section>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 relative">
                  {isEdit ? (
                    <p className="text-xs text-text-muted sm:pt-7">
                      Test cases, including the expected output, are managed on the activity page.
                    </p>
                  ) : (
                  <div>
                    <label htmlFor="expected_output" className={LABEL_CLASS}>Expected Output</label>
                    <textarea
                      id="expected_output"
                      name="expected_output"
                      value={formData.expected_output}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Target output string..."
                      className="w-full bg-bg-base border border-border-subtle rounded-xl p-3 font-mono text-xs text-text-brand focus:outline-none focus:border-psu-maroon transition-colors h-full"
                    />
                  </div>
                  )}

                  <div className="relative h-full flex flex-col gap-4">
                    <div>
                      <p className={LABEL_CLASS}>
                        Difficulty Level <span className="text-text-brand">*</span>
                      </p>
                      <div className="flex bg-bg-base border border-border-subtle rounded-xl p-1" role="group" aria-label="Difficulty level">
                        {DIFFICULTY_LEVELS.map(level => (
                          <button
                            key={level.id}
                            type="button"
                            onClick={() => handleDifficultyChange(level.id)}
                            aria-pressed={formData.difficulty === level.id}
                            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-colors ${
                              formData.difficulty === level.id
                                ? 'bg-bg-glass text-text-brand shadow-sm border border-border-subtle'
                                : 'text-text-muted hover:text-text-main hover:bg-bg-glass/50'
                            }`}
                          >
                            {level.label}
                          </button>
                        ))}
                      </div>
                      <p className="mt-1.5 text-xs text-text-muted">
                        {selectedLevel ? selectedLevel.definition : "Pick a level, or use “Analyze and suggest”."}
                      </p>
                      <DifficultyStatus
                        difficulty={formData.difficulty}
                        source={difficultySource}
                        checklistLevel={checklistLevel}
                        ruleCount={checkedRuleIds.length}
                        rulesAbove={rulesAboveLevel}
                        onUseChecklistLevel={handleUseChecklistLevel}
                        onRemoveRulesAbove={handleRemoveRulesAbove}
                      />
                    </div>

                    <div className="flex-1 relative min-h-[200px]">
                      <div className="mb-1.5 flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                        <span className="text-sm font-semibold text-text-main">AST Checklist Requirements</span>
                        <div className="flex items-center gap-4 whitespace-nowrap">
                          {formData.difficulty && (
                            <label className="flex items-center gap-2 cursor-pointer group">
                              <span className="text-xs font-bold uppercase tracking-wider text-text-brand">
                                Toggle all
                              </span>
                              <div className="relative inline-flex items-center">
                                <input
                                  type="checkbox"
                                  checked={allVisibleSelected}
                                  onChange={(e) => handleSelectAllVisible(e.target.checked)}
                                  className="sr-only peer"
                                />
                                <div className="w-8 h-4 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-psu-maroon group-hover:bg-text-muted/30 peer-checked:group-hover:bg-psu-maroon-dark shadow-inner"></div>
                              </div>
                            </label>
                          )}
                          <span className="text-text-muted font-normal text-xs">{Object.keys(formData.requirements).length} active</span>
                        </div>
                      </div>
                      <div className={`flex flex-col h-full transition-opacity duration-300 ${!formData.difficulty ? 'opacity-30 pointer-events-none blur-[2px]' : ''}`}>
                        {visibleGroups.map((group) => (
                          <ASTCategoryAccordion
                            key={group.title}
                            category={group}
                            requirements={formData.requirements}
                            onToggleRule={handleToggleRule}
                            onToggleCategory={handleToggleCategory}
                            onCountChange={handleCountChange}
                          />
                        ))}
                      </div>
                      {!formData.difficulty && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center z-10 p-4 text-center mt-6">
                          <div className="bg-bg-panel/90 backdrop-blur-sm border border-border-strong rounded-xl p-4 shadow-lg shadow-black/20">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-text-brand" aria-hidden="true">
                              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            <p className="text-sm font-bold text-text-main mb-1">Requirements Locked</p>
                            <p className="text-xs text-text-muted">Select a Difficulty Level first to configure AST requirements.</p>
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
                  <h2 className="text-sm font-bold uppercase tracking-wider text-text-brand pb-2 border-b border-border-subtle mb-4">
                    Starter Code Template
                  </h2>

                  <div className="flex-1 min-h-[220px]">
                    <textarea
                      id="starter_code"
                      name="starter_code"
                      aria-label="Starter code template"
                      value={formData.starter_code}
                      onChange={handleChange}
                      rows={12}
                      placeholder="# Write initial starter code template for students..."
                      className="w-full h-full bg-bg-base border border-border-subtle rounded-xl p-4 text-text-main font-mono text-xs focus:outline-none focus:border-psu-maroon transition-colors resize-none"
                    />
                  </div>
                </div>

                <div className="bg-bg-glass p-6 rounded-2xl border border-border-subtle space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">Options & Controls</h3>

                  <div className="flex flex-col gap-6">
                    <div className="flex flex-wrap items-center gap-8">
                      {!isEdit && (
                      <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            name="is_published"
                            checked={formData.is_published}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-psu-maroon group-hover:bg-text-muted/30 peer-checked:group-hover:bg-psu-maroon-dark"></div>
                        </div>
                        <span className="text-sm font-semibold text-text-main select-none">Publish immediately</span>
                      </label>
                      )}

                      <label className="relative inline-flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            name="allow_paste"
                            checked={formData.allow_paste}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-border-strong rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-panel after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-psu-maroon group-hover:bg-text-muted/30 peer-checked:group-hover:bg-psu-maroon-dark"></div>
                        </div>
                        <span className="text-sm font-semibold text-text-main select-none">Allow workspace clipboard paste</span>
                      </label>
                    </div>

                    <div className="flex flex-col gap-4">
                      {!isPublishedTask && (
                        <div className={`animate-fade-in transition-opacity ${formData.is_published ? 'opacity-30 pointer-events-none' : ''} ${formData.class_ids.length > 1 ? 'opacity-50' : ''}`}>
                          <label htmlFor="scheduled_publish_at" className={`${LABEL_CLASS} flex items-center justify-between`}>
                            <span>Scheduled Publish Date <span className="text-text-muted font-normal ml-1">(Optional)</span></span>
                          </label>
                          <div className="relative group flex">
                            <Flatpickr
                              id="scheduled_publish_at"
                              data-enable-time
                              value={formData.scheduled_publish_at}
                              onChange={([date]) => setFormData(prev => ({ ...prev, scheduled_publish_at: date || null }))}
                              disabled={formData.is_published || formData.class_ids.length > 1}
                              className={`w-full bg-bg-glass border border-border-subtle rounded-xl pl-4 pr-10 py-2.5 text-sm focus:outline-none focus:border-psu-maroon/50 focus:ring-1 focus:ring-psu-maroon/20 transition-all group-hover:border-border-strong shadow-inner ${formData.class_ids.length > 1 ? 'text-text-muted cursor-not-allowed' : 'text-text-main cursor-pointer'}`}
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
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            </div>
                          </div>
                          {formData.class_ids.length > 1 && (
                            <p className="mt-2 text-xs text-text-amber flex items-center gap-1.5">
                              Scheduling is disabled when assigning to multiple classrooms.
                            </p>
                          )}
                        </div>
                      )}

                      <div>
                        <label htmlFor="due_at" className={`${LABEL_CLASS} flex items-center justify-between`}>
                          <span>Deadline / Due Date <span className="text-text-muted font-normal ml-1">(Optional)</span></span>
                          {formData.due_at && (
                            <button
                              type="button"
                              onClick={() => setFormData(prev => ({ ...prev, due_at: null }))}
                              className="text-xs font-semibold text-text-brand hover:underline"
                            >
                              Remove deadline
                            </button>
                          )}
                        </label>
                        <div className="relative group flex">
                          <Flatpickr
                            id="due_at"
                            data-enable-time
                            value={formData.due_at}
                            onChange={([date]) => setFormData(prev => ({ ...prev, due_at: date || null }))}
                            className="w-full bg-bg-glass border border-border-subtle rounded-xl pl-4 pr-10 py-2.5 text-sm text-text-main focus:outline-none focus:border-psu-maroon/50 focus:ring-1 focus:ring-psu-maroon/20 transition-all group-hover:border-border-strong shadow-inner cursor-pointer"
                            placeholder="Select deadline"
                            options={{
                              dateFormat: "Y-m-d H:i",
                              time_24hr: false,
                              altInput: true,
                              altFormat: "M j, Y h:i K"
                            }}
                          />
                          <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-text-muted group-hover:text-text-brand transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                        </div>
                        {isPublishedTask && (
                          <p className="mt-1.5 text-xs text-text-muted">
                            Moving the deadline of a published activity reopens or closes it for every student and notifies them. To give one student another attempt after the deadline, use “Allow another attempt” in the Grading Bench.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2 pt-3 border-t border-border-subtle">
                    {missingFields.length > 0 && (
                      <p className="text-xs text-text-muted" id="submit-hint">
                        Add {missingFields.length > 1 ? `${missingFields.slice(0, -1).join(", ")} and ${missingFields.at(-1)}` : missingFields[0]} to continue.
                      </p>
                    )}
                    <div className="flex items-center justify-end gap-3">
                      <button
                        type="button"
                        onClick={() => navigate(-1)}
                        className="px-4 py-2 text-sm font-semibold text-text-muted hover:text-text-main transition-colors cursor-pointer"
                      >
                        Cancel
                      </button>

                      <button
                        type="submit"
                        disabled={loading || missingFields.length > 0}
                        aria-describedby={missingFields.length > 0 ? "submit-hint" : undefined}
                        className="px-5 py-2.5 bg-psu-maroon hover:bg-psu-maroon-dark text-white rounded-xl text-sm font-bold shadow-md shadow-psu-maroon/20 transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isEdit ? (loading ? "Saving..." : "Save Changes") : (loading ? "Creating..." : "Create Activity")}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </form>
    </>
  );
};

export default ActivityEditor;

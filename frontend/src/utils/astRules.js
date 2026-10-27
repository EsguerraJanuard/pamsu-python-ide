/**
 * AST requirement catalogue shared by the activity editor, the practice
 * module editor, the student workspace and the grading bench.
 *
 * Rule ids match backend/app/services/ast_evaluator.py. The difficulty
 * levels on each group match RULE_LEVELS in backend/app/services/ast_analyzer.py:
 * a group can be required from its lowest level upward.
 */

export const DIFFICULTY_LEVELS = [
  { id: "beginner", label: "Beginner", definition: "Input/output, conditionals and loops." },
  { id: "intermediate", label: "Intermediate", definition: "Adds functions, data structures and file handling." },
  { id: "expert", label: "Expert", definition: "Adds classes, exception handling, lambdas and other advanced constructs." },
];

export const AST_GROUPS = [
  {
    title: "Output & Input",
    levels: ["beginner", "intermediate", "expert"],
    rules: [
      { id: "require_print_call", label: "print() call" },
      { id: "require_input_call", label: "input() call" },
    ],
  },
  {
    title: "Control Flow",
    levels: ["beginner", "intermediate", "expert"],
    rules: [
      { id: "require_if_statement", label: "if statement" },
      { id: "require_for_loop", label: "for loop" },
      { id: "require_while_loop", label: "while loop" },
      { id: "require_break_statement", label: "break statement" },
      { id: "require_continue_statement", label: "continue statement" },
      { id: "require_with_statement", label: "with statement" },
      { id: "require_pass_statement", label: "pass statement" },
    ],
  },
  {
    title: "Functions",
    levels: ["intermediate", "expert"],
    rules: [
      { id: "require_function_def", label: "Function definition" },
      { id: "require_function_call", label: "Function call" },
      { id: "require_return_statement", label: "return statement" },
      { id: "require_global", label: "global keyword" },
      { id: "require_nonlocal", label: "nonlocal keyword" },
    ],
  },
  {
    title: "Data Structures",
    levels: ["intermediate", "expert"],
    rules: [
      { id: "require_list", label: "List literal" },
      { id: "require_dict", label: "Dictionary literal" },
      { id: "require_tuple", label: "Tuple literal" },
      { id: "require_set", label: "Set literal" },
      { id: "require_list_comprehension", label: "List comprehension" },
      { id: "require_dict_comprehension", label: "Dictionary comprehension" },
      { id: "require_del_statement", label: "del statement" },
    ],
  },
  {
    title: "File Handling",
    levels: ["intermediate", "expert"],
    rules: [{ id: "require_open_call", label: "open() call" }],
  },
  {
    title: "OOP & Advanced",
    levels: ["expert"],
    rules: [
      { id: "require_class_def", label: "Class definition" },
      { id: "require_try_except", label: "try/except block" },
      { id: "require_lambda", label: "Lambda function" },
      { id: "require_import", label: "import statement" },
      { id: "require_match_statement", label: "match statement" },
      { id: "require_yield", label: "yield (generator)" },
      { id: "require_assert_statement", label: "assert statement" },
      { id: "require_raise_statement", label: "raise statement" },
      { id: "require_decorator", label: "Decorator (@)" },
      { id: "require_async_function", label: "async def" },
      { id: "require_await", label: "await" },
    ],
  },
];

const RULE_LABELS = Object.fromEntries(AST_GROUPS.flatMap((group) => group.rules.map((rule) => [rule.id, rule.label])));

// Older activities may still use these names.
RULE_LABELS.require_function = RULE_LABELS.require_function_def;
RULE_LABELS.require_class = RULE_LABELS.require_class_def;

/** Readable name for a rule id, e.g. "require_for_loop" -> "for loop". */
export function ruleLabel(ruleId) {
  if (RULE_LABELS[ruleId]) return RULE_LABELS[ruleId];
  const text = String(ruleId || "").replace(/^require_/, "").replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Lowest difficulty at which a rule can be required. */
export function ruleLevel(ruleId) {
  const group = AST_GROUPS.find((g) => g.rules.some((rule) => rule.id === ruleId));
  return group ? group.levels[0] : "beginner";
}

const LEVEL_IDS = DIFFICULTY_LEVELS.map((level) => level.id);

/**
 * Difficulty detected from required rules: the highest level among them,
 * "beginner" when there are none. Same rule as the backend
 * (highest_level in backend/app/services/ast_analyzer.py).
 */
export function levelForRules(ruleIds) {
  return ruleIds.reduce((highest, ruleId) => {
    const level = ruleLevel(ruleId);
    return LEVEL_IDS.indexOf(level) > LEVEL_IDS.indexOf(highest) ? level : highest;
  }, "beginner");
}

/** Minimum count from a stored rule configuration (true, a number, or { min_count }). */
export function ruleMinCount(configuration) {
  if (typeof configuration === "number") return configuration;
  if (configuration && typeof configuration === "object") return configuration.min_count ?? 1;
  return 1;
}

/** Rule ids that are actually required by a stored rule map. */
export function requiredRuleIds(rules) {
  return Object.entries(rules || {})
    .filter(([, configuration]) => {
      if (typeof configuration === "boolean") return configuration;
      if (typeof configuration === "number") return configuration > 0;
      if (configuration && typeof configuration === "object") return configuration.required !== false;
      return true;
    })
    .map(([ruleId]) => ruleId);
}

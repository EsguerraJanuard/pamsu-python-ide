/*
 * Review indicator thresholds: when a coding-session count is colored on the
 * Grading Bench and Live Monitoring. One place, so both screens agree.
 *
 * Levels: "typical" (no color), "above" (gold, "Above typical"),
 * "wellAbove" (red, "Well above typical"). A count is at a level when it is
 * at or above that level's number. The colors guide the instructor's
 * attention; they are not evidence of misconduct and never set a grade.
 *
 * Why these numbers (laboratory activities):
 * - Blocked pastes (1 / 3): a paste is counted only when it carries text from
 *   outside the workspace (the student's own Ctrl+C / Ctrl+V inside the
 *   editor is not counted), and each one shows the student a notice. One try
 *   is worth a look; three, after the notice each time, is a pattern.
 * - Tab switches (4 / 10): counted when the page is hidden (another tab, a
 *   minimised or covered window, a locked screen). About one per 30 minutes
 *   is ordinary in a 1–3 hour lab, so up to 3 stays uncolored.
 * - Pointer exits (10 / 25): counted every time the mouse crosses the browser
 *   window edge (tab bar, taskbar, second monitor, touchpad overshoot) and
 *   with most mouse-driven tab switches, so it is the noisiest signal and has
 *   the loosest numbers, about 2.5× the tab-switch ones.
 *
 * Homework is done outside class, over several days, with resources allowed,
 * and the counts add up across visits, so tab switches and pointer exits are
 * never colored for homework. Blocked pastes keep their numbers: the paste
 * policy applies at home too.
 *
 * These are starting values. Re-check them against pilot data: gold near the
 * 90th percentile and red near the 98th percentile of laboratory sessions.
 */
export const INDICATOR_THRESHOLDS = {
  blocked_paste_count: { above: 1, wellAbove: 3, coloredForHomework: true },
  tab_switch_count: { above: 4, wellAbove: 10, coloredForHomework: false },
  mouseleave_count: { above: 10, wellAbove: 25, coloredForHomework: false },
};

export const INDICATOR_LEVELS = {
  typical: { tone: "neutral", label: null },
  above: { tone: "attention", label: "Above typical" },
  wellAbove: { tone: "danger", label: "Well above typical" },
};

/**
 * Level for one count. `field` is the coding-session field name
 * (tab_switch_count, blocked_paste_count, mouseleave_count); unknown fields,
 * missing counts and uncolored homework signals are "typical".
 */
export function indicatorLevel(field, count, activityType) {
  const rule = INDICATOR_THRESHOLDS[field];
  if (!rule || typeof count !== "number") return INDICATOR_LEVELS.typical;
  if (activityType === "homework" && !rule.coloredForHomework) return INDICATOR_LEVELS.typical;
  if (count >= rule.wellAbove) return INDICATOR_LEVELS.wellAbove;
  if (count >= rule.above) return INDICATOR_LEVELS.above;
  return INDICATOR_LEVELS.typical;
}

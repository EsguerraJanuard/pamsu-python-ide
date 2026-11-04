import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DiffEditor } from "@monaco-editor/react";

import PageShell from "../../../components/layout/PageShell";
import ConfirmationModal from "../../../components/modals/ConfirmationModal";
import { EmptyState, ErrorState, FieldError, InlineAlert, LoadingState, PageHeader, Spinner } from "../../../components/ui/StateViews";
import Avatar from "../../../components/ui/Avatar";
import Icon from "../../../components/ui/Icon";
import StatTile from "../../../components/ui/StatTile";
import Switch from "../../../components/ui/Switch";
import api, { API_BASE_URL, getErrorMessage } from "../../../services/api";
import { ruleLabel } from "../../../utils/astRules";
import { INDICATOR_THRESHOLDS, indicatorLevel } from "../../../utils/reviewIndicators";
import { classLabel, formatDateTime, humanize } from "../../../utils/format";
import { useTheme } from "../../theme/ThemeContext";
import { defineEditorThemes, editorThemeFor } from "../../workspace/editorThemes";

const MAX_SCORE = 100;

const STATUS_BADGE = {
  graded: { label: "Graded", badge: "badge-success" },
  rejected: { label: "Returned", badge: "badge-danger" },
  submitted: { label: "Submitted", badge: "badge-brand" },
  awaiting_review: { label: "Awaiting review", badge: "badge-brand" },
};

/** Score input and feedback textarea: soft border, rounded, clear focus ring. */
const GRADE_FIELD =
  "block w-full rounded-xl border border-border-strong bg-bg-panel text-text-main shadow-sm transition-[border-color,box-shadow] duration-150 placeholder:text-[var(--text-placeholder)] hover:border-text-muted/60 focus:border-border-focus focus:outline-none focus:ring-2 focus:ring-border-focus/35 disabled:cursor-not-allowed disabled:bg-bg-alt disabled:text-text-muted disabled:shadow-none aria-[invalid=true]:border-psu-red aria-[invalid=true]:focus:ring-psu-red/25";

const FEEDBACK_MAX_LENGTH = 5000;

/** Student-list filters on the bench: [value, label]. */
const STUDENT_FILTERS = [
  ["all", "All"],
  ["review", "To review"],
  ["graded", "Graded"],
  ["none", "Not submitted"],
];

/*
 * Review indicators use the shared StatTile. Session counts are colored by the
 * shared thresholds in utils/reviewIndicators.js (also used by Live
 * Monitoring). Similarity stays neutral: the score has no cut-off, and honest
 * work on a short task can match 100% (backend/algorithm_qa_results.md).
 * [label, icon, coding-session field, caption]
 */
const SESSION_INDICATORS = [
  ["Tab switches", "window", "tab_switch_count", "Times the student left the tab"],
  ["Blocked pastes", "clipboardX", "blocked_paste_count", "Paste attempts that were blocked"],
  ["Pointer exits", "pointer", "mouseleave_count", "Times the pointer left the page"],
];

const STRUCTURE_PILLS = {
  found: {
    label: "Found",
    className: "bg-emerald-600/10 text-text-emerald ring-emerald-600/25",
    icon: <path d="M3.5 8.5l3 3 6-7" />,
  },
  missing: {
    label: "Missing",
    className: "bg-psu-gold/15 text-text-amber ring-psu-gold/40",
    icon: <path d="M4.5 4.5l7 7M11.5 4.5l-7 7" />,
  },
  unknown: {
    label: "Not evaluated",
    className: "bg-bg-alt text-text-muted ring-border-strong",
    icon: <path d="M4 8h8" />,
  },
};

/** Found / Missing / Not evaluated pill for one required AST structure. */
function StructurePill({ passed }) {
  const pill = STRUCTURE_PILLS[passed === true ? "found" : passed === false ? "missing" : "unknown"];
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full py-1 pl-2 pr-2.5 text-xs font-semibold ring-1 ring-inset ${pill.className}`}>
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {pill.icon}
      </svg>
      {pill.label}
    </span>
  );
}

/**
 * Findings of an AST analysis. Stored finding rows are used when present;
 * otherwise the evaluator's own result in `details` (what evaluation saves).
 */
function analysisFindings(analysis) {
  if (!analysis) return [];
  if (analysis.findings?.length) return analysis.findings;
  return (analysis.details?.findings || []).map((finding) => ({
    finding_id: finding.rule,
    rule_key: finding.rule,
    label: finding.label,
    passed: finding.passed,
    required_count: finding.required_count,
    detected_count: finding.detected_count,
  }));
}

/**
 * Score suggested by the structure check: the share of required AST
 * structures that were found. It only pre-fills the form; the instructor
 * reviews the indicators, adjusts and saves the official grade.
 */
function suggestScore(analysis, maxScore) {
  if (!analysis || analysis.syntax_error) return null;
  const findings = analysisFindings(analysis).filter((finding) => typeof finding.passed === "boolean");
  if (findings.length === 0) return null;
  const found = findings.filter((finding) => finding.passed).length;
  return { score: Math.round((maxScore * found) / findings.length), found, total: findings.length };
}

async function loadAllQueueItems(taskId) {
  const items = [];
  let page = 1;
  let totalPages;
  do {
    const response = await api.get(`/instructors/review-queue?task_id=${taskId}&page=${page}&page_size=100`);
    items.push(...(response?.items || []));
    totalPages = response?.total_pages || 1;
    page += 1;
  } while (page <= totalPages && page <= 20);
  return items;
}

/** One representative attempt per student: the official one, else the newest. */
function pickSubmissions(items) {
  const byStudent = {};
  items.forEach((item) => {
    const studentId = item.student?.student_id;
    if (!studentId) return;
    const current = byStudent[studentId];
    if (!current || (item.is_official && !current.is_official) ||
      (item.is_official === current.is_official && new Date(item.submitted_at) > new Date(current.submitted_at))) {
      byStudent[studentId] = item;
    }
  });
  return byStudent;
}

function SubmissionReview({ submission, task, onGraded }) {
  const { effectiveTheme } = useTheme();
  const [details, setDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [score, setScore] = useState("");
  const [feedback, setFeedback] = useState("");
  const [release, setRelease] = useState(false);
  const [scoreError, setScoreError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [suggestion, setSuggestion] = useState(null);
  const [isRetakeConfirmOpen, setIsRetakeConfirmOpen] = useState(false);
  const [isGrantingRetake, setIsGrantingRetake] = useState(false);
  const [retakeMessage, setRetakeMessage] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [evaluation, record, executions] = await Promise.all([
        api.get(`/evaluation/submissions/${submission.sub_id}`),
        api.get(`/instructors/submissions/${submission.sub_id}`),
        api
          .get(`/instructors/tasks/${submission.activity.task_id}/execution-requests?student_id=${submission.student.student_id}&request_kind=submit`)
          .catch(() => []),
      ]);
      let session = null;
      if (record?.coding_session_id) {
        session = await api.get(`/instructors/coding-sessions/${record.coding_session_id}`).catch(() => null);
      }
      const execution = (Array.isArray(executions) ? executions : []).find((e) => e.submission_id === submission.sub_id) || null;
      setDetails({ evaluation, session, execution, record, sourceCode: record?.raw_code || execution?.source_code || "" });

      const grade = evaluation?.instructor_grade;
      const latestAnalysis = (evaluation?.ast_analyses || []).slice(-1)[0] || null;
      const suggested = grade ? null : suggestScore(latestAnalysis, MAX_SCORE);
      setSuggestion(suggested);
      setScore(grade ? String(grade.score) : suggested ? String(suggested.score) : "");
      setFeedback(grade?.feedback || "");
      setRelease(Boolean(grade?.is_released));
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [submission]);

  useEffect(() => {
    load();
  }, [load]);

  // The code diff's two text models. @monaco-editor/react disposes them before
  // the diff editor, which Monaco 0.55 reports as "TextModel got disposed
  // before DiffEditorWidget model got reset". So the DiffEditor keeps them
  // (keepCurrent*Model) and they are disposed here, once the editor is gone.
  const diffModelsRef = useRef(null);
  useEffect(
    () => () => {
      const models = diffModelsRef.current;
      diffModelsRef.current = null;
      if (!models) return;
      setTimeout(() => {
        models.original?.dispose();
        models.modified?.dispose();
      }, 0);
    },
    [],
  );

  const handleSave = async (event) => {
    event.preventDefault();
    const value = Number(score);
    if (score.trim() === "" || Number.isNaN(value)) {
      setScoreError("Enter a score.");
      return;
    }
    if (value < 0 || value > MAX_SCORE) {
      setScoreError(`The score must be between 0 and ${MAX_SCORE}.`);
      return;
    }
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const saved = await api.put(`/evaluation/submissions/${submission.sub_id}/grade`, {
        score: value,
        max_score: details?.evaluation?.instructor_grade?.max_score || MAX_SCORE,
        feedback: feedback.trim() || null,
        is_released: release,
      });
      setDetails((prev) => ({ ...prev, evaluation: { ...prev.evaluation, instructor_grade: saved } }));
      setSaveMessage({ tone: "success", text: release ? "Grade saved and released to the student." : "Grade saved. It is not visible to the student until released." });
      onGraded?.(Boolean(saved?.is_released ?? release));
    } catch (err) {
      setSaveMessage({ tone: "error", text: getErrorMessage(err, "The grade could not be saved.") });
    } finally {
      setIsSaving(false);
    }
  };

  const handleGrantRetake = async () => {
    setIsGrantingRetake(true);
    setRetakeMessage(null);
    try {
      const updated = await api.post(`/instructors/submissions/${submission.sub_id}/retake`);
      setDetails((prev) => ({ ...prev, record: { ...prev.record, ...updated } }));
      setRetakeMessage({ tone: "success", text: "Another attempt is allowed. The student was notified and can submit once more, even after the deadline." });
    } catch (err) {
      setRetakeMessage({ tone: "error", text: getErrorMessage(err, "Another attempt could not be allowed.") });
    } finally {
      setIsGrantingRetake(false);
      setIsRetakeConfirmOpen(false);
    }
  };

  if (isLoading) return <LoadingState label="Loading submission…" />;
  if (error) return <ErrorState error={error} resource="this submission" onRetry={load} />;

  const { evaluation, session, execution, record, sourceCode } = details;
  const retakeAllowed = Boolean(record?.retake_allowed);
  const analysis = (evaluation?.ast_analyses || []).slice(-1)[0] || null;
  const findings = analysisFindings(analysis);
  const checkedFindings = analysis && !analysis.syntax_error ? findings.filter((finding) => typeof finding.passed === "boolean") : [];
  const foundCount = checkedFindings.filter((finding) => finding.passed).length;
  const hasSimilarity = typeof evaluation?.jaccard_score === "number";
  const isHomework = task?.activity_type === "homework";
  const savedGrade = evaluation?.instructor_grade;
  const maxScore = savedGrade?.max_score || MAX_SCORE;
  const gradeState = !savedGrade
    ? { label: "Not graded yet", badge: "badge-neutral" }
    : savedGrade.is_released
      ? { label: "Released to student", badge: "badge-success" }
      : { label: "Saved, not released", badge: "badge-gold" };
  const status = STATUS_BADGE[submission.status] || STATUS_BADGE.submitted;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`badge ${status.badge}`}>{status.label}</span>
        <span className="badge badge-neutral">Attempt {submission.attempt_number}</span>
        {submission.is_official && <span className="badge badge-brand">Official</span>}
        <span className="text-xs text-text-muted">Submitted {formatDateTime(submission.submitted_at)}</span>
        {retakeAllowed && <span className="badge badge-gold">Another attempt allowed</span>}
        {!retakeAllowed && record && (
          <button type="button" onClick={() => setIsRetakeConfirmOpen(true)} className="btn-secondary btn-sm ml-auto">
            Allow another attempt
          </button>
        )}
      </div>

      {retakeMessage && (
        <InlineAlert tone={retakeMessage.tone} onDismiss={() => setRetakeMessage(null)}>
          {retakeMessage.text}
        </InlineAlert>
      )}

      <section className="card @container p-5 sm:p-6" aria-labelledby="indicators-heading">
        <div className="mb-5">
          <h3 id="indicators-heading" className="text-sm font-semibold text-text-main">
            Review indicators
          </h3>
          <p className="mt-1 text-xs leading-relaxed text-text-muted">
            Signals to inform your review. They are not evidence of misconduct and do not set the grade.
          </p>
        </div>
        <dl className="grid grid-cols-2 gap-3 @2xl:grid-cols-4">
          <StatTile
            label="Similarity"
            icon="copy"
            value={hasSimilarity ? evaluation.jaccard_score.toFixed(1) : null}
            unit="%"
            meter={hasSimilarity ? evaluation.jaccard_score : undefined}
            caption={hasSimilarity ? "Highest match with a classmate" : "Not computed yet"}
          />
          {SESSION_INDICATORS.map(([label, icon, field, caption]) => {
            const count = session ? (session[field] ?? 0) : null;
            const level = indicatorLevel(field, count, task?.activity_type);
            return (
              <StatTile
                key={label}
                label={label}
                icon={icon}
                value={count}
                caption={session ? caption : "No session record"}
                tone={level.tone}
                status={level.label}
              />
            );
          })}
        </dl>
        {!session && <p className="mt-3 text-xs text-text-muted">No coding-session record is linked to this submission.</p>}
        {session && isHomework && (
          <p className="mt-3 text-xs text-text-muted">
            This is a homework activity, done outside class, so tab switches and pointer exits are shown without color.
          </p>
        )}
        <details className="group mt-3 text-xs text-text-muted">
          <summary className="inline-flex cursor-pointer items-center gap-1 rounded font-medium hover:text-text-main">
            <Icon name="chevronRight" className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
            How the colors are set
          </summary>
          <div className="mt-2 rounded-lg border border-border-subtle bg-bg-alt/50 px-3 py-2.5 leading-relaxed">
            <p className="mb-1.5">
              <span className="font-semibold text-text-amber">Above typical</span> (gold) and{" "}
              <span className="font-semibold text-text-rose">Well above typical</span> (red) start at these counts:
            </p>
            <ul className="space-y-0.5">
              {SESSION_INDICATORS.map(([label, , field]) => {
                const rule = INDICATOR_THRESHOLDS[field];
                return (
                  <li key={field}>
                    {label}: <span className="tabular-nums text-text-main">{rule.above}</span> and{" "}
                    <span className="tabular-nums text-text-main">{rule.wellAbove}</span>
                    {!rule.coloredForHomework && " (not colored for homework)"}
                  </li>
                );
              })}
            </ul>
            <p className="mt-1.5">Similarity is never colored: honest work on a short task can match closely.</p>
          </div>
        </details>

        <div className="mt-6 border-t border-border-subtle pt-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">Structure check (AST)</h4>
            {checkedFindings.length > 0 && (
              <span className="text-xs font-medium tabular-nums text-text-muted">
                {foundCount} of {checkedFindings.length} found
              </span>
            )}
          </div>
          {!analysis ? (
            <p className="rounded-xl border border-dashed border-border-subtle px-4 py-3 text-sm text-text-muted">
              No structure analysis has been recorded for this submission.
            </p>
          ) : analysis.syntax_error ? (
            <p className="rounded-xl border border-psu-red/20 bg-psu-red/[0.06] px-4 py-3 text-sm text-text-rose">
              <span className="font-semibold">Syntax error:</span> {analysis.syntax_error.message || "the code could not be parsed."}
            </p>
          ) : findings.length === 0 ? (
            <p className="rounded-xl border border-dashed border-border-subtle px-4 py-3 text-sm text-text-muted">
              The activity has no required structures to check.
            </p>
          ) : (
            <ul className="divide-y divide-border-subtle overflow-hidden rounded-xl border border-border-subtle">
              {findings.map((finding) => (
                <li
                  key={finding.finding_id || finding.rule_key}
                  className="flex items-center justify-between gap-3 bg-bg-panel px-4 py-3 transition-colors hover:bg-bg-alt/50"
                >
                  <div className="min-w-0">
                    <p className="break-words text-sm font-medium text-text-main">{ruleLabel(finding.rule_key) || finding.label}</p>
                    {typeof finding.detected_count === "number" && (
                      <p className="mt-0.5 text-xs tabular-nums text-text-muted">
                        {finding.detected_count} found · {finding.required_count} needed
                      </p>
                    )}
                  </div>
                  <StructurePill passed={finding.passed} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <form onSubmit={handleSave} noValidate className="card overflow-hidden" aria-labelledby="grade-heading">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border-subtle px-5 py-4 sm:px-6">
          <div className="min-w-0">
            <h3 id="grade-heading" className="text-sm font-semibold text-text-main">
              Grade and feedback
            </h3>
            <p className="mt-1 text-xs text-text-muted">The official grade for this attempt.</p>
          </div>
          <span className={`badge ${gradeState.badge}`}>{gradeState.label}</span>
        </div>

        <div className="space-y-5 px-5 py-5 sm:px-6">
          {saveMessage && (
            <InlineAlert tone={saveMessage.tone} onDismiss={() => setSaveMessage(null)}>
              {saveMessage.text}
            </InlineAlert>
          )}
          {suggestion && !savedGrade && (
            <div role="note" className="flex gap-3 rounded-r-lg border-l-4 border-psu-gold bg-psu-gold/[0.08] py-3 pl-4 pr-4">
              <svg
                width="18"
                height="18"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="mt-px shrink-0 text-text-amber"
                aria-hidden="true"
              >
                <path d="M6 12.5h4M6.75 14.5h2.5M8 1.75a4.25 4.25 0 0 0-2.5 7.69c.47.34.75.88.75 1.46v.1h3.5v-.1c0-.58.28-1.12.75-1.46A4.25 4.25 0 0 0 8 1.75z" />
              </svg>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-text-main">
                  Suggested score: <span className="tabular-nums">{suggestion.score}</span>
                  <span className="font-medium text-text-muted"> / {maxScore}</span>
                </p>
                <p className="mt-0.5 text-xs leading-relaxed text-text-muted">
                  The structure check found {suggestion.found} of {suggestion.total} required structure{suggestion.total === 1 ? "" : "s"}. Review
                  the indicators above, deduct for any problems you find, then save.
                </p>
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-[200px_minmax(0,1fr)]">
            <div>
              <label htmlFor="grade-score" className="field-label">
                Score <span className="sr-only">(out of {maxScore})</span>
              </label>
              <div className="relative">
                <input
                  id="grade-score"
                  type="text"
                  inputMode="decimal"
                  value={score}
                  onChange={(e) => {
                    setScore(e.target.value.replace(/[^\d.]/g, ""));
                    setScoreError("");
                  }}
                  aria-invalid={Boolean(scoreError)}
                  aria-describedby={scoreError ? "grade-score-error" : undefined}
                  className={`${GRADE_FIELD} h-12 pl-4 pr-16 text-xl font-semibold tabular-nums`}
                  disabled={isSaving}
                />
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-sm font-medium text-text-muted"
                >
                  / {maxScore}
                </span>
              </div>
              <FieldError id="grade-score-error">{scoreError}</FieldError>
            </div>
            <div>
              <label htmlFor="grade-feedback" className="field-label">
                Feedback for the student
              </label>
              <textarea
                id="grade-feedback"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                maxLength={FEEDBACK_MAX_LENGTH}
                placeholder="What went well, and what to improve next time…"
                aria-describedby="grade-feedback-hint"
                className={`${GRADE_FIELD} min-h-[8.5rem] resize-y px-4 py-3 text-sm leading-relaxed`}
                disabled={isSaving}
              />
              <div className="mt-1.5 flex items-start justify-between gap-3 text-xs text-text-muted">
                <span id="grade-feedback-hint">The student sees this with the grade once it is released.</span>
                <span className="shrink-0 tabular-nums">
                  {feedback.length.toLocaleString()} / {FEEDBACK_MAX_LENGTH.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4 border-t border-border-subtle bg-bg-alt/40 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-start gap-3">
            <Switch id="grade-release" checked={release} onChange={setRelease} disabled={isSaving} aria-describedby="grade-release-hint" />
            <div className="min-w-0">
              {/* leading-6 matches the switch's 24px height, so the label sits on its center line. */}
              <label htmlFor="grade-release" className="block cursor-pointer text-sm font-medium leading-6 text-text-main">
                Release grade to the student
              </label>
              <p id="grade-release-hint" className="text-xs text-text-muted">
                {release ? "The student sees the score and feedback once you save." : "Hidden from the student until you release it."}
              </p>
            </div>
          </div>
          <button type="submit" disabled={isSaving} className="btn-primary w-full px-5 sm:w-auto sm:min-w-[8.5rem]">
            {isSaving ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden="true" /> : <Icon name="save" className="h-4 w-4" />}
            {isSaving ? "Saving…" : "Save grade"}
          </button>
        </div>
      </form>

      <section className="card overflow-hidden" aria-labelledby="code-heading">
        <div className="border-b border-border-subtle px-5 py-3">
          <h3 id="code-heading" className="text-sm font-semibold">
            Submitted code
          </h3>
          <p className="text-xs text-text-muted">Left: starter code · Right: submitted code</p>
        </div>
        {sourceCode ? (
          <>
            <div className="h-[420px]">
              <DiffEditor
                height="100%"
                language="python"
                theme={editorThemeFor(effectiveTheme)}
                beforeMount={defineEditorThemes}
                original={task?.starter_code || ""}
                modified={sourceCode}
                loading={<LoadingState label="Loading code…" />}
                options={{ readOnly: true, minimap: { enabled: false }, scrollBeyondLastLine: false, renderSideBySide: true, wordWrap: "on" }}
                keepCurrentOriginalModel
                keepCurrentModifiedModel
                onMount={(editor) => {
                  diffModelsRef.current = editor.getModel();
                }}
              />
            </div>
            {execution && (
              <div className="border-t border-border-subtle p-4">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                  Submission run · {humanize(execution.status)}
                </p>
                <pre className="max-h-40 overflow-auto whitespace-pre-wrap font-mono text-xs text-text-main">
                  {[execution.stdout, execution.stderr].filter(Boolean).join("\n") || "(no output recorded)"}
                </pre>
              </div>
            )}
          </>
        ) : (
          <p className="p-5 text-sm text-text-muted">
            The source code for this attempt isn&apos;t available from the review service.
          </p>
        )}
      </section>

      <ConfirmationModal
        isOpen={isRetakeConfirmOpen}
        title="Allow another attempt?"
        message="This student may submit this activity one more time, even if the deadline has passed. The new attempt becomes the official one, and you grade it separately. The student is notified."
        confirmText="Allow attempt"
        isLoading={isGrantingRetake}
        onConfirm={handleGrantRetake}
        onCancel={() => setIsRetakeConfirmOpen(false)}
      />
    </div>
  );
}

export default function SplitPaneGradingWorkspace() {
  const { classId, taskId } = useParams();
  const [students, setStudents] = useState([]);
  const [submissions, setSubmissions] = useState({});
  const [task, setTask] = useState(null);
  const [classroom, setClassroom] = useState(null);
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportError, setExportError] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [studentQuery, setStudentQuery] = useState("");
  const [studentFilter, setStudentFilter] = useState("all");

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [members, items, taskRes, classRes] = await Promise.all([
        api.get(`/classrooms/${classId}/members`),
        loadAllQueueItems(taskId),
        api.get(`/instructors/tasks/${taskId}`),
        api.get(`/classrooms/${classId}`),
      ]);
      setStudents((Array.isArray(members) ? members : []).filter((m) => m.status !== "removed"));
      setSubmissions(pickSubmissions(items.filter((i) => String(i.activity?.task_id) === String(taskId))));
      setTask(taskRes);
      setClassroom(classRes);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [classId, taskId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const selectedStudent = students.find((s) => s.student_id === selectedStudentId) || null;
  const selectedSubmission = selectedStudent ? submissions[selectedStudent.student_id] : null;
  const submittedCount = useMemo(() => students.filter((s) => submissions[s.student_id]).length, [students, submissions]);

  const reviewStateOf = useCallback(
    (student) => {
      const sub = submissions[student.student_id];
      return !sub ? "none" : sub.has_manual_grade ? "graded" : "review";
    },
    [submissions],
  );
  const filterCounts = useMemo(() => {
    const counts = { all: students.length, review: 0, graded: 0, none: 0 };
    students.forEach((student) => {
      counts[reviewStateOf(student)] += 1;
    });
    return counts;
  }, [students, reviewStateOf]);
  const visibleStudents = useMemo(() => {
    const query = studentQuery.trim().toLowerCase();
    return students.filter(
      (student) =>
        (studentFilter === "all" || reviewStateOf(student) === studentFilter) &&
        (!query || [student.name, student.school_id, student.email].some((value) => value && value.toLowerCase().includes(query))),
    );
  }, [students, studentFilter, studentQuery, reviewStateOf]);

  const handleExport = async () => {
    setIsExporting(true);
    setExportError("");
    try {
      const token = localStorage.getItem("pamsu_access_token");
      const response = await fetch(`${API_BASE_URL}/reports/classrooms/${classId}/gradebook.csv?task_id=${taskId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error(`Export failed (${response.status})`);
      let filename = `class_${classId}_activity_${taskId}_grades.csv`;
      const disposition = response.headers.get("Content-Disposition");
      if (disposition && disposition.includes('filename="')) filename = disposition.split('filename="')[1].split('"')[0];
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      setExportError("The gradebook could not be exported. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <PageShell role="instructor" maxWidth="max-w-7xl" statusContext={classroom?.name}>
      <Link
        to={`/instructor/bench/${classId}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted transition-colors hover:text-text-main"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {classroom ? `Back to ${classroom.name}` : "Back to activities"}
      </Link>

      {error ? (
        <ErrorState error={error} resource="the grading workspace" onRetry={fetchData} />
      ) : isLoading ? (
        <LoadingState label="Loading submissions…" />
      ) : (
        <>
          <PageHeader
            eyebrow={classLabel(classroom)}
            title={task?.title || "Activity"}
            description={`${submittedCount} of ${students.length} students have submitted.`}
            actions={
              <button
                type="button"
                onClick={handleExport}
                disabled={isExporting}
                aria-busy={isExporting}
                className="btn-secondary group"
              >
                {isExporting ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="text-text-muted transition-colors duration-150 group-hover:text-text-main"
                    aria-hidden="true"
                  >
                    <g className="transition-transform duration-200 ease-out group-hover:translate-y-0.5">
                      <path d="M8 2.5v7" />
                      <path d="M5 6.75l3 3 3-3" />
                    </g>
                    <path d="M2.75 10.25v1.5c0 .83.67 1.5 1.5 1.5h7.5c.83 0 1.5-.67 1.5-1.5v-1.5" />
                  </svg>
                )}
                {isExporting ? "Exporting…" : "Export grades (CSV)"}
              </button>
            }
          />
          {exportError && (
            <InlineAlert tone="error" onDismiss={() => setExportError("")} className="mb-4">
              {exportError}
            </InlineAlert>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
            <section className={`card h-fit overflow-hidden ${selectedStudent ? "hidden lg:block" : ""}`} aria-label="Students">
              <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3">
                <h2 className="text-sm font-semibold">Students</h2>
                <span className="badge badge-neutral">{students.length}</span>
              </div>
              {students.length > 0 && (
                <div className="space-y-2.5 border-b border-border-subtle px-3 py-3">
                  <div className="relative">
                    <label htmlFor="bench-student-search" className="sr-only">
                      Search students
                    </label>
                    <Icon name="search" className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                    <input
                      id="bench-student-search"
                      type="search"
                      value={studentQuery}
                      onChange={(e) => setStudentQuery(e.target.value)}
                      placeholder="Search name or ID…"
                      className="input-field py-1.5 pl-8"
                    />
                  </div>
                  <div className="flex flex-wrap gap-1.5" role="group" aria-label="Show students">
                    {STUDENT_FILTERS.map(([value, label]) => {
                      const active = studentFilter === value;
                      return (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setStudentFilter(value)}
                          aria-pressed={active}
                          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition-colors ${
                            active
                              ? "border-psu-maroon bg-psu-maroon text-white shadow-sm"
                              : "border-border-subtle bg-bg-panel text-text-muted hover:border-border-strong hover:text-text-main"
                          }`}
                        >
                          {label}{" "}
                          <span className={`tabular-nums ${active ? "text-white/80" : "text-text-muted"}`}>{filterCounts[value]}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
              {students.length === 0 ? (
                <p className="p-4 text-sm text-text-muted">No students are enrolled in this class.</p>
              ) : visibleStudents.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-text-muted">No students match.</p>
              ) : (
                <ul className="max-h-[70vh] divide-y divide-border-subtle overflow-y-auto">
                  {visibleStudents.map((student) => {
                    const sub = submissions[student.student_id];
                    const badge = !sub
                      ? { label: "No submission", cls: "badge-neutral" }
                      : sub.has_manual_grade
                        ? { label: sub.grade_is_released ? "Released" : "Graded", cls: "badge-success" }
                        : { label: "To review", cls: "badge-brand" };
                    const isSelected = selectedStudentId === student.student_id;
                    return (
                      <li key={student.student_id}>
                        <button
                          type="button"
                          onClick={() => setSelectedStudentId(student.student_id)}
                          aria-current={isSelected ? "true" : undefined}
                          className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors focus-visible:-outline-offset-2 ${
                            isSelected ? "bg-selected" : "hover:bg-bg-alt"
                          }`}
                        >
                          <span className="flex min-w-0 items-center gap-2.5">
                            <Avatar name={student.name} size="sm" />
                            <span className="min-w-0">
                              <span className="block truncate text-sm font-medium text-text-main">{student.name}</span>
                              <span className="block truncate text-xs text-text-muted">{student.school_id || student.email}</span>
                            </span>
                          </span>
                          <span className={`badge shrink-0 ${badge.cls}`}>{badge.label}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

            <section className={`min-w-0 ${selectedStudent ? "" : "hidden lg:block"}`} aria-label="Submission review">
              {!selectedStudent ? (
                <EmptyState title="Select a student" message="Choose a student on the left to review their submission and record a grade." />
              ) : (
                <>
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-bold tracking-tight">{selectedStudent.name}</h2>
                      <p className="text-xs text-text-muted">{[selectedStudent.school_id, selectedStudent.email].filter(Boolean).join(" · ")}</p>
                    </div>
                    <button type="button" onClick={() => setSelectedStudentId(null)} className="btn-ghost btn-sm lg:hidden">
                      <Icon name="arrowLeft" className="h-3.5 w-3.5" />
                      All students
                    </button>
                  </div>
                  {selectedSubmission ? (
                    <SubmissionReview
                      key={selectedSubmission.sub_id}
                      submission={selectedSubmission}
                      task={task}
                      onGraded={(released) =>
                        setSubmissions((prev) => ({
                          ...prev,
                          [selectedStudent.student_id]: {
                            ...prev[selectedStudent.student_id],
                            has_manual_grade: true,
                            grade_is_released: released,
                          },
                        }))
                      }
                    />
                  ) : (
                    <EmptyState title="No submission yet" message="This student hasn't submitted this activity." />
                  )}
                </>
              )}
            </section>
          </div>
        </>
      )}
    </PageShell>
  );
}

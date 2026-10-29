import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DiffEditor } from "@monaco-editor/react";

import PageShell from "../../../components/layout/PageShell";
import ConfirmationModal from "../../../components/modals/ConfirmationModal";
import { EmptyState, ErrorState, FieldError, InlineAlert, LoadingState, PageHeader } from "../../../components/ui/StateViews";
import Switch from "../../../components/ui/Switch";
import api, { API_BASE_URL, getErrorMessage } from "../../../services/api";
import { ruleLabel } from "../../../utils/astRules";
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

      <section className="card p-5" aria-labelledby="indicators-heading">
        <h3 id="indicators-heading" className="text-sm font-semibold">
          Review indicators
        </h3>
        <p className="mb-4 text-xs text-text-muted">
          Signals to inform your review. They are not evidence of misconduct and do not set the grade.
        </p>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Similarity", typeof evaluation?.jaccard_score === "number" ? `${evaluation.jaccard_score.toFixed(1)}%` : "Not computed"],
            ["Tab switches", session ? session.tab_switch_count : "—"],
            ["Blocked pastes", session ? session.blocked_paste_count : "—"],
            ["Pointer exits", session ? session.mouseleave_count : "—"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-border-subtle p-3">
              <dt className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">{label}</dt>
              <dd className="mt-1 text-lg font-semibold text-text-main">{value}</dd>
            </div>
          ))}
        </dl>
        {!session && <p className="mt-3 text-xs text-text-muted">No coding-session record is linked to this submission.</p>}

        <h4 className="mb-2 mt-5 text-xs font-semibold uppercase tracking-wider text-text-muted">Structure check (AST)</h4>
        {!analysis ? (
          <p className="text-sm text-text-muted">No structure analysis has been recorded for this submission.</p>
        ) : analysis.syntax_error ? (
          <p className="text-sm text-text-rose">Syntax error: {analysis.syntax_error.message || "the code could not be parsed."}</p>
        ) : findings.length === 0 ? (
          <p className="text-sm text-text-muted">The activity has no required structures to check.</p>
        ) : (
          <ul className="space-y-1.5">
            {findings.map((finding) => (
              <li key={finding.finding_id || finding.rule_key} className="flex items-center justify-between gap-3 rounded-lg border border-border-subtle px-3 py-2 text-sm">
                <span className="text-text-main">
                  {ruleLabel(finding.rule_key) || finding.label}
                  {typeof finding.detected_count === "number" && (
                    <span className="ml-2 text-xs text-text-muted">
                      {finding.detected_count} found, {finding.required_count} needed
                    </span>
                  )}
                </span>
                <span className={`badge ${finding.passed ? "badge-success" : finding.passed === false ? "badge-gold" : "badge-neutral"}`}>
                  {finding.passed ? "Found" : finding.passed === false ? "Missing" : "Not evaluated"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <form onSubmit={handleSave} noValidate className="card space-y-4 p-5" aria-labelledby="grade-heading">
        <h3 id="grade-heading" className="text-sm font-semibold">
          Grade
        </h3>
        {saveMessage && (
          <InlineAlert tone={saveMessage.tone} onDismiss={() => setSaveMessage(null)}>
            {saveMessage.text}
          </InlineAlert>
        )}
        {suggestion && !evaluation?.instructor_grade && (
          <p className="rounded-lg border border-psu-gold/40 bg-psu-gold/[0.06] px-3 py-2 text-xs text-text-main">
            <span className="font-semibold">Suggested score: {suggestion.score}.</span>{" "}
            The structure check found {suggestion.found} of {suggestion.total} required structure{suggestion.total === 1 ? "" : "s"}.
            Review the indicators above, deduct for any problems you find, then save.
          </p>
        )}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-[180px_minmax(0,1fr)]">
          <div>
            <label htmlFor="grade-score" className="field-label">
              Score (out of {details?.evaluation?.instructor_grade?.max_score || MAX_SCORE})
            </label>
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
              className="input-field"
              disabled={isSaving}
            />
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
              maxLength={5000}
              className="input-field h-24 resize-y"
              disabled={isSaving}
            />
          </div>
        </div>
        <div className="flex flex-col gap-4 border-t border-border-subtle pt-4 sm:flex-row sm:items-center sm:justify-between">
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
          <button type="submit" disabled={isSaving} className="btn-primary w-full sm:w-auto">
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
              <button type="button" onClick={handleExport} disabled={isExporting} className="btn-secondary">
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
              {students.length === 0 ? (
                <p className="p-4 text-sm text-text-muted">No students are enrolled in this class.</p>
              ) : (
                <ul className="max-h-[70vh] divide-y divide-border-subtle overflow-y-auto">
                  {students.map((student) => {
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
                          className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors ${
                            isSelected ? "bg-selected" : "hover:bg-bg-alt"
                          }`}
                        >
                          <span className="min-w-0">
                            <span className="block truncate text-sm font-medium text-text-main">{student.name}</span>
                            <span className="block truncate text-xs text-text-muted">{student.school_id || student.email}</span>
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

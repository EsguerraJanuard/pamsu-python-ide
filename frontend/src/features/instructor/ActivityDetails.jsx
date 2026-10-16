import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { EmptyState, ErrorState, FieldError, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { classLabel, formatDateTime } from "../../utils/format";

const EMPTY_CASE = { name: "", standard_input: "", expected_output: "", is_hidden: false };

export default function ActivityDetails() {
  const { id } = useParams();
  const [activity, setActivity] = useState(null);
  const [classroom, setClassroom] = useState(null);
  const [testCases, setTestCases] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const [confirm, setConfirm] = useState(null); // { type: "publish" | "unpublish" | "delete-case", testCase? }
  const [isWorking, setIsWorking] = useState(false);
  const [isSavingPolicy, setIsSavingPolicy] = useState(false);

  const [newCase, setNewCase] = useState(EMPTY_CASE);
  const [caseErrors, setCaseErrors] = useState({});
  const [isAddingCase, setIsAddingCase] = useState(false);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [task, cases] = await Promise.all([
        api.get(`/instructors/tasks/${id}`),
        api.get(`/instructors/tasks/${id}/test-cases`),
      ]);
      setActivity(task);
      setTestCases(Array.isArray(cases) ? cases : []);
      try {
        setClassroom(await api.get(`/classrooms/${task.class_id}`));
      } catch {
        setClassroom(null);
      }
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const reloadCases = async () => {
    const cases = await api.get(`/instructors/tasks/${id}/test-cases`);
    setTestCases(Array.isArray(cases) ? cases : []);
  };

  const handleConfirm = async () => {
    if (!confirm || isWorking) return;
    setIsWorking(true);
    try {
      if (confirm.type === "delete-case") {
        await api.delete(`/instructors/test-cases/${confirm.testCase.test_case_id}`);
        await reloadCases();
        setMessage({ tone: "success", text: `Test case "${confirm.testCase.name}" was deleted.` });
      } else {
        const publish = confirm.type === "publish";
        const updated = await api.patch(`/instructors/tasks/${id}/publication`, { is_published: publish });
        setActivity((prev) => ({ ...prev, ...(updated || { is_published: publish }) }));
        setMessage({ tone: "success", text: publish ? "Activity published to students." : "Activity moved back to draft." });
      }
    } catch (err) {
      setMessage({ tone: "error", text: getErrorMessage(err, "The change could not be saved.") });
    } finally {
      setIsWorking(false);
      setConfirm(null);
    }
  };

  const handlePastePolicy = async (policy) => {
    if (policy === activity.paste_policy) return;
    setIsSavingPolicy(true);
    try {
      const updated = await api.patch(`/instructors/tasks/${id}`, { paste_policy: policy });
      setActivity((prev) => ({ ...prev, ...(updated || { paste_policy: policy }) }));
      setMessage({ tone: "success", text: "Paste policy updated." });
    } catch (err) {
      setMessage({ tone: "error", text: getErrorMessage(err, "The paste policy could not be updated.") });
    } finally {
      setIsSavingPolicy(false);
    }
  };

  const handleAddTestCase = async (event) => {
    event.preventDefault();
    const errors = {};
    if (!newCase.name.trim()) errors.name = "Give the test case a short name.";
    if (!newCase.expected_output.trim()) errors.expected_output = "Expected output is required.";
    setCaseErrors(errors);
    if (Object.keys(errors).length) return;

    setIsAddingCase(true);
    try {
      await api.post(`/instructors/tasks/${id}/test-cases`, {
        name: newCase.name.trim(),
        standard_input: newCase.standard_input,
        expected_output: newCase.expected_output,
        is_hidden: newCase.is_hidden,
        display_order: testCases.length,
      });
      setNewCase(EMPTY_CASE);
      await reloadCases();
      setMessage({ tone: "success", text: "Test case added." });
    } catch (err) {
      setMessage({ tone: "error", text: getErrorMessage(err, "The test case could not be added.") });
    } finally {
      setIsAddingCase(false);
    }
  };

  const backLink = (
    <Link
      to={activity?.class_id ? `/instructor/classes/${activity.class_id}` : "/instructor/classes"}
      className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted transition-colors hover:text-text-main"
    >
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {classroom ? `Back to ${classroom.name}` : "Back to classes"}
    </Link>
  );

  if (error) {
    return (
      <PageShell role="instructor">
        {backLink}
        <ErrorState error={error} resource="this activity" onRetry={fetchAll} />
      </PageShell>
    );
  }

  if (isLoading) {
    return (
      <PageShell role="instructor">
        <SkeletonList rows={3} className="h-32" />
      </PageShell>
    );
  }

  const rules = Object.keys(activity.required_ast_rules || {});
  const isPublished = activity.is_published;

  return (
    <PageShell role="instructor" statusContext={classroom?.name}>
      {backLink}
      <PageHeader
        eyebrow={[classroom ? classLabel(classroom) : null, activity.activity_type === "homework" ? "Homework" : "Laboratory"].filter(Boolean).join(" · ")}
        title={activity.title}
        description={activity.description || undefined}
        actions={
          <>
            {isPublished && (
              <Link to={`/instructor/bench/${activity.class_id}/${activity.task_id}`} className="btn-secondary">
                Open grading bench
              </Link>
            )}
            <button
              type="button"
              onClick={() => setConfirm({ type: isPublished ? "unpublish" : "publish" })}
              className={isPublished ? "btn-secondary" : "btn-primary"}
            >
              {isPublished ? "Unpublish" : "Publish"}
            </button>
          </>
        }
      />

      {message && (
        <InlineAlert tone={message.tone} onDismiss={() => setMessage(null)} className="mb-5">
          {message.text}
        </InlineAlert>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-5">
          <section className="card p-5" aria-labelledby="instructions-heading">
            <h2 id="instructions-heading" className="mb-2 text-sm font-semibold">
              Instructions
            </h2>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-main">
              {activity.instructions || <span className="text-text-muted">No instructions provided.</span>}
            </p>
            {activity.starter_code && (
              <>
                <h3 className="mb-2 mt-5 text-xs font-semibold uppercase tracking-wider text-text-muted">Starter code</h3>
                <pre className="overflow-x-auto rounded-lg border border-border-subtle bg-bg-alt p-3 font-mono text-xs text-text-main">
                  {activity.starter_code}
                </pre>
              </>
            )}
          </section>

          <section className="card p-5" aria-labelledby="test-cases-heading">
            <h2 id="test-cases-heading" className="mb-1 text-sm font-semibold">
              Test cases
            </h2>
            <p className="mb-4 text-xs text-text-muted">
              Visible cases are shown to students as samples. Hidden cases are used only for evaluation.
            </p>

            {testCases.length === 0 ? (
              <EmptyState className="py-8" title="No test cases yet" message="Add at least one case so runs can be compared with expected output." />
            ) : (
              <ul className="space-y-3">
                {testCases.map((tc) => (
                  <li key={tc.test_case_id} className="rounded-lg border border-border-subtle p-4">
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-text-main">{tc.name}</span>
                        <span className={`badge ${tc.is_hidden ? "badge-neutral" : "badge-brand"}`}>
                          {tc.is_hidden ? "Hidden" : "Sample"}
                        </span>
                      </div>
                      {!isPublished && (
                        <button
                          type="button"
                          onClick={() => setConfirm({ type: "delete-case", testCase: tc })}
                          className="btn-ghost btn-sm hover:text-psu-red"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <div>
                        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">Input</p>
                        <pre className="max-h-40 overflow-auto rounded-md bg-bg-alt p-2.5 font-mono text-xs text-text-main">{tc.standard_input || "(none)"}</pre>
                      </div>
                      <div>
                        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">Expected output</p>
                        <pre className="max-h-40 overflow-auto rounded-md bg-bg-alt p-2.5 font-mono text-xs text-text-main">{tc.expected_output}</pre>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {isPublished ? (
              <InlineAlert tone="info" className="mt-4">
                Unpublish the activity to add or delete test cases.
              </InlineAlert>
            ) : (
              <form onSubmit={handleAddTestCase} noValidate className="mt-5 space-y-4 border-t border-border-subtle pt-5">
                <h3 className="text-sm font-semibold">Add a test case</h3>
                <div>
                  <label htmlFor="tc-name" className="field-label">
                    Name
                  </label>
                  <input
                    id="tc-name"
                    type="text"
                    value={newCase.name}
                    onChange={(e) => {
                      setNewCase((p) => ({ ...p, name: e.target.value }));
                      setCaseErrors((p) => ({ ...p, name: "" }));
                    }}
                    placeholder="e.g. Small input"
                    maxLength={150}
                    aria-invalid={Boolean(caseErrors.name)}
                    aria-describedby={caseErrors.name ? "tc-name-error" : undefined}
                    className="input-field"
                    disabled={isAddingCase}
                  />
                  <FieldError id="tc-name-error">{caseErrors.name}</FieldError>
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="tc-input" className="field-label">
                      Standard input (optional)
                    </label>
                    <textarea
                      id="tc-input"
                      value={newCase.standard_input}
                      onChange={(e) => setNewCase((p) => ({ ...p, standard_input: e.target.value }))}
                      className="input-field h-28 resize-y font-mono text-xs"
                      disabled={isAddingCase}
                    />
                  </div>
                  <div>
                    <label htmlFor="tc-output" className="field-label">
                      Expected output
                    </label>
                    <textarea
                      id="tc-output"
                      value={newCase.expected_output}
                      onChange={(e) => {
                        setNewCase((p) => ({ ...p, expected_output: e.target.value }));
                        setCaseErrors((p) => ({ ...p, expected_output: "" }));
                      }}
                      aria-invalid={Boolean(caseErrors.expected_output)}
                      aria-describedby={caseErrors.expected_output ? "tc-output-error" : undefined}
                      className="input-field h-28 resize-y font-mono text-xs"
                      disabled={isAddingCase}
                    />
                    <FieldError id="tc-output-error">{caseErrors.expected_output}</FieldError>
                  </div>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-text-main">
                    <input
                      type="checkbox"
                      checked={newCase.is_hidden}
                      onChange={(e) => setNewCase((p) => ({ ...p, is_hidden: e.target.checked }))}
                      className="h-4 w-4 accent-psu-maroon"
                      disabled={isAddingCase}
                    />
                    Hidden from students
                  </label>
                  <button type="submit" disabled={isAddingCase} className="btn-primary">
                    {isAddingCase ? "Adding…" : "Add test case"}
                  </button>
                </div>
              </form>
            )}
          </section>
        </div>

        <aside className="space-y-5">
          <section className="card p-5" aria-label="Activity settings">
            <h2 className="mb-3 text-sm font-semibold">Settings</h2>
            <dl className="space-y-2.5 text-sm">
              {[
                ["Status", isPublished ? "Published" : activity.scheduled_publish_at ? "Scheduled" : "Draft"],
                ["Published", activity.published_at ? formatDateTime(activity.published_at) : "—"],
                ["Scheduled", activity.scheduled_publish_at ? formatDateTime(activity.scheduled_publish_at) : "—"],
                ["Due", activity.due_at ? formatDateTime(activity.due_at) : "No due date"],
                ["Difficulty", activity.difficulty ? activity.difficulty.charAt(0).toUpperCase() + activity.difficulty.slice(1) : "—"],
                ["Graded", activity.is_graded ? "Yes" : "No"],
              ].map(([term, value]) => (
                <div key={term} className="flex justify-between gap-3">
                  <dt className="text-text-muted">{term}</dt>
                  <dd className="text-right font-medium text-text-main">{value}</dd>
                </div>
              ))}
            </dl>

            <fieldset className="mt-5 border-t border-border-subtle pt-4" disabled={isSavingPolicy}>
              <legend className="mb-2 text-xs font-semibold text-text-muted">Paste policy</legend>
              {[
                ["internal_only", "Workspace clipboard only", "Students can copy/paste within the editor; outside pastes are blocked."],
                ["disabled", "No pasting", "All paste actions are blocked."],
              ].map(([value, label, help]) => (
                <label key={value} className="mb-2 flex cursor-pointer items-start gap-2.5 rounded-lg border border-border-subtle p-2.5 has-[:checked]:border-psu-maroon/40 has-[:checked]:bg-psu-cream">
                  <input
                    type="radio"
                    name="paste-policy"
                    value={value}
                    checked={activity.paste_policy === value}
                    onChange={() => handlePastePolicy(value)}
                    className="mt-0.5 accent-psu-maroon"
                  />
                  <span>
                    <span className="block text-sm font-medium text-text-main">{label}</span>
                    <span className="block text-xs text-text-muted">{help}</span>
                  </span>
                </label>
              ))}
            </fieldset>
          </section>

          <section className="card p-5" aria-label="Required structures">
            <h2 className="mb-3 text-sm font-semibold">Required structures</h2>
            {rules.length === 0 ? (
              <p className="text-xs text-text-muted">No AST requirements for this activity.</p>
            ) : (
              <ul className="flex flex-wrap gap-1.5">
                {rules.map((rule) => (
                  <li key={rule} className="badge badge-neutral">
                    {rule.replace(/^require_/, "").replace(/_/g, " ")}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>

      <ConfirmationModal
        isOpen={Boolean(confirm)}
        title={
          confirm?.type === "publish"
            ? "Publish this activity?"
            : confirm?.type === "unpublish"
              ? "Unpublish this activity?"
              : "Delete this test case?"
        }
        message={
          confirm?.type === "publish"
            ? "Students in the class will be able to see and submit this activity."
            : confirm?.type === "unpublish"
              ? "Students will no longer see this activity. Existing submissions are kept."
              : `"${confirm?.testCase?.name}" will be permanently removed.`
        }
        confirmText={confirm?.type === "publish" ? "Publish" : confirm?.type === "unpublish" ? "Unpublish" : "Delete"}
        isDanger={confirm?.type !== "publish"}
        isLoading={isWorking}
        onConfirm={handleConfirm}
        onCancel={() => setConfirm(null)}
      />
    </PageShell>
  );
}

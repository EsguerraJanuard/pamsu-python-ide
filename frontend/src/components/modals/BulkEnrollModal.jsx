import { useRef, useState } from "react";
import api, { getErrorMessage } from "../../services/api";
import Modal from "../ui/Modal";
import { FieldError, InlineAlert } from "../ui/StateViews";

const EMAIL_PATTERN = /[a-zA-Z0-9_.+-]+@pampangastateu\.edu\.ph/gi;

export default function BulkEnrollModal({ isOpen, onClose, classId, onSuccess }) {
  const [mode, setMode] = useState("upload");
  const [emailsText, setEmailsText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState("");
  const fileInputRef = useRef(null);

  const reset = () => {
    setEmailsText("");
    setResult(null);
    setError("");
    setFieldError("");
    setMode("upload");
  };

  const handleClose = () => {
    if (isSubmitting) return;
    reset();
    onClose();
  };

  const handlePasteSubmit = async (event) => {
    event.preventDefault();
    const emails = [...new Set((emailsText.match(EMAIL_PATTERN) || []).map((e) => e.toLowerCase()))];
    if (emails.length === 0) {
      setFieldError("No @pampangastateu.edu.ph email addresses were found in the text.");
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      setResult(await api.post(`/classrooms/${classId}/bulk-enroll`, { emails }));
      onSuccess?.();
    } catch (err) {
      setError(getErrorMessage(err, "Students could not be enrolled."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setIsSubmitting(true);
    setError("");
    try {
      setResult(await api.post(`/classrooms/${classId}/bulk-enroll/file`, formData));
      onSuccess?.();
    } catch (err) {
      setError(getErrorMessage(err, "The file could not be processed."));
    } finally {
      setIsSubmitting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const tabClass = (tab) =>
    `flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
      mode === tab ? "bg-psu-maroon text-white shadow-sm" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
    }`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Bulk enroll students"
      description="Only @pampangastateu.edu.ph addresses are accepted. Students who already have an account are enrolled now. Addresses without one are saved as pending and enrolled when MIS creates a student account with that exact email."
      dismissible={!isSubmitting}
    >
      {result ? (
        <div>
          <InlineAlert tone="success">Enrollment processed.</InlineAlert>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-center sm:grid-cols-3">
            {[
              ["Enrolled", result.enrolled ?? 0, "text-text-emerald"],
              ["Pending (no account)", result.queued ?? 0, "text-text-amber"],
              ["Invalid", result.invalid ?? 0, "text-text-rose"],
              ...(result.already_enrolled > 0 ? [["Already in class", result.already_enrolled, "text-text-main"]] : []),
              ...(result.ineligible > 0 ? [["Not a student account", result.ineligible, "text-text-amber"]] : []),
            ].map(([label, value, tone]) => (
              <div key={label} className="rounded-lg border border-border-subtle p-3">
                <dd className={`text-2xl font-bold ${tone}`}>{value}</dd>
                <dt className="text-xs text-text-muted">{label}</dt>
              </div>
            ))}
          </dl>
          {result.queued > 0 && (
            <InlineAlert tone="warning" className="mt-4">
              {result.queued === 1 ? "1 address has" : `${result.queued} addresses have`} no student account yet. They
              will be added to this class when MIS creates a student account with the same university email, as long as
              this class is still active. A misspelled address will not match, so check it with the student.
            </InlineAlert>
          )}
          {result.ineligible > 0 && (
            <InlineAlert tone="warning" className="mt-4">
              {result.ineligible === 1 ? "1 address belongs" : `${result.ineligible} addresses belong`} to a faculty or
              admin account and {result.ineligible === 1 ? "was" : "were"} not enrolled.
            </InlineAlert>
          )}
          <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <button type="button" className="btn-secondary" onClick={reset}>
              Enroll more
            </button>
            <button type="button" className="btn-primary" onClick={handleClose}>
              Done
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="mb-4 flex gap-1 rounded-lg border border-border-subtle bg-bg-panel p-1" role="tablist" aria-label="Enrollment method">
            <button type="button" role="tab" aria-selected={mode === "upload"} className={tabClass("upload")} onClick={() => setMode("upload")}>
              Upload file
            </button>
            <button type="button" role="tab" aria-selected={mode === "paste"} className={tabClass("paste")} onClick={() => setMode("paste")}>
              Paste emails
            </button>
          </div>

          {error && (
            <InlineAlert tone="error" className="mb-4">
              {error}
            </InlineAlert>
          )}

          {mode === "upload" ? (
            <div>
              <label
                htmlFor="bulk-enroll-file"
                className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border-strong px-6 py-10 text-center transition-colors hover:border-psu-maroon/40 hover:bg-selected"
              >
                <span className="text-sm font-semibold text-text-main">
                  {isSubmitting ? "Uploading…" : "Choose a CSV or Excel file"}
                </span>
                <span className="mt-1 text-xs text-text-muted">.csv, .xlsx, .xls or .txt with one email per row</span>
              </label>
              <input
                ref={fileInputRef}
                id="bulk-enroll-file"
                type="file"
                accept=".csv,.xlsx,.xls,.txt"
                onChange={handleFileUpload}
                disabled={isSubmitting}
                className="sr-only"
              />
            </div>
          ) : (
            <form onSubmit={handlePasteSubmit} noValidate>
              <label htmlFor="bulk-enroll-emails" className="field-label">
                Student emails
              </label>
              <textarea
                id="bulk-enroll-emails"
                value={emailsText}
                onChange={(e) => {
                  setEmailsText(e.target.value);
                  setFieldError("");
                }}
                placeholder={"juan.delacruz@pampangastateu.edu.ph\nmaria.santos@pampangastateu.edu.ph"}
                aria-invalid={Boolean(fieldError)}
                aria-describedby={fieldError ? "bulk-enroll-emails-error" : undefined}
                className="input-field h-40 resize-none font-mono text-xs"
                disabled={isSubmitting}
              />
              <FieldError id="bulk-enroll-emails-error">{fieldError}</FieldError>
              <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <button type="button" className="btn-secondary" onClick={handleClose} disabled={isSubmitting}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmitting || !emailsText.trim()}>
                  {isSubmitting ? "Enrolling…" : "Enroll students"}
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </Modal>
  );
}

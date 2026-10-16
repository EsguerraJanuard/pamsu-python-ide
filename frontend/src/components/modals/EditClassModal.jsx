import { useEffect, useState } from "react";
import api, { getErrorMessage } from "../../services/api";
import Modal from "../ui/Modal";
import { FieldError, InlineAlert } from "../ui/StateViews";

const FIELDS = [
  { name: "name", label: "Class name", required: true },
  { name: "subject_code", label: "Subject code", required: false },
  { name: "section", label: "Section", required: false },
];

export default function EditClassModal({ isOpen, onClose, classroom, onSuccess }) {
  const [form, setForm] = useState({ name: "", subject_code: "", section: "" });
  const [classCode, setClassCode] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [message, setMessage] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [confirmRegenerate, setConfirmRegenerate] = useState(false);

  useEffect(() => {
    if (!isOpen || !classroom) return;
    setForm({
      name: classroom.name || "",
      subject_code: classroom.subject_code || "",
      section: classroom.section || "",
    });
    setClassCode(classroom.class_code || "");
    setFieldErrors({});
    setMessage(null);
    setConfirmRegenerate(false);
  }, [classroom, isOpen]);

  if (!classroom) return null;
  const busy = isSaving || isRegenerating;

  const handleSave = async (event) => {
    event.preventDefault();
    const errors = {};
    FIELDS.forEach((f) => {
      if (f.required && !form[f.name].trim()) errors[f.name] = `${f.label} is required.`;
    });
    setFieldErrors(errors);
    if (Object.keys(errors).length) return;

    setIsSaving(true);
    setMessage(null);
    try {
      const payload = { name: form.name.trim() };
      if (form.subject_code.trim()) payload.subject_code = form.subject_code.trim();
      if (form.section.trim()) payload.section = form.section.trim();
      const updated = await api.patch(`/classrooms/${classroom.class_id}`, payload);
      onSuccess?.(updated);
      setMessage({ tone: "success", text: "Class details saved." });
    } catch (err) {
      setMessage({ tone: "error", text: getErrorMessage(err, "The class could not be updated.") });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    setMessage(null);
    try {
      const updated = await api.post(`/classrooms/${classroom.class_id}/regenerate-code`);
      if (updated?.class_code) {
        setClassCode(updated.class_code);
        onSuccess?.(updated);
      }
      setMessage({ tone: "success", text: "A new enrollment code was generated. The previous code no longer works." });
    } catch (err) {
      setMessage({ tone: "error", text: getErrorMessage(err, "A new code could not be generated.") });
    } finally {
      setIsRegenerating(false);
      setConfirmRegenerate(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Class settings" dismissible={!busy}>
      {message && (
        <InlineAlert tone={message.tone} onDismiss={() => setMessage(null)} className="mb-4">
          {message.text}
        </InlineAlert>
      )}

      <form onSubmit={handleSave} noValidate className="space-y-4">
        {FIELDS.map((field) => (
          <div key={field.name}>
            <label htmlFor={`edit-class-${field.name}`} className="field-label">
              {field.label}
            </label>
            <input
              id={`edit-class-${field.name}`}
              type="text"
              value={form[field.name]}
              onChange={(e) => {
                setForm((prev) => ({ ...prev, [field.name]: e.target.value }));
                setFieldErrors((prev) => ({ ...prev, [field.name]: "" }));
              }}
              aria-invalid={Boolean(fieldErrors[field.name])}
              aria-describedby={fieldErrors[field.name] ? `edit-class-${field.name}-error` : undefined}
              disabled={busy}
              className="input-field"
            />
            <FieldError id={`edit-class-${field.name}-error`}>{fieldErrors[field.name]}</FieldError>
          </div>
        ))}
        <div className="flex justify-end">
          <button type="submit" disabled={busy} className="btn-primary">
            {isSaving ? "Saving…" : "Save details"}
          </button>
        </div>
      </form>

      <div className="mt-6 rounded-xl border border-border-subtle bg-bg-alt p-4">
        <p className="text-sm font-semibold text-text-main">Enrollment code</p>
        <p className="mt-0.5 text-xs text-text-muted">Students use this code to join. Generating a new one disables the old code.</p>
        <p className="mt-3 font-mono text-2xl font-bold tracking-[0.25em] text-psu-maroon">{classCode || "—"}</p>
        {confirmRegenerate ? (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-text-main">Replace the current code?</span>
            <button type="button" onClick={handleRegenerate} disabled={busy} className="btn-danger btn-sm">
              {isRegenerating ? "Generating…" : "Yes, generate new code"}
            </button>
            <button type="button" onClick={() => setConfirmRegenerate(false)} disabled={busy} className="btn-ghost btn-sm">
              Cancel
            </button>
          </div>
        ) : (
          <button type="button" onClick={() => setConfirmRegenerate(true)} disabled={busy} className="btn-secondary btn-sm mt-3">
            Generate new code
          </button>
        )}
      </div>
    </Modal>
  );
}

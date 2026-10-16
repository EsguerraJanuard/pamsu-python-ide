import { useState } from "react";
import api, { getErrorMessage } from "../../services/api";
import Modal from "../ui/Modal";
import { FieldError, InlineAlert } from "../ui/StateViews";

const EMPTY_FORM = { name: "", subject_code: "", section: "" };

const FIELDS = [
  { name: "name", label: "Class name", placeholder: "e.g. Computer Programming 1" },
  { name: "subject_code", label: "Subject code", placeholder: "e.g. CCS101" },
  { name: "section", label: "Section", placeholder: "e.g. BSCS 1A" },
];

export default function CreateClassModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [created, setCreated] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleClose = () => {
    if (isLoading) return;
    setFormData(EMPTY_FORM);
    setFieldErrors({});
    setError("");
    setCreated(null);
    setCopied(false);
    onClose();
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const errors = {};
    FIELDS.forEach((field) => {
      if (!formData[field.name].trim()) errors[field.name] = `${field.label} is required.`;
    });
    setFieldErrors(errors);
    if (Object.keys(errors).length) return;

    setIsLoading(true);
    setError("");
    try {
      const data = await api.post("/classrooms/", {
        name: formData.name.trim(),
        subject_code: formData.subject_code.trim(),
        section: formData.section.trim(),
      });
      setCreated(data);
      onSuccess?.(data);
    } catch (err) {
      setError(getErrorMessage(err, "The class could not be created."));
    } finally {
      setIsLoading(false);
    }
  };

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(created.class_code);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={created ? "Class created" : "Create a class"}
      description={created ? undefined : "Students join using the enrollment code generated for the class."}
      dismissible={!isLoading}
    >
      {created ? (
        <div className="text-center">
          <p className="text-sm text-text-muted">Share this enrollment code with the students of {created.name}.</p>
          <p className="mt-4 rounded-xl border border-psu-gold/50 bg-psu-gold/10 px-4 py-4 font-mono text-3xl font-bold tracking-[0.3em] text-psu-maroon">
            {created.class_code}
          </p>
          <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-center">
            <button type="button" className="btn-secondary" onClick={copyCode}>
              {copied ? "Copied" : "Copy code"}
            </button>
            <button type="button" className="btn-primary" onClick={handleClose}>
              Done
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {error && <InlineAlert tone="error">{error}</InlineAlert>}
          {FIELDS.map((field) => (
            <div key={field.name}>
              <label htmlFor={`create-class-${field.name}`} className="field-label">
                {field.label}
              </label>
              <input
                id={`create-class-${field.name}`}
                type="text"
                value={formData[field.name]}
                onChange={(e) => {
                  setFormData((prev) => ({ ...prev, [field.name]: e.target.value }));
                  setFieldErrors((prev) => ({ ...prev, [field.name]: "" }));
                }}
                placeholder={field.placeholder}
                aria-invalid={Boolean(fieldErrors[field.name])}
                aria-describedby={fieldErrors[field.name] ? `create-class-${field.name}-error` : undefined}
                disabled={isLoading}
                className="input-field"
              />
              <FieldError id={`create-class-${field.name}-error`}>{fieldErrors[field.name]}</FieldError>
            </div>
          ))}
          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
            <button type="button" onClick={handleClose} disabled={isLoading} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              {isLoading ? "Creating…" : "Create class"}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}

import { useState } from "react";
import api, { getErrorMessage } from "../../services/api";
import Modal from "../ui/Modal";
import { FieldError } from "../ui/StateViews";
import { classCodeError } from "../../utils/validation";

export default function JoinClassModal({ isOpen, onClose, onSuccess }) {
  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleClose = () => {
    if (isLoading) return;
    setCode("");
    setError("");
    onClose();
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    // Spaces around a pasted code are dropped; anything else must already
    // be letters and digits only (the server refuses the rest too).
    const trimmed = code.trim().toUpperCase();
    const problem = classCodeError(trimmed);

    if (problem) {
      setError(problem);
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      await api.post("/classrooms/join", { class_code: trimmed });
      setCode("");
      onSuccess?.();
      onClose();
    } catch (err) {
      if (err?.status === 404) {
        setError("No class matches that code. Check the code and try again.");
      } else if (err?.status === 409) {
        setError(getErrorMessage(err, "You are already enrolled in this class, or it is no longer active."));
      } else {
        setError(getErrorMessage(err, "We couldn't join the class. Please try again."));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Join a class"
      description="Ask your instructor for the class code and enter it below."
      size="sm"
      dismissible={!isLoading}
    >
      <form id="join-class-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="class-code" className="field-label">
          Class code
        </label>
        <input
          id="class-code"
          type="text"
          value={code}
          onChange={(e) => {
            setCode(e.target.value.toUpperCase());
            if (error) setError("");
          }}
          placeholder="e.g. QATEST1"
          maxLength={40}
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck="false"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "class-code-error" : "class-code-hint"}
          className="input-field font-mono tracking-widest"
          disabled={isLoading}
        />
        {error ? (
          <FieldError id="class-code-error">{error}</FieldError>
        ) : (
          <p id="class-code-hint" className="mt-1.5 text-xs text-text-muted">
            Letters and numbers only, no spaces.
          </p>
        )}

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" onClick={handleClose} disabled={isLoading} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isLoading || !code.trim()} className="btn-primary">
            {isLoading ? "Joining…" : "Join class"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

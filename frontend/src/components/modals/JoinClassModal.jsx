import { useState } from "react";
import api, { getErrorMessage } from "../../services/api";
import Modal from "../ui/Modal";
import { FieldError } from "../ui/StateViews";

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
    const trimmed = code.trim();

    if (trimmed.length < 6) {
      setError("Enter the class code from your instructor (at least 6 characters).");
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
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck="false"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "class-code-error" : undefined}
          className="input-field font-mono tracking-widest"
          disabled={isLoading}
        />
        <FieldError id="class-code-error">{error}</FieldError>

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

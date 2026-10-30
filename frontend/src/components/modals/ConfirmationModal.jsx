import { useRef } from "react";
import Modal from "../ui/Modal";

/**
 * Decision dialog for destructive or important actions.
 * While `isLoading` is true both buttons are disabled and the dialog cannot be
 * dismissed, which prevents double submission.
 */
export default function ConfirmationModal({
  isOpen,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  isDanger = false,
  isLoading = false,
  loadingText,
  children,
}) {
  const cancelRef = useRef(null);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
      size="sm"
      dismissible={!isLoading}
      showCloseButton={false}
      // Destructive dialogs focus Cancel first so Enter never confirms by accident.
      initialFocusRef={isDanger ? cancelRef : undefined}
      footer={
        <>
          <button
            ref={cancelRef}
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="btn-secondary"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={isDanger ? "btn-danger" : "btn-primary"}
          >
            {isLoading && (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden="true" />
            )}
            {isLoading ? loadingText || "Working…" : confirmText}
          </button>
        </>
      }
    >
      {message && <p className="text-sm leading-relaxed text-text-muted">{message}</p>}
      {children}
    </Modal>
  );
}

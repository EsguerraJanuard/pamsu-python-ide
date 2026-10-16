import Modal from "../ui/Modal";

/**
 * Blocking acknowledgement dialog. Reserve for outcomes the user must notice;
 * prefer InlineAlert for routine success/error feedback.
 */
export default function AlertModal({ isOpen, title = "Notice", message, onClose, isError = false }) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      showCloseButton={false}
      footer={
        <button type="button" onClick={onClose} className="btn-primary">
          OK
        </button>
      }
    >
      <div className="flex items-start gap-3">
        {isError && (
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-psu-red/10 text-psu-red">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </span>
        )}
        <p className="text-sm leading-relaxed text-text-muted">{message}</p>
      </div>
    </Modal>
  );
}

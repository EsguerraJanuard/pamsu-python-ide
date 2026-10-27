import { useRef } from "react";

import { useAuth } from "../../features/auth/AuthContext";
import { isGuestUser } from "../../features/auth/guest";
import ConfirmationModal from "../modals/ConfirmationModal";
import Modal from "../ui/Modal";

/** Shown to guests instead of the usual confirmation: an invitation to enroll. */
function GuestSignOutModal({ isOpen, onClose, onConfirm }) {
  const closeRef = useRef(null);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Thanks for trying the PSU Python IDE"
      size="sm"
      showCloseButton={false}
      initialFocusRef={closeRef}
      footer={
        <>
          <button ref={closeRef} type="button" onClick={onClose} className="btn-secondary">
            Close
          </button>
          <button type="button" onClick={onConfirm} className="btn-primary">
            Sign Out
          </button>
        </>
      }
    >
      <div className="space-y-3 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-psu-gold/15 text-text-brand" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 14l9-5-9-5-9 5 9 5zm0 0v6m-6-9.5v5.5l6 3 6-3v-5.5" />
          </svg>
        </div>
        <p className="text-base font-semibold text-text-main">Want to experience more of the system?</p>
        <p className="text-sm leading-relaxed text-text-muted">
          Enroll at <span className="font-semibold text-text-brand">Pampanga State University</span> today! Enrolled students join real
          classes, submit graded activities and keep their progress.
        </p>
        <p className="text-xs text-text-muted">Guest work is not kept: this guest account and its code are deleted within 24 hours.</p>
      </div>
    </Modal>
  );
}

export default function SignOutModal({ isOpen, onClose, onConfirm }) {
  const { user } = useAuth();

  if (isGuestUser(user)) {
    return <GuestSignOutModal isOpen={isOpen} onClose={onClose} onConfirm={onConfirm} />;
  }

  return (
    <ConfirmationModal
      isOpen={isOpen}
      title="Sign out?"
      message="You will need to sign in again to access your workspace. Unsubmitted code drafts are removed from this browser, so the next person cannot see them. Submit your work first."
      confirmText="Sign out"
      onConfirm={onConfirm}
      onCancel={onClose}
      isDanger
    />
  );
}

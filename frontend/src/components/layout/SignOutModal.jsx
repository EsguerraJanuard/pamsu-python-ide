import { useRef } from "react";

import { useAuth } from "../../features/auth/AuthContext";
import { isGuestUser } from "../../features/auth/guest";
import ConfirmationModal from "../modals/ConfirmationModal";
import Modal from "../ui/Modal";

// Pampanga State University's online admission page.
const ADMISSION_URL = "https://sms.pampangastateu.edu.ph/padmission";

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
          <button ref={closeRef} type="button" onClick={onClose} className="btn-ghost">
            Close
          </button>
          <button type="button" onClick={onConfirm} className="btn-secondary">
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
        <p className="text-base font-semibold text-text-main">Want to experience more of this IDE?</p>
        <p className="text-sm leading-relaxed text-text-muted">
          Enroll at <span className="font-semibold text-text-brand">Pampanga State University</span> today! Enrolled students get the full
          IDE: real classes, graded activities, and progress that is kept.
        </p>
        <div className="pt-1">
          <a href={ADMISSION_URL} target="_blank" rel="noopener noreferrer" className="btn-primary w-full">
            Enroll at PSU
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M9 3h4v4M13 3L7 9M11 9.5V13H3V5h3.5" />
            </svg>
            <span className="sr-only">(opens the PSU admission page in a new tab)</span>
          </a>
          <p className="mt-1.5 break-all text-xs text-text-muted">sms.pampangastateu.edu.ph/padmission</p>
        </div>
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

  // Only students have workspaces and code drafts to lose.
  const message =
    user?.role === "student"
      ? "You will need to sign in again to access your workspace. Unsubmitted code drafts are removed from this browser, so the next person cannot see them. Submit your work first."
      : "Are you sure you want to sign out?";

  return (
    <ConfirmationModal
      isOpen={isOpen}
      title="Sign out?"
      message={message}
      confirmText="Sign out"
      onConfirm={onConfirm}
      onCancel={onClose}
      isDanger
    />
  );
}

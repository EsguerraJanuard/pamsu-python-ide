import ConfirmationModal from "../modals/ConfirmationModal";

export default function SignOutModal({ isOpen, onClose, onConfirm }) {
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

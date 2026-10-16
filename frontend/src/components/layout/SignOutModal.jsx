import ConfirmationModal from "../modals/ConfirmationModal";

export default function SignOutModal({ isOpen, onClose, onConfirm }) {
  return (
    <ConfirmationModal
      isOpen={isOpen}
      title="Sign out?"
      message="You will need to sign in again to access your workspace. Unsaved editor drafts stay in this browser."
      confirmText="Sign out"
      onConfirm={onConfirm}
      onCancel={onClose}
      isDanger
    />
  );
}

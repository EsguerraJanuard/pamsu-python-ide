import React from 'react';

export default function ConfirmationModal({ 
  isOpen, 
  title, 
  message, 
  confirmText = "Confirm", 
  cancelText = "Cancel", 
  onConfirm, 
  onCancel,
  isDanger = false 
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity">
      <div 
        className="w-full max-w-sm rounded-xl border border-border-subtle bg-bg-glass p-6 shadow-2xl transform transition-all scale-100 opacity-100"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-2 text-lg font-bold text-white">
          {title}
        </h3>
        <p className="mb-6 text-sm text-text-muted">
          {message}
        </p>
        
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-4 py-2 text-sm font-semibold text-text-muted transition-colors hover:bg-bg-glass hover:text-text-main"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`rounded-lg px-4 py-2 text-sm font-semibold text-text-main transition-colors ${
              isDanger 
                ? "bg-red-500/20 text-text-rose hover:bg-red-500 hover:text-text-main"
                : "bg-emerald-500 hover:bg-emerald-400"
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

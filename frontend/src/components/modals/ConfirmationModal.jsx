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
        className="w-full max-w-sm rounded-xl border border-white/[0.08] bg-[#1a1d27] p-6 shadow-2xl transform transition-all scale-100 opacity-100"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-2 text-lg font-bold text-white">
          {title}
        </h3>
        <p className="mb-6 text-sm text-white/60">
          {message}
        </p>
        
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-4 py-2 text-sm font-semibold text-white/60 transition-colors hover:bg-white/[0.04] hover:text-white"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors ${
              isDanger 
                ? "bg-red-500/20 text-red-400 hover:bg-red-500 hover:text-white"
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

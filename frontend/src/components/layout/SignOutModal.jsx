import React from "react";

export default function SignOutModal({ isOpen, onClose, onConfirm }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-sm transform overflow-hidden rounded-xl border border-white/[0.08] bg-[#1a1d27] p-6 text-left align-middle shadow-2xl transition-all">
        <h3 className="text-lg font-bold text-white">Sign Out</h3>
        <p className="mt-2 text-sm text-slate-400 leading-relaxed">
          Are you sure you want to sign out of your account? You will need to log in again to access your workspace.
        </p>
        
        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            type="button"
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/[0.06] transition-colors"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/20 hover:border-red-500/30 transition-colors"
            onClick={onConfirm}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

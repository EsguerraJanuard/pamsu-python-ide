import React from 'react';

export default function AlertModal({ 
  isOpen, 
  title = "Alert", 
  message, 
  onClose,
  isError = false
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity">
      <div 
        className="w-full max-w-sm rounded-xl border border-border-subtle bg-bg-panel p-6 shadow-2xl transform transition-all scale-100 opacity-100"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-2">
          {isError && (
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          <h3 className={`text-lg font-bold ${isError ? 'text-red-400' : 'text-text-main'}`}>
            {title}
          </h3>
        </div>
        
        <p className="mb-6 text-sm text-text-muted">
          {message}
        </p>
        
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-bg-glass hover:bg-bg-glass-hover px-5 py-2 text-sm font-semibold text-text-main transition-colors border border-border-subtle"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}

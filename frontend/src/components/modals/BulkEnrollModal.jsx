import { useState, useRef } from 'react';
import api from '../../services/api';

export default function BulkEnrollModal({ isOpen, onClose, classId, onSuccess }) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'paste'
  const [emailsText, setEmailsText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handlePasteSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    setResult(null);
    
    // Extract emails using a basic regex
    const emails = emailsText.match(/[a-zA-Z0-9_.+-]+@pampangastateu\.edu\.ph/gi) || [];
    
    if (emails.length === 0) {
      setError("No valid @pampangastateu.edu.ph email addresses found in the text.");
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await api.post(`/classrooms/${classId}/bulk-enroll`, {
        emails: [...new Set(emails)] // Unique
      });
      setResult(response);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.message || "An error occurred while enrolling students.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(`/classrooms/${classId}/bulk-enroll/file`, formData);
      setResult(response);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.message || "Failed to parse the file or enroll students.");
    } finally {
      setIsSubmitting(false);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-border-subtle bg-bg-panel p-6 shadow-2xl relative">
        <button 
          onClick={onClose}
          className="absolute right-4 top-4 text-text-muted hover:text-white"
        >
          ✕
        </button>

        <h2 className="mb-2 text-xl font-bold text-text-main">Bulk Enroll Students</h2>
        <p className="mb-6 text-sm text-text-muted">
          Add multiple students to your class instantly. Only <code className="bg-bg-base px-1 rounded">@pampangastateu.edu.ph</code> emails are accepted.
        </p>

        {!result ? (
          <>
            <div className="flex border-b border-border-subtle mb-6">
              <button
                className={`pb-2 px-4 text-sm font-medium ${activeTab === 'upload' ? 'border-b-2 border-brand-primary text-brand-primary' : 'text-text-muted hover:text-text-main'}`}
                onClick={() => setActiveTab('upload')}
              >
                Upload File (CSV/Excel)
              </button>
              <button
                className={`pb-2 px-4 text-sm font-medium ${activeTab === 'paste' ? 'border-b-2 border-brand-primary text-brand-primary' : 'text-text-muted hover:text-text-main'}`}
                onClick={() => setActiveTab('paste')}
              >
                Paste Emails
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-lg bg-red-900/20 p-3 text-sm text-red-400 border border-red-900/50">
                {error}
              </div>
            )}

            {activeTab === 'upload' ? (
              <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border-subtle bg-bg-base p-10 text-center transition-colors hover:border-brand-primary/50">
                <svg className="mb-3 h-10 w-10 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="mb-1 text-sm font-medium text-text-main">
                  Click to upload or drag and drop
                </p>
                <p className="mb-4 text-xs text-text-muted">
                  CSV, XLSX, or TXT files
                </p>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls,.txt"
                  className="hidden"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  disabled={isSubmitting}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isSubmitting}
                  className="rounded-lg bg-bg-glass px-4 py-2 text-xs font-semibold text-text-main hover:bg-bg-glass-hover disabled:opacity-50"
                >
                  {isSubmitting ? 'Processing...' : 'Select File'}
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <textarea
                  className="h-32 w-full rounded-xl border border-border-subtle bg-bg-base p-3 text-sm text-text-main placeholder-text-muted focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
                  placeholder="student1@pampangastateu.edu.ph, student2@pampangastateu.edu.ph&#10;Or paste a column from Excel here..."
                  value={emailsText}
                  onChange={(e) => setEmailsText(e.target.value)}
                  disabled={isSubmitting}
                />
                <button
                  onClick={handlePasteSubmit}
                  disabled={isSubmitting || !emailsText.trim()}
                  className="w-full rounded-xl bg-brand-primary py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-primary-hover disabled:opacity-50"
                >
                  {isSubmitting ? 'Enrolling...' : 'Enroll Students'}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center text-center p-6 bg-bg-base rounded-xl border border-border-subtle">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mb-4 text-emerald-400">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Enrollment Processed</h3>
            
            <div className="w-full grid grid-cols-3 gap-2 mt-4 text-sm">
              <div className="bg-bg-panel p-3 rounded-lg border border-border-subtle">
                <div className="text-2xl font-bold text-emerald-400">{result.enrolled || 0}</div>
                <div className="text-text-muted text-xs uppercase tracking-wider mt-1">Enrolled</div>
              </div>
              <div className="bg-bg-panel p-3 rounded-lg border border-border-subtle">
                <div className="text-2xl font-bold text-amber-400">{result.queued || 0}</div>
                <div className="text-text-muted text-xs uppercase tracking-wider mt-1">Queued</div>
              </div>
              <div className="bg-bg-panel p-3 rounded-lg border border-border-subtle">
                <div className="text-2xl font-bold text-red-400">{result.invalid || 0}</div>
                <div className="text-text-muted text-xs uppercase tracking-wider mt-1">Invalid</div>
              </div>
            </div>
            
            <p className="mt-6 text-xs text-text-muted text-left w-full">
              <strong>Queued students</strong> will be automatically enrolled the moment they create their account.<br/>
              <strong>Invalid emails</strong> were ignored (not ending in @pampangastateu.edu.ph).
            </p>
            
            <button
              onClick={onClose}
              className="mt-6 w-full rounded-xl bg-bg-glass py-2 text-sm font-semibold text-text-main hover:bg-bg-glass-hover"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

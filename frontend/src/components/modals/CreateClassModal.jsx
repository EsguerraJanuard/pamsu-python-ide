import { useState } from "react";
import api from "../../services/api";
export default function CreateClassModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({ name: "", subject_code: "", section: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedCode, setGeneratedCode] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await api.post("/classrooms/", formData);
      setGeneratedCode(data.class_code); 
      onSuccess(); 
    } catch (err) {
      setError(err.message || "Failed to create class. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetAndClose = () => {
    setFormData({ name: "", subject_code: "", section: "" });
    setGeneratedCode(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-glass p-6 shadow-2xl">
        {!generatedCode ? (
          <>
            <h2 className="mb-2 text-lg font-bold text-text-main">Create New Cohort</h2>
            <p className="mb-6 text-sm text-text-muted">
              Initialize a new class section for automated grading.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Course Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g. Object-Oriented Programming"
                  className="w-full rounded-lg border border-border-subtle bg-bg-base px-4 py-2.5 text-sm text-text-main focus:border-emerald-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Subject Code</label>
                <input
                  type="text"
                  name="subject_code"
                  value={formData.subject_code}
                  onChange={handleChange}
                  placeholder="e.g. CCS101"
                  className="w-full rounded-lg border border-border-subtle bg-bg-base px-4 py-2.5 text-sm text-text-main focus:border-emerald-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-text-muted">Section / Schedule</label>
                <input
                  type="text"
                  name="section"
                  value={formData.section}
                  onChange={handleChange}
                  placeholder="e.g. Block A"
                  className="w-full rounded-lg border border-border-subtle bg-bg-base px-4 py-2.5 text-sm text-text-main focus:border-emerald-500 focus:outline-none"
                  required
                />
              </div>

              {error && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-text-rose">
                  {error}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleResetAndClose}
                  className="rounded-lg px-4 py-2 text-xs font-semibold text-text-muted hover:bg-bg-glass hover:text-text-main"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !formData.name || !formData.subject_code || !formData.section}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50 hover:bg-emerald-500"
                >
                  {isLoading ? "Creating..." : "Create Class"}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-text-emerald">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2 className="mb-2 text-lg font-bold text-text-main">Class Created!</h2>
            <p className="mb-4 text-sm text-text-muted">
              Share this code with your students so they can join the class.
            </p>
            <div className="mb-6 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4">
              <span className="font-mono text-2xl font-bold tracking-wider text-text-emerald">
                {generatedCode}
              </span>
            </div>
            <button
              onClick={handleResetAndClose}
              className="w-full rounded-lg bg-white/[0.06] px-4 py-2.5 text-sm font-semibold text-text-main hover:bg-bg-glass-hover"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
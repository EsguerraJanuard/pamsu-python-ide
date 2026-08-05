import { useState } from "react";
import api from "../../services/api";
export default function JoinClassModal({ isOpen, onClose, onSuccess }) {
  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Basic validation: must be at least 6 characters
    if (code.trim().length < 6) {
      setError("Class code must be at least 6 characters.");
      return;
    }

    setIsLoading(true);

    try {
      await api.post("/classrooms/join", {
        class_code: code.trim(),
      });

      setCode("");
      if (onSuccess) onSuccess(); // Triggers the parent to refresh the class list
      onClose();
    } catch (err) {
      setError(err.message || "Invalid class code or class is full.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-white/[0.08] bg-[#1a1d27] p-6 shadow-2xl">
        <h2 className="mb-2 text-lg font-bold text-white">Join a Class</h2>
        <p className="mb-6 text-sm text-white/50">
          Ask your instructor for the class code and enter it below.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-white/70">
              Class Code
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="e.g. CCS101-XYZ"
              className="w-full rounded-lg border border-white/[0.08] bg-[#0f1117] px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:border-[#3b82f6] focus:outline-none"
              autoFocus
            />
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
              {error}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="rounded-lg px-4 py-2 text-xs font-semibold text-white/60 transition hover:bg-white/[0.04] hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !code}
              className="rounded-lg bg-[#3b82f6] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#2563eb] disabled:opacity-50"
            >
              {isLoading ? "Joining..." : "Join Class"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
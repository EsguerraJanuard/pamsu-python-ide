import { useState, useEffect } from "react";
import api from "../../services/api";

export default function EditClassModal({
  isOpen,
  onClose,
  classroom,
  onSuccess,
}) {
  const [className, setClassName] = useState("");
  const [schedule, setSchedule] = useState("");
  const [classCode, setClassCode] = useState("");

  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    if (classroom) {
      setClassName(classroom.name || classroom.class_name || "");
      setSchedule(classroom.schedule || "");
      setClassCode(classroom.class_code || classroom.code || classroom.invite_code || "");
    }
    setError("");
    setSuccessMsg("");
  }, [classroom, isOpen]);

  if (!isOpen || !classroom) return null;

  const handleSaveChanges = async (e) => {
    e.preventDefault();
    if (!className.trim()) {
      setError("Classroom name is required.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccessMsg("");

    try {
      const response = await api.patch(`/classrooms/${classroom.id}`, {
        name: className.trim(),
        schedule: schedule.trim() || undefined,
      });

      setSuccessMsg("Classroom updated successfully!");
      if (onSuccess) onSuccess(response || { ...classroom, name: className, schedule });
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      setError(err.message || "Failed to update classroom settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerateCode = async () => {
    setRegenerating(true);
    setError("");
    setSuccessMsg("");

    try {
      const response = await api.post(`/classrooms/${classroom.id}/regenerate-code`);
      const newCode = response?.class_code || response?.code || response?.invite_code;
      if (newCode) {
        setClassCode(newCode);
        setSuccessMsg(`Invite code regenerated: ${newCode}`);
        if (onSuccess) onSuccess({ ...classroom, code: newCode });
      } else {
        setSuccessMsg("Invite code regenerated successfully!");
      }
    } catch (err) {
      setError(err.message || "Failed to regenerate invite code.");
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-glass p-6 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-border-subtle pb-4">
          <div>
            <h2 className="text-lg font-bold text-text-main">Classroom Settings</h2>
            <p className="text-xs text-text-muted">Update classroom details or reset student invite code.</p>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-main text-lg font-bold p-1 rounded-lg hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-text-rose">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-text-emerald">
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSaveChanges} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-text-muted uppercase tracking-wider mb-1.5">
              Classroom Name
            </label>
            <input
              type="text"
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              placeholder="e.g. CS101 — Intro to Programming"
              className="w-full rounded-lg border border-border-subtle bg-bg-glass/80 px-3.5 py-2.5 text-sm text-text-main placeholder:text-text-muted focus:border-blue-500 focus:outline-none transition"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-muted uppercase tracking-wider mb-1.5">
              Schedule / Hours
            </label>
            <input
              type="text"
              value={schedule}
              onChange={(e) => setSchedule(e.target.value)}
              placeholder="e.g. Mon / Wed 10:00 AM - 12:00 PM"
              className="w-full rounded-lg border border-border-subtle bg-bg-glass/80 px-3.5 py-2.5 text-sm text-text-main placeholder:text-text-muted focus:border-blue-500 focus:outline-none transition"
            />
          </div>

          {/* Invite Code Regeneration Section */}
          <div className="rounded-xl border border-border-subtle/80 bg-bg-glass/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-text-muted">Student Invite Code</div>
                <div className="text-[11px] text-text-muted">Share with students to enroll.</div>
              </div>
              <div className="font-mono text-base font-extrabold text-text-blue bg-cyan-950/40 border border-cyan-500/30 px-2.5 py-1 rounded">
                {classCode || "------"}
              </div>
            </div>

            <button
              type="button"
              onClick={handleRegenerateCode}
              disabled={regenerating}
              className="w-full mt-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-text-amber hover:bg-amber-500/20 transition disabled:opacity-50"
            >
              {regenerating ? "Regenerating..." : "↻ Regenerate Invite Code"}
            </button>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border-subtle bg-bg-glass px-4 py-2 text-xs font-medium text-text-muted hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-blue-600 px-5 py-2 text-xs font-semibold text-text-main shadow-lg hover:bg-blue-500 transition disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

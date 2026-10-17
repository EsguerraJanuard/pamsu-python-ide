import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import CreateClassModal from "../../components/modals/CreateClassModal";
import { EmptyState, ErrorState, InlineAlert, PageHeader } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";

export default function ClassManagement() {
  const [classes, setClasses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [classToToggle, setClassToToggle] = useState(null);
  const [isToggling, setIsToggling] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const fetchClasses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get("/classrooms/");
      setClasses(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  const handleConfirmToggle = async () => {
    if (!classToToggle || isToggling) return;
    setIsToggling(true);
    try {
      const updated = await api.patch(`/classrooms/${classToToggle.class_id}`, { is_active: !classToToggle.is_active });
      setClasses((prev) =>
        prev.map((c) => (c.class_id === classToToggle.class_id ? { ...c, ...(updated || { is_active: !c.is_active }) } : c)),
      );
      setActionMessage({
        tone: "success",
        text: `${classToToggle.name} was ${classToToggle.is_active ? "archived" : "restored"}.`,
      });
      setClassToToggle(null);
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, "The class status could not be updated.") });
      setClassToToggle(null);
    } finally {
      setIsToggling(false);
    }
  };

  const copyCode = async (cls) => {
    try {
      await navigator.clipboard.writeText(cls.class_code);
      setCopiedId(cls.class_id);
      window.setTimeout(() => setCopiedId(null), 2000);
    } catch {
      setActionMessage({ tone: "error", text: "Your browser blocked clipboard access. Select the code and copy it manually." });
    }
  };

  return (
    <PageShell role="instructor">
      <PageHeader
        eyebrow="Management"
        title="Classes"
        description="Create classes, share enrollment codes and manage rosters."
        actions={
          <button type="button" onClick={() => setIsCreateOpen(true)} className="btn-primary">
            Create class
          </button>
        }
      />

      {actionMessage && (
        <InlineAlert tone={actionMessage.tone} onDismiss={() => setActionMessage(null)} className="mb-5">
          {actionMessage.text}
        </InlineAlert>
      )}

      {error ? (
        <ErrorState error={error} resource="your classes" onRetry={fetchClasses} />
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading classes">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card h-48 animate-pulse" />
          ))}
        </div>
      ) : classes.length === 0 ? (
        <EmptyState
          title="No classes yet"
          message="Create a class to generate an enrollment code for your students."
          action={
            <button type="button" className="btn-primary" onClick={() => setIsCreateOpen(true)}>
              Create class
            </button>
          }
        />
      ) : (
        <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {classes.map((cls) => (
            <li key={cls.class_id} className={`card flex flex-col p-5 ${cls.is_active ? "" : "bg-bg-alt/60"}`}>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                {cls.subject_code && <span className="badge badge-brand">{cls.subject_code}</span>}
                {cls.section && <span className="badge badge-neutral">Section {cls.section}</span>}
                <span className={`badge ${cls.is_active ? "badge-success" : "badge-neutral"}`}>
                  {cls.is_active ? "Active" : "Archived"}
                </span>
              </div>
              <h2 className="line-clamp-2 text-base font-semibold text-text-main">{cls.name}</h2>

              <div className="mt-4 rounded-lg border border-border-subtle bg-bg-alt px-3 py-2.5">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Enrollment code</p>
                <div className="mt-1 flex items-center justify-between gap-2">
                  <span className="font-mono text-lg font-bold tracking-widest text-text-brand">{cls.class_code}</span>
                  <button type="button" onClick={() => copyCode(cls)} className="btn-ghost btn-sm" aria-label={`Copy enrollment code for ${cls.name}`}>
                    {copiedId === cls.class_id ? "Copied" : "Copy"}
                  </button>
                </div>
              </div>

              <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-4">
                <Link to={`/instructor/classes/${cls.class_id}`} className="btn-secondary btn-sm">
                  Open roster
                </Link>
                <button
                  type="button"
                  onClick={() => setClassToToggle(cls)}
                  className={`btn-ghost btn-sm ${cls.is_active ? "hover:text-text-rose" : ""}`}
                >
                  {cls.is_active ? "Archive" : "Restore"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <CreateClassModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} onSuccess={fetchClasses} />

      <ConfirmationModal
        isOpen={Boolean(classToToggle)}
        title={classToToggle?.is_active ? "Archive this class?" : "Restore this class?"}
        message={
          classToToggle?.is_active
            ? `Students in "${classToToggle?.name}" will no longer be able to join or submit work. You can restore it later.`
            : `"${classToToggle?.name}" will become active again and students can submit work.`
        }
        confirmText={classToToggle?.is_active ? "Archive class" : "Restore class"}
        loadingText={classToToggle?.is_active ? "Archiving…" : "Restoring…"}
        isDanger={Boolean(classToToggle?.is_active)}
        isLoading={isToggling}
        onConfirm={handleConfirmToggle}
        onCancel={() => setClassToToggle(null)}
      />
    </PageShell>
  );
}

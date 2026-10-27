import { useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import CreateClassModal from "../../components/modals/CreateClassModal";
import { EmptyState, ErrorState, InlineAlert, PageHeader } from "../../components/ui/StateViews";
import useApiQuery from "../../hooks/useApiQuery";
import useUrlFilters from "../../hooks/useUrlFilters";
import api, { getErrorMessage } from "../../services/api";
import { updateCachedApi } from "../../services/queryClient";

const CLASSES_ENDPOINT = "/classrooms/";

// ?view=archived&q=cc102 — kept in the URL so a reload or a shared link
// opens the same list.
const FILTER_DEFAULTS = { view: "active", q: "" };
const FILTER_ALLOWED = { view: ["active", "archived"] };

const VIEWS = [
  ["active", "Active"],
  ["archived", "Archived"],
];

function matchesClass(cls, query) {
  if (!query) return true;
  return [cls.name, cls.subject_code, cls.section, cls.class_code]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(query));
}

export default function ClassManagement() {
  const classesQuery = useApiQuery(CLASSES_ENDPOINT);
  const [filters, setFilters] = useUrlFilters(FILTER_DEFAULTS, FILTER_ALLOWED);
  const [actionMessage, setActionMessage] = useState(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [classToToggle, setClassToToggle] = useState(null);
  const [isToggling, setIsToggling] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const classes = Array.isArray(classesQuery.data) ? classesQuery.data : [];
  const activeClasses = classes.filter((c) => c.is_active);
  const archivedClasses = classes.filter((c) => !c.is_active);
  const showingArchived = filters.view === "archived";
  const query = filters.q.trim().toLowerCase();
  const inView = showingArchived ? archivedClasses : activeClasses;
  const visibleClasses = inView.filter((c) => matchesClass(c, query));

  const setActive = async (cls, isActive) => {
    const updated = await api.patch(`/classrooms/${cls.class_id}`, { is_active: isActive });
    // Show the change at once; the API client's change notice also reloads the list.
    updateCachedApi(CLASSES_ENDPOINT, (prev) =>
      Array.isArray(prev) ? prev.map((c) => (c.class_id === cls.class_id ? { ...c, ...(updated || { is_active: isActive }) } : c)) : prev,
    );
  };

  const handleConfirmToggle = async () => {
    if (!classToToggle || isToggling) return;
    const cls = classToToggle;
    const archiving = cls.is_active;
    setIsToggling(true);
    try {
      await setActive(cls, !archiving);
      setActionMessage(
        archiving
          ? { tone: "success", text: `${cls.name} was archived. Find it under Archived.`, undo: cls }
          : { tone: "success", text: `${cls.name} was unarchived and is active again.` },
      );
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, "The class status could not be updated.") });
    } finally {
      setClassToToggle(null);
      setIsToggling(false);
    }
  };

  // "Undo" right after an archive: restores without a second confirmation.
  const undoArchive = async (cls) => {
    setIsToggling(true);
    try {
      await setActive(cls, true);
      setActionMessage({ tone: "success", text: `Archive undone. ${cls.name} is active again.` });
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, "The class could not be unarchived.") });
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

  const countFor = (view) => (view === "archived" ? archivedClasses.length : activeClasses.length);

  return (
    <PageShell role="instructor">
      <PageHeader
        eyebrow="Management"
        title="Classes"
        description="Create classes, share enrollment codes and manage rosters. Archived classes can be unarchived at any time."
        actions={
          <button type="button" onClick={() => setIsCreateOpen(true)} className="btn-primary">
            Create class
          </button>
        }
      />

      {actionMessage && (
        <InlineAlert tone={actionMessage.tone} onDismiss={() => setActionMessage(null)} className="mb-5">
          <span>{actionMessage.text}</span>
          {actionMessage.undo && (
            <button
              type="button"
              className="ml-2 font-semibold underline underline-offset-2 disabled:opacity-60"
              onClick={() => undoArchive(actionMessage.undo)}
              disabled={isToggling}
            >
              {isToggling ? "Undoing…" : "Undo"}
            </button>
          )}
        </InlineAlert>
      )}

      {classesQuery.error && !classesQuery.data ? (
        <ErrorState error={classesQuery.error} resource="your classes" onRetry={() => classesQuery.refetch()} />
      ) : classesQuery.isPending ? (
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
        <>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex w-fit gap-1 rounded-lg border border-border-subtle bg-bg-panel p-1" role="tablist" aria-label="Class status">
              {VIEWS.map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  role="tab"
                  aria-selected={filters.view === value}
                  onClick={() => setFilters({ view: value })}
                  className={`rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors ${
                    filters.view === value ? "bg-psu-maroon text-white shadow-sm" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
                  }`}
                >
                  {label}
                  <span className={`ml-1.5 text-xs ${filters.view === value ? "text-white/80" : "text-text-muted"}`}>{countFor(value)}</span>
                </button>
              ))}
            </div>
            <div className="w-full sm:w-72">
              <label htmlFor="class-search" className="sr-only">
                Search classes
              </label>
              <input
                id="class-search"
                type="search"
                value={filters.q}
                onChange={(e) => setFilters({ q: e.target.value })}
                placeholder="Search name, subject, section or code…"
                className="input-field"
              />
            </div>
          </div>

          {visibleClasses.length === 0 ? (
            query ? (
              <EmptyState
                icon="search"
                title="No matching classes"
                message={`No ${showingArchived ? "archived" : "active"} class matches “${filters.q.trim()}”.`}
                action={
                  <button type="button" className="btn-secondary" onClick={() => setFilters({ q: "" })}>
                    Clear search
                  </button>
                }
              />
            ) : showingArchived ? (
              <EmptyState title="No archived classes" message="Classes you archive appear here, where you can unarchive them." />
            ) : (
              <EmptyState
                title="No active classes"
                message="Every class is archived. Unarchive one from the Archived tab, or create a new class."
                action={
                  <button type="button" className="btn-secondary" onClick={() => setFilters({ view: "archived" })}>
                    Show archived classes
                  </button>
                }
              />
            )
          ) : (
            <ul className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {visibleClasses.map((cls) => (
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
                      className={`btn-sm ${cls.is_active ? "btn-ghost hover:text-text-rose" : "btn-primary"}`}
                    >
                      {cls.is_active ? "Archive" : "Unarchive"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      <CreateClassModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />

      <ConfirmationModal
        isOpen={Boolean(classToToggle)}
        title={classToToggle?.is_active ? "Archive this class?" : "Unarchive this class?"}
        message={
          classToToggle?.is_active
            ? `Students in "${classToToggle?.name}" will no longer be able to join or submit work. You can unarchive it later from the Archived tab.`
            : `"${classToToggle?.name}" will become active again and students can submit work.`
        }
        confirmText={classToToggle?.is_active ? "Archive class" : "Unarchive class"}
        loadingText={classToToggle?.is_active ? "Archiving…" : "Unarchiving…"}
        isDanger={Boolean(classToToggle?.is_active)}
        isLoading={isToggling}
        onConfirm={handleConfirmToggle}
        onCancel={() => setClassToToggle(null)}
      />
    </PageShell>
  );
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import SignOutModal from "../../components/layout/SignOutModal";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { EmptyState, ErrorState, FieldError, InlineAlert, LoadingState, PageHeader } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { formatDateTime, humanize } from "../../utils/format";
import { useAuth } from "../auth/AuthContext";

const PAGE_SIZE = 50;
const SCHOOL_EMAIL = /^[^\s@]+@pampangastateu\.edu\.ph$/i;
const SCHOOL_ID = /^(\d{10}|\d{4}-\d{5})$/;

const TABS = [
  { id: "overview", label: "Overview", icon: "M3 12l2-2 7-7 7 7 2 2M5 10v10h4v-6h6v6h4V10" },
  { id: "faculty", label: "Faculty", icon: "M12 14l9-5-9-5-9 5 9 5zm0 0v6m-6-9.5v5.5l6 3 6-3v-5.5" },
  { id: "students", label: "Students", icon: "M17 20h5v-2a3 3 0 00-5.36-1.86M9 20H4v-2a4 4 0 017-2.65M15 7a3 3 0 11-6 0 3 3 0 016 0z" },
  { id: "audit", label: "Audit trail", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" },
  { id: "settings", label: "Settings", icon: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-2.82 1.17V21a2 2 0 11-4 0v-.09A1.65 1.65 0 008.6 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06A1.65 1.65 0 003 15.08V15a2 2 0 110-4h.09A1.65 1.65 0 004.6 8.6a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.6V4a2 2 0 114 0v.09a1.65 1.65 0 001.03 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06A1.65 1.65 0 0019.4 9c.4.16.84.24 1.28.24H21a2 2 0 110 4h-.09c-.44 0-.88.08-1.28.24z" },
];

const STRICTNESS = [
  ["lax", "Lenient", "Focus on execution output; structural checks are relaxed."],
  ["moderate", "Moderate", "Balanced structural checks (recommended)."],
  ["strict", "Strict", "Required structures are enforced rigidly."],
];

/** Random temporary password (letters, digits, symbol) shown once to the admin. */
function generateTempPassword() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const bytes = new Uint32Array(10);
  crypto.getRandomValues(bytes);
  const core = Array.from(bytes, (b) => alphabet[b % alphabet.length]).join("");
  return `${core.slice(0, 5)}-${core.slice(5)}!`;
}

/** Admin endpoints may be missing on a server; explain that plainly. */
function AdminErrorState({ error, resource, onRetry }) {
  if (error?.status === 404) {
    return (
      <ErrorState
        error={error}
        title="Administration service unavailable"
        message="This server does not expose the administration API, so this information can't be loaded. Contact the system maintainer."
      />
    );
  }
  return <ErrorState error={error} resource={resource} onRetry={onRetry} />;
}

function useAdminList(endpoint) {
  const [items, setItems] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get(`${endpoint}?skip=0&limit=${PAGE_SIZE}`);
      const list = Array.isArray(data) ? data : [];
      setItems(list);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [endpoint]);

  const loadMore = async () => {
    setIsLoadingMore(true);
    try {
      const data = await api.get(`${endpoint}?skip=${items.length}&limit=${PAGE_SIZE}`);
      const list = Array.isArray(data) ? data : [];
      setItems((prev) => [...prev, ...list]);
      setHasMore(list.length === PAGE_SIZE);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoadingMore(false);
    }
  };

  return { items, setItems, hasMore, isLoading, isLoadingMore, error, load, loadMore };
}

function TextField({ id, label, error, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <input
        id={id}
        className="input-field"
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      <FieldError id={`${id}-error`}>{error}</FieldError>
    </div>
  );
}

function ProvisionForm({ role, onCreated }) {
  const isStudent = role === "student";
  const empty = { email: "", first_name: "", last_name: "", school_id: "", password: generateTempPassword() };
  const [form, setForm] = useState(empty);
  const [errors, setErrors] = useState({});
  const [result, setResult] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const set = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const next = {};
    if (!SCHOOL_EMAIL.test(form.email.trim())) next.email = "Use an @pampangastateu.edu.ph email address.";
    if (!form.first_name.trim()) next.first_name = "First name is required.";
    if (!form.last_name.trim()) next.last_name = "Last name is required.";
    if (isStudent && !SCHOOL_ID.test(form.school_id.trim())) next.school_id = "Use a 10-digit ID or the format 2026-00001.";
    if (form.password.length < 8) next.password = "Use at least 8 characters.";
    setErrors(next);
    if (Object.keys(next).length) return;

    setIsSaving(true);
    setResult(null);
    try {
      const payload = {
        email: form.email.trim().toLowerCase(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        password: form.password,
        ...(isStudent ? { school_id: form.school_id.trim() } : {}),
      };
      const created = await api.post(isStudent ? "/admin/students" : "/admin/instructors", payload);
      const pending = created?.pending_enrollments;
      const joined = pending?.enrolled_class_ids?.length ?? 0;
      const waiting = pending?.skipped?.length ?? 0;
      const enrollmentNote = [
        joined > 0 && `Added to ${joined} class${joined === 1 ? "" : "es"} that had queued this email.`,
        waiting > 0 && `${waiting} queued class${waiting === 1 ? " is" : "es are"} inactive or could not be joined and stay${waiting === 1 ? "s" : ""} pending.`,
      ].filter(Boolean).join(" ");
      setResult({
        tone: waiting > 0 ? "warning" : "success",
        text: `Account created for ${payload.email}. Temporary password: ${payload.password} — share it securely.${enrollmentNote ? ` ${enrollmentNote}` : ""}`,
      });
      setForm({ ...empty, password: generateTempPassword() });
      onCreated?.();
    } catch (err) {
      setResult({ tone: "error", text: getErrorMessage(err, "The account could not be created.") });
    } finally {
      setIsSaving(false);
    }
  };

  const prefix = `provision-${role}`;
  return (
    <form onSubmit={handleSubmit} noValidate className="card space-y-4 p-5">
      <h2 className="text-sm font-semibold">{isStudent ? "Create student account" : "Create faculty account"}</h2>
      {result && (
        <InlineAlert tone={result.tone} onDismiss={() => setResult(null)}>
          {result.text}
        </InlineAlert>
      )}
      <TextField id={`${prefix}-email`} label="University email" type="email" autoComplete="off" value={form.email} onChange={set("email")} error={errors.email} disabled={isSaving} />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TextField id={`${prefix}-first`} label="First name" value={form.first_name} onChange={set("first_name")} error={errors.first_name} disabled={isSaving} />
        <TextField id={`${prefix}-last`} label="Last name" value={form.last_name} onChange={set("last_name")} error={errors.last_name} disabled={isSaving} />
      </div>
      {isStudent && (
        <TextField id={`${prefix}-school-id`} label="School ID" value={form.school_id} onChange={set("school_id")} error={errors.school_id} disabled={isSaving} />
      )}
      <div>
        <label htmlFor={`${prefix}-password`} className="field-label">
          Temporary password
        </label>
        <div className="flex gap-2">
          <input
            id={`${prefix}-password`}
            type="text"
            value={form.password}
            onChange={set("password")}
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? `${prefix}-password-error` : undefined}
            className="input-field font-mono"
            disabled={isSaving}
            autoComplete="off"
          />
          <button type="button" className="btn-secondary shrink-0" onClick={() => setForm((p) => ({ ...p, password: generateTempPassword() }))} disabled={isSaving}>
            Generate
          </button>
        </div>
        <FieldError id={`${prefix}-password-error`}>{errors.password}</FieldError>
      </div>
      <button type="submit" disabled={isSaving} className="btn-primary w-full">
        {isSaving ? "Creating…" : "Create account"}
      </button>
    </form>
  );
}

function UserTable({ users, emptyMessage, onAction }) {
  if (users.length === 0) return <EmptyState className="py-10" title="No accounts" message={emptyMessage} />;
  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[620px] text-left text-sm">
          <thead className="border-b border-border-subtle bg-bg-alt text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            <tr>
              <th scope="col" className="px-4 py-3">Name</th>
              <th scope="col" className="px-4 py-3">School ID</th>
              <th scope="col" className="px-4 py-3">Status</th>
              <th scope="col" className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {users.map((user) => (
              <tr key={user.user_id}>
                <td className="px-4 py-3">
                  <p className="font-medium text-text-main">{user.name}</p>
                  <p className="text-xs text-text-muted">{user.email}</p>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-text-muted">{user.school_id || "—"}</td>
                <td className="px-4 py-3">
                  <span className={`badge ${user.is_active ? "badge-success" : "badge-neutral"}`}>{user.is_active ? "Active" : "Suspended"}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1">
                    <button type="button" className="btn-ghost btn-sm" onClick={() => onAction(user, "reset")}>
                      Reset password
                    </button>
                    <button type="button" className={`btn-ghost btn-sm ${user.is_active ? "hover:text-psu-red" : ""}`} onClick={() => onAction(user, "status")}>
                      {user.is_active ? "Suspend" : "Activate"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [pendingTab, setPendingTab] = useState(null);
  const [isSignOutOpen, setIsSignOutOpen] = useState(false);

  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const users = useAdminList("/admin/users");
  const logs = useAdminList("/admin/audit-logs");

  const [settings, setSettings] = useState(null);
  const [savedSettings, setSavedSettings] = useState(null);
  const [settingsError, setSettingsError] = useState(null);
  const [settingsMessage, setSettingsMessage] = useState(null);
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  const [search, setSearch] = useState("");
  const [userAction, setUserAction] = useState(null);
  const [isActing, setIsActing] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);
  const [bulkMessage, setBulkMessage] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileRef = useRef(null);

  const loadStats = useCallback(async () => {
    setStatsError(null);
    try {
      setStats(await api.get("/admin/stats"));
    } catch (err) {
      setStatsError(err);
    }
  }, []);

  const loadSettings = useCallback(async () => {
    setSettingsError(null);
    try {
      const data = await api.get("/admin/settings");
      setSettings(data);
      setSavedSettings(data);
    } catch (err) {
      setSettingsError(err);
    }
  }, []);

  const { load: loadUsers } = users;
  const { load: loadLogs } = logs;
  useEffect(() => {
    loadStats();
    loadUsers();
    loadLogs();
    loadSettings();
  }, [loadStats, loadUsers, loadLogs, loadSettings]);

  const settingsDirty =
    settings && savedSettings && ["maintenance_mode", "default_ast_strictness"].some((k) => settings[k] !== savedSettings[k]);

  const changeTab = (tab) => {
    if (activeTab === "settings" && settingsDirty && tab !== "settings") {
      setPendingTab(tab);
      return;
    }
    setActiveTab(tab);
  };

  const faculty = users.items.filter((u) => u.role === "instructor");
  const students = users.items.filter((u) => u.role === "student");
  const query = search.trim().toLowerCase();
  const filteredStudents = useMemo(
    () => (query ? students.filter((s) => [s.name, s.email, s.school_id].some((v) => v && v.toLowerCase().includes(query))) : students),
    [students, query],
  );

  const runUserAction = async () => {
    if (!userAction || isActing) return;
    const { user, type, password } = userAction;
    setIsActing(true);
    try {
      if (type === "status") {
        const res = await api.patch(`/admin/users/${user.user_id}/status`);
        users.setItems((prev) => prev.map((u) => (u.user_id === user.user_id ? { ...u, is_active: res?.is_active ?? !u.is_active } : u)));
        setActionMessage({ tone: "success", text: `${user.name} is now ${(res?.is_active ?? !user.is_active) ? "active" : "suspended"}.` });
      } else {
        await api.patch(`/admin/users/${user.user_id}/password`, { new_password: password });
        setActionMessage({ tone: "success", text: `Password for ${user.email} was reset to ${password} — share it securely.` });
      }
    } catch (err) {
      setActionMessage({ tone: "error", text: getErrorMessage(err, "The action could not be completed.") });
    } finally {
      setIsActing(false);
      setUserAction(null);
    }
  };

  const handleBulkUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setIsUploading(true);
    setBulkMessage(null);
    try {
      const res = await api.post("/admin/students/bulk-register/file", formData);
      const fromPending = res?.enrolled_from_pending ?? 0;
      const pendingLeft = res?.pending_left ?? 0;
      const created = res?.created ?? 0;
      const failedRows = (res?.rows ?? []).filter((row) => row.status === "failed");
      setBulkMessage({
        tone: failedRows.length > 0 || pendingLeft > 0 ? "warning" : "success",
        text:
          `${created} account${created === 1 ? "" : "s"} created, ${res?.skipped ?? 0} already existed, ${failedRows.length} row${failedRows.length === 1 ? "" : "s"} failed.` +
          (created > 0 ? " Students set their own password with “Forgot password?” on the sign-in page." : "") +
          (fromPending > 0 ? ` ${fromPending} queued class enrollment${fromPending === 1 ? " was" : "s were"} completed.` : "") +
          (pendingLeft > 0 ? ` ${pendingLeft} stay${pendingLeft === 1 ? "s" : ""} pending because the class is inactive or could not be joined.` : ""),
        rows: failedRows,
      });
      users.load();
      loadStats();
    } catch (err) {
      setBulkMessage({ tone: "error", text: getErrorMessage(err, "The file could not be processed.") });
    } finally {
      setIsUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const exportStudents = () => {
    const escape = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = [["User ID", "Name", "Email", "School ID", "Active"], ...students.map((u) => [u.user_id, u.name, u.email, u.school_id, u.is_active])];
    const blob = new Blob([rows.map((r) => r.map(escape).join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "pamsu_students.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const saveSettings = async (event) => {
    event.preventDefault();
    setIsSavingSettings(true);
    setSettingsMessage(null);
    try {
      await api.patch("/admin/settings", {
        maintenance_mode: Boolean(settings.maintenance_mode),
        // Required by the API but no longer editable here: send back the
        // stored value unchanged so saving never flips it.
        registration_enabled: Boolean(savedSettings?.registration_enabled),
        default_ast_strictness: settings.default_ast_strictness || "moderate",
      });
      setSavedSettings(settings);
      setSettingsMessage({ tone: "success", text: "Settings saved." });
    } catch (err) {
      setSettingsMessage({ tone: "error", text: getErrorMessage(err, "Settings could not be saved.") });
    } finally {
      setIsSavingSettings(false);
    }
  };

  const tabButton = (tab, compact = false) => (
    <button
      key={tab.id}
      type="button"
      onClick={() => changeTab(tab.id)}
      aria-current={activeTab === tab.id ? "page" : undefined}
      className={`flex items-center gap-2.5 rounded-lg text-sm transition-colors ${compact ? "shrink-0 px-3 py-2" : "w-full px-3 py-2.5"} ${
        activeTab === tab.id
          ? "bg-psu-cream font-semibold text-psu-maroon shadow-[inset_3px_0_0_var(--color-psu-gold)]"
          : "font-medium text-text-muted hover:bg-bg-alt hover:text-text-main"
      }`}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d={tab.icon} />
      </svg>
      {tab.label}
    </button>
  );

  return (
    <div className="flex min-h-screen flex-col bg-bg-base text-text-main">
      <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between border-b border-border-subtle bg-bg-panel px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/school_logo.png" alt="Pampanga State University logo" className="h-10 w-10 object-contain" />
          <div className="min-w-0 leading-tight">
            <p className="truncate text-sm font-bold tracking-tight sm:text-base">Pampanga State University</p>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">MIS Administration</p>
          </div>
        </div>
        <button type="button" onClick={() => setIsSignOutOpen(true)} className="btn-secondary btn-sm">
          Sign out
        </button>
      </header>

      <nav aria-label="Administration sections" className="flex gap-1 overflow-x-auto border-b border-border-subtle bg-bg-panel px-3 py-2 lg:hidden">
        {TABS.map((tab) => tabButton(tab, true))}
      </nav>

      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-60 shrink-0 border-r border-border-subtle bg-bg-panel p-4 lg:block">
          <nav aria-label="Administration sections" className="space-y-1">
            {TABS.map((tab) => tabButton(tab))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 px-4 py-6 sm:px-8">
          <div className="animate-page-fade mx-auto w-full max-w-6xl">
            {actionMessage && (
              <InlineAlert tone={actionMessage.tone} onDismiss={() => setActionMessage(null)} className="mb-5">
                {actionMessage.text}
              </InlineAlert>
            )}

            {activeTab === "overview" && (
              <>
                <PageHeader eyebrow="Metrics" title="System overview" description="Accounts and classrooms across the platform." />
                {statsError ? (
                  <AdminErrorState error={statsError} resource="platform statistics" onRetry={loadStats} />
                ) : !stats ? (
                  <LoadingState label="Loading statistics…" />
                ) : (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    {[
                      ["Instructors", stats.total_instructors],
                      ["Students", stats.total_students],
                      ["Classrooms", stats.total_classrooms],
                    ].map(([label, value]) => (
                      <div key={label} className="card p-5">
                        <p className="text-3xl font-bold tracking-tight">{value ?? 0}</p>
                        <p className="mt-1 text-sm font-medium text-text-muted">{label}</p>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {activeTab === "faculty" && (
              <>
                <PageHeader eyebrow="Accounts" title="Faculty" description="Create instructor accounts and manage access." />
                <div className="grid grid-cols-1 gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
                  <ProvisionForm role="instructor" onCreated={() => { users.load(); loadStats(); }} />
                  <div className="min-w-0">
                    {users.error ? (
                      <AdminErrorState error={users.error} resource="faculty accounts" onRetry={users.load} />
                    ) : users.isLoading ? (
                      <LoadingState label="Loading accounts…" />
                    ) : (
                      <UserTable users={faculty} emptyMessage="No faculty accounts have been created yet." onAction={(user, type) => setUserAction({ user, type, password: generateTempPassword() })} />
                    )}
                  </div>
                </div>
              </>
            )}

            {activeTab === "students" && (
              <>
                <PageHeader
                  eyebrow="Accounts"
                  title="Students"
                  description="Create student accounts individually or from a masterlist file."
                  actions={
                    <button type="button" className="btn-secondary" onClick={exportStudents} disabled={students.length === 0}>
                      Export CSV
                    </button>
                  }
                />
                <div className="grid grid-cols-1 gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
                  <div className="space-y-4">
                    <ProvisionForm role="student" onCreated={() => { users.load(); loadStats(); }} />
                    <div className="card p-5">
                      <h2 className="text-sm font-semibold">Bulk register from masterlist</h2>
                      <p className="mt-1 text-xs text-text-muted">
                        Upload a CSV or .xlsx masterlist with the columns <code>email</code>, <code>school_id</code> and <code>name</code> (or <code>first_name</code> and <code>last_name</code>). No password is set or emailed.
                      </p>
                      {bulkMessage && (
                        <InlineAlert tone={bulkMessage.tone} onDismiss={() => setBulkMessage(null)} className="mt-3">
                          {bulkMessage.text}
                          {bulkMessage.rows?.length > 0 && (
                            <ul className="mt-2 max-h-40 list-disc space-y-1 overflow-y-auto pl-4 text-xs">
                              {bulkMessage.rows.map((row) => (
                                <li key={row.row}>
                                  Row {row.row}
                                  {row.email ? ` (${row.email})` : ""}: {row.reason}
                                </li>
                              ))}
                            </ul>
                          )}
                        </InlineAlert>
                      )}
                      <label htmlFor="admin-bulk-file" className="btn-secondary mt-3 w-full cursor-pointer">
                        {isUploading ? "Uploading…" : "Choose file"}
                      </label>
                      <input ref={fileRef} id="admin-bulk-file" type="file" accept=".csv,.xlsx" className="sr-only" onChange={handleBulkUpload} disabled={isUploading} />
                    </div>
                  </div>
                  <div className="min-w-0">
                    <div className="mb-3 w-full sm:w-80">
                      <label htmlFor="admin-student-search" className="sr-only">
                        Search students
                      </label>
                      <input id="admin-student-search" type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name, email or ID…" className="input-field" />
                    </div>
                    {users.error ? (
                      <AdminErrorState error={users.error} resource="student accounts" onRetry={users.load} />
                    ) : users.isLoading ? (
                      <LoadingState label="Loading accounts…" />
                    ) : (
                      <UserTable
                        users={filteredStudents}
                        emptyMessage={query ? "No students match your search." : "No student accounts yet."}
                        onAction={(user, type) => setUserAction({ user, type, password: generateTempPassword() })}
                      />
                    )}
                    {users.hasMore && !users.error && (
                      <button type="button" className="btn-secondary mt-4 w-full" onClick={users.loadMore} disabled={users.isLoadingMore}>
                        {users.isLoadingMore ? "Loading…" : "Load more accounts"}
                      </button>
                    )}
                  </div>
                </div>
              </>
            )}

            {activeTab === "audit" && (
              <>
                <PageHeader eyebrow="Security" title="Global audit trail" description="Recorded account, classroom and academic events." />
                {logs.error ? (
                  <AdminErrorState error={logs.error} resource="the audit trail" onRetry={logs.load} />
                ) : logs.isLoading ? (
                  <LoadingState label="Loading audit trail…" />
                ) : logs.items.length === 0 ? (
                  <EmptyState title="No audit events" message="Recorded actions will appear here." />
                ) : (
                  <div className="card overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[640px] text-left text-sm">
                        <thead className="border-b border-border-subtle bg-bg-alt text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                          <tr>
                            <th scope="col" className="px-4 py-3">When</th>
                            <th scope="col" className="px-4 py-3">Actor</th>
                            <th scope="col" className="px-4 py-3">Event</th>
                            <th scope="col" className="px-4 py-3">Resource</th>
                            <th scope="col" className="px-4 py-3 text-right">Outcome</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-subtle">
                          {logs.items.map((log) => (
                            <tr key={log.log_id}>
                              <td className="whitespace-nowrap px-4 py-3 text-xs text-text-muted">{formatDateTime(log.occurred_at)}</td>
                              <td className="px-4 py-3">
                                <p className="font-medium text-text-main">{log.actor_name}</p>
                                <p className="text-xs text-text-muted">{humanize(log.actor_role)}</p>
                              </td>
                              <td className="px-4 py-3 text-text-main">{humanize(log.action_type)}</td>
                              <td className="px-4 py-3 text-text-muted">{humanize(log.resource_type)}</td>
                              <td className="px-4 py-3 text-right">
                                <span className={`badge ${log.status === "succeeded" ? "badge-success" : log.status === "failed" ? "badge-danger" : "badge-gold"}`}>
                                  {humanize(log.status)}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                {logs.hasMore && !logs.error && (
                  <button type="button" className="btn-secondary mt-4 w-full" onClick={logs.loadMore} disabled={logs.isLoadingMore}>
                    {logs.isLoadingMore ? "Loading…" : "Load older events"}
                  </button>
                )}
              </>
            )}

            {activeTab === "settings" && (
              <>
                <PageHeader eyebrow="Configuration" title="System settings" description="Platform-wide policies." />
                {settingsError ? (
                  <AdminErrorState error={settingsError} resource="system settings" onRetry={loadSettings} />
                ) : !settings ? (
                  <LoadingState label="Loading settings…" />
                ) : (
                  <form onSubmit={saveSettings} noValidate className="card max-w-3xl space-y-6 p-6">
                    {settingsMessage && (
                      <InlineAlert tone={settingsMessage.tone} onDismiss={() => setSettingsMessage(null)}>
                        {settingsMessage.text}
                      </InlineAlert>
                    )}
                    {[
                      ["maintenance_mode", "Maintenance mode", "Blocks student sign-in. Instructors and MIS keep access."],
                    ].map(([key, label, help]) => (
                      <div key={key} className="flex items-start justify-between gap-4">
                        <div>
                          <p id={`setting-${key}-label`} className="text-sm font-semibold text-text-main">
                            {label}
                          </p>
                          <p className="text-xs text-text-muted">{help}</p>
                        </div>
                        <button
                          type="button"
                          role="switch"
                          aria-checked={Boolean(settings[key])}
                          aria-labelledby={`setting-${key}-label`}
                          onClick={() => setSettings((prev) => ({ ...prev, [key]: !prev[key] }))}
                          className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${settings[key] ? "bg-psu-maroon" : "bg-border-strong"}`}
                        >
                          <span className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${settings[key] ? "translate-x-[22px]" : "translate-x-0.5"}`} aria-hidden="true" />
                        </button>
                      </div>
                    ))}
                    {/* Public self-registration is retired; this reports the stored
                        legacy flag (it still gates POST /registration/start) instead
                        of offering a toggle. */}
                    <div>
                      <p className="text-sm font-semibold text-text-main">Student self-registration</p>
                      {savedSettings?.registration_enabled ? (
                        <InlineAlert tone="warning" className="mt-2">
                          Public sign-up has been removed from the app, but the legacy self-registration setting is still
                          enabled on the server, so its registration API remains open. Student accounts are provisioned by
                          MIS; ask the system maintainer to turn this setting off.
                        </InlineAlert>
                      ) : (
                        <p className="text-xs text-text-muted">
                          Student self-registration is disabled. Student accounts are provisioned by MIS.
                        </p>
                      )}
                    </div>
                    <fieldset>
                      <legend className="text-sm font-semibold text-text-main">Default AST strictness</legend>
                      <p className="mb-3 text-xs text-text-muted">Used for instructors who haven&apos;t chosen their own level.</p>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                        {STRICTNESS.map(([value, label, help]) => (
                          <label key={value} className="cursor-pointer rounded-xl border border-border-strong p-4 transition-colors has-[:checked]:border-psu-maroon has-[:checked]:bg-psu-cream">
                            <input
                              type="radio"
                              name="default-strictness"
                              value={value}
                              checked={settings.default_ast_strictness === value}
                              onChange={() => setSettings((prev) => ({ ...prev, default_ast_strictness: value }))}
                              className="accent-psu-maroon"
                            />
                            <span className="ml-2 text-sm font-semibold text-text-main">{label}</span>
                            <span className="mt-1 block text-xs text-text-muted">{help}</span>
                          </label>
                        ))}
                      </div>
                    </fieldset>
                    <div className="flex items-center justify-end gap-3 border-t border-border-subtle pt-5">
                      {settingsDirty && <span className="text-xs text-text-muted">Unsaved changes</span>}
                      <button type="submit" className="btn-primary" disabled={isSavingSettings || !settingsDirty}>
                        {isSavingSettings ? "Saving…" : "Save settings"}
                      </button>
                    </div>
                  </form>
                )}
              </>
            )}
          </div>
        </main>
      </div>

      <ConfirmationModal
        isOpen={Boolean(userAction)}
        title={
          userAction?.type === "reset"
            ? "Reset password?"
            : userAction?.user?.is_active
              ? "Suspend account?"
              : "Activate account?"
        }
        message={
          userAction?.type === "reset"
            ? `${userAction?.user?.name}'s password will be replaced with a new temporary password, which will be shown to you once.`
            : userAction?.user?.is_active
              ? `${userAction?.user?.name} will not be able to sign in until the account is activated again.`
              : `${userAction?.user?.name} will be able to sign in again.`
        }
        confirmText={userAction?.type === "reset" ? "Reset password" : userAction?.user?.is_active ? "Suspend" : "Activate"}
        isDanger={userAction?.type === "reset" || Boolean(userAction?.user?.is_active)}
        isLoading={isActing}
        onConfirm={runUserAction}
        onCancel={() => setUserAction(null)}
      />
      <ConfirmationModal
        isOpen={Boolean(pendingTab)}
        title="Discard unsaved settings?"
        message="You changed system settings without saving. Leaving this section discards those changes."
        confirmText="Discard changes"
        isDanger
        onConfirm={() => {
          setSettings(savedSettings);
          setActiveTab(pendingTab);
          setPendingTab(null);
        }}
        onCancel={() => setPendingTab(null)}
      />
      <SignOutModal
        isOpen={isSignOutOpen}
        onClose={() => setIsSignOutOpen(false)}
        onConfirm={() => {
          setIsSignOutOpen(false);
          logout();
          navigate("/login", { replace: true });
        }}
      />
    </div>
  );
}

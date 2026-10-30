import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import PasswordInput from "../../components/ui/PasswordInput";
import { FieldError, InlineAlert } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { useAuth } from "../auth/AuthContext";

/** Settings card with a title, an optional description and its content. */
export function SettingsSection({ title, description, children, id }) {
  return (
    <section className="card p-5 sm:p-6" aria-labelledby={id}>
      <div className="mb-5">
        <h2 id={id} className="text-base font-semibold text-text-main">
          {title}
        </h2>
        {description && <p className="mt-1 text-sm text-text-muted">{description}</p>}
      </div>
      {children}
    </section>
  );
}

function ReadOnlyField({ id, label, value, note }) {
  return (
    <div>
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <input id={id} type="text" value={value || "—"} readOnly disabled className="input-field" />
      {note && <p className="mt-1.5 text-xs text-text-muted">{note}</p>}
    </div>
  );
}

/** Identity details are verified at registration and are read-only here. */
export function ProfileSection() {
  const { user } = useAuth();
  return (
    <SettingsSection
      id="profile-heading"
      title="Profile information"
      description="Your verified identity. To correct any detail, contact the MIS office."
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <ReadOnlyField id="settings-full-name" label="Full name" value={user?.name} />
        <ReadOnlyField id="settings-school-id" label="School ID" value={user?.school_id} />
        <div className="sm:col-span-2">
          <ReadOnlyField
            id="settings-email"
            label="University email"
            value={user?.email}
            note={user?.email_verified ? "Verified by email one-time code." : undefined}
          />
        </div>
      </div>
    </SettingsSection>
  );
}

function getPasswordStrength(password) {
  if (!password) return null;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { score: 1, label: "Weak", hint: "Use at least 8 characters.", tone: "bg-psu-red" };
  if (score === 2) return { score: 2, label: "Fair", hint: "Add uppercase letters, numbers or symbols.", tone: "bg-psu-gold" };
  if (score === 3) return { score: 3, label: "Good", hint: "One more character type makes it stronger.", tone: "bg-emerald-500" };
  return { score: 4, label: "Strong", hint: "", tone: "bg-emerald-600" };
}

const EMPTY_PASSWORDS = { currentPassword: "", newPassword: "", confirmPassword: "" };

const PASSWORD_FIELDS = [
  { key: "currentPassword", id: "current-password", label: "Current password", autoComplete: "current-password" },
  { key: "newPassword", id: "new-password", label: "New password", autoComplete: "new-password" },
  { key: "confirmPassword", id: "confirm-new-password", label: "Confirm new password", autoComplete: "new-password" },
];

function LockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="4" y="10.5" width="16" height="10" rx="2" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3M12 14.5v2" />
    </svg>
  );
}

function StrengthMeter({ strength }) {
  return (
    <div className="mt-2" aria-live="polite">
      <div className="flex gap-1" aria-hidden="true">
        {[1, 2, 3, 4].map((step) => (
          <span
            key={step}
            className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${step <= strength.score ? strength.tone : "bg-border-strong/60"}`}
          />
        ))}
      </div>
      <p className="mt-1.5 text-xs text-text-muted">
        <span className="font-semibold text-text-main">Strength: {strength.label}</span>
        {strength.hint ? ` · ${strength.hint}` : ""}
      </p>
    </div>
  );
}

/** Live checklist of the rules the server enforces on a new password. */
function PasswordRequirements({ passwords }) {
  const { currentPassword, newPassword, confirmPassword } = passwords;
  const rules = [
    { id: "length", label: "8 to 128 characters", met: newPassword.length >= 8 && newPassword.length <= 128 },
    { id: "different", label: "Different from your current password", met: newPassword.length > 0 && newPassword !== currentPassword },
    { id: "match", label: "Both new password fields match", met: confirmPassword.length > 0 && confirmPassword === newPassword },
  ];

  return (
    <div className="rounded-lg border border-border-subtle bg-bg-alt/60 p-4 md:self-start">
      <p className="text-[11px] font-semibold uppercase tracking-widest text-text-muted">Requirements</p>
      <ul className="mt-3 space-y-2.5">
        {rules.map((rule) => (
          <li key={rule.id} className={`flex items-start gap-2.5 text-sm transition-colors ${rule.met ? "text-text-emerald" : "text-text-muted"}`}>
            <span
              className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full transition-colors ${
                rule.met ? "bg-emerald-600 text-white" : "border border-border-strong bg-bg-panel"
              }`}
              aria-hidden="true"
            >
              {rule.met && (
                <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
                  <path d="M2.5 6.2 5 8.5l4.5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </span>
            <span>
              {rule.label}
              <span className="sr-only">{rule.met ? " (done)" : " (not yet)"}</span>
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-3 border-t border-border-subtle pt-3 text-xs leading-relaxed text-text-muted">
        Tip: mix uppercase letters, numbers and symbols, and don&apos;t reuse a password from another site.
      </p>
    </div>
  );
}

/**
 * Changing the password invalidates every existing session on the server,
 * so a successful change signs the user out and returns them to sign-in.
 * Shared by the student, faculty and MIS settings pages.
 */
export function ChangePasswordSection() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [passwords, setPasswords] = useState(EMPTY_PASSWORDS);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const signOutTimer = useRef(null);

  useEffect(() => () => window.clearTimeout(signOutTimer.current), []);

  const update = (field, value) => {
    setPasswords((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
    setFormError("");
  };

  const validate = () => {
    const errors = {};
    if (!passwords.currentPassword) errors.currentPassword = "Enter your current password.";
    if (passwords.newPassword.length < 8) errors.newPassword = "Use at least 8 characters.";
    else if (passwords.newPassword.length > 128) errors.newPassword = "Use at most 128 characters.";
    else if (passwords.newPassword === passwords.currentPassword)
      errors.newPassword = "Choose a password different from your current one.";
    if (!errors.newPassword && passwords.confirmPassword !== passwords.newPassword)
      errors.confirmPassword = "The passwords do not match.";
    return errors;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSaving || success) return;
    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsSaving(true);
    setFormError("");
    try {
      await api.patch("/users/me/password", {
        current_password: passwords.currentPassword,
        new_password: passwords.newPassword,
        confirm_password: passwords.confirmPassword,
      });
      setPasswords(EMPTY_PASSWORDS);
      setSuccess(true);
      signOutTimer.current = window.setTimeout(() => {
        logout();
        navigate("/login", { replace: true });
      }, 2500);
    } catch (err) {
      if (err?.status === 400) {
        setFieldErrors({ currentPassword: getErrorMessage(err, "The current password is incorrect.") });
      } else {
        setFormError(getErrorMessage(err, "Your password could not be changed. Please try again."));
      }
    } finally {
      setIsSaving(false);
    }
  };

  const strength = getPasswordStrength(passwords.newPassword);
  const locked = isSaving || success;

  return (
    <section className="card overflow-hidden" aria-labelledby="password-heading">
      <div className="flex items-start gap-3 border-b border-border-subtle px-5 py-4 sm:px-6">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-psu-maroon/[0.07] text-text-brand">
          <LockIcon />
        </span>
        <div className="min-w-0">
          <h2 id="password-heading" className="text-base font-semibold text-text-main">
            Change password
          </h2>
          <p className="mt-0.5 text-sm text-text-muted">Confirm your current password, then choose a new one.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="space-y-4 p-5 sm:p-6">
          {success && (
            <InlineAlert tone="success">Password changed. Signing you out so you can sign in with your new password…</InlineAlert>
          )}
          {formError && (
            <InlineAlert tone="error" onDismiss={() => setFormError("")}>
              {formError}
            </InlineAlert>
          )}

          <div className="grid grid-cols-1 gap-6 md:grid-cols-[minmax(0,1fr)_15rem]">
            <div className="space-y-4">
              {PASSWORD_FIELDS.map((field) => (
                <div key={field.key}>
                  <label htmlFor={field.id} className="field-label">
                    {field.label}
                  </label>
                  <PasswordInput
                    id={field.id}
                    value={passwords[field.key]}
                    onChange={(event) => update(field.key, event.target.value)}
                    autoComplete={field.autoComplete}
                    aria-invalid={Boolean(fieldErrors[field.key])}
                    aria-describedby={fieldErrors[field.key] ? `${field.id}-error` : undefined}
                    disabled={locked}
                  />
                  <FieldError id={`${field.id}-error`}>{fieldErrors[field.key]}</FieldError>
                  {field.key === "newPassword" && strength && !fieldErrors.newPassword && <StrengthMeter strength={strength} />}
                </div>
              ))}
            </div>
            <PasswordRequirements passwords={passwords} />
          </div>
        </div>

        <div className="flex flex-col gap-3 border-t border-border-subtle bg-bg-alt/60 px-5 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p className="text-xs text-text-muted">You&apos;ll be signed out on all devices after the change.</p>
          <button type="submit" disabled={locked} className="btn-primary w-full sm:w-auto">
            {isSaving && <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden="true" />}
            {isSaving ? "Updating…" : "Update password"}
          </button>
        </div>
      </form>
    </section>
  );
}

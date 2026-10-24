import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import PasswordInput from "../../components/ui/PasswordInput";
import { FieldError, InlineAlert } from "../../components/ui/StateViews";
import api, { getErrorMessage } from "../../services/api";
import { useAuth } from "../auth/AuthContext";

/**
 * Settings card. `divided` puts the title in its own header row above a
 * divider, matching the admin dashboard's cards; other pages keep the plain
 * layout.
 */
export function SettingsSection({ title, description, children, id, divided = false }) {
  if (divided) {
    return (
      <section className="card overflow-hidden" aria-labelledby={id}>
        <div className="border-b border-border-subtle px-5 py-4 sm:px-6">
          <h2 id={id} className="text-base font-semibold text-text-main">
            {title}
          </h2>
          {description && <p className="mt-0.5 text-sm text-text-muted">{description}</p>}
        </div>
        <div className="p-5 sm:p-6">{children}</div>
      </section>
    );
  }
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
  if (score <= 1) return { label: "Weak", hint: "Use at least 8 characters.", tone: "bg-psu-red", width: "25%" };
  if (score === 2) return { label: "Fair", hint: "Add uppercase letters, numbers or symbols.", tone: "bg-psu-gold", width: "50%" };
  if (score === 3) return { label: "Good", hint: "One more character type makes it stronger.", tone: "bg-psu-maroon", width: "75%" };
  return { label: "Strong", hint: "", tone: "bg-emerald-600", width: "100%" };
}

const EMPTY_PASSWORDS = { currentPassword: "", newPassword: "", confirmPassword: "" };

/**
 * Changing the password invalidates every existing session on the server,
 * so a successful change signs the user out and returns them to sign-in.
 */
export function ChangePasswordSection({ divided = false }) {
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
  const fields = [
    { key: "currentPassword", id: "current-password", label: "Current password", autoComplete: "current-password" },
    { key: "newPassword", id: "new-password", label: "New password", autoComplete: "new-password" },
    { key: "confirmPassword", id: "confirm-new-password", label: "Confirm new password", autoComplete: "new-password" },
  ];

  return (
    <SettingsSection
      id="password-heading"
      divided={divided}
      title="Change password"
      description="Your current password is verified by the server. You'll be signed out on all devices after a change."
    >
      {success && (
        <InlineAlert tone="success" className="mb-4">
          Password changed. Signing you out so you can sign in with your new password…
        </InlineAlert>
      )}
      {formError && (
        <InlineAlert tone="error" onDismiss={() => setFormError("")} className="mb-4">
          {formError}
        </InlineAlert>
      )}

      <form onSubmit={handleSubmit} noValidate className="max-w-xl space-y-5">
        {fields.map((field) => (
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
              disabled={isSaving || success}
            />
            <FieldError id={`${field.id}-error`}>{fieldErrors[field.key]}</FieldError>
            {field.key === "newPassword" && strength && !fieldErrors.newPassword && (
              <div className="mt-2" aria-live="polite">
                <div className="h-1 w-full overflow-hidden rounded-full bg-bg-alt">
                  <div className={`h-full rounded-full transition-all duration-300 ${strength.tone}`} style={{ width: strength.width }} />
                </div>
                <p className="mt-1 text-xs text-text-muted">
                  <span className="font-semibold text-text-main">{strength.label}</span>
                  {strength.hint ? ` — ${strength.hint}` : ""}
                </p>
              </div>
            )}
          </div>
        ))}

        <div className="flex justify-end border-t border-border-subtle pt-5">
          <button type="submit" disabled={isSaving || success} className="btn-primary w-full sm:w-auto">
            {isSaving ? "Updating…" : "Update password"}
          </button>
        </div>
      </form>
    </SettingsSection>
  );
}

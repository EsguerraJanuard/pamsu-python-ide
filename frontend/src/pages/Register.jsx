import { useState } from "react";
import { useNavigate } from "react-router-dom";

const SCHOOL_EMAIL_DOMAIN = "@pampangastateu.edu.ph";
const SCHOOL_ID_PATTERN = /^\d{10}$/;
const SCHOOL_EMAIL_PATTERN =
  /^[^\s@]+@pampangastateu\.edu\.ph$/i;

function getPasswordStrength(password) {
  if (!password) {
    return null;
  }

  let score = 0;

  if (password.length >= 8) {
    score += 1;
  }

  if (/[A-Z]/.test(password)) {
    score += 1;
  }

  if (/[0-9]/.test(password)) {
    score += 1;
  }

  if (/[^A-Za-z0-9]/.test(password)) {
    score += 1;
  }

  if (score <= 1) {
    return {
      label: "Weak — use at least 8 characters",
      color: "#ef4444",
      width: "25%",
    };
  }

  if (score === 2) {
    return {
      label: "Fair — add uppercase letters, numbers, or symbols",
      color: "#f59e0b",
      width: "50%",
    };
  }

  if (score === 3) {
    return {
      label: "Good — one more requirement can strengthen it",
      color: "#3b82f6",
      width: "75%",
    };
  }

  return {
    label: "Strong password",
    color: "#22c55e",
    width: "100%",
  };
}

function validateSchoolEmail(email) {
  return SCHOOL_EMAIL_PATTERN.test(email.trim());
}

function validateFullName(name) {
  return name.trim().length >= 3;
}

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    fullName: "",
    schoolId: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("error");

  const passwordStrength = getPasswordStrength(form.password);

  const inputWrapClass =
    "flex items-center gap-2.5 rounded-lg border border-white/[0.08] bg-[#1a1d27] px-3 py-2.5 transition-colors duration-200 focus-within:border-[#3b82f6]/60";

  const inputClass =
    "flex-1 bg-transparent text-sm text-white outline-none placeholder-white/20";

  const updateField = (field, value) => {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }));

    if (message) {
      setMessage("");
    }
  };

  const updateSchoolId = (value) => {
    const digitsOnly = value.replace(/\D/g, "").slice(0, 10);
    updateField("schoolId", digitsOnly);
  };

  const showError = (text) => {
    setMessageType("error");
    setMessage(text);
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const normalizedEmail = form.email.trim().toLowerCase();
    const normalizedName = form.fullName.trim();

    if (!validateFullName(normalizedName)) {
      showError("Enter your complete name.");
      return;
    }

    if (!SCHOOL_ID_PATTERN.test(form.schoolId)) {
      showError("Your school ID must contain exactly 10 digits.");
      return;
    }

    if (!validateSchoolEmail(normalizedEmail)) {
      showError(
        `Use your official university email ending in ${SCHOOL_EMAIL_DOMAIN}.`,
      );
      return;
    }

    if (form.password.length < 8) {
      showError("Your password must contain at least 8 characters.");
      return;
    }

    if (form.password !== form.confirmPassword) {
      showError("The passwords do not match.");
      return;
    }

    if (!acknowledged) {
      showError(
        "Please read and acknowledge the data collection notice.",
      );
      return;
    }

    /*
     * Backend integration will be added after the OTP API contract
     * and centralized frontend API client are completed.
     *
     * Planned flow:
     *
     * 1. Request an OTP for the normalized school email.
     * 2. Display the OTP verification step only after the backend
     *    confirms that the code was sent.
     * 3. Verify the OTP.
     * 4. Submit the profile, school ID, and password.
     * 5. Let the backend assign the correct role.
     *
     * Do not send a role value from the frontend.
     */

    setMessageType("info");
    setMessage(
      "The registration form is ready. School-email OTP verification is not connected to the backend yet.",
    );
  };

  return (
    <main className="min-h-screen bg-[#0f1117] px-4 py-10 text-white">
      <style>
        {`
          @keyframes registerFadeUp {
            from {
              opacity: 0;
              transform: translateY(16px);
            }

            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          .register-page-card {
            animation:
              registerFadeUp 500ms
              cubic-bezier(0.25, 0.46, 0.45, 0.94)
              both;
          }

          @media (prefers-reduced-motion: reduce) {
            .register-page-card {
              animation: none;
            }
          }
        `}
      </style>

      <div className="register-page-card mx-auto w-full max-w-[560px]">
        <header className="mb-6">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#3b82f6] font-mono text-xs font-bold">
              &gt;_
            </div>

            <span className="text-sm font-semibold">
              PAMSU Python IDE
            </span>
          </div>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold">
                Create your university account
              </h1>

              <p className="mt-1 text-sm text-white/40">
                Your email will be verified before the account is
                activated.
              </p>
            </div>

            <div
              className="rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-[11px] font-medium text-blue-300"
              aria-label="Registration step"
            >
              Account details
            </div>
          </div>
        </header>

        <section className="mb-5 rounded-xl border border-blue-500/20 bg-blue-500/[0.07] px-4 py-3">
          <p className="text-xs leading-relaxed text-blue-200/80">
            Your account role is assigned securely by the server.
            Verified university users register as students unless
            their email is included in the approved instructor
            allowlist.
          </p>
        </section>

        {message && (
          <div
            role={messageType === "error" ? "alert" : "status"}
            aria-live="polite"
            className={`mb-5 rounded-lg border px-4 py-3 text-sm ${
              messageType === "error"
                ? "border-red-500/20 bg-red-500/10 text-red-300"
                : "border-blue-500/20 bg-blue-500/10 text-blue-300"
            }`}
          >
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="full-name"
              className="mb-1.5 block text-xs font-medium text-white/60"
            >
              Complete name
            </label>

            <div className={inputWrapClass}>
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                className="shrink-0 text-white/30"
                aria-hidden="true"
              >
                <circle
                  cx="7"
                  cy="4.5"
                  r="2.5"
                  stroke="currentColor"
                  strokeWidth="1.2"
                />
                <path
                  d="M1.5 12.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                />
              </svg>

              <input
                id="full-name"
                type="text"
                value={form.fullName}
                onChange={(event) =>
                  updateField("fullName", event.target.value)
                }
                placeholder="Juan Dela Cruz"
                autoComplete="name"
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="school-id"
              className="mb-1.5 block text-xs font-medium text-white/60"
            >
              School ID
            </label>

            <div className={inputWrapClass}>
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                className="shrink-0 text-white/30"
                aria-hidden="true"
              >
                <rect
                  x="1"
                  y="2"
                  width="12"
                  height="10"
                  rx="1.5"
                  stroke="currentColor"
                  strokeWidth="1.2"
                />
                <path
                  d="M4 6h2M4 8.5h6M8 6h2"
                  stroke="currentColor"
                  strokeWidth="1"
                  strokeLinecap="round"
                />
              </svg>

              <input
                id="school-id"
                type="text"
                inputMode="numeric"
                value={form.schoolId}
                onChange={(event) =>
                  updateSchoolId(event.target.value)
                }
                placeholder="0000000000"
                pattern="[0-9]{10}"
                minLength={10}
                maxLength={10}
                autoComplete="off"
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />
            </div>

            <p className="mt-1.5 text-[11px] text-white/30">
              Enter the 10-digit number printed on your school ID.
            </p>
          </div>

          <div>
            <label
              htmlFor="school-email"
              className="mb-1.5 block text-xs font-medium text-white/60"
            >
              University email
            </label>

            <div className={inputWrapClass}>
              <svg
                width="15"
                height="15"
                viewBox="0 0 15 15"
                fill="none"
                className="shrink-0 text-white/30"
                aria-hidden="true"
              >
                <path
                  d="M1 4l6.5 4.5L14 4M1 3h13a.5.5 0 01.5.5v8a.5.5 0 01-.5.5H1a.5.5 0 01-.5-.5v-8A.5.5 0 011 3z"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  strokeLinejoin="round"
                />
              </svg>

              <input
                id="school-email"
                type="email"
                value={form.email}
                onChange={(event) =>
                  updateField("email", event.target.value)
                }
                placeholder={`yourname${SCHOOL_EMAIL_DOMAIN}`}
                autoComplete="email"
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />
            </div>

            <p className="mt-1.5 text-[11px] text-white/30">
              Personal email accounts are not accepted.
            </p>
          </div>

          <div>
            <label
              htmlFor="registration-password"
              className="mb-1.5 block text-xs font-medium text-white/60"
            >
              Password
            </label>

            <div className={inputWrapClass}>
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                className="shrink-0 text-white/30"
                aria-hidden="true"
              >
                <rect
                  x="2"
                  y="6"
                  width="10"
                  height="7"
                  rx="1.5"
                  stroke="currentColor"
                  strokeWidth="1.2"
                />
                <path
                  d="M4.5 6V4.5a2.5 2.5 0 015 0V6"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                />
              </svg>

              <input
                id="registration-password"
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={(event) =>
                  updateField("password", event.target.value)
                }
                placeholder="At least 8 characters"
                autoComplete="new-password"
                minLength={8}
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword((currentValue) => !currentValue)
                }
                className="shrink-0 text-xs text-white/40 transition-colors hover:text-white/70"
                aria-label={
                  showPassword ? "Hide password" : "Show password"
                }
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>

            {passwordStrength && (
              <div className="mt-2">
                <div className="h-1 w-full overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: passwordStrength.width,
                      backgroundColor: passwordStrength.color,
                    }}
                  />
                </div>

                <p
                  className="mt-1 text-[11px]"
                  style={{ color: passwordStrength.color }}
                >
                  Strength: {passwordStrength.label}
                </p>
              </div>
            )}
          </div>

          <div>
            <label
              htmlFor="confirm-password"
              className="mb-1.5 block text-xs font-medium text-white/60"
            >
              Confirm password
            </label>

            <div className={inputWrapClass}>
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                className="shrink-0 text-white/30"
                aria-hidden="true"
              >
                <rect
                  x="2"
                  y="6"
                  width="10"
                  height="7"
                  rx="1.5"
                  stroke="currentColor"
                  strokeWidth="1.2"
                />
                <path
                  d="M4.5 6V4.5a2.5 2.5 0 015 0V6"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                />
              </svg>

              <input
                id="confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                value={form.confirmPassword}
                onChange={(event) =>
                  updateField(
                    "confirmPassword",
                    event.target.value,
                  )
                }
                placeholder="Enter the password again"
                autoComplete="new-password"
                minLength={8}
                required
                className={inputClass}
                style={{ caretColor: "#3b82f6" }}
              />

              <button
                type="button"
                onClick={() =>
                  setShowConfirmPassword(
                    (currentValue) => !currentValue,
                  )
                }
                className="shrink-0 text-xs text-white/40 transition-colors hover:text-white/70"
                aria-label={
                  showConfirmPassword
                    ? "Hide confirmed password"
                    : "Show confirmed password"
                }
              >
                {showConfirmPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <section className="rounded-xl border border-white/[0.08] bg-[#1a1d27] p-4">
            <h2 className="mb-2 text-xs font-semibold text-white">
              Data collection notice
            </h2>

            <p className="mb-3 text-[11px] leading-relaxed text-white/50">
              The platform records limited activity information during
              controlled programming activities to support instructor
              review and system operation.
            </p>

            <ul className="mb-4 list-inside list-disc space-y-1.5 text-[11px] leading-relaxed text-white/40">
              <li>
                Tab switches and activity status may be recorded during
                graded laboratory sessions.
              </li>
              <li>
                Blocked external paste attempts may be counted, but
                clipboard contents are not stored.
              </li>
              <li>
                Submitted code may be checked using AST rules, test
                cases, and Jaccard similarity.
              </li>
              <li>
                The system does not record websites visited, screen
                recordings, webcam data, or every keystroke.
              </li>
              <li>
                Relevant records are available only to authorized
                instructors and system personnel.
              </li>
            </ul>

            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(event) =>
                  setAcknowledged(event.target.checked)
                }
                className="mt-0.5 h-4 w-4 shrink-0 accent-[#3b82f6]"
                required
              />

              <span className="text-[11px] leading-relaxed text-white/50">
                I have read and acknowledge the platform’s data
                collection notice.
              </span>
            </label>
          </section>

          <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-white/40">
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => navigate("/login")}
                className="font-medium text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
              >
                Sign in
              </button>
            </p>

            <button
              type="submit"
              disabled={!acknowledged}
              className="rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#2563eb] px-5 py-2.5 text-sm font-semibold text-white transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-none disabled:bg-white/[0.06] disabled:text-white/25 disabled:hover:translate-y-0 disabled:hover:opacity-100"
            >
              Continue to email verification
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

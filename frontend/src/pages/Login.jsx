import { useState } from "react";
import { useNavigate } from "react-router-dom";

const SCHOOL_EMAIL_DOMAIN = "@pampangastateu.edu.ph";

const features = [
  {
    label: "AST-driven structural feedback",
    color: "#22c55e",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="8" cy="8" r="7" stroke="#22c55e" strokeWidth="1.5" />
        <path
          d="M5 8l2 2 4-4"
          stroke="#22c55e"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    label: "Privacy-conscious behavioral indicators",
    color: "#38bdf8",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="8" cy="8" r="3" stroke="#38bdf8" strokeWidth="1.5" />
        <circle
          cx="8"
          cy="8"
          r="6.5"
          stroke="#38bdf8"
          strokeWidth="1"
          strokeDasharray="2 2"
        />
      </svg>
    ),
  },
  {
    label: "Instructor activity monitoring",
    color: "#a78bfa",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <rect
          x="1"
          y="3"
          width="14"
          height="9"
          rx="1.5"
          stroke="#a78bfa"
          strokeWidth="1.5"
        />
        <path
          d="M5 7h6M5 9.5h4"
          stroke="#a78bfa"
          strokeWidth="1.2"
          strokeLinecap="round"
        />
      </svg>
    ),
  },
  {
    label: "Jaccard similarity review indicators",
    color: "#fbbf24",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M8 2l1.5 3 3.5.5-2.5 2.5.5 3.5L8 10l-3 1.5.5-3.5L3 5.5 6.5 5 8 2z"
          stroke="#fbbf24"
          strokeWidth="1.3"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
];

function isValidSchoolEmail(email) {
  return email.trim().toLowerCase().endsWith(SCHOOL_EMAIL_DOMAIN);
}

export default function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("error");

  const updateFormField = (field, value) => {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }));

    if (message) {
      setMessage("");
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const normalizedEmail = form.email.trim().toLowerCase();

    if (!isValidSchoolEmail(normalizedEmail)) {
      setMessageType("error");
      setMessage(
        `Use your official school email ending in ${SCHOOL_EMAIL_DOMAIN}.`,
      );
      return;
    }

    /*
     * Backend integration will be added after:
     * 1. The centralized API client is implemented.
     * 2. The backend email-based login migration is finalized.
     * 3. The authentication context and protected routes are created.
     *
     * The backend, not this page, will determine whether the account
     * belongs to a student or an allowlisted instructor.
     */
    setMessageType("info");
    setMessage(
      "The login interface is ready, but backend authentication is not connected yet.",
    );
  };

  const handleForgotPassword = () => {
    setMessageType("info");
    setMessage(
      "School-email password recovery will be enabled with the OTP module.",
    );
  };

  return (
    <main className="flex min-h-screen overflow-hidden bg-[#0f1117] text-white">
      <style>
        {`
          @keyframes loginFadeLeft {
            from {
              opacity: 0;
              transform: translateX(-16px);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }

          @keyframes loginFadeUp {
            from {
              opacity: 0;
              transform: translateY(18px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          @keyframes featureFadeIn {
            from {
              opacity: 0;
              transform: translateX(-8px);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }

          @media (prefers-reduced-motion: reduce) {
            .login-animated {
              animation: none !important;
            }
          }
        `}
      </style>

      <section
        className="login-animated hidden w-[52%] flex-col justify-between border-r border-white/[0.06] px-16 py-10 lg:flex"
        style={{
          animation:
            "loginFadeLeft 700ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both",
        }}
        aria-label="Platform introduction"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#3b82f6] font-mono text-xs font-bold text-white">
            &gt;_
          </div>

          <span className="font-semibold tracking-wide text-white">
            PAMSU Python IDE
          </span>
        </div>

        <div className="max-w-md">
          <p className="mb-5 text-xs font-semibold uppercase tracking-[0.2em] text-[#3b82f6]">
            Python Learning Platform
          </p>

          <h1 className="mb-1 text-4xl font-bold leading-tight text-white">
            Code with integrity.
          </h1>

          <h2 className="mb-6 text-4xl font-bold leading-tight text-[#3b82f6]">
            Learn to think.
          </h2>

          <p className="mb-8 text-sm leading-relaxed text-white/50">
            A browser-based Python environment that supports structural
            feedback, safe code execution, personal practice, and
            instructor-guided review.
          </p>

          <ul className="space-y-3">
            {features.map((feature, index) => (
              <li
                key={feature.label}
                className="login-animated flex items-center gap-3 text-sm text-white/70"
                style={{
                  animation: `featureFadeIn 450ms ease ${
                    250 + index * 100
                  }ms both`,
                }}
              >
                <span className="shrink-0">{feature.icon}</span>
                <span>{feature.label}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="font-mono text-xs text-white/25">
          Python 3 · FastAPI · Isolated execution
        </p>
      </section>

      <section className="flex flex-1 items-center justify-center px-6 py-12">
        <div
          className="login-animated w-full max-w-[380px]"
          style={{
            animation:
              "loginFadeUp 650ms cubic-bezier(0.25, 0.46, 0.45, 0.94) 100ms both",
          }}
        >
          <div className="mb-7 text-center">
            <h2 className="text-lg font-semibold text-white">
              Sign in to your workspace
            </h2>

            <p className="mt-1 text-sm text-white/40">
              Use your verified university account
            </p>
          </div>

          {message && (
            <div
              role={messageType === "error" ? "alert" : "status"}
              aria-live="polite"
              className={`mb-4 rounded-lg border px-4 py-3 text-sm ${
                messageType === "error"
                  ? "border-red-500/20 bg-red-500/10 text-red-300"
                  : "border-blue-500/20 bg-blue-500/10 text-blue-300"
              }`}
            >
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="school-email"
                className="mb-1.5 block text-xs font-medium text-white/60"
              >
                School email
              </label>

              <div className="flex items-center gap-2.5 rounded-lg border border-white/[0.08] bg-[#1a1d27] px-3 py-2.5 transition-colors duration-200 focus-within:border-[#3b82f6]/60">
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
                    updateFormField("email", event.target.value)
                  }
                  placeholder={`yourname${SCHOOL_EMAIL_DOMAIN}`}
                  autoComplete="email"
                  required
                  className="flex-1 bg-transparent text-sm text-white outline-none placeholder-white/20"
                  style={{ caretColor: "#3b82f6" }}
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-xs font-medium text-white/60"
              >
                Password
              </label>

              <div className="flex items-center gap-2.5 rounded-lg border border-white/[0.08] bg-[#1a1d27] px-3 py-2.5 transition-colors duration-200 focus-within:border-[#3b82f6]/60">
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
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(event) =>
                    updateFormField("password", event.target.value)
                  }
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  className="flex-1 bg-transparent text-sm text-white outline-none placeholder-white/20"
                  style={{ caretColor: "#3b82f6" }}
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword((currentValue) => !currentValue)
                  }
                  className="shrink-0 text-white/30 transition-colors hover:text-white/70"
                  aria-label={
                    showPassword ? "Hide password" : "Show password"
                  }
                >
                  {showPassword ? (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z"
                        stroke="currentColor"
                        strokeWidth="1.2"
                      />
                      <circle
                        cx="8"
                        cy="8"
                        r="1.5"
                        stroke="currentColor"
                        strokeWidth="1.2"
                      />
                      <path
                        d="M3 3l10 10"
                        stroke="currentColor"
                        strokeWidth="1.2"
                        strokeLinecap="round"
                      />
                    </svg>
                  ) : (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z"
                        stroke="currentColor"
                        strokeWidth="1.2"
                      />
                      <circle
                        cx="8"
                        cy="8"
                        r="1.5"
                        stroke="currentColor"
                        strokeWidth="1.2"
                      />
                    </svg>
                  )}
                </button>
              </div>

              <div className="mt-2 text-right">
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  className="text-xs text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
                >
                  Forgot password?
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#2563eb] py-2.5 text-sm font-semibold text-white transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98]"
            >
              Sign in
            </button>

            <p className="text-center text-xs text-white/40">
              Need a verified university account?{" "}
              <button
                type="button"
                onClick={() => navigate("/register")}
                className="font-medium text-[#3b82f6] transition-colors hover:text-[#60a5fa]"
              >
                Create one
              </button>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}

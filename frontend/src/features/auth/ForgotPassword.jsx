import { useNavigate } from "react-router-dom";
import { ThemeToggle } from "../theme/ThemeToggle";

export default function ForgotPassword() {
  const navigate = useNavigate();

  return (
    <main className="flex min-h-screen items-center justify-center bg-bg-base text-text-main overflow-hidden p-6 relative">
      {/* Background Grid & Glows */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
      <div className="absolute top-0 right-0 -z-10 h-[500px] w-[500px] translate-x-1/3 -translate-y-1/4 rounded-full bg-emerald-500/10 blur-[120px]" />
      <div className="absolute bottom-0 left-0 -z-10 h-[500px] w-[500px] -translate-x-1/3 translate-y-1/4 rounded-full bg-cyan-500/10 blur-[120px]" />

      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <div className="relative z-10 w-full max-w-[420px] rounded-2xl border border-border-subtle bg-bg-glass/70 backdrop-blur-2xl p-8 shadow-[0_0_40px_-10px_rgba(16,185,129,0.15)] animate-page-fade">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </div>
          <h2 className="text-xl font-bold text-text-main">
            Account Recovery
          </h2>
          <p className="mt-3 text-sm text-text-muted leading-relaxed">
            Automated password resets are currently disabled for security reasons. 
            Please contact your instructor or the university IT department to request a password reset.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/login")}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-border-subtle bg-bg-glass py-3 text-sm font-semibold text-text-main transition-colors hover:bg-bg-glass-hover"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Back to Login
        </button>
      </div>
    </main>
  );
}

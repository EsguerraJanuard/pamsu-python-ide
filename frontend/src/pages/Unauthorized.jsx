import { useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';

export const Unauthorized = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-bg-glass p-6 text-center text-text-main selection:bg-psu-maroon selection:text-white">
      <div className="max-w-md space-y-6 rounded-3xl border border-red-900/50 bg-bg-base/90 p-10 shadow-2xl backdrop-blur-md animate-fade-in-up">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-red-500/10 text-red-500 border border-red-500/20 shadow-inner">
          <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h1 className="text-3xl font-black tracking-tight text-text-main mb-2">Access Denied</h1>
          <p className="text-sm leading-relaxed text-text-muted">
            You do not have the security permissions to view this workspace. This area is restricted to authorized role personnel only.
          </p>
        </div>
        <div className="flex flex-col gap-3 pt-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex w-full items-center justify-center rounded-xl border border-border-strong bg-bg-glass px-4 py-3 text-sm font-bold text-text-muted transition-all hover:text-text-main hover:bg-bg-glass-hover hover:border-border-subtle hover:-translate-y-0.5"
          >
            Return to Previous Page
          </button>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate('/login');
            }}
            className="inline-flex w-full items-center justify-center rounded-xl bg-psu-maroon px-4 py-3 text-sm font-bold text-white shadow-lg shadow-psu-maroon/20 transition-all hover:scale-[1.02] hover:shadow-psu-maroon/40"
          >
            Switch Account (Log In)
          </button>
        </div>
      </div>
    </main>
  );
};

export default Unauthorized;

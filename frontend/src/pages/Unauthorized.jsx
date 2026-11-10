import { Link, useNavigate } from 'react-router-dom';
import { useAuth, homePathForRole } from '../features/auth/AuthContext';

export const Unauthorized = () => {
  const navigate = useNavigate();
  const { isAuthenticated, role, logout } = useAuth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-bg-base p-6 text-text-main">
      <div className="card w-full max-w-md p-8 text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-psu-red/10 text-psu-red">
          <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 11V7a5 5 0 0 1 10 0v4M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z" />
          </svg>
        </div>
        <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">Access restricted</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">You don&apos;t have access to this page</h1>
        <p className="mt-2 text-sm leading-relaxed text-text-muted">
          This area is available to a different account type. If you believe this is a mistake, contact your
          instructor or the MIS office.
        </p>
        <div className="mt-6 flex flex-col gap-2">
          {isAuthenticated ? (
            <>
              <Link to={homePathForRole(role)} className="btn-primary w-full">
                Go to my dashboard
              </Link>
              <button
                type="button"
                onClick={() => {
                  logout();
                  navigate('/login', { replace: true });
                }}
                className="btn-secondary w-full"
              >
                Sign in with a different account
              </button>
            </>
          ) : (
            <Link to="/login" className="btn-primary w-full">
              Go to sign in
            </Link>
          )}
        </div>
      </div>
    </main>
  );
};

export default Unauthorized;

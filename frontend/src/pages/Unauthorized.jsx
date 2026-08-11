import { useNavigate } from 'react-router-dom';

export const Unauthorized = () => {
  const navigate = useNavigate();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-bg-glass p-6 text-center text-slate-100">
      <div className="max-w-md space-y-6 rounded-2xl border border-red-900/50 bg-bg-glass/80 p-8 shadow-2xl backdrop-blur">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 text-red-400">
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-text-main">Access Denied</h1>
        <p className="text-sm leading-relaxed text-text-muted">
          You do not have the required security permissions to view this workspace. This area is restricted to authorized role personnel only.
        </p>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-text-main transition-colors hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        >
          Return to Previous Page
        </button>
      </div>
    </main>
  );
};

export default Unauthorized;
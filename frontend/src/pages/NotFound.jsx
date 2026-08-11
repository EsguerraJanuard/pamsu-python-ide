import { Link } from 'react-router-dom';

export const NotFound = () => {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-bg-glass p-6 text-center text-slate-100">
      <div className="max-w-md space-y-6 rounded-2xl border border-border-subtle bg-bg-glass/80 p-8 shadow-2xl">
        <p className="text-sm font-semibold uppercase tracking-widest text-blue-500">Error 404</p>
        <h1 className="text-3xl font-extrabold tracking-tight text-text-main">Page Not Found</h1>
        <p className="text-sm leading-relaxed text-text-muted">
          We couldn&apos;t find the workspace or classroom page you are looking for. It may have been moved, archived, or deleted.
        </p>
        <Link
          to="/login"
          className="inline-flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-text-main transition-colors hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        >
          Return to Login
        </Link>
      </div>
    </main>
  );
};

export default NotFound;
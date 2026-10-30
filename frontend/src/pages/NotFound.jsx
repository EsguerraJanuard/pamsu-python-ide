import { Link } from 'react-router-dom';
import { useAuth, homePathForRole } from '../features/auth/AuthContext';

export const NotFound = () => {
  const { isAuthenticated, role } = useAuth();
  const destination = isAuthenticated ? homePathForRole(role) : '/login';

  return (
    <main className="flex min-h-screen items-center justify-center bg-bg-base p-6 text-text-main">
      <div className="card w-full max-w-md p-8 text-center">
        <img src="/school_logo.png" alt="Pampanga State University logo" className="mx-auto mb-5 h-14 w-14 object-contain" />
        <p className="text-[11px] font-semibold uppercase tracking-widest text-text-brand">Error 404</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">Page not found</h1>
        <p className="mt-2 text-sm leading-relaxed text-text-muted">
          The page you are looking for does not exist. It may have been moved, or the link may be incorrect.
        </p>
        <Link to={destination} className="btn-primary mt-6 w-full">
          {isAuthenticated ? 'Go to my dashboard' : 'Go to sign in'}
        </Link>
      </div>
    </main>
  );
};

export default NotFound;

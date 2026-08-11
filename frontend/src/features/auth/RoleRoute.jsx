import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext';

export const RoleRoute = ({ allowedRole }) => {
  const { role, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-glass text-text-main" role="status" aria-live="polite">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm font-medium animate-pulse">Checking permissions...</p>
        </div>
      </div>
    );
  }

  if (role !== allowedRole) {
    // If a student tries to access instructor pages (or vice versa), send to unauthorized
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

export default RoleRoute;
import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

const INSTRUCTOR_NAV_ITEMS = [
  { name: 'Overview', path: '/dashboard/instructor' },
  { name: 'Class Management', path: '/instructor/classes' },
  { name: 'Activity Authoring', path: '/instructor/activities' },
  { name: 'Grading Bench', path: '/instructor/submissions' },
  { name: 'Live Monitoring', path: '/instructor/monitoring' },
  { name: 'Settings', path: '/settings' },
];

export const InstructorLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100 lg:flex-row">
      {/* Mobile Navigation Bar */}
      <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900 px-4 lg:hidden">
        <span className="text-lg font-bold tracking-tight text-emerald-400">PAMSU Instructor</span>
        <button
          type="button"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          aria-label="Toggle navigation menu"
          aria-expanded={isMobileMenuOpen}
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={isMobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
        </button>
      </header>

      {/* Sidebar Navigation */}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-800 bg-slate-900 transition-transform duration-200 lg:static lg:translate-x-0 ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-16 items-center border-b border-slate-800 px-6">
          <span className="text-lg font-bold tracking-tight text-emerald-400">PAMSU IDE</span>
          <span className="ml-2 rounded bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-400">Faculty</span>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Instructor main navigation">
          {INSTRUCTOR_NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              {item.name}
            </NavLink>
          ))}
        </nav>

        {/* Faculty Footer Controls */}
        <div className="border-t border-slate-800 p-4">
          <div className="mb-3 truncate px-2 text-xs text-slate-400">
            Faculty ID: <strong className="block truncate font-medium text-slate-200">{user?.email || 'Instructor Account'}</strong>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center justify-center rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10 hover:text-red-300"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-x-hidden">
        <div className="min-h-full p-4 md:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default InstructorLayout;
/**
 * NewsMind AI - App Layout with navigation
 */

import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Newspaper,
  Settings,
  Clock,
  User,
  Sparkles,
} from 'lucide-react';
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/reports', label: 'Reports', icon: Newspaper },
  { to: '/preferences', label: 'Preferences', icon: Settings },
  { to: '/schedule', label: 'Schedule', icon: Clock },
  { to: '/profile', label: 'Profile', icon: User },
];

export default function Layout({ children }) {
  const location = useLocation();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 flex">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <Link to="/dashboard" className="flex items-center gap-2 text-brand-400 font-bold text-lg">
            <Sparkles className="w-6 h-6" />
            NewsMind AI
          </Link>
          {user && (
            <p className="text-slate-400 text-sm mt-2 truncate">{user.name}</p>
          )}
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = location.pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                  active
                    ? 'bg-brand-500/10 text-brand-400'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Icon className="w-5 h-5" />
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

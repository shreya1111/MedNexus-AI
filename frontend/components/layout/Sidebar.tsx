'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, FileText, Calendar, User, Settings,
  Users, BarChart3, Brain, LogOut, Activity, ChevronLeft
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/lib/api';
import { useRouter } from 'next/navigation';

const patientNav = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/records', label: 'Medical Records', icon: FileText },
  { href: '/dashboard/appointments', label: 'Appointments', icon: Calendar },
  { href: '/dashboard/profile', label: 'My Profile', icon: User },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

const doctorNav = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/patients', label: 'Patients', icon: Users },
  { href: '/dashboard/appointments', label: 'Appointments', icon: Calendar },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

const adminNav = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/admin', label: 'User Management', icon: Users },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const navItems = user?.role === 'admin' ? adminNav : user?.role === 'doctor' ? doctorNav : patientNav;

  const handleLogout = async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      try { await authApi.logout(refreshToken); } catch {}
    }
    logout();
    router.push('/login');
  };

  return (
    <aside className={cn(
      'flex h-screen flex-col border-r border-gray-100 bg-white transition-all duration-300',
      collapsed ? 'w-16' : 'w-64'
    )}>
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-gray-100">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-gray-900">MedNexus AI</span>
          </div>
        )}
        {collapsed && <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600"><Activity className="h-5 w-5 text-white" /></div>}
        {!collapsed && (
          <button onClick={onToggle} className="rounded-lg p-1 hover:bg-gray-100 text-gray-400">
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                active ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                collapsed && 'justify-center px-2'
              )}
              title={collapsed ? label : undefined}
            >
              <Icon className={cn('h-5 w-5 shrink-0', active ? 'text-blue-600' : 'text-gray-400')} />
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}

        {/* AI Assistant link */}
        <Link
          href="/dashboard/ai"
          className={cn(
            'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
            pathname === '/dashboard/ai' ? 'bg-purple-50 text-purple-700 font-medium' : 'text-gray-600 hover:bg-gray-50',
            collapsed && 'justify-center px-2'
          )}
          title={collapsed ? 'AI Assistant' : undefined}
        >
          <Brain className={cn('h-5 w-5 shrink-0', pathname === '/dashboard/ai' ? 'text-purple-600' : 'text-gray-400')} />
          {!collapsed && <span>AI Assistant</span>}
        </Link>
      </nav>

      {/* User + logout */}
      <div className="border-t border-gray-100 p-2">
        {!collapsed && user && (
          <div className="mb-2 flex items-center gap-3 rounded-lg px-3 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-semibold">
              {user.firstName[0]}{user.lastName[0]}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-gray-900">{user.fullName || `${user.firstName} ${user.lastName}`}</p>
              <p className="truncate text-xs text-gray-500 capitalize">{user.role}</p>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={cn(
            'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors',
            collapsed && 'justify-center px-2'
          )}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}

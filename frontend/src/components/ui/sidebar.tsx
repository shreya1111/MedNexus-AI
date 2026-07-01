import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  MessageSquare,
  Search,
  FileText,
  FolderOpen,
  User,
  Settings,
  Shield,
} from 'lucide-react'

interface SidebarProps {
  variant?: 'default' | 'chat' | 'admin'
}

export default function Sidebar({ variant = 'default' }: SidebarProps) {
  const location = useLocation()

  const defaultNavItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Chat', href: '/chat', icon: MessageSquare },
    { name: 'Search', href: '/search', icon: Search },
    { name: 'Reports', href: '/reports', icon: FileText },
    { name: 'Documents', href: '/documents', icon: FolderOpen },
    { name: 'Profile', href: '/profile', icon: User },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  const adminNavItems = [
    { name: 'Admin Dashboard', href: '/admin', icon: Shield },
    { name: 'Users', href: '/admin/users', icon: User },
    { name: 'System Health', href: '/admin/health', icon: LayoutDashboard },
    { name: 'Settings', href: '/admin/settings', icon: Settings },
  ]

  const chatNavItems = [
    { name: 'New Chat', href: '/chat', icon: MessageSquare },
  ]

  const navItems = variant === 'admin' ? adminNavItems : variant === 'chat' ? chatNavItems : defaultNavItems

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-surface-glass backdrop-blur-glass border-r border-border hidden lg:block">
      {/* Logo */}
      <div className="flex items-center gap-2 p-lg border-b border-border">
        <div className="h-8 w-8 rounded-lg bg-primary-container" />
        <span className="text-headline-md font-bold text-primary-container">
          MedNexus AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon
          
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg text-body-md font-medium transition-all',
                'hover:bg-surface-container-high hover:translate-x-1',
                isActive
                  ? 'bg-surface-container-high text-primary-container border-l-4 border-primary-container translate-x-1'
                  : 'text-foreground'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Chat Sidebar: Conversation List */}
      {variant === 'chat' && (
        <div className="p-4 border-t border-border">
          <h3 className="text-label-caps text-muted-foreground mb-2">
            Recent Conversations
          </h3>
          {/* Placeholder for conversation list */}
          <div className="space-y-2">
            <div className="p-3 rounded-lg bg-surface-container hover:bg-surface-container-high cursor-pointer transition-colors">
              <p className="text-body-sm text-foreground truncate">
                Previous conversation...
              </p>
              <span className="text-label-caps text-muted-foreground">
                2 hours ago
              </span>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}

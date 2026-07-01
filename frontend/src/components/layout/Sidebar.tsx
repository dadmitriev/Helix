'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Users, FlaskConical, FileText, BarChart3, ClipboardList,
  LogOut, Activity, Shield, UserCircle, Stethoscope
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { clearAuth, getStoredUser } from '@/lib/auth'
import api from '@/lib/api'
import { toast } from 'sonner'

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
}

const DOCTOR_NAV: NavItem[] = [
  { href: '/doctor/orders', label: 'Направления', icon: ClipboardList },
  { href: '/doctor/patients', label: 'Пациенты', icon: Users },
]

const LAB_NAV: NavItem[] = [
  { href: '/lab/queue', label: 'Очередь', icon: FlaskConical },
]

const PATIENT_NAV: NavItem[] = [
  { href: '/patient', label: 'Мои данные', icon: UserCircle },
]

const ADMIN_NAV: NavItem[] = [
  { href: '/admin/dashboard', label: 'Статистика', icon: BarChart3 },
  { href: '/admin/users', label: 'Пользователи', icon: Users },
  { href: '/admin/audit', label: 'Аудит', icon: Shield },
]

const ROLE_NAV = {
  DOCTOR: DOCTOR_NAV,
  LABORATORIAN: LAB_NAV,
  PATIENT: PATIENT_NAV,
  ADMIN: ADMIN_NAV,
}

const ROLE_LABELS = {
  DOCTOR: 'Врач',
  LABORATORIAN: 'Лаборант',
  PATIENT: 'Пациент',
  ADMIN: 'Администратор',
}

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const user = getStoredUser()

  const navItems = user ? ROLE_NAV[user.role] ?? [] : []

  async function handleLogout() {
    try {
      await api.post('/auth/logout')
    } catch { /* ignore */ }
    clearAuth()
    router.push('/login')
    toast.success('Вы вышли из системы')
  }

  return (
    <aside className="flex flex-col w-60 min-h-screen bg-white border-r border-gray-200 shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-100">
        <div className="w-8 h-8 rounded-lg bg-[#4A6FA5] flex items-center justify-center">
          <Activity className="w-4 h-4 text-white" />
        </div>
        <span className="text-lg font-bold text-gray-900">Helix</span>
      </div>

      {/* User info */}
      {user && (
        <div className="px-4 py-3 border-b border-gray-100">
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg bg-[#F8F9FA]">
            <div className="w-8 h-8 rounded-full bg-[#4A6FA5]/20 flex items-center justify-center">
              <Stethoscope className="w-4 h-4 text-[#4A6FA5]" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.full_name}</p>
              <p className="text-xs text-gray-500">{ROLE_LABELS[user.role]}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-[#4A6FA5] text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-gray-100">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-700 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Выйти
        </button>
      </div>
    </aside>
  )
}

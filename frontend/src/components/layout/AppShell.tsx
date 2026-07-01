'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from './Sidebar'
import { getStoredUser } from '@/lib/auth'
import { UserRole } from '@/types'

interface AppShellProps {
  children: React.ReactNode
  requiredRole?: UserRole | UserRole[]
}

export function AppShell({ children, requiredRole }: AppShellProps) {
  const router = useRouter()

  useEffect(() => {
    const user = getStoredUser()
    if (!user) {
      router.replace('/login')
      return
    }
    if (requiredRole) {
      const allowed = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
      if (!allowed.includes(user.role)) {
        router.replace('/login')
      }
    }
  }, [router, requiredRole])

  return (
    <div className="flex min-h-screen bg-[#F8F9FA]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}

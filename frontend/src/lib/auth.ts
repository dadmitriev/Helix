import { User, UserRole } from '@/types'

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

export function storeAuth(token: string, user: User) {
  localStorage.setItem('access_token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

export function roleHomePath(role: UserRole): string {
  switch (role) {
    case 'DOCTOR': return '/doctor/orders'
    case 'LABORATORIAN': return '/lab/queue'
    case 'PATIENT': return '/patient'
    case 'ADMIN': return '/admin/dashboard'
  }
}

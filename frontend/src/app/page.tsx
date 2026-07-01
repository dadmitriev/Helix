'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getStoredUser } from '@/lib/auth'
import { roleHomePath } from '@/lib/auth'

export default function Home() {
  const router = useRouter()
  useEffect(() => {
    const user = getStoredUser()
    if (user) {
      router.replace(roleHomePath(user.role))
    } else {
      router.replace('/login')
    }
  }, [router])
  return null
}

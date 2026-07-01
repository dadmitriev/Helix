'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { Activity, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import api from '@/lib/api'
import { storeAuth, roleHomePath } from '@/lib/auth'
import { TokenResponse } from '@/types'
import { toast } from 'sonner'

interface LoginForm {
  email: string
  password: string
}

export default function LoginPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>()

  async function onSubmit(data: LoginForm) {
    setLoading(true)
    try {
      const res = await api.post<TokenResponse>('/auth/login', data)
      storeAuth(res.data.access_token, res.data.user)
      toast.success(`Добро пожаловать, ${res.data.user.first_name}!`)
      router.push(roleHomePath(res.data.user.role))
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg || 'Неверный email или пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-[#4A6FA5] flex items-center justify-center shadow-lg mb-4">
            <Activity className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Helix</h1>
          <p className="text-gray-500 text-sm mt-1">Система анализа риска диабета</p>
        </div>

        <Card className="shadow-sm border-0">
          <CardHeader className="pb-4">
            <h2 className="text-lg font-semibold text-gray-900">Вход в систему</h2>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="doctor@clinic.com"
                  autoComplete="email"
                  className="h-10 rounded-lg"
                  {...register('email', {
                    required: 'Введите email',
                    pattern: { value: /\S+@\S+\.\S+/, message: 'Некорректный email' },
                  })}
                />
                {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Пароль</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    className="h-10 rounded-lg pr-10"
                    {...register('password', { required: 'Введите пароль' })}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-10 bg-[#4A6FA5] hover:bg-[#3d5d8f] text-white rounded-lg font-medium"
              >
                {loading ? 'Вход...' : 'Войти'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-gray-400 mt-6">
          Система поддержки клинических решений. Только для авторизованного персонала.
        </p>
      </div>
    </div>
  )
}

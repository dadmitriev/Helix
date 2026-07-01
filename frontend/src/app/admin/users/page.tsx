'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserPlus, ToggleLeft, ToggleRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/lib/api'
import { User, UserRole, PaginatedResponse } from '@/types'
import { formatDateTime } from '@/lib/utils'
import { toast } from 'sonner'

const ROLE_LABELS: Record<UserRole, string> = {
  ADMIN: 'Администратор',
  DOCTOR: 'Врач',
  LABORATORIAN: 'Лаборант',
  PATIENT: 'Пациент',
}

const ROLE_COLORS: Record<UserRole, string> = {
  ADMIN: 'bg-purple-100 text-purple-700',
  DOCTOR: 'bg-blue-100 text-blue-700',
  LABORATORIAN: 'bg-teal-100 text-teal-700',
  PATIENT: 'bg-gray-100 text-gray-700',
}

interface CreateForm {
  email: string
  password: string
  first_name: string
  last_name: string
  middle_name: string
  role: UserRole
  date_of_birth: string
  gender: string
}

function emptyForm(): CreateForm {
  return { email: '', password: '', first_name: '', last_name: '', middle_name: '', role: 'DOCTOR', date_of_birth: '', gender: 'MALE' }
}

export default function AdminUsersPage() {
  const qc = useQueryClient()
  const [roleFilter, setRoleFilter] = useState<UserRole | 'ALL'>('ALL')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<CreateForm>(emptyForm())

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', roleFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), size: '20' })
      if (roleFilter !== 'ALL') params.set('role', roleFilter)
      const res = await api.get<PaginatedResponse<User>>(`/users?${params}`)
      return res.data
    },
  })

  const createMutation = useMutation({
    mutationFn: (body: object) => api.post('/users', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      setShowCreate(false)
      setForm(emptyForm())
      toast.success('Пользователь создан')
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      if (typeof detail === 'string') {
        toast.error(detail)
      } else if (Array.isArray(detail)) {
        const msg = (detail as { msg?: string }[])[0]?.msg ?? 'Ошибка валидации'
        toast.error(msg)
      } else {
        toast.error('Ошибка при создании пользователя')
      }
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ userId }: { userId: string; active: boolean }) =>
      api.patch(`/users/${userId}/toggle-active`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      toast.success('Статус обновлён')
    },
    onError: () => toast.error('Ошибка при обновлении'),
  })

  function handleCreate() {
    if (!form.email || !form.password || !form.first_name || !form.last_name) {
      return toast.error('Заполните обязательные поля')
    }
    if (form.role === 'PATIENT' && !form.date_of_birth) {
      return toast.error('Для пациента укажите дату рождения')
    }
    createMutation.mutate({
      email: form.email,
      password: form.password,
      role: form.role,
      first_name: form.first_name,
      last_name: form.last_name,
      middle_name: form.middle_name || null,
      ...(form.role === 'PATIENT' && {
        date_of_birth: form.date_of_birth,
        gender: form.gender || 'MALE',
      }),
    })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Пользователи</h1>
          <p className="text-sm text-gray-500 mt-0.5">Всего: {data?.total ?? 0}</p>
        </div>
        <Button onClick={() => setShowCreate(p => !p)} className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg gap-2">
          <UserPlus className="w-4 h-4" />
          Создать пользователя
        </Button>
      </div>

      {showCreate && (
        <Card className="border-0 shadow-sm mb-4 p-4">
          <h3 className="font-semibold text-gray-800 mb-3">Новый пользователь</h3>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Фамилия *</Label>
              <Input value={form.last_name} onChange={e => setForm(p => ({ ...p, last_name: e.target.value }))} className="rounded-lg h-9" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Имя *</Label>
              <Input value={form.first_name} onChange={e => setForm(p => ({ ...p, first_name: e.target.value }))} className="rounded-lg h-9" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Отчество</Label>
              <Input value={form.middle_name} onChange={e => setForm(p => ({ ...p, middle_name: e.target.value }))} className="rounded-lg h-9" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Роль *</Label>
              <Select value={form.role} onValueChange={v => { if (v) setForm(p => ({ ...p, role: v as UserRole })) }}>
                <SelectTrigger className="rounded-lg h-9"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(Object.entries(ROLE_LABELS) as [UserRole, string][]).map(([r, l]) => (
                    <SelectItem key={r} value={r}>{l}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Email *</Label>
              <Input type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} className="rounded-lg h-9" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Пароль *</Label>
              <Input type="password" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} className="rounded-lg h-9" />
            </div>
            {form.role === 'PATIENT' && (
              <>
                <div className="space-y-1.5">
                  <Label className="text-xs">Дата рождения *</Label>
                  <Input type="date" value={form.date_of_birth} onChange={e => setForm(p => ({ ...p, date_of_birth: e.target.value }))} className="rounded-lg h-9" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Пол *</Label>
                  <Select value={form.gender} onValueChange={v => { if (v) setForm(p => ({ ...p, gender: v })) }}>
                    <SelectTrigger className="rounded-lg h-9"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MALE">Мужской</SelectItem>
                      <SelectItem value="FEMALE">Женский</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" size="sm" className="rounded-lg" onClick={() => setShowCreate(false)}>Отмена</Button>
            <Button size="sm" className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg" disabled={createMutation.isPending} onClick={handleCreate}>
              {createMutation.isPending ? 'Создание...' : 'Создать'}
            </Button>
          </div>
        </Card>
      )}

      {/* Role filter */}
      <div className="flex gap-2 mb-4">
        {(['ALL', 'DOCTOR', 'LABORATORIAN', 'PATIENT', 'ADMIN'] as const).map(r => (
          <button
            key={r}
            onClick={() => { setRoleFilter(r); setPage(1) }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              roleFilter === r ? 'bg-[#4A6FA5] text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {r === 'ALL' ? 'Все' : ROLE_LABELS[r]}
          </button>
        ))}
      </div>

      <Card className="border-0 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">ФИО</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Роль</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Создан</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Статус</th>
                <th className="w-12" />
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={6} className="text-center py-12 text-gray-400">Загрузка...</td></tr>}
              {!isLoading && data?.items.length === 0 && <tr><td colSpan={6} className="text-center py-12 text-gray-400">Пользователи не найдены</td></tr>}
              {data?.items.map(u => (
                <tr key={u.id} className="border-b border-gray-50 hover:bg-[#F8F9FA] transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_COLORS[u.role]}`}>
                      {ROLE_LABELS[u.role]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{formatDateTime(u.created_at)}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                      {u.is_active ? 'Активен' : 'Заблокирован'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleMutation.mutate({ userId: u.id, active: !u.is_active })}
                      disabled={toggleMutation.isPending}
                      className="text-gray-400 hover:text-[#4A6FA5] transition-colors"
                      title={u.is_active ? 'Заблокировать' : 'Разблокировать'}
                    >
                      {u.is_active
                        ? <ToggleRight className="w-5 h-5 text-green-500" />
                        : <ToggleLeft className="w-5 h-5 text-gray-400" />
                      }
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-sm text-gray-500">Страница {page} из {data.pages}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page === 1} className="rounded-lg">Назад</Button>
              <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= data.pages} className="rounded-lg">Вперёд</Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}

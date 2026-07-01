'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/lib/api'
import { AuditLog, PaginatedResponse } from '@/types'
import { formatDateTime } from '@/lib/utils'

const ENTITY_TYPES = ['user', 'patient', 'lab_order', 'conclusion', 'prediction']
const ACTION_FILTER_OPTIONS = [
  { value: 'ALL', label: 'Все действия' },
  { value: 'login', label: 'Вход' },
  { value: 'logout', label: 'Выход' },
  { value: 'create', label: 'Создание' },
  { value: 'update', label: 'Обновление' },
  { value: 'delete', label: 'Удаление' },
]

export default function AdminAuditPage() {
  const [entityType, setEntityType] = useState<string>('ALL')
  const [actionFilter, setActionFilter] = useState<string>('ALL')
  const [userId, setUserId] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', entityType, actionFilter, userId, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), size: '30' })
      if (entityType !== 'ALL') params.set('entity_type', entityType)
      if (actionFilter !== 'ALL') params.set('action', actionFilter)
      if (userId.trim()) params.set('user_id', userId.trim())
      const res = await api.get<PaginatedResponse<AuditLog>>(`/admin/audit-logs?${params}`)
      return res.data
    },
  })

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Журнал аудита</h1>
        <p className="text-sm text-gray-500 mt-0.5">Всего записей: {data?.total ?? 0}</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <Select value={entityType} onValueChange={v => { setEntityType(v ?? 'ALL'); setPage(1) }}>
          <SelectTrigger className="rounded-lg h-9 w-44">
            <SelectValue placeholder="Тип сущности" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Все типы</SelectItem>
            {ENTITY_TYPES.map(t => (
              <SelectItem key={t} value={t}>{t}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={actionFilter} onValueChange={v => { setActionFilter(v ?? 'ALL'); setPage(1) }}>
          <SelectTrigger className="rounded-lg h-9 w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ACTION_FILTER_OPTIONS.map(o => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          placeholder="UUID пользователя..."
          value={userId}
          onChange={e => { setUserId(e.target.value); setPage(1) }}
          className="rounded-lg h-9 w-64 font-mono text-xs"
        />
      </div>

      <Card className="border-0 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Время</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Действие</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Тип</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">ID сущности</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Пользователь</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">IP</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={6} className="text-center py-12 text-gray-400">Загрузка...</td></tr>}
              {!isLoading && data?.items.length === 0 && <tr><td colSpan={6} className="text-center py-12 text-gray-400">Нет записей</td></tr>}
              {data?.items.map(log => (
                <tr key={log.id} className="border-b border-gray-50 hover:bg-[#F8F9FA] transition-colors">
                  <td className="px-4 py-2.5 text-gray-500 whitespace-nowrap">{formatDateTime(log.timestamp)}</td>
                  <td className="px-4 py-2.5">
                    <span className="font-mono bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded text-xs">{log.action}</span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-600">{log.entity_type ?? '—'}</td>
                  <td className="px-4 py-2.5 font-mono text-gray-400">{log.entity_id ? log.entity_id.slice(0, 8) + '…' : '—'}</td>
                  <td className="px-4 py-2.5 font-mono text-gray-400">{log.user_id ? log.user_id.slice(0, 8) + '…' : '—'}</td>
                  <td className="px-4 py-2.5 text-gray-400">{log.ip_address ?? '—'}</td>
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

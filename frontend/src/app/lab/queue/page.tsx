'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, PlayCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import api from '@/lib/api'
import { LabOrder, LabOrderStatus, PaginatedResponse } from '@/types'
import { StatusBadge, PriorityBadge } from '@/components/shared/StatusBadge'
import { formatDateTime, PANEL_LABELS } from '@/lib/utils'
import { toast } from 'sonner'

export default function LabQueuePage() {
  const [status, setStatus] = useState<LabOrderStatus | 'ALL'>('ORDERED')
  const [page, setPage] = useState(1)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['lab-queue', status, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), size: '20' })
      if (status !== 'ALL') params.set('status', status)
      const res = await api.get<PaginatedResponse<LabOrder>>(`/lab-orders?${params}`)
      return res.data
    },
  })

  const acceptMutation = useMutation({
    mutationFn: (orderId: string) => api.post(`/lab-orders/${orderId}/accept`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lab-queue'] })
      toast.success('Направление принято в работу')
    },
    onError: () => toast.error('Ошибка при принятии направления'),
  })

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Очередь анализов</h1>
        <p className="text-sm text-gray-500 mt-0.5">Всего: {data?.total ?? 0}</p>
      </div>

      {/* Status filter */}
      <div className="flex gap-2 mb-4">
        {(['ORDERED', 'IN_PROGRESS', 'ALL'] as const).map((s) => (
          <button
            key={s}
            onClick={() => { setStatus(s); setPage(1) }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              status === s
                ? 'bg-[#4A6FA5] text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {s === 'ALL' ? 'Все' : s === 'ORDERED' ? 'Назначено' : 'В работе'}
          </button>
        ))}
      </div>

      <Card className="border-0 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Пациент</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Панели</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Статус</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Приоритет</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Дата</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Действие</th>
                <th className="w-8" />
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">Загрузка...</td></tr>
              )}
              {!isLoading && data?.items.length === 0 && (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">Нет направлений</td></tr>
              )}
              {data?.items.map((o) => (
                <tr key={o.id} className="border-b border-gray-50 hover:bg-[#F8F9FA] transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{o.patient.full_name}</p>
                    <p className="text-xs text-gray-400 font-mono">{o.patient.medical_record_number}</p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {o.requested_panels.map(p => (
                        <span key={p} className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                          {PANEL_LABELS[p] ?? p}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={o.status} /></td>
                  <td className="px-4 py-3"><PriorityBadge priority={o.priority} /></td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{formatDateTime(o.ordered_at)}</td>
                  <td className="px-4 py-3">
                    {o.status === 'ORDERED' && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-lg gap-1.5 h-7 text-xs"
                        disabled={acceptMutation.isPending}
                        onClick={() => acceptMutation.mutate(o.id)}
                      >
                        <PlayCircle className="w-3.5 h-3.5" />
                        Принять
                      </Button>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/lab/orders/${o.id}`} className="text-gray-400 hover:text-[#4A6FA5]">
                      <ChevronRight className="w-4 h-4" />
                    </Link>
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

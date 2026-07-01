'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import api from '@/lib/api'
import { Patient, LabOrder, Conclusion, PaginatedResponse } from '@/types'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDate, formatDateTime, PANEL_LABELS } from '@/lib/utils'

export default function PatientDashboard() {
  const [expandedOrder, setExpandedOrder] = useState<string | null>(null)
  const [page, setPage] = useState(1)

  const { data: patient } = useQuery({
    queryKey: ['my-patient'],
    queryFn: async () => (await api.get<Patient>('/patients/me')).data,
    retry: false,
  })

  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['my-orders', page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), size: '10' })
      const res = await api.get<PaginatedResponse<LabOrder>>(`/lab-orders?${params}`)
      return res.data
    },
  })

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Личный кабинет</h1>
        <p className="text-sm text-gray-500 mt-0.5">Ваши медицинские данные и направления</p>
      </div>

      {/* Patient card */}
      {patient && (
        <Card className="border-0 shadow-sm mb-4">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Карточка пациента</h2></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-gray-500">ФИО</p>
              <p className="font-medium text-gray-900">{patient.full_name}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Номер карты (МКН)</p>
              <p className="font-mono text-sm text-[#4A6FA5]">{patient.medical_record_number}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Дата рождения</p>
              <p className="text-sm text-gray-900">{formatDate(patient.date_of_birth)} ({patient.age} лет)</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Пол</p>
              <p className="text-sm text-gray-900">{patient.gender === 'MALE' ? 'Мужской' : 'Женский'}</p>
            </div>
            {patient.phone && (
              <div>
                <p className="text-xs text-gray-500">Телефон</p>
                <p className="text-sm text-gray-900">{patient.phone}</p>
              </div>
            )}
            {patient.address && (
              <div>
                <p className="text-xs text-gray-500">Адрес</p>
                <p className="text-sm text-gray-900">{patient.address}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Orders */}
      <h2 className="font-semibold text-gray-800 mb-3">Мои направления</h2>

      {isLoading && <p className="text-gray-400 text-sm">Загрузка...</p>}
      {!isLoading && ordersData?.items.length === 0 && (
        <Card className="border-0 shadow-sm">
          <CardContent className="text-center py-8 text-gray-400">Направлений пока нет</CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {ordersData?.items.map(order => (
          <OrderCard
            key={order.id}
            order={order}
            expanded={expandedOrder === order.id}
            onToggle={() => setExpandedOrder(prev => prev === order.id ? null : order.id)}
          />
        ))}
      </div>

      {ordersData && ordersData.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">Страница {page} из {ordersData.pages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page === 1} className="rounded-lg">Назад</Button>
            <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= ordersData.pages} className="rounded-lg">Вперёд</Button>
          </div>
        </div>
      )}
    </div>
  )
}

function OrderCard({ order, expanded, onToggle }: { order: LabOrder; expanded: boolean; onToggle: () => void }) {
  const { data: conclusion } = useQuery({
    queryKey: ['patient-conclusion', order.id],
    queryFn: async () => {
      try {
        const c = (await api.get<Conclusion>(`/lab-orders/${order.id}/conclusion`)).data
        return c.status === 'SENT' ? c : null
      } catch {
        return null
      }
    },
    enabled: order.status === 'CONCLUDED',
  })

  return (
    <Card className="border-0 shadow-sm overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full text-left px-4 py-3 hover:bg-[#F8F9FA] transition-colors"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <StatusBadge status={order.status} />
              <span className="text-xs text-gray-400">{formatDateTime(order.ordered_at)}</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {order.requested_panels.map(p => (
                <span key={p} className="text-xs text-gray-600">{PANEL_LABELS[p] ?? p}</span>
              )).reduce((acc: React.ReactNode[], el, i, arr) => [
                ...acc,
                el,
                i < arr.length - 1 ? <span key={`sep-${i}`} className="text-xs text-gray-300">·</span> : null,
              ], [])}
            </div>
          </div>
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-100 px-4 py-3 space-y-3">
          {order.results && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-2">Результаты анализов</p>
              <div className="grid grid-cols-2 gap-2">
                {([
                  ['Глюкоза', order.results.glucose, 'ммоль/л'],
                  ['HbA1c', order.results.hba1c, '%'],
                  ['Инсулин', order.results.insulin, 'мкМЕ/мл'],
                  ['ИМТ', order.results.bmi, 'кг/м²'],
                  ['Обхват талии', order.results.waist_circumference, 'см'],
                  ['Систол. АД', order.results.systolic_bp, 'мм рт.ст.'],
                  ['Диастол. АД', order.results.diastolic_bp, 'мм рт.ст.'],
                  ['Общий хол.', order.results.total_cholesterol, 'ммоль/л'],
                  ['ЛПВП', order.results.hdl_cholesterol, 'ммоль/л'],
                  ['ЛПНП', order.results.ldl_cholesterol, 'ммоль/л'],
                  ['Триглицериды', order.results.triglycerides, 'ммоль/л'],
                ] as [string, string | number | null, string][]).map(([label, val, unit]) =>
                  val != null && val !== '' ? (
                    <div key={label} className="bg-[#F8F9FA] rounded-lg p-2">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className="font-semibold text-gray-900 text-sm">{val} <span className="font-normal text-xs text-gray-400">{unit}</span></p>
                    </div>
                  ) : null
                )}
              </div>
            </div>
          )}

          {/* Only show SENT conclusion to patient — no ML scores */}
          {conclusion && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 space-y-2">
              <p className="text-xs font-medium text-blue-800">Заключение врача</p>
              {conclusion.preliminary_diagnosis && (
                <div>
                  <p className="text-xs text-blue-600">Диагноз</p>
                  <p className="text-sm text-blue-900">{conclusion.preliminary_diagnosis}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-blue-600">Заключение</p>
                <p className="text-sm text-blue-900 whitespace-pre-line">{conclusion.conclusion_text}</p>
              </div>
              {conclusion.recommendations && (
                <div>
                  <p className="text-xs text-blue-600">Рекомендации</p>
                  <p className="text-sm text-blue-900 whitespace-pre-line">{conclusion.recommendations}</p>
                </div>
              )}
              {conclusion.follow_up_date && (
                <div>
                  <p className="text-xs text-blue-600">Повторный визит</p>
                  <p className="text-sm text-blue-900">{formatDate(conclusion.follow_up_date)}</p>
                </div>
              )}
              {conclusion.sent_at && (
                <p className="text-xs text-blue-400">Выдано {formatDateTime(conclusion.sent_at)}</p>
              )}
            </div>
          )}

          {order.status === 'CONCLUDED' && !conclusion && (
            <p className="text-xs text-gray-400">Заключение ещё не передано</p>
          )}
        </div>
      )}
    </Card>
  )
}

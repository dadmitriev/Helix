'use client'

import { useQuery } from '@tanstack/react-query'
import { Users, ClipboardList, Activity, UserCheck } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import api from '@/lib/api'
import { SystemStats } from '@/types'
import { STATUS_LABELS } from '@/lib/utils'

const STATUS_BAR_COLORS: Record<string, string> = {
  ORDERED: 'bg-blue-500',
  IN_PROGRESS: 'bg-yellow-500',
  RESULTS_READY: 'bg-green-500',
  CONCLUDED: 'bg-gray-400',
}

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => (await api.get<SystemStats>('/admin/stats')).data,
  })

  if (isLoading) return <div className="p-6 text-gray-400">Загрузка...</div>

  const totalOrders = stats ? Object.values(stats.orders_by_status).reduce((a, b) => a + b, 0) : 0

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Панель управления</h1>
        <p className="text-sm text-gray-500 mt-0.5">Статистика системы</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={<Users className="w-5 h-5 text-[#4A6FA5]" />}
          label="Пользователей"
          value={stats?.total_users ?? 0}
        />
        <StatCard
          icon={<UserCheck className="w-5 h-5 text-green-600" />}
          label="Пациентов"
          value={stats?.total_patients ?? 0}
        />
        <StatCard
          icon={<ClipboardList className="w-5 h-5 text-yellow-600" />}
          label="Направлений"
          value={totalOrders}
        />
        <StatCard
          icon={<Activity className="w-5 h-5 text-purple-600" />}
          label="В работе"
          value={stats?.orders_by_status?.IN_PROGRESS ?? 0}
        />
      </div>

      {/* Orders by status chart */}
      <Card className="border-0 shadow-sm mb-4">
        <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Направления по статусам</h2></CardHeader>
        <CardContent>
          {totalOrders === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">Нет данных</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(stats?.orders_by_status ?? {}).map(([status, count]) => {
                const pct = totalOrders > 0 ? (count / totalOrders) * 100 : 0
                return (
                  <div key={status}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-700">{STATUS_LABELS[status as keyof typeof STATUS_LABELS] ?? status}</span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                    <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${STATUS_BAR_COLORS[status] ?? 'bg-gray-400'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <Card className="border-0 shadow-sm">
      <CardContent className="pt-5 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#F8F9FA] rounded-lg">{icon}</div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

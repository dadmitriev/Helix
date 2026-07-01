'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { Search, UserPlus, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import api from '@/lib/api'
import { Patient, PaginatedResponse } from '@/types'
import { formatDate } from '@/lib/utils'

export default function PatientsPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['patients', search, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), size: '20' })
      if (search) params.set('search', search)
      const res = await api.get<PaginatedResponse<Patient>>(`/patients?${params}`)
      return res.data
    },
  })

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Пациенты</h1>
          <p className="text-sm text-gray-500 mt-0.5">Всего: {data?.total ?? 0}</p>
        </div>
        <Link href="/doctor/patients/new" className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#4A6FA5] hover:bg-[#3d5d8f] text-white text-sm font-medium rounded-lg transition-colors">
          <UserPlus className="w-4 h-4" />
          Новый пациент
        </Link>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          placeholder="Поиск по имени или номеру карты (MRN)..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          className="pl-9 h-10 rounded-lg"
        />
      </div>

      {/* Table */}
      <Card className="border-0 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">МКН</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">ФИО</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Дата рождения</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Возраст</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Пол</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Анамнез</th>
                <th className="w-8" />
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">Загрузка...</td></tr>
              )}
              {!isLoading && data?.items.length === 0 && (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">Пациенты не найдены</td></tr>
              )}
              {data?.items.map((p) => (
                <tr key={p.id} className="border-b border-gray-50 hover:bg-[#F8F9FA] transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-[#4A6FA5]">{p.medical_record_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{p.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(p.date_of_birth)}</td>
                  <td className="px-4 py-3 text-gray-600">{p.age} лет</td>
                  <td className="px-4 py-3 text-gray-600">{p.gender === 'MALE' ? 'М' : 'Ж'}</td>
                  <td className="px-4 py-3">
                    {p.family_history_diabetes ? (
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">Есть</span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/doctor/patients/${p.id}`} className="text-gray-400 hover:text-[#4A6FA5]">
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
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

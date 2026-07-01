'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Edit2, Check, X, ClipboardList } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/lib/api'
import { Patient } from '@/types'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [editData, setEditData] = useState<Partial<Patient>>({})

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', id],
    queryFn: async () => (await api.get<Patient>(`/patients/${id}`)).data,
  })

  const update = useMutation({
    mutationFn: (body: Partial<Patient>) => api.patch(`/patients/${id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['patient', id] })
      setEditing(false)
      toast.success('Данные обновлены')
    },
    onError: () => toast.error('Ошибка при сохранении'),
  })

  if (isLoading) return <div className="p-6 text-gray-400">Загрузка...</div>
  if (!patient) return <div className="p-6 text-gray-400">Пациент не найден</div>

  const d = editing ? { ...patient, ...editData } : patient

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{patient.full_name}</h1>
            <p className="text-sm text-[#4A6FA5] font-mono">{patient.medical_record_number}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Link href={`/doctor/orders/new?patient_id=${id}`} className="inline-flex items-center gap-2 px-3 py-1.5 border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors">
            <ClipboardList className="w-4 h-4" />
            Новое направление
          </Link>
          {!editing ? (
            <Button onClick={() => setEditing(true)} variant="outline" className="rounded-lg gap-2">
              <Edit2 className="w-4 h-4" />
              Редактировать
            </Button>
          ) : (
            <>
              <Button onClick={() => update.mutate(editData)} disabled={update.isPending} className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg gap-2">
                <Check className="w-4 h-4" />
                Сохранить
              </Button>
              <Button onClick={() => { setEditing(false); setEditData({}) }} variant="outline" className="rounded-lg gap-2">
                <X className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card className="border-0 shadow-sm col-span-2">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Персональные данные</h2></CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Field label="Фамилия" value={d.last_name} editing={editing}
              onChange={v => setEditData(p => ({ ...p, last_name: v }))} />
            <Field label="Имя" value={d.first_name} editing={editing}
              onChange={v => setEditData(p => ({ ...p, first_name: v }))} />
            <Field label="Отчество" value={d.middle_name ?? ''} editing={editing}
              onChange={v => setEditData(p => ({ ...p, middle_name: v }))} />
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-500">Дата рождения</Label>
              {editing ? (
                <Input type="date" defaultValue={d.date_of_birth} className="rounded-lg h-9"
                  onChange={e => setEditData(p => ({ ...p, date_of_birth: e.target.value }))} />
              ) : (
                <p className="text-sm text-gray-900">{formatDate(d.date_of_birth)}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-500">Возраст</Label>
              <p className="text-sm text-gray-900">{patient.age} лет</p>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-500">Пол</Label>
              {editing ? (
                <Select defaultValue={d.gender} onValueChange={v => setEditData(p => ({ ...p, gender: v as 'MALE' | 'FEMALE' }))}>
                  <SelectTrigger className="rounded-lg h-9"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MALE">Мужской</SelectItem>
                    <SelectItem value="FEMALE">Женский</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm text-gray-900">{d.gender === 'MALE' ? 'Мужской' : 'Женский'}</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm col-span-2">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Контакты и анамнез</h2></CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Field label="Телефон" value={d.phone ?? ''} editing={editing}
              onChange={v => setEditData(p => ({ ...p, phone: v }))} />
            <Field label="Адрес" value={d.address ?? ''} editing={editing}
              onChange={v => setEditData(p => ({ ...p, address: v }))} />
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-500">Семейный анамнез по СД</Label>
              {editing ? (
                <Select defaultValue={String(d.family_history_diabetes)}
                  onValueChange={v => setEditData(p => ({ ...p, family_history_diabetes: v === 'true' }))}>
                  <SelectTrigger className="rounded-lg h-9"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false">Не отягощён</SelectItem>
                    <SelectItem value="true">Отягощён</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm">
                  {d.family_history_diabetes
                    ? <span className="text-orange-600 font-medium">Отягощён</span>
                    : <span className="text-gray-600">Не отягощён</span>}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Field({ label, value, editing, onChange }: {
  label: string; value: string; editing: boolean; onChange: (v: string) => void
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-gray-500">{label}</Label>
      {editing ? (
        <Input className="rounded-lg h-9" defaultValue={value} onChange={e => onChange(e.target.value)} />
      ) : (
        <p className="text-sm text-gray-900">{value || '—'}</p>
      )}
    </div>
  )
}

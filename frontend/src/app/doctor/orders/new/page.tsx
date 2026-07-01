'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import api from '@/lib/api'
import { Patient, PaginatedResponse } from '@/types'
import { ALL_PANELS, PANEL_LABELS } from '@/lib/utils'
import { toast } from 'sonner'

export default function NewOrderPage() {
  return (
    <Suspense>
      <NewOrderForm />
    </Suspense>
  )
}

function NewOrderForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const presetPatientId = searchParams.get('patient_id')

  const [patientSearch, setPatientSearch] = useState('')
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const [selectedPanels, setSelectedPanels] = useState<string[]>([])
  const [priority, setPriority] = useState('ROUTINE')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { data: patients } = useQuery({
    queryKey: ['patients-search', patientSearch],
    queryFn: async () => {
      const params = new URLSearchParams({ size: '10' })
      if (patientSearch) params.set('search', patientSearch)
      const res = await api.get<PaginatedResponse<Patient>>(`/patients?${params}`)
      return res.data.items
    },
    enabled: !presetPatientId,
  })

  const { data: presetPatient } = useQuery({
    queryKey: ['patient', presetPatientId],
    queryFn: async () => (await api.get<Patient>(`/patients/${presetPatientId}`)).data,
    enabled: !!presetPatientId,
  })

  const activePatient = presetPatient ?? selectedPatient

  function togglePanel(panel: string) {
    setSelectedPanels(prev =>
      prev.includes(panel) ? prev.filter(p => p !== panel) : [...prev, panel]
    )
  }

  async function handleSubmit() {
    if (!activePatient) return toast.error('Выберите пациента')
    if (selectedPanels.length === 0) return toast.error('Выберите хотя бы одну панель')

    setSubmitting(true)
    try {
      const res = await api.post('/lab-orders', {
        patient_id: activePatient.id,
        priority,
        requested_panels: selectedPanels,
        order_notes: notes || null,
      })
      toast.success('Направление создано')
      router.push(`/doctor/orders/${res.data.id}`)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Ошибка при создании направления')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Новое направление</h1>
          <p className="text-sm text-gray-500">Создание направления в лабораторию</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Patient */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Пациент</h2></CardHeader>
          <CardContent>
            {activePatient ? (
              <div className="flex items-center justify-between p-3 bg-[#F8F9FA] rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{activePatient.full_name}</p>
                  <p className="text-xs text-[#4A6FA5] font-mono">{activePatient.medical_record_number} · {activePatient.age} лет</p>
                </div>
                {!presetPatientId && (
                  <button onClick={() => setSelectedPatient(null)} className="text-xs text-gray-400 hover:text-red-500">Изменить</button>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Поиск по имени или MRN..."
                    value={patientSearch}
                    onChange={e => setPatientSearch(e.target.value)}
                    className="pl-9 rounded-lg"
                  />
                </div>
                {patients && patients.length > 0 && (
                  <div className="border border-gray-100 rounded-lg overflow-hidden">
                    {patients.map(p => (
                      <button
                        key={p.id}
                        onClick={() => setSelectedPatient(p)}
                        className="w-full text-left px-4 py-2.5 hover:bg-[#F8F9FA] border-b border-gray-50 last:border-0 transition-colors"
                      >
                        <p className="text-sm font-medium text-gray-900">{p.full_name}</p>
                        <p className="text-xs text-gray-400">{p.medical_record_number}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Panels */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Панели анализов</h2></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {ALL_PANELS.map(panel => (
                <button
                  key={panel}
                  onClick={() => togglePanel(panel)}
                  className={`px-3 py-2.5 rounded-lg text-sm font-medium text-left border transition-colors ${
                    selectedPanels.includes(panel)
                      ? 'bg-[#4A6FA5] text-white border-[#4A6FA5]'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-[#4A6FA5] hover:text-[#4A6FA5]'
                  }`}
                >
                  {PANEL_LABELS[panel]}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Priority and notes */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Параметры направления</h2></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Приоритет</Label>
              <Select value={priority} onValueChange={v => setPriority(v ?? 'ROUTINE')}>
                <SelectTrigger className="rounded-lg">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ROUTINE">Плановое</SelectItem>
                  <SelectItem value="URGENT">Срочное</SelectItem>
                  <SelectItem value="EMERGENCY">Экстренное</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Примечания</Label>
              <Textarea
                placeholder="Клинические сведения для лаборанта..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
                className="rounded-lg resize-none"
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="outline" className="rounded-lg" onClick={() => router.back()}>Отмена</Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting || !activePatient || selectedPanels.length === 0}
            className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg"
          >
            {submitting ? 'Создание...' : 'Создать направление'}
          </Button>
        </div>
      </div>
    </div>
  )
}

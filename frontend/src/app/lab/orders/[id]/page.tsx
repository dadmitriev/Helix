'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, RotateCcw, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import api from '@/lib/api'
import { LabOrder } from '@/types'
import { StatusBadge, PriorityBadge } from '@/components/shared/StatusBadge'
import { formatDateTime, PANEL_LABELS } from '@/lib/utils'
import { toast } from 'sonner'

interface ResultsForm {
  analysis_date: string
  analysis_time: string
  lab_notes: string
  glucose: string
  hba1c: string
  insulin: string
  bmi: string
  waist_circumference: string
  systolic_bp: string
  diastolic_bp: string
  total_cholesterol: string
  hdl_cholesterol: string
  ldl_cholesterol: string
  triglycerides: string
}

const PANEL_FIELDS: Record<string, { key: keyof ResultsForm; label: string; unit: string; step: string }[]> = {
  GLUCOSE: [{ key: 'glucose', label: 'Глюкоза', unit: 'ммоль/л', step: '0.01' }],
  HBA1C: [{ key: 'hba1c', label: 'HbA1c', unit: '%', step: '0.1' }],
  INSULIN: [{ key: 'insulin', label: 'Инсулин', unit: 'мкМЕ/мл', step: '0.1' }],
  ANTHROPOMETRY: [
    { key: 'bmi', label: 'ИМТ', unit: 'кг/м²', step: '0.1' },
    { key: 'waist_circumference', label: 'Обхват талии', unit: 'см', step: '0.1' },
  ],
  BLOOD_PRESSURE: [
    { key: 'systolic_bp', label: 'Систол. АД', unit: 'мм рт.ст.', step: '1' },
    { key: 'diastolic_bp', label: 'Диастол. АД', unit: 'мм рт.ст.', step: '1' },
  ],
  LIPID_PANEL: [
    { key: 'total_cholesterol', label: 'Общий хол.', unit: 'ммоль/л', step: '0.01' },
    { key: 'hdl_cholesterol', label: 'ЛПВП', unit: 'ммоль/л', step: '0.01' },
    { key: 'ldl_cholesterol', label: 'ЛПНП', unit: 'ммоль/л', step: '0.01' },
    { key: 'triglycerides', label: 'Триглицериды', unit: 'ммоль/л', step: '0.01' },
  ],
}

function emptyForm(): ResultsForm {
  const today = new Date()
  return {
    analysis_date: today.toISOString().split('T')[0],
    analysis_time: today.toTimeString().slice(0, 5),
    lab_notes: '',
    glucose: '', hba1c: '', insulin: '', bmi: '',
    waist_circumference: '', systolic_bp: '', diastolic_bp: '',
    total_cholesterol: '', hdl_cholesterol: '', ldl_cholesterol: '', triglycerides: '',
  }
}

export default function LabOrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()

  const [form, setForm] = useState<ResultsForm>(emptyForm())
  const [editing, setEditing] = useState(false)

  const { data: order, isLoading } = useQuery({
    queryKey: ['lab-order', id],
    queryFn: async () => {
      const res = await api.get<LabOrder>(`/lab-orders/${id}`)
      return res.data
    },
  })

  function initFormFromOrder(o: LabOrder) {
    if (!o.results) return
    const r = o.results
    setForm({
      analysis_date: r.analysis_date ?? new Date().toISOString().split('T')[0],
      analysis_time: r.analysis_time ?? new Date().toTimeString().slice(0, 5),
      lab_notes: r.lab_notes ?? '',
      glucose: r.glucose ?? '',
      hba1c: r.hba1c ?? '',
      insulin: r.insulin ?? '',
      bmi: r.bmi ?? '',
      waist_circumference: r.waist_circumference ?? '',
      systolic_bp: r.systolic_bp != null ? String(r.systolic_bp) : '',
      diastolic_bp: r.diastolic_bp != null ? String(r.diastolic_bp) : '',
      total_cholesterol: r.total_cholesterol ?? '',
      hdl_cholesterol: r.hdl_cholesterol ?? '',
      ldl_cholesterol: r.ldl_cholesterol ?? '',
      triglycerides: r.triglycerides ?? '',
    })
  }

  const submitMutation = useMutation({
    mutationFn: async (body: object) => {
      // Step 1: save field values
      await api.patch(`/lab-orders/${id}/results`, body)
      // Step 2: finalize — validates all required panel fields are filled
      return api.post(`/lab-orders/${id}/submit-results`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lab-order', id] })
      qc.invalidateQueries({ queryKey: ['lab-queue'] })
      setEditing(false)
      toast.success('Результаты внесены')
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Ошибка при внесении результатов')
    },
  })

  const reopenMutation = useMutation({
    mutationFn: () => api.post(`/lab-orders/${id}/reopen-results`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lab-order', id] })
      qc.invalidateQueries({ queryKey: ['lab-queue'] })
      toast.success('Направление переоткрыто для редактирования')
    },
    onError: () => toast.error('Ошибка при переоткрытии'),
  })

  function handleSubmit() {
    const body: Record<string, string | number | null> = {
      analysis_date: form.analysis_date || null,
      analysis_time: form.analysis_time || null,
      lab_notes: form.lab_notes || null,
    }
    ;(['glucose', 'hba1c', 'insulin', 'bmi', 'waist_circumference',
      'total_cholesterol', 'hdl_cholesterol', 'ldl_cholesterol', 'triglycerides'] as const).forEach(k => {
      body[k] = form[k] ? form[k] : null
    })
    ;(['systolic_bp', 'diastolic_bp'] as const).forEach(k => {
      body[k] = form[k] ? parseInt(form[k], 10) : null
    })
    submitMutation.mutate(body)
  }

  function setField(key: keyof ResultsForm, value: string) {
    setForm(p => ({ ...p, [key]: value }))
  }

  if (isLoading) return <div className="p-6 text-gray-400">Загрузка...</div>
  if (!order) return <div className="p-6 text-gray-400">Направление не найдено</div>

  const canEdit = order.status === 'IN_PROGRESS'
  const hasResults = !!order.results && order.status !== 'IN_PROGRESS'

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Направление #{order.id.slice(0, 8)}</h1>
            <p className="text-sm text-gray-500">{order.patient.full_name}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={order.status} />
          <PriorityBadge priority={order.priority} />
        </div>
      </div>

      <div className="space-y-4">
        {/* Info */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Пациент и назначение</h2></CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{order.patient.full_name}</p>
                <p className="text-xs text-[#4A6FA5] font-mono">{order.patient.medical_record_number} · {order.patient.age} лет</p>
              </div>
              <p className="text-xs text-gray-400">{formatDateTime(order.ordered_at)}</p>
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {order.requested_panels.map(p => (
                <span key={p} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                  {PANEL_LABELS[p] ?? p}
                </span>
              ))}
            </div>
            {order.order_notes && (
              <p className="text-xs text-gray-500 italic">«{order.order_notes}»</p>
            )}
          </CardContent>
        </Card>

        {/* Results form or view */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">Результаты анализов</h2>
              {hasResults && !editing && (
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-lg gap-1.5 h-7 text-xs"
                  onClick={() => { reopenMutation.mutate() }}
                  disabled={reopenMutation.isPending}
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Переоткрыть
                </Button>
              )}
              {canEdit && !editing && (
                <Button
                  size="sm"
                  className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg h-7 text-xs"
                  onClick={() => { initFormFromOrder(order); setEditing(true) }}
                >
                  Заполнить результаты
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!editing && !hasResults && order.status === 'IN_PROGRESS' && (
              <p className="text-sm text-gray-400 text-center py-4">Нажмите «Заполнить результаты» для внесения данных</p>
            )}
            {!editing && !hasResults && order.status === 'ORDERED' && (
              <p className="text-sm text-gray-400 text-center py-4">Сначала примите направление в работу из очереди</p>
            )}

            {/* View mode for submitted results */}
            {!editing && hasResults && order.results && (
              <div className="space-y-3">
                <div className="flex gap-4 text-xs text-gray-500">
                  {order.results.analysis_date && <span>Дата: {order.results.analysis_date}</span>}
                  {order.results.analysis_time && <span>Время: {order.results.analysis_time}</span>}
                </div>
                <div className="grid grid-cols-3 gap-3">
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
                      <div key={label} className="bg-[#F8F9FA] rounded-lg p-2.5">
                        <p className="text-xs text-gray-500">{label}</p>
                        <p className="font-semibold text-gray-900 text-sm">{val} <span className="font-normal text-xs text-gray-400">{unit}</span></p>
                      </div>
                    ) : null
                  )}
                </div>
                {order.results.lab_notes && (
                  <p className="text-xs text-gray-500 italic">Примечание: «{order.results.lab_notes}»</p>
                )}
                <div className="flex items-center gap-2 text-green-700 bg-green-50 rounded-lg px-3 py-2 text-xs">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  Результаты переданы врачу
                </div>
              </div>
            )}

            {/* Edit form */}
            {editing && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Дата анализа</Label>
                    <Input type="date" value={form.analysis_date} onChange={e => setField('analysis_date', e.target.value)} className="rounded-lg h-9" />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Время анализа</Label>
                    <Input type="time" value={form.analysis_time} onChange={e => setField('analysis_time', e.target.value)} className="rounded-lg h-9" />
                  </div>
                </div>

                {order.requested_panels.map(panel => {
                  const fields = PANEL_FIELDS[panel]
                  if (!fields) return null
                  return (
                    <div key={panel}>
                      <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">{PANEL_LABELS[panel] ?? panel}</p>
                      <div className="grid grid-cols-2 gap-3">
                        {fields.map(f => (
                          <div key={f.key} className="space-y-1.5">
                            <Label className="text-xs">{f.label} <span className="text-gray-400 font-normal">({f.unit})</span></Label>
                            <Input
                              type="number"
                              step={f.step}
                              placeholder={`0.00`}
                              value={form[f.key]}
                              onChange={e => setField(f.key, e.target.value)}
                              className="rounded-lg h-9"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}

                <div className="space-y-1.5">
                  <Label className="text-xs">Примечание лаборанта</Label>
                  <Textarea
                    value={form.lab_notes}
                    onChange={e => setField('lab_notes', e.target.value)}
                    placeholder="Дополнительные наблюдения..."
                    rows={2}
                    className="rounded-lg resize-none"
                  />
                </div>

                <div className="flex gap-2 justify-end pt-1">
                  <Button variant="outline" size="sm" className="rounded-lg" onClick={() => setEditing(false)}>
                    Отмена
                  </Button>
                  <Button
                    size="sm"
                    className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg gap-1.5"
                    disabled={submitMutation.isPending}
                    onClick={handleSubmit}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {submitMutation.isPending ? 'Сохранение...' : 'Передать результаты врачу'}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

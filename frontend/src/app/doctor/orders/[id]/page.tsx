'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Brain, Send, Edit2, Check, X, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/lib/api'
import { LabOrder, PredictionFullResponse, Conclusion, RiskLevel } from '@/types'
import { StatusBadge, PriorityBadge } from '@/components/shared/StatusBadge'
import { RiskBadge } from '@/components/shared/RiskBadge'
import { formatDateTime, formatDate, PANEL_LABELS, RISK_LABELS } from '@/lib/utils'
import { toast } from 'sonner'

const FEATURE_LABELS: Record<string, string> = {
  glucose: 'Глюкоза',
  hba1c: 'HbA1c',
  insulin: 'Инсулин',
  bmi: 'ИМТ',
  waist_circumference: 'Обхват талии',
  systolic_bp: 'Систол. АД',
  diastolic_bp: 'Диастол. АД',
  total_cholesterol: 'Общий холестерин',
  hdl_cholesterol: 'ЛПВП',
  ldl_cholesterol: 'ЛПНП',
  triglycerides: 'Триглицериды',
  family_history_diabetes: 'Сем. анамнез СД',
  age: 'Возраст',
}

const REC_PRIORITY_COLORS: Record<string, string> = {
  HIGH: 'border-red-300 bg-red-50',
  MEDIUM: 'border-yellow-300 bg-yellow-50',
  LOW: 'border-green-300 bg-green-50',
}

const REC_PRIORITY_LABELS: Record<string, string> = {
  HIGH: 'Высокий',
  MEDIUM: 'Средний',
  LOW: 'Низкий',
}

interface ConclusionForm {
  conclusion_text: string
  preliminary_diagnosis: string
  recommendations: string
  agreed_with_ai: boolean
  risk_confirmed: RiskLevel | ''
  follow_up_date: string
}

function emptyForm(): ConclusionForm {
  return {
    conclusion_text: '',
    preliminary_diagnosis: '',
    recommendations: '',
    agreed_with_ai: false,
    risk_confirmed: '',
    follow_up_date: '',
  }
}

function conclusionToForm(c: Conclusion): ConclusionForm {
  return {
    conclusion_text: c.conclusion_text,
    preliminary_diagnosis: c.preliminary_diagnosis ?? '',
    recommendations: c.recommendations ?? '',
    agreed_with_ai: c.agreed_with_ai,
    risk_confirmed: c.risk_confirmed ?? '',
    follow_up_date: c.follow_up_date ?? '',
  }
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()

  const [editingConclusion, setEditingConclusion] = useState(false)
  const [conclusionForm, setConclusionForm] = useState<ConclusionForm>(emptyForm())

  const { data: order, isLoading: orderLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: async () => (await api.get<LabOrder>(`/lab-orders/${id}`)).data,
  })

  const { data: predData } = useQuery({
    queryKey: ['prediction', id],
    queryFn: async () => (await api.get<PredictionFullResponse>(`/lab-orders/${id}/prediction`)).data,
    enabled: !!order && (order.status === 'RESULTS_READY' || order.status === 'CONCLUDED'),
    retry: false,
  })

  const { data: conclusion, refetch: refetchConclusion } = useQuery({
    queryKey: ['conclusion', id],
    queryFn: async () => {
      try {
        return (await api.get<Conclusion>(`/lab-orders/${id}/conclusion`)).data
      } catch {
        return null
      }
    },
    enabled: !!order && (order.status === 'RESULTS_READY' || order.status === 'CONCLUDED'),
  })

  const predictMutation = useMutation({
    mutationFn: () => api.post(`/lab-orders/${id}/predict`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prediction', id] })
      qc.invalidateQueries({ queryKey: ['order', id] })
      toast.success('ML-анализ выполнен')
    },
    onError: () => toast.error('Ошибка при запуске анализа'),
  })

  const createConclusionMutation = useMutation({
    mutationFn: (body: object) => api.post(`/lab-orders/${id}/conclusion`, body),
    onSuccess: () => {
      refetchConclusion()
      qc.invalidateQueries({ queryKey: ['order', id] })
      setEditingConclusion(false)
      toast.success('Заключение создано')
    },
    onError: () => toast.error('Ошибка при создании заключения'),
  })

  const updateConclusionMutation = useMutation({
    mutationFn: (body: object) => api.patch(`/lab-orders/${id}/conclusion`, body),
    onSuccess: () => {
      refetchConclusion()
      setEditingConclusion(false)
      toast.success('Заключение обновлено')
    },
    onError: () => toast.error('Ошибка при обновлении заключения'),
  })

  const sendConclusionMutation = useMutation({
    mutationFn: () => api.post(`/lab-orders/${id}/conclusion/send`),
    onSuccess: () => {
      refetchConclusion()
      qc.invalidateQueries({ queryKey: ['order', id] })
      toast.success('Заключение отправлено пациенту')
    },
    onError: () => toast.error('Ошибка при отправке'),
  })

  function startCreateConclusion() {
    if (predData?.prediction) {
      setConclusionForm({
        ...emptyForm(),
        agreed_with_ai: true,
        risk_confirmed: predData.prediction.risk_level,
      })
    } else {
      setConclusionForm(emptyForm())
    }
    setEditingConclusion(true)
  }

  function startEditConclusion() {
    if (conclusion) setConclusionForm(conclusionToForm(conclusion))
    setEditingConclusion(true)
  }

  function submitConclusion() {
    const body = {
      conclusion_text: conclusionForm.conclusion_text,
      preliminary_diagnosis: conclusionForm.preliminary_diagnosis || null,
      recommendations: conclusionForm.recommendations || null,
      agreed_with_ai: conclusionForm.agreed_with_ai,
      risk_confirmed: conclusionForm.risk_confirmed || null,
      follow_up_date: conclusionForm.follow_up_date || null,
    }
    if (!conclusion) {
      createConclusionMutation.mutate(body)
    } else {
      updateConclusionMutation.mutate(body)
    }
  }

  if (orderLoading) return <div className="p-6 text-gray-400">Загрузка...</div>
  if (!order) return <div className="p-6 text-gray-400">Направление не найдено</div>

  const canPredict = order.status === 'RESULTS_READY' || order.status === 'CONCLUDED'
  const hasPrediction = !!predData
  const sortedImportances = predData
    ? Object.entries(predData.prediction.feature_importances).sort((a, b) => b[1] - a[1])
    : []
  const maxImportance = sortedImportances[0]?.[1] ?? 1

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Направление #{order.id.slice(0, 8)}</h1>
            <p className="text-sm text-gray-500">{order.patient.full_name} · {formatDateTime(order.ordered_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={order.status} />
          <PriorityBadge priority={order.priority} />
        </div>
      </div>

      <div className="space-y-4">
        {/* Order info */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Пациент</h2></CardHeader>
            <CardContent className="space-y-1">
              <p className="font-medium text-gray-900">{order.patient.full_name}</p>
              <p className="text-xs text-[#4A6FA5] font-mono">{order.patient.medical_record_number}</p>
              <p className="text-xs text-gray-500">{order.patient.age} лет · {order.patient.gender === 'MALE' ? 'М' : 'Ж'}</p>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Панели анализов</h2></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {order.requested_panels.map(p => (
                  <span key={p} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                    {PANEL_LABELS[p] ?? p}
                  </span>
                ))}
              </div>
              {order.order_notes && (
                <p className="text-xs text-gray-500 mt-2 italic">«{order.order_notes}»</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Lab results */}
        {order.results && (
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-800">Результаты анализов</h2>
                <span className="text-xs text-gray-400">
                  {order.results.analysis_date ? formatDate(order.results.analysis_date) : ''}
                  {order.results.analysis_time ? ` ${order.results.analysis_time}` : ''}
                </span>
              </div>
            </CardHeader>
            <CardContent>
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
                <p className="text-xs text-gray-500 mt-3 italic">Примечание лаборанта: «{order.results.lab_notes}»</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* ML Prediction */}
        {canPredict && (
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-800">ML-анализ риска СД</h2>
                {!hasPrediction && (
                  <Button
                    onClick={() => predictMutation.mutate()}
                    disabled={predictMutation.isPending}
                    className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg gap-2 h-8 text-xs"
                  >
                    <Brain className="w-3.5 h-3.5" />
                    {predictMutation.isPending ? 'Анализ...' : 'Запустить анализ'}
                  </Button>
                )}
              </div>
            </CardHeader>
            {hasPrediction && predData && (
              <CardContent className="space-y-4">
                {/* Risk score */}
                <div className="flex items-center gap-4 p-4 bg-[#F8F9FA] rounded-lg">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-1">Вероятность СД 2 типа</p>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            predData.prediction.risk_level === 'HIGH' ? 'bg-red-500' :
                            predData.prediction.risk_level === 'MODERATE' ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.round(parseFloat(predData.prediction.risk_score) * 100)}%` }}
                        />
                      </div>
                      <span className="text-lg font-bold text-gray-900 min-w-[48px]">
                        {Math.round(parseFloat(predData.prediction.risk_score) * 100)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">Уровень риска</p>
                    <RiskBadge level={predData.prediction.risk_level} />
                  </div>
                  {predData.prediction.homa_ir && (
                    <div className="text-center">
                      <p className="text-xs text-gray-500 mb-1">HOMA-IR</p>
                      <p className="text-lg font-bold text-gray-900">{parseFloat(predData.prediction.homa_ir).toFixed(2)}</p>
                    </div>
                  )}
                </div>

                {/* Feature importances */}
                {sortedImportances.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-2">Вклад факторов</p>
                    <div className="space-y-1.5">
                      {sortedImportances.slice(0, 8).map(([key, val]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-xs text-gray-500 w-36 shrink-0">{FEATURE_LABELS[key] ?? key}</span>
                          <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#4A6FA5] rounded-full"
                              style={{ width: `${(val / maxImportance) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400 w-10 text-right">{(val * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warning flags */}
                {predData.ai_recommendation.warning_flags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {predData.ai_recommendation.warning_flags.map((flag, i) => (
                      <div key={i} className="flex items-center gap-1 text-xs text-orange-700 bg-orange-50 border border-orange-200 px-2 py-1 rounded-lg">
                        <AlertTriangle className="w-3 h-3 shrink-0" />
                        {flag}
                      </div>
                    ))}
                  </div>
                )}

                {/* AI summary */}
                <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg">
                  <p className="text-xs font-medium text-blue-800 mb-1">Сводка ИИ</p>
                  <p className="text-sm text-blue-900">{predData.ai_recommendation.summary}</p>
                </div>

                {/* Recommendations */}
                {predData.ai_recommendation.recommendations.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-2">Рекомендации ИИ</p>
                    <div className="space-y-2">
                      {predData.ai_recommendation.recommendations.map((rec, i) => (
                        <div key={i} className={`p-3 rounded-lg border ${REC_PRIORITY_COLORS[rec.priority] ?? 'bg-gray-50 border-gray-200'}`}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-700">{rec.category}</span>
                            <span className="text-xs text-gray-500">Приоритет: {REC_PRIORITY_LABELS[rec.priority] ?? rec.priority}</span>
                          </div>
                          <p className="text-sm text-gray-800">{rec.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer */}
                <p className="text-xs text-gray-400 italic">{predData.disclaimer}</p>
              </CardContent>
            )}
            {!hasPrediction && (
              <CardContent>
                <p className="text-sm text-gray-400 text-center py-4">Нажмите «Запустить анализ» для получения прогноза ML-модели</p>
              </CardContent>
            )}
          </Card>
        )}

        {/* Conclusion */}
        {canPredict && (
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-800">Заключение врача</h2>
                {conclusion && !editingConclusion && (
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${conclusion.status === 'SENT' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {conclusion.status === 'SENT' ? 'Отправлено' : 'Черновик'}
                    </span>
                    {conclusion.status === 'DRAFT' && (
                      <>
                        <Button onClick={startEditConclusion} variant="outline" size="sm" className="rounded-lg gap-1.5 h-7 text-xs">
                          <Edit2 className="w-3 h-3" /> Редактировать
                        </Button>
                        <Button
                          onClick={() => sendConclusionMutation.mutate()}
                          disabled={sendConclusionMutation.isPending}
                          size="sm"
                          className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg gap-1.5 h-7 text-xs"
                        >
                          <Send className="w-3 h-3" />
                          {sendConclusionMutation.isPending ? 'Отправка...' : 'Отправить пациенту'}
                        </Button>
                      </>
                    )}
                  </div>
                )}
                {!conclusion && !editingConclusion && (
                  <Button onClick={startCreateConclusion} variant="outline" size="sm" className="rounded-lg h-7 text-xs">
                    + Создать заключение
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {!editingConclusion && conclusion && (
                <div className="space-y-3">
                  {conclusion.risk_confirmed && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Подтверждённый риск:</span>
                      <RiskBadge level={conclusion.risk_confirmed} />
                      {conclusion.agreed_with_ai && <span className="text-xs text-gray-400">(согласовано с ИИ)</span>}
                    </div>
                  )}
                  {conclusion.preliminary_diagnosis && (
                    <div>
                      <p className="text-xs text-gray-500 mb-0.5">Предварительный диагноз</p>
                      <p className="text-sm text-gray-900">{conclusion.preliminary_diagnosis}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">Заключение</p>
                    <p className="text-sm text-gray-900 whitespace-pre-line">{conclusion.conclusion_text}</p>
                  </div>
                  {conclusion.recommendations && (
                    <div>
                      <p className="text-xs text-gray-500 mb-0.5">Рекомендации</p>
                      <p className="text-sm text-gray-900 whitespace-pre-line">{conclusion.recommendations}</p>
                    </div>
                  )}
                  {conclusion.follow_up_date && (
                    <div>
                      <p className="text-xs text-gray-500 mb-0.5">Дата повторного визита</p>
                      <p className="text-sm text-gray-900">{formatDate(conclusion.follow_up_date)}</p>
                    </div>
                  )}
                  {conclusion.sent_at && (
                    <p className="text-xs text-gray-400">Отправлено: {formatDateTime(conclusion.sent_at)}</p>
                  )}
                </div>
              )}

              {!editingConclusion && !conclusion && (
                <p className="text-sm text-gray-400 text-center py-4">Заключение ещё не создано</p>
              )}

              {editingConclusion && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label className="text-xs">Заключение *</Label>
                    <Textarea
                      value={conclusionForm.conclusion_text}
                      onChange={e => setConclusionForm(p => ({ ...p, conclusion_text: e.target.value }))}
                      placeholder="Клиническое заключение врача..."
                      rows={4}
                      className="rounded-lg resize-none"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Предварительный диагноз</Label>
                    <Input
                      value={conclusionForm.preliminary_diagnosis}
                      onChange={e => setConclusionForm(p => ({ ...p, preliminary_diagnosis: e.target.value }))}
                      placeholder="МКБ-10 код или формулировка"
                      className="rounded-lg h-9"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-xs">Рекомендации</Label>
                    <Textarea
                      value={conclusionForm.recommendations}
                      onChange={e => setConclusionForm(p => ({ ...p, recommendations: e.target.value }))}
                      placeholder="Рекомендации по лечению и наблюдению..."
                      rows={3}
                      className="rounded-lg resize-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-xs">Подтверждённый уровень риска</Label>
                      <Select
                        value={conclusionForm.risk_confirmed}
                        onValueChange={v => setConclusionForm(p => ({ ...p, risk_confirmed: v as RiskLevel }))}
                      >
                        <SelectTrigger className="rounded-lg h-9">
                          <SelectValue placeholder="Не указан" />
                        </SelectTrigger>
                        <SelectContent>
                          {(['LOW', 'MODERATE', 'HIGH'] as RiskLevel[]).map(r => (
                            <SelectItem key={r} value={r}>{RISK_LABELS[r]}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Дата повторного визита</Label>
                      <Input
                        type="date"
                        value={conclusionForm.follow_up_date}
                        onChange={e => setConclusionForm(p => ({ ...p, follow_up_date: e.target.value }))}
                        className="rounded-lg h-9"
                      />
                    </div>
                  </div>
                  {hasPrediction && (
                    <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={conclusionForm.agreed_with_ai}
                        onChange={e => setConclusionForm(p => ({ ...p, agreed_with_ai: e.target.checked }))}
                        className="rounded"
                      />
                      Согласен с оценкой ИИ
                    </label>
                  )}
                  <div className="flex gap-2 justify-end pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-lg gap-1.5"
                      onClick={() => setEditingConclusion(false)}
                    >
                      <X className="w-3.5 h-3.5" /> Отмена
                    </Button>
                    <Button
                      size="sm"
                      className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg gap-1.5"
                      disabled={!conclusionForm.conclusion_text || createConclusionMutation.isPending || updateConclusionMutation.isPending}
                      onClick={submitConclusion}
                    >
                      <Check className="w-3.5 h-3.5" />
                      {(createConclusionMutation.isPending || updateConclusionMutation.isPending) ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

'use client'

import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/lib/api'
import { toast } from 'sonner'

interface PatientForm {
  first_name: string
  last_name: string
  middle_name: string
  date_of_birth: string
  gender: string
  phone: string
  address: string
  family_history_diabetes: string
}

export default function NewPatientPage() {
  const router = useRouter()
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<PatientForm>()

  async function onSubmit(data: PatientForm) {
    try {
      await api.post('/patients', {
        ...data,
        middle_name: data.middle_name || null,
        phone: data.phone || null,
        address: data.address || null,
        family_history_diabetes: data.family_history_diabetes === 'true',
      })
      toast.success('Пациент зарегистрирован')
      router.push('/doctor/patients')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Ошибка при создании пациента')
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/doctor/patients" className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Новый пациент</h1>
          <p className="text-sm text-gray-500">Регистрация карточки пациента</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Персональные данные</h2></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Фамилия *</Label>
                <Input className="rounded-lg" {...register('last_name', { required: 'Обязательное поле' })} />
                {errors.last_name && <p className="text-xs text-red-500">{errors.last_name.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Имя *</Label>
                <Input className="rounded-lg" {...register('first_name', { required: 'Обязательное поле' })} />
                {errors.first_name && <p className="text-xs text-red-500">{errors.first_name.message}</p>}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Отчество</Label>
              <Input className="rounded-lg" {...register('middle_name')} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Дата рождения *</Label>
                <Input type="date" className="rounded-lg" {...register('date_of_birth', { required: 'Обязательное поле' })} />
                {errors.date_of_birth && <p className="text-xs text-red-500">{errors.date_of_birth.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Пол *</Label>
                <Select onValueChange={(v) => { if (v) setValue('gender', v as string) }}>
                  <SelectTrigger className="rounded-lg">
                    <SelectValue placeholder="Выберите" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MALE">Мужской</SelectItem>
                    <SelectItem value="FEMALE">Женский</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Контакты</h2></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Телефон</Label>
              <Input type="tel" placeholder="+7 (900) 000-00-00" className="rounded-lg" {...register('phone')} />
            </div>
            <div className="space-y-1.5">
              <Label>Адрес</Label>
              <Input className="rounded-lg" {...register('address')} />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2"><h2 className="font-semibold text-gray-800">Анамнез</h2></CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              <Label>Семейный анамнез по сахарному диабету *</Label>
              <Select onValueChange={(v) => { if (v != null) setValue('family_history_diabetes', v as string) }} defaultValue="false">
                <SelectTrigger className="rounded-lg">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Не отягощён</SelectItem>
                  <SelectItem value="true">Отягощён (СД у родственников)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3 justify-end pt-2">
          <Button type="button" variant="outline" className="rounded-lg" onClick={() => router.back()}>Отмена</Button>
          <Button type="submit" disabled={isSubmitting} className="bg-[#4A6FA5] hover:bg-[#3d5d8f] rounded-lg">
            {isSubmitting ? 'Сохранение...' : 'Зарегистрировать'}
          </Button>
        </div>
      </form>
    </div>
  )
}

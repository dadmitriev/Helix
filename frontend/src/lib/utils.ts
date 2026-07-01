import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { LabOrderStatus, LabOrderPriority, RiskLevel } from "@/types"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export const STATUS_LABELS: Record<LabOrderStatus, string> = {
  ORDERED: 'Назначено',
  IN_PROGRESS: 'В работе',
  RESULTS_READY: 'Готово',
  CONCLUDED: 'Завершено',
}

export const STATUS_COLORS: Record<LabOrderStatus, string> = {
  ORDERED: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  RESULTS_READY: 'bg-green-100 text-green-800',
  CONCLUDED: 'bg-gray-100 text-gray-700',
}

export const PRIORITY_LABELS: Record<LabOrderPriority, string> = {
  ROUTINE: 'Плановое',
  URGENT: 'Срочное',
  EMERGENCY: 'Экстренное',
}

export const PRIORITY_COLORS: Record<LabOrderPriority, string> = {
  ROUTINE: 'bg-gray-100 text-gray-700',
  URGENT: 'bg-orange-100 text-orange-800',
  EMERGENCY: 'bg-red-100 text-red-800',
}

export const RISK_LABELS: Record<RiskLevel, string> = {
  LOW: 'Низкий',
  MODERATE: 'Умеренный',
  HIGH: 'Высокий',
}

export const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: 'bg-green-100 text-green-800',
  MODERATE: 'bg-yellow-100 text-yellow-800',
  HIGH: 'bg-red-100 text-red-800',
}

export const PANEL_LABELS: Record<string, string> = {
  GLUCOSE: 'Глюкоза',
  HBA1C: 'HbA1c',
  INSULIN: 'Инсулин',
  LIPID_PANEL: 'Липидный профиль',
  BLOOD_PRESSURE: 'Артериальное давление',
  ANTHROPOMETRY: 'Антропометрия',
}

export const ALL_PANELS = ['GLUCOSE', 'HBA1C', 'INSULIN', 'LIPID_PANEL', 'BLOOD_PRESSURE', 'ANTHROPOMETRY']

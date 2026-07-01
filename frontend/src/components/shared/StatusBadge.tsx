import { LabOrderStatus, LabOrderPriority } from '@/types'
import { STATUS_LABELS, STATUS_COLORS, PRIORITY_LABELS, PRIORITY_COLORS } from '@/lib/utils'
import { cn } from '@/lib/utils'

export function StatusBadge({ status }: { status: LabOrderStatus }) {
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', STATUS_COLORS[status])}>
      {STATUS_LABELS[status]}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: LabOrderPriority }) {
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', PRIORITY_COLORS[priority])}>
      {PRIORITY_LABELS[priority]}
    </span>
  )
}

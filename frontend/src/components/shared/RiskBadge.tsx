import { RiskLevel } from '@/types'
import { RISK_LABELS } from '@/lib/utils'
import { cn } from '@/lib/utils'

const RISK_STYLES: Record<RiskLevel, string> = {
  LOW: 'bg-[#22C55E]/15 text-[#15803d] border border-[#22C55E]/30',
  MODERATE: 'bg-[#F59E0B]/15 text-[#b45309] border border-[#F59E0B]/30',
  HIGH: 'bg-[#EF4444]/15 text-[#b91c1c] border border-[#EF4444]/30',
}

export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', RISK_STYLES[level], className)}>
      {RISK_LABELS[level]}
    </span>
  )
}

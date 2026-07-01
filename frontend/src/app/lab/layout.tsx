import { AppShell } from '@/components/layout/AppShell'

export default function LabLayout({ children }: { children: React.ReactNode }) {
  return <AppShell requiredRole={['LABORATORIAN', 'ADMIN']}>{children}</AppShell>
}

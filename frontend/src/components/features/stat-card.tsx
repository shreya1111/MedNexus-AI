import { Card } from '@/components/ui/card'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  icon: LucideIcon
  label: string
  value: string | number
  className?: string
}

export default function StatCard({ icon: Icon, label, value, className }: StatCardProps) {
  return (
    <Card className={cn('flex items-center gap-4 hover:scale-105 transition-transform', className)}>
      <div className="p-3 rounded-lg bg-primary-container/10">
        <Icon className="h-6 w-6 text-primary-container" />
      </div>
      <div className="flex-1">
        <p className="text-label-caps text-muted-foreground uppercase">{label}</p>
        <p className="text-headline-md font-mono-data font-bold text-foreground">{value}</p>
      </div>
    </Card>
  )
}

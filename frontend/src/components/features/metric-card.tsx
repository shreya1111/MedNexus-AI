import { Card } from '@/components/ui/card'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  trend?: 'up' | 'down'
  suffix?: string
  icon?: React.ReactNode
  className?: string
}

export default function MetricCard({
  title,
  value,
  change,
  trend,
  suffix,
  icon,
  className,
}: MetricCardProps) {
  return (
    <Card className={cn('flex flex-col gap-4', className)}>
      <div className="flex items-center justify-between">
        <span className="text-label-caps text-muted-foreground uppercase">
          {title}
        </span>
        {icon && <div className="text-primary-container">{icon}</div>}
      </div>

      <div className="flex items-end gap-2">
        <span className="text-display-lg-mobile font-mono-data font-bold text-foreground">
          {value}
        </span>
        {suffix && (
          <span className="text-body-lg text-muted-foreground mb-1">
            {suffix}
          </span>
        )}
      </div>

      {change !== undefined && (
        <div className="flex items-center gap-1">
          {trend === 'up' ? (
            <TrendingUp className="h-4 w-4 text-success" />
          ) : (
            <TrendingDown className="h-4 w-4 text-error" />
          )}
          <span
            className={cn(
              'text-body-sm font-semibold',
              trend === 'up' ? 'text-success' : 'text-error'
            )}
          >
            {change > 0 ? '+' : ''}
            {change}%
          </span>
          <span className="text-body-sm text-muted-foreground">
            vs last period
          </span>
        </div>
      )}
    </Card>
  )
}

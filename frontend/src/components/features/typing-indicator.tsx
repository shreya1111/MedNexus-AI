import { cn } from '@/lib/utils'

interface TypingIndicatorProps {
  className?: string
}

export default function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-1', className)}>
      <div className="h-2 w-2 rounded-full bg-primary-container animate-pulse-cyan" />
      <div className="h-2 w-2 rounded-full bg-primary-container animate-pulse-cyan [animation-delay:0.2s]" />
      <div className="h-2 w-2 rounded-full bg-primary-container animate-pulse-cyan [animation-delay:0.4s]" />
    </div>
  )
}

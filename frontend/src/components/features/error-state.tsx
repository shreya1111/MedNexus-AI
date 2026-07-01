import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
}

export default function ErrorState({
  title = 'Something went wrong',
  description = 'An error occurred while loading this content.',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 rounded-full bg-error-container/20 p-6">
        <AlertCircle className="h-12 w-12 text-error" />
      </div>
      <h3 className="text-headline-md font-semibold text-foreground">{title}</h3>
      <p className="mt-2 text-body-md text-muted-foreground max-w-md">{description}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-6">
          Try again
        </Button>
      )}
    </div>
  )
}

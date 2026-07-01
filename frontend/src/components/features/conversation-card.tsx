import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Copy, User, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ConversationCardProps {
  role: 'user' | 'assistant'
  content: string
  confidence?: number
  citations?: string[]
  timestamp?: string
  className?: string
}

export default function ConversationCard({
  role,
  content,
  confidence,
  citations,
  timestamp,
  className,
}: ConversationCardProps) {
  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'flex gap-4',
        isUser ? 'justify-end' : 'justify-start',
        className
      )}
    >
      {!isUser && (
        <Avatar>
          <AvatarFallback className="bg-secondary-container">
            <Bot className="h-5 w-5 text-secondary-foreground" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={cn('flex-1 max-w-3xl', isUser && 'flex justify-end')}>
        <Card
          className={cn(
            'p-4',
            isUser
              ? 'bg-primary-container/20 border-primary-container/40'
              : 'bg-surface-container'
          )}
        >
          {/* Message Content */}
          <div className="text-body-md text-foreground whitespace-pre-wrap">
            {content}
          </div>

          {/* Citations */}
          {citations && citations.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {citations.map((citation, idx) => (
                <Badge key={idx} variant="outline">
                  [{idx + 1}] {citation}
                </Badge>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="mt-4 flex items-center justify-between text-body-sm text-muted-foreground">
            <div className="flex items-center gap-3">
              {timestamp && <span>{timestamp}</span>}
              {confidence !== undefined && (
                <Badge variant="secondary">
                  Confidence: {(confidence * 100).toFixed(1)}%
                </Badge>
              )}
            </div>
            <Button variant="ghost" size="icon">
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>

      {isUser && (
        <Avatar>
          <AvatarFallback className="bg-primary-container">
            <User className="h-5 w-5 text-primary-foreground" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, ChevronDown } from 'lucide-react'
import { useState } from 'react'

interface CitationCardProps {
  source: string
  excerpt: string
  similarity?: number
  metadata?: Record<string, any>
}

export default function CitationCard({
  source,
  excerpt,
  similarity,
  metadata,
}: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <Card className="hover:border-primary-container/60">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex-1">
          <CardTitle className="text-body-md font-semibold">{source}</CardTitle>
          {similarity !== undefined && (
            <Badge variant="secondary" className="mt-2">
              {(similarity * 100).toFixed(1)}% match
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="icon" asChild>
          <a href="#" target="_blank" rel="noopener noreferrer">
            <ExternalLink className="h-4 w-4" />
          </a>
        </Button>
      </CardHeader>

      <CardContent>
        <p className="text-body-sm text-muted-foreground line-clamp-3">
          {excerpt}
        </p>

        {metadata && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-2"
          >
            {isExpanded ? 'Hide' : 'Show'} metadata
            <ChevronDown
              className={`ml-2 h-4 w-4 transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
            />
          </Button>
        )}

        {isExpanded && metadata && (
          <div className="mt-4 p-4 bg-surface-container-low rounded-lg">
            <pre className="text-mono-data text-body-sm">
              {JSON.stringify(metadata, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import ConversationCard from '@/components/features/conversation-card'
import TypingIndicator from '@/components/features/typing-indicator'
import EmptyState from '@/components/features/empty-state'
import { useSendMessage, useSessionHistory } from '@/hooks/useChat'
import { useChatStore } from '@/stores/chat-store'
import { Send, MessageSquare } from 'lucide-react'

export default function Chat() {
  const { sessionId } = useParams<{ sessionId?: string }>()
  const [message, setMessage] = useState('')
  
  const { 
    messages, 
    setMessages, 
    setCurrentSession,
    setIsLoading,
    isLoading 
  } = useChatStore()
  
  const sendMessage = useSendMessage()
  const { data: sessionHistory } = useSessionHistory(sessionId || null)

  // Load session history when sessionId changes
  useEffect(() => {
    if (sessionId) {
      setCurrentSession(sessionId)
    }
  }, [sessionId, setCurrentSession])

  useEffect(() => {
    if (sessionHistory) {
      setMessages(sessionHistory.messages)
    }
  }, [sessionHistory, setMessages])

  const handleSend = async () => {
    if (!message.trim() || isLoading) return
    
    const messageText = message
    setMessage('')
    setIsLoading(true)
    
    try {
      await sendMessage.mutateAsync(messageText)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-lg space-y-lg">
        {messages.length === 0 ? (
          <EmptyState
            icon={MessageSquare}
            title="Start a conversation"
            description="Ask any medical question and get evidence-based answers."
          />
        ) : (
          messages.map((msg, idx) => (
            <ConversationCard
              key={idx}
              role={msg.role}
              content={msg.content}
              confidence={msg.metadata?.confidence}
              citations={msg.metadata?.citations?.map(c => c.source)}
              timestamp={msg.timestamp}
            />
          ))
        )}
        {isLoading && (
          <div className="flex items-center gap-2">
            <TypingIndicator />
            <span className="text-body-sm text-muted-foreground">Thinking...</span>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-surface-container p-lg">
        <div className="flex gap-4">
          <Textarea
            placeholder="Type your medical question here..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-[80px]"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            size="icon"
            className="h-[80px] w-[80px]"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        <p className="mt-2 text-body-sm text-muted-foreground">
          Press Ctrl+Enter to send
        </p>
      </div>
    </div>
  )
}

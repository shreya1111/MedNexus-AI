import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import chatService, { ChatRequest } from '@/services/chat.service'
import { useChatStore } from '@/stores/chat-store'
import { useNotificationStore } from '@/stores/notification-store'

export function useSendMessage() {
  const { currentSessionId, addMessage, setCurrentSession } = useChatStore()
  const { addNotification } = useNotificationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (message: string) => {
      const request: ChatRequest = {
        message,
        session_id: currentSessionId || undefined,
      }
      return chatService.sendMessage(request)
    },
    onMutate: async (message) => {
      // Optimistically add user message
      addMessage({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      })
    },
    onSuccess: (data) => {
      // Update session ID if it's a new conversation
      if (!currentSessionId) {
        setCurrentSession(data.session_id)
      }

      // Add assistant message
      addMessage({
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
        metadata: {
          confidence: data.confidence,
          citations: data.citations,
          followup_questions: data.followup_questions,
        },
      })

      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        title: 'Message failed',
        description: error.message || 'Failed to send message.',
      })
    },
  })
}

export function useChatSessions() {
  return useQuery({
    queryKey: ['chatSessions'],
    queryFn: chatService.getChatSessions,
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useSessionHistory(sessionId: string | null) {
  return useQuery({
    queryKey: ['sessionHistory', sessionId],
    queryFn: () => chatService.getSessionHistory(sessionId!),
    enabled: !!sessionId,
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useDeleteSession() {
  const { currentSessionId, clearCurrentSession } = useChatStore()
  const { addNotification } = useNotificationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: chatService.deleteSession,
    onSuccess: (_, sessionId) => {
      // Clear current session if it was deleted
      if (currentSessionId === sessionId) {
        clearCurrentSession()
      }

      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
      
      addNotification({
        type: 'success',
        title: 'Session deleted',
        description: 'Chat session has been deleted.',
      })
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        title: 'Delete failed',
        description: error.message,
      })
    },
  })
}

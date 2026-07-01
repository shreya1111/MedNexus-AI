import { create } from 'zustand'

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
  metadata?: {
    confidence?: number
    citations?: Citation[]
    followup_questions?: string[]
  }
}

export interface Citation {
  content: string
  metadata: Record<string, any>
  score: number
  source: string
}

interface ChatState {
  currentSessionId: string | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  
  // Actions
  setCurrentSession: (sessionId: string | null) => void
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  clearCurrentSession: () => void
  setIsLoading: (isLoading: boolean) => void
  setIsStreaming: (isStreaming: boolean) => void
}

export const useChatStore = create<ChatState>()((set) => ({
  currentSessionId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,

  setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  setMessages: (messages) => set({ messages }),
  
  clearCurrentSession: () => set({
    currentSessionId: null,
    messages: [],
  }),
  
  setIsLoading: (isLoading) => set({ isLoading }),
  
  setIsStreaming: (isStreaming) => set({ isStreaming }),
}))

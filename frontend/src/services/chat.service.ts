import api from './api'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
  metadata?: Record<string, any>
}

export interface ChatRequest {
  message: string
  session_id?: string
  stream?: boolean
}

export interface ChatResponse {
  message: string
  session_id: string
  confidence: number
  followup_questions: string[]
  citations: Array<{
    content: string
    metadata: Record<string, any>
    score: number
    source: string
  }>
  metadata: Record<string, any>
  latency_ms: number
}

export interface SessionInfo {
  session_id: string
  message_count: number
  created_at: string
  last_accessed: string
  is_active: boolean
  metadata?: Record<string, any>
}

export interface ChatHistory {
  session_id: string
  messages: ChatMessage[]
  total_messages: number
  created_at: string
  last_accessed: string
}

export interface ChatHistoryList {
  sessions: SessionInfo[]
  total: number
}

const chatService = {
  async sendMessage(data: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', data)
    return response.data
  },

  async getChatSessions(): Promise<ChatHistoryList> {
    const response = await api.get<ChatHistoryList>('/chat/history')
    return response.data
  },

  async getSessionHistory(sessionId: string, limit?: number): Promise<ChatHistory> {
    const params = limit ? { limit } : {}
    const response = await api.get<ChatHistory>(`/chat/history/${sessionId}`, { params })
    return response.data
  },

  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/chat/history/${sessionId}`)
  },
}

export default chatService

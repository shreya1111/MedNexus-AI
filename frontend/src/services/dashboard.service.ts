import api from './api'

export interface DashboardStats {
  total_conversations: number
  total_messages: number
  knowledge_base_size: number
  avg_confidence: number
  recent_activity_7d: number
  total_users?: number
  last_updated: string
}

export interface UsageTrend {
  days: number
  data: Array<{
    date: string
    conversations: number
    messages: number
  }>
}

export interface SystemHealth {
  status: string
  database: string
  vector_db: string
  ai_service: string
  uptime_hours: number
  last_check: string
}

const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/dashboard/stats')
    return response.data
  },

  async getAllStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/dashboard/stats/all')
    return response.data
  },

  async getUsageTrend(days: number = 7): Promise<UsageTrend> {
    const response = await api.get<UsageTrend>('/dashboard/trend', {
      params: { days }
    })
    return response.data
  },

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await api.get<SystemHealth>('/dashboard/health')
    return response.data
  }
}

export default dashboardService

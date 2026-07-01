import api from './api'

// Types matching backend schemas
export interface UserListItem {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  last_login: string | null
  created_at: string
}

export interface UserList {
  users: UserListItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface UserDetail {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  last_login: string | null
  created_at: string
  updated_at: string
  statistics: {
    total_conversations: number
    total_messages: number
    total_documents: number
    total_reports: number
  }
}

export interface SystemStats {
  total_users: number
  active_users: number
  total_conversations: number
  total_messages: number
  total_documents: number
  total_reports: number
  total_searches: number
  avg_confidence: number
  avg_latency_ms: number
}

export interface SystemHealth {
  status: string
  database: string
  vector_db: string
  ai_service: string
  cpu_usage?: number
  memory_usage?: number
  disk_usage?: number
}

export interface ActivityLog {
  id: number
  user_id: number
  user_email: string
  action: string
  endpoint: string
  status_code: number
  timestamp: string
  latency_ms: number
}

export interface ActivityLogList {
  logs: ActivityLog[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

const adminService = {
  async getUsers(params?: {
    page?: number
    page_size?: number
    role?: string
    is_active?: boolean
  }): Promise<UserList> {
    const response = await api.get<UserList>('/api/v1/admin/users', { params })
    return response.data
  },

  async getUser(userId: number): Promise<UserDetail> {
    const response = await api.get<UserDetail>(`/api/v1/admin/users/${userId}`)
    return response.data
  },

  async updateUser(
    userId: number,
    data: {
      full_name?: string
      role?: string
      is_active?: boolean
      is_verified?: boolean
    }
  ): Promise<UserDetail> {
    const response = await api.put<UserDetail>(`/api/v1/admin/users/${userId}`, data)
    return response.data
  },

  async deleteUser(userId: number): Promise<void> {
    await api.delete(`/api/v1/admin/users/${userId}`)
  },

  async getSystemStats(): Promise<SystemStats> {
    const response = await api.get<SystemStats>('/api/v1/admin/stats')
    return response.data
  },

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await api.get<SystemHealth>('/api/v1/admin/health')
    return response.data
  },

  async getActivityLogs(params?: {
    page?: number
    page_size?: number
    user_id?: number
    endpoint?: string
    status_code?: number
  }): Promise<ActivityLogList> {
    const response = await api.get<ActivityLogList>('/api/v1/admin/logs', { params })
    return response.data
  },
}

export default adminService

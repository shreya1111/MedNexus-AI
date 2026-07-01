import api from './api'

// Types matching backend schemas
export interface ProfileStatistics {
  total_conversations: number
  total_messages: number
  total_documents: number
  total_reports: number
  member_since: string
  days_active: number
}

export interface Profile {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login: string | null
  statistics?: ProfileStatistics
}

export interface Settings {
  theme: 'light' | 'dark' | 'system'
  language: string
  notifications_enabled: boolean
  email_notifications: boolean
  ai_model: string
  retrieval_top_k: number
  chunk_size: number
  embedding_provider: string
}

const profileService = {
  async getProfile(): Promise<Profile> {
    const response = await api.get<Profile>('/api/v1/profile')
    return response.data
  },

  async updateProfile(data: {
    full_name?: string
    email?: string
  }): Promise<Profile> {
    const response = await api.put<Profile>('/api/v1/profile', data)
    return response.data
  },

  async changePassword(data: {
    current_password: string
    new_password: string
  }): Promise<void> {
    await api.post('/api/v1/profile/password', data)
  },

  async getSettings(): Promise<Settings> {
    const response = await api.get<Settings>('/api/v1/settings')
    return response.data
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    const response = await api.put<Settings>('/api/v1/settings', settings)
    return response.data
  },
}

export default profileService

import api from './api'

export interface UserSettings {
  theme: 'dark' | 'light'
  notifications: {
    email: boolean
    push: boolean
    digest: boolean
  }
  privacy: {
    show_profile: boolean
    share_analytics: boolean
  }
  api_keys: ApiKey[]
}

export interface ApiKey {
  id: string
  name: string
  key: string
  created_at: string
  last_used: string
}

const settingsService = {
  async getSettings(): Promise<UserSettings> {
    const response = await api.get('/api/v1/settings')
    return response.data
  },

  async updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
    const response = await api.put('/api/v1/settings', data)
    return response.data
  },

  async generateApiKey(name: string): Promise<ApiKey> {
    const response = await api.post('/api/v1/settings/api-keys', { name })
    return response.data
  },

  async revokeApiKey(keyId: string): Promise<void> {
    await api.delete(`/api/v1/settings/api-keys/${keyId}`)
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/api/v1/settings/password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}

export default settingsService

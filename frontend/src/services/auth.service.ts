import api from './api'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  full_name: string
  email: string
  password: string
  role: 'patient' | 'doctor' | 'researcher' | 'administrator'
}

export interface User {
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
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthResponse extends Token {
  user?: User
}

const authService = {
  async login(data: LoginRequest): Promise<Token> {
    const response = await api.post<Token>('/auth/login', data)
    
    // Store tokens
    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)
    
    return response.data
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },

  async logout(refreshToken: string): Promise<void> {
    try {
      await api.post('/auth/logout', { refresh_token: refreshToken })
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  },

  async refreshToken(refreshToken: string): Promise<Token> {
    const response = await api.post<Token>('/auth/refresh', { refresh_token: refreshToken })
    
    // Update stored tokens
    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)
    
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  async forgotPassword(email: string): Promise<void> {
    await api.post('/auth/forgot-password', { email })
  },

  async resetPassword(token: string, password: string): Promise<void> {
    await api.post('/auth/reset-password', { token, new_password: password })
  },
}

export default authService

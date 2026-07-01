import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: number
  email: string
  full_name: string
  role: 'patient' | 'doctor' | 'researcher' | 'administrator'
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  last_login: string | null
  created_at: string
  updated_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  
  // Actions
  setUser: (user: User | null) => void
  setTokens: (accessToken: string, refreshToken: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ 
        user, 
        isAuthenticated: !!user 
      }),
      
      setTokens: (accessToken, refreshToken) => {
        set({ 
          accessToken, 
          refreshToken,
          isAuthenticated: true
        })
        // Also store in localStorage for API interceptor
        localStorage.setItem('access_token', accessToken)
        localStorage.setItem('refresh_token', refreshToken)
      },
      
      clearAuth: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
        // Clear from localStorage
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

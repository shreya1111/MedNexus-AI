import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import authService, { LoginRequest, RegisterRequest, User } from '@/services/auth.service'
import { useAuthStore } from '@/stores/auth-store'
import { useNotificationStore } from '@/stores/notification-store'

export function useLogin() {
  const navigate = useNavigate()
  const { setUser, setTokens } = useAuthStore()
  const { addNotification } = useNotificationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authService.login,
    onSuccess: async (data) => {
      // Store tokens
      setTokens(data.access_token, data.refresh_token)
      
      // Fetch user data
      try {
        const user = await authService.getCurrentUser()
        setUser(user)
        queryClient.setQueryData(['currentUser'], user)
        
        addNotification({
          type: 'success',
          title: 'Welcome back!',
          description: 'You have successfully logged in.',
        })
        
        navigate('/dashboard')
      } catch (error) {
        addNotification({
          type: 'error',
          title: 'Login failed',
          description: 'Failed to fetch user data.',
        })
      }
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        title: 'Login failed',
        description: error.message || 'Invalid email or password.',
      })
    },
  })
}

export function useRegister() {
  const navigate = useNavigate()
  const { addNotification } = useNotificationStore()

  return useMutation({
    mutationFn: authService.register,
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Registration successful',
        description: 'Please log in with your credentials.',
      })
      navigate('/login')
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        title: 'Registration failed',
        description: error.message || 'Failed to create account.',
      })
    },
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const { clearAuth, refreshToken } = useAuthStore()
  const { addNotification } = useNotificationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await authService.logout(refreshToken)
      }
    },
    onSettled: () => {
      clearAuth()
      queryClient.clear()
      navigate('/login')
      addNotification({
        type: 'info',
        title: 'Logged out',
        description: 'You have been logged out successfully.',
      })
    },
  })
}

export function useCurrentUser() {
  const { isAuthenticated, user } = useAuthStore()

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: authService.getCurrentUser,
    enabled: isAuthenticated && !user,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })
}

export function useForgotPassword() {
  const { addNotification } = useNotificationStore()

  return useMutation({
    mutationFn: authService.forgotPassword,
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Email sent',
        description: 'Check your email for password reset instructions.',
      })
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        title: 'Failed to send email',
        description: error.message,
      })
    },
  })
}

export function useResetPassword() {
  const navigate = useNavigate()
  const { addNotification } = useNotificationStore()

  return useMutation({
    mutationFn: ({ token, password }: { token: string; password: string }) =>
      authService.resetPassword(token, password),
    onSuccess: () => {
      addNotification({
        type: 'success',
        title: 'Password reset',
        description: 'Your password has been reset. Please log in.',
      })
      navigate('/login')
    },
    onError: (error: Error) => {
      addNotification({
        type: 'error',
        title: 'Password reset failed',
        description: error.message,
      })
    },
  })
}

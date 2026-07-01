/**
 * React Query hooks for Admin
 * 
 * Provides hooks for system administration
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import adminService from '@/services/admin.service'
import { toast } from 'sonner'

// Query keys
export const adminKeys = {
  all: ['admin'] as const,
  users: (params?: any) => [...adminKeys.all, 'users', params] as const,
  user: (id: number) => [...adminKeys.all, 'user', id] as const,
  stats: () => [...adminKeys.all, 'stats'] as const,
  health: () => [...adminKeys.all, 'health'] as const,
  logs: (params?: any) => [...adminKeys.all, 'logs', params] as const,
}

/**
 * Hook to get users list
 */
export function useAdminUsers(params?: {
  page?: number
  page_size?: number
  role?: string
  is_active?: boolean
}) {
  return useQuery({
    queryKey: adminKeys.users(params),
    queryFn: () => adminService.getUsers(params),
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to get single user details
 */
export function useAdminUser(userId: number, enabled: boolean = true) {
  return useQuery({
    queryKey: adminKeys.user(userId),
    queryFn: () => adminService.getUser(userId),
    enabled: enabled && !!userId,
    staleTime: 60000,
  })
}

/**
 * Hook to update user
 */
export function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: number
      data: {
        full_name?: string
        role?: string
        is_active?: boolean
        is_verified?: boolean
      }
    }) => adminService.updateUser(userId, data),
    onSuccess: (data, variables) => {
      toast.success('User updated successfully')
      
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: adminKeys.users() })
      queryClient.invalidateQueries({ queryKey: adminKeys.user(variables.userId) })
    },
    onError: (error: any) => {
      const message = error?.response?.data?.error || 'Failed to update user'
      toast.error(message)
    },
  })
}

/**
 * Hook to delete user
 */
export function useDeleteUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: number) => adminService.deleteUser(userId),
    onMutate: async (userId) => {
      toast.loading('Deleting user...', { id: 'delete-user' })
    },
    onSuccess: () => {
      toast.dismiss('delete-user')
      toast.success('User deleted successfully')
      
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: adminKeys.users() })
      queryClient.invalidateQueries({ queryKey: adminKeys.stats() })
    },
    onError: (error: any) => {
      toast.dismiss('delete-user')
      const message = error?.response?.data?.error || 'Failed to delete user'
      toast.error(message)
    },
  })
}

/**
 * Hook to get system statistics
 */
export function useSystemStats() {
  return useQuery({
    queryKey: adminKeys.stats(),
    queryFn: adminService.getSystemStats,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  })
}

/**
 * Hook to get system health
 */
export function useSystemHealth() {
  return useQuery({
    queryKey: adminKeys.health(),
    queryFn: adminService.getSystemHealth,
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

/**
 * Hook to get activity logs
 */
export function useActivityLogs(params?: {
  page?: number
  page_size?: number
  user_id?: number
  endpoint?: string
  status_code?: number
}) {
  return useQuery({
    queryKey: adminKeys.logs(params),
    queryFn: () => adminService.getActivityLogs(params),
    staleTime: 30000,
  })
}

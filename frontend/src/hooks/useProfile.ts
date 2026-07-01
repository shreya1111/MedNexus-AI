/**
 * React Query hooks for Profile and Settings
 * 
 * Provides hooks for user profile and settings management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import profileService, { Settings } from '@/services/profile.service'
import { toast } from 'sonner'

// Query keys
export const profileKeys = {
  all: ['profile'] as const,
  profile: () => [...profileKeys.all, 'info'] as const,
  settings: () => [...profileKeys.all, 'settings'] as const,
}

/**
 * Hook to get user profile
 */
export function useProfile() {
  return useQuery({
    queryKey: profileKeys.profile(),
    queryFn: profileService.getProfile,
    staleTime: 300000, // 5 minutes
    refetchOnWindowFocus: true,
  })
}

/**
 * Hook to update profile
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { full_name?: string; email?: string }) =>
      profileService.updateProfile(data),
    onSuccess: (data) => {
      toast.success('Profile updated successfully')
      
      // Update cache
      queryClient.setQueryData(profileKeys.profile(), data)
      
      // Also invalidate to refetch with new stats
      queryClient.invalidateQueries({ queryKey: profileKeys.profile() })
    },
    onError: (error: any) => {
      const message = error?.response?.data?.error || 'Failed to update profile'
      toast.error(message)
    },
  })
}

/**
 * Hook to change password
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      profileService.changePassword(data),
    onSuccess: () => {
      toast.success('Password changed successfully')
    },
    onError: (error: any) => {
      const message = error?.response?.data?.error || 'Failed to change password'
      toast.error(message)
    },
  })
}

/**
 * Hook to get user settings
 */
export function useSettings() {
  return useQuery({
    queryKey: profileKeys.settings(),
    queryFn: profileService.getSettings,
    staleTime: 300000, // 5 minutes
  })
}

/**
 * Hook to update settings
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (settings: Partial<Settings>) =>
      profileService.updateSettings(settings),
    onMutate: async (newSettings) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: profileKeys.settings() })

      // Snapshot previous value
      const previousSettings = queryClient.getQueryData(profileKeys.settings())

      // Optimistically update settings
      queryClient.setQueryData(profileKeys.settings(), (old: any) => ({
        ...old,
        ...newSettings,
      }))

      return { previousSettings }
    },
    onSuccess: (data) => {
      toast.success('Settings updated successfully')
      
      // Update cache with server response
      queryClient.setQueryData(profileKeys.settings(), data)
    },
    onError: (error: any, newSettings, context) => {
      // Rollback on error
      if (context?.previousSettings) {
        queryClient.setQueryData(profileKeys.settings(), context.previousSettings)
      }

      const message = error?.response?.data?.error || 'Failed to update settings'
      toast.error(message)
    },
  })
}

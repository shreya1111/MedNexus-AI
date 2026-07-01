import { useQuery } from '@tanstack/react-query'
import dashboardService from '@/services/dashboard.service'

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: dashboardService.getStats,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}

export function useAllDashboardStats() {
  return useQuery({
    queryKey: ['allDashboardStats'],
    queryFn: dashboardService.getAllStats,
    staleTime: 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  })
}

export function useUsageTrend(days: number = 7) {
  return useQuery({
    queryKey: ['usageTrend', days],
    queryFn: () => dashboardService.getUsageTrend(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: dashboardService.getSystemHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  })
}

/**
 * React Query hooks for Medical Reports
 * 
 * Provides hooks for report upload, listing, analysis, and deletion
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import reportsService, { Report, UploadReportResponse } from '@/services/reports.service'
import { toast } from 'sonner'

// Query keys
export const reportsKeys = {
  all: ['reports'] as const,
  lists: () => [...reportsKeys.all, 'list'] as const,
  list: () => [...reportsKeys.lists()] as const,
  details: () => [...reportsKeys.all, 'detail'] as const,
  detail: (id: string) => [...reportsKeys.details(), id] as const,
}

/**
 * Hook to get all reports
 */
export function useReports() {
  return useQuery({
    queryKey: reportsKeys.list(),
    queryFn: reportsService.getReports,
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  })
}

/**
 * Hook to get a single report
 */
export function useReport(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: reportsKeys.detail(id),
    queryFn: () => reportsService.getReport(id),
    enabled: enabled && !!id,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook to upload a report
 */
export function useUploadReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => reportsService.uploadReport(file),
    onMutate: async () => {
      // Show loading toast
      toast.loading('Uploading report...', { id: 'upload-report' })
    },
    onSuccess: (data: UploadReportResponse) => {
      // Dismiss loading toast
      toast.dismiss('upload-report')
      
      // Show success toast
      if (data.status === 'completed') {
        toast.success('Report uploaded and processed successfully')
      } else if (data.status === 'processing') {
        toast.info('Report uploaded. Processing in progress...')
      } else {
        toast.warning('Report uploaded but processing failed')
      }

      // Invalidate and refetch reports list
      queryClient.invalidateQueries({ queryKey: reportsKeys.list() })
    },
    onError: (error: any) => {
      // Dismiss loading toast
      toast.dismiss('upload-report')
      
      // Show error toast
      const message = error?.response?.data?.error || 'Failed to upload report'
      toast.error(message)
    },
  })
}

/**
 * Hook to analyze a report
 */
export function useAnalyzeReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reportId: string) => reportsService.analyzeReport(reportId),
    onMutate: async () => {
      // Show loading toast
      toast.loading('Analyzing report...', { id: 'analyze-report' })
    },
    onSuccess: (data, reportId) => {
      // Dismiss loading toast
      toast.dismiss('analyze-report')
      
      // Show success toast
      toast.success('Report analyzed successfully')

      // Invalidate report detail to refetch with new analysis
      queryClient.invalidateQueries({ queryKey: reportsKeys.detail(reportId) })
    },
    onError: (error: any) => {
      // Dismiss loading toast
      toast.dismiss('analyze-report')
      
      // Show error toast
      const message = error?.response?.data?.error || 'Failed to analyze report'
      toast.error(message)
    },
  })
}

/**
 * Hook to delete a report
 */
export function useDeleteReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reportId: string) => reportsService.deleteReport(reportId),
    onMutate: async (reportId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: reportsKeys.list() })

      // Snapshot previous value
      const previousReports = queryClient.getQueryData<Report[]>(reportsKeys.list())

      // Optimistically update list
      queryClient.setQueryData<Report[]>(reportsKeys.list(), (old) => {
        if (!old) return []
        return old.filter((report) => report.id !== reportId)
      })

      // Show loading toast
      toast.loading('Deleting report...', { id: 'delete-report' })

      return { previousReports }
    },
    onSuccess: () => {
      // Dismiss loading toast
      toast.dismiss('delete-report')
      
      // Show success toast
      toast.success('Report deleted successfully')
    },
    onError: (error: any, reportId, context) => {
      // Dismiss loading toast
      toast.dismiss('delete-report')
      
      // Rollback on error
      if (context?.previousReports) {
        queryClient.setQueryData(reportsKeys.list(), context.previousReports)
      }

      // Show error toast
      const message = error?.response?.data?.error || 'Failed to delete report'
      toast.error(message)
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: reportsKeys.list() })
    },
  })
}

/**
 * Hook to check if a report is being uploaded
 */
export function useIsUploading() {
  const queryClient = useQueryClient()
  return queryClient.isMutating({ mutationKey: ['upload-report'] }) > 0
}

/**
 * Hook to check if a report is being analyzed
 */
export function useIsAnalyzing() {
  const queryClient = useQueryClient()
  return queryClient.isMutating({ mutationKey: ['analyze-report'] }) > 0
}

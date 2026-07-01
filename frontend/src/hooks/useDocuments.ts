/**
 * React Query hooks for Documents
 * 
 * Provides hooks for document management in knowledge base
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import documentsService, { DocumentFilterParams, DocumentInfo } from '@/services/documents.service'
import { toast } from 'sonner'

// Query keys
export const documentsKeys = {
  all: ['documents'] as const,
  lists: () => [...documentsKeys.all, 'list'] as const,
  list: (params?: DocumentFilterParams) => [...documentsKeys.lists(), params] as const,
  details: () => [...documentsKeys.all, 'detail'] as const,
  detail: (id: number) => [...documentsKeys.details(), id] as const,
  stats: () => [...documentsKeys.all, 'stats'] as const,
}

/**
 * Hook to get documents with filtering
 */
export function useDocuments(params?: DocumentFilterParams) {
  return useQuery({
    queryKey: documentsKeys.list(params),
    queryFn: () => documentsService.getDocuments(params),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  })
}

/**
 * Hook to get document statistics
 */
export function useDocumentStats() {
  return useQuery({
    queryKey: documentsKeys.stats(),
    queryFn: documentsService.getStats,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook to get a single document
 */
export function useDocument(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: documentsKeys.detail(id),
    queryFn: () => documentsService.getDocument(id),
    enabled: enabled && !!id,
    staleTime: 60000,
  })
}

/**
 * Hook to upload a document
 */
export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, source }: { file: File; source?: string }) =>
      documentsService.uploadDocument(file, source),
    onMutate: async () => {
      toast.loading('Uploading document...', { id: 'upload-document' })
    },
    onSuccess: (data) => {
      toast.dismiss('upload-document')
      
      if (data.status === 'completed') {
        toast.success('Document uploaded and processed successfully')
      } else if (data.status === 'processing') {
        toast.info('Document uploaded. Processing in progress...')
      } else {
        toast.warning('Document uploaded but processing may have failed')
      }

      // Invalidate documents list
      queryClient.invalidateQueries({ queryKey: documentsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() })
    },
    onError: (error: any) => {
      toast.dismiss('upload-document')
      const message = error?.response?.data?.error || 'Failed to upload document'
      toast.error(message)
    },
  })
}

/**
 * Hook to rename a document
 */
export function useRenameDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, newFilename }: { id: number; newFilename: string }) =>
      documentsService.renameDocument(id, newFilename),
    onSuccess: (data) => {
      toast.success('Document renamed successfully')
      
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: documentsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: documentsKeys.detail(data.id) })
    },
    onError: (error: any) => {
      const message = error?.response?.data?.error || 'Failed to rename document'
      toast.error(message)
    },
  })
}

/**
 * Hook to download a document
 */
export function useDownloadDocument() {
  return useMutation({
    mutationFn: async ({ id, filename }: { id: number; filename: string }) => {
      const blob = await documentsService.downloadDocument(id)
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      return { id, filename }
    },
    onSuccess: (data) => {
      toast.success(`Downloading ${data.filename}`)
    },
    onError: (error: any) => {
      const message = error?.response?.data?.error || 'Failed to download document'
      toast.error(message)
    },
  })
}

/**
 * Hook to delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: number) => documentsService.deleteDocument(documentId),
    onMutate: async (documentId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: documentsKeys.lists() })

      // Snapshot previous value
      const previousDocuments = queryClient.getQueryData(documentsKeys.lists())

      // Optimistically update lists
      queryClient.setQueriesData({ queryKey: documentsKeys.lists() }, (old: any) => {
        if (!old) return old
        return {
          ...old,
          documents: old.documents.filter((doc: DocumentInfo) => doc.id !== documentId),
          total: old.total - 1,
        }
      })

      toast.loading('Deleting document...', { id: 'delete-document' })

      return { previousDocuments }
    },
    onSuccess: () => {
      toast.dismiss('delete-document')
      toast.success('Document deleted successfully')
    },
    onError: (error: any, documentId, context) => {
      toast.dismiss('delete-document')
      
      // Rollback on error
      if (context?.previousDocuments) {
        queryClient.setQueryData(documentsKeys.lists(), context.previousDocuments)
      }

      const message = error?.response?.data?.error || 'Failed to delete document'
      toast.error(message)
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: documentsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: documentsKeys.stats() })
    },
  })
}

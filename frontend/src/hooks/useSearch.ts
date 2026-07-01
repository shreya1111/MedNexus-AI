import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import searchService, { SearchRequest, HybridSearchRequest } from '@/services/search.service'
import { useSearchStore } from '@/stores/search-store'
import { useNotificationStore } from '@/stores/notification-store'

export function useSearch() {
  const { setResults, setIsSearching, addToHistory } = useSearchStore()
  const { addNotification } = useNotificationStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SearchRequest) => searchService.search(data),
    onMutate: () => {
      setIsSearching(true)
    },
    onSuccess: (data) => {
      setResults(data.results)
      addToHistory(data.query)
      setIsSearching(false)
    },
    onError: (error: Error) => {
      setIsSearching(false)
      addNotification({
        type: 'error',
        title: 'Search failed',
        description: error.message || 'Failed to search knowledge base.',
      })
    },
  })
}

export function useVectorSearch() {
  const { setResults, setIsSearching, addToHistory } = useSearchStore()
  const { addNotification } = useNotificationStore()

  return useMutation({
    mutationFn: ({ query, topK }: { query: string; topK?: number }) =>
      searchService.vectorSearch(query, topK),
    onMutate: () => {
      setIsSearching(true)
    },
    onSuccess: (data) => {
      setResults(data.results)
      addToHistory(data.query)
      setIsSearching(false)
    },
    onError: (error: Error) => {
      setIsSearching(false)
      addNotification({
        type: 'error',
        title: 'Search failed',
        description: error.message,
      })
    },
  })
}

export function useHybridSearch() {
  const { setResults, setIsSearching, addToHistory } = useSearchStore()
  const { addNotification } = useNotificationStore()

  return useMutation({
    mutationFn: (data: HybridSearchRequest) => searchService.hybridSearch(data),
    onMutate: () => {
      setIsSearching(true)
    },
    onSuccess: (data) => {
      setResults(data.results)
      addToHistory(data.query)
      setIsSearching(false)
    },
    onError: (error: Error) => {
      setIsSearching(false)
      addNotification({
        type: 'error',
        title: 'Search failed',
        description: error.message,
      })
    },
  })
}

export function useSearchStats() {
  return useQuery({
    queryKey: ['searchStats'],
    queryFn: searchService.getStats,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

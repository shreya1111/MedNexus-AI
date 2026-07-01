import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SearchFilters {
  topK: number
  vectorWeight: number
  bm25Weight: number
  sources: string[]
}

interface SearchResult {
  chunk_id: string
  document: string
  content: string
  similarity: number
  metadata: Record<string, any>
}

interface SearchState {
  query: string
  history: string[]
  filters: SearchFilters
  results: SearchResult[]
  isSearching: boolean
  
  setQuery: (query: string) => void
  addToHistory: (query: string) => void
  clearHistory: () => void
  setFilters: (filters: Partial<SearchFilters>) => void
  resetFilters: () => void
  setResults: (results: SearchResult[]) => void
  setIsSearching: (isSearching: boolean) => void
}

const defaultFilters: SearchFilters = {
  topK: 10,
  vectorWeight: 0.7,
  bm25Weight: 0.3,
  sources: [],
}

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      query: '',
      history: [],
      filters: defaultFilters,
      results: [],
      isSearching: false,
      
      setQuery: (query) => set({ query }),
      addToHistory: (query) =>
        set((state) => ({
          history: [query, ...state.history.filter((q) => q !== query)].slice(0, 10),
        })),
      clearHistory: () => set({ history: [] }),
      setFilters: (newFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
        })),
      resetFilters: () => set({ filters: defaultFilters }),
      setResults: (results) => set({ results }),
      setIsSearching: (isSearching) => set({ isSearching }),
    }),
    {
      name: 'search-storage',
      partialize: (state) => ({
        history: state.history,
        filters: state.filters,
      }),
    }
  )
)

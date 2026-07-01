import api from './api'

export interface SearchRequest {
  query: string
  top_k?: number
  filters?: Record<string, any>
}

export interface HybridSearchRequest extends SearchRequest {
  vector_weight?: number
  bm25_weight?: number
}

export interface SearchResult {
  chunk_id: string
  document: string
  content: string
  similarity: number
  metadata: Record<string, any>
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  total_results: number
  processing_time_ms: number
  weights?: {
    vector: number
    bm25: number
  }
}

export interface SearchStats {
  total_documents: number
  collection_name: string
  embedding_dimension: number
}

const searchService = {
  async search(data: SearchRequest): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>('/search', data)
    return response.data
  },

  async vectorSearch(query: string, topK: number = 10): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>('/search/vector', {
      query,
      top_k: topK
    })
    return response.data
  },

  async hybridSearch(data: HybridSearchRequest): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>('/search/hybrid', {
      query: data.query,
      top_k: data.top_k || 10,
      vector_weight: data.vector_weight || 0.7,
      bm25_weight: data.bm25_weight || 0.3,
      filters: data.filters
    })
    return response.data
  },

  async getStats(): Promise<SearchStats> {
    const response = await api.get<SearchStats>('/search/stats')
    return response.data
  }
}

export default searchService

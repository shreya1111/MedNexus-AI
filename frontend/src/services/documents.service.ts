import api from './api'

// Types matching backend schemas
export interface DocumentInfo {
  id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  is_processed: boolean
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  source?: string
  created_at: string
  updated_at: string
}

export interface DocumentDetail extends DocumentInfo {
  processing_error?: string
  metadata?: Record<string, any>
  checksum?: string
}

export interface DocumentList {
  documents: DocumentInfo[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface DocumentUploadResponse {
  id: number
  filename: string
  status: string
  message: string
}

export interface DocumentStats {
  total_documents: number
  processed_documents: number
  pending_documents: number
  total_size_bytes: number
  by_type: Record<string, number>
}

export interface DocumentFilterParams {
  page?: number
  page_size?: number
  mime_type?: string
  source?: string
  is_processed?: boolean
  date_from?: string
  date_to?: string
}

const documentsService = {
  async uploadDocument(file: File, source?: string): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const params = source ? { source } : {}
    
    const response = await api.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params,
    })
    return response.data
  },

  async getDocuments(params?: DocumentFilterParams): Promise<DocumentList> {
    const response = await api.get<DocumentList>('/api/v1/documents', { params })
    return response.data
  },

  async getDocument(id: number): Promise<DocumentDetail> {
    const response = await api.get<DocumentDetail>(`/api/v1/documents/${id}`)
    return response.data
  },

  async renameDocument(id: number, newFilename: string): Promise<DocumentDetail> {
    const response = await api.put<DocumentDetail>(`/api/v1/documents/${id}/rename`, {
      new_filename: newFilename,
    })
    return response.data
  },

  async downloadDocument(id: number): Promise<Blob> {
    const response = await api.get(`/api/v1/documents/${id}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  async deleteDocument(id: number): Promise<void> {
    await api.delete(`/api/v1/documents/${id}`)
  },

  async getStats(): Promise<DocumentStats> {
    const response = await api.get<DocumentStats>('/api/v1/documents/stats')
    return response.data
  },
}

export default documentsService

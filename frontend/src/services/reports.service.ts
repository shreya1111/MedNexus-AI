import api from './api'

// Types matching backend schemas
export interface ReportAnalysis {
  summary: string
  findings: string[]
  recommendations: string[]
  risks: string[]
  confidence: number
}

export interface Report {
  id: number
  filename: string
  original_filename: string
  file_size: number
  mime_type: string
  is_processed: boolean
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  processing_error?: string
  analysis?: ReportAnalysis
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface UploadReportResponse {
  id: number
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message: string
}

export interface ReportList {
  reports: Report[]
  total: number
}

const reportsService = {
  async uploadReport(file: File): Promise<UploadReportResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/api/v1/reports/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async getReports(): Promise<Report[]> {
    const response = await api.get<ReportList>('/api/v1/reports')
    return response.data.reports
  },

  async getReport(id: string): Promise<Report> {
    const response = await api.get<Report>(`/api/v1/reports/${id}`)
    return response.data
  },

  async analyzeReport(
    id: string,
    includeRecommendations: boolean = true,
    includeRisks: boolean = true
  ): Promise<ReportAnalysis> {
    const response = await api.post<ReportAnalysis>(
      `/api/v1/reports/${id}/analyze`,
      null,
      {
        params: {
          include_recommendations: includeRecommendations,
          include_risks: includeRisks,
        },
      }
    )
    return response.data
  },

  async deleteReport(id: string): Promise<void> {
    await api.delete(`/api/v1/reports/${id}`)
  },
}

export default reportsService

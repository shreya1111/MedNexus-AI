import { useState, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import EmptyState from '@/components/features/empty-state'
import ErrorState from '@/components/features/error-state'
import Skeleton from '@/components/ui/skeleton'
import { 
  FileText, 
  Upload, 
  Download, 
  Trash2, 
  Brain, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { useReports, useUploadReport, useDeleteReport, useAnalyzeReport } from '@/hooks/useReports'
import { Report } from '@/services/reports.service'
import { formatDistanceToNow } from 'date-fns'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export default function Reports() {
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [isAnalysisDialogOpen, setIsAnalysisDialogOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: reports, isLoading, isError, error, refetch } = useReports()
  const uploadMutation = useUploadReport()
  const deleteMutation = useDeleteReport()
  const analyzeMutation = useAnalyzeReport()

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]

    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a PDF, TXT, DOC, or DOCX file')
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB')
      return
    }

    await uploadMutation.mutateAsync(file)

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (reportId: number) => {
    if (!confirm('Are you sure you want to delete this report?')) return
    await deleteMutation.mutateAsync(String(reportId))
  }

  const handleAnalyze = async (report: Report) => {
    setSelectedReport(report)
    
    if (report.analysis) {
      // Already analyzed, just show results
      setIsAnalysisDialogOpen(true)
    } else {
      // Analyze first
      try {
        await analyzeMutation.mutateAsync(String(report.id))
        // Refetch to get updated report with analysis
        await refetch()
        setIsAnalysisDialogOpen(true)
      } catch (error) {
        console.error('Analysis failed:', error)
      }
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-success" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />
      case 'processing':
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Processed</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      case 'processing':
        return <Badge variant="default">Processing</Badge>
      default:
        return <Badge variant="secondary">Pending</Badge>
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  if (isLoading) {
    return (
      <div className="space-y-lg">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Skeleton className="h-10 w-40" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-lg">
              <Skeleton className="h-6 w-3/4 mb-4" />
              <Skeleton className="h-4 w-1/2 mb-2" />
              <Skeleton className="h-4 w-2/3" />
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-display-lg-mobile font-bold text-foreground">Medical Reports</h1>
            <p className="text-body-md text-muted-foreground mt-2">
              Upload and analyze medical reports with AI.
            </p>
          </div>
        </div>

        <ErrorState
          title="Failed to load reports"
          message={error?.message || 'An error occurred'}
          onRetry={refetch}
        />
      </div>
    )
  }

  return (
    <div className="space-y-lg">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg-mobile font-bold text-foreground">Medical Reports</h1>
          <p className="text-body-md text-muted-foreground mt-2">
            Upload and analyze medical reports with AI.
          </p>
        </div>
        <Button onClick={handleUploadClick} disabled={uploadMutation.isPending}>
          {uploadMutation.isPending ? (
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          ) : (
            <Upload className="mr-2 h-5 w-5" />
          )}
          Upload Report
        </Button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.doc,.docx"
        onChange={handleFileChange}
        className="hidden"
      />

      {!reports || reports.length === 0 ? (
        <Card className="p-2xl">
          <EmptyState
            icon={FileText}
            title="No reports yet"
            description="Upload your first medical report to get AI-powered insights."
            action={{
              label: 'Upload Report',
              onClick: handleUploadClick,
            }}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
          {reports.map((report) => (
            <Card key={report.id} className="p-lg hover:shadow-md transition-shadow">
              <div className="space-y-md">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-5 w-5 text-primary flex-shrink-0" />
                      <h3 className="font-semibold text-foreground truncate">
                        {report.original_filename}
                      </h3>
                    </div>
                    {getStatusBadge(report.processing_status)}
                  </div>
                </div>

                {/* Info */}
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Size:</span>
                    <span className="font-medium">{formatFileSize(report.file_size)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Uploaded:</span>
                    <span className="font-medium">
                      {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  {report.analysis && (
                    <div className="flex items-center justify-between">
                      <span>Confidence:</span>
                      <span className="font-medium">
                        {(report.analysis.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Error Message */}
                {report.processing_status === 'failed' && report.processing_error && (
                  <div className="flex items-start gap-2 p-2 bg-destructive/10 rounded-md">
                    <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-destructive">{report.processing_error}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2 border-t">
                  {report.is_processed && report.processing_status === 'completed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleAnalyze(report)}
                      disabled={analyzeMutation.isPending}
                    >
                      {analyzeMutation.isPending ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Brain className="h-4 w-4 mr-2" />
                      )}
                      {report.analysis ? 'View Analysis' : 'Analyze'}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(report.id)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Analysis Dialog */}
      <Dialog open={isAnalysisDialogOpen} onOpenChange={setIsAnalysisDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Medical Report Analysis</DialogTitle>
            <DialogDescription>
              {selectedReport?.original_filename}
            </DialogDescription>
          </DialogHeader>

          {selectedReport?.analysis && (
            <div className="space-y-lg">
              {/* Confidence Score */}
              <div className="flex items-center justify-between p-md bg-primary/5 rounded-lg">
                <span className="text-sm font-medium">Confidence Score</span>
                <Badge variant="default">
                  {(selectedReport.analysis.confidence * 100).toFixed(0)}%
                </Badge>
              </div>

              {/* Summary */}
              <div>
                <h3 className="font-semibold mb-2">Summary</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {selectedReport.analysis.summary}
                </p>
              </div>

              {/* Findings */}
              {selectedReport.analysis.findings.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Key Findings</h3>
                  <ul className="space-y-2">
                    {selectedReport.analysis.findings.map((finding, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-success flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-muted-foreground">{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {selectedReport.analysis.recommendations.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Recommendations</h3>
                  <ul className="space-y-2">
                    {selectedReport.analysis.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <Brain className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-muted-foreground">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Risks */}
              {selectedReport.analysis.risks.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Risk Factors</h3>
                  <ul className="space-y-2">
                    {selectedReport.analysis.risks.map((risk, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-warning flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-muted-foreground">{risk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

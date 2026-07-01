import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import EmptyState from '@/components/features/empty-state'
import ErrorState from '@/components/features/error-state'
import Skeleton from '@/components/ui/skeleton'
import { 
  FolderOpen, 
  Upload, 
  FileText, 
  Download, 
  Trash2, 
  Edit2,
  CheckCircle,
  XCircle,
  Clock,
  Loader2
} from 'lucide-react'
import { useDocuments, useUploadDocument, useDeleteDocument, useDownloadDocument, useDocumentStats } from '@/hooks/useDocuments'
import { formatDistanceToNow } from 'date-fns'
import StatCard from '@/components/features/stat-card'

export default function Documents() {
  const [page, setPage] = useState(1)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data, isLoading, isError, error, refetch } = useDocuments({ page, page_size: 20 })
  const { data: stats } = useDocumentStats()
  const uploadMutation = useUploadDocument()
  const deleteMutation = useDeleteDocument()
  const downloadMutation = useDownloadDocument()

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
      'text/markdown',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]

    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a PDF, TXT, MD, DOC, or DOCX file')
      return
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB')
      return
    }

    await uploadMutation.mutateAsync({ file, source: 'manual_upload' })

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (documentId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return
    await deleteMutation.mutateAsync(documentId)
  }

  const handleDownload = async (documentId: number, filename: string) => {
    await downloadMutation.mutateAsync({ id: documentId, filename })
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
          <Skeleton className="h-10 w-48" />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-lg">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>

        {/* Documents grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40" />
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
            <h1 className="text-display-lg-mobile font-bold text-foreground">Documents</h1>
            <p className="text-body-md text-muted-foreground mt-2">
              Manage your knowledge base documents.
            </p>
          </div>
        </div>

        <ErrorState
          title="Failed to load documents"
          message={error?.message || 'An error occurred'}
          onRetry={refetch}
        />
      </div>
    )
  }

  const documents = data?.documents || []

  return (
    <div className="space-y-lg">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg-mobile font-bold text-foreground">Documents</h1>
          <p className="text-body-md text-muted-foreground mt-2">
            Manage your knowledge base documents.
          </p>
        </div>
        <Button onClick={handleUploadClick} disabled={uploadMutation.isPending}>
          {uploadMutation.isPending ? (
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          ) : (
            <Upload className="mr-2 h-5 w-5" />
          )}
          Upload Document
        </Button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md,.doc,.docx"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-lg">
          <StatCard 
            icon={FolderOpen} 
            label="Total Documents" 
            value={stats.total_documents.toString()} 
          />
          <StatCard 
            icon={CheckCircle} 
            label="Processed" 
            value={stats.processed_documents.toString()} 
          />
          <StatCard 
            icon={Clock} 
            label="Pending" 
            value={stats.pending_documents.toString()} 
          />
          <StatCard 
            icon={FileText} 
            label="Total Size" 
            value={formatFileSize(stats.total_size_bytes)} 
          />
        </div>
      )}

      {documents.length === 0 ? (
        <Card className="p-2xl">
          <EmptyState
            icon={FolderOpen}
            title="No documents"
            description="Start by uploading your first document to the knowledge base."
            action={{
              label: 'Upload Document',
              onClick: handleUploadClick,
            }}
          />
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
            {documents.map((doc) => (
              <Card key={doc.id} className="p-lg hover:shadow-md transition-shadow">
                <div className="space-y-md">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-5 w-5 text-primary flex-shrink-0" />
                        <h3 className="font-semibold text-foreground truncate">
                          {doc.original_filename}
                        </h3>
                      </div>
                      {getStatusBadge(doc.processing_status)}
                    </div>
                  </div>

                  {/* Info */}
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div className="flex items-center justify-between">
                      <span>Size:</span>
                      <span className="font-medium">{formatFileSize(doc.file_size)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Uploaded:</span>
                      <span className="font-medium">
                        {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    {doc.source && (
                      <div className="flex items-center justify-between">
                        <span>Source:</span>
                        <span className="font-medium capitalize">{doc.source.replace('_', ' ')}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2 border-t">
                    {doc.is_processed && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleDownload(doc.id, doc.original_filename)}
                        disabled={downloadMutation.isPending}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(doc.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {data && data.total > data.page_size && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {Math.ceil(data.total / data.page_size)}
              </span>
              <Button
                variant="outline"
                disabled={!data.has_more}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

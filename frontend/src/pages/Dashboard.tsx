import MetricCard from '@/components/features/metric-card'
import { MessageSquare, HelpCircle, Target, Database } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Link } from 'react-router-dom'
import { useDashboardStats, useSystemHealth } from '@/hooks/useDashboard'
import ErrorState from '@/components/features/error-state'

export default function Dashboard() {
  const { data: stats, isLoading, error, refetch } = useDashboardStats()
  const { data: health } = useSystemHealth()

  if (error) {
    return (
      <div className="space-y-lg">
        <h1 className="text-display-lg-mobile font-bold text-foreground">Dashboard</h1>
        <ErrorState
          title="Failed to load dashboard"
          description={(error as Error).message}
          onRetry={refetch}
        />
      </div>
    )
  }

  return (
    <div className="space-y-lg">
      <div>
        <h1 className="text-display-lg-mobile font-bold text-foreground">Dashboard</h1>
        <p className="text-body-md text-muted-foreground mt-2">
          Welcome back! Here's your activity overview.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-lg">
        {isLoading ? (
          <>
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </>
        ) : (
          <>
            <MetricCard
              title="Total Conversations"
              value={stats?.total_conversations?.toLocaleString() || '0'}
              icon={<MessageSquare />}
            />
            <MetricCard
              title="Messages Sent"
              value={stats?.total_messages?.toLocaleString() || '0'}
              icon={<HelpCircle />}
            />
            <MetricCard
              title="Avg. Confidence"
              value={`${Math.round((stats?.avg_confidence || 0) * 100)}%`}
              icon={<Target />}
            />
            <MetricCard
              title="Knowledge Base"
              value={stats?.knowledge_base_size?.toLocaleString() || '0'}
              suffix="docs"
              icon={<Database />}
            />
          </>
        )}
      </div>

      {/* System Health */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-label-caps text-muted-foreground">Status</p>
                <p className="text-body-lg font-semibold text-success capitalize">
                  {health.status}
                </p>
              </div>
              <div>
                <p className="text-label-caps text-muted-foreground">Database</p>
                <p className="text-body-lg font-semibold text-foreground capitalize">
                  {health.database}
                </p>
              </div>
              <div>
                <p className="text-label-caps text-muted-foreground">Vector DB</p>
                <p className="text-body-lg font-semibold text-foreground capitalize">
                  {health.vector_db}
                </p>
              </div>
              <div>
                <p className="text-label-caps text-muted-foreground">AI Service</p>
                <p className="text-body-lg font-semibold text-foreground capitalize">
                  {health.ai_service}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      {!isLoading && stats && stats.recent_activity_7d > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-body-md text-muted-foreground">
              You've sent <span className="font-semibold text-foreground">{stats.recent_activity_7d}</span> messages 
              in the last 7 days.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4 flex-wrap">
          <Button asChild>
            <Link to="/chat">New Conversation</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/search">Search Knowledge</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/reports">Upload Report</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

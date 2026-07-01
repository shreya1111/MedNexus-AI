import { useState } from 'react'
import MetricCard from '@/components/features/metric-card'
import { Users, MessageSquare, Activity, Database } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useAllDashboardStats, useSystemHealth } from '@/hooks/useDashboard'
import { useAdminUsers } from '@/hooks/useAdmin'
import ErrorState from '@/components/features/error-state'
import { formatDistanceToNow } from 'date-fns'

export default function AdminDashboard() {
  const { data: stats, isLoading, error, refetch } = useAllDashboardStats()
  const { data: health } = useSystemHealth()

  if (error) {
    return (
      <div className="space-y-lg">
        <h1 className="text-display-lg-mobile font-bold text-foreground">Admin Dashboard</h1>
        <ErrorState
          title="Failed to load admin dashboard"
          description={(error as Error).message}
          onRetry={refetch}
        />
      </div>
    )
  }

  return (
    <div className="space-y-lg">
      <div>
        <h1 className="text-display-lg-mobile font-bold text-foreground">Admin Dashboard</h1>
        <p className="text-body-md text-muted-foreground mt-2">
          System overview and user management.
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
              title="Total Users"
              value={stats?.total_users?.toLocaleString() || '0'}
              icon={<Users />}
            />
            <MetricCard
              title="Total Conversations"
              value={stats?.total_conversations?.toLocaleString() || '0'}
              icon={<MessageSquare />}
            />
            <MetricCard
              title="System Health"
              value={health?.status === 'healthy' ? '100%' : 'Degraded'}
              icon={<Activity />}
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

      {/* System Health Details */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-label-caps text-muted-foreground">Status</p>
                <p className={`text-body-lg font-semibold capitalize ${
                  health.status === 'healthy' ? 'text-success' : 'text-error'
                }`}>
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

      {/* System Metrics */}
      {!isLoading && stats && (
        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-body-md text-muted-foreground">Total Messages</span>
                <span className="text-body-lg font-semibold text-foreground">
                  {stats.total_messages?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-body-md text-muted-foreground">Average Confidence</span>
                <span className="text-body-lg font-semibold text-foreground">
                  {Math.round((stats.avg_confidence || 0) * 100)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-body-md text-muted-foreground">Recent Activity (7d)</span>
                <span className="text-body-lg font-semibold text-foreground">
                  {stats.recent_activity_7d?.toLocaleString() || '0'} messages
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Users</CardTitle>
        </CardHeader>
        <CardContent>
          <UsersTable />
        </CardContent>
      </Card>
    </div>
  )
}

function UsersTable() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAdminUsers({ page, page_size: 10 })

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    )
  }

  if (!data || data.users.length === 0) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Role</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Login</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
              No users found
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Role</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Login</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.users.map((user) => (
            <TableRow key={user.id}>
              <TableCell className="font-medium">{user.email}</TableCell>
              <TableCell>{user.full_name}</TableCell>
              <TableCell className="capitalize">{user.role}</TableCell>
              <TableCell>
                <Badge variant={user.is_active ? 'success' : 'secondary'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {user.last_login
                  ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
                  : 'Never'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Pagination */}
      {data.total > data.page_size && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
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
            size="sm"
            disabled={!data.has_more}
            onClick={() => setPage(p => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}

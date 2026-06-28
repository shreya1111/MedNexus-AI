'use client';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { analyticsApi, recordsApi, appointmentsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AnalyticsData, MedicalRecord, Appointment } from '@/types';
import { Users, FileText, Calendar, TrendingUp, Brain, Clock } from 'lucide-react';
import { formatDateTime, formatDate, capitalize } from '@/lib/utils';
import Link from 'next/link';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const STATUS_COLORS: Record<string, string> = {
  pending: '#f59e0b', confirmed: '#3b82f6', completed: '#10b981', cancelled: '#ef4444',
};
const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const statusVariant = (s: string) =>
  s === 'confirmed' ? 'default' : s === 'completed' ? 'success' : s === 'cancelled' ? 'destructive' : 'warning';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const isStaff = user?.role === 'doctor' || user?.role === 'admin';

  const { data: analytics } = useQuery<{ data: { data: AnalyticsData } }>({
    queryKey: ['analytics'],
    queryFn: analyticsApi.getDashboard,
    enabled: isStaff,
  });

  const { data: records } = useQuery<{ data: { data: { records: MedicalRecord[] } } }>({
    queryKey: ['records', { limit: 5 }],
    queryFn: () => recordsApi.getAll({ limit: 5 }),
  });

  const { data: appointments } = useQuery<{ data: { data: { appointments: Appointment[] } } }>({
    queryKey: ['appointments', { limit: 5 }],
    queryFn: () => appointmentsApi.getAll({ limit: 5 }),
  });

  const stats = analytics?.data?.data;
  const recentRecords = records?.data?.data?.records || [];
  const recentAppts = appointments?.data?.data?.appointments || [];

  const monthlyData = stats?.charts?.monthlyRecords?.map((m) => ({
    name: new Date(m._id.year, m._id.month - 1).toLocaleString('default', { month: 'short' }),
    records: m.count,
  })) || [];

  const typeData = stats?.charts?.recordsByType?.map((r) => ({
    name: r._id.replace('_', ' '),
    value: r.count,
  })) || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Good {new Date().getHours() < 12 ? 'morning' : 'afternoon'},{' '}
          {user?.firstName} 👋
        </h1>
        <p className="text-gray-500 mt-1">Here&apos;s what&apos;s happening with your health today.</p>
      </div>

      {/* Stats grid (staff only) */}
      {isStaff && stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Total Patients', value: stats.overview.totalPatients, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
            { label: 'Medical Records', value: stats.overview.totalRecords, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: 'Appointments', value: stats.overview.totalAppointments, icon: Calendar, color: 'text-amber-600', bg: 'bg-amber-50' },
            { label: 'New This Month', value: stats.overview.newUsersLast30Days, icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-50' },
          ].map(({ label, value, icon: Icon, color, bg }) => (
            <Card key={label}>
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="text-sm text-gray-500">{label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{value.toLocaleString()}</p>
                </div>
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${bg}`}>
                  <Icon className={`h-6 w-6 ${color}`} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Patient quick actions */}
      {!isStaff && (
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { href: '/dashboard/records', icon: FileText, label: 'My Records', desc: `${recentRecords.length} recent`, color: 'bg-blue-50 text-blue-600' },
            { href: '/dashboard/appointments', icon: Calendar, label: 'Appointments', desc: `${recentAppts.length} upcoming`, color: 'bg-emerald-50 text-emerald-600' },
            { href: '/dashboard/ai', icon: Brain, label: 'AI Assistant', desc: 'Ask medical questions', color: 'bg-purple-50 text-purple-600' },
          ].map(({ href, icon: Icon, label, desc, color }) => (
            <Link key={href} href={href}>
              <Card className="cursor-pointer hover:shadow-md transition-shadow">
                <CardContent className="p-6 flex items-center gap-4">
                  <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{label}</p>
                    <p className="text-sm text-gray-500">{desc}</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Charts (staff) */}
        {isStaff && monthlyData.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Records This Year</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={monthlyData}>
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="records" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {isStaff && typeData.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Records by Type</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={typeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                    {typeData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Recent records */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <CardTitle>Recent Records</CardTitle>
            <Link href="/dashboard/records" className="text-sm text-blue-600 hover:underline">View all</Link>
          </CardHeader>
          <CardContent className="p-0">
            {recentRecords.length === 0 ? (
              <p className="px-6 pb-6 text-sm text-gray-500">No records yet.</p>
            ) : (
              <ul className="divide-y divide-gray-50">
                {recentRecords.map((r) => (
                  <li key={r._id} className="flex items-center justify-between px-6 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50">
                        <FileText className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{r.title}</p>
                        <p className="text-xs text-gray-500">{formatDate(r.date)}</p>
                      </div>
                    </div>
                    <Badge variant="secondary">{r.type.replace('_', ' ')}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Upcoming appointments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <CardTitle>Upcoming Appointments</CardTitle>
            <Link href="/dashboard/appointments" className="text-sm text-blue-600 hover:underline">View all</Link>
          </CardHeader>
          <CardContent className="p-0">
            {recentAppts.length === 0 ? (
              <p className="px-6 pb-6 text-sm text-gray-500">No appointments scheduled.</p>
            ) : (
              <ul className="divide-y divide-gray-50">
                {recentAppts.slice(0, 4).map((a) => {
                  const person = user?.role === 'patient'
                    ? (typeof a.doctor === 'object' ? a.doctor : null)
                    : (typeof a.patient === 'object' ? a.patient : null);
                  return (
                    <li key={a._id} className="flex items-center justify-between px-6 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
                          <Clock className="h-4 w-4 text-emerald-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {person ? `${person.firstName} ${person.lastName}` : 'Appointment'}
                          </p>
                          <p className="text-xs text-gray-500">{formatDateTime(a.scheduledAt)}</p>
                        </div>
                      </div>
                      <Badge variant={statusVariant(a.status) as 'default' | 'success' | 'destructive' | 'warning'}>
                        {capitalize(a.status)}
                      </Badge>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

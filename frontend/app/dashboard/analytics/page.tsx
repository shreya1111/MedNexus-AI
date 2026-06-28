'use client';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { AnalyticsData } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, FileText, Calendar, TrendingUp } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: analyticsApi.getDashboard,
  });

  const stats: AnalyticsData | undefined = data?.data?.data;

  const monthlyData = stats?.charts?.monthlyRecords?.map((m) => ({
    month: new Date(m._id.year, m._id.month - 1).toLocaleString('default', { month: 'short', year: '2-digit' }),
    records: m.count,
  })) || [];

  const typeData = stats?.charts?.recordsByType?.map((r) => ({
    name: r._id.replace('_', ' '),
    value: r.count,
  })) || [];

  const statusData = stats?.charts?.appointmentsByStatus?.map((a) => ({
    name: a._id,
    value: a.count,
  })) || [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="grid gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-28 rounded-xl bg-gray-100 animate-pulse" />)}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-64 rounded-xl bg-gray-100 animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-500 mt-1">Platform insights and health trends</p>
      </div>

      {/* KPI cards */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Total Patients', value: stats.overview.totalPatients, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
            { label: 'Medical Records', value: stats.overview.totalRecords, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: 'Total Appointments', value: stats.overview.totalAppointments, icon: Calendar, color: 'text-amber-600', bg: 'bg-amber-50' },
            { label: 'New (30 days)', value: stats.overview.newUsersLast30Days, icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-50' },
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

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Monthly records trend */}
        <Card>
          <CardHeader><CardTitle>Monthly Records Created</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="records" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Records by type */}
        <Card>
          <CardHeader><CardTitle>Records by Type</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={typeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false}>
                  {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Appointment status */}
        <Card>
          <CardHeader><CardTitle>Appointments by Status</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={statusData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {statusData.map((entry, i) => {
                    const c = entry.name === 'completed' ? '#10b981' : entry.name === 'cancelled' ? '#ef4444' : entry.name === 'confirmed' ? '#3b82f6' : '#f59e0b';
                    return <Cell key={i} fill={c} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Upcoming */}
        {stats?.upcoming && stats.upcoming.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Upcoming Appointments</CardTitle></CardHeader>
            <CardContent className="p-0">
              <ul className="divide-y divide-gray-50">
                {stats.upcoming.map((a) => (
                  <li key={a._id} className="flex items-center justify-between px-6 py-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {typeof a.patient === 'object' ? `${a.patient.firstName} ${a.patient.lastName}` : 'Patient'}
                      </p>
                      <p className="text-xs text-gray-500">{new Date(a.scheduledAt).toLocaleString()}</p>
                    </div>
                    <span className="text-xs text-gray-500">{a.type}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

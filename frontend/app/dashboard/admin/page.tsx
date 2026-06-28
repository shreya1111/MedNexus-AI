'use client';
import { useQuery } from '@tanstack/react-query';
import { patientsApi } from '@/lib/api';
import { User } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Users, Search } from 'lucide-react';
import { useState } from 'react';
import { formatDate } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';
import { redirect } from 'next/navigation';

export default function AdminPage() {
  const { user } = useAuthStore();
  const [search, setSearch] = useState('');

  if (user?.role !== 'admin') {
    redirect('/dashboard');
  }

  const { data, isLoading } = useQuery({
    queryKey: ['patients', { search }],
    queryFn: () => patientsApi.getAll({ search, limit: 30 }),
  });

  const patients: User[] = data?.data?.data?.patients || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="text-gray-500 mt-1">Manage patients and platform users</p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          placeholder="Search patients…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-10 w-full rounded-lg border border-gray-200 pl-9 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <Users className="h-5 w-5 text-blue-600" />
          <CardTitle>Patients ({patients.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 rounded-lg bg-gray-100 animate-pulse" />)}
            </div>
          ) : patients.length === 0 ? (
            <p className="p-6 text-gray-500 text-sm">No patients found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                    <th className="px-6 py-3">Name</th>
                    <th className="px-6 py-3">Email</th>
                    <th className="px-6 py-3">Role</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Joined</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {patients.map((p) => (
                    <tr key={p._id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-semibold">
                            {p.firstName[0]}{p.lastName[0]}
                          </div>
                          <span className="font-medium text-gray-900">{p.firstName} {p.lastName}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-500">{p.email}</td>
                      <td className="px-6 py-4">
                        <Badge variant="secondary" className="capitalize">{p.role}</Badge>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={p.isActive ? 'success' : 'destructive'}>{p.isActive ? 'Active' : 'Inactive'}</Badge>
                      </td>
                      <td className="px-6 py-4 text-gray-500">{formatDate(p.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

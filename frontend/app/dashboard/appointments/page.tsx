'use client';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Calendar, Clock, X, Video, Building2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { appointmentsApi } from '@/lib/api';
import { Appointment } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { formatDateTime, capitalize } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';

const schema = z.object({
  doctorId: z.string().min(1, 'Doctor ID required'),
  scheduledAt: z.string().min(1, 'Date & time required'),
  reason: z.string().min(5, 'Min 5 characters'),
  type: z.enum(['in-person', 'telemedicine']),
  notes: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

const statusVariant = (s: string): 'default' | 'success' | 'destructive' | 'warning' | 'secondary' =>
  s === 'confirmed' ? 'default' : s === 'completed' ? 'success' : s === 'cancelled' ? 'destructive' : 'warning';

export default function AppointmentsPage() {
  const { user } = useAuthStore();
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['appointments', { status: statusFilter }],
    queryFn: () => appointmentsApi.getAll({ status: statusFilter || undefined, limit: 20 }),
  });
  const appointments: Appointment[] = data?.data?.data?.appointments || [];

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { type: 'in-person' },
  });

  const createMutation = useMutation({
    mutationFn: (d: FormData) => appointmentsApi.create(d as Record<string, unknown>),
    onSuccess: () => { toast.success('Appointment booked'); qc.invalidateQueries({ queryKey: ['appointments'] }); setShowModal(false); reset(); },
    onError: (e: unknown) => { const err = e as { response?: { data?: { message?: string } } }; toast.error(err?.response?.data?.message || 'Booking failed'); },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => appointmentsApi.cancel(id),
    onSuccess: () => { toast.success('Cancelled'); qc.invalidateQueries({ queryKey: ['appointments'] }); },
    onError: () => toast.error('Cancel failed'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-gray-500 mt-1">Schedule and manage your appointments</p>
        </div>
        {user?.role === 'patient' && (
          <Button onClick={() => setShowModal(true)}>
            <Plus className="h-4 w-4" /> Book Appointment
          </Button>
        )}
      </div>

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {['', 'pending', 'confirmed', 'completed', 'cancelled'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${statusFilter === s ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {s ? capitalize(s) : 'All'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-24 rounded-xl bg-gray-100 animate-pulse" />)}</div>
      ) : appointments.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-16">
            <Calendar className="h-12 w-12 text-gray-300 mb-4" />
            <p className="font-medium text-gray-500">No appointments</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {appointments.map((a) => {
            const other = user?.role === 'patient'
              ? (typeof a.doctor === 'object' ? a.doctor : null)
              : (typeof a.patient === 'object' ? a.patient : null);
            const label = user?.role === 'patient' ? 'Dr.' : 'Patient:';
            return (
              <Card key={a._id}>
                <CardContent className="flex items-center justify-between p-5">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-50">
                      {a.type === 'telemedicine' ? <Video className="h-6 w-6 text-blue-600" /> : <Building2 className="h-6 w-6 text-blue-600" />}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">
                        {other ? `${label} ${other.firstName} ${other.lastName}` : 'Appointment'}
                      </p>
                      <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                        <Clock className="h-3.5 w-3.5" />
                        <span>{formatDateTime(a.scheduledAt)}</span>
                        <span>·</span>
                        <span>{a.duration} min</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{a.reason}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={statusVariant(a.status)}>{capitalize(a.status)}</Badge>
                    {a.status === 'pending' && user?.role === 'patient' && (
                      <button
                        onClick={() => { if (confirm('Cancel this appointment?')) cancelMutation.mutate(a._id); }}
                        className="text-xs text-red-500 hover:text-red-700 font-medium"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Book modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Book Appointment</CardTitle>
              <button onClick={() => { setShowModal(false); reset(); }}><X className="h-5 w-5 text-gray-400" /></button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
                <Input label="Doctor ID" placeholder="Enter doctor's user ID" error={errors.doctorId?.message} {...register('doctorId')} />
                <Input label="Date & Time" type="datetime-local" error={errors.scheduledAt?.message} {...register('scheduledAt')} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Reason for visit</label>
                  <textarea
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm min-h-20 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="Describe your symptoms or reason…"
                    {...register('reason')}
                  />
                  {errors.reason && <p className="mt-1 text-xs text-red-500">{errors.reason.message}</p>}
                </div>
                <Select
                  label="Type"
                  options={[{ value: 'in-person', label: 'In-person' }, { value: 'telemedicine', label: 'Telemedicine (Video)' }]}
                  error={errors.type?.message}
                  {...register('type')}
                />
                <Input label="Notes (optional)" placeholder="Any additional notes" {...register('notes')} />
                <div className="flex gap-3 pt-2">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => { setShowModal(false); reset(); }}>Cancel</Button>
                  <Button type="submit" className="flex-1" loading={isSubmitting || createMutation.isPending}>Book</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

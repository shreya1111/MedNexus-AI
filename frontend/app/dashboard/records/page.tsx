'use client';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Search, FileText, Trash2, Eye, Upload, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { recordsApi } from '@/lib/api';
import { MedicalRecord } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { formatDate, RECORD_TYPES } from '@/lib/utils';

const schema = z.object({
  title: z.string().min(2),
  description: z.string().min(5),
  type: z.string().min(1),
  date: z.string(),
  tags: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export default function RecordsPage() {
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [viewRecord, setViewRecord] = useState<MedicalRecord | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['records', { search, type: typeFilter }],
    queryFn: () => recordsApi.getAll({ search, type: typeFilter || undefined, limit: 20 }),
  });

  const records: MedicalRecord[] = data?.data?.data?.records || [];

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { date: new Date().toISOString().split('T')[0] },
  });

  const createMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const fd = new FormData();
      Object.entries(formData).forEach(([k, v]) => { if (v) fd.append(k, v); });
      if (formData.tags) fd.set('tags', formData.tags.split(',').map((t) => t.trim()).join(','));
      if (file) fd.append('file', file);
      return recordsApi.create(fd);
    },
    onSuccess: () => {
      toast.success('Record created');
      qc.invalidateQueries({ queryKey: ['records'] });
      setShowModal(false);
      reset();
      setFile(null);
    },
    onError: () => toast.error('Failed to create record'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => recordsApi.delete(id),
    onSuccess: () => { toast.success('Deleted'); qc.invalidateQueries({ queryKey: ['records'] }); },
    onError: () => toast.error('Delete failed'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Records</h1>
          <p className="text-gray-500 mt-1">Manage your health documents</p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="h-4 w-4" /> Add Record
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            placeholder="Search records…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full rounded-lg border border-gray-200 pl-9 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
        <Select
          options={[{ value: '', label: 'All types' }, ...RECORD_TYPES]}
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="w-44"
        />
      </div>

      {/* Records grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-36 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      ) : records.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-16">
            <FileText className="h-12 w-12 text-gray-300 mb-4" />
            <p className="font-medium text-gray-500">No records found</p>
            <p className="text-sm text-gray-400 mt-1">Add your first medical record to get started</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {records.map((r) => (
            <Card key={r._id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <Badge variant="default">{r.type.replace('_', ' ')}</Badge>
                  <div className="flex gap-1">
                    <button onClick={() => setViewRecord(r)} className="rounded p-1 hover:bg-gray-100 text-gray-400 hover:text-gray-700">
                      <Eye className="h-4 w-4" />
                    </button>
                    <button onClick={() => { if (confirm('Delete this record?')) deleteMutation.mutate(r._id); }} className="rounded p-1 hover:bg-red-50 text-gray-400 hover:text-red-500">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{r.title}</h3>
                <p className="text-sm text-gray-500 line-clamp-2 mb-3">{r.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{formatDate(r.date)}</span>
                  {r.fileUrl && <span className="text-blue-500">📎 File attached</span>}
                </div>
                {r.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {r.tags.slice(0, 3).map((t) => (
                      <span key={t} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{t}</span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>New Medical Record</CardTitle>
              <button onClick={() => { setShowModal(false); reset(); setFile(null); }}>
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
                <Input label="Title" placeholder="e.g. Annual Blood Test" error={errors.title?.message} {...register('title')} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm min-h-20 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    placeholder="Details about this record…"
                    {...register('description')}
                  />
                  {errors.description && <p className="mt-1 text-xs text-red-500">{errors.description.message}</p>}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Select label="Type" options={RECORD_TYPES.map((t) => ({ value: t.value, label: t.label }))} error={errors.type?.message} {...register('type')} />
                  <Input label="Date" type="date" error={errors.date?.message} {...register('date')} />
                </div>
                <Input label="Tags (comma-separated)" placeholder="diabetes, insulin, blood" {...register('tags')} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Attach file (optional)</label>
                  <label className="flex cursor-pointer items-center gap-3 rounded-lg border-2 border-dashed border-gray-200 p-4 hover:border-blue-400 transition-colors">
                    <Upload className="h-5 w-5 text-gray-400" />
                    <span className="text-sm text-gray-500">{file ? file.name : 'Click to upload PDF or image'}</span>
                    <input type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                  </label>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => { setShowModal(false); reset(); setFile(null); }}>Cancel</Button>
                  <Button type="submit" className="flex-1" loading={isSubmitting || createMutation.isPending}>Create</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* View modal */}
      {viewRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{viewRecord.title}</CardTitle>
              <button onClick={() => setViewRecord(null)}><X className="h-5 w-5 text-gray-400" /></button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Badge>{viewRecord.type.replace('_', ' ')}</Badge>
                <Badge variant="secondary">{formatDate(viewRecord.date)}</Badge>
              </div>
              <p className="text-gray-700 text-sm">{viewRecord.description}</p>
              {viewRecord.aiSummary && (
                <div className="rounded-lg bg-purple-50 p-4">
                  <p className="text-xs font-semibold text-purple-700 mb-1">🤖 AI Summary</p>
                  <p className="text-sm text-purple-800">{viewRecord.aiSummary}</p>
                </div>
              )}
              {viewRecord.fileUrl && (
                <a href={viewRecord.fileUrl} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
                  <FileText className="h-4 w-4" /> View attached file
                </a>
              )}
              {viewRecord.tags?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {viewRecord.tags.map((t) => (
                    <span key={t} className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600">{t}</span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

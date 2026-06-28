'use client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useEffect } from 'react';
import toast from 'react-hot-toast';
import { patientsApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { BLOOD_TYPES } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';

interface ProfileForm {
  dateOfBirth: string;
  gender: string;
  bloodType: string;
  height: string;
  weight: string;
  allergies: string;
  chronicConditions: string;
  emergencyName: string;
  emergencyPhone: string;
  emergencyRelation: string;
}

export default function ProfilePage() {
  const { user } = useAuthStore();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['patientProfile'],
    queryFn: patientsApi.getMyProfile,
    enabled: user?.role === 'patient',
  });

  const profile = data?.data?.data?.profile;

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<ProfileForm>();

  useEffect(() => {
    if (profile) {
      reset({
        dateOfBirth: profile.dateOfBirth ? profile.dateOfBirth.split('T')[0] : '',
        gender: profile.gender || '',
        bloodType: profile.bloodType || '',
        height: profile.height?.toString() || '',
        weight: profile.weight?.toString() || '',
        allergies: profile.allergies?.join(', ') || '',
        chronicConditions: profile.chronicConditions?.join(', ') || '',
        emergencyName: profile.emergencyContact?.name || '',
        emergencyPhone: profile.emergencyContact?.phone || '',
        emergencyRelation: profile.emergencyContact?.relation || '',
      });
    }
  }, [profile, reset]);

  const mutation = useMutation({
    mutationFn: (d: ProfileForm) => patientsApi.updateMyProfile({
      dateOfBirth: d.dateOfBirth || undefined,
      gender: d.gender || undefined,
      bloodType: d.bloodType || undefined,
      height: d.height ? parseFloat(d.height) : undefined,
      weight: d.weight ? parseFloat(d.weight) : undefined,
      allergies: d.allergies ? d.allergies.split(',').map((s) => s.trim()).filter(Boolean) : [],
      chronicConditions: d.chronicConditions ? d.chronicConditions.split(',').map((s) => s.trim()).filter(Boolean) : [],
      emergencyContact: d.emergencyName ? { name: d.emergencyName, phone: d.emergencyPhone, relation: d.emergencyRelation } : undefined,
    }),
    onSuccess: () => { toast.success('Profile updated'); qc.invalidateQueries({ queryKey: ['patientProfile'] }); },
    onError: () => toast.error('Update failed'),
  });

  if (user?.role !== 'patient') {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <Card><CardContent className="p-6"><p className="text-gray-500">Patient profile management is available for patient accounts.</p></CardContent></Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Health Profile</h1>
        <p className="text-gray-500 mt-1">Keep your medical information up to date</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Account Information</CardTitle></CardHeader>
        <CardContent>
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-xl font-bold mb-4">
            {user?.firstName?.[0]}{user?.lastName?.[0]}
          </div>
          <p className="text-lg font-semibold text-gray-900">{user?.firstName} {user?.lastName}</p>
          <p className="text-gray-500">{user?.email}</p>
          <span className="inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700 capitalize mt-1">{user?.role}</span>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="h-64 rounded-xl bg-gray-100 animate-pulse" />
      ) : (
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Personal Health Info</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input label="Date of Birth" type="date" {...register('dateOfBirth')} />
                <Select
                  label="Gender"
                  options={[{ value: 'male', label: 'Male' }, { value: 'female', label: 'Female' }, { value: 'other', label: 'Other' }]}
                  placeholder="Select gender"
                  {...register('gender')}
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <Select
                  label="Blood Type"
                  options={BLOOD_TYPES.map((b) => ({ value: b, label: b }))}
                  placeholder="Select"
                  {...register('bloodType')}
                />
                <Input label="Height (cm)" type="number" placeholder="170" {...register('height')} />
                <Input label="Weight (kg)" type="number" placeholder="70" {...register('weight')} />
              </div>
              <Input label="Allergies (comma-separated)" placeholder="Penicillin, Latex" {...register('allergies')} />
              <Input label="Chronic Conditions (comma-separated)" placeholder="Diabetes, Hypertension" {...register('chronicConditions')} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Emergency Contact</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input label="Full Name" placeholder="Jane Doe" {...register('emergencyName')} />
                <Input label="Phone Number" placeholder="+91 9876543210" {...register('emergencyPhone')} />
              </div>
              <Input label="Relationship" placeholder="Spouse, Parent…" {...register('emergencyRelation')} />
            </CardContent>
          </Card>

          <Button type="submit" loading={isSubmitting || mutation.isPending}>Save Profile</Button>
        </form>
      )}
    </div>
  );
}

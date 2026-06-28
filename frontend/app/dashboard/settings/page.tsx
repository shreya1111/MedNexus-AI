'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const nameSchema = z.object({
  firstName: z.string().min(2),
  lastName: z.string().min(2),
});

const pwSchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: z.string().min(8).regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Must contain uppercase, lowercase & number'),
  confirmPassword: z.string(),
}).refine((d) => d.newPassword === d.confirmPassword, { message: "Passwords don't match", path: ['confirmPassword'] });

type NameForm = z.infer<typeof nameSchema>;
type PwForm = z.infer<typeof pwSchema>;

export default function SettingsPage() {
  const { user, updateUser } = useAuthStore();

  const { register: rn, handleSubmit: hn, formState: { isSubmitting: isn } } = useForm<NameForm>({
    resolver: zodResolver(nameSchema),
    defaultValues: { firstName: user?.firstName, lastName: user?.lastName },
  });

  const { register: rp, handleSubmit: hp, reset: resetPw, formState: { errors: pe, isSubmitting: isp } } = useForm<PwForm>({
    resolver: zodResolver(pwSchema),
  });

  const nameMutation = useMutation({
    mutationFn: (d: NameForm) => authApi.updateProfile(d as Record<string, unknown>),
    onSuccess: (res) => { updateUser(res.data.data.user); toast.success('Name updated'); },
    onError: () => toast.error('Update failed'),
  });

  const pwMutation = useMutation({
    mutationFn: (d: PwForm) => authApi.changePassword({ currentPassword: d.currentPassword, newPassword: d.newPassword }),
    onSuccess: () => { toast.success('Password changed'); resetPw(); },
    onError: (e: unknown) => { const err = e as { response?: { data?: { message?: string } } }; toast.error(err?.response?.data?.message || 'Failed'); },
  });

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your account preferences</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Display Name</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={hn((d) => nameMutation.mutate(d))} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="First name" {...rn('firstName')} />
              <Input label="Last name" {...rn('lastName')} />
            </div>
            <Button type="submit" loading={isn || nameMutation.isPending}>Update name</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Change Password</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={hp((d) => pwMutation.mutate(d))} className="space-y-4">
            <Input label="Current password" type="password" error={pe.currentPassword?.message} {...rp('currentPassword')} />
            <Input label="New password" type="password" error={pe.newPassword?.message} {...rp('newPassword')} />
            <Input label="Confirm new password" type="password" error={pe.confirmPassword?.message} {...rp('confirmPassword')} />
            <Button type="submit" loading={isp || pwMutation.isPending}>Change password</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Account Info</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Email</span>
            <span className="font-medium text-gray-900">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Role</span>
            <span className="font-medium text-gray-900 capitalize">{user?.role}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Email verified</span>
            <span className={user?.isEmailVerified ? 'text-emerald-600 font-medium' : 'text-amber-600 font-medium'}>
              {user?.isEmailVerified ? 'Verified ✓' : 'Not verified'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Last login</span>
            <span className="font-medium text-gray-900">{user?.lastLogin ? new Date(user.lastLogin).toLocaleString() : 'N/A'}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

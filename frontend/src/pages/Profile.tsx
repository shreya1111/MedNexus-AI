import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useAuthStore } from '@/stores/auth-store'
import { useProfile, useUpdateProfile, useChangePassword } from '@/hooks/useProfile'
import StatCard from '@/components/features/stat-card'
import Skeleton from '@/components/ui/skeleton'
import ErrorState from '@/components/features/error-state'
import { MessageSquare, Calendar, HelpCircle, FileText, Activity } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'

export default function Profile() {
  const { user } = useAuthStore()
  const { data: profile, isLoading, isError, error, refetch } = useProfile()
  const updateProfileMutation = useUpdateProfile()
  const changePasswordMutation = useChangePassword()

  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    email: '',
  })

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  const handleEditProfile = () => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name,
        email: profile.email,
      })
      setIsEditingProfile(true)
    }
  }

  const handleSaveProfile = async () => {
    await updateProfileMutation.mutateAsync(profileForm)
    setIsEditingProfile(false)
  }

  const handleChangePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      alert('Passwords do not match')
      return
    }

    if (passwordForm.new_password.length < 8) {
      alert('Password must be at least 8 characters')
      return
    }

    await changePasswordMutation.mutateAsync({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })

    setPasswordForm({
      current_password: '',
      new_password: '',
      confirm_password: '',
    })
    setIsChangingPassword(false)
  }

  if (isLoading) {
    return (
      <div className="space-y-lg">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-lg">
        <h1 className="text-display-lg-mobile font-bold text-foreground">Profile</h1>
        <ErrorState
          title="Failed to load profile"
          message={error?.message || 'An error occurred'}
          onRetry={refetch}
        />
      </div>
    )
  }

  const stats = profile?.statistics

  return (
    <div className="space-y-lg">
      <h1 className="text-display-lg-mobile font-bold text-foreground">Profile</h1>

      {/* Profile Card */}
      <Card>
        <CardContent className="pt-lg">
          <div className="flex items-center gap-6">
            <Avatar className="h-24 w-24">
              <AvatarFallback className="text-headline-md">
                {profile?.full_name?.charAt(0) || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h2 className="text-headline-md font-semibold">{profile?.full_name || 'User'}</h2>
              <p className="text-body-md text-muted-foreground">{profile?.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="primary" className="capitalize">{profile?.role || 'Patient'}</Badge>
                {profile?.is_verified && (
                  <Badge variant="success">Verified</Badge>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Button variant="outline" onClick={handleEditProfile}>
                Edit Profile
              </Button>
              <Button variant="outline" onClick={() => setIsChangingPassword(true)}>
                Change Password
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-lg">
          <StatCard 
            icon={MessageSquare} 
            label="Conversations" 
            value={stats.total_conversations.toString()} 
          />
          <StatCard 
            icon={HelpCircle} 
            label="Messages" 
            value={stats.total_messages.toString()} 
          />
          <StatCard 
            icon={FileText} 
            label="Documents" 
            value={stats.total_documents.toString()} 
          />
          <StatCard 
            icon={Calendar} 
            label="Member Since" 
            value={stats.member_since} 
          />
        </div>
      )}

      {/* Activity */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle>Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-body-md text-muted-foreground">Total Reports</span>
                <span className="text-body-lg font-semibold text-foreground">
                  {stats.total_reports}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-body-md text-muted-foreground">Days Active</span>
                <span className="text-body-lg font-semibold text-foreground">
                  {stats.days_active}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Edit Profile Dialog */}
      <Dialog open={isEditingProfile} onOpenChange={setIsEditingProfile}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
            <DialogDescription>
              Update your profile information
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                className="mt-2"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsEditingProfile(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSaveProfile}
                disabled={updateProfileMutation.isPending}
              >
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={isChangingPassword} onOpenChange={setIsChangingPassword}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and a new password
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="current_password">Current Password</Label>
              <Input
                id="current_password"
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="confirm_password">Confirm New Password</Label>
              <Input
                id="confirm_password"
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                className="mt-2"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsChangingPassword(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleChangePassword}
                disabled={changePasswordMutation.isPending}
              >
                Change Password
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

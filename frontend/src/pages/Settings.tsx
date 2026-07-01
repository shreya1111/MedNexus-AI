import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useSettings, useUpdateSettings } from '@/hooks/useProfile'
import Skeleton from '@/components/ui/skeleton'
import ErrorState from '@/components/features/error-state'
import { Settings as SettingsType } from '@/services/profile.service'

export default function Settings() {
  const { data: settings, isLoading, isError, error, refetch } = useSettings()
  const updateSettingsMutation = useUpdateSettings()

  const handleUpdateSetting = async <K extends keyof SettingsType>(
    key: K,
    value: SettingsType[K]
  ) => {
    await updateSettingsMutation.mutateAsync({ [key]: value })
  }

  if (isLoading) {
    return (
      <div className="space-y-lg max-w-4xl">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-lg max-w-4xl">
        <h1 className="text-display-lg-mobile font-bold text-foreground">Settings</h1>
        <ErrorState
          title="Failed to load settings"
          message={error?.message || 'An error occurred'}
          onRetry={refetch}
        />
      </div>
    )
  }

  if (!settings) return null

  return (
    <div className="space-y-lg max-w-4xl">
      <h1 className="text-display-lg-mobile font-bold text-foreground">Settings</h1>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="theme">Theme</Label>
            <Select
              value={settings.theme}
              onValueChange={(value: 'light' | 'dark' | 'system') =>
                handleUpdateSetting('theme', value)
              }
            >
              <SelectTrigger id="theme" className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="language">Language</Label>
            <Select
              value={settings.language}
              onValueChange={(value) => handleUpdateSetting('language', value)}
            >
              <SelectTrigger id="language" className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
                <SelectItem value="fr">French</SelectItem>
                <SelectItem value="de">German</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="notifications">Enable Notifications</Label>
              <p className="text-sm text-muted-foreground mt-1">
                Receive notifications about important updates
              </p>
            </div>
            <Switch
              id="notifications"
              checked={settings.notifications_enabled}
              onCheckedChange={(checked) =>
                handleUpdateSetting('notifications_enabled', checked)
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="email-notifications">Email Notifications</Label>
              <p className="text-sm text-muted-foreground mt-1">
                Receive email notifications
              </p>
            </div>
            <Switch
              id="email-notifications"
              checked={settings.email_notifications}
              onCheckedChange={(checked) =>
                handleUpdateSetting('email_notifications', checked)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* AI Settings */}
      <Card>
        <CardHeader>
          <CardTitle>AI Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="ai_model">AI Model</Label>
            <Select
              value={settings.ai_model}
              onValueChange={(value) => handleUpdateSetting('ai_model', value)}
            >
              <SelectTrigger id="ai_model" className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gemini-2.0-flash">Gemini 2.0 Flash</SelectItem>
                <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="retrieval_top_k">Retrieval Top K</Label>
            <p className="text-sm text-muted-foreground mb-2">
              Number of documents to retrieve (1-20)
            </p>
            <Input
              id="retrieval_top_k"
              type="number"
              min={1}
              max={20}
              value={settings.retrieval_top_k}
              onChange={(e) =>
                handleUpdateSetting('retrieval_top_k', parseInt(e.target.value))
              }
            />
          </div>

          <div>
            <Label htmlFor="chunk_size">Chunk Size</Label>
            <p className="text-sm text-muted-foreground mb-2">
              Size of text chunks for processing (128-2048)
            </p>
            <Input
              id="chunk_size"
              type="number"
              min={128}
              max={2048}
              step={128}
              value={settings.chunk_size}
              onChange={(e) =>
                handleUpdateSetting('chunk_size', parseInt(e.target.value))
              }
            />
          </div>

          <div>
            <Label htmlFor="embedding_provider">Embedding Provider</Label>
            <Select
              value={settings.embedding_provider}
              onValueChange={(value) =>
                handleUpdateSetting('embedding_provider', value)
              }
            >
              <SelectTrigger id="embedding_provider" className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="google">Google (Gemini)</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Privacy & Security */}
      <Card>
        <CardHeader>
          <CardTitle>Privacy & Security</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-body-md text-muted-foreground">
            Your data is encrypted and secure. We never share your information with third parties.
          </p>
          <div className="flex gap-2">
            <Button variant="outline">Download My Data</Button>
            <Button variant="outline">Delete Account</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

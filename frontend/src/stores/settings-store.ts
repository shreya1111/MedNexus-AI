import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SettingsState {
  fontSize: 'small' | 'medium' | 'large'
  emailNotifications: boolean
  pushNotifications: boolean
  showProfile: boolean
  shareAnalytics: boolean
  
  setFontSize: (size: 'small' | 'medium' | 'large') => void
  setEmailNotifications: (enabled: boolean) => void
  setPushNotifications: (enabled: boolean) => void
  setShowProfile: (enabled: boolean) => void
  setShareAnalytics: (enabled: boolean) => void
  resetSettings: () => void
}

const defaultSettings = {
  fontSize: 'medium' as const,
  emailNotifications: true,
  pushNotifications: false,
  showProfile: true,
  shareAnalytics: false,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaultSettings,
      setFontSize: (fontSize) => set({ fontSize }),
      setEmailNotifications: (emailNotifications) => set({ emailNotifications }),
      setPushNotifications: (pushNotifications) => set({ pushNotifications }),
      setShowProfile: (showProfile) => set({ showProfile }),
      setShareAnalytics: (shareAnalytics) => set({ shareAnalytics }),
      resetSettings: () => set(defaultSettings),
    }),
    {
      name: 'settings-storage',
    }
  )
)

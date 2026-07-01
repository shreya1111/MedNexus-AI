import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/ui/sidebar'

export default function ChatLayout() {
  return (
    <div className="h-screen bg-background text-foreground flex overflow-hidden">
      {/* Fixed Sidebar for conversation list - 256px width */}
      <Sidebar variant="chat" />
      
      {/* Chat Area - takes remaining space */}
      <main className="flex-1 flex flex-col lg:ml-64">
        <Outlet />
      </main>
    </div>
  )
}

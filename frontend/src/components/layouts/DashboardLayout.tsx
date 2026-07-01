import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/ui/sidebar'
import Navbar from '@/components/ui/navbar'

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Fixed Sidebar - 256px width */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="lg:pl-64">
        {/* Top Navbar - 64px height */}
        <Navbar />
        
        {/* Page Content */}
        <main className="p-lg">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

import { Outlet } from 'react-router-dom'

export default function PublicLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Public pages don't need header/footer for now */}
      <main>
        <Outlet />
      </main>
    </div>
  )
}

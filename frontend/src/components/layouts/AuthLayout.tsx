import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4">
      {/* Centered auth form container */}
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>
  )
}

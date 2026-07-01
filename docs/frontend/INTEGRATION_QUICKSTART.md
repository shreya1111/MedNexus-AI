# MedNexus-AI Integration Quickstart

## 🚀 Getting Started

### Prerequisites

1. **Backend Running**: FastAPI server on `http://localhost:8000`
2. **Database**: PostgreSQL running and migrated
3. **Node.js**: v18+ installed
4. **Python**: 3.10+ installed

### Start Development

```bash
# Terminal 1: Start Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd frontend
npm install
npm run dev
```

Access: `http://localhost:5173`

---

## 🔑 Authentication

### Login

```typescript
import { useLogin } from '@/hooks/useAuth'

function LoginPage() {
  const login = useLogin()
  
  const handleSubmit = (email: string, password: string) => {
    login.mutate({ email, password })
    // Automatically redirects to /dashboard on success
  }
}
```

### Register

```typescript
import { useRegister } from '@/hooks/useAuth'

function RegisterPage() {
  const register = useRegister()
  
  const handleSubmit = (data) => {
    register.mutate({
      full_name: data.fullName,
      email: data.email,
      password: data.password,
      role: 'patient' // or 'doctor', 'researcher', 'administrator'
    })
    // Automatically redirects to /login on success
  }
}
```

### Logout

```typescript
import { useLogout } from '@/hooks/useAuth'

function NavBar() {
  const logout = useLogout()
  
  return (
    <button onClick={() => logout.mutate()}>
      Logout
    </button>
  )
}
```

### Get Current User

```typescript
import { useCurrentUser } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/auth-store'

function ProfilePage() {
  const { user } = useAuthStore()
  const { data, isLoading } = useCurrentUser()
  
  if (isLoading) return <div>Loading...</div>
  
  return <div>{user?.full_name}</div>
}
```

---

## 💬 Chat Integration

### Send Message

```typescript
import { useSendMessage } from '@/hooks/useChat'
import { useChatStore } from '@/stores/chat-store'

function ChatPage() {
  const sendMessage = useSendMessage()
  const { messages, isLoading } = useChatStore()
  
  const handleSend = async (text: string) => {
    await sendMessage.mutateAsync(text)
    // Message appears optimistically, then updated with AI response
  }
}
```

### Load Chat Sessions

```typescript
import { useChatSessions } from '@/hooks/useChat'

function ChatSidebar() {
  const { data: sessions, isLoading } = useChatSessions()
  
  if (isLoading) return <div>Loading sessions...</div>
  
  return (
    <div>
      {sessions?.sessions.map(session => (
        <div key={session.session_id}>
          {session.message_count} messages
        </div>
      ))}
    </div>
  )
}
```

### Load Session History

```typescript
import { useSessionHistory } from '@/hooks/useChat'

function ChatPage() {
  const sessionId = "session-123"
  const { data: history, isLoading } = useSessionHistory(sessionId)
  
  if (isLoading) return <div>Loading...</div>
  
  return (
    <div>
      {history?.messages.map((msg, idx) => (
        <div key={idx}>{msg.content}</div>
      ))}
    </div>
  )
}
```

### Delete Session

```typescript
import { useDeleteSession } from '@/hooks/useChat'

function ChatSidebar() {
  const deleteSession = useDeleteSession()
  
  const handleDelete = (sessionId: string) => {
    deleteSession.mutate(sessionId)
    // Automatically removes from list and shows notification
  }
}
```

---

## 🛡️ Protected Routes

### Basic Protection

```typescript
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}
```

### Admin Protection

```typescript
function AdminRoute({ children }) {
  const { isAuthenticated, user } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (user?.role !== 'administrator' && !user?.is_superuser) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}
```

---

## 📡 API Services

### Making Custom API Calls

```typescript
import api from '@/services/api'

// GET request
const response = await api.get('/endpoint')

// POST request
const response = await api.post('/endpoint', { data })

// PUT request
const response = await api.put('/endpoint/{id}', { data })

// DELETE request
await api.delete('/endpoint/{id}')

// With query params
const response = await api.get('/endpoint', {
  params: { page: 1, limit: 20 }
})
```

### Error Handling

```typescript
import { useNotificationStore } from '@/stores/notification-store'

function MyComponent() {
  const { addNotification } = useNotificationStore()
  
  try {
    await api.get('/endpoint')
  } catch (error) {
    addNotification({
      type: 'error',
      title: 'Error',
      description: error.message
    })
  }
}
```

---

## 🔔 Notifications

### Show Notification

```typescript
import { useNotificationStore } from '@/stores/notification-store'

function MyComponent() {
  const { addNotification } = useNotificationStore()
  
  // Success
  addNotification({
    type: 'success',
    title: 'Success!',
    description: 'Operation completed.'
  })
  
  // Error
  addNotification({
    type: 'error',
    title: 'Error',
    description: 'Something went wrong.'
  })
  
  // Info
  addNotification({
    type: 'info',
    title: 'Info',
    description: 'Here is some information.'
  })
  
  // Warning
  addNotification({
    type: 'warning',
    title: 'Warning',
    description: 'Please be careful.'
  })
}
```

---

## 🎨 Using Components

### Button

```typescript
import { Button } from '@/components/ui/button'

<Button onClick={handleClick}>Click me</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button disabled>Disabled</Button>
```

### Card

```typescript
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>
```

### Input

```typescript
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

<div>
  <Label htmlFor="email">Email</Label>
  <Input 
    id="email"
    type="email" 
    placeholder="Enter email"
    value={value}
    onChange={(e) => setValue(e.target.value)}
  />
</div>
```

### MetricCard

```typescript
import MetricCard from '@/components/features/metric-card'
import { MessageSquare } from 'lucide-react'

<MetricCard
  title="Total Conversations"
  value="1,234"
  change={12.5}
  trend="up"
  icon={<MessageSquare />}
/>
```

### ConversationCard

```typescript
import ConversationCard from '@/components/features/conversation-card'

<ConversationCard
  role="assistant"
  content="This is the AI response..."
  confidence={0.95}
  citations={["Source 1", "Source 2"]}
  timestamp="2025-01-01T12:00:00Z"
/>
```

---

## 🔧 Common Patterns

### Loading State

```typescript
function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['myData'],
    queryFn: fetchData
  })
  
  if (isLoading) return <Skeleton />
  if (error) return <ErrorState onRetry={refetch} />
  
  return <div>{data}</div>
}
```

### Form Handling

```typescript
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

function MyForm() {
  const [formData, setFormData] = useState({ name: '' })
  const mutation = useMutation({ mutationFn: submitForm })
  
  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate(formData)
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <Input 
        value={formData.name}
        onChange={(e) => setFormData({ name: e.target.value })}
        disabled={mutation.isPending}
      />
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Submitting...' : 'Submit'}
      </Button>
    </form>
  )
}
```

### Optimistic Updates

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'

function MyComponent() {
  const queryClient = useQueryClient()
  
  const mutation = useMutation({
    mutationFn: updateData,
    onMutate: async (newData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['myData'] })
      
      // Snapshot current value
      const previous = queryClient.getQueryData(['myData'])
      
      // Optimistically update
      queryClient.setQueryData(['myData'], newData)
      
      return { previous }
    },
    onError: (err, newData, context) => {
      // Rollback on error
      queryClient.setQueryData(['myData'], context.previous)
    },
    onSettled: () => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['myData'] })
    },
  })
}
```

---

## 🐛 Debugging

### Check Authentication

```typescript
import { useAuthStore } from '@/stores/auth-store'

function DebugAuth() {
  const { user, isAuthenticated, accessToken } = useAuthStore()
  
  console.log('User:', user)
  console.log('Authenticated:', isAuthenticated)
  console.log('Token:', accessToken)
  
  // Check localStorage
  console.log('Stored token:', localStorage.getItem('access_token'))
}
```

### Check API Requests

```typescript
// API service already logs requests in interceptor
// Check browser console for:
// - Request URL
// - Request headers
// - Response data
// - Errors
```

### React Query DevTools

```typescript
// Add to App.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  )
}
```

---

## 📝 TypeScript Tips

### Extending Types

```typescript
import { User } from '@/stores/auth-store'

interface ExtendedUser extends User {
  customField: string
}
```

### Type-safe API Calls

```typescript
import api from '@/services/api'

interface MyResponse {
  data: string[]
  total: number
}

const response = await api.get<MyResponse>('/endpoint')
// response.data is now type-safe
```

---

## 🚨 Common Errors

### "401 Unauthorized"
- Check if token exists in localStorage
- Check if token is expired
- Verify backend is running
- Check CORS settings

### "Network Error"
- Verify backend URL in `.env`
- Check if backend is running on port 8000
- Check firewall/antivirus

### "Invalid Token"
- Clear localStorage and login again
- Check token format (should be JWT)
- Verify JWT_SECRET_KEY matches backend

---

## 📚 Additional Resources

- [React Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://github.com/pmndrs/zustand)
- [Radix UI Docs](https://www.radix-ui.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

**Quick Reference Complete** ✅

For detailed integration status, see `PHASE_5C_INTEGRATION_SUMMARY.md`

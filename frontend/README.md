# MedNexus-AI Frontend

Next.js 15 + TypeScript frontend for MedNexus healthcare platform.

## Features

- ✅ Next.js 15 with App Router
- ✅ TypeScript with strict mode
- ✅ Tailwind CSS for styling
- ✅ TanStack Query for server state
- ✅ Zustand for client state
- ✅ React Hook Form + Zod validation
- ✅ Responsive design
- ✅ Dark mode support (via next-themes)
- ✅ Chart visualizations (Recharts)
- ✅ Automatic token refresh
- ✅ File upload support

## Prerequisites

- Node.js 20+
- Backend API running (see `../backend/`)

## Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with API URLs
```

## Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
NEXT_PUBLIC_AI_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:5000
```

**Important:** For Docker deployment, use internal service names:
```bash
NEXT_PUBLIC_API_URL=http://backend:5000/api/v1
NEXT_PUBLIC_AI_URL=http://ai-services:8000
```

## Development

```bash
# Run development server
npm run dev

# Open http://localhost:3000
```

## Production Build

```bash
# Build for production
npm run build

# Run production server
npm start
```

## Docker

```bash
# Build image
docker build -t mednexus-frontend .

# Run container
docker run -p 3000:3000 mednexus-frontend
```

**Note:** Dockerfile uses `output: 'standalone'` mode for optimal Docker images.

## Project Structure

```
app/
├── dashboard/       # Protected dashboard pages
│   ├── admin/      # Admin-only pages
│   ├── ai/         # AI assistant interface
│   ├── analytics/  # Analytics & reports
│   ├── appointments/
│   ├── profile/
│   ├── records/
│   └── settings/
├── login/          # Login page
├── register/       # Registration page
├── layout.tsx      # Root layout
├── page.tsx        # Landing page
└── providers.tsx   # React Query provider

components/
├── layout/         # Layout components (Sidebar, etc.)
└── ui/             # Reusable UI components

lib/
├── api.ts          # Axios instance + API methods
└── utils.ts        # Utility functions

hooks/              # Custom React hooks
```

## API Integration

API client is configured in `lib/api.ts`:

```typescript
import { authApi, recordsApi, appointmentsApi, aiApi } from '@/lib/api';

// Authentication
const { data } = await authApi.login({ email, password });

// Medical records
const records = await recordsApi.getAll({ page: 1, limit: 20 });

// AI services
const response = await aiApi.query('What are diabetes symptoms?');
```

## State Management

**Zustand** for auth state:
```typescript
import { useAuthStore } from '@/hooks/useAuth';

const { user, setUser, logout } = useAuthStore();
```

**TanStack Query** for server state:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['records'],
  queryFn: () => recordsApi.getAll(),
});
```

## Forms

Using React Hook Form + Zod:

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const { register, handleSubmit } = useForm({
  resolver: zodResolver(schema),
});
```

## Styling

Tailwind CSS with custom configuration:

```tsx
<div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
  <h1 className="text-2xl font-bold">Title</h1>
</div>
```

## Authentication Flow

1. User logs in → receives access token (15m) + refresh token (7d)
2. Tokens stored in `localStorage`
3. API client adds `Authorization: Bearer {token}` to requests
4. On 401 error → auto-refresh using refresh token
5. On refresh failure → redirect to login

## Protected Routes

Dashboard pages are protected by middleware/auth check (implement in layout).

## Available Pages

- `/` - Landing page
- `/login` - Login
- `/register` - Registration
- `/dashboard` - Main dashboard
- `/dashboard/profile` - User profile
- `/dashboard/records` - Medical records
- `/dashboard/appointments` - Appointments
- `/dashboard/analytics` - Analytics (doctor/admin)
- `/dashboard/ai` - AI assistant
- `/dashboard/admin` - Admin panel
- `/dashboard/settings` - User settings

## UI Components

Located in `components/ui/`:
- `Button` - Button variants
- `Input` - Form inputs
- `Card` - Card layouts
- `Badge` - Status badges
- `Select` - Dropdown selects

## Troubleshooting

**API connection fails:**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend is running (`curl http://localhost:5000/health`)
- Check CORS configuration in backend

**Build errors:**
- Delete `.next/` folder
- Run `npm install` again
- Check TypeScript errors: `npx tsc --noEmit`

**Blank page:**
- Check browser console for errors
- Verify environment variables are set
- Ensure API is accessible

## Contributing

1. Follow Tailwind CSS conventions
2. Use TypeScript strictly
3. Keep components small and reusable
4. Use TanStack Query for API calls
5. Add proper error handling

## License

MIT

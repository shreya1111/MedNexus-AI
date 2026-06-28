# MedNexus-AI Backend

Express.js + TypeScript backend API for MedNexus healthcare platform.

## Features

- ✅ RESTful API with Express.js
- ✅ TypeScript with strict type checking
- ✅ MongoDB with Mongoose ODM
- ✅ Redis caching (optional, graceful degradation)
- ✅ JWT authentication with refresh tokens
- ✅ Role-based access control (Patient / Doctor / Admin)
- ✅ File uploads to Cloudinary
- ✅ Request validation with Zod
- ✅ Structured logging with Winston
- ✅ Rate limiting & security headers
- ✅ WebSocket support (Socket.io)
- ✅ Pagination & search utilities
- ✅ Comprehensive test suite

## Prerequisites

- Node.js 20+
- MongoDB 7.0+
- Redis 7.2+ (optional)

## Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your configuration
```

## Environment Variables

See `.env.example` for full list. Required variables:

```bash
MONGODB_URI=mongodb://localhost:27017/mednexus
JWT_SECRET=your-secret-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-min-32-chars
```

## Development

```bash
# Run in development mode (auto-reload)
npm run dev

# Run linter
npm run lint

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Seed database with demo data
npm run seed
```

## Production Build

```bash
# Build TypeScript to JavaScript
npm run build

# Run production server
npm start
```

## Docker

```bash
# Build image
docker build -t mednexus-backend .

# Run container
docker run -p 5000:5000 --env-file .env mednexus-backend
```

## API Structure

```
src/
├── config/          # Database, Redis, environment config
├── controllers/     # Request handlers
├── middleware/      # Auth, validation, error handling
├── models/          # Mongoose schemas
├── routes/          # API route definitions
├── services/        # Business logic (Cloudinary, etc.)
├── utils/           # JWT, logger, pagination helpers
├── validators/      # Zod schemas for validation
├── types/           # TypeScript interfaces
├── __tests__/       # Test files
├── app.ts           # Express app setup
└── index.ts         # Entry point
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update profile
- `PUT /api/v1/auth/me/password` - Change password

### Medical Records
- `GET /api/v1/records` - List records (paginated)
- `GET /api/v1/records/search?q=term` - Search records
- `GET /api/v1/records/:id` - Get by ID
- `POST /api/v1/records` - Create record (with file upload)
- `PUT /api/v1/records/:id` - Update record
- `DELETE /api/v1/records/:id` - Delete record

### Appointments
- `GET /api/v1/appointments` - List appointments
- `POST /api/v1/appointments` - Book appointment
- `PUT /api/v1/appointments/:id/status` - Update status
- `PUT /api/v1/appointments/:id/cancel` - Cancel appointment

### Patients (Doctor/Admin)
- `GET /api/v1/patients` - List patients
- `GET /api/v1/patients/:id` - Get patient details
- `GET /api/v1/patients/profile` - Get own profile
- `PUT /api/v1/patients/profile` - Update own profile

### Analytics (Doctor/Admin)
- `GET /api/v1/analytics/dashboard` - Dashboard KPIs

### Health Check
- `GET /health` - Service health status

## Response Format

All API responses follow this format:

**Success:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "pagination": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "totalPages": 5
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message",
  "details": { ... }
}
```

## Testing

```bash
# Run all tests
npm test

# Run specific test file
npm test -- src/__tests__/jwt.test.ts

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

Test coverage:
- JWT utilities: 7 tests
- Pagination: 9 tests  
- API integration: 14 tests
- **Total: 30 tests**

## Logging

Logs are written to:
- `logs/combined.log` - All logs
- `logs/error.log` - Error logs only
- Console - Development mode

Log format:
```
2026-06-28 14:30:45 [info]: [req-id] GET /api/v1/records
```

## Security Features

- **Helmet.js** - Security headers
- **CORS** - Configurable origin whitelist
- **Rate Limiting** - 20 auth requests / 15min, 200 general / 15min
- **JWT** - Access (15m) + refresh (7d) token rotation
- **bcrypt** - Password hashing (12 rounds)
- **Zod** - Input validation
- **File validation** - Type & size limits

## Troubleshooting

See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) in project root.

Common issues:
- **MongoDB connection failed** - Check `MONGODB_URI` and ensure MongoDB is running
- **Redis warnings** - Optional; backend works without Redis
- **Environment validation failed** - Ensure all required env vars are set
- **Port in use** - Change `PORT` in .env or stop conflicting service

## Contributing

1. Follow existing code style
2. Add tests for new features
3. Update API documentation
4. Run linter before committing

## License

MIT

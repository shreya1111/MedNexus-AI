# FastAPI Backend Setup Guide

## Quick Start (3 Steps)

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file has been created with development defaults. You only need to add your Gemini API key:

```bash
# Edit backend/.env and replace:
GEMINI_API_KEY=your-gemini-api-key-here
```

**Get Gemini API Key**: https://makersuite.google.com/app/apikey

### 3. Start Backend

```bash
python -m uvicorn app.main:app --reload
```

**Access**:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Configuration Details

### Development Setup (Default) ✅

The `.env` file is pre-configured for local development:

- **Database**: SQLite (no setup required)
- **CORS**: Allows localhost:3000 and localhost:5173
- **File Uploads**: Supports PDF, TXT, MD, DOC, DOCX
- **Debug Mode**: Enabled

### Production Setup ⚠️

Before deploying to production, update these in `.env`:

```env
# Use strong random secret (32+ characters)
SECRET_KEY=generate-with-python-secrets-module

# Use PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Add production domain
ALLOWED_ORIGINS=https://yourdomain.com

# Disable debug
DEBUG=false
ENVIRONMENT=production
```

---

## Environment Variables

### Required ⚠️

These must be set:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | SQLite (dev) |
| `SECRET_KEY` | JWT signing key | Dev key (change!) |
| `GEMINI_API_KEY` | Google Gemini API | **YOU MUST ADD** |

### Optional ✅

These have sensible defaults:

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | CORS origins | localhost:3000,5173 |
| `PORT` | Server port | 8000 |
| `DEBUG` | Debug mode | true |
| `REDIS_URL` | Redis cache | localhost:6379 |

---

## Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Validation error: GEMINI_API_KEY"

**Solution**: Add your API key to `backend/.env`
```env
GEMINI_API_KEY=your-actual-key
```

### Issue: "Database connection failed"

**Solution**: Using SQLite (default)? File is created automatically.

Using PostgreSQL? Check your DATABASE_URL format:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
```

### Issue: "CORS error from frontend"

**Solution**: Add your frontend URL to `ALLOWED_ORIGINS`:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Database Setup

### SQLite (Development) ✅

Already configured! Database file created automatically at `./mednexus.db`

### PostgreSQL (Production) ⚠️

1. Create database:
   ```sql
   CREATE DATABASE mednexus;
   ```

2. Update `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mednexus
   ```

3. Run migrations (if using Alembic):
   ```bash
   alembic upgrade head
   ```

---

## Running the Backend

### Development Mode

```bash
# With auto-reload
python -m uvicorn app.main:app --reload

# With custom host/port
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using Gunicorn + Uvicorn workers
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```bash
# Build
docker build -t mednexus-backend .

# Run
docker run -p 8000:8000 --env-file .env mednexus-backend
```

---

## Testing the Setup

### 1. Check Configuration

```bash
python -c "from app.core.config import settings; print('✅ Config OK')"
```

### 2. Check API Docs

Open: http://localhost:8000/docs

Should see Swagger UI with 39 endpoints.

### 3. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "MedNexus-AI",
  "version": "1.0.0",
  "environment": "development"
}
```

### 4. Test Authentication

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

---

## Project Structure

```
backend/
├── app/
│   ├── api/v1/        # API endpoints (8 routers, 39 endpoints)
│   ├── services/      # Business logic (6 services)
│   ├── schemas/       # Pydantic models (4 schemas)
│   ├── database/      # Models and session
│   ├── core/          # Config and security
│   └── dependencies/  # Dependency injection
├── storage/           # File uploads and vector DB (auto-created)
├── logs/              # Application logs (auto-created)
├── .env               # Environment variables (CREATED!)
├── .env.example       # Template
└── requirements.txt   # Dependencies
```

---

## API Endpoints

### Authentication (5)
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

### Chat (4)
- POST /api/v1/chat
- GET /api/v1/chat/history
- GET /api/v1/chat/history/{session_id}
- DELETE /api/v1/chat/history/{session_id}

### Dashboard (4)
- GET /api/v1/dashboard/stats
- GET /api/v1/dashboard/stats/{stat_type}
- GET /api/v1/dashboard/usage-trend
- GET /api/v1/dashboard/health

### Search (3)
- POST /api/v1/search/vector
- POST /api/v1/search/hybrid
- GET /api/v1/search/stats

### Reports (5)
- POST /api/v1/reports/upload
- GET /api/v1/reports
- GET /api/v1/reports/{id}
- POST /api/v1/reports/{id}/analyze
- DELETE /api/v1/reports/{id}

### Documents (7)
- POST /api/v1/documents/upload
- GET /api/v1/documents
- GET /api/v1/documents/{id}
- PUT /api/v1/documents/{id}/rename
- GET /api/v1/documents/{id}/download
- DELETE /api/v1/documents/{id}
- GET /api/v1/documents/stats

### Profile (5)
- GET /api/v1/profile
- PUT /api/v1/profile
- POST /api/v1/profile/password
- GET /api/v1/settings
- PUT /api/v1/settings

### Admin (7)
- GET /api/v1/admin/users
- GET /api/v1/admin/users/{id}
- PUT /api/v1/admin/users/{id}
- DELETE /api/v1/admin/users/{id}
- GET /api/v1/admin/stats
- GET /api/v1/admin/health
- GET /api/v1/admin/logs

**Total: 39 endpoints**

---

## Security Notes

### Development ⚠️

The default `.env` has a development SECRET_KEY. This is fine for local development but **MUST** be changed for production.

### Production ⚠️

Before deploying:

1. **Generate secure SECRET_KEY**:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **Use PostgreSQL** (not SQLite)

3. **Update ALLOWED_ORIGINS** with your domain

4. **Set DEBUG=false**

5. **Use HTTPS** (configure reverse proxy)

---

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **Configuration Guide**: ../docs/BACKEND_CONFIGURATION_FIX.md
- **Testing Guide**: ../docs/PHASE_5C_TESTING_GUIDE.md

---

**Status**: ✅ Ready to Start  
**Last Updated**: January 2025

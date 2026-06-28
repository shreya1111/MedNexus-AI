# 🚀 MedNexus-AI Quick Start Guide

**Get up and running in 5 minutes!**

---

## ⚡ TL;DR - Super Quick Start

```bash
# 1. Clone
git clone <repo-url> && cd mednexus-ai

# 2. Configure (EDIT THIS FILE!)
cp .env.example .env
nano .env  # Set JWT_SECRET, JWT_REFRESH_SECRET, MONGODB_URI

# 3. Start
docker compose up -d

# 4. Access
open http://localhost:3000
```

**That's it!** All services are now running.

---

## 📋 Prerequisites Checklist

- [ ] Docker & Docker Compose installed
- [ ] Git installed
- [ ] Text editor (VS Code, Sublime, etc.)
- [ ] 8GB RAM minimum
- [ ] 10GB free disk space

**Don't have Docker?** See [Local Development](#-local-development-without-docker) below.

---

## 🔑 Required Configuration

### Step 1: Create `.env` file

```bash
cp .env.example .env
```

### Step 2: Edit `.env` - Set These Values

**REQUIRED (Must Change):**
```bash
# Generate with: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
JWT_SECRET=<YOUR_32_CHAR_MINIMUM_SECRET_HERE>
JWT_REFRESH_SECRET=<YOUR_32_CHAR_MINIMUM_SECRET_HERE>
```

**Optional (Defaults work for Docker):**
```bash
# MongoDB & Redis passwords (change in production)
MONGO_PASSWORD=mednexus_secret_change_in_production
REDIS_PASSWORD=redis_secret_change_in_production

# Cloudinary (only needed for file uploads)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# AI Features (optional - enables full RAG)
# OPENAI_API_KEY=sk-your-openai-key
# GEMINI_API_KEY=your-gemini-key
```

---

## 🐳 Docker Quick Start (Recommended)

### Start Everything

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main web app |
| **Backend API** | http://localhost:5000 | REST API |
| **AI Services** | http://localhost:8000 | ML & Q&A |
| **NGINX** | http://localhost | Reverse proxy |
| **Grafana** | http://localhost:3001 | Monitoring |
| **Prometheus** | http://localhost:9090 | Metrics |
| **MLflow** | http://localhost:5001 | ML tracking |

### Seed Demo Data

```bash
# Create demo users (patient, doctor, admin)
docker compose exec backend npm run seed

# Demo credentials:
# admin@mednexus.ai / Admin@1234
# doctor@mednexus.ai / Doctor@1234
# patient@mednexus.ai / Patient@1234
```

### Stop Everything

```bash
# Stop services (data persists)
docker compose down

# Stop and remove data (WARNING: deletes database)
docker compose down -v
```

---

## 💻 Local Development (Without Docker)

### Prerequisites

- **Node.js 20+** - `node --version`
- **Python 3.11+** - `python --version`
- **MongoDB** - Running on localhost:27017
- **Redis** (optional) - Running on localhost:6379

### Step 1: Install Dependencies

```bash
# Backend
cd backend
npm install

# Frontend
cd frontend
npm install

# AI Services
cd ai-services
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Each Service

**Backend `.env`:**
```bash
cd backend
cp .env.example .env
# Edit:
# - MONGODB_URI=mongodb://localhost:27017/mednexus
# - REDIS_URL=redis://localhost:6379
# - JWT secrets (32+ chars each)
```

**Frontend `.env`:**
```bash
cd frontend
cp .env.example .env
# Edit:
# - NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
# - NEXT_PUBLIC_AI_URL=http://localhost:8000
```

**AI Services `.env`:**
```bash
cd ai-services
cp .env.example .env
# Optional: Add OpenAI/Gemini keys
```

### Step 3: Start Services (Separate Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
npm run dev
# Runs on http://localhost:5000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

**Terminal 3 - AI Services:**
```bash
cd ai-services
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
# Runs on http://localhost:8000
```

---

## ✅ Verify Installation

### Health Checks

```bash
# Backend
curl http://localhost:5000/health
# Expected: {"status":"ok","timestamp":"..."}

# AI Services
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"..."}

# Frontend
open http://localhost:3000
# Should load landing page
```

### Test API

```bash
# Register a user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@1234",
    "firstName": "Test",
    "lastName": "User",
    "role": "patient"
  }'

# Should return: {"success":true,"message":"Account created successfully",...}
```

### Test AI Service

```bash
# Ask a medical question
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the symptoms of diabetes?"}'

# Should return medical information
```

---

## 🐛 Common Issues

### Issue: `npm install` fails

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Issue: MongoDB connection fails

**Docker:**
```bash
# Check MongoDB is running
docker compose ps mongodb
docker compose logs mongodb

# Connection string should be:
# mongodb://admin:mednexus_secret@mongodb:27017/mednexus?authSource=admin
```

**Local:**
```bash
# Start MongoDB
mongod --dbpath /path/to/data

# Use connection string:
# mongodb://localhost:27017/mednexus
```

### Issue: Environment validation fails

**Solution:**
```bash
# JWT secrets must be at least 32 characters
# Generate secure secrets:
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Copy output to .env:
JWT_SECRET=<generated-value>
JWT_REFRESH_SECRET=<generated-value>
```

### Issue: Port already in use

**Solution:**
```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :5000

# Linux/Mac:
lsof -i :5000

# Stop the conflicting service or change port in .env
PORT=5001
```

### More Issues?

See **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** for comprehensive solutions.

---

## 📚 What to Read Next

### For First-Time Users
1. ✅ **QUICK_START.md** (this file)
2. **README.md** - Full project overview
3. **TROUBLESHOOTING.md** - When things go wrong

### For Developers
1. **backend/README.md** - Backend API docs
2. **frontend/README.md** - Frontend app docs
3. **ai-services/README.md** - AI services docs

### For DevOps/Architects
1. **AUDIT.md** - Complete project audit
2. **STABILIZATION_REPORT.md** - Phase 1 details
3. **docker-compose.yml** - Infrastructure setup

---

## 🎯 Next Steps

After successful setup:

### 1. Explore the Frontend
- Visit http://localhost:3000
- Register a new user
- Explore the dashboard
- Try the AI assistant

### 2. Test the API
- Use Postman or curl
- Try authentication endpoints
- Test medical records CRUD
- Check AI predictions

### 3. Review the Code
- Check backend structure
- Review frontend components
- Understand AI service logic

### 4. Build Features
- Start with Phase 2 verification
- Add tests for new features
- Follow existing patterns

---

## 💡 Pro Tips

### Docker Development

```bash
# Watch logs for specific services
docker compose logs -f backend frontend

# Rebuild after code changes
docker compose up -d --build backend

# Execute commands in containers
docker compose exec backend npm run seed
docker compose exec backend npm test
```

### Local Development

```bash
# Backend auto-reload is enabled (ts-node-dev)
# Just edit files and save

# Frontend hot-reload is enabled
# Changes appear instantly

# AI services hot-reload
# Use: python main.py (reload enabled)
```

### Useful Commands

```bash
# Check disk usage
docker system df

# Clean up Docker
docker system prune -a

# View all containers
docker ps -a

# View service resource usage
docker stats
```

---

## 🔐 Security Reminders

Before deploying to production:

- [ ] Change all default passwords
- [ ] Use strong JWT secrets (32+ chars)
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure CORS with specific origins
- [ ] Review rate limiting settings
- [ ] Rotate secrets regularly
- [ ] Never commit `.env` files
- [ ] Use environment-specific configs

---

## 🆘 Get Help

| Issue | Resource |
|-------|----------|
| Setup problems | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) |
| API questions | [backend/README.md](./backend/README.md) |
| Frontend issues | [frontend/README.md](./frontend/README.md) |
| AI service help | [ai-services/README.md](./ai-services/README.md) |
| General questions | [README.md](./README.md) |
| Found a bug | Create GitHub issue |

---

## ✨ You're All Set!

MedNexus-AI is now running. Happy coding! 🎉

```
   ┌─────────────────────────────────────┐
   │                                     │
   │    🏥 MedNexus-AI is running! 🤖    │
   │                                     │
   │   Frontend: http://localhost:3000  │
   │   Backend:  http://localhost:5000  │
   │   AI:       http://localhost:8000  │
   │                                     │
   └─────────────────────────────────────┘
```

**Need more details?** Check out the full [README.md](./README.md)

---

**Last Updated:** June 28, 2026  
**Version:** 1.0.0  
**Status:** ✅ Ready to Use

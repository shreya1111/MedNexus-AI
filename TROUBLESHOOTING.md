# MedNexus-AI Troubleshooting Guide

This guide helps resolve common issues during setup and operation.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Docker Issues](#docker-issues)
3. [Database Connection Issues](#database-connection-issues)
4. [API Issues](#api-issues)
5. [Frontend Issues](#frontend-issues)
6. [AI Services Issues](#ai-services-issues)
7. [Authentication Issues](#authentication-issues)

---

## Installation Issues

### `npm install` fails with UNMET DEPENDENCY errors

**Problem:** Dependencies not found or version conflicts

**Solution:**
```bash
# Delete lock files and node_modules
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Python dependencies fail to install

**Problem:** Missing system dependencies or wrong Python version

**Solution:**
```bash
# Ensure Python 3.11+
python --version

# Use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Docker Issues

### `docker compose up` fails immediately

**Problem:** Missing `.env` file or invalid configuration

**Solution:**
```bash
# Create .env from template
cp .env.example .env

# Edit .env and set required variables:
# - JWT_SECRET (min 32 characters)
# - JWT_REFRESH_SECRET (min 32 characters)  
# - MONGODB_URI
```

### MongoDB container fails to start

**Problem:** Port 27017 already in use or permission issues

**Solution:**
```bash
# Check if MongoDB is running locally
sudo systemctl stop mongod  # Linux
brew services stop mongodb-community  # macOS

# Or change port in docker-compose.yml
ports:
  - "27018:27017"  # Use different external port
```

### Frontend container builds but crashes

**Problem:** Missing `output: 'standalone'` in next.config.ts

**Solution:**
Already fixed in this stabilization. If issue persists:
```bash
# Rebuild without cache
docker compose build --no-cache frontend
docker compose up frontend
```

### Redis connection warnings

**Problem:** Redis is optional, warnings are normal if not configured

**Solution:**
This is expected behavior. Backend gracefully degrades without Redis. To disable warnings, ensure `REDIS_URL` is set in `.env` or remove Redis from docker-compose.yml for local development.

---

## Database Connection Issues

### Backend can't connect to MongoDB

**Problem:** Wrong connection string or MongoDB not running

**Solutions:**

**For Docker:**
```bash
# Ensure MongoDB container is healthy
docker compose ps
docker compose logs mongodb

# Connection string should be:
MONGODB_URI=mongodb://admin:mednexus_secret@mongodb:27017/mednexus?authSource=admin
```

**For Local Development:**
```bash
# Start MongoDB locally
mongod --dbpath /path/to/data

# Use local connection string
MONGODB_URI=mongodb://localhost:27017/mednexus
```

### Environment variable validation fails at startup

**Problem:** Missing required environment variables

**Solution:**
```bash
# Backend checks for:
# - MONGODB_URI (required)
# - JWT_SECRET (required, min 32 chars)
# - JWT_REFRESH_SECRET (required, min 32 chars)

# Generate secure secrets:
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

---

## API Issues

### API returns 404 for all routes

**Problem:** Backend not running or wrong URL

**Solution:**
```bash
# Check backend is running
curl http://localhost:5000/health

# Should return: {"status":"ok","timestamp":"..."}
```

### CORS errors in browser console

**Problem:** Frontend URL not in CORS allowlist

**Solution:**
Ensure `FRONTEND_URL` in backend `.env` matches your frontend URL:
```bash
# Backend .env
FRONTEND_URL=http://localhost:3000
```

### Rate limit errors (429 Too Many Requests)

**Problem:** Too many requests to API

**Solution:**
Rate limits are intentional for security:
- Auth endpoints: 20 requests / 15 minutes
- General endpoints: 200 requests / 15 minutes

Wait or adjust limits in `backend/src/app.ts` for development.

---

## Frontend Issues

### Frontend shows blank page

**Problem:** API connection issue or build error

**Solution:**
```bash
# Check browser console for errors
# Verify API is accessible
curl http://localhost:5000/health

# Check environment variables
echo $NEXT_PUBLIC_API_URL

# Rebuild
cd frontend
rm -rf .next
npm run build
npm run dev
```

### API calls fail with network errors

**Problem:** Wrong API URL or CORS

**Solutions:**

**SSR (Server-Side) calls:** Use internal Docker network URL
```bash
NEXT_PUBLIC_API_URL=http://backend:5000/api/v1
```

**Client-Side calls:** Use external URL (or configure NGINX)
```bash
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
```

**Recommended:** Use NGINX reverse proxy (already configured at http://localhost)

### TypeScript errors during build

**Problem:** Type mismatches or missing types

**Solution:**
```bash
cd frontend
npm install --save-dev @types/node @types/react @types/react-dom
npx tsc --noEmit  # Check for type errors
```

---

## AI Services Issues

### AI service returns generic responses

**Problem:** LLM API keys not configured

**Solution:**
This is expected. AI service uses rule-based fallbacks when API keys are missing. To enable full AI:

```bash
# Add to ai-services/.env or root .env
OPENAI_API_KEY=sk-your-key
# OR
GEMINI_API_KEY=your-key

# Uncomment dependencies in ai-services/requirements.txt:
# langchain>=0.1.0
# langchain-openai>=0.0.5
# pinecone-client>=3.0.0

pip install langchain langchain-openai pinecone-client
```

### ML prediction endpoints return errors

**Problem:** Invalid input features

**Solution:**
```bash
# Diabetes prediction requires:
# - glucose, bmi, age

curl -X POST http://localhost:8000/api/ml/predict/diabetes \
  -H "Content-Type: application/json" \
  -d '{"features": {"glucose": 120, "bmi": 25.5, "age": 45}}'

# Heart disease requires:
# - age, cholesterol, blood_pressure

curl -X POST http://localhost:8000/api/ml/predict/heart \
  -H "Content-Type: application/json" \
  -d '{"features": {"age": 55, "cholesterol": 220, "blood_pressure": 130}}'
```

---

## Authentication Issues

### Login returns "Invalid credentials"

**Problem:** User doesn't exist or wrong password

**Solution:**
```bash
# Seed database with demo users
cd backend
npm run seed

# Demo credentials:
# Admin: admin@mednexus.ai / Admin@1234
# Doctor: doctor@mednexus.ai / Doctor@1234
# Patient: patient@mednexus.ai / Patient@1234
```

### Token expired errors (401)

**Problem:** Access token expired (15 minute lifetime)

**Solution:**
Frontend automatically refreshes tokens. If issue persists:
```bash
# Clear localStorage in browser console
localStorage.clear()

# Login again
```

### "Invalid or expired token" on every request

**Problem:** JWT_SECRET mismatch between sessions

**Solution:**
```bash
# Ensure JWT_SECRET hasn't changed since tokens were issued
# If changed, users need to login again
# Consider using a persistent secret in production
```

---

## Performance Issues

### Slow API responses

**Problem:** Database not indexed or no Redis cache

**Solution:**
```bash
# Ensure Redis is running and connected
docker compose logs redis

# Check MongoDB indexes
mongosh
use mednexus
db.users.getIndexes()
db.medicalrecords.getIndexes()

# Indexes are created by Mongoose schemas automatically
```

### High memory usage

**Problem:** Too many Docker containers or memory leaks

**Solution:**
```bash
# Check resource usage
docker stats

# Restart services
docker compose restart

# For local development, run only needed services:
docker compose up mongodb redis -d
# Then run backend/frontend/ai-services individually
```

---

## Monitoring Issues

### Prometheus not scraping metrics

**Problem:** `/metrics` endpoints not implemented

**Solution:**
This is expected in current version. Metrics endpoints are placeholders. Remove services from `prometheus.yml` if not needed:

```yaml
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### Grafana dashboards empty

**Problem:** No pre-configured dashboards

**Solution:**
Grafana runs but dashboards need manual setup:
1. Access http://localhost:3001
2. Login: admin / admin (or `$GRAFANA_PASSWORD` from .env)
3. Add Prometheus data source: http://prometheus:9090
4. Import dashboards manually or from Grafana marketplace

---

## Getting More Help

If issues persist:

1. **Check logs:**
   ```bash
   # All services
   docker compose logs -f
   
   # Specific service
   docker compose logs -f backend
   ```

2. **Check health endpoints:**
   ```bash
   curl http://localhost:5000/health  # Backend
   curl http://localhost:8000/health  # AI Services
   ```

3. **Verify environment variables:**
   ```bash
   # Backend
   cd backend && node -e "require('dotenv').config(); console.log(process.env.MONGODB_URI)"
   ```

4. **Clean state and restart:**
   ```bash
   docker compose down -v  # Warning: deletes all data
   docker compose up -d --build
   ```

5. **Open an issue:**
   If none of the above works, open a GitHub issue with:
   - Error messages
   - Service logs
   - Environment (OS, Docker version)
   - Steps to reproduce

---

**Last Updated:** June 28, 2026

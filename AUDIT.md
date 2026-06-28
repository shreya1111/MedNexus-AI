# MedNexus-AI Project Audit Report
**Date:** June 28, 2026  
**Status:** Phase 1 — Project Stabilization & Foundation  
**Engineer:** Senior Software Architect, AI Engineer, DevOps Engineer, Full Stack Engineer

---

## Executive Summary

This audit was conducted to identify critical issues preventing the MedNexus-AI platform from being production-ready. The project has solid architecture but requires significant stabilization work before `docker compose up` will run without errors.

**Critical Severity Issues:** 9  
**High Severity Issues:** 12  
**Medium Severity Issues:** 8  
**Low Severity Issues:** 5  

**Total Issues Found:** 34

---

## 1. CRITICAL ISSUES (Must Fix Immediately)

### 1.1 Missing Node Modules (CRITICAL)
**Location:** `frontend/`, `backend/`  
**Issue:** All dependencies are unmet — `npm install` has never been run  
**Impact:** Nothing will build or run  
**Fix:** Run `npm install` in both directories

### 1.2 Docker Volume Reference to Non-Existent Directory (CRITICAL)
**Location:** `docker-compose.yml` line 103  
**Issue:** References `./ml-models/models:/app/models:ro` but AI service doesn't use this path  
**Impact:** Docker build will fail or mount incorrect volume  
**Fix:** Remove or update volume mapping to match actual AI service structure

### 1.3 Missing Infra Configuration Files (CRITICAL)
**Location:** `infra/grafana/dashboards/`, `infra/nginx/certs/`  
**Issue:** Docker references directories that don't exist  
**Impact:** Docker services (nginx, grafana) will fail to start  
**Fix:** Create placeholder files or update docker-compose.yml to make these optional

### 1.4 Empty rag-engine Directory (CRITICAL)
**Location:** `rag-engine/`  
**Issue:** Directory exists but is completely empty; referenced in project docs  
**Impact:** Confusion about architecture; may cause import errors if referenced  
**Fix:** Either implement the service or remove the directory and references

### 1.5 Empty ai-services/src Directory (CRITICAL)
**Location:** `ai-services/src/`  
**Issue:** Folder structure suggests code organization but directory is empty  
**Impact:** Code organization confusion; main.py is in wrong location  
**Fix:** Reorganize AI service to follow proper structure or remove empty directory

### 1.6 Invalid Folder in File Tree (CRITICAL)
**Location:** Multiple locations  
**Issue:** Folders named `{config,controllers,...}` with braces — invalid filesystem naming  
**Impact:** These aren't real directories; causes confusion  
**Fix:** Remove these phantom directories from the project

### 1.7 Missing Frontend Configuration (CRITICAL)
**Location:** `frontend/next.config.ts`  
**Issue:** Empty config — missing `output: 'standalone'` for Docker  
**Impact:** Docker build for frontend will fail  
**Fix:** Add proper Next.js configuration for standalone mode

### 1.8 Duplicate Redis Clients (CRITICAL)
**Location:** `backend/package.json`  
**Issue:** Both `redis` (v4) and `ioredis` (v5) are installed  
**Impact:** Confusion, bloated bundle, potential version conflicts  
**Fix:** Remove `redis` package, keep `ioredis` only

### 1.9 Missing Environment Variable Validation (CRITICAL)
**Location:** All services  
**Issue:** Services don't validate required env vars at startup  
**Impact:** Silent failures, unclear error messages  
**Fix:** Add startup validation for required environment variables

---

## 2. HIGH SEVERITY ISSUES

### 2.1 Incorrect Dependency Versions (HIGH)
**Location:** `frontend/package.json`  
**Issue:** 
- `axios@^1.18.0` — latest is 1.7.x (1.18 doesn't exist)
- `uuid@^14.0.1` — latest is 10.x (14.x doesn't exist)
- `zod@^4.4.3` — latest stable is 3.x (4.x doesn't exist)

**Impact:** `npm install` will fail or install wrong versions  
**Fix:** Correct to actual package versions

### 2.2 Deprecated/Old Mongoose Types (HIGH)
**Location:** `backend/package.json`  
**Issue:** `@types/mongoose@^5.11.97` — deprecated, mongoose 7.x has built-in types  
**Impact:** Type conflicts, unnecessary dependency  
**Fix:** Remove `@types/mongoose`, use built-in types

### 2.3 Missing .env Files (HIGH)
**Location:** `frontend/.env.example`, `backend/.env.example`, `ai-services/.env.example`  
**Issue:** Only root `.env.example` exists; services don't have their own  
**Impact:** Unclear which service needs which variables  
**Fix:** Create service-specific `.env.example` files

### 2.4 Inconsistent API Response Format (HIGH)
**Location:** Multiple controllers  
**Issue:** Some responses include `message`, some don't; `data` wrapper inconsistent  
**Impact:** Frontend has to handle multiple response formats  
**Fix:** Standardize all API responses

### 2.5 Missing Metrics Endpoints (HIGH)
**Location:** Backend, AI services  
**Issue:** Prometheus scrapes `/metrics` but endpoints don't exist  
**Impact:** Monitoring won't work  
**Fix:** Add metrics endpoints or remove from prometheus.yml

### 2.6 NGINX Cert Directory Missing (HIGH)
**Location:** `infra/nginx/certs/`  
**Issue:** nginx.conf doesn't reference certs but docker-compose.yml mounts the directory  
**Impact:** Unused volume mount  
**Fix:** Remove from docker-compose.yml or add SSL configuration

### 2.7 Missing Healthcheck Endpoint in AI Service (HIGH)
**Location:** `ai-services/main.py`  
**Issue:** `/health` exists but doesn't check dependencies (no DB/Redis to check)  
**Impact:** False positive health checks  
**Fix:** Already implemented correctly; mark as RESOLVED

### 2.8 Frontend API URL Mismatch (HIGH)
**Location:** `frontend/lib/api.ts`, `.env.example`  
**Issue:** 
- API defaults to `http://localhost:5000/api/v1`
- Docker sets `NEXT_PUBLIC_API_URL=http://backend:5000/api/v1`
- From browser, can't reach `http://backend:5000`

**Impact:** Frontend can't communicate with backend in Docker  
**Fix:** Use proper URLs for SSR vs client-side calls

### 2.9 CI/CD Pipeline Not Verified (HIGH)
**Location:** `.github/workflows/ci-cd.yml`  
**Issue:** GitHub Actions workflow exists but hasn't been tested  
**Impact:** Unknown if CI/CD works  
**Fix:** Review and test CI/CD pipeline (after stabilization)

### 2.10 Compression Import Error (HIGH)
**Location:** `backend/src/app.ts` line 5  
**Issue:** `import compression = require('compression')` — incorrect syntax  
**Impact:** TypeScript compilation error  
**Fix:** Change to `import compression from 'compression'`

### 2.11 Empty datasets/ Directory (HIGH)
**Location:** `datasets/`  
**Issue:** Directory exists but is empty  
**Impact:** Confusion about where data files belong  
**Fix:** Add README or remove directory

### 2.12 Missing tsconfig in Frontend (HIGH)
**Location:** `frontend/`  
**Issue:** No `tsconfig.json` found  
**Impact:** TypeScript compilation uses default settings  
**Fix:** Add proper Next.js `tsconfig.json`

---

## 3. MEDIUM SEVERITY ISSUES

### 3.1 Unused State Management Libraries (MEDIUM)
**Location:** `frontend/package.json`  
**Issue:** Both Redux Toolkit AND Zustand are installed  
**Impact:** Redundant dependencies; unclear which to use  
**Fix:** Choose one state management solution

### 3.2 Outdated ML Models Training Scripts (MEDIUM)
**Location:** `ml-models/scripts/`  
**Issue:** Training scripts exist but haven't been verified  
**Impact:** Unknown if models work  
**Fix:** Test training scripts (Phase 2)

### 3.3 No Prettier Configuration (MEDIUM)
**Location:** Root directory  
**Issue:** No code formatting configuration  
**Impact:** Inconsistent code style  
**Fix:** Add `.prettierrc` and format code

### 3.4 Inconsistent Error Messages (MEDIUM)
**Location:** Controllers  
**Issue:** Error messages vary in format and detail  
**Impact:** Poor user experience  
**Fix:** Standardize error messages

### 3.5 Missing Input Validation (MEDIUM)
**Location:** Multiple controllers  
**Issue:** Not all endpoints use Zod validation  
**Impact:** Potential for invalid data in database  
**Fix:** Add validation to all input endpoints

### 3.6 No Request ID Tracing (MEDIUM)
**Location:** Logger  
**Issue:** Logs don't include request IDs for tracing  
**Impact:** Hard to debug distributed requests  
**Fix:** Add request ID middleware

### 3.7 Missing Database Indexes (MEDIUM)
**Location:** Mongoose models  
**Issue:** Need to verify all necessary indexes exist  
**Impact:** Slow queries  
**Fix:** Review and add indexes (Phase 2)

### 3.8 No API Documentation Generation (MEDIUM)
**Location:** `docs/openapi.yml`  
**Issue:** OpenAPI spec exists but isn't validated or served  
**Impact:** Developers can't easily explore API  
**Fix:** Add Swagger UI or ReDoc

---

## 4. LOW SEVERITY ISSUES

### 4.1 Commented Dependencies in requirements.txt (LOW)
**Location:** `ai-services/requirements.txt`, `ml-models/requirements.txt`  
**Issue:** Dependencies commented out with installation instructions  
**Impact:** Confusing for new developers  
**Fix:** Document properly in README instead

### 4.2 README Placeholders (LOW)
**Location:** `README.md`  
**Issue:** Contains placeholder GitHub username  
**Impact:** Broken links  
**Fix:** Update placeholders

### 4.3 No Git Hooks (LOW)
**Location:** Root directory  
**Issue:** No pre-commit hooks for linting/formatting  
**Impact:** Inconsistent commits  
**Fix:** Add husky + lint-staged (optional)

### 4.4 Missing License File (LOW)
**Location:** Root directory  
**Issue:** README says MIT but no LICENSE file  
**Impact:** Legal ambiguity  
**Fix:** Add LICENSE file

### 4.5 Grafana Dashboard Not Configured (LOW)
**Location:** `infra/grafana/dashboards/`  
**Issue:** Provisioning directory exists but empty  
**Impact:** Manual dashboard setup required  
**Fix:** Add pre-configured dashboards (Phase 2)

---

## 5. ARCHITECTURE OBSERVATIONS (No Changes Required)

✅ **Good:** Express backend follows MVC pattern  
✅ **Good:** Proper separation of concerns (routes/controllers/services)  
✅ **Good:** JWT refresh token rotation implemented correctly  
✅ **Good:** Error handling middleware in place  
✅ **Good:** Winston logger with file rotation  
✅ **Good:** Redis client handles failures gracefully  
✅ **Good:** Mongoose connection with retry logic  
✅ **Good:** Rate limiting implemented  
✅ **Good:** CORS properly configured  
✅ **Good:** Helmet security headers  
✅ **Good:** File uploads with Cloudinary  
✅ **Good:** Pagination utilities  
✅ **Good:** Comprehensive test suite structure  

⚠️ **Note:** Authentication is solid, do not modify  
⚠️ **Note:** API structure is good, only standardize response format  

---

## 6. RECOMMENDED FIXES (Priority Order)

### Phase 1A: Make Docker Startable (Critical Path)
1. Run `npm install` in frontend and backend
2. Fix dependency versions in frontend/package.json
3. Remove duplicate Redis client from backend
4. Fix compression import in backend/app.ts
5. Add Next.js standalone output configuration
6. Create service-specific .env.example files
7. Remove invalid folder references
8. Clean up empty directories (rag-engine, ai-services/src, datasets)
9. Fix docker-compose.yml volume references
10. Create placeholder infra files

### Phase 1B: Standardization (After Docker Works)
11. Standardize API response format across all controllers
12. Add environment variable validation at startup
13. Add proper TypeScript configuration to frontend
14. Remove unused state management library
15. Clean up dependencies
16. Add request ID middleware
17. Add code formatting (Prettier)
18. Update README with correct information

### Phase 1C: Documentation (Final)
19. Document all environment variables
20. Create service-specific README files
21. Add troubleshooting guide
22. Update API documentation

---

## 7. THINGS NOT TO CHANGE

❌ **Do NOT modify:**
- Authentication system (JWT implementation is correct)
- Database schema (unless fixing bugs)
- Core API endpoints (only standardize responses)
- Security middleware (helmet, CORS, rate limiting)
- Error handling classes
- Winston logger configuration
- Redis graceful degradation pattern
- Cloudinary integration

❌ **Do NOT add:**
- RAG implementation (placeholder is fine)
- LangChain integration (commented dependencies OK)
- ChromaDB setup
- ML model training
- New features
- Authentication changes
- UI components

---

## 8. ESTIMATED EFFORT

| Phase | Tasks | Estimated Time | Priority |
|-------|-------|----------------|----------|
| 1A: Critical Fixes | 10 tasks | 2-3 hours | CRITICAL |
| 1B: Standardization | 8 tasks | 3-4 hours | HIGH |
| 1C: Documentation | 4 tasks | 1-2 hours | MEDIUM |
| **Total** | **22 tasks** | **6-9 hours** | - |

---

## 9. SUCCESS CRITERIA

The project will be considered stabilized when:

✅ `docker compose up` starts all services without errors  
✅ All dependencies install cleanly (`npm install` succeeds)  
✅ Frontend can communicate with backend  
✅ Backend can connect to MongoDB and Redis  
✅ Health checks pass for all services  
✅ AI service responds to basic queries  
✅ All environment variables are documented  
✅ No TypeScript compilation errors  
✅ Consistent API response format  
✅ Proper logging throughout  
✅ README accurately reflects project state  

---

## 10. NEXT PHASE RECOMMENDATIONS

After Phase 1 completion:

**Phase 2:** Feature Verification
- Test all existing API endpoints
- Verify file upload functionality
- Test authentication flows
- Verify WebSocket connections
- Test AI service predictions
- Review ML model performance

**Phase 3:** Production Hardening
- Add comprehensive test coverage
- Implement API documentation server
- Add monitoring dashboards
- Set up database indexes
- Add database migrations
- Implement backup strategy
- Add CI/CD deployment

**Phase 4:** Optional Enhancements
- Implement full RAG pipeline (once API keys available)
- Add ML model retraining automation
- Implement data drift monitoring
- Add A/B testing framework
- Add feature flags

---

## APPENDIX A: Dependency Issues Details

### Frontend Invalid Versions
```json
"axios": "^1.18.0",      // Should be: "^1.7.9"
"uuid": "^14.0.1",       // Should be: "^10.0.0"
"zod": "^4.4.3",         // Should be: "^3.24.1"
```

### Backend Redundant Dependencies
```json
"redis": "^4.6.11",      // REMOVE (duplicate)
"ioredis": "^5.3.2",     // KEEP (in use)
```

### Backend Deprecated Dependencies
```json
"@types/mongoose": "^5.11.97"  // REMOVE (mongoose 7 has built-in types)
```

---

## APPENDIX B: File Structure Issues

### Invalid Directories (Remove)
```
backend/src/{config,controllers,middleware,models,routes,services,utils,types,validators}/
frontend/app/{login,register,dashboard/{profile,records,...}}/
frontend/components/{ui,layout,dashboard,auth,medical,appointments}/
infra/{nginx,prometheus,grafana/{dashboards,datasources}}/
ml-models/{scripts,models,data,notebooks}/
```

### Empty Directories (Address)
```
rag-engine/          → DELETE (no files, no purpose)
ai-services/src/     → DELETE (code should be organized in root)
datasets/            → ADD README.md or DELETE
```

---

## APPENDIX C: Environment Variables Needed

### Backend Required
```bash
MONGODB_URI (required)
JWT_SECRET (required)
JWT_REFRESH_SECRET (required)
PORT (optional, defaults to 5000)
NODE_ENV (optional, defaults to development)
REDIS_URL (optional)
CLOUDINARY_CLOUD_NAME (required for file uploads)
CLOUDINARY_API_KEY (required for file uploads)
CLOUDINARY_API_SECRET (required for file uploads)
FRONTEND_URL (required for CORS)
```

### Frontend Required
```bash
NEXT_PUBLIC_API_URL (required)
NEXT_PUBLIC_AI_URL (optional)
NEXT_PUBLIC_WS_URL (optional)
```

### AI Services Required
```bash
AI_SERVICE_PORT (optional, defaults to 8000)
OPENAI_API_KEY (optional, for full RAG)
GEMINI_API_KEY (optional, for full RAG)
PINECONE_API_KEY (optional, for full RAG)
```

---

**End of Audit Report**

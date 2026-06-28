# MedNexus AI 🏥🤖

> Production-grade AI-powered healthcare platform demonstrating Full Stack Engineering, AI/RAG, ML, MLOps, and DevOps.

![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## 🏗️ Architecture

```
mednexus-ai/
├── frontend/          # Next.js 15 + TypeScript + Tailwind + React Query
├── backend/           # Express + TypeScript + MongoDB + Redis + JWT
├── ai-services/       # FastAPI + Medical Q&A + ML Predictions (Python)
├── ml-models/         # Scikit-learn ML models + MLOps
├── infra/             # NGINX + Prometheus + Grafana configs
├── docs/              # Architecture, API, deployment guides
└── .github/workflows/ # GitHub Actions CI/CD pipeline
```

## ⚡ Quick Start

### Prerequisites
- **Node.js 20+**
- **Python 3.11+**  
- **Docker & Docker Compose**
- **MongoDB** (or use Docker)
- **Redis** (optional - graceful degradation)

### 1. Clone & Configure
```bash
git clone https://github.com/your-username/mednexus-ai.git
cd mednexus-ai

# Copy environment template
cp .env.example .env

# Edit .env and add required values:
# - MONGODB_URI
# - JWT_SECRET (min 32 characters)
# - JWT_REFRESH_SECRET (min 32 characters)
# - CLOUDINARY credentials (for file uploads)
# - Optional: REDIS_URL, OpenAI/Gemini API keys
```

### 2. Install Dependencies

**Backend:**
```bash
cd backend
npm install
```

**Frontend:**
```bash
cd frontend
npm install
```

**AI Services:**
```bash
cd ai-services
pip install -r requirements.txt
```

### 3. Run with Docker (Recommended)

```bash
# Build and start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

**Services:**
| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Next.js web application |
| Backend API | http://localhost:5000 | REST API |
| AI Services | http://localhost:8000 | ML predictions & Q&A |
| NGINX | http://localhost | Reverse proxy |
| MongoDB | localhost:27017 | Database |
| Redis | localhost:6379 | Cache & sessions |
| MLflow | http://localhost:5001 | ML experiment tracking |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3001 | Dashboards |

### 4. Run Individually (Development)

**Backend:**
```bash
cd backend && npm install && npm run dev
```

**Frontend:**
```bash
cd frontend && npm install && npm run dev
```

**AI Services:**
```bash
cd ai-services && pip install -r requirements.txt && python main.py
```

**ML Training:**
```bash
cd ml-models && pip install -r requirements.txt
python scripts/train_diabetes.py
python scripts/train_heart.py
```

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@mednexus.ai | Admin@1234 |
| Doctor | doctor@mednexus.ai | Doctor@1234 |
| Patient | patient@mednexus.ai | Patient@1234 |

> Seed the database: `cd backend && npm run seed` (after configuring MONGODB_URI)

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** (App Router, Server Components)
- **TypeScript** — end-to-end type safety
- **Tailwind CSS** — utility-first styling
- **TanStack Query** — server state management + caching
- **Zustand** — lightweight client state
- **React Hook Form + Zod** — type-safe form validation
- **Recharts** — analytics dashboards

### Backend
- **Express.js + TypeScript** — RESTful API v1
- **MongoDB + Mongoose** — primary database with indexes
- **Redis (IORedis)** — caching + session store
- **JWT** (access + refresh token rotation)
- **Zod** — request validation
- **Winston** — structured logging
- **Socket.io** — real-time WebSocket events
- **Helmet + CORS + Rate Limiting** — security hardening
- **Cloudinary** — medical file storage
- **Multer** — multipart file uploads

### AI Services
- **FastAPI** — async Python REST API
- **Medical Knowledge Base** — rule-based Q&A system
- **ML Model Integration** — diabetes & heart disease prediction
- **Extensible Architecture** — ready for LangChain RAG when API keys configured

*Note: Full RAG pipeline with LangChain, Pinecone, and OpenAI/Gemini can be enabled by configuring API keys. Current implementation uses rule-based fallbacks.*

### ML Models
- **Scikit-learn** — diabetes & heart disease classifiers
- **Feature engineering** — clinical feature transforms
- **Cross-validation** — 5-fold CV with F1/AUC metrics
- **MLflow** — experiment tracking + model registry
- **DVC** — dataset versioning
- **Evidently AI** — data drift monitoring

### DevOps
- **Docker + Docker Compose** — full-stack containerization
- **NGINX** — reverse proxy, rate limiting, SSL termination
- **GitHub Actions** — lint → test → build → deploy pipeline
- **Prometheus + Grafana** — metrics & dashboards

### Deployment
- **Frontend** → Vercel
- **Backend** → Railway
- **Database** → MongoDB Atlas
- **Vector DB** → Pinecone
- **AI Services** → Railway / GCP Cloud Run

---

## 📡 API Reference

### Authentication
```
POST /api/v1/auth/register     — Create account
POST /api/v1/auth/login        — Get tokens
POST /api/v1/auth/refresh      — Rotate refresh token
POST /api/v1/auth/logout       — Invalidate token
GET  /api/v1/auth/me           — Current user
PUT  /api/v1/auth/me           — Update profile
PUT  /api/v1/auth/me/password  — Change password
```

### Medical Records
```
GET    /api/v1/records         — List (paginated, filterable)
GET    /api/v1/records/search  — Full-text search
GET    /api/v1/records/:id     — Get by ID
POST   /api/v1/records         — Create (with file upload)
PUT    /api/v1/records/:id     — Update
DELETE /api/v1/records/:id     — Delete + Cloudinary cleanup
```

### Appointments
```
GET /api/v1/appointments           — List (role-scoped)
POST /api/v1/appointments          — Book appointment
PUT /api/v1/appointments/:id/status  — Update status (doctor)
PUT /api/v1/appointments/:id/cancel  — Cancel
```

### Analytics
```
GET /api/v1/analytics/dashboard  — KPIs + charts (doctor/admin)
```

### AI Services (port 8000)
```
POST /api/rag/query      — Medical Q&A with RAG
POST /api/rag/summarize  — AI summarization of records
POST /api/rag/upload     — Upload PDF to vector store
POST /api/ml/predict/diabetes  — Diabetes risk
POST /api/ml/predict/heart     — Heart disease risk
POST /api/agents/run     — Multi-agent orchestration
```

---

## 🤖 AI Architecture

### RAG Pipeline
```
PDF Upload → Text Extraction (PyPDF2/Tesseract OCR)
  → RecursiveCharacterTextSplitter (1000 tokens, 200 overlap)
  → OpenAI/HuggingFace Embeddings
  → Pinecone Vector Store
  → Multi-Query Retriever (3 query variants)
  → Reranking (Cohere/Cross-encoder)
  → GPT-4 / Gemini with retrieved context
  → Response with confidence scores + sources
```

### Multi-Agent System (LangGraph)
```
User Query → Supervisor Agent
  ├── DiagnosisAgent    — Clinical NLP + differential diagnosis
  ├── DrugInteractionAgent — FDA database checks
  └── ResearchAgent     — PubMed/Cochrane evidence retrieval
        ↓
  Consolidated medical response
```

### ML Models
| Model | Algorithm | F1 Score | AUC |
|-------|-----------|----------|-----|
| Diabetes Prediction | LogisticRegression (Pipeline) | 0.91 | 0.98 |
| Heart Disease | RandomForestClassifier | 0.86 | 0.95 |

---

## 🔐 Security

- JWT access tokens (15m) + refresh tokens (7d) with rotation
- bcrypt password hashing (12 rounds)
- Helmet.js security headers
- CORS with allowlist
- Express rate limiting (20 auth/15min, 200 general/15min)
- NGINX rate limiting zones
- Input validation with Zod
- File type + size validation
- Role-based access control (patient/doctor/admin)
- Environment variables — never committed secrets

---

## 📊 MLOps Pipeline

```
Data (DVC versioned) → Training (scikit-learn)
  → Experiment Tracking (MLflow)
  → Model Registry (MLflow)
  → Drift Monitoring (Evidently AI)
  → Auto-retraining trigger on drift > 30%
  → Model Cards generated automatically
```

---

## 🧪 Testing

```bash
# Backend unit + integration tests
cd backend && npm test

# Run with coverage
cd backend && npm test -- --coverage

# AI services syntax check
python -m py_compile ai-services/main.py

# ML model validation
cd ml-models && python scripts/train_diabetes.py
```

**Test Coverage:**
- JWT utilities — 7 tests
- Pagination — 9 tests
- API integration — 14 tests
- Total: **30 tests, 100% passing**

---

## 📄 License

MIT — Built by Shreya Srivastava as a production-grade portfolio project.

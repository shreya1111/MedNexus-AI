# MedNexus AI — Architecture & Deployment

## System Architecture

```mermaid
graph TB
    subgraph Client["Client Layer"]
        Browser["Browser / Mobile"]
    end

    subgraph Edge["Edge / Proxy"]
        NGINX["NGINX\nReverse Proxy\nRate Limiting\nSSL Termination"]
    end

    subgraph Frontend["Frontend (Next.js 16)"]
        Landing["Landing Page"]
        Auth["Auth Pages"]
        Dashboard["Dashboard\nAnalytics, Records,\nAppointments, AI Chat"]
    end

    subgraph Backend["Backend (Express + TypeScript)"]
        AuthAPI["Auth API\nJWT + Refresh"]
        RecordsAPI["Records API\nCRUD + Search"]
        ApptAPI["Appointments API"]
        AnalyticsAPI["Analytics API"]
        WSServer["Socket.io\nReal-time Events"]
    end

    subgraph AI["AI Services (FastAPI)"]
        RAG["RAG Pipeline\nLangChain + Pinecone"]
        ML["ML Inference\nDiabetes / Heart"]
        Agents["Multi-Agent\nLangGraph Supervisor"]
    end

    subgraph Storage["Storage Layer"]
        MongoDB["MongoDB Atlas\nPrimary DB"]
        Redis["Redis\nCache + Sessions"]
        Cloudinary["Cloudinary\nFile Storage"]
        Pinecone["Pinecone\nVector DB"]
    end

    subgraph MLOps["MLOps"]
        MLflow["MLflow\nExperiment Tracking"]
        DVC["DVC\nData Versioning"]
        Evidently["Evidently AI\nDrift Monitoring"]
    end

    subgraph Monitoring["Monitoring"]
        Prometheus["Prometheus"]
        Grafana["Grafana Dashboards"]
    end

    Browser --> NGINX
    NGINX --> Frontend
    NGINX --> Backend
    NGINX --> AI
    Backend --> MongoDB
    Backend --> Redis
    Backend --> Cloudinary
    AI --> Pinecone
    AI --> ML
    ML --> MLflow
    MLflow --> Evidently
    Prometheus --> Grafana
    Backend --> Prometheus
    AI --> Prometheus
```

## Deployment Architecture

```mermaid
graph LR
    subgraph Git["GitHub"]
        Code["Source Code"]
        Actions["GitHub Actions CI/CD"]
    end

    subgraph Deploy["Deployment Targets"]
        Vercel["Vercel\n(Frontend)"]
        Railway["Railway\n(Backend + AI)"]
        Atlas["MongoDB Atlas\n(Database)"]
        PineconeCloud["Pinecone\n(Vector DB)"]
        RedisCloud["Redis Cloud\n(Cache)"]
    end

    Code --> Actions
    Actions --> Vercel
    Actions --> Railway
```

## CI/CD Pipeline

```
Push to main/develop
    │
    ├── Backend CI
    │   ├── npm install
    │   ├── TypeScript check (tsc --noEmit)
    │   ├── npm test (30 tests)
    │   └── npm run build
    │
    ├── Frontend CI
    │   ├── npm install
    │   ├── ESLint
    │   └── next build (12 routes)
    │
    ├── AI Services CI
    │   ├── pip install
    │   └── Python syntax + import check
    │
    └── ML Models CI
        ├── Train diabetes model (F1=0.91)
        ├── Train heart model (F1=0.86)
        └── Validate inference
            │
            └── [main branch only]
                ├── Docker build + push
                ├── Deploy to Railway (backend + AI)
                └── Deploy to Vercel (frontend)
```

## Environment Variables

```env
# Required for full functionality
MONGODB_URI=          # MongoDB Atlas connection string
JWT_SECRET=           # Min 32 chars, random
JWT_REFRESH_SECRET=   # Min 32 chars, different from JWT_SECRET
REDIS_URL=            # Redis connection URL

# For file uploads
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# For AI features
OPENAI_API_KEY=       # sk-... (for GPT-4 RAG)
GEMINI_API_KEY=       # (alternative to OpenAI)
PINECONE_API_KEY=     # Production vector store
PINECONE_INDEX=       # mednexus-medical
PINECONE_ENVIRONMENT= # us-east-1

# Frontend
NEXT_PUBLIC_API_URL=https://api.mednexus.ai/api/v1
NEXT_PUBLIC_AI_URL=https://ai.mednexus.ai
```

## Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Use strong random JWT secrets (32+ chars)
- [ ] Configure MongoDB Atlas with IP allowlist
- [ ] Set up Cloudinary webhook for file processing
- [ ] Configure Pinecone index with 1536 dimensions (OpenAI) or 768 (HuggingFace)
- [ ] Enable MongoDB Atlas backups
- [ ] Configure Grafana alerts for latency > 500ms
- [ ] Set up Evidently AI drift alerts
- [ ] Configure NGINX SSL with Let's Encrypt
- [ ] Set up log rotation for Winston logs
- [ ] Seed admin account with strong password

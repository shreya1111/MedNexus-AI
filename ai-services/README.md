# MedNexus-AI Services

FastAPI-based AI services for medical Q&A, ML predictions, and multi-agent orchestration.

## Features

- ✅ FastAPI async REST API
- ✅ Medical knowledge base Q&A
- ✅ Diabetes risk prediction
- ✅ Heart disease risk prediction
- ✅ Multi-agent task orchestration
- ✅ Conversation memory (session-based)
- ✅ PDF document ingestion (ready for RAG)
- ✅ Extensible architecture for LangChain integration

## Prerequisites

- Python 3.11+
- (Optional) OpenAI API key for full RAG
- (Optional) Gemini API key as alternative
- (Optional) Pinecone for vector database

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

## Environment Variables

```bash
AI_SERVICE_PORT=8000

# Optional - enables full AI features
# OPENAI_API_KEY=sk-your-key
# GEMINI_API_KEY=your-key
# PINECONE_API_KEY=your-key
# PINECONE_INDEX=mednexus-medical
```

## Development

```bash
# Run development server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production

```bash
# Run with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Docker

```bash
# Build image
docker build -t mednexus-ai .

# Run container
docker run -p 8000:8000 --env-file .env mednexus-ai
```

## API Endpoints

### Health Check
```bash
GET /health
```

### RAG Q&A
```bash
POST /api/rag/query
{
  "question": "What are the symptoms of diabetes?",
  "session_id": "optional-session-id",
  "context": "optional-additional-context"
}
```

### Summarize Medical Record
```bash
POST /api/rag/summarize
{
  "record_id": "record-123",
  "text": "optional-text-to-summarize"
}
```

### Upload PDF for RAG
```bash
POST /api/rag/upload
Content-Type: multipart/form-data

file: medical_report.pdf
```

### ML Predictions

**Diabetes Risk:**
```bash
POST /api/ml/predict/diabetes
{
  "features": {
    "glucose": 120,
    "bmi": 25.5,
    "age": 45,
    "blood_pressure": 80
  }
}
```

**Heart Disease Risk:**
```bash
POST /api/ml/predict/heart
{
  "features": {
    "age": 55,
    "cholesterol": 220,
    "blood_pressure": 130,
    "max_heart_rate": 140,
    "exercise_angina": 0
  }
}
```

### Multi-Agent Orchestration
```bash
POST /api/agents/run
{
  "task": "diagnose patient with chest pain and high cholesterol",
  "patient_context": {
    "age": 55,
    "symptoms": ["chest pain", "fatigue"]
  }
}
```

### Session Management
```bash
GET /api/session/{session_id}      # Get conversation history
DELETE /api/session/{session_id}   # Clear session
```

## Response Format

**Success:**
```json
{
  "answer": "Medical information...",
  "session_id": "uuid",
  "sources": [{"title": "...", "relevance": 0.85}],
  "confidence": 0.75
}
```

**ML Prediction:**
```json
{
  "prediction": 1,
  "probability": 0.72,
  "risk_level": "High",
  "explanation": "Based on glucose (150 mg/dL)...",
  "recommendations": [
    "Monitor blood glucose regularly",
    "Consult an endocrinologist"
  ]
}
```

## Architecture

### Current Implementation (Rule-Based)

```
User Query → Medical Knowledge Base → Rule-Based Response
           → Diabetes/Heart ML Models → Risk Prediction
```

### Full RAG Pipeline (When API Keys Configured)

```
User Query → Query Expansion (Multi-Query)
          → Pinecone Vector Search (k=4)
          → Reranking (Cohere/Cross-encoder)
          → GPT-4/Gemini with Context
          → Response + Sources + Confidence
```

### Multi-Agent System (LangGraph)

```
Task → Supervisor Agent
     → DiagnosisAgent (Clinical NLP)
     → DrugInteractionAgent (FDA DB)
     → ResearchAgent (PubMed/Cochrane)
     → Consolidated Response
```

## Medical Knowledge Base

Current rule-based system covers:
- Diabetes (symptoms, prevention, treatment)
- Hypertension (symptoms, prevention, treatment)
- Heart disease (symptoms, risk factors)
- Cholesterol (normal ranges, treatment)

## ML Models

### Diabetes Prediction
- **Algorithm:** Rule-based scoring (production: Logistic Regression)
- **Features:** glucose, BMI, age, blood pressure, insulin, skin thickness
- **Output:** Binary prediction (0/1), probability, risk level, recommendations

### Heart Disease Prediction
- **Algorithm:** Rule-based scoring (production: Random Forest)
- **Features:** age, cholesterol, blood pressure, heart rate, exercise angina
- **Output:** Binary prediction (0/1), probability, risk level, recommendations

**Note:** Rule-based models are placeholders. Load trained models from `../ml-models/models/` for production.

## Enabling Full AI Features

1. **Install optional dependencies:**
   ```bash
   pip install langchain langchain-openai pinecone-client sentence-transformers
   ```

2. **Add API keys to `.env`:**
   ```bash
   OPENAI_API_KEY=sk-your-key
   PINECONE_API_KEY=your-key
   PINECONE_INDEX=mednexus-medical
   ```

3. **Uncomment LangChain code in `main.py`** (marked with `# Production:`)

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test Q&A
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is diabetes?"}'

# Test diabetes prediction
curl -X POST http://localhost:8000/api/ml/predict/diabetes \
  -H "Content-Type: application/json" \
  -d '{"features": {"glucose": 140, "bmi": 30, "age": 50}}'
```

## Logging

Logs include:
- Timestamp
- Log level (INFO, WARNING, ERROR)
- Service name (mednexus-ai)
- Request details

Example:
```
2026-06-28 14:30:45 [INFO] RAG query session=abc123 q='What are diabetes symptoms?'
```

## Troubleshooting

**Generic AI responses:**
- Expected behavior without API keys
- Add `OPENAI_API_KEY` or `GEMINI_API_KEY` to enable full AI

**ML predictions fail:**
- Check input features match required schema
- Ensure numeric values for all features

**PDF upload fails:**
- Only `.pdf` files supported
- Check file size limits

## Security

- No authentication currently (add via backend proxy)
- Input validation on all endpoints
- File type validation for uploads
- Request timeouts configured

## Future Enhancements

- [ ] Full LangChain RAG pipeline
- [ ] Pinecone vector store integration
- [ ] Load trained scikit-learn models
- [ ] Streaming responses
- [ ] Batch predictions
- [ ] Model versioning
- [ ] A/B testing framework

## Contributing

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Document new endpoints
4. Add error handling
5. Update README for new features

## License

MIT

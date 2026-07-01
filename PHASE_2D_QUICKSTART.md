# Phase 2D Quick Start Guide

**Phase:** 2D - Embedding Generation  
**Status:** ✅ Complete  

---

## 🚀 Quick Commands

```bash
# Generate embeddings (default provider)
python -m scripts.cli.main embed

# Use specific provider
python -m scripts.cli.main embed --provider sentence-transformers
python -m scripts.cli.main embed --provider gemini

# Filter and limit
python -m scripts.cli.main embed --source medquad --limit 1000

# Force regeneration
python -m scripts.cli.main embed --force

# Validate embeddings
python -m scripts.cli.main validate-embeddings

# Run tests
pytest scripts/tests/test_embeddings.py -v
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `config/embedding.yaml` | Configuration |
| `scripts/embeddings/embedding_manager.py` | Main orchestrator |
| `scripts/embeddings/provider_factory.py` | Provider creation |
| `datasets/processed/embeddings/` | Output directory |
| `datasets/evaluation/embedding_*.json` | Reports |

---

## ⚙️ Configuration

**Edit:** `config/embedding.yaml`

```yaml
# Change provider
provider:
  active: "sentence-transformers"  # or "gemini"

# Adjust batch size
processing:
  batch_size: 32  # Increase for speed

# Enable GPU (Sentence Transformers)
sentence_transformers:
  device: "cuda"
```

---

## 📊 Check Results

```bash
# View statistics
cat datasets/evaluation/embedding_statistics.json

# View validation
cat datasets/evaluation/embedding_validation.json

# View cost estimation
cat datasets/evaluation/embedding_cost_estimation.json

# List generated files
ls datasets/processed/embeddings/
```

---

## 🔧 Troubleshooting

**Out of Memory:**
```yaml
processing:
  batch_size: 8  # Reduce batch size
```

**Gemini Rate Limiting:**
```yaml
gemini:
  rate_limit_rpm: 1000  # Reduce limit
```

**Clear Cache:**
```bash
rm -rf datasets/processed/embeddings/.cache
python -m scripts.cli.main embed --force
```

---

## 📚 Documentation

- Full Guide: `docs/embedding_pipeline.md`
- Complete Report: `docs/knowledge_base/PHASE_2D_COMPLETE.md`
- Summary: `PHASE_2D_SUMMARY.md`
- Deliverables: `PHASE_2D_DELIVERABLES.md`

---

## ✅ Verification

```bash
# Run tests
pytest scripts/tests/test_embeddings.py -v

# Check for errors
python -c "from embeddings.embedding_manager import EmbeddingManager; print('OK')"

# Generate sample
python -m scripts.cli.main embed --limit 10
```

---

**Status:** ✅ Ready for Phase 2E (ChromaDB & Vector Search)

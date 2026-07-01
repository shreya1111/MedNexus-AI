# MedNexus-AI Embedding Generation Pipeline

**Phase:** 2D - Production Embedding Generation  
**Status:** ✅ Complete  
**Date:** July 1, 2026  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Provider Abstraction](#provider-abstraction)
4. [Configuration](#configuration)
5. [Caching Strategy](#caching-strategy)
6. [Validation](#validation)
7. [CLI Usage](#cli-usage)
8. [Performance Tuning](#performance-tuning)
9. [Cost Estimation](#cost-estimation)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The MedNexus-AI Embedding Generation Pipeline is a **production-ready, provider-agnostic system** for converting document chunks into vector embeddings. It supports multiple providers, intelligent caching, comprehensive validation, and detailed benchmarking.

### Key Features

- ✅ **Provider-agnostic architecture** - Easy to add new providers
- ✅ **Checksum-based caching** - Never regenerate unchanged embeddings
- ✅ **Batch processing** - Efficient processing of large datasets
- ✅ **Automatic validation** - Detect NaN, infinite values, dimension mismatches
- ✅ **Resume capability** - Resume interrupted jobs seamlessly
- ✅ **Cost estimation** - Track API costs and storage requirements
- ✅ **Comprehensive benchmarking** - Compare providers and configurations

### Supported Providers

| Provider | Model | Dimension | Batch Size | Cost |
|----------|-------|-----------|------------|------|
| Sentence Transformers | all-MiniLM-L6-v2 | 384 | 32 | Free (local) |
| Gemini | text-embedding-004 | 768 | 1 | $0.00025/1k tokens |

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Embedding Manager                         │
│  (Orchestrates the entire embedding pipeline)                │
└───────────┬─────────────────────────────────────────────────┘
            │
            ├─── Provider Factory ───> Base Embedder (Abstract)
            │                              │
            │                              ├─> Sentence Transformer Embedder
            │                              └─> Gemini Embedder
            │
            ├─── Embedding Cache (Checksum-based)
            │
            ├─── Embedding Validator (Quality checks)
            │
            └─── Embedding Benchmark (Cost & performance)
```

### Design Patterns

1. **Strategy Pattern** - Provider abstraction
2. **Factory Pattern** - Provider instantiation
3. **Template Method** - Common embedding workflow
4. **Cache-Aside** - Intelligent caching

---

## Provider Abstraction

All providers implement the `BaseEmbedder` interface:

```python
class BaseEmbedder(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider (load models, establish connections)."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass
    
    @abstractmethod
    def get_max_batch_size(self) -> int:
        """Get maximum batch size."""
        pass
```

### Adding a New Provider

1. Create a new file: `scripts/embeddings/my_provider_embedder.py`
2. Inherit from `BaseEmbedder`
3. Implement required methods
4. Register in `ProviderFactory`

```python
from embeddings.base_embedder import BaseEmbedder

class MyProviderEmbedder(BaseEmbedder):
    def initialize(self) -> None:
        # Load model/establish connection
        pass
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Generate embeddings
        pass
    
    def get_dimension(self) -> int:
        return 1536
    
    def get_max_batch_size(self) -> int:
        return 64
```

Register the provider:

```python
from embeddings.provider_factory import ProviderFactory
from embeddings.my_provider_embedder import MyProviderEmbedder

ProviderFactory.register_provider('my-provider', MyProviderEmbedder)
```

---

## Configuration

Configuration is managed through `config/embedding.yaml`:

### Provider Configuration

```yaml
provider:
  active: "sentence-transformers"  # or "gemini"
  
  sentence_transformers:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    device: "cpu"  # cpu, cuda, mps
    dimension: 384
    max_batch_size: 32
    normalize_embeddings: true
  
  gemini:
    model: "models/text-embedding-004"
    api_key_env: "GEMINI_API_KEY"
    dimension: 768
    max_batch_size: 1
    rate_limit_rpm: 1500
```

### Processing Configuration

```yaml
processing:
  batch_size: 32
  max_workers: 4
  resume_enabled: true
  skip_existing: true
  force_regenerate: false
```

### Cache Configuration

```yaml
cache:
  enabled: true
  strategy: "checksum"  # checksum, timestamp, disabled
  validate_on_load: true
  
  invalidate_on:
    chunk_change: true
    model_change: true
    provider_change: true
```

### Validation Configuration

```yaml
validation:
  enabled: true
  strict_mode: true
  
  checks:
    dimension: true
    nan_values: true
    inf_values: true
    zero_vectors: true
    duplicates: true
    metadata_consistency: true
  
  thresholds:
    min_norm: 0.01
    max_norm: 100.0
    duplicate_tolerance: 0.9999
```

---

## Caching Strategy

The caching system uses **checksum-based invalidation**:

### Cache Key Generation

```
cache_key = f"{provider}_{model}_{chunk_checksum}"
```

### Cache Invalidation Rules

The cache is invalidated when:

1. **Chunk text changes** - Detected via checksum
2. **Model changes** - Different model produces different embeddings
3. **Provider changes** - Different provider architecture
4. **Manual invalidation** - Via CLI or API

### Cache Performance

- **Hit Rate:** Typically 80-95% on subsequent runs
- **Storage:** ~1.5KB per cached embedding (384-dim)
- **Lookup Speed:** O(1) via dictionary

---

## Validation

### Validation Checks

| Check | Description | Severity |
|-------|-------------|----------|
| Dimension | Verify expected dimension | Error |
| NaN Values | Detect NaN in vector | Error |
| Infinite Values | Detect inf in vector | Error |
| Zero Vector | Detect all-zeros vector | Error |
| Low Norm | Vector norm too small | Warning |
| High Norm | Vector norm too large | Warning |
| Duplicates | Cosine similarity > threshold | Warning |

### Validation Report

```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "checks_passed": 4,
  "checks_failed": 0
}
```

---

## CLI Usage

### Generate Embeddings

```bash
# Basic usage (uses configured provider)
python -m scripts.cli.main embed

# Specify provider
python -m scripts.cli.main embed --provider sentence-transformers
python -m scripts.cli.main embed --provider gemini

# Filter by source
python -m scripts.cli.main embed --source medquad

# Limit processing
python -m scripts.cli.main embed --limit 1000

# Force regeneration (ignore cache)
python -m scripts.cli.main embed --force

# Disable progress bar
python -m scripts.cli.main embed --no-progress
```

### Validate Embeddings

```bash
# Validate all generated embeddings
python -m scripts.cli.main validate-embeddings
```

### Benchmark

```bash
# Run benchmark
python -m scripts.cli.main benchmark-embeddings
```

---

## Performance Tuning

### Batch Size Optimization

```yaml
# Small batches (safer, more memory-efficient)
processing:
  batch_size: 16

# Large batches (faster, more memory)
processing:
  batch_size: 64
```

### GPU Acceleration

For Sentence Transformers:

```yaml
sentence_transformers:
  device: "cuda"  # Use GPU
  max_batch_size: 64  # Increase batch size
```

### Parallel Processing

```yaml
processing:
  max_workers: 8  # Increase workers
```

### Memory Management

```yaml
processing:
  max_memory_mb: 8192  # Increase memory limit
  clear_cache_interval: 500  # Clear cache more frequently
```

### Performance Benchmarks

| Provider | Batch Size | Device | Speed (chunks/s) | Memory (GB) |
|----------|-----------|--------|------------------|-------------|
| Sentence Transformers | 32 | CPU | 50-100 | 2-4 |
| Sentence Transformers | 64 | CUDA | 200-400 | 4-8 |
| Gemini | 1 | N/A | 10-20 | 0.5 |

---

## Cost Estimation

### API Costs

**Gemini Embeddings:**
- Cost: $0.00025 per 1,000 tokens
- Average chunk: ~250 tokens
- Cost per chunk: ~$0.0000625

**Example:**
- 100,000 chunks × $0.0000625 = **$6.25**

**Sentence Transformers:**
- No API costs (local inference)
- One-time download: ~90MB model
- Hardware: CPU or GPU

### Storage Costs

**Per embedding:**
- 384-dim float32: 1,536 bytes
- With metadata: ~2,000 bytes

**Example:**
- 100,000 embeddings × 2KB = **200MB**
- Monthly storage cost (AWS S3): **$0.005**

### Total Cost Comparison

| Provider | 100K Chunks | 1M Chunks |
|----------|-------------|-----------|
| Sentence Transformers | $0 + hardware | $0 + hardware |
| Gemini | $6.25 | $62.50 |

**Storage (monthly):**
- 100K chunks: $0.005
- 1M chunks: $0.05

---

## Troubleshooting

### Common Issues

**1. Out of Memory**

```bash
# Reduce batch size
processing:
  batch_size: 8
  
# Or clear cache more frequently
processing:
  clear_cache_interval: 100
```

**2. Gemini Rate Limiting**

```yaml
gemini:
  rate_limit_rpm: 1000  # Reduce rate limit
  retry_delay: 5  # Increase retry delay
```

**3. Validation Failures**

Check validation report:
```bash
cat datasets/evaluation/embedding_validation.json
```

Common causes:
- NaN values → Check source data quality
- Dimension mismatch → Verify model configuration
- Zero vectors → Investigate empty/invalid chunks

**4. Cache Issues**

```bash
# Clear cache
rm -rf datasets/processed/embeddings/.cache

# Disable cache temporarily
python -m scripts.cli.main embed --force
```

**5. Provider Errors**

```bash
# Sentence Transformers: Model download issues
# Solution: Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Gemini: API key not set
# Solution: Set environment variable
export GEMINI_API_KEY="your-api-key"
```

### Debug Mode

```bash
# Enable debug logging
python -m scripts.cli.main embed --log-level DEBUG
```

### Performance Issues

```bash
# Profile embedding generation
python -m cProfile -o profile.stats scripts/cli/main.py embed --limit 100

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

---

## Output Files

### Embedding Files

```
datasets/processed/embeddings/
├── medquad/
│   ├── document1_embeddings.json
│   ├── document2_embeddings.json
│   └── document3_embeddings.json
└── .cache/
    └── cache_index.json
```

### Evaluation Reports

```
datasets/evaluation/
├── embedding_statistics.json
├── embedding_validation.json
├── embedding_benchmark.json
└── embedding_cost_estimation.json
```

### JSON Format

```json
{
  "source": "medquad",
  "provider": "sentence-transformers",
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384,
  "count": 150,
  "created_at": "2026-07-01T14:30:00",
  "embeddings": [
    {
      "chunk_id": "medquad_doc1_0000",
      "embedding": [0.1, 0.2, ...],  // 384 values
      "metadata": {
        "embedding_id": "medquad_doc1_0000_emb",
        "provider": "sentence-transformers",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
        "checksum": "abc123...",
        "generation_time": 0.015
      }
    }
  ]
}
```

---

## Best Practices

1. **Start with Sentence Transformers** - Free and fast for development
2. **Use caching** - Enable cache for faster iterations
3. **Validate embeddings** - Run validation after generation
4. **Monitor costs** - Check cost estimation reports regularly
5. **Batch appropriately** - Balance speed vs memory
6. **Test on subset** - Use `--limit` for testing
7. **Version your embeddings** - Track model versions
8. **Document provider changes** - Keep notes on configuration changes

---

## Next Steps

After generating embeddings, proceed to:

1. **Phase 2E:** ChromaDB integration
2. **Phase 2E:** Vector search implementation
3. **Phase 2E:** Retrieval quality evaluation

---

**Documentation Version:** 1.0.0  
**Last Updated:** July 1, 2026  
**Maintained by:** MedNexus-AI Engineering Team

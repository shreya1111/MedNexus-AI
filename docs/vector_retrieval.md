# Vector Knowledge Retrieval Engine

**MedNexus-AI Phase 3: Intelligent Vector Knowledge Retrieval**

This document provides comprehensive documentation for the vector retrieval system that transforms validated embeddings into a production-grade searchable medical knowledge base.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [ChromaDB Design](#chromadb-design)
3. [Collection Management](#collection-management)
4. [Index Building](#index-building)
5. [Vector Search](#vector-search)
6. [BM25 Search](#bm25-search)
7. [Hybrid Retrieval](#hybrid-retrieval)
8. [Maximum Marginal Relevance (MMR)](#maximum-marginal-relevance-mmr)
9. [Metadata Filtering](#metadata-filtering)
10. [Query Processing](#query-processing)
11. [Search Caching](#search-caching)
12. [Validation](#validation)
13. [Benchmarking](#benchmarking)
14. [CLI Usage](#cli-usage)
15. [Performance Tuning](#performance-tuning)
16. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The retrieval system follows a modular, provider-agnostic architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Query Interface                          │
│  (QueryProcessor → EmbeddingProvider → Retriever)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Retrieval Strategy                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Vector    │  │    BM25     │  │     Hybrid       │   │
│  │  Retriever  │  │  Retriever  │  │    Retriever     │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Metadata Filtering & Caching                    │
│  ┌──────────────────┐        ┌─────────────────────┐       │
│  │ MetadataFilter   │        │   SearchCache       │       │
│  └──────────────────┘        └─────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Vector Database Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           ChromaDB Collection Manager                │  │
│  │  • Persistent Storage  • Multiple Collections       │  │
│  │  • Metadata Management • Health Checks              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Validation & Benchmarking                  │
│  ┌─────────────────┐        ┌──────────────────────┐       │
│  │   Validator     │        │    Benchmark         │       │
│  │  • Consistency  │        │  • Recall@K          │       │
│  │  • Duplicates   │        │  • Precision@K       │       │
│  │  • Checksums    │        │  • MRR, nDCG         │       │
│  └─────────────────┘        └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **CollectionManager**: Manages ChromaDB collections and persistence
- **IndexBuilder**: Indexes embeddings with incremental updates
- **VectorRetriever**: Semantic search with MMR support
- **BM25Retriever**: Traditional text-based search
- **HybridRetriever**: Combines vector and BM25 using RRF
- **MetadataFilter**: Filters results by metadata attributes
- **QueryProcessor**: Preprocesses queries (lowercasing, abbreviation expansion)
- **SearchCache**: LRU cache for search results
- **RetrievalValidator**: Validates collection consistency
- **RetrievalBenchmark**: Evaluates retrieval quality and performance

---

## ChromaDB Design

### Storage Structure

```
storage/
└── chroma_db/
    ├── chroma.sqlite3          # Metadata and configuration
    ├── collections/
    │   └── medical_knowledge/  # Collection data
    ├── backups/                # Automatic backups
    └── .checkpoint.json        # Indexing checkpoints
```

### Collection Configuration

```yaml
chromadb:
  persist_directory: "storage/chroma_db"
  collection_name: "medical_knowledge"
  distance_metric: "cosine"  # cosine, l2, ip
  
  metadata:
    description: "Medical knowledge base"
    version: "1.0.0"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    dimension: 384
```

### Distance Metrics

- **cosine**: Cosine similarity (default, best for semantic search)
- **l2**: Euclidean distance
- **ip**: Inner product

---

## Collection Management

### Creating Collections

```python
from vector_db.collection_manager import CollectionManager

config = load_yaml_config('config/retrieval.yaml')
manager = CollectionManager(config)

# Create or get collection
collection = manager.get_or_create_collection()
```

### Collection Operations

```python
# List all collections
collections = manager.list_collections()

# Get collection statistics
stats = manager.get_collection_stats('medical_knowledge')
print(f"Documents: {stats['count']}")
print(f"Metadata: {stats['metadata']}")

# Delete collection
manager.delete_collection('old_collection')
```

### Health Checks

```python
# Validate collection
is_healthy = manager.validate_collection()

if not is_healthy:
    print("Collection requires maintenance")
```

---

## Index Building

### Incremental Indexing

The index builder supports incremental updates using checksums:

```python
from vector_db.index_builder import IndexBuilder

builder = IndexBuilder(
    config=config,
    embeddings_dir=Path('datasets/processed/embeddings'),
    collection_manager=manager
)

# Build index (skips unchanged embeddings)
stats = builder.build_index(
    source='medquad',
    force=False,  # Set True to reindex everything
    show_progress=True
)
```

### Batch Processing

```python
# Index configuration
indexing:
  mode: "incremental"  # incremental, full, force
  batch_size: 100
  parallel_workers: 4
  resume_enabled: true
  skip_unchanged: true
```

### Checkpoint System

If indexing is interrupted, it automatically resumes:

```python
# Checkpoint is saved every 1000 documents
checkpoint_enabled: true
checkpoint_interval: 1000
checkpoint_file: "storage/chroma_db/.checkpoint.json"
```

---

## Vector Search

### Basic Search

```python
from vector_db.retriever import VectorRetriever

retriever = VectorRetriever(config, collection_manager)

# Generate query embedding
query_embedding = embedder.embed_batch(["What causes diabetes?"])[0]

# Search
results = retriever.search(
    query_embedding=query_embedding,
    top_k=10,
    filters=None
)

for result in results:
    print(f"ID: {result['chunk_id']}")
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Text: {result['document'][:200]}...")
```

### Search Parameters

```yaml
search:
  top_k: 10
  similarity_threshold: 0.0  # Minimum similarity score
  distance_metric: "cosine"
  deduplicate: true
  max_results: 100
```

---

## BM25 Search

### Building BM25 Index

```python
from vector_db.bm25_retriever import BM25Retriever

bm25 = BM25Retriever(config)

# Build index from documents
documents = [
    {'chunk_id': 'doc1', 'document': 'diabetes is a disease'},
    {'chunk_id': 'doc2', 'document': 'hypertension causes high blood pressure'}
]

bm25.build_index(documents)
```

### BM25 Search

```python
# Search
results = bm25.search(
    query_text="diabetes treatment",
    top_k=10
)

for result in results:
    print(f"BM25 Score: {result['bm25_score']:.4f}")
```

### BM25 Parameters

```yaml
bm25:
  k1: 1.5  # Term frequency saturation (1.2-2.0 typical)
  b: 0.75  # Length normalization (0-1, 0=no norm, 1=full norm)
  
  tokenizer: "simple"
  lowercase: true
  remove_punctuation: true
```

---

## Hybrid Retrieval

### Reciprocal Rank Fusion (RRF)

Hybrid retrieval combines vector and BM25 search using RRF:

**RRF Formula**: `score = Σ(1 / (k + rank))`

```python
from vector_db.hybrid_retriever import HybridRetriever

hybrid = HybridRetriever(
    config=config,
    vector_retriever=vector_retriever,
    bm25_retriever=bm25_retriever
)

results = hybrid.search(
    query_embedding=query_embedding,
    query_text=query_text,
    top_k=10
)
```

### Hybrid Configuration

```yaml
search:
  mode: "hybrid"  # vector, bm25, hybrid
  
  hybrid:
    vector_weight: 0.7  # 70% weight for vector search
    bm25_weight: 0.3    # 30% weight for BM25
    rrf_k: 60           # RRF constant
```

### When to Use Each Mode

- **Vector**: Best for semantic similarity, concept matching
- **BM25**: Best for exact keyword matching, acronyms
- **Hybrid**: Best overall performance, combines both strengths

---

## Maximum Marginal Relevance (MMR)

MMR balances relevance and diversity in search results.

### How MMR Works

1. Fetch `mmr_fetch_k` candidates using vector search
2. Select documents that maximize: `λ * relevance - (1-λ) * diversity`
3. Return top K diverse results

### MMR Configuration

```yaml
search:
  mmr_enabled: true
  mmr_lambda: 0.5  # 0=max diversity, 1=max relevance
  mmr_fetch_k: 20  # Fetch extra candidates
```

### Using MMR

```python
# Enable MMR
config['search']['mmr_enabled'] = True
config['search']['mmr_lambda'] = 0.7  # Favor relevance

results = retriever.search(
    query_embedding=query_embedding,
    top_k=10
)
```

### MMR Use Cases

- **High λ (0.7-0.9)**: When you want highly relevant but somewhat diverse results
- **Mid λ (0.4-0.6)**: Balanced relevance and diversity
- **Low λ (0.1-0.3)**: Maximum diversity, exploratory search

---

## Metadata Filtering

### Supported Fields

- `source`: Data source (e.g., "medquad", "pubmed")
- `document_id`: Document identifier
- `disease`: Disease name
- `drug`: Drug name
- `section`: Document section
- `language`: Language code
- `date`: Publication date
- `specialty`: Medical specialty
- `document_type`: Type of document

### Filtering Operators

- **eq**: Equal
- **ne**: Not equal
- **in**: In list
- **nin**: Not in list
- **gt**: Greater than
- **gte**: Greater than or equal
- **lt**: Less than
- **lte**: Less than or equal
- **contains**: String contains
- **startswith**: String starts with
- **endswith**: String ends with

### Filter Examples

```python
from vector_db.metadata_filter import MetadataFilter

filter_module = MetadataFilter(config)

# Simple equality
filters = {'source': 'medquad'}

# Multiple conditions
filters = {
    'source': 'medquad',
    'language': 'en'
}

# Using operators
filters = {
    'source': {'in': ['medquad', 'pubmed']},
    'date': {'gte': '2020-01-01'}
}

# String operations
filters = {
    'disease': {'contains': 'diabetes'},
    'document_type': {'startswith': 'clinical'}
}

# Apply filters
filtered_results = filter_module.apply_filters(results, filters)
```

---

## Query Processing

### Preprocessing Steps

1. **Lowercasing**: Convert to lowercase
2. **Whitespace normalization**: Collapse multiple spaces
3. **Abbreviation expansion**: Expand medical abbreviations
4. **Validation**: Check query length

### Configuration

```yaml
query_preprocessing:
  enabled: true
  lowercase: true
  normalize_whitespace: true
  expand_abbreviations: true
  
  abbreviations:
    dm: "diabetes mellitus"
    htn: "hypertension"
    mi: "myocardial infarction"
    chf: "congestive heart failure"
  
  min_query_length: 2
  max_query_length: 500
```

### Usage

```python
from vector_db.query_processor import QueryProcessor

processor = QueryProcessor(config)

# Process query
processed = processor.process("What is DM?")
# Output: "what is diabetes mellitus?"

# Validate query
is_valid = processor.validate("hi")  # False (too short)
```

---

## Search Caching

### LRU Cache

The search cache stores recent query results:

```yaml
cache:
  enabled: true
  strategy: "lru"  # Least Recently Used
  max_size: 1000   # Maximum cached queries
  ttl_seconds: 3600  # 1 hour TTL
  
  track_statistics: true
  auto_invalidate: true
```

### Using the Cache

```python
from vector_db.search_cache import SearchCache

cache = SearchCache(config)

# Generate cache key
cache_key = cache.hash_query(query_text, top_k, filters)

# Check cache
cached_results = cache.get(cache_key)

if cached_results:
    return cached_results

# Perform search
results = retriever.search(...)

# Cache results
cache.put(cache_key, results)

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

---

## Validation

### Validation Checks

- **Missing vectors**: Documents without embeddings
- **Duplicate IDs**: Duplicate chunk IDs in collection
- **Broken metadata**: Missing or invalid metadata fields
- **Collection consistency**: Mismatched array lengths
- **Checksum validation**: Embedding integrity

### Running Validation

```python
from vector_db.retrieval_validator import RetrievalValidator

validator = RetrievalValidator(config)

# Validate collection
result = validator.validate_collection(collection_manager)

if result.is_valid:
    print("✓ Collection is valid")
else:
    print(f"✗ Found {len(result.errors)} errors")
    for error in result.errors:
        print(f"  - {error}")

# Generate report
validator.generate_report(result, Path('validation_report.json'))
```

### CLI Validation

```bash
python -m scripts.cli.main validate-index
python -m scripts.cli.main validate-index --output reports/validation.json
```

---

## Benchmarking

### Retrieval Metrics

- **Recall@K**: Fraction of relevant docs in top K
- **Precision@K**: Fraction of top K that are relevant
- **MRR**: Mean Reciprocal Rank
- **nDCG**: Normalized Discounted Cumulative Gain
- **Hit Rate**: Fraction of queries with at least one relevant result

### Performance Metrics

- **Latency**: Search response time (avg, p95, p99)
- **Memory Usage**: RAM consumption during search

### Running Benchmarks

```python
from vector_db.retrieval_benchmark import RetrievalBenchmark

benchmark = RetrievalBenchmark(config)

# Run benchmark
metrics = benchmark.benchmark_retrieval(retriever, test_queries)

# Print results
benchmark.print_metrics(metrics)

# Save results
benchmark.save_metrics(metrics)
```

### CLI Benchmarking

```bash
python -m scripts.cli.main benchmark-search
python -m scripts.cli.main benchmark-search --queries test_queries.json
```

### Interpreting Results

- **Recall@10 > 0.7**: Good retrieval quality
- **MRR > 0.5**: Relevant results appear early
- **Latency < 100ms**: Excellent performance
- **Latency < 500ms**: Acceptable performance
- **Latency > 1000ms**: Needs optimization

---

## CLI Usage

### Indexing

```bash
# Index all embeddings
python -m scripts.cli.main index

# Index specific source
python -m scripts.cli.main index --source medquad

# Force full reindex
python -m scripts.cli.main index --force
```

### Searching

```bash
# Basic search
python -m scripts.cli.main search "What causes diabetes?"

# Specify number of results
python -m scripts.cli.main search "Metformin dosage" --top-k 5
```

### Collection Status

```bash
# Show collection statistics
python -m scripts.cli.main collection-status
```

### Validation

```bash
# Validate index
python -m scripts.cli.main validate-index

# Save validation report
python -m scripts.cli.main validate-index --output validation.json
```

### Benchmarking

```bash
# Run benchmark with default queries
python -m scripts.cli.main benchmark-search

# Use custom test queries
python -m scripts.cli.main benchmark-search --queries test_queries.json
```

---

## Performance Tuning

### Indexing Performance

```yaml
indexing:
  batch_size: 100          # Increase for faster indexing
  parallel_workers: 4      # Match CPU cores
  checkpoint_interval: 1000  # Adjust for reliability
```

### Search Performance

```yaml
search:
  top_k: 10                # Lower = faster
  mmr_enabled: false       # Disable if not needed
  mmr_fetch_k: 20          # Lower = faster

cache:
  enabled: true            # Enable caching
  max_size: 1000           # Larger = more hits
```

### Memory Optimization

```yaml
performance:
  max_memory_mb: 8192
  clear_cache_on_memory_limit: true
  batch_processing: true
```

### Database Optimization

```yaml
chromadb:
  enable_optimization: true
  optimize_on_startup: false
  optimize_interval_hours: 24
```

---

## Troubleshooting

### Issue: Slow Search

**Solutions:**
- Enable search caching
- Reduce `top_k` value
- Disable MMR if not needed
- Optimize ChromaDB collection

### Issue: Out of Memory

**Solutions:**
- Reduce `batch_size` in indexing
- Enable `clear_cache_on_memory_limit`
- Use incremental indexing instead of full reindex
- Reduce `max_workers`

### Issue: Low Recall

**Solutions:**
- Increase `top_k` value
- Lower `similarity_threshold`
- Use hybrid search instead of vector-only
- Check embedding quality

### Issue: Duplicate Results

**Solutions:**
- Enable `deduplicate: true` in search config
- Run validation to check for duplicate IDs
- Clean up collection

### Issue: Index Corruption

**Solutions:**
- Run `validate-index` command
- Check ChromaDB logs
- Restore from backup
- Rebuild index with `--force`

---

## Best Practices

1. **Always use incremental indexing** unless specifically needed
2. **Enable caching** for production deployments
3. **Run validation** after major index updates
4. **Benchmark regularly** to detect performance regressions
5. **Use hybrid search** for best overall results
6. **Set appropriate timeouts** for long-running operations
7. **Monitor memory usage** during indexing
8. **Keep backups** of ChromaDB data
9. **Use metadata filtering** to narrow search scope
10. **Test query preprocessing** with medical abbreviations

---

## Next Steps (Phase 4)

Phase 4 will add:
- LangChain integration
- Prompt engineering templates
- Gemini Chat integration
- Conversational memory
- Medical chatbot interface
- REST API endpoints
- Frontend UI
- Authentication & authorization

---

For more information, see:
- [Embedding Pipeline Documentation](embedding_pipeline.md)
- [Configuration Guide](../config/retrieval.yaml)
- [API Reference](../scripts/vector_db/)

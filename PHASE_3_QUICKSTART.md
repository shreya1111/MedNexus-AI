# Phase 3 Quick Start Guide

**Quick reference for the Vector Knowledge Retrieval Engine**

---

## Installation

```bash
# Install dependencies
pip install -r requirements-kb.txt

# Verify ChromaDB installation
python -c "import chromadb; print('ChromaDB:', chromadb.__version__)"
```

---

## Basic Workflow

### 1. Index Embeddings

```bash
# Index all embeddings (incremental, skips unchanged)
python -m scripts.cli.main index

# Index specific source
python -m scripts.cli.main index --source medquad

# Force full reindex
python -m scripts.cli.main index --force
```

**Output:**
```
Indexing Summary:
  Total Processed: 1000
  Indexed: 950
  Skipped: 50
  Failed: 0
  Duration: 45.32s
```

### 2. Search Knowledge Base

```bash
# Basic search
python -m scripts.cli.main search "What causes diabetes?"

# Specify number of results
python -m scripts.cli.main search "Metformin dosage" --top-k 5
```

**Output:**
```
Search Results (10 found):

1. medquad_diabetes_001
   Similarity: 0.8543
   Preview: Diabetes is a chronic disease that occurs when the pancreas...

2. medquad_diabetes_002
   Similarity: 0.8234
   Preview: Type 2 diabetes is the most common form of diabetes...
```

### 3. Check Status

```bash
# View collection status
python -m scripts.cli.main collection-status
```

**Output:**
```
Collections (1 found):

Collection: medical_knowledge
  Documents: 1000
  Metadata: {'version': '1.0.0', 'dimension': 384}
```

### 4. Validate Index

```bash
# Validate collection
python -m scripts.cli.main validate-index

# Save validation report
python -m scripts.cli.main validate-index --output validation_report.json
```

**Output:**
```
Index Validation Results:
Valid: True
Errors: 0
Warnings: 2

Warnings:
  - Found 5 documents with missing optional metadata

Statistics:
  total_documents: 1000
  unique_ids: 1000
  error_count: 0
  warning_count: 2
```

### 5. Benchmark Search

```bash
# Run benchmark (requires test queries)
python -m scripts.cli.main benchmark-search

# Use custom queries
python -m scripts.cli.main benchmark-search --queries test_queries.json
```

**Output:**
```
RETRIEVAL BENCHMARK RESULTS

Retrieval Quality:
  Recall@1:     0.750
  Recall@10:    0.890
  MRR:          0.650
  nDCG:         0.720

Performance:
  Avg Latency:  85.32 ms
  P95 Latency:  145.67 ms
```

---

## Python Usage

### Index Embeddings

```python
from pathlib import Path
from vector_db.collection_manager import CollectionManager
from vector_db.index_builder import IndexBuilder
from utils.config_loader import load_yaml_config

# Load configuration
config = load_yaml_config('config/retrieval.yaml')

# Initialize collection manager
collection_manager = CollectionManager(config)

# Initialize index builder
index_builder = IndexBuilder(
    config=config,
    embeddings_dir=Path('datasets/processed/embeddings'),
    collection_manager=collection_manager
)

# Build index
stats = index_builder.build_index(
    source='medquad',
    force=False,
    show_progress=True
)

print(f"Indexed: {stats['indexed']} documents")
```

### Search

```python
from vector_db.retriever import VectorRetriever
from vector_db.query_processor import QueryProcessor
from embeddings.provider_factory import ProviderFactory

# Initialize components
collection_manager = CollectionManager(config)
retriever = VectorRetriever(config, collection_manager)
processor = QueryProcessor(config)

# Initialize embedder
embedder = ProviderFactory.create_embedder('sentence-transformers', {})
embedder.initialize()

# Process query
query_text = "What causes diabetes?"
processed_query = processor.process(query_text)

# Generate embedding
query_embedding = embedder.embed_batch([processed_query])[0]

# Search
results = retriever.search(
    query_embedding=query_embedding,
    top_k=10
)

# Display results
for i, result in enumerate(results, 1):
    print(f"{i}. {result['chunk_id']}")
    print(f"   Similarity: {result['similarity']:.4f}")
    print(f"   Text: {result['document'][:200]}...")

# Cleanup
embedder.cleanup()
```

### Hybrid Search

```python
from vector_db.hybrid_retriever import HybridRetriever
from vector_db.bm25_retriever import BM25Retriever

# Initialize BM25
bm25 = BM25Retriever(config)

# Load all documents for BM25 index
collection = collection_manager.get_collection()
all_docs = collection.get(include=['documents', 'metadatas'])

documents = [
    {
        'chunk_id': chunk_id,
        'document': doc
    }
    for chunk_id, doc in zip(all_docs['ids'], all_docs['documents'])
]

bm25.build_index(documents)

# Initialize hybrid retriever
hybrid = HybridRetriever(config, retriever, bm25)

# Search
results = hybrid.search(
    query_embedding=query_embedding,
    query_text=query_text,
    top_k=10
)
```

### Metadata Filtering

```python
from vector_db.metadata_filter import MetadataFilter

filter_module = MetadataFilter(config)

# Define filters
filters = {
    'source': 'medquad',
    'language': 'en',
    'disease': {'contains': 'diabetes'}
}

# Apply to results
filtered_results = filter_module.apply_filters(results, filters)
```

### With Caching

```python
from vector_db.search_cache import SearchCache

cache = SearchCache(config)

# Generate cache key
cache_key = cache.hash_query(query_text, top_k=10, filters=None)

# Check cache
cached_results = cache.get(cache_key)

if cached_results:
    results = cached_results
else:
    # Perform search
    results = retriever.search(query_embedding, top_k=10)
    
    # Cache results
    cache.put(cache_key, results)

# Get cache statistics
stats = cache.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```

---

## Configuration Quick Reference

### config/retrieval.yaml

```yaml
# ChromaDB
chromadb:
  persist_directory: "storage/chroma_db"
  collection_name: "medical_knowledge"
  distance_metric: "cosine"

# Indexing
indexing:
  mode: "incremental"  # incremental, full, force
  batch_size: 100
  parallel_workers: 4

# Search
search:
  mode: "hybrid"  # vector, bm25, hybrid
  top_k: 10
  mmr_enabled: false
  hybrid:
    vector_weight: 0.7
    bm25_weight: 0.3

# Query Processing
query_preprocessing:
  enabled: true
  lowercase: true
  expand_abbreviations: true
  abbreviations:
    dm: "diabetes mellitus"
    htn: "hypertension"

# Caching
cache:
  enabled: true
  max_size: 1000
  ttl_seconds: 3600

# Validation
validation:
  enabled: true
  checks:
    missing_vectors: true
    duplicate_ids: true
```

---

## Common Workflows

### Initial Setup

```bash
# 1. Ensure embeddings are generated (Phase 2D)
python -m scripts.cli.main embed

# 2. Index embeddings
python -m scripts.cli.main index

# 3. Validate index
python -m scripts.cli.main validate-index

# 4. Test search
python -m scripts.cli.main search "test query"
```

### Regular Updates

```bash
# 1. Generate new embeddings (if new data)
python -m scripts.cli.main embed --source new_source

# 2. Incremental index (automatic with new embeddings)
python -m scripts.cli.main index

# 3. Validate
python -m scripts.cli.main validate-index
```

### Performance Testing

```bash
# 1. Create test queries file
cat > test_queries.json << EOF
[
  {
    "query": "What causes diabetes?",
    "embedding": [...],
    "relevant_docs": ["doc1", "doc2"]
  }
]
EOF

# 2. Run benchmark
python -m scripts.cli.main benchmark-search --queries test_queries.json

# 3. Review results
cat datasets/evaluation/retrieval_benchmark.json
```

### Troubleshooting

```bash
# 1. Check collection status
python -m scripts.cli.main collection-status

# 2. Validate index
python -m scripts.cli.main validate-index --output debug_report.json

# 3. Force reindex if needed
python -m scripts.cli.main index --force

# 4. Clear cache (Python)
from vector_db.search_cache import SearchCache
cache = SearchCache(config)
cache.clear()
```

---

## Search Modes

### Vector Search (Semantic)

```yaml
search:
  mode: "vector"
```

**Best for:**
- Concept matching
- Semantic similarity
- Paraphrased queries

### BM25 Search (Keyword)

```yaml
search:
  mode: "bm25"
```

**Best for:**
- Exact keyword matching
- Acronyms
- Specific terms

### Hybrid Search (Combined)

```yaml
search:
  mode: "hybrid"
  hybrid:
    vector_weight: 0.7
    bm25_weight: 0.3
```

**Best for:**
- General purpose
- Best overall accuracy
- Balanced results

---

## MMR (Maximum Marginal Relevance)

### Enable MMR for Diverse Results

```yaml
search:
  mmr_enabled: true
  mmr_lambda: 0.5  # 0=diversity, 1=relevance
  mmr_fetch_k: 20
```

```python
# Use in code
config['search']['mmr_enabled'] = True
config['search']['mmr_lambda'] = 0.7  # Favor relevance

results = retriever.search(query_embedding, top_k=10)
```

---

## Performance Tips

### Faster Indexing

```yaml
indexing:
  batch_size: 500  # Increase batch size
  parallel_workers: 8  # Use more workers
```

### Faster Search

```yaml
search:
  top_k: 5  # Request fewer results
  mmr_enabled: false  # Disable MMR

cache:
  enabled: true  # Enable caching
  max_size: 2000  # Larger cache
```

### Lower Memory

```yaml
indexing:
  batch_size: 50  # Smaller batches
  parallel_workers: 2  # Fewer workers

performance:
  max_memory_mb: 4096
  clear_cache_on_memory_limit: true
```

---

## File Locations

### Input
```
datasets/processed/embeddings/
└── source_embeddings.json
```

### Output
```
storage/chroma_db/           # Vector database
datasets/evaluation/         # Reports
├── retrieval_metrics.json
├── retrieval_latency.json
├── retrieval_benchmark.json
└── retrieval_validation.json
```

### Configuration
```
config/retrieval.yaml        # Main config
config/embedding.yaml        # Embedding config (for query embeddings)
```

---

## Quick Debugging

### Check if ChromaDB is working

```python
import chromadb

client = chromadb.PersistentClient(path="storage/chroma_db")
collections = client.list_collections()
print(f"Collections: {len(collections)}")
```

### Check collection contents

```python
collection = client.get_collection("medical_knowledge")
print(f"Documents: {collection.count()}")

# Get sample
sample = collection.get(limit=1, include=['embeddings', 'metadatas', 'documents'])
print(f"Sample: {sample['ids'][0]}")
```

### Test query processing

```python
from vector_db.query_processor import QueryProcessor

processor = QueryProcessor(config)
processed = processor.process("What is DM?")
print(f"Processed: {processed}")
```

---

## Next Steps

1. **Complete Phase 3 Testing**: Run full benchmark suite
2. **Tune Configuration**: Optimize for your hardware
3. **Prepare for Phase 4**: RAG chain integration
4. **Monitor Performance**: Track metrics over time

---

## Need Help?

- **Documentation**: [docs/vector_retrieval.md](docs/vector_retrieval.md)
- **Summary**: [PHASE_3_SUMMARY.md](PHASE_3_SUMMARY.md)
- **Deliverables**: [PHASE_3_DELIVERABLES.md](PHASE_3_DELIVERABLES.md)
- **Configuration**: [config/retrieval.yaml](config/retrieval.yaml)

---

**Phase 3 Status**: ✅ Production Ready

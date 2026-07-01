"""
Unit tests for vector database module.

Tests collection management, indexing, retrieval, caching, BM25, metadata filtering,
validation, and benchmarking.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from vector_db.query_processor import QueryProcessor
from vector_db.search_cache import SearchCache
from vector_db.bm25_retriever import BM25Retriever
from vector_db.metadata_filter import MetadataFilter
from vector_db.retrieval_validator import RetrievalValidator, ValidationResult
from vector_db.retrieval_benchmark import RetrievalBenchmark, BenchmarkMetrics


class TestQueryProcessor:
    """Tests for QueryProcessor."""
    
    def test_processor_initialization(self):
        """Test initialization."""
        config = {
            'query_preprocessing': {
                'enabled': True,
                'lowercase': True,
                'normalize_whitespace': True
            }
        }
        
        processor = QueryProcessor(config)
        
        assert processor.enabled
        assert processor.lowercase
    
    def test_process_basic(self):
        """Test basic query processing."""
        config = {
            'query_preprocessing': {
                'enabled': True,
                'lowercase': True,
                'normalize_whitespace': True,
                'expand_abbreviations': False,
                'min_query_length': 2,
                'max_query_length': 500
            }
        }
        
        processor = QueryProcessor(config)
        
        result = processor.process("What is DIABETES?")
        
        assert result == "what is diabetes?"
    
    def test_process_whitespace(self):
        """Test whitespace normalization."""
        config = {
            'query_preprocessing': {
                'enabled': True,
                'lowercase': False,
                'normalize_whitespace': True,
                'expand_abbreviations': False,
                'min_query_length': 2
            }
        }
        
        processor = QueryProcessor(config)
        
        result = processor.process("What    is     this?")
        
        assert result == "What is this?"
    
    def test_expand_abbreviations(self):
        """Test abbreviation expansion."""
        config = {
            'query_preprocessing': {
                'enabled': True,
                'lowercase': True,
                'normalize_whitespace': True,
                'expand_abbreviations': True,
                'abbreviations': {
                    'dm': 'diabetes mellitus',
                    'htn': 'hypertension'
                },
                'min_query_length': 2
            }
        }
        
        processor = QueryProcessor(config)
        
        result = processor.process("What is dm?")
        
        assert 'diabetes mellitus' in result
    
    def test_validate_too_short(self):
        """Test validation for short queries."""
        config = {
            'query_preprocessing': {
                'min_query_length': 5
            }
        }
        
        processor = QueryProcessor(config)
        
        assert not processor.validate("hi")
    
    def test_validate_too_long(self):
        """Test validation for long queries."""
        config = {
            'query_preprocessing': {
                'min_query_length': 2,
                'max_query_length': 10
            }
        }
        
        processor = QueryProcessor(config)
        
        assert not processor.validate("This is a very long query")
    
    def test_validate_valid(self):
        """Test validation for valid queries."""
        config = {
            'query_preprocessing': {
                'min_query_length': 2,
                'max_query_length': 100
            }
        }
        
        processor = QueryProcessor(config)
        
        assert processor.validate("What is diabetes?")


class TestSearchCache:
    """Tests for SearchCache."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        assert cache.enabled
        assert cache.max_size == 100
    
    def test_cache_put_get(self):
        """Test caching results."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        results = [{'chunk_id': 'test_001', 'similarity': 0.9}]
        cache.put('test_hash', results)
        
        cached = cache.get('test_hash')
        
        assert cached is not None
        assert len(cached) == 1
        assert cached[0]['chunk_id'] == 'test_001'
    
    def test_cache_miss(self):
        """Test cache miss."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        cached = cache.get('nonexistent')
        
        assert cached is None
    
    def test_cache_disabled(self):
        """Test disabled cache."""
        config = {
            'cache': {
                'enabled': False,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        results = [{'chunk_id': 'test_001'}]
        cache.put('test_hash', results)
        
        cached = cache.get('test_hash')
        
        assert cached is None
    
    def test_cache_eviction(self):
        """Test LRU eviction."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 2,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        cache.put('hash1', [{'id': '1'}])
        cache.put('hash2', [{'id': '2'}])
        cache.put('hash3', [{'id': '3'}])  # Should evict hash1
        
        assert cache.get('hash1') is None
        assert cache.get('hash2') is not None
        assert cache.get('hash3') is not None
    
    def test_hash_query(self):
        """Test query hashing."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        hash1 = cache.hash_query("test query", 10, None)
        hash2 = cache.hash_query("test query", 10, None)
        hash3 = cache.hash_query("different query", 10, None)
        
        assert hash1 == hash2
        assert hash1 != hash3
    
    def test_cache_stats(self):
        """Test cache statistics."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        cache.put('hash1', [{'id': '1'}])
        cache.get('hash1')  # Hit
        cache.get('hash2')  # Miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1
    
    def test_cache_clear(self):
        """Test cache clearing."""
        config = {
            'cache': {
                'enabled': True,
                'max_size': 100,
                'ttl_seconds': 3600
            }
        }
        
        cache = SearchCache(config)
        
        cache.put('hash1', [{'id': '1'}])
        cache.put('hash2', [{'id': '2'}])
        
        cache.clear()
        
        assert cache.get('hash1') is None
        assert cache.get('hash2') is None
        assert cache.hits == 0
        assert cache.misses == 0


class TestBM25Retriever:
    """Tests for BM25Retriever."""
    
    def test_retriever_initialization(self):
        """Test BM25 initialization."""
        config = {
            'bm25': {
                'k1': 1.5,
                'b': 0.75,
                'lowercase': True,
                'remove_punctuation': True
            }
        }
        
        retriever = BM25Retriever(config)
        
        assert retriever.k1 == 1.5
        assert retriever.b == 0.75
        assert retriever.lowercase
        assert not retriever.indexed
    
    def test_tokenize(self):
        """Test text tokenization."""
        config = {
            'bm25': {
                'lowercase': True,
                'remove_punctuation': True
            }
        }
        
        retriever = BM25Retriever(config)
        
        tokens = retriever.tokenize("What is diabetes?")
        
        assert 'what' in tokens
        assert 'is' in tokens
        assert 'diabetes' in tokens
    
    def test_build_index(self):
        """Test building BM25 index."""
        config = {'bm25': {}}
        
        retriever = BM25Retriever(config)
        
        documents = [
            {'chunk_id': 'doc1', 'document': 'diabetes is a disease'},
            {'chunk_id': 'doc2', 'document': 'hypertension is high blood pressure'},
            {'chunk_id': 'doc3', 'document': 'diabetes causes high blood sugar'}
        ]
        
        retriever.build_index(documents)
        
        assert retriever.indexed
        assert retriever.total_docs == 3
        assert len(retriever.documents) == 3
        assert 'diabetes' in retriever.inverted_index
    
    def test_search(self):
        """Test BM25 search."""
        config = {'bm25': {}}
        
        retriever = BM25Retriever(config)
        
        documents = [
            {'chunk_id': 'doc1', 'document': 'diabetes is a metabolic disease'},
            {'chunk_id': 'doc2', 'document': 'hypertension is high blood pressure'},
            {'chunk_id': 'doc3', 'document': 'diabetes causes high blood sugar'}
        ]
        
        retriever.build_index(documents)
        
        results = retriever.search('diabetes', top_k=2)
        
        assert len(results) <= 2
        assert all('chunk_id' in r for r in results)
        assert all('bm25_score' in r for r in results)
    
    def test_search_no_results(self):
        """Test search with no matching documents."""
        config = {'bm25': {}}
        
        retriever = BM25Retriever(config)
        
        documents = [
            {'chunk_id': 'doc1', 'document': 'diabetes is a disease'}
        ]
        
        retriever.build_index(documents)
        
        results = retriever.search('nonexistent', top_k=5)
        
        assert len(results) == 0
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        config = {'bm25': {}}
        
        retriever = BM25Retriever(config)
        
        documents = [
            {'chunk_id': 'doc1', 'document': 'test document'}
        ]
        
        retriever.build_index(documents)
        
        stats = retriever.get_statistics()
        
        assert stats['total_documents'] == 1
        assert stats['indexed'] is True
        assert 'total_terms' in stats


class TestMetadataFilter:
    """Tests for MetadataFilter."""
    
    def test_filter_initialization(self):
        """Test filter initialization."""
        config = {
            'metadata_filtering': {
                'enabled': True,
                'supported_fields': ['source', 'disease'],
                'operators': ['eq', 'ne', 'in']
            }
        }
        
        filter_module = MetadataFilter(config)
        
        assert filter_module.enabled
        assert 'source' in filter_module.supported_fields
        assert 'eq' in filter_module.supported_operators
    
    def test_validate_filter(self):
        """Test filter validation."""
        config = {
            'metadata_filtering': {
                'enabled': True,
                'supported_fields': ['source', 'disease'],
                'operators': ['eq', 'ne', 'in']
            }
        }
        
        filter_module = MetadataFilter(config)
        
        # Valid filter
        assert filter_module.validate_filter({'source': 'medquad'})
        
        # Invalid field
        assert not filter_module.validate_filter({'invalid_field': 'value'})
    
    def test_apply_filters_simple(self):
        """Test simple equality filtering."""
        config = {
            'metadata_filtering': {
                'enabled': True,
                'supported_fields': ['source'],
                'operators': ['eq']
            }
        }
        
        filter_module = MetadataFilter(config)
        
        results = [
            {'chunk_id': '1', 'metadata': {'source': 'medquad'}},
            {'chunk_id': '2', 'metadata': {'source': 'pubmed'}},
            {'chunk_id': '3', 'metadata': {'source': 'medquad'}}
        ]
        
        filtered = filter_module.apply_filters(results, {'source': 'medquad'})
        
        assert len(filtered) == 2
        assert all(r['metadata']['source'] == 'medquad' for r in filtered)
    
    def test_apply_filters_operators(self):
        """Test operator-based filtering."""
        config = {
            'metadata_filtering': {
                'enabled': True,
                'supported_fields': ['source'],
                'operators': ['in', 'ne']
            }
        }
        
        filter_module = MetadataFilter(config)
        
        results = [
            {'chunk_id': '1', 'metadata': {'source': 'medquad'}},
            {'chunk_id': '2', 'metadata': {'source': 'pubmed'}},
            {'chunk_id': '3', 'metadata': {'source': 'test'}}
        ]
        
        # Test 'in' operator
        filtered = filter_module.apply_filters(
            results,
            {'source': {'in': ['medquad', 'pubmed']}}
        )
        
        assert len(filtered) == 2
    
    def test_apply_filters_contains(self):
        """Test contains operator."""
        config = {
            'metadata_filtering': {
                'enabled': True,
                'supported_fields': ['document_type'],
                'operators': ['contains']
            }
        }
        
        filter_module = MetadataFilter(config)
        
        results = [
            {'chunk_id': '1', 'metadata': {'document_type': 'clinical_guideline'}},
            {'chunk_id': '2', 'metadata': {'document_type': 'research_paper'}},
            {'chunk_id': '3', 'metadata': {'document_type': 'medical_guideline'}}
        ]
        
        filtered = filter_module.apply_filters(
            results,
            {'document_type': {'contains': 'guideline'}}
        )
        
        assert len(filtered) == 2


class TestRetrievalValidator:
    """Tests for RetrievalValidator."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        config = {
            'validation': {
                'enabled': True,
                'strict_mode': False,
                'checks': {
                    'missing_vectors': True,
                    'duplicate_ids': True
                }
            }
        }
        
        validator = RetrievalValidator(config)
        
        assert validator.enabled
        assert not validator.strict_mode
        assert validator.check_missing_vectors
        assert validator.check_duplicate_ids
    
    def test_validate_embeddings(self):
        """Test embedding validation."""
        config = {'validation': {}}
        
        validator = RetrievalValidator(config)
        
        embeddings = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ]
        
        result = validator.validate_embeddings(embeddings, expected_dimension=3)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_embeddings_wrong_dimension(self):
        """Test validation with wrong dimension."""
        config = {'validation': {}}
        
        validator = RetrievalValidator(config)
        
        embeddings = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0]  # Wrong dimension
        ]
        
        result = validator.validate_embeddings(embeddings, expected_dimension=3)
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_embeddings_nan(self):
        """Test validation with NaN values."""
        config = {'validation': {}}
        
        validator = RetrievalValidator(config)
        
        embeddings = [
            [1.0, float('nan'), 3.0]
        ]
        
        result = validator.validate_embeddings(embeddings, expected_dimension=3)
        
        assert not result.is_valid
        assert any('NaN' in err for err in result.errors)
    
    def test_check_duplicates(self):
        """Test duplicate ID checking."""
        config = {'validation': {}}
        
        validator = RetrievalValidator(config)
        
        ids = ['doc1', 'doc2', 'doc1', 'doc3']
        
        errors = validator._check_duplicates(ids)
        
        assert len(errors) > 0
        assert any('duplicate' in err.lower() for err in errors)
    
    def test_check_missing_vectors(self):
        """Test missing vector checking."""
        config = {'validation': {}}
        
        validator = RetrievalValidator(config)
        
        ids = ['doc1', 'doc2', 'doc3']
        embeddings = [[1.0], [2.0]]  # Missing one
        
        errors = validator._check_missing_vectors(ids, embeddings)
        
        assert len(errors) > 0


class TestRetrievalBenchmark:
    """Tests for RetrievalBenchmark."""
    
    def test_benchmark_initialization(self):
        """Test benchmark initialization."""
        config = {
            'benchmarking': {
                'enabled': True,
                'metrics': ['recall_at_1', 'mrr'],
                'output_dir': 'test_output'
            }
        }
        
        benchmark = RetrievalBenchmark(config)
        
        assert benchmark.enabled
        assert 'recall_at_1' in benchmark.metrics_to_track
    
    def test_calculate_mrr(self):
        """Test MRR calculation."""
        config = {'benchmarking': {}}
        
        benchmark = RetrievalBenchmark(config)
        
        result_ids = ['doc3', 'doc1', 'doc2']
        relevant_docs = {'doc1', 'doc2'}
        
        mrr = benchmark._calculate_mrr(result_ids, relevant_docs)
        
        assert mrr == 0.5  # First relevant at position 2
    
    def test_calculate_mrr_no_relevant(self):
        """Test MRR with no relevant docs."""
        config = {'benchmarking': {}}
        
        benchmark = RetrievalBenchmark(config)
        
        result_ids = ['doc1', 'doc2']
        relevant_docs = {'doc3'}
        
        mrr = benchmark._calculate_mrr(result_ids, relevant_docs)
        
        assert mrr == 0.0
    
    def test_calculate_ndcg(self):
        """Test nDCG calculation."""
        config = {'benchmarking': {}}
        
        benchmark = RetrievalBenchmark(config)
        
        result_ids = ['doc1', 'doc2', 'doc3']
        relevant_docs = {'doc1', 'doc3'}
        
        ndcg = benchmark._calculate_ndcg(result_ids, relevant_docs, k=3)
        
        assert 0.0 <= ndcg <= 1.0
    
    def test_mean(self):
        """Test mean calculation."""
        config = {'benchmarking': {}}
        
        benchmark = RetrievalBenchmark(config)
        
        assert benchmark._mean([1.0, 2.0, 3.0]) == 2.0
        assert benchmark._mean([]) == 0.0
    
    def test_percentile(self):
        """Test percentile calculation."""
        config = {'benchmarking': {}}
        
        benchmark = RetrievalBenchmark(config)
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        p50 = benchmark._percentile(values, 50)
        p95 = benchmark._percentile(values, 95)
        
        assert p50 == 3.0
        assert p95 == 5.0


class TestCollectionManager:
    """Tests for CollectionManager."""
    
    @patch('vector_db.collection_manager.chromadb')
    def test_initialization(self, mock_chromadb):
        """Test collection manager initialization."""
        from vector_db.collection_manager import CollectionManager
        
        config = {
            'chromadb': {
                'persist_directory': 'test_storage',
                'collection_name': 'test_collection'
            }
        }
        
        manager = CollectionManager(config)
        
        assert manager.collection_name == 'test_collection'
    
    @patch('vector_db.collection_manager.chromadb')
    def test_get_or_create_collection(self, mock_chromadb):
        """Test collection creation."""
        from vector_db.collection_manager import CollectionManager
        
        config = {
            'chromadb': {
                'persist_directory': 'test_storage',
                'collection_name': 'test_collection',
                'metadata': {'version': '1.0.0'}
            }
        }
        
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        manager = CollectionManager(config)
        collection = manager.get_or_create_collection()
        
        assert collection is not None


class TestIndexBuilder:
    """Tests for IndexBuilder."""
    
    @patch('vector_db.collection_manager.chromadb')
    def test_initialization(self, mock_chromadb):
        """Test index builder initialization."""
        from vector_db.index_builder import IndexBuilder
        from vector_db.collection_manager import CollectionManager
        
        config = {
            'chromadb': {'persist_directory': 'test'},
            'indexing': {
                'batch_size': 100,
                'mode': 'incremental'
            }
        }
        
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        collection_manager = CollectionManager(config)
        builder = IndexBuilder(config, Path('test'), collection_manager)
        
        assert builder.batch_size == 100
        assert builder.mode == 'incremental'


class TestVectorRetriever:
    """Tests for VectorRetriever."""
    
    @patch('vector_db.collection_manager.chromadb')
    def test_initialization(self, mock_chromadb):
        """Test retriever initialization."""
        from vector_db.retriever import VectorRetriever
        from vector_db.collection_manager import CollectionManager
        
        config = {
            'chromadb': {'persist_directory': 'test'},
            'search': {
                'top_k': 10,
                'mmr_enabled': False
            }
        }
        
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        collection_manager = CollectionManager(config)
        retriever = VectorRetriever(config, collection_manager)
        
        assert retriever.top_k == 10


class TestHybridRetriever:
    """Tests for HybridRetriever."""
    
    @patch('vector_db.collection_manager.chromadb')
    def test_initialization(self, mock_chromadb):
        """Test hybrid retriever initialization."""
        from vector_db.hybrid_retriever import HybridRetriever
        from vector_db.retriever import VectorRetriever
        from vector_db.collection_manager import CollectionManager
        
        config = {
            'chromadb': {'persist_directory': 'test'},
            'search': {
                'mode': 'hybrid',
                'hybrid': {
                    'vector_weight': 0.7,
                    'bm25_weight': 0.3,
                    'rrf_k': 60
                }
            }
        }
        
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        
        collection_manager = CollectionManager(config)
        vector_retriever = VectorRetriever(config, collection_manager)
        bm25_retriever = BM25Retriever(config)
        
        hybrid = HybridRetriever(config, vector_retriever, bm25_retriever)
        
        assert hybrid.vector_weight == 0.7
        assert hybrid.bm25_weight == 0.3
        assert hybrid.mode == 'hybrid'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

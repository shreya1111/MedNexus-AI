"""
Unit tests for embedding generation module.

Tests provider abstraction, caching, validation, and manager.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from embeddings.base_embedder import BaseEmbedder, EmbeddingResult, EmbeddingMetadata
from embeddings.provider_factory import ProviderFactory
from embeddings.embedding_cache import EmbeddingCache
from embeddings.embedding_validator import EmbeddingValidator, ValidationResult


# Mock embedder for testing
class MockEmbedder(BaseEmbedder):
    """Mock embedder for testing."""
    
    def initialize(self) -> None:
        """Initialize mock embedder."""
        self._is_initialized = True
        self.dimension = 384
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings."""
        if not self._is_initialized:
            raise RuntimeError("Not initialized")
        
        # Return mock embeddings (zeros)
        return [[0.1] * self.dimension for _ in texts]
    
    def get_dimension(self) -> int:
        """Get dimension."""
        return self.dimension
    
    def get_max_batch_size(self) -> int:
        """Get max batch size."""
        return 32


class TestEmbeddingMetadata:
    """Tests for EmbeddingMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = EmbeddingMetadata(
            embedding_id="test_001_emb",
            chunk_id="test_001",
            document_id="doc1",
            provider="test",
            model="test-model",
            dimension=384,
            created_at="2026-07-01T10:00:00"
        )
        
        assert metadata.embedding_id == "test_001_emb"
        assert metadata.dimension == 384
        assert metadata.provider == "test"
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = EmbeddingMetadata(
            embedding_id="test_001_emb",
            chunk_id="test_001",
            document_id="doc1",
            provider="test",
            model="test-model",
            dimension=384,
            created_at="2026-07-01T10:00:00",
            quality_score=85.5
        )
        
        result = metadata.to_dict()
        
        assert isinstance(result, dict)
        assert result['embedding_id'] == "test_001_emb"
        assert result['quality_score'] == 85.5
        assert 'chunk_id' in result


class TestEmbeddingResult:
    """Tests for EmbeddingResult dataclass."""
    
    def test_result_creation(self):
        """Test creating embedding result."""
        result = EmbeddingResult(
            chunk_id="test_001",
            embedding=[0.1, 0.2, 0.3],
            status="success"
        )
        
        assert result.chunk_id == "test_001"
        assert len(result.embedding) == 3
        assert result.status == "success"
    
    def test_is_success(self):
        """Test success check."""
        success_result = EmbeddingResult(
            chunk_id="test_001",
            embedding=[0.1] * 384,
            status="success"
        )
        
        assert success_result.is_success()
        
        failed_result = EmbeddingResult(
            chunk_id="test_002",
            status="failed",
            error="Test error"
        )
        
        assert not failed_result.is_success()
    
    def test_cached_is_success(self):
        """Test cached status is considered success."""
        cached_result = EmbeddingResult(
            chunk_id="test_001",
            embedding=[0.1] * 384,
            status="cached"
        )
        
        assert cached_result.is_success()


class TestBaseEmbedder:
    """Tests for BaseEmbedder abstract class."""
    
    def test_embedder_initialization(self):
        """Test embedder initialization."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        
        assert embedder.model_name == 'test-model'
        assert embedder.dimension == 384
        assert not embedder._is_initialized
    
    def test_embedder_initialize(self):
        """Test initialize method."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        
        embedder.initialize()
        
        assert embedder._is_initialized
    
    def test_embed_batch_before_init(self):
        """Test embedding before initialization fails."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        
        with pytest.raises(RuntimeError):
            embedder.embed_batch(["test text"])
    
    def test_embed_batch_after_init(self):
        """Test embedding after initialization."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        embedder.initialize()
        
        result = embedder.embed_batch(["test text"])
        
        assert len(result) == 1
        assert len(result[0]) == 384
    
    def test_validate_embedding_valid(self):
        """Test validating valid embedding."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        embedder.initialize()
        
        embedding = [0.1] * 384
        
        assert embedder.validate_embedding(embedding)
    
    def test_validate_embedding_wrong_dimension(self):
        """Test validating wrong dimension."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        embedder.initialize()
        
        embedding = [0.1] * 512  # Wrong dimension
        
        assert not embedder.validate_embedding(embedding)
    
    def test_validate_embedding_nan(self):
        """Test validating embedding with NaN."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        embedder.initialize()
        
        embedding = [0.1] * 383 + [float('nan')]
        
        assert not embedder.validate_embedding(embedding)
    
    def test_validate_embedding_zero_vector(self):
        """Test validating zero vector."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        embedder.initialize()
        
        embedding = [0.0] * 384
        
        assert not embedder.validate_embedding(embedding)
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        config = {'model': 'test-model', 'dimension': 384}
        embedder = MockEmbedder(config)
        
        text = "This is a test" * 10
        tokens = embedder.estimate_tokens(text)
        
        assert tokens > 0
        assert tokens == len(text) // 4
    
    def test_context_manager(self):
        """Test using embedder as context manager."""
        config = {'model': 'test-model', 'dimension': 384}
        
        with MockEmbedder(config) as embedder:
            assert embedder._is_initialized
            result = embedder.embed_batch(["test"])
            assert len(result) == 1


class TestProviderFactory:
    """Tests for ProviderFactory."""
    
    def test_register_provider(self):
        """Test registering a custom provider."""
        ProviderFactory.register_provider('mock', MockEmbedder)
        
        assert 'mock' in ProviderFactory._providers
    
    def test_create_embedder(self):
        """Test creating embedder."""
        ProviderFactory.register_provider('mock', MockEmbedder)
        
        config = {'model': 'test-model', 'dimension': 384}
        embedder = ProviderFactory.create_embedder('mock', config)
        
        assert isinstance(embedder, MockEmbedder)
    
    def test_create_unknown_provider(self):
        """Test creating unknown provider."""
        with pytest.raises(ValueError):
            ProviderFactory.create_embedder('unknown-provider', {})
    
    def test_list_providers(self):
        """Test listing providers."""
        ProviderFactory.register_provider('mock', MockEmbedder)
        
        providers = ProviderFactory.list_providers()
        
        assert isinstance(providers, list)
        assert 'mock' in providers


class TestEmbeddingCache:
    """Tests for EmbeddingCache."""
    
    def test_cache_initialization(self, tmp_path):
        """Test cache initialization."""
        cache = EmbeddingCache(
            cache_dir=tmp_path / "cache",
            strategy="checksum",
            enabled=True
        )
        
        assert cache.enabled
        assert cache.strategy == "checksum"
    
    def test_cache_put_get(self, tmp_path):
        """Test putting and getting from cache."""
        cache = EmbeddingCache(
            cache_dir=tmp_path / "cache",
            strategy="checksum",
            enabled=True
        )
        
        embedding = [0.1] * 384
        metadata = {'provider': 'test', 'model': 'test-model'}
        
        cache.put(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model",
            embedding=embedding,
            metadata=metadata
        )
        
        result = cache.get(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model"
        )
        
        assert result is not None
        assert result['embedding'] == embedding
    
    def test_cache_miss(self, tmp_path):
        """Test cache miss."""
        cache = EmbeddingCache(
            cache_dir=tmp_path / "cache",
            strategy="checksum",
            enabled=True
        )
        
        result = cache.get(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model"
        )
        
        assert result is None
    
    def test_cache_disabled(self, tmp_path):
        """Test disabled cache."""
        cache = EmbeddingCache(
            cache_dir=tmp_path / "cache",
            strategy="disabled",
            enabled=False
        )
        
        embedding = [0.1] * 384
        metadata = {'provider': 'test'}
        
        cache.put(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model",
            embedding=embedding,
            metadata=metadata
        )
        
        result = cache.get(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model"
        )
        
        assert result is None
    
    def test_cache_invalidate(self, tmp_path):
        """Test cache invalidation."""
        cache = EmbeddingCache(
            cache_dir=tmp_path / "cache",
            strategy="checksum",
            enabled=True
        )
        
        embedding = [0.1] * 384
        metadata = {'provider': 'test'}
        
        cache.put(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model",
            embedding=embedding,
            metadata=metadata
        )
        
        invalidated = cache.invalidate(chunk_checksum="abc123")
        
        assert invalidated == 1
        
        result = cache.get(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model"
        )
        
        assert result is None
    
    def test_cache_stats(self, tmp_path):
        """Test cache statistics."""
        cache = EmbeddingCache(
            cache_dir=tmp_path / "cache",
            strategy="checksum",
            enabled=True
        )
        
        embedding = [0.1] * 384
        metadata = {'provider': 'test'}
        
        cache.put(
            chunk_id="test_001",
            chunk_checksum="abc123",
            provider="test",
            model="test-model",
            embedding=embedding,
            metadata=metadata
        )
        
        # Cache hit
        cache.get("test_001", "abc123", "test", "test-model")
        
        # Cache miss
        cache.get("test_002", "def456", "test", "test-model")
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['entries'] == 1


class TestEmbeddingValidator:
    """Tests for EmbeddingValidator."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        config = {
            'strict_mode': True,
            'checks': {'dimension': True, 'nan_values': True},
            'thresholds': {'min_norm': 0.01}
        }
        
        validator = EmbeddingValidator(config)
        
        assert validator.strict_mode
    
    def test_validate_valid_embedding(self):
        """Test validating valid embedding."""
        config = {
            'strict_mode': True,
            'checks': {'dimension': True, 'nan_values': True, 'inf_values': True, 'zero_vectors': True},
            'thresholds': {}
        }
        
        validator = EmbeddingValidator(config)
        embedding = [0.1] * 384
        
        result = validator.validate_embedding(embedding, 384, "test_001")
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_wrong_dimension(self):
        """Test validating wrong dimension."""
        config = {
            'strict_mode': True,
            'checks': {'dimension': True},
            'thresholds': {}
        }
        
        validator = EmbeddingValidator(config)
        embedding = [0.1] * 512
        
        result = validator.validate_embedding(embedding, 384, "test_001")
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_nan_values(self):
        """Test validating NaN values."""
        config = {
            'strict_mode': True,
            'checks': {'dimension': True, 'nan_values': True},
            'thresholds': {}
        }
        
        validator = EmbeddingValidator(config)
        embedding = [0.1] * 383 + [float('nan')]
        
        result = validator.validate_embedding(embedding, 384, "test_001")
        
        assert not result.is_valid
        assert any('NaN' in e for e in result.errors)
    
    def test_validate_metadata(self):
        """Test metadata validation."""
        config = {
            'strict_mode': True,
            'checks': {'metadata_consistency': True},
            'thresholds': {}
        }
        
        validator = EmbeddingValidator(config)
        
        metadata = {
            'embedding_id': 'test_001_emb',
            'chunk_id': 'test_001',
            'provider': 'test',
            'model': 'test-model',
            'dimension': 384
        }
        
        required_fields = ['embedding_id', 'chunk_id', 'provider', 'model', 'dimension']
        
        is_valid, errors = validator.validate_metadata(metadata, required_fields)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_metadata_missing_fields(self):
        """Test metadata validation with missing fields."""
        config = {
            'strict_mode': True,
            'checks': {'metadata_consistency': True},
            'thresholds': {}
        }
        
        validator = EmbeddingValidator(config)
        
        metadata = {
            'embedding_id': 'test_001_emb',
            # missing other fields
        }
        
        required_fields = ['embedding_id', 'chunk_id', 'provider']
        
        is_valid, errors = validator.validate_metadata(metadata, required_fields)
        
        assert not is_valid
        assert len(errors) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Unit tests for chunk evaluation module.

Tests quality analyzer, metrics calculation, and recommendation generation.
"""

import sys
from pathlib import Path
import pytest
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from evaluators.metrics import ChunkMetrics, QualityScore, BenchmarkResult, Recommendation
from evaluators.quality_analyzer import QualityAnalyzer


# Test fixtures
@pytest.fixture
def sample_chunks() -> List[Dict[str, Any]]:
    """Sample chunks for testing."""
    return [
        {
            'chunk_id': 'test_doc1_0000',
            'document_id': 'doc1',
            'source': 'test',
            'text': 'This is a test chunk with some content. ' * 10,
            'chunk_index': 0,
            'total_chunks': 3,
            'start_character': 0,
            'end_character': 400,
            'word_count': 80,
            'created_at': '2026-06-28T10:00:00',
            'checksum': 'abc123',
            'title': 'Test Document',
            'section': 'Introduction',
            'language': 'en',
            'tokens': None,
            'has_code': False,
            'has_list': True,
            'has_table': False,
            'parent_document_checksum': 'parent123'
        },
        {
            'chunk_id': 'test_doc1_0001',
            'document_id': 'doc1',
            'source': 'test',
            'text': 'This is a test chunk with some content. ' * 10,
            'chunk_index': 1,
            'total_chunks': 3,
            'start_character': 350,
            'end_character': 750,
            'word_count': 80,
            'created_at': '2026-06-28T10:00:00',
            'checksum': 'abc124',
            'title': 'Test Document',
            'section': 'Methods',
            'language': 'en',
            'tokens': None,
            'has_code': False,
            'has_list': False,
            'has_table': True,
            'parent_document_checksum': 'parent123'
        },
        {
            'chunk_id': 'test_doc1_0002',
            'document_id': 'doc1',
            'source': 'test',
            'text': 'Different content in the last chunk.',
            'chunk_index': 2,
            'total_chunks': 3,
            'start_character': 700,
            'end_character': 737,
            'word_count': 6,
            'created_at': '2026-06-28T10:00:00',
            'checksum': 'abc125',
            'title': 'Test Document',
            'section': 'Conclusion',
            'language': 'en',
            'tokens': None,
            'has_code': False,
            'has_list': False,
            'has_table': False,
            'parent_document_checksum': 'parent123'
        }
    ]


@pytest.fixture
def duplicate_chunks() -> List[Dict[str, Any]]:
    """Chunks with duplicates for testing."""
    base_chunk = {
        'chunk_id': 'test_doc1_0000',
        'document_id': 'doc1',
        'source': 'test',
        'text': 'This is a duplicate chunk.',
        'chunk_index': 0,
        'total_chunks': 2,
        'start_character': 0,
        'end_character': 27,
        'word_count': 5,
        'created_at': '2026-06-28T10:00:00',
        'checksum': 'dup123',
        'language': 'en',
    }
    
    duplicate = base_chunk.copy()
    duplicate['chunk_id'] = 'test_doc1_0001'
    duplicate['chunk_index'] = 1
    duplicate['checksum'] = 'dup124'
    
    return [base_chunk, duplicate]


@pytest.fixture
def eval_config() -> Dict[str, Any]:
    """Test evaluation configuration."""
    return {
        'quality_scores': {
            'weights': {
                'chunk_size': 0.15,
                'metadata': 0.15,
                'structure': 0.15,
                'lists': 0.10,
                'tables': 0.10,
                'duplicates': 0.15,
                'overlap': 0.10,
                'readability': 0.05,
                'density': 0.05
            },
            'thresholds': {
                'excellent': 90,
                'good': 75,
                'fair': 60,
                'poor': 0
            }
        },
        'chunk_size': {
            'target_min': 500,
            'target_max': 1500,
            'absolute_min': 100,
            'absolute_max': 5000,
            'flag_tiny_below': 200,
            'flag_oversized_above': 3000
        },
        'duplicates': {
            'check_exact': True,
            'check_near': True,
            'near_similarity_threshold': 0.95,
            'acceptable_rate': 0.02
        },
        'overlap': {
            'minimum_percentage': 5,
            'maximum_percentage': 30,
            'recommended_percentage': 15
        },
        'metadata': {
            'required_fields': [
                'chunk_id', 'document_id', 'source', 'checksum',
                'word_count', 'created_at'
            ]
        }
    }


@pytest.fixture
def quality_analyzer(eval_config):
    """Initialize quality analyzer."""
    return QualityAnalyzer(eval_config)


class TestChunkMetrics:
    """Tests for ChunkMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test creating ChunkMetrics instance."""
        metrics = ChunkMetrics(
            total_chunks=100,
            total_documents=10,
            avg_chunk_size=1000,
            min_chunk_size=500,
            max_chunk_size=1500,
            median_chunk_size=1000,
            std_chunk_size=200,
            avg_chunks_per_doc=10.0,
            avg_tokens=150,
            min_tokens=75,
            max_tokens=225,
            median_tokens=150,
            avg_overlap_percentage=15.0,
            min_overlap_percentage=10.0,
            max_overlap_percentage=20.0,
            duplicate_chunks=2,
            duplicate_rate=0.02,
            chunks_with_headers=50,
            chunks_with_lists=30,
            chunks_with_tables=20,
            tiny_chunks=5,
            oversized_chunks=3,
            empty_chunks=0,
            metadata_completeness=1.0,
            evaluation_time_seconds=10.5
        )
        
        assert metrics.total_chunks == 100
        assert metrics.avg_chunk_size == 1000
        assert metrics.duplicate_rate == 0.02
        assert metrics.metadata_completeness == 1.0
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = ChunkMetrics(
            total_chunks=100,
            total_documents=10,
            avg_chunk_size=1000,
            min_chunk_size=500,
            max_chunk_size=1500,
            median_chunk_size=1000,
            std_chunk_size=200,
            avg_chunks_per_doc=10.0,
            avg_tokens=150,
            min_tokens=75,
            max_tokens=225,
            median_tokens=150,
            avg_overlap_percentage=15.0,
            min_overlap_percentage=10.0,
            max_overlap_percentage=20.0,
            duplicate_chunks=2,
            duplicate_rate=0.02,
            chunks_with_headers=50,
            chunks_with_lists=30,
            chunks_with_tables=20,
            tiny_chunks=5,
            oversized_chunks=3,
            empty_chunks=0,
            metadata_completeness=1.0,
            evaluation_time_seconds=10.5
        )
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result['total_chunks'] == 100
        assert result['duplicate_rate'] == 0.02
        assert 'avg_chunk_size' in result


class TestQualityScore:
    """Tests for QualityScore dataclass."""
    
    def test_quality_score_creation(self):
        """Test creating QualityScore instance."""
        score = QualityScore(
            overall_score=85.5,
            chunk_size_score=0.90,
            metadata_score=1.0,
            structure_score=0.85,
            list_score=0.80,
            table_score=0.75,
            duplicate_score=0.95,
            overlap_score=0.88,
            readability_score=0.82,
            density_score=0.78
        )
        
        assert score.overall_score == 85.5
        assert score.metadata_score == 1.0
        assert score.duplicate_score == 0.95
    
    def test_quality_score_grade(self):
        """Test grade calculation."""
        excellent = QualityScore(
            overall_score=95.0, chunk_size_score=0.9, metadata_score=1.0,
            structure_score=0.9, list_score=0.9, table_score=0.9,
            duplicate_score=0.9, overlap_score=0.9, readability_score=0.9,
            density_score=0.9
        )
        assert excellent.grade() == 'A'
        
        good = QualityScore(
            overall_score=80.0, chunk_size_score=0.8, metadata_score=0.8,
            structure_score=0.8, list_score=0.8, table_score=0.8,
            duplicate_score=0.8, overlap_score=0.8, readability_score=0.8,
            density_score=0.8
        )
        assert good.grade() == 'B'
        
        fair = QualityScore(
            overall_score=65.0, chunk_size_score=0.6, metadata_score=0.7,
            structure_score=0.6, list_score=0.6, table_score=0.6,
            duplicate_score=0.7, overlap_score=0.6, readability_score=0.6,
            density_score=0.6
        )
        assert fair.grade() == 'C'
        
        poor = QualityScore(
            overall_score=50.0, chunk_size_score=0.5, metadata_score=0.5,
            structure_score=0.5, list_score=0.5, table_score=0.5,
            duplicate_score=0.5, overlap_score=0.5, readability_score=0.5,
            density_score=0.5
        )
        assert poor.grade() == 'D'


class TestQualityAnalyzer:
    """Tests for QualityAnalyzer."""
    
    def test_analyze_chunks(self, quality_analyzer, sample_chunks):
        """Test analyzing sample chunks."""
        metrics = quality_analyzer.analyze(sample_chunks)
        
        assert metrics.total_chunks == 3
        assert metrics.total_documents == 1
        assert metrics.avg_chunk_size > 0
        assert metrics.chunks_with_headers == 3
        assert metrics.chunks_with_lists == 1
        assert metrics.chunks_with_tables == 1
    
    def test_duplicate_detection(self, quality_analyzer, duplicate_chunks):
        """Test duplicate detection."""
        metrics = quality_analyzer.analyze(duplicate_chunks)
        
        assert metrics.duplicate_chunks > 0
        assert metrics.duplicate_rate > 0
    
    def test_quality_score_calculation(self, quality_analyzer, sample_chunks):
        """Test quality score calculation."""
        metrics = quality_analyzer.analyze(sample_chunks)
        quality_score = quality_analyzer.calculate_quality_score(metrics)
        
        assert 0 <= quality_score.overall_score <= 100
        assert 0 <= quality_score.chunk_size_score <= 1
        assert 0 <= quality_score.metadata_score <= 1
        assert 0 <= quality_score.duplicate_score <= 1
    
    def test_recommendation_generation(self, quality_analyzer, sample_chunks):
        """Test recommendation generation."""
        metrics = quality_analyzer.analyze(sample_chunks)
        quality_score = quality_analyzer.calculate_quality_score(metrics)
        recommendations = quality_analyzer.generate_recommendations(metrics, quality_score)
        
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.priority in ['high', 'medium', 'low']
            assert 0 <= rec.confidence <= 1


class TestMetadataValidation:
    """Tests for metadata validation."""
    
    def test_complete_metadata(self, quality_analyzer, sample_chunks):
        """Test chunks with complete metadata."""
        metrics = quality_analyzer.analyze(sample_chunks)
        
        # All sample chunks have required fields
        assert metrics.metadata_completeness > 0.9
    
    def test_incomplete_metadata(self, quality_analyzer):
        """Test chunks with missing metadata."""
        incomplete_chunks = [
            {
                'chunk_id': 'test_0000',
                'text': 'Test chunk',
                # Missing many required fields
            }
        ]
        
        metrics = quality_analyzer.analyze(incomplete_chunks)
        
        # Should detect incomplete metadata
        assert metrics.metadata_completeness < 1.0


class TestOverlapAnalysis:
    """Tests for overlap analysis."""
    
    def test_overlap_calculation(self, quality_analyzer, sample_chunks):
        """Test overlap percentage calculation."""
        metrics = quality_analyzer.analyze(sample_chunks)
        
        # Sample chunks have overlap (350-400 overlap between chunks 0 and 1)
        assert metrics.avg_overlap_percentage > 0
    
    def test_no_overlap(self, quality_analyzer):
        """Test chunks with no overlap."""
        no_overlap_chunks = [
            {
                'chunk_id': 'test_0000',
                'text': 'First chunk',
                'start_character': 0,
                'end_character': 11,
                'chunk_index': 0,
                'total_chunks': 2,
                'document_id': 'doc1'
            },
            {
                'chunk_id': 'test_0001',
                'text': 'Second chunk',
                'start_character': 11,
                'end_character': 23,
                'chunk_index': 1,
                'total_chunks': 2,
                'document_id': 'doc1'
            }
        ]
        
        metrics = quality_analyzer.analyze(no_overlap_chunks)
        
        # Should detect no overlap
        assert metrics.avg_overlap_percentage == 0


class TestSpecialContentDetection:
    """Tests for special content detection."""
    
    def test_header_detection(self, quality_analyzer):
        """Test header preservation detection."""
        chunks_with_headers = [
            {
                'chunk_id': 'test_0000',
                'text': 'Content',
                'title': 'Introduction',
                'section': 'Section 1'
            },
            {
                'chunk_id': 'test_0001',
                'text': 'More content',
                'title': None,
                'section': None
            }
        ]
        
        metrics = quality_analyzer.analyze(chunks_with_headers)
        
        assert metrics.chunks_with_headers == 1
    
    def test_list_detection(self, quality_analyzer):
        """Test list preservation detection."""
        chunks_with_lists = [
            {
                'chunk_id': 'test_0000',
                'text': 'Content',
                'has_list': True
            },
            {
                'chunk_id': 'test_0001',
                'text': 'Content',
                'has_list': False
            }
        ]
        
        metrics = quality_analyzer.analyze(chunks_with_lists)
        
        assert metrics.chunks_with_lists == 1
    
    def test_table_detection(self, quality_analyzer):
        """Test table preservation detection."""
        chunks_with_tables = [
            {
                'chunk_id': 'test_0000',
                'text': 'Content',
                'has_table': True
            },
            {
                'chunk_id': 'test_0001',
                'text': 'Content',
                'has_table': False
            }
        ]
        
        metrics = quality_analyzer.analyze(chunks_with_tables)
        
        assert metrics.chunks_with_tables == 1


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""
    
    def test_benchmark_result_creation(self):
        """Test creating BenchmarkResult."""
        result = BenchmarkResult(
            strategy='recursive',
            avg_chunk_size=1000,
            chunk_count=100,
            overlap_percentage=15.0,
            duplicate_rate=0.02,
            processing_time=10.5,
            quality_score=85.0,
            recommended_use_case='General-purpose documents'
        )
        
        assert result.strategy == 'recursive'
        assert result.quality_score == 85.0
        assert result.duplicate_rate == 0.02
    
    def test_benchmark_to_dict(self):
        """Test converting benchmark to dictionary."""
        result = BenchmarkResult(
            strategy='recursive',
            avg_chunk_size=1000,
            chunk_count=100,
            overlap_percentage=15.0,
            duplicate_rate=0.02,
            processing_time=10.5,
            quality_score=85.0,
            recommended_use_case='General-purpose documents'
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['strategy'] == 'recursive'
        assert result_dict['quality_score'] == 85.0


class TestRecommendation:
    """Tests for Recommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating Recommendation."""
        rec = Recommendation(
            priority='high',
            category='chunk_size',
            issue='Chunks are too large',
            recommendation='Reduce chunk size to 1000 characters',
            confidence=0.9,
            affected_chunks=10
        )
        
        assert rec.priority == 'high'
        assert rec.category == 'chunk_size'
        assert rec.confidence == 0.9
    
    def test_recommendation_to_dict(self):
        """Test converting recommendation to dictionary."""
        rec = Recommendation(
            priority='high',
            category='chunk_size',
            issue='Chunks are too large',
            recommendation='Reduce chunk size to 1000 characters',
            confidence=0.9,
            affected_chunks=10
        )
        
        rec_dict = rec.to_dict()
        
        assert isinstance(rec_dict, dict)
        assert rec_dict['priority'] == 'high'
        assert rec_dict['confidence'] == 0.9


class TestSizeAnalysis:
    """Tests for chunk size analysis."""
    
    def test_tiny_chunk_detection(self, quality_analyzer):
        """Test detection of tiny chunks."""
        tiny_chunks = [
            {
                'chunk_id': 'test_0000',
                'text': 'Tiny',  # Very small
                'word_count': 1
            }
        ]
        
        metrics = quality_analyzer.analyze(tiny_chunks)
        
        assert metrics.tiny_chunks > 0
    
    def test_oversized_chunk_detection(self, quality_analyzer):
        """Test detection of oversized chunks."""
        oversized_chunks = [
            {
                'chunk_id': 'test_0000',
                'text': 'A' * 10000,  # Very large
                'word_count': 2000
            }
        ]
        
        metrics = quality_analyzer.analyze(oversized_chunks)
        
        assert metrics.oversized_chunks > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

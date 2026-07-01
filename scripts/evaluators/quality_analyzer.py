"""
Quality analyzer for chunk evaluation.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time
import statistics
import re
from collections import Counter

import sys
sys.path.append(str(Path(__file__).parent.parent))

from evaluators.metrics import ChunkMetrics, QualityScore, Recommendation
from utils.logger import get_logger


class QualityAnalyzer:
    """Analyzes chunk quality and generates comprehensive metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize quality analyzer.
        
        Args:
            config: Evaluation configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
    
    def analyze(self, chunks: List[Dict[str, Any]]) -> ChunkMetrics:
        """
        Analyze chunks and calculate metrics.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            ChunkMetrics
        """
        start_time = time.time()
        
        metrics = ChunkMetrics()
        
        if not chunks:
            self.logger.warning("No chunks to analyze")
            return metrics
        
        # Basic statistics
        metrics.total_chunks = len(chunks)
        metrics.total_documents = len(set(c.get('document_id') for c in chunks))
        
        # Group chunks by document
        doc_chunks = {}
        for chunk in chunks:
            doc_id = chunk.get('document_id')
            if doc_id not in doc_chunks:
                doc_chunks[doc_id] = []
            doc_chunks[doc_id].append(chunk)
        
        chunks_per_doc = [len(chunks) for chunks in doc_chunks.values()]
        metrics.chunks_per_document_avg = statistics.mean(chunks_per_doc) if chunks_per_doc else 0
        metrics.chunks_per_document_median = statistics.median(chunks_per_doc) if chunks_per_doc else 0
        
        # Analyze each chunk
        chunk_sizes = []
        token_counts = []
        overlap_percentages = []
        text_hashes = []
        sentence_lengths = []
        word_counts = []
        
        for chunk in chunks:
            # Size analysis
            text = chunk.get('text', '')
            size = len(text)
            chunk_sizes.append(size)
            
            # Token estimation
            tokens = self._estimate_tokens(text)
            token_counts.append(tokens)
            
            # Word count
            words = len(text.split())
            word_counts.append(words)
            
            # Sentence analysis
            sentences = self._split_sentences(text)
            if sentences:
                avg_sent_len = sum(len(s.split()) for s in sentences) / len(sentences)
                sentence_lengths.append(avg_sent_len)
            
            # For duplicate detection
            text_hashes.append(hash(text))
            
            # Metadata validation
            if not self._validate_metadata(chunk):
                metrics.missing_metadata_count += 1
            
            # Structure detection
            if chunk.get('section') or self._detect_headers(text):
                metrics.chunks_with_headers += 1
            
            if chunk.get('has_list') or self._detect_lists(text):
                metrics.chunks_with_lists += 1
            
            if chunk.get('has_table') or self._detect_tables(text):
                metrics.chunks_with_tables += 1
        
        # Calculate size metrics
        if chunk_sizes:
            metrics.avg_chunk_size = statistics.mean(chunk_sizes)
            metrics.min_chunk_size = min(chunk_sizes)
            metrics.max_chunk_size = max(chunk_sizes)
            metrics.median_chunk_size = statistics.median(chunk_sizes)
            metrics.std_chunk_size = statistics.stdev(chunk_sizes) if len(chunk_sizes) > 1 else 0
            
            # Count tiny and oversized chunks
            size_config = self.config.get('chunk_size', {})
            metrics.tiny_chunks_count = sum(1 for s in chunk_sizes if s < size_config.get('warning_min', 100))
            metrics.oversized_chunks_count = sum(1 for s in chunk_sizes if s > size_config.get('warning_max', 2500))
        
        # Calculate token metrics
        if token_counts:
            metrics.avg_tokens = statistics.mean(token_counts)
            metrics.min_tokens = min(token_counts)
            metrics.max_tokens = max(token_counts)
            metrics.median_tokens = statistics.median(token_counts)
            
            token_limit = self.config.get('tokens', {}).get('warning_limit', 500)
            metrics.tokens_exceeding_limit = sum(1 for t in token_counts if t > token_limit)
        
        # Calculate overlap metrics
        overlap_percentages = self._calculate_overlaps(doc_chunks)
        if overlap_percentages:
            metrics.avg_overlap_percentage = statistics.mean(overlap_percentages)
            metrics.min_overlap_percentage = min(overlap_percentages)
            metrics.max_overlap_percentage = max(overlap_percentages)
            
            overlap_config = self.config.get('overlap', {})
            metrics.missing_overlap_count = sum(1 for o in overlap_percentages if o < overlap_config.get('min_percentage', 5))
            metrics.excessive_overlap_count = sum(1 for o in overlap_percentages if o > overlap_config.get('max_percentage', 30))
        
        # Duplicate detection
        hash_counts = Counter(text_hashes)
        metrics.exact_duplicates = sum(1 for count in hash_counts.values() if count > 1)
        metrics.duplicate_rate = metrics.exact_duplicates / metrics.total_chunks if metrics.total_chunks > 0 else 0
        
        # Check for duplicate chunk IDs
        chunk_ids = [c.get('chunk_id') for c in chunks if c.get('chunk_id')]
        metrics.duplicate_chunk_ids = len(chunk_ids) - len(set(chunk_ids))
        
        # Structure preservation scores
        metrics.header_preservation_score = metrics.chunks_with_headers / metrics.total_chunks if metrics.total_chunks > 0 else 0
        metrics.list_preservation_score = metrics.chunks_with_lists / metrics.total_chunks if metrics.total_chunks > 0 else 0
        metrics.table_preservation_score = metrics.chunks_with_tables / metrics.total_chunks if metrics.total_chunks > 0 else 0
        
        # Readability metrics
        if sentence_lengths:
            metrics.avg_sentence_length = statistics.mean(sentence_lengths)
        if word_counts:
            metrics.avg_words_per_chunk = statistics.mean(word_counts)
        
        # Metadata completeness
        total_fields = len(self.config.get('metadata', {}).get('required_fields', []))
        if total_fields > 0:
            complete_chunks = metrics.total_chunks - metrics.missing_metadata_count
            metrics.metadata_completeness = complete_chunks / metrics.total_chunks if metrics.total_chunks > 0 else 0
        
        # Processing time
        metrics.evaluation_time_seconds = time.time() - start_time
        
        self.logger.info(f"Analyzed {metrics.total_chunks} chunks in {metrics.evaluation_time_seconds:.2f}s")
        
        return metrics
    
    def calculate_quality_score(self, metrics: ChunkMetrics) -> QualityScore:
        """
        Calculate overall quality score.
        
        Args:
            metrics: Chunk metrics
            
        Returns:
            QualityScore
        """
        score = QualityScore()
        weights = self.config.get('quality_weights', {})
        score.weights = weights
        
        # 1. Chunk Size Score (0-1)
        size_config = self.config.get('chunk_size', {})
        ideal_min = size_config.get('ideal_min', 300)
        ideal_max = size_config.get('ideal_max', 1500)
        
        if ideal_min <= metrics.avg_chunk_size <= ideal_max:
            score.chunk_size_score = 1.0
        elif metrics.avg_chunk_size < ideal_min:
            score.chunk_size_score = max(0, metrics.avg_chunk_size / ideal_min)
        else:
            score.chunk_size_score = max(0, 1.0 - (metrics.avg_chunk_size - ideal_max) / ideal_max)
        
        # Penalize for outliers
        if metrics.tiny_chunks_count > metrics.total_chunks * 0.05:
            score.chunk_size_score *= 0.9
            score.warnings.append(f"{metrics.tiny_chunks_count} tiny chunks detected")
        
        if metrics.oversized_chunks_count > metrics.total_chunks * 0.05:
            score.chunk_size_score *= 0.9
            score.warnings.append(f"{metrics.oversized_chunks_count} oversized chunks detected")
        
        # 2. Metadata Score
        score.metadata_score = metrics.metadata_completeness
        if metrics.missing_metadata_count > 0:
            score.warnings.append(f"{metrics.missing_metadata_count} chunks with missing metadata")
        
        # 3. Structure Score
        structure_config = self.config.get('structure', {})
        min_header = structure_config.get('min_header_preservation', 0.8)
        
        if metrics.header_preservation_score >= min_header:
            score.structure_score = 1.0
        else:
            score.structure_score = metrics.header_preservation_score / min_header
        
        # 4. List Score
        min_list = structure_config.get('min_list_preservation', 0.7)
        if metrics.list_preservation_score >= min_list:
            score.list_score = 1.0
        else:
            score.list_score = metrics.list_preservation_score / min_list if min_list > 0 else 1.0
        
        # 5. Table Score
        min_table = structure_config.get('min_table_preservation', 0.6)
        if metrics.table_preservation_score >= min_table:
            score.table_score = 1.0
        else:
            score.table_score = metrics.table_preservation_score / min_table if min_table > 0 else 1.0
        
        # 6. Duplicate Score
        dup_config = self.config.get('duplicates', {})
        max_dup_rate = dup_config.get('max_acceptable_rate', 0.01)
        
        if metrics.duplicate_rate <= max_dup_rate:
            score.duplicate_score = 1.0
        else:
            score.duplicate_score = max(0, 1.0 - (metrics.duplicate_rate - max_dup_rate) / max_dup_rate)
        
        if metrics.duplicate_rate > max_dup_rate:
            score.issues.append(f"Duplicate rate ({metrics.duplicate_rate:.2%}) exceeds threshold")
        
        # 7. Overlap Score
        overlap_config = self.config.get('overlap', {})
        ideal_overlap = overlap_config.get('ideal_percentage', 15)
        
        if abs(metrics.avg_overlap_percentage - ideal_overlap) < 5:
            score.overlap_score = 1.0
        else:
            diff = abs(metrics.avg_overlap_percentage - ideal_overlap)
            score.overlap_score = max(0, 1.0 - diff / 20)
        
        # 8. Readability Score
        readability_config = self.config.get('readability', {})
        ideal_sent_len = readability_config.get('ideal_sentence_length', 20)
        
        if abs(metrics.avg_sentence_length - ideal_sent_len) < 5:
            score.readability_score = 1.0
        else:
            diff = abs(metrics.avg_sentence_length - ideal_sent_len)
            score.readability_score = max(0, 1.0 - diff / ideal_sent_len)
        
        # 9. Density Score (simplified - full implementation would analyze content)
        score.density_score = 0.8  # Placeholder
        
        # Calculate weighted overall score
        score.overall_score = (
            score.chunk_size_score * weights.get('chunk_size', 0.15) +
            score.metadata_score * weights.get('metadata', 0.10) +
            score.structure_score * weights.get('structure', 0.15) +
            score.list_score * weights.get('lists', 0.10) +
            score.table_score * weights.get('tables', 0.10) +
            score.duplicate_score * weights.get('duplicates', 0.10) +
            score.overlap_score * weights.get('overlap', 0.10) +
            score.readability_score * weights.get('readability', 0.10) +
            score.density_score * weights.get('density', 0.10)
        ) * 100
        
        return score
    
    def generate_recommendations(
        self,
        metrics: ChunkMetrics,
        score: QualityScore
    ) -> List[Recommendation]:
        """
        Generate quality improvement recommendations.
        
        Args:
            metrics: Chunk metrics
            score: Quality score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Chunk size recommendations
        if metrics.avg_chunk_size < 300:
            recommendations.append(Recommendation(
                priority="high",
                category="chunk_size",
                issue="Average chunk size is too small",
                recommendation=f"Increase chunk size from {metrics.avg_chunk_size:.0f} to 500-1000 characters",
                confidence=0.9,
                affected_chunks=metrics.total_chunks
            ))
        elif metrics.avg_chunk_size > 1500:
            recommendations.append(Recommendation(
                priority="medium",
                category="chunk_size",
                issue="Average chunk size is large",
                recommendation=f"Consider decreasing chunk size from {metrics.avg_chunk_size:.0f} to 800-1200 characters",
                confidence=0.8,
                affected_chunks=metrics.total_chunks
            ))
        
        # Overlap recommendations
        if metrics.avg_overlap_percentage < 10:
            recommendations.append(Recommendation(
                priority="medium",
                category="overlap",
                issue="Low overlap between chunks",
                recommendation=f"Increase overlap from {metrics.avg_overlap_percentage:.1f}% to 15-20%",
                confidence=0.85,
                affected_chunks=metrics.total_chunks
            ))
        elif metrics.avg_overlap_percentage > 25:
            recommendations.append(Recommendation(
                priority="low",
                category="overlap",
                issue="High overlap creates redundancy",
                recommendation=f"Decrease overlap from {metrics.avg_overlap_percentage:.1f}% to 15-20%",
                confidence=0.75,
                affected_chunks=metrics.total_chunks
            ))
        
        # Duplicate recommendations
        if metrics.duplicate_rate > 0.05:
            recommendations.append(Recommendation(
                priority="high",
                category="duplicates",
                issue=f"High duplicate rate: {metrics.duplicate_rate:.2%}",
                recommendation="Review chunking strategy to reduce duplicates - consider using different separators",
                confidence=0.9,
                affected_chunks=metrics.exact_duplicates
            ))
        
        # Structure recommendations
        if score.structure_score < 0.7:
            recommendations.append(Recommendation(
                priority="high",
                category="structure",
                issue="Headers and sections are being split",
                recommendation="Consider using section-aware chunking strategy",
                confidence=0.85,
                affected_chunks=int(metrics.total_chunks * (1 - score.structure_score))
            ))
        
        # Metadata recommendations
        if metrics.missing_metadata_count > 0:
            recommendations.append(Recommendation(
                priority="high",
                category="metadata",
                issue=f"{metrics.missing_metadata_count} chunks have incomplete metadata",
                recommendation="Ensure all required metadata fields are populated during chunking",
                confidence=1.0,
                affected_chunks=metrics.missing_metadata_count
            ))
        
        # Sort by priority and confidence
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: (priority_order[r.priority], -r.confidence))
        
        return recommendations
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        method = self.config.get('tokens', {}).get('estimate_method', 'simple')
        
        if method == 'simple':
            words = len(text.split())
            words_per_token = self.config.get('tokens', {}).get('words_per_token', 1.3)
            return int(words / words_per_token)
        else:
            # Fallback
            return len(text) // 4
    
    def _validate_metadata(self, chunk: Dict[str, Any]) -> bool:
        """Validate chunk metadata."""
        required_fields = self.config.get('metadata', {}).get('required_fields', [])
        
        for field in required_fields:
            if field not in chunk or chunk[field] is None:
                return False
        
        return True
    
    def _detect_headers(self, text: str) -> bool:
        """Detect if text contains headers."""
        # Check for Markdown headers
        if re.search(r'^#{1,6}\s+.+$', text, re.MULTILINE):
            return True
        
        # Check for all-caps lines (likely headers)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            if line.strip() and line.strip().isupper() and len(line.strip()) < 100:
                return True
        
        return False
    
    def _detect_lists(self, text: str) -> bool:
        """Detect if text contains lists."""
        # Bullet lists
        if re.search(r'^[\s]*[-*•]\s+', text, re.MULTILINE):
            return True
        
        # Numbered lists
        if re.search(r'^[\s]*\d+[\.\)]\s+', text, re.MULTILINE):
            return True
        
        return False
    
    def _detect_tables(self, text: str) -> bool:
        """Detect if text contains tables."""
        # Markdown tables
        if '|' in text and text.count('|') > 4:
            lines = text.split('\n')
            pipe_lines = [l for l in lines if '|' in l]
            if len(pipe_lines) > 2:
                return True
        
        return False
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_overlaps(self, doc_chunks: Dict[str, List[Dict]]) -> List[float]:
        """Calculate overlap percentages between consecutive chunks."""
        overlaps = []
        
        for doc_id, chunks in doc_chunks.items():
            if len(chunks) < 2:
                continue
            
            # Sort chunks by index
            sorted_chunks = sorted(chunks, key=lambda c: c.get('chunk_index', 0))
            
            for i in range(len(sorted_chunks) - 1):
                chunk1 = sorted_chunks[i]
                chunk2 = sorted_chunks[i + 1]
                
                text1 = chunk1.get('text', '')
                text2 = chunk2.get('text', '')
                
                if not text1 or not text2:
                    continue
                
                # Calculate overlap
                overlap_chars = self._calculate_text_overlap(text1, text2)
                overlap_percentage = (overlap_chars / len(text1) * 100) if len(text1) > 0 else 0
                overlaps.append(overlap_percentage)
        
        return overlaps
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> int:
        """Calculate character overlap between two texts."""
        # Find longest common suffix of text1 and prefix of text2
        min_len = min(len(text1), len(text2))
        
        for length in range(min_len, 0, -1):
            if text1[-length:] == text2[:length]:
                return length
        
        return 0

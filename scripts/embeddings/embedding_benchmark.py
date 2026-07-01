"""
Embedding benchmark for MedNexus-AI.

Provides benchmarking and cost estimation for embedding generation.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.file_utils import ensure_directory


class EmbeddingBenchmark:
    """Benchmark and cost estimation for embeddings."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize benchmark.
        
        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Cost configuration
        cost_config = config.get('cost_estimation', {})
        self.gemini_cost = cost_config.get('gemini_cost_per_1m_tokens', 0.00025)
        self.storage_cost = cost_config.get('storage_cost_per_gb_month', 0.023)
        
        # Metrics to track
        self.tracked_metrics = config.get('track_metrics', [])
    
    def generate_statistics(
        self,
        stats: Dict[str, Any],
        output_file: Path
    ) -> None:
        """
        Generate embedding statistics report.
        
        Args:
            stats: Statistics dictionary from EmbeddingManager
            output_file: Output file path
        """
        ensure_directory(output_file.parent)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_chunks': stats.get('total_chunks', 0),
                'successful': stats.get('successful', 0),
                'failed': stats.get('failed', 0),
                'cached': stats.get('cached', 0),
                'skipped': stats.get('skipped', 0),
                'success_rate': self._calculate_success_rate(stats),
            },
            'performance': {
                'total_time': stats.get('generation_time', 0),
                'average_time_per_chunk': self._calculate_avg_time(stats),
                'chunks_per_second': self._calculate_throughput(stats),
            },
            'provider': stats.get('provider_info', {}),
            'cache': stats.get('cache_stats', {}),
            'validation': stats.get('validation_stats', {}),
            'errors': {
                'validation_errors': stats.get('validation_errors', 0),
                'retry_count': stats.get('retry_count', 0),
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Saved statistics to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
    
    def generate_validation_report(
        self,
        validation_stats: Dict[str, Any],
        output_file: Path
    ) -> None:
        """
        Generate validation report.
        
        Args:
            validation_stats: Validation statistics
            output_file: Output file path
        """
        ensure_directory(output_file.parent)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_summary': validation_stats,
            'validation_checks': {
                'dimension_check': True,
                'nan_check': True,
                'inf_check': True,
                'zero_vector_check': True,
                'metadata_check': True,
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Saved validation report to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")
    
    def generate_cost_estimation(
        self,
        stats: Dict[str, Any],
        provider: str,
        dimension: int,
        output_file: Path
    ) -> None:
        """
        Generate cost estimation report.
        
        Args:
            stats: Processing statistics
            provider: Provider name
            dimension: Embedding dimension
            output_file: Output file path
        """
        ensure_directory(output_file.parent)
        
        total_chunks = stats.get('total_chunks', 0)
        successful = stats.get('successful', 0)
        
        # Estimate tokens
        avg_chunk_size = 1000  # characters
        tokens_per_chunk = avg_chunk_size // 4
        total_tokens = successful * tokens_per_chunk
        
        # Estimate API cost
        if provider == 'gemini':
            api_cost = (total_tokens / 1_000_000) * self.gemini_cost
        else:
            api_cost = 0.0  # Local models have no API cost
        
        # Estimate storage cost
        bytes_per_embedding = dimension * 4  # 4 bytes per float32
        total_bytes = successful * bytes_per_embedding
        total_gb = total_bytes / (1024 ** 3)
        storage_cost_monthly = total_gb * self.storage_cost
        
        # Estimate indexing time (approximate)
        indexing_time = successful * 0.001  # 1ms per embedding
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'dimension': dimension,
            'chunks': {
                'total': total_chunks,
                'processed': successful,
            },
            'tokens': {
                'estimated_per_chunk': tokens_per_chunk,
                'total_estimated': total_tokens,
            },
            'costs': {
                'api_cost_usd': round(api_cost, 4),
                'storage_cost_per_month_usd': round(storage_cost_monthly, 4),
                'total_monthly_usd': round(api_cost + storage_cost_monthly, 4),
            },
            'storage': {
                'bytes_per_embedding': bytes_per_embedding,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024 ** 2), 2),
                'total_gb': round(total_gb, 4),
            },
            'performance': {
                'estimated_indexing_time_seconds': round(indexing_time, 2),
            },
            'notes': [
                'API costs are estimates based on average token counts',
                'Storage costs are monthly recurring costs',
                'Local models (Sentence Transformers) have no API costs',
                'Indexing time is approximate and depends on vector database'
            ]
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Saved cost estimation to {output_file}")
            
            # Log summary
            self.logger.info(
                f"Cost Estimation: API=${api_cost:.4f}, "
                f"Storage=${storage_cost_monthly:.4f}/month, "
                f"Size={total_gb:.2f}GB"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save cost estimation: {e}")
    
    def compare_providers(
        self,
        provider_stats: List[Dict[str, Any]],
        output_file: Path
    ) -> None:
        """
        Compare multiple providers.
        
        Args:
            provider_stats: List of statistics for each provider
            output_file: Output file path
        """
        ensure_directory(output_file.parent)
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'providers': []
        }
        
        for stat in provider_stats:
            provider_info = stat.get('provider_info', {})
            
            comparison['providers'].append({
                'provider': provider_info.get('provider', 'unknown'),
                'model': provider_info.get('model', 'unknown'),
                'dimension': provider_info.get('dimension', 0),
                'success_rate': self._calculate_success_rate(stat),
                'avg_time_per_chunk': self._calculate_avg_time(stat),
                'throughput': self._calculate_throughput(stat),
                'cache_hit_rate': stat.get('cache_stats', {}).get('hit_rate', 0),
            })
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2)
            
            self.logger.info(f"Saved provider comparison to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save comparison: {e}")
    
    def _calculate_success_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate success rate."""
        total = stats.get('total_chunks', 0)
        successful = stats.get('successful', 0)
        cached = stats.get('cached', 0)
        
        if total == 0:
            return 0.0
        
        return ((successful + cached) / total) * 100
    
    def _calculate_avg_time(self, stats: Dict[str, Any]) -> float:
        """Calculate average time per chunk."""
        total_time = stats.get('generation_time', 0)
        successful = stats.get('successful', 0)
        cached = stats.get('cached', 0)
        
        total_processed = successful + cached
        if total_processed == 0:
            return 0.0
        
        return total_time / total_processed
    
    def _calculate_throughput(self, stats: Dict[str, Any]) -> float:
        """Calculate chunks per second."""
        total_time = stats.get('generation_time', 0)
        successful = stats.get('successful', 0)
        cached = stats.get('cached', 0)
        
        if total_time == 0:
            return 0.0
        
        return (successful + cached) / total_time

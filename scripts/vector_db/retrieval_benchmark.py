"""
Benchmarking module for vector retrieval system.

Calculates metrics like Recall@K, Precision@K, MRR, nDCG, latency, and memory usage.
"""

import sys
import time
import json
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import math

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


@dataclass
class BenchmarkMetrics:
    """Benchmark metrics."""
    
    # Retrieval metrics
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_1: float = 0.0
    precision_at_3: float = 0.0
    precision_at_5: float = 0.0
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg: float = 0.0  # Normalized Discounted Cumulative Gain
    hit_rate: float = 0.0
    
    # Performance metrics
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    
    # Resource metrics
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    
    # Query statistics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0


class RetrievalBenchmark:
    """
    Benchmark for vector retrieval system.
    
    Evaluates retrieval quality and performance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize benchmark.
        
        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Benchmark configuration
        benchmark_config = config.get('benchmarking', {})
        self.enabled = benchmark_config.get('enabled', True)
        self.metrics_to_track = set(benchmark_config.get('metrics', []))
        
        # Test queries
        test_queries_file = benchmark_config.get('test_queries_file')
        self.test_queries: List[Dict[str, Any]] = []
        
        if test_queries_file and Path(test_queries_file).exists():
            self.test_queries = self._load_test_queries(Path(test_queries_file))
        
        # Output configuration
        output_config = benchmark_config.get('output_files', {})
        self.output_dir = Path(benchmark_config.get('output_dir', 'datasets/evaluation'))
        self.metrics_file = output_config.get('metrics', 'retrieval_metrics.json')
        self.latency_file = output_config.get('latency', 'retrieval_latency.json')
        self.benchmark_file = output_config.get('benchmark', 'retrieval_benchmark.json')
        
        self.logger.info(
            f"RetrievalBenchmark initialized: {len(self.test_queries)} test queries"
        )
    
    def _load_test_queries(self, path: Path) -> List[Dict[str, Any]]:
        """Load test queries from file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load test queries: {e}")
            return []
    
    def benchmark_retrieval(
        self,
        retriever,
        queries: Optional[List[Dict[str, Any]]] = None
    ) -> BenchmarkMetrics:
        """
        Run retrieval benchmark.
        
        Args:
            retriever: Retriever instance (VectorRetriever or HybridRetriever)
            queries: Test queries (uses default if None)
            
        Returns:
            BenchmarkMetrics
        """
        if not self.enabled:
            self.logger.warning("Benchmarking is disabled")
            return BenchmarkMetrics()
        
        queries = queries or self.test_queries
        
        if not queries:
            self.logger.warning("No test queries available")
            return BenchmarkMetrics()
        
        self.logger.info(f"Running benchmark with {len(queries)} queries...")
        
        # Track metrics
        latencies = []
        memory_samples = []
        
        recall_at_k = {1: [], 3: [], 5: [], 10: []}
        precision_at_k = {1: [], 3: [], 5: []}
        mrr_scores = []
        ndcg_scores = []
        hits = 0
        
        successful = 0
        failed = 0
        
        process = psutil.Process()
        
        for query_data in queries:
            query_embedding = query_data.get('embedding')
            query_text = query_data.get('query', '')
            relevant_docs = set(query_data.get('relevant_docs', []))
            
            if not query_embedding or not relevant_docs:
                continue
            
            try:
                # Measure latency
                start_time = time.time()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Perform search
                results = retriever.search(
                    query_embedding=query_embedding,
                    top_k=10
                )
                
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                memory_samples.append(end_memory)
                
                # Extract result IDs
                result_ids = [r.get('chunk_id', '') for r in results]
                
                # Calculate recall@K
                for k in [1, 3, 5, 10]:
                    top_k_ids = set(result_ids[:k])
                    recall = len(top_k_ids & relevant_docs) / len(relevant_docs) if relevant_docs else 0
                    recall_at_k[k].append(recall)
                
                # Calculate precision@K
                for k in [1, 3, 5]:
                    top_k_ids = set(result_ids[:k])
                    precision = len(top_k_ids & relevant_docs) / k if k > 0 else 0
                    precision_at_k[k].append(precision)
                
                # Calculate MRR
                mrr = self._calculate_mrr(result_ids, relevant_docs)
                mrr_scores.append(mrr)
                
                # Calculate nDCG
                ndcg = self._calculate_ndcg(result_ids, relevant_docs, k=10)
                ndcg_scores.append(ndcg)
                
                # Hit rate
                if any(rid in relevant_docs for rid in result_ids[:10]):
                    hits += 1
                
                successful += 1
                
            except Exception as e:
                self.logger.warning(f"Query failed: {e}")
                failed += 1
        
        # Calculate aggregate metrics
        metrics = BenchmarkMetrics(
            recall_at_1=self._mean(recall_at_k[1]),
            recall_at_3=self._mean(recall_at_k[3]),
            recall_at_5=self._mean(recall_at_k[5]),
            recall_at_10=self._mean(recall_at_k[10]),
            precision_at_1=self._mean(precision_at_k[1]),
            precision_at_3=self._mean(precision_at_k[3]),
            precision_at_5=self._mean(precision_at_k[5]),
            mrr=self._mean(mrr_scores),
            ndcg=self._mean(ndcg_scores),
            hit_rate=hits / successful if successful > 0 else 0,
            avg_latency_ms=self._mean(latencies),
            p95_latency_ms=self._percentile(latencies, 95),
            p99_latency_ms=self._percentile(latencies, 99),
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            avg_memory_mb=self._mean(memory_samples),
            peak_memory_mb=max(memory_samples) if memory_samples else 0,
            total_queries=len(queries),
            successful_queries=successful,
            failed_queries=failed
        )
        
        self.logger.info(
            f"Benchmark complete: {successful} successful, {failed} failed"
        )
        
        return metrics
    
    def _calculate_mrr(
        self,
        result_ids: List[str],
        relevant_docs: set
    ) -> float:
        """
        Calculate Mean Reciprocal Rank.
        
        MRR = 1 / rank of first relevant document
        
        Args:
            result_ids: Retrieved document IDs
            relevant_docs: Set of relevant document IDs
            
        Returns:
            MRR score
        """
        for i, doc_id in enumerate(result_ids, 1):
            if doc_id in relevant_docs:
                return 1.0 / i
        
        return 0.0
    
    def _calculate_ndcg(
        self,
        result_ids: List[str],
        relevant_docs: set,
        k: int = 10
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain.
        
        DCG = Σ(rel_i / log2(i + 1))
        nDCG = DCG / IDCG
        
        Args:
            result_ids: Retrieved document IDs
            relevant_docs: Set of relevant document IDs
            k: Number of results to consider
            
        Returns:
            nDCG score
        """
        # Calculate DCG
        dcg = 0.0
        for i, doc_id in enumerate(result_ids[:k], 1):
            rel = 1 if doc_id in relevant_docs else 0
            dcg += rel / math.log2(i + 1)
        
        # Calculate IDCG (ideal DCG)
        ideal_relevances = [1] * min(len(relevant_docs), k)
        idcg = sum(rel / math.log2(i + 1) for i, rel in enumerate(ideal_relevances, 1))
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def _mean(self, values: List[float]) -> float:
        """Calculate mean."""
        return sum(values) / len(values) if values else 0.0
    
    def _percentile(self, values: List[float], p: int) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def save_metrics(
        self,
        metrics: BenchmarkMetrics,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save metrics to file.
        
        Args:
            metrics: Benchmark metrics
            filename: Output filename (uses default if None)
            
        Returns:
            Output file path
        """
        output_path = self.output_dir / (filename or self.metrics_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(metrics)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Metrics saved to: {output_path}")
        
        return output_path
    
    def save_latency_report(
        self,
        latencies: List[float],
        filename: Optional[str] = None
    ) -> Path:
        """
        Save latency analysis.
        
        Args:
            latencies: List of latency measurements (ms)
            filename: Output filename
            
        Returns:
            Output file path
        """
        output_path = self.output_dir / (filename or self.latency_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'count': len(latencies),
                'mean_ms': self._mean(latencies),
                'min_ms': min(latencies) if latencies else 0,
                'max_ms': max(latencies) if latencies else 0,
                'p50_ms': self._percentile(latencies, 50),
                'p95_ms': self._percentile(latencies, 95),
                'p99_ms': self._percentile(latencies, 99)
            },
            'latencies': latencies
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Latency report saved to: {output_path}")
        
        return output_path
    
    def compare_retrievers(
        self,
        retrievers: Dict[str, Any],
        queries: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, BenchmarkMetrics]:
        """
        Compare multiple retrievers.
        
        Args:
            retrievers: Dictionary of retriever_name -> retriever_instance
            queries: Test queries
            
        Returns:
            Dictionary of retriever_name -> metrics
        """
        self.logger.info(f"Comparing {len(retrievers)} retrievers...")
        
        results = {}
        
        for name, retriever in retrievers.items():
            self.logger.info(f"Benchmarking {name}...")
            metrics = self.benchmark_retrieval(retriever, queries)
            results[name] = metrics
        
        # Save comparison
        comparison_path = self.output_dir / self.benchmark_file
        comparison_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'retrievers': {
                name: asdict(metrics)
                for name, metrics in results.items()
            }
        }
        
        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Comparison saved to: {comparison_path}")
        
        return results
    
    def print_metrics(self, metrics: BenchmarkMetrics) -> None:
        """
        Print metrics summary.
        
        Args:
            metrics: Benchmark metrics
        """
        print("\n" + "=" * 80)
        print("RETRIEVAL BENCHMARK RESULTS")
        print("=" * 80)
        
        print("\nRetrieval Quality:")
        print(f"  Recall@1:     {metrics.recall_at_1:.3f}")
        print(f"  Recall@3:     {metrics.recall_at_3:.3f}")
        print(f"  Recall@5:     {metrics.recall_at_5:.3f}")
        print(f"  Recall@10:    {metrics.recall_at_10:.3f}")
        print(f"  Precision@1:  {metrics.precision_at_1:.3f}")
        print(f"  Precision@3:  {metrics.precision_at_3:.3f}")
        print(f"  Precision@5:  {metrics.precision_at_5:.3f}")
        print(f"  MRR:          {metrics.mrr:.3f}")
        print(f"  nDCG:         {metrics.ndcg:.3f}")
        print(f"  Hit Rate:     {metrics.hit_rate:.3f}")
        
        print("\nPerformance:")
        print(f"  Avg Latency:  {metrics.avg_latency_ms:.2f} ms")
        print(f"  P95 Latency:  {metrics.p95_latency_ms:.2f} ms")
        print(f"  P99 Latency:  {metrics.p99_latency_ms:.2f} ms")
        print(f"  Min Latency:  {metrics.min_latency_ms:.2f} ms")
        print(f"  Max Latency:  {metrics.max_latency_ms:.2f} ms")
        
        print("\nResources:")
        print(f"  Avg Memory:   {metrics.avg_memory_mb:.1f} MB")
        print(f"  Peak Memory:  {metrics.peak_memory_mb:.1f} MB")
        
        print("\nQueries:")
        print(f"  Total:        {metrics.total_queries}")
        print(f"  Successful:   {metrics.successful_queries}")
        print(f"  Failed:       {metrics.failed_queries}")
        
        print("=" * 80 + "\n")

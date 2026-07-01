"""
Main chunk evaluator for MedNexus-AI Knowledge Ingestion Framework.

Orchestrates chunk quality evaluation and report generation.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import csv
import time

import sys
sys.path.append(str(Path(__file__).parent.parent))

from evaluators.metrics import ChunkMetrics, QualityScore, BenchmarkResult, Recommendation
from evaluators.quality_analyzer import QualityAnalyzer
from utils.logger import get_logger
from utils.file_utils import ensure_directory


class ChunkEvaluator:
    """Evaluates chunk quality and generates comprehensive reports."""
    
    def __init__(
        self,
        chunks_dir: Path,
        output_dir: Path,
        config: Dict[str, Any]
    ):
        """
        Initialize chunk evaluator.
        
        Args:
            chunks_dir: Directory containing chunk files
            output_dir: Directory for evaluation reports
            config: Evaluation configuration
        """
        self.chunks_dir = chunks_dir
        self.output_dir = ensure_directory(output_dir)
        self.config = config
        
        self.analyzer = QualityAnalyzer(config)
        self.logger = get_logger(__name__)
    
    def evaluate(
        self,
        source: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate chunks and generate reports.
        
        Args:
            source: Filter by source name
            strategy: Filter by strategy name
            
        Returns:
            Evaluation results dictionary
        """
        start_time = time.time()
        
        self.logger.info("Starting chunk quality evaluation...")
        
        # Load chunks
        chunks = self._load_chunks(source, strategy)
        
        if not chunks:
            self.logger.warning("No chunks found to evaluate")
            return {}
        
        self.logger.info(f"Loaded {len(chunks)} chunks for evaluation")
        
        # Analyze chunks
        metrics = self.analyzer.analyze(chunks)
        
        # Calculate quality score
        quality_score = self.analyzer.calculate_quality_score(metrics)
        
        # Generate recommendations
        recommendations = self.analyzer.generate_recommendations(metrics, quality_score)
        
        # Prepare results
        results = {
            'evaluation_info': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source_filter': source,
                'strategy_filter': strategy,
                'total_chunks_evaluated': len(chunks),
                'evaluation_time_seconds': time.time() - start_time
            },
            'metrics': metrics.to_dict(),
            'quality_score': quality_score.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
        }
        
        # Generate visualization data
        if self.config.get('visualization', {}).get('generate_histogram_data', True):
            viz_data = self._generate_visualization_data(chunks, metrics)
            results['visualization'] = viz_data
        
        # Sample chunks
        if self.config.get('output', {}).get('include_sample_chunks', True):
            sample_size = self.config.get('output', {}).get('sample_size', 10)
            results['sample_chunks'] = chunks[:sample_size]
        
        self.logger.info(f"Evaluation complete. Quality score: {quality_score.overall_score:.1f}/100 ({quality_score.grade()})")
        
        return results
    
    def evaluate_benchmark(self) -> List[BenchmarkResult]:
        """
        Benchmark different chunking strategies.
        
        Returns:
            List of benchmark results
        """
        self.logger.info("Starting strategy benchmark...")
        
        strategies = self.config.get('benchmark', {}).get('strategies', [])
        results = []
        
        for strategy in strategies:
            self.logger.info(f"Evaluating strategy: {strategy}")
            
            # Load chunks for this strategy
            chunks = self._load_chunks(strategy=strategy)
            
            if not chunks:
                self.logger.warning(f"No chunks found for strategy: {strategy}")
                continue
            
            # Analyze
            metrics = self.analyzer.analyze(chunks)
            quality_score = self.analyzer.calculate_quality_score(metrics)
            
            # Create benchmark result
            result = BenchmarkResult(
                strategy=strategy,
                avg_chunk_size=metrics.avg_chunk_size,
                chunk_count=metrics.total_chunks,
                overlap_percentage=metrics.avg_overlap_percentage,
                duplicate_rate=metrics.duplicate_rate,
                processing_time=metrics.evaluation_time_seconds,
                quality_score=quality_score.overall_score,
                recommended_use_case=self._get_use_case(strategy)
            )
            
            results.append(result)
        
        # Sort by quality score
        results.sort(key=lambda r: r.quality_score, reverse=True)
        
        if results:
            best = results[0]
            self.logger.info(f"Best strategy: {best.strategy} (score: {best.quality_score:.1f})")
        
        return results
    
    def save_reports(self, results: Dict[str, Any]):
        """
        Save evaluation reports to files.
        
        Args:
            results: Evaluation results
        """
        self.logger.info("Saving evaluation reports...")
        
        # 1. Quality report (JSON)
        quality_report_path = self.output_dir / "chunk_quality_report.json"
        with open(quality_report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved quality report: {quality_report_path}")
        
        # 2. Statistics (JSON)
        stats_path = self.output_dir / "chunk_statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metrics': results['metrics'],
                'evaluation_info': results['evaluation_info']
            }, f, indent=2)
        self.logger.info(f"Saved statistics: {stats_path}")
        
        # 3. Recommendations (Markdown)
        recommendations_path = self.output_dir / "chunk_recommendations.md"
        self._save_recommendations_markdown(
            results['recommendations'],
            results['quality_score'],
            recommendations_path
        )
        self.logger.info(f"Saved recommendations: {recommendations_path}")
        
        # 4. Dashboard data (JSON)
        dashboard_path = self.output_dir / "quality_dashboard.json"
        dashboard_data = {
            'summary': {
                'quality_score': results['quality_score']['overall_score'],
                'grade': results['quality_score'].get('grade', 'N/A'),
                'total_chunks': results['metrics']['total_chunks'],
                'total_documents': results['metrics']['total_documents'],
                'avg_chunk_size': results['metrics']['avg_chunk_size'],
            },
            'scores': {
                k: v for k, v in results['quality_score'].items()
                if k.endswith('_score') and k != 'overall_score'
            },
            'key_metrics': {
                'duplicate_rate': results['metrics']['duplicate_rate'],
                'avg_overlap': results['metrics']['avg_overlap_percentage'],
                'metadata_completeness': results['metrics']['metadata_completeness'],
            },
            'visualization': results.get('visualization', {})
        }
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2)
        self.logger.info(f"Saved dashboard data: {dashboard_path}")
    
    def save_benchmark_csv(self, benchmark_results: List[BenchmarkResult]):
        """
        Save benchmark results to CSV.
        
        Args:
            benchmark_results: List of benchmark results
        """
        csv_path = self.output_dir / "chunk_benchmark.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if not benchmark_results:
                return
            
            fieldnames = benchmark_results[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in benchmark_results:
                writer.writerow(result.to_dict())
        
        self.logger.info(f"Saved benchmark CSV: {csv_path}")
    
    def _load_chunks(
        self,
        source: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load chunks from JSON files."""
        chunks = []
        
        # Find chunk files
        if source:
            source_dir = self.chunks_dir / source
            if not source_dir.exists():
                self.logger.warning(f"Source directory not found: {source_dir}")
                return chunks
            chunk_files = list(source_dir.glob('*.json'))
        else:
            chunk_files = list(self.chunks_dir.rglob('*.json'))
        
        # Load chunks from files
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Filter by strategy if specified
                file_strategy = data.get('strategy', '')
                if strategy and file_strategy != strategy:
                    continue
                
                # Extract chunks array
                file_chunks = data.get('chunks', [])
                chunks.extend(file_chunks)
                
            except Exception as e:
                self.logger.error(f"Error loading {chunk_file}: {e}")
        
        return chunks
    
    def _generate_visualization_data(
        self,
        chunks: List[Dict[str, Any]],
        metrics: ChunkMetrics
    ) -> Dict[str, Any]:
        """Generate data for visualizations."""
        import statistics
        
        # Chunk size distribution
        sizes = [len(c.get('text', '')) for c in chunks]
        
        # Create histogram bins
        bins = self.config.get('visualization', {}).get('histogram_bins', 50)
        if sizes:
            min_size = min(sizes)
            max_size = max(sizes)
            bin_width = (max_size - min_size) / bins if max_size > min_size else 1
            
            histogram = {}
            for size in sizes:
                bin_index = int((size - min_size) / bin_width) if bin_width > 0 else 0
                bin_index = min(bin_index, bins - 1)
                bin_label = f"{int(min_size + bin_index * bin_width)}-{int(min_size + (bin_index + 1) * bin_width)}"
                histogram[bin_label] = histogram.get(bin_label, 0) + 1
        else:
            histogram = {}
        
        viz_data = {
            'chunk_size_distribution': {
                'histogram': histogram,
                'mean': metrics.avg_chunk_size,
                'median': metrics.median_chunk_size,
                'std': metrics.std_chunk_size
            },
            'token_distribution': {
                'mean': metrics.avg_tokens,
                'median': metrics.median_tokens,
                'max': metrics.max_tokens
            },
            'structure_breakdown': {
                'with_headers': metrics.chunks_with_headers,
                'with_lists': metrics.chunks_with_lists,
                'with_tables': metrics.chunks_with_tables,
                'plain_text': metrics.total_chunks - metrics.chunks_with_headers - metrics.chunks_with_lists - metrics.chunks_with_tables
            }
        }
        
        return viz_data
    
    def _save_recommendations_markdown(
        self,
        recommendations: List[Dict[str, Any]],
        quality_score: Dict[str, Any],
        output_path: Path
    ):
        """Save recommendations as Markdown."""
        lines = []
        
        lines.append("# Chunk Quality Recommendations\n")
        lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Overall Quality Score:** {quality_score['overall_score']:.1f}/100\n")
        lines.append("\n---\n")
        
        # Group by priority
        by_priority = {'high': [], 'medium': [], 'low': []}
        for rec in recommendations:
            priority = rec.get('priority', 'medium')
            by_priority[priority].append(rec)
        
        for priority in ['high', 'medium', 'low']:
            recs = by_priority[priority]
            if not recs:
                continue
            
            lines.append(f"\n## {priority.upper()} Priority\n")
            
            for rec in recs:
                lines.append(f"\n### {rec['category'].replace('_', ' ').title()}\n")
                lines.append(f"**Issue:** {rec['issue']}\n")
                lines.append(f"**Recommendation:** {rec['recommendation']}\n")
                lines.append(f"**Confidence:** {rec['confidence']:.0%}\n")
                if rec.get('affected_chunks'):
                    lines.append(f"**Affected Chunks:** {rec['affected_chunks']}\n")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def _get_use_case(self, strategy: str) -> str:
        """Get recommended use case for strategy."""
        use_cases = {
            'recursive': 'General-purpose documents with mixed content',
            'fixed': 'Documents requiring uniform chunk sizes',
            'paragraph': 'Documents with clear paragraph structure',
            'section': 'Structured documents with headers and sections'
        }
        return use_cases.get(strategy, 'Unknown')

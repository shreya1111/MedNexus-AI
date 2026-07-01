"""
Chunk manager for MedNexus-AI Knowledge Ingestion Framework.

Orchestrates chunking operations with incremental processing and validation.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time

import sys
sys.path.append(str(Path(__file__).parent.parent))

from chunkers.base_chunker import Chunk, ChunkingResult
from chunkers.recursive_chunker import RecursiveChunker
from chunkers.fixed_chunker import FixedChunker
from chunkers.paragraph_chunker import ParagraphChunker
from chunkers.section_chunker import SectionChunker
from utils.logger import get_logger
from utils.hash_utils import compute_file_hash
from utils.file_utils import ensure_directory


class ChunkManager:
    """Manages document chunking with incremental processing."""
    
    def __init__(
        self,
        output_dir: Path,
        config: Dict[str, Any],
        strategy: str = "recursive",
        enable_incremental: bool = True,
    ):
        """
        Initialize chunk manager.
        
        Args:
            output_dir: Directory for chunk output
            config: Chunking configuration
            strategy: Chunking strategy name
            enable_incremental: Enable incremental processing
        """
        self.output_dir = ensure_directory(output_dir)
        self.config = config
        self.strategy_name = strategy
        self.enable_incremental = enable_incremental
        
        # Initialize chunker
        self.chunker = self._create_chunker(strategy, config)
        
        # Checksum cache for incremental processing
        self.checksum_cache_file = self.output_dir.parent / "chunk_checksums.json"
        self.checksum_cache = self._load_checksum_cache()
        
        self.logger = get_logger(__name__)
    
    def _create_chunker(self, strategy: str, config: Dict[str, Any]):
        """Create chunker based on strategy."""
        strategy_config = config.get('strategies', {}).get(strategy, {})
        
        if strategy == "recursive":
            return RecursiveChunker(**strategy_config)
        elif strategy == "fixed":
            return FixedChunker(**strategy_config)
        elif strategy == "paragraph":
            return ParagraphChunker(**strategy_config)
        elif strategy == "section":
            return SectionChunker(**strategy_config)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def process_document(
        self,
        input_path: Path,
        source: str,
        force: bool = False,
    ) -> ChunkingResult:
        """
        Process a single document.
        
        Args:
            input_path: Path to input document
            source: Source name
            force: Force reprocessing even if unchanged
            
        Returns:
            ChunkingResult
        """
        start_time = time.time()
        document_id = input_path.stem
        
        try:
            # Check if document needs processing
            if not force and self.enable_incremental:
                if not self._needs_processing(input_path):
                    self.logger.info(f"Skipping unchanged document: {document_id}")
                    return ChunkingResult(
                        document_id=document_id,
                        source=source,
                        chunks=[],
                        processing_time_seconds=time.time() - start_time,
                        status='skipped',
                        metadata={'reason': 'unchanged'}
                    )
            
            # Read document
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                self.logger.warning(f"Empty document: {document_id}")
                return ChunkingResult(
                    document_id=document_id,
                    source=source,
                    chunks=[],
                    processing_time_seconds=time.time() - start_time,
                    status='failed',
                    error_message='Empty document'
                )
            
            # Calculate document checksum
            doc_checksum = compute_file_hash(input_path, algorithm='sha256')
            
            # Chunk text
            chunks = self.chunker.chunk_text(
                text=text,
                document_id=document_id,
                source=source,
                parent_document_checksum=doc_checksum
            )
            
            # Save chunks
            output_path = self._save_chunks(chunks, document_id, source)
            
            # Update checksum cache
            if self.enable_incremental:
                self._update_checksum_cache(input_path, doc_checksum)
            
            processing_time = time.time() - start_time
            
            self.logger.info(
                f"Chunked {document_id}: {len(chunks)} chunks in {processing_time:.2f}s"
            )
            
            return ChunkingResult(
                document_id=document_id,
                source=source,
                chunks=chunks,
                processing_time_seconds=processing_time,
                status='success',
                metadata={
                    'output_path': str(output_path),
                    'document_checksum': doc_checksum,
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error chunking document {document_id}: {e}")
            return ChunkingResult(
                document_id=document_id,
                source=source,
                chunks=[],
                processing_time_seconds=time.time() - start_time,
                status='failed',
                error_message=str(e)
            )
    
    def process_batch(
        self,
        input_paths: List[Path],
        source: str,
        force: bool = False,
        show_progress: bool = True,
    ) -> List[ChunkingResult]:
        """
        Process multiple documents.
        
        Args:
            input_paths: List of input paths
            source: Source name
            force: Force reprocessing
            show_progress: Show progress bar
            
        Returns:
            List of ChunkingResult objects
        """
        results = []
        
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(input_paths, desc=f"Chunking {source}")
            except ImportError:
                iterator = input_paths
        else:
            iterator = input_paths
        
        for input_path in iterator:
            result = self.process_document(input_path, source, force)
            results.append(result)
        
        # Save checksum cache
        if self.enable_incremental:
            self._save_checksum_cache()
        
        return results
    
    def _needs_processing(self, input_path: Path) -> bool:
        """Check if document needs processing."""
        path_key = str(input_path)
        
        if path_key not in self.checksum_cache:
            return True
        
        current_checksum = compute_file_hash(input_path, algorithm='sha256')
        cached_checksum = self.checksum_cache[path_key]
        
        return current_checksum != cached_checksum
    
    def _save_chunks(
        self,
        chunks: List[Chunk],
        document_id: str,
        source: str
    ) -> Path:
        """Save chunks to JSON file."""
        # Organize by source if configured
        if self.config.get('output', {}).get('organize_by_source', True):
            output_subdir = self.output_dir / source
            output_subdir.mkdir(parents=True, exist_ok=True)
        else:
            output_subdir = self.output_dir
        
        # Generate filename
        filename_pattern = self.config.get('output', {}).get(
            'filename_pattern',
            '{document_stem}.json'
        )
        filename = filename_pattern.format(document_stem=document_id)
        output_path = output_subdir / filename
        
        # Convert chunks to dict
        chunks_data = {
            'document_id': document_id,
            'source': source,
            'strategy': self.strategy_name,
            'chunk_count': len(chunks),
            'chunks': [chunk.to_dict() for chunk in chunks]
        }
        
        # Write JSON
        indent = self.config.get('output', {}).get('indent', 2)
        ensure_ascii = self.config.get('output', {}).get('ensure_ascii', False)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        return output_path
    
    def _load_checksum_cache(self) -> Dict[str, str]:
        """Load checksum cache from disk."""
        if self.checksum_cache_file.exists():
            try:
                with open(self.checksum_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load checksum cache: {e}")
        
        return {}
    
    def _save_checksum_cache(self):
        """Save checksum cache to disk."""
        try:
            with open(self.checksum_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.checksum_cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save checksum cache: {e}")
    
    def _update_checksum_cache(self, input_path: Path, checksum: str):
        """Update checksum cache for a document."""
        path_key = str(input_path)
        self.checksum_cache[path_key] = checksum
    
    def get_statistics(self, results: List[ChunkingResult]) -> Dict[str, Any]:
        """Calculate statistics from results."""
        successful = [r for r in results if r.status == 'success']
        failed = [r for r in results if r.status == 'failed']
        skipped = [r for r in results if r.status == 'skipped']
        
        total_chunks = sum(r.chunk_count for r in successful)
        all_chunk_sizes = []
        
        for result in successful:
            for chunk in result.chunks:
                all_chunk_sizes.append(len(chunk.text))
        
        avg_chunk_size = sum(all_chunk_sizes) / len(all_chunk_sizes) if all_chunk_sizes else 0
        median_chunk_size = sorted(all_chunk_sizes)[len(all_chunk_sizes) // 2] if all_chunk_sizes else 0
        
        return {
            'total_documents': len(results),
            'successful_documents': len(successful),
            'failed_documents': len(failed),
            'skipped_documents': len(skipped),
            'total_chunks': total_chunks,
            'average_chunks_per_document': total_chunks / len(successful) if successful else 0,
            'average_chunk_size': avg_chunk_size,
            'median_chunk_size': median_chunk_size,
            'largest_chunk': max(all_chunk_sizes) if all_chunk_sizes else 0,
            'smallest_chunk': min(all_chunk_sizes) if all_chunk_sizes else 0,
            'total_processing_time': sum(r.processing_time_seconds for r in results),
        }

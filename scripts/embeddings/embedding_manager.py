"""
Embedding manager for MedNexus-AI.

Orchestrates the entire embedding generation pipeline with caching,
validation, and benchmarking.
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from embeddings.base_embedder import BaseEmbedder, EmbeddingResult, EmbeddingMetadata
from embeddings.provider_factory import ProviderFactory
from embeddings.embedding_cache import EmbeddingCache
from embeddings.embedding_validator import EmbeddingValidator
from utils.logger import get_logger
from utils.file_utils import ensure_directory
from utils.hash_utils import calculate_file_checksum, calculate_string_checksum


class EmbeddingManager:
    """Manages embedding generation pipeline."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        chunks_dir: Path,
        output_dir: Path
    ):
        """
        Initialize embedding manager.
        
        Args:
            config: Complete embedding configuration
            chunks_dir: Directory containing chunk files
            output_dir: Directory for embedding output
        """
        self.config = config
        self.chunks_dir = Path(chunks_dir)
        self.output_dir = ensure_directory(Path(output_dir))
        self.logger = get_logger(__name__)
        
        # Provider configuration
        provider_config = config.get('provider', {})
        self.active_provider = provider_config.get('active', 'sentence-transformers')
        
        # Get provider-specific config
        provider_settings = provider_config.get(self.active_provider, {})
        
        # Initialize provider
        self.embedder: Optional[BaseEmbedder] = None
        self._initialize_provider(self.active_provider, provider_settings)
        
        # Processing configuration
        proc_config = config.get('processing', {})
        self.batch_size = proc_config.get('batch_size', 32)
        self.max_workers = proc_config.get('max_workers', 4)
        self.resume_enabled = proc_config.get('resume_enabled', True)
        self.skip_existing = proc_config.get('skip_existing', True)
        self.force_regenerate = proc_config.get('force_regenerate', False)
        
        # Initialize cache
        cache_config = config.get('cache', {})
        self.cache = EmbeddingCache(
            cache_dir=Path(cache_config.get('cache_dir', output_dir / '.cache')),
            strategy=cache_config.get('strategy', 'checksum'),
            enabled=cache_config.get('enabled', True) and not self.force_regenerate
        )
        
        # Initialize validator
        validation_config = config.get('validation', {})
        self.validator = EmbeddingValidator(validation_config)
        
        # Output configuration
        output_config = config.get('output', {})
        self.save_json = output_config.get('save_json', True)
        self.save_numpy = output_config.get('save_numpy', False)
        self.organize_by = output_config.get('organize_by', 'source')
        
        # Retry configuration
        retry_config = config.get('retry', {})
        self.max_retries = retry_config.get('max_attempts', 3)
        self.backoff_factor = retry_config.get('backoff_factor', 2)
        
        # Statistics
        self.stats = {
            'total_chunks': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'skipped': 0,
            'generation_time': 0.0,
            'validation_errors': 0,
            'retry_count': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _initialize_provider(
        self,
        provider_name: str,
        provider_config: Dict[str, Any]
    ) -> None:
        """Initialize embedding provider."""
        try:
            self.embedder = ProviderFactory.create_embedder(
                provider_name,
                provider_config
            )
            self.embedder.initialize()
            
            self.logger.info(
                f"Initialized {provider_name} provider. "
                f"Dimension: {self.embedder.get_dimension()}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize provider: {e}")
            raise
    

    def process_chunks(
        self,
        source: Optional[str] = None,
        document: Optional[str] = None,
        limit: Optional[int] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Process chunks and generate embeddings.
        
        Args:
            source: Filter by source name
            document: Filter by document name
            limit: Maximum number of chunks to process
            show_progress: Show progress bar
            
        Returns:
            Dictionary containing processing results
        """
        self.stats['start_time'] = datetime.now().isoformat()
        start = time.time()
        
        # Load chunks
        chunks = self._load_chunks(source, document, limit)
        
        if not chunks:
            self.logger.warning("No chunks found to process")
            return self.stats
        
        self.logger.info(f"Processing {len(chunks)} chunks")
        self.stats['total_chunks'] = len(chunks)
        
        # Process in batches
        results = []
        batch_size = min(self.batch_size, self.embedder.get_max_batch_size())
        
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(total=len(chunks), desc="Generating embeddings")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
            
            if progress_bar:
                progress_bar.update(len(batch))
        
        if progress_bar:
            progress_bar.close()
        
        # Save results
        self._save_results(results, source)
        
        # Save cache
        self.cache.save()
        
        # Update statistics
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['generation_time'] = time.time() - start
        
        self.logger.info(
            f"Embedding generation complete. "
            f"Successful: {self.stats['successful']}, "
            f"Failed: {self.stats['failed']}, "
            f"Cached: {self.stats['cached']}"
        )
        
        return self.stats
    
    def _load_chunks(
        self,
        source: Optional[str],
        document: Optional[str],
        limit: Optional[int]
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
            if document and document not in chunk_file.stem:
                continue
            
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_chunks = data.get('chunks', [])
                chunks.extend(file_chunks)
                
                if limit and len(chunks) >= limit:
                    chunks = chunks[:limit]
                    break
                    
            except Exception as e:
                self.logger.error(f"Error loading {chunk_file}: {e}")
        
        return chunks
    
    def _process_batch(
        self,
        batch: List[Dict[str, Any]]
    ) -> List[EmbeddingResult]:
        """Process a batch of chunks."""
        results = []
        
        # Separate cached and non-cached
        to_generate = []
        cached_results = []
        
        for chunk in batch:
            chunk_id = chunk.get('chunk_id', '')
            text = chunk.get('text', '')
            
            if not text:
                self.logger.warning(f"Empty text for chunk {chunk_id}")
                results.append(EmbeddingResult(
                    chunk_id=chunk_id,
                    status='failed',
                    error='Empty text'
                ))
                self.stats['failed'] += 1
                continue
            
            # Check cache
            chunk_checksum = chunk.get('checksum') or calculate_string_checksum(text)
            cached = self.cache.get(
                chunk_id=chunk_id,
                chunk_checksum=chunk_checksum,
                provider=self.active_provider,
                model=self.embedder.model_name
            )
            
            if cached and not self.force_regenerate:
                # Use cached embedding
                result = EmbeddingResult(
                    chunk_id=chunk_id,
                    embedding=cached['embedding'],
                    metadata=EmbeddingMetadata(**cached['metadata']),
                    status='cached'
                )
                cached_results.append(result)
                self.stats['cached'] += 1
            else:
                to_generate.append(chunk)
        
        # Generate embeddings for non-cached chunks
        if to_generate:
            generated = self._generate_embeddings(to_generate)
            results.extend(generated)
        
        results.extend(cached_results)
        return results
    
    def _generate_embeddings(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[EmbeddingResult]:
        """Generate embeddings for chunks."""
        results = []
        texts = [c.get('text', '') for c in chunks]
        
        for attempt in range(self.max_retries):
            try:
                start = time.time()
                embeddings = self.embedder.embed_batch(texts)
                generation_time = time.time() - start
                
                # Process each embedding
                for i, chunk in enumerate(chunks):
                    embedding = embeddings[i]
                    chunk_id = chunk.get('chunk_id', '')
                    
                    # Validate embedding
                    validation = self.validator.validate_embedding(
                        embedding=embedding,
                        expected_dimension=self.embedder.get_dimension(),
                        chunk_id=chunk_id
                    )
                    
                    if not validation.is_valid:
                        self.logger.warning(
                            f"Validation failed for {chunk_id}: {validation.errors}"
                        )
                        self.stats['validation_errors'] += 1
                        results.append(EmbeddingResult(
                            chunk_id=chunk_id,
                            status='failed',
                            error='; '.join(validation.errors)
                        ))
                        self.stats['failed'] += 1
                        continue
                    
                    # Create metadata
                    chunk_checksum = chunk.get('checksum') or calculate_string_checksum(texts[i])
                    
                    metadata = EmbeddingMetadata(
                        embedding_id=f"{chunk_id}_emb",
                        chunk_id=chunk_id,
                        document_id=chunk.get('document_id', ''),
                        provider=self.active_provider,
                        model=self.embedder.model_name,
                        dimension=len(embedding),
                        created_at=datetime.now().isoformat(),
                        source=chunk.get('source'),
                        checksum=calculate_string_checksum(str(embedding)),
                        chunk_checksum=chunk_checksum,
                        generation_time=generation_time / len(chunks),
                        quality_score=chunk.get('quality_score'),
                        token_count=self.embedder.estimate_tokens(texts[i]),
                        processing_status='success',
                        retry_count=attempt,
                        cache_hit=False
                    )
                    
                    result = EmbeddingResult(
                        chunk_id=chunk_id,
                        embedding=embedding,
                        metadata=metadata,
                        status='success',
                        generation_time=generation_time / len(chunks)
                    )
                    
                    results.append(result)
                    self.stats['successful'] += 1
                    
                    # Cache the embedding
                    self.cache.put(
                        chunk_id=chunk_id,
                        chunk_checksum=chunk_checksum,
                        provider=self.active_provider,
                        model=self.embedder.model_name,
                        embedding=embedding,
                        metadata=metadata.to_dict()
                    )
                
                # Success - break retry loop
                break
                
            except Exception as e:
                self.logger.error(f"Embedding generation failed (attempt {attempt + 1}): {e}")
                self.stats['retry_count'] += 1
                
                if attempt < self.max_retries - 1:
                    sleep_time = self.backoff_factor ** attempt
                    self.logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    # Max retries exceeded
                    for chunk in chunks:
                        results.append(EmbeddingResult(
                            chunk_id=chunk.get('chunk_id', ''),
                            status='failed',
                            error=str(e),
                            retry_count=attempt + 1
                        ))
                        self.stats['failed'] += 1
        
        return results
    
    def _save_results(
        self,
        results: List[EmbeddingResult],
        source: Optional[str]
    ) -> None:
        """Save embedding results to files."""
        if not results:
            return
        
        # Organize by source/document
        organized = self._organize_results(results, source)
        
        for key, group_results in organized.items():
            if self.save_json:
                self._save_json(key, group_results)
            
            if self.save_numpy:
                self._save_numpy(key, group_results)
    
    def _organize_results(
        self,
        results: List[EmbeddingResult],
        source: Optional[str]
    ) -> Dict[str, List[EmbeddingResult]]:
        """Organize results by source or document."""
        organized = {}
        
        for result in results:
            if not result.is_success():
                continue
            
            if self.organize_by == 'source' and result.metadata:
                key = result.metadata.source or 'unknown'
            elif self.organize_by == 'document' and result.metadata:
                key = result.metadata.document_id or 'unknown'
            else:
                key = source or 'embeddings'
            
            if key not in organized:
                organized[key] = []
            organized[key].append(result)
        
        return organized
    
    def _save_json(
        self,
        key: str,
        results: List[EmbeddingResult]
    ) -> None:
        """Save results as JSON."""
        output_dir = self.output_dir / key if self.organize_by != 'flat' else self.output_dir
        ensure_directory(output_dir)
        
        output_file = output_dir / f"{key}_embeddings.json"
        
        data = {
            'source': key,
            'provider': self.active_provider,
            'model': self.embedder.model_name,
            'dimension': self.embedder.get_dimension(),
            'count': len(results),
            'created_at': datetime.now().isoformat(),
            'embeddings': []
        }
        
        for result in results:
            data['embeddings'].append({
                'chunk_id': result.chunk_id,
                'embedding': result.embedding,
                'metadata': result.metadata.to_dict() if result.metadata else None
            })
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved {len(results)} embeddings to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON: {e}")
    
    def _save_numpy(
        self,
        key: str,
        results: List[EmbeddingResult]
    ) -> None:
        """Save embeddings as numpy array."""
        try:
            import numpy as np
            
            output_dir = self.output_dir / key if self.organize_by != 'flat' else self.output_dir
            ensure_directory(output_dir)
            
            output_file = output_dir / f"{key}_embeddings.npy"
            
            embeddings = [r.embedding for r in results if r.embedding]
            embeddings_array = np.array(embeddings)
            
            np.save(output_file, embeddings_array)
            
            self.logger.info(f"Saved numpy array to {output_file}")
            
        except ImportError:
            self.logger.warning("numpy not available, skipping numpy save")
        except Exception as e:
            self.logger.error(f"Failed to save numpy: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        stats['cache_stats'] = self.cache.get_stats()
        stats['validation_stats'] = self.validator.get_stats()
        stats['provider_info'] = self.embedder.get_provider_info() if self.embedder else {}
        return stats
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.embedder:
            self.embedder.cleanup()

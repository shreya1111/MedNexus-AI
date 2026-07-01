"""
Index builder for MedNexus-AI ChromaDB.

Manages indexing of embeddings into ChromaDB with incremental updates.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from vector_db.collection_manager import CollectionManager
from utils.logger import get_logger
from utils.hash_utils import compute_string_hash


class IndexBuilder:
    """Builds and maintains ChromaDB indexes."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        embeddings_dir: Path,
        collection_manager: CollectionManager
    ):
        """
        Initialize index builder.
        
        Args:
            config: Retrieval configuration
            embeddings_dir: Directory containing embeddings
            collection_manager: Collection manager instance
        """
        self.config = config
        self.embeddings_dir = Path(embeddings_dir)
        self.collection_manager = collection_manager
        self.logger = get_logger(__name__)
        
        # Indexing configuration
        index_config = config.get('indexing', {})
        self.mode = index_config.get('mode', 'incremental')
        self.batch_size = index_config.get('batch_size', 100)
        self.parallel_workers = index_config.get('parallel_workers', 4)
        self.resume_enabled = index_config.get('resume_enabled', True)
        self.skip_unchanged = index_config.get('skip_unchanged', True)
        self.validate_checksums = index_config.get('validate_checksums', True)
        
        # Checkpoint
        self.checkpoint_enabled = index_config.get('checkpoint_enabled', True)
        self.checkpoint_interval = index_config.get('checkpoint_interval', 1000)
        self.checkpoint_file = Path(index_config.get('checkpoint_file', 'storage/chroma_db/.checkpoint.json'))
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'indexed': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }
    
    def build_index(
        self,
        source: Optional[str] = None,
        force: bool = False,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Build or update index.
        
        Args:
            source: Filter by source
            force: Force full reindex
            show_progress: Show progress bar
            
        Returns:
            Statistics dictionary
        """
        self.stats['start_time'] = datetime.now().isoformat()
        start = time.time()
        
        self.logger.info(f"Starting index build (mode: {self.mode})")
        
        # Get or create collection
        collection = self.collection_manager.get_or_create_collection()
        
        # Load embeddings
        embeddings_data = self._load_embeddings(source)
        
        if not embeddings_data:
            self.logger.warning("No embeddings found to index")
            return self.stats
        
        self.logger.info(f"Found {len(embeddings_data)} embeddings to process")
        
        # Filter if incremental and not force
        if self.mode == 'incremental' and not force and self.skip_unchanged:
            embeddings_data = self._filter_unchanged(collection, embeddings_data)
            self.logger.info(f"After filtering: {len(embeddings_data)} embeddings to index")
        
        self.stats['total_processed'] = len(embeddings_data)
        
        # Index in batches
        self._index_batches(collection, embeddings_data, show_progress)
        
        # Update statistics
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['duration_seconds'] = time.time() - start
        
        self.logger.info(
            f"Indexing complete. Indexed: {self.stats['indexed']}, "
            f"Skipped: {self.stats['skipped']}, Failed: {self.stats['failed']}"
        )
        
        return self.stats
    
    def _load_embeddings(self, source: Optional[str]) -> List[Dict[str, Any]]:
        """Load embeddings from JSON files."""
        embeddings_data = []
        
        # Find embedding files
        if source:
            source_dir = self.embeddings_dir / source
            if not source_dir.exists():
                self.logger.warning(f"Source directory not found: {source_dir}")
                return embeddings_data
            embedding_files = list(source_dir.glob('*_embeddings.json'))
        else:
            embedding_files = list(self.embeddings_dir.rglob('*_embeddings.json'))
        
        self.logger.info(f"Found {len(embedding_files)} embedding files")
        
        # Load embeddings
        for emb_file in embedding_files:
            try:
                with open(emb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_embeddings = data.get('embeddings', [])
                embeddings_data.extend(file_embeddings)
                
            except Exception as e:
                self.logger.error(f"Error loading {emb_file}: {e}")
        
        return embeddings_data
    
    def _filter_unchanged(
        self,
        collection: Any,
        embeddings_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter out unchanged embeddings."""
        if not embeddings_data:
            return []
        
        # Get existing IDs
        try:
            existing = collection.get(include=[])
            existing_ids = set(existing['ids']) if existing and 'ids' in existing else set()
        except:
            existing_ids = set()
        
        # Filter
        filtered = []
        for emb_data in embeddings_data:
            chunk_id = emb_data.get('chunk_id', '')
            
            if chunk_id not in existing_ids:
                filtered.append(emb_data)
            else:
                self.stats['skipped'] += 1
        
        return filtered
    
    def _index_batches(
        self,
        collection: Any,
        embeddings_data: List[Dict[str, Any]],
        show_progress: bool
    ) -> None:
        """Index embeddings in batches."""
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(total=len(embeddings_data), desc="Indexing")
        
        for i in range(0, len(embeddings_data), self.batch_size):
            batch = embeddings_data[i:i + self.batch_size]
            
            try:
                self._index_batch(collection, batch)
                self.stats['indexed'] += len(batch)
            except Exception as e:
                self.logger.error(f"Failed to index batch: {e}")
                self.stats['failed'] += len(batch)
            
            if progress_bar:
                progress_bar.update(len(batch))
            
            # Checkpoint
            if self.checkpoint_enabled and (i + self.batch_size) % self.checkpoint_interval == 0:
                self._save_checkpoint(i + self.batch_size)
        
        if progress_bar:
            progress_bar.close()
    
    def _index_batch(
        self,
        collection: Any,
        batch: List[Dict[str, Any]]
    ) -> None:
        """Index a single batch."""
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for emb_data in batch:
            chunk_id = emb_data.get('chunk_id', '')
            embedding = emb_data.get('embedding', [])
            metadata = emb_data.get('metadata', {})
            
            if not chunk_id or not embedding:
                continue
            
            ids.append(chunk_id)
            embeddings.append(embedding)
            
            # Prepare metadata (ChromaDB only accepts string, int, float, bool)
            clean_metadata = self._clean_metadata(metadata)
            metadatas.append(clean_metadata)
            
            # Use chunk text as document
            documents.append(metadata.get('text', ''))
        
        if ids:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata for ChromaDB compatibility."""
        clean = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            
            # Convert to acceptable types
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            elif isinstance(value, list):
                clean[key] = str(value)
            elif isinstance(value, dict):
                clean[key] = json.dumps(value)
            else:
                clean[key] = str(value)
        
        return clean
    
    def _save_checkpoint(self, position: int) -> None:
        """Save checkpoint."""
        checkpoint = {
            'position': position,
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats
        }
        
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save checkpoint: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        return self.stats.copy()

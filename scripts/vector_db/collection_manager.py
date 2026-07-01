"""
Collection manager for MedNexus-AI ChromaDB.

Manages ChromaDB collections including creation, deletion, and statistics.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.file_utils import ensure_directory


class CollectionManager:
    """Manages ChromaDB collections."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize collection manager.
        
        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # ChromaDB configuration
        chromadb_config = config.get('chromadb', {})
        self.persist_directory = Path(chromadb_config.get('persist_directory', 'storage/chroma_db'))
        self.collection_name = chromadb_config.get('collection_name', 'medical_knowledge')
        self.distance_metric = chromadb_config.get('distance_metric', 'cosine')
        
        # Ensure directory exists
        ensure_directory(self.persist_directory)
        
        # Initialize ChromaDB client
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            settings = Settings(
                persist_directory=str(self.persist_directory),
                anonymized_telemetry=False
            )
            
            self.client = chromadb.Client(settings)
            
            self.logger.info(f"Initialized ChromaDB client at {self.persist_directory}")
            
        except ImportError:
            raise RuntimeError(
                "chromadb not installed. Install with: pip install chromadb"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
    
    def create_collection(
        self,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        distance_metric: Optional[str] = None
    ) -> Any:
        """
        Create a new collection.
        
        Args:
            name: Collection name (default from config)
            metadata: Collection metadata
            distance_metric: Distance metric (cosine, l2, ip)
            
        Returns:
            ChromaDB collection object
        """
        name = name or self.collection_name
        distance_metric = distance_metric or self.distance_metric
        
        # Prepare metadata
        if metadata is None:
            metadata = self.config.get('chromadb', {}).get('metadata', {})
        
        metadata['created_at'] = datetime.now().isoformat()
        
        try:
            # Check if collection exists
            existing = self.client.list_collections()
            if any(c.name == name for c in existing):
                self.logger.warning(f"Collection '{name}' already exists")
                self.collection = self.client.get_collection(name=name)
                return self.collection
            
            # Create collection
            self.collection = self.client.create_collection(
                name=name,
                metadata=metadata,
                embedding_function=None  # We provide embeddings directly
            )
            
            self.logger.info(f"Created collection '{name}' with {distance_metric} metric")
            
            return self.collection
            
        except Exception as e:
            self.logger.error(f"Failed to create collection: {e}")
            raise
    
    def get_collection(self, name: Optional[str] = None) -> Any:
        """
        Get existing collection.
        
        Args:
            name: Collection name
            
        Returns:
            ChromaDB collection object
        """
        name = name or self.collection_name
        
        try:
            self.collection = self.client.get_collection(name=name)
            self.logger.info(f"Retrieved collection '{name}'")
            return self.collection
            
        except Exception as e:
            self.logger.error(f"Collection '{name}' not found: {e}")
            raise
    
    def delete_collection(self, name: Optional[str] = None) -> bool:
        """
        Delete a collection.
        
        Args:
            name: Collection name
            
        Returns:
            True if deleted successfully
        """
        name = name or self.collection_name
        
        try:
            self.client.delete_collection(name=name)
            self.logger.info(f"Deleted collection '{name}'")
            
            if self.collection and self.collection.name == name:
                self.collection = None
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete collection: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all collections.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            names = [c.name for c in collections]
            
            self.logger.info(f"Found {len(names)} collections")
            
            return names
            
        except Exception as e:
            self.logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection_stats(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Args:
            name: Collection name
            
        Returns:
            Dictionary containing statistics
        """
        collection = self.collection
        if name:
            collection = self.get_collection(name)
        
        if not collection:
            return {}
        
        try:
            count = collection.count()
            metadata = collection.metadata
            
            stats = {
                'name': collection.name,
                'count': count,
                'metadata': metadata,
                'persist_directory': str(self.persist_directory)
            }
            
            self.logger.info(f"Collection '{collection.name}' has {count} documents")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def validate_collection(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate collection health.
        
        Args:
            name: Collection name
            
        Returns:
            Validation results
        """
        collection = self.collection
        if name:
            try:
                collection = self.get_collection(name)
            except:
                return {
                    'valid': False,
                    'errors': ['Collection not found'],
                    'warnings': []
                }
        
        if not collection:
            return {
                'valid': False,
                'errors': ['No collection loaded'],
                'warnings': []
            }
        
        errors = []
        warnings = []
        
        try:
            # Check count
            count = collection.count()
            if count == 0:
                warnings.append('Collection is empty')
            
            # Check metadata
            metadata = collection.metadata
            if not metadata:
                warnings.append('No metadata found')
            
            # Try to query
            try:
                results = collection.peek(limit=1)
                if not results:
                    warnings.append('No documents found in peek')
            except Exception as e:
                errors.append(f'Failed to peek collection: {e}')
            
        except Exception as e:
            errors.append(f'Validation error: {e}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'count': count if 'count' in locals() else 0
        }
    
    def get_or_create_collection(
        self,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Get existing collection or create if not exists.
        
        Args:
            name: Collection name
            metadata: Collection metadata (for creation)
            
        Returns:
            ChromaDB collection object
        """
        name = name or self.collection_name
        
        try:
            return self.get_collection(name)
        except:
            return self.create_collection(name, metadata)

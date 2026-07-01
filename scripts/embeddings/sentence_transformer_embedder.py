"""
Sentence Transformers embedding provider for MedNexus-AI.

Uses sentence-transformers library for local embedding generation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import warnings

sys.path.append(str(Path(__file__).parent.parent))

from embeddings.base_embedder import BaseEmbedder
from utils.logger import get_logger


class SentenceTransformerEmbedder(BaseEmbedder):
    """Sentence Transformers embedding provider."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Sentence Transformer embedder.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.model = None
        self.device = config.get('device', 'cpu')
        self.normalize = config.get('normalize_embeddings', True)
        self.show_progress = config.get('show_progress_bar', False)
    
    def initialize(self) -> None:
        """Initialize the sentence transformer model."""
        try:
            # Suppress warnings during model loading
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from sentence_transformers import SentenceTransformer
                
                self.logger.info(f"Loading model: {self.model_name}")
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )
                
                # Get actual dimension from model
                self.dimension = self.model.get_sentence_embedding_dimension()
                
                self.logger.info(
                    f"Model loaded successfully. "
                    f"Dimension: {self.dimension}, Device: {self.device}"
                )
                
                self._is_initialized = True
                
        except ImportError:
            raise RuntimeError(
                "sentence-transformers library not installed. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if not self._is_initialized or self.model is None:
            raise RuntimeError("Embedder not initialized. Call initialize() first.")
        
        if not texts:
            return []
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=self.normalize,
                show_progress_bar=self.show_progress,
                convert_to_numpy=True
            )
            
            # Convert to list of lists
            return embeddings.tolist()
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if not self._is_initialized:
            # Return configured dimension before initialization
            return self.config.get('dimension', 384)
        return self.dimension
    
    def get_max_batch_size(self) -> int:
        """Get maximum batch size."""
        return self.config.get('max_batch_size', 32)
    
    def cleanup(self) -> None:
        """Cleanup model resources."""
        if self.model is not None:
            del self.model
            self.model = None
            
            # Clear CUDA cache if using GPU
            if self.device != 'cpu':
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
            
            self.logger.info("Model resources cleaned up")

"""
Gemini embedding provider for MedNexus-AI.

Uses Google's Gemini API for embedding generation.
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

from embeddings.base_embedder import BaseEmbedder
from utils.logger import get_logger


class GeminiEmbedder(BaseEmbedder):
    """Gemini API embedding provider."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini embedder.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.client = None
        self.api_key_env = config.get('api_key_env', 'GEMINI_API_KEY')
        self.task_type = config.get('task_type', 'RETRIEVAL_DOCUMENT')
        self.title_prefix = config.get('title_prefix', 'Medical Document')
        self.rate_limit_rpm = config.get('rate_limit_rpm', 1500)
        self.retry_delay = config.get('retry_delay', 2)
        self._last_request_time = 0
        self._request_count = 0
        self._minute_start = time.time()
    
    def initialize(self) -> None:
        """Initialize the Gemini API client."""
        try:
            import google.generativeai as genai
            
            # Get API key from environment
            api_key = os.getenv(self.api_key_env)
            if not api_key:
                raise ValueError(
                    f"API key not found. Set {self.api_key_env} environment variable."
                )
            
            # Configure API
            genai.configure(api_key=api_key)
            
            self.logger.info(f"Gemini API configured. Model: {self.model_name}")
            self._is_initialized = True
            
        except ImportError:
            raise RuntimeError(
                "google-generativeai library not installed. "
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini API: {e}")
    
    def _rate_limit(self) -> None:
        """Apply rate limiting."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._minute_start >= 60:
            self._request_count = 0
            self._minute_start = current_time
        
        # Check if we've hit the rate limit
        if self._request_count >= self.rate_limit_rpm:
            sleep_time = 60 - (current_time - self._minute_start)
            if sleep_time > 0:
                self.logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self._request_count = 0
                self._minute_start = time.time()
        
        # Increment request count
        self._request_count += 1
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if not self._is_initialized:
            raise RuntimeError("Embedder not initialized. Call initialize() first.")
        
        if not texts:
            return []
        
        try:
            import google.generativeai as genai
            
            embeddings = []
            
            for text in texts:
                # Apply rate limiting
                self._rate_limit()
                
                # Generate embedding
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type=self.task_type,
                    title=f"{self.title_prefix}: {text[:50]}..."
                )
                
                embeddings.append(result['embedding'])
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Gemini embedding generation failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.config.get('dimension', 768)
    
    def get_max_batch_size(self) -> int:
        """Get maximum batch size."""
        # Gemini processes one at a time due to API structure
        return 1
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for Gemini.
        
        Gemini uses approximately 1 token per 4 characters for English.
        """
        return len(text) // 4

"""
Provider factory for creating embedding providers.

Uses the Factory pattern to instantiate the correct provider based on configuration.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

from embeddings.base_embedder import BaseEmbedder
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from embeddings.gemini_embedder import GeminiEmbedder
from utils.logger import get_logger


class ProviderFactory:
    """Factory for creating embedding providers."""
    
    # Registry of available providers
    _providers = {
        'sentence-transformers': SentenceTransformerEmbedder,
        'sentence_transformers': SentenceTransformerEmbedder,
        'st': SentenceTransformerEmbedder,
        'gemini': GeminiEmbedder,
        'google': GeminiEmbedder,
    }
    
    @classmethod
    def create_embedder(
        cls,
        provider_name: str,
        config: Dict[str, Any]
    ) -> BaseEmbedder:
        """
        Create an embedding provider instance.
        
        Args:
            provider_name: Name of the provider (e.g., 'gemini', 'sentence-transformers')
            config: Provider-specific configuration
            
        Returns:
            Initialized BaseEmbedder instance
            
        Raises:
            ValueError: If provider not found
        """
        logger = get_logger(__name__)
        
        # Normalize provider name
        provider_key = provider_name.lower().strip()
        
        if provider_key not in cls._providers:
            available = ', '.join(set(cls._providers.keys()))
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {available}"
            )
        
        provider_class = cls._providers[provider_key]
        logger.info(f"Creating {provider_class.__name__} provider")
        
        return provider_class(config)
    
    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: type
    ) -> None:
        """
        Register a new provider.
        
        This allows custom providers to be added at runtime.
        
        Args:
            name: Provider name
            provider_class: Provider class (must inherit from BaseEmbedder)
        """
        if not issubclass(provider_class, BaseEmbedder):
            raise TypeError(
                f"Provider class must inherit from BaseEmbedder, "
                f"got {provider_class.__name__}"
            )
        
        cls._providers[name.lower()] = provider_class
        
        logger = get_logger(__name__)
        logger.info(f"Registered provider: {name}")
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List all available providers.
        
        Returns:
            List of provider names
        """
        # Return unique provider names
        return sorted(set(cls._providers.keys()))
    
    @classmethod
    def get_provider_info(cls, provider_name: str) -> Dict[str, Any]:
        """
        Get information about a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary containing provider information
        """
        provider_key = provider_name.lower().strip()
        
        if provider_key not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_class = cls._providers[provider_key]
        
        return {
            'name': provider_name,
            'class': provider_class.__name__,
            'module': provider_class.__module__,
        }

"""
Embedding generation module for MedNexus-AI.

This module provides provider-agnostic embedding generation with support
for multiple providers, caching, validation, and benchmarking.
"""

from .base_embedder import BaseEmbedder, EmbeddingResult, EmbeddingMetadata
from .provider_factory import ProviderFactory
from .embedding_manager import EmbeddingManager

__all__ = [
    'BaseEmbedder',
    'EmbeddingResult',
    'EmbeddingMetadata',
    'ProviderFactory',
    'EmbeddingManager',
]

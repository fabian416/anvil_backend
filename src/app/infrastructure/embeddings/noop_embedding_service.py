"""
Noop Embedding Service

A no-operation embedding service that returns empty/zero vectors.
Used when DEEPINFRA_API_KEY is not configured, allowing the system
to function without GraphRAG features.
"""

from typing import List
import logging

from app.domain.ports.embeddings import EmbeddingResult

logger = logging.getLogger(__name__)


class NoopEmbeddingService:
    """
    No-operation embedding service.
    
    Returns zero vectors for all embedding requests.
    This allows the system to start and function without GraphRAG
    features when the embedding API key is not configured.
    """
    
    # Default dimensions (matching BAAI/bge-m3 model dimensions)
    DEFAULT_DIMENSIONS = 1024
    
    def __init__(self, dimensions: int = DEFAULT_DIMENSIONS):
        """
        Initialize noop embedding service.
        
        Args:
            dimensions: Number of dimensions for zero vectors (default: 1024)
        """
        self._dimensions = dimensions
        logger.info(
            f"NoopEmbeddingService initialized. GraphRAG search features disabled. "
            f"Set DEEPINFRA_API_KEY to enable protocol search."
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Return a zero vector.
        
        Args:
            text: Input text (ignored)
            
        Returns:
            Zero vector of configured dimensions
        """
        return [0.0] * self._dimensions
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Return zero vectors for batch.
        
        Args:
            texts: List of input texts (ignored)
            
        Returns:
            List of zero vectors
        """
        return [[0.0] * self._dimensions for _ in texts]
    
    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """
        Return zero embedding with metadata.
        
        Args:
            text: Input text
            
        Returns:
            EmbeddingResult with zero vector
        """
        return EmbeddingResult(
            text=text,
            embedding=[0.0] * self._dimensions,
            model="noop",
            dimensions=self._dimensions,
        )
    
    def get_dimensions(self) -> int:
        """
        Get embedding dimensions.
        
        Returns:
            Number of dimensions in embeddings
        """
        return self._dimensions


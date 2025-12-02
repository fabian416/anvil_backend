"""
Embedding Service Port

Interface for generating embeddings from text.
"""

from typing import Protocol, List
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    text: str
    embedding: List[float]
    model: str
    dimensions: int


class EmbeddingService(Protocol):
    """
    Port for embedding generation.
    
    Implementations can use:
    - OpenAI embeddings
    - Sentence Transformers
    - Custom models
    """
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        ...
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        ...
    
    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """
        Generate embedding with metadata.
        
        Args:
            text: Input text
            
        Returns:
            EmbeddingResult with vector and metadata
        """
        ...
    
    def get_dimensions(self) -> int:
        """
        Get embedding dimensions.
        
        Returns:
            Number of dimensions in embeddings
        """
        ...

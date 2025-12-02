"""Embedding service port."""
from typing import List, Protocol


class EmbeddingService(Protocol):
    """Service for generating text embeddings."""
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        ...
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        ...

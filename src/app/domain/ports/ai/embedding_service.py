"""
Embedding Service Port.

Interface for generating text embeddings from various providers.
Supports batch processing, caching, and cost tracking.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Protocol


class EmbeddingInputType(Enum):
    """Type of input text for embedding."""

    SEARCH_DOCUMENT = "search_document"  # Text to be indexed/searched
    SEARCH_QUERY = "search_query"  # Query text for searching
    CLASSIFICATION = "classification"  # Text for classification
    CLUSTERING = "clustering"  # Text for clustering


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    text: str
    embedding: List[float]
    model: str
    dimensions: int
    provider: str
    input_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class BatchEmbeddingResult:
    """Result of batch embedding generation."""

    embeddings: List[List[float]]
    texts: List[str]
    model: str
    dimensions: int
    provider: str
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def __len__(self) -> int:
        """Return number of embeddings."""
        return len(self.embeddings)


class EmbeddingService(Protocol):
    """
    Port for embedding generation.

    Implementations:
    - OpenAI (text-embedding-3-large, text-embedding-3-small)
    - Cohere (embed-english-v3.0, embed-multilingual-v3.0)
    - Sentence Transformers (local models)
    - Custom models

    Features:
    - Single and batch embedding generation
    - Automatic batching for large text sets
    - Cost tracking and token counting
    - Caching for frequently embedded texts
    - Input type specification for optimized embeddings
    """

    async def embed_text(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text
            input_type: Type of input (for providers that support it)

        Returns:
            Embedding vector
        """
        ...

    async def embed_texts(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).

        Automatically handles batching for providers with batch size limits.

        Args:
            texts: List of input texts
            input_type: Type of input (for providers that support it)

        Returns:
            List of embedding vectors
        """
        ...

    async def embed_with_metadata(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> EmbeddingResult:
        """
        Generate embedding with metadata (tokens, cost, etc.).

        Args:
            text: Input text
            input_type: Type of input

        Returns:
            EmbeddingResult with vector and metadata
        """
        ...

    async def embed_batch_with_metadata(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> BatchEmbeddingResult:
        """
        Generate batch embeddings with metadata.

        Args:
            texts: List of input texts
            input_type: Type of input

        Returns:
            BatchEmbeddingResult with vectors and metadata
        """
        ...

    def get_dimensions(self) -> int:
        """
        Get embedding dimensions for this service.

        Returns:
            Number of dimensions in embeddings
        """
        ...

    def get_max_batch_size(self) -> int:
        """
        Get maximum batch size for this service.

        Returns:
            Maximum number of texts that can be embedded in one call
        """
        ...

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            Provider identifier (e.g., "openai", "cohere")
        """
        ...

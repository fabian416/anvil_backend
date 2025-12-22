"""
Cohere Embedding Adapter.

Implements embedding service using Cohere's embed models.

Supported Models:
- embed-english-v3.0 (1024 dimensions, optimized for English)
- embed-multilingual-v3.0 (1024 dimensions, 100+ languages)
- embed-english-light-v3.0 (384 dimensions, faster/cheaper)
- embed-multilingual-light-v3.0 (384 dimensions, faster/cheaper)

Features:
- Input type specification (search_document, search_query, classification, clustering)
- Batch processing (up to 96 texts per request)
- Automatic batching for large datasets
- Cost tracking and token counting
- Retry logic with exponential backoff
- Rate limit handling
- Compression levels for better performance

Pricing (as of 2024):
- embed-v3.0 models: $0.10 per 1M tokens
- embed-light-v3.0 models: $0.10 per 1M tokens
"""

import asyncio
import logging
from typing import List, Optional

import cohere
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.domain.ports.ai.embedding_service import (
    EmbeddingInputType,
    EmbeddingResult,
    BatchEmbeddingResult,
)

logger = logging.getLogger(__name__)


class CohereEmbeddingAdapter:
    """
    Cohere embedding service adapter.

    Usage:
        >>> adapter = CohereEmbeddingAdapter(
        ...     api_key="...",
        ...     model="embed-english-v3.0",
        ... )
        >>>
        >>> # Single embedding
        >>> embedding = await adapter.embed_text(
        ...     "Hello world",
        ...     input_type=EmbeddingInputType.SEARCH_DOCUMENT,
        ... )
        >>>
        >>> # Batch embeddings
        >>> embeddings = await adapter.embed_texts(
        ...     ["First document", "Second document"],
        ...     input_type=EmbeddingInputType.SEARCH_DOCUMENT,
        ... )
        >>>
        >>> # With metadata
        >>> result = await adapter.embed_with_metadata(
        ...     "Search query text",
        ...     input_type=EmbeddingInputType.SEARCH_QUERY,
        ... )
    """

    # Model configurations
    MODEL_CONFIGS = {
        "embed-english-v3.0": {
            "dimensions": 1024,
            "cost_per_1m_tokens": 0.10,
            "supports_input_type": True,
        },
        "embed-multilingual-v3.0": {
            "dimensions": 1024,
            "cost_per_1m_tokens": 0.10,
            "supports_input_type": True,
        },
        "embed-english-light-v3.0": {
            "dimensions": 384,
            "cost_per_1m_tokens": 0.10,
            "supports_input_type": True,
        },
        "embed-multilingual-light-v3.0": {
            "dimensions": 384,
            "cost_per_1m_tokens": 0.10,
            "supports_input_type": True,
        },
        # Legacy models
        "embed-english-v2.0": {
            "dimensions": 4096,
            "cost_per_1m_tokens": 0.10,
            "supports_input_type": False,
        },
        "embed-multilingual-v2.0": {
            "dimensions": 768,
            "cost_per_1m_tokens": 0.10,
            "supports_input_type": False,
        },
    }

    # Cohere limits
    MAX_BATCH_SIZE = 96  # Max texts per request
    MAX_TEXT_LENGTH = 512  # Max tokens per text (approximate)

    # Input type mapping
    INPUT_TYPE_MAP = {
        EmbeddingInputType.SEARCH_DOCUMENT: "search_document",
        EmbeddingInputType.SEARCH_QUERY: "search_query",
        EmbeddingInputType.CLASSIFICATION: "classification",
        EmbeddingInputType.CLUSTERING: "clustering",
    }

    def __init__(
        self,
        api_key: str,
        model: str = "embed-english-v3.0",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize Cohere embedding adapter.

        Args:
            api_key: Cohere API key
            model: Model name (default: embed-english-v3.0)
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        if model not in self.MODEL_CONFIGS:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported: {list(self.MODEL_CONFIGS.keys())}"
            )

        self._client = cohere.AsyncClient(
            api_key=api_key,
            timeout=timeout,
        )
        self._model = model
        self._max_retries = max_retries

        # Get model config
        model_config = self.MODEL_CONFIGS[model]
        self._dimensions = model_config["dimensions"]
        self._supports_input_type = model_config["supports_input_type"]
        self._cost_per_token = model_config["cost_per_1m_tokens"] / 1_000_000

        logger.info(
            f"Cohere embedding adapter initialized: model={model}, "
            f"dimensions={self._dimensions}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def _create_embeddings(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> cohere.EmbedResponse:
        """
        Call Cohere API to create embeddings.

        Args:
            texts: List of texts to embed
            input_type: Type of input for optimized embeddings

        Returns:
            Cohere API response
        """
        # Build request parameters
        params = {
            "texts": texts,
            "model": self._model,
        }

        # Add input type if supported and provided
        if self._supports_input_type and input_type is not None:
            cohere_input_type = self.INPUT_TYPE_MAP.get(input_type)
            if cohere_input_type:
                params["input_type"] = cohere_input_type
            else:
                logger.warning(f"Unknown input type: {input_type}, using default")

        # Call API
        try:
            response = await self._client.embed(**params)
            return response
        except Exception as e:
            logger.error(f"Cohere embedding API error: {e}")
            raise

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses rough approximation: 1 token ≈ 4 characters.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough approximation (actual tokenization is more complex)
        return len(text) // 4

    def _calculate_tokens(self, texts: List[str]) -> int:
        """
        Calculate total tokens for texts.

        Args:
            texts: List of texts

        Returns:
            Total estimated tokens
        """
        return sum(self._estimate_tokens(text) for text in texts)

    def _calculate_cost(self, tokens: int) -> float:
        """
        Calculate cost for token count.

        Args:
            tokens: Number of tokens

        Returns:
            Cost in USD
        """
        return tokens * self._cost_per_token

    async def embed_text(
        self,
        text: str,
        input_type: Optional[EmbeddingInputType] = None,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text
            input_type: Type of input (search_document, search_query, etc.)

        Returns:
            Embedding vector
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        response = await self._create_embeddings([text], input_type)

        # Extract embedding
        embedding = response.embeddings[0]
        return embedding

    async def embed_texts(
        self,
        texts: List[str],
        input_type: Optional[EmbeddingInputType] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).

        Automatically handles batching if texts exceed MAX_BATCH_SIZE.

        Args:
            texts: List of input texts
            input_type: Type of input

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts
        non_empty_texts = [t for t in texts if t.strip()]
        if not non_empty_texts:
            raise ValueError("All texts are empty")

        # Handle batching if needed
        if len(non_empty_texts) <= self.MAX_BATCH_SIZE:
            # Single batch
            response = await self._create_embeddings(non_empty_texts, input_type)
            return response.embeddings

        # Multiple batches
        all_embeddings = []
        for i in range(0, len(non_empty_texts), self.MAX_BATCH_SIZE):
            batch = non_empty_texts[i : i + self.MAX_BATCH_SIZE]
            response = await self._create_embeddings(batch, input_type)
            all_embeddings.extend(response.embeddings)

            # Small delay between batches to avoid rate limits
            if i + self.MAX_BATCH_SIZE < len(non_empty_texts):
                await asyncio.sleep(0.2)

        return all_embeddings

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
        if not text.strip():
            raise ValueError("Text cannot be empty")

        response = await self._create_embeddings([text], input_type)

        # Extract data
        embedding = response.embeddings[0]

        # Calculate tokens and cost (Cohere doesn't return token count)
        tokens = self._estimate_tokens(text)
        cost = self._calculate_cost(tokens)

        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self._model,
            dimensions=self._dimensions,
            provider="cohere",
            input_tokens=tokens,
            cost_usd=cost,
        )

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
        if not texts:
            return BatchEmbeddingResult(
                embeddings=[],
                texts=[],
                model=self._model,
                dimensions=self._dimensions,
                provider="cohere",
                total_tokens=0,
                total_cost_usd=0.0,
            )

        # Filter out empty texts
        non_empty_texts = [t for t in texts if t.strip()]
        if not non_empty_texts:
            raise ValueError("All texts are empty")

        # Handle batching if needed
        all_embeddings = []

        if len(non_empty_texts) <= self.MAX_BATCH_SIZE:
            # Single batch
            response = await self._create_embeddings(non_empty_texts, input_type)
            all_embeddings = response.embeddings
        else:
            # Multiple batches
            for i in range(0, len(non_empty_texts), self.MAX_BATCH_SIZE):
                batch = non_empty_texts[i : i + self.MAX_BATCH_SIZE]
                response = await self._create_embeddings(batch, input_type)
                all_embeddings.extend(response.embeddings)

                # Small delay between batches
                if i + self.MAX_BATCH_SIZE < len(non_empty_texts):
                    await asyncio.sleep(0.2)

        # Calculate tokens and cost
        total_tokens = self._calculate_tokens(non_empty_texts)
        cost = self._calculate_cost(total_tokens)

        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            texts=non_empty_texts,
            model=self._model,
            dimensions=self._dimensions,
            provider="cohere",
            total_tokens=total_tokens,
            total_cost_usd=cost,
        )

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    def get_max_batch_size(self) -> int:
        """Get maximum batch size."""
        return self.MAX_BATCH_SIZE

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "cohere"

    async def close(self) -> None:
        """Close the client connection."""
        await self._client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Factory function
def create_cohere_embedding_service(
    api_key: str,
    model: str = "embed-english-v3.0",
    **kwargs,
) -> CohereEmbeddingAdapter:
    """
    Factory function to create Cohere embedding service.

    Args:
        api_key: Cohere API key
        model: Model name
        **kwargs: Additional arguments for adapter

    Returns:
        CohereEmbeddingAdapter instance
    """
    return CohereEmbeddingAdapter(
        api_key=api_key,
        model=model,
        **kwargs,
    )

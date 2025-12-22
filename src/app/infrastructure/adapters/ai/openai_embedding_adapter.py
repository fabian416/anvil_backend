"""
OpenAI Embedding Adapter.

Implements embedding service using OpenAI's text-embedding models.

Supported Models:
- text-embedding-3-large (3072 dimensions, best quality)
- text-embedding-3-small (1536 dimensions, faster/cheaper)
- text-embedding-ada-002 (1536 dimensions, legacy)

Features:
- Batch processing (up to 2048 texts per request)
- Automatic batching for large datasets
- Cost tracking and token counting
- Configurable dimensions (for v3 models)
- Retry logic with exponential backoff
- Rate limit handling

Pricing (as of 2024):
- text-embedding-3-large: $0.13 per 1M tokens
- text-embedding-3-small: $0.02 per 1M tokens
- text-embedding-ada-002: $0.10 per 1M tokens
"""

import asyncio
import logging
from typing import List, Optional

from openai import AsyncOpenAI
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


class OpenAIEmbeddingAdapter:
    """
    OpenAI embedding service adapter.

    Usage:
        >>> adapter = OpenAIEmbeddingAdapter(
        ...     api_key="sk-...",
        ...     model="text-embedding-3-large",
        ...     dimensions=1536,  # Optional dimension reduction
        ... )
        >>>
        >>> # Single embedding
        >>> embedding = await adapter.embed_text("Hello world")
        >>>
        >>> # Batch embeddings
        >>> embeddings = await adapter.embed_texts([
        ...     "First document",
        ...     "Second document",
        ...     "Third document",
        ... ])
        >>>
        >>> # With metadata
        >>> result = await adapter.embed_with_metadata("Hello world")
        >>> print(f"Cost: ${result.cost_usd:.6f}, Tokens: {result.input_tokens}")
    """

    # Model configurations
    MODEL_CONFIGS = {
        "text-embedding-3-large": {
            "default_dimensions": 3072,
            "max_dimensions": 3072,
            "cost_per_1m_tokens": 0.13,
            "supports_shortening": True,
        },
        "text-embedding-3-small": {
            "default_dimensions": 1536,
            "max_dimensions": 1536,
            "cost_per_1m_tokens": 0.02,
            "supports_shortening": True,
        },
        "text-embedding-ada-002": {
            "default_dimensions": 1536,
            "max_dimensions": 1536,
            "cost_per_1m_tokens": 0.10,
            "supports_shortening": False,
        },
    }

    # OpenAI limits
    MAX_BATCH_SIZE = 2048  # Max texts per request
    MAX_TOKENS_PER_REQUEST = 8191  # Max tokens per text

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimensions: Optional[int] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        organization: Optional[str] = None,
    ):
        """
        Initialize OpenAI embedding adapter.

        Args:
            api_key: OpenAI API key
            model: Model name (default: text-embedding-3-large)
            dimensions: Optional dimension reduction (for v3 models)
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds
            organization: Optional OpenAI organization ID
        """
        if model not in self.MODEL_CONFIGS:
            raise ValueError(
                f"Unsupported model: {model}. "
                f"Supported: {list(self.MODEL_CONFIGS.keys())}"
            )

        self._client = AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._model = model
        self._max_retries = max_retries

        # Get model config
        model_config = self.MODEL_CONFIGS[model]

        # Validate and set dimensions
        if dimensions is not None:
            if not model_config["supports_shortening"]:
                raise ValueError(
                    f"Model {model} does not support dimension reduction"
                )
            if dimensions > model_config["max_dimensions"]:
                raise ValueError(
                    f"Dimensions {dimensions} exceeds max {model_config['max_dimensions']} for {model}"
                )
            self._dimensions = dimensions
        else:
            self._dimensions = model_config["default_dimensions"]

        self._cost_per_token = model_config["cost_per_1m_tokens"] / 1_000_000

        logger.info(
            f"OpenAI embedding adapter initialized: model={model}, "
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
    ) -> dict:
        """
        Call OpenAI API to create embeddings.

        Args:
            texts: List of texts to embed
            input_type: Input type (not used by OpenAI, kept for interface compatibility)

        Returns:
            API response dictionary
        """
        # Build request parameters
        params = {
            "model": self._model,
            "input": texts,
        }

        # Add dimensions parameter for v3 models if specified
        model_config = self.MODEL_CONFIGS[self._model]
        if (
            model_config["supports_shortening"]
            and self._dimensions != model_config["default_dimensions"]
        ):
            params["dimensions"] = self._dimensions

        # Call API
        try:
            response = await self._client.embeddings.create(**params)
            return response.model_dump()
        except Exception as e:
            logger.error(f"OpenAI embedding API error: {e}")
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
            input_type: Input type (not used by OpenAI)

        Returns:
            Embedding vector
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        response = await self._create_embeddings([text], input_type)

        # Extract embedding
        embedding = response["data"][0]["embedding"]
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
            input_type: Input type (not used by OpenAI)

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
            embeddings = [item["embedding"] for item in response["data"]]
            return embeddings

        # Multiple batches
        all_embeddings = []
        for i in range(0, len(non_empty_texts), self.MAX_BATCH_SIZE):
            batch = non_empty_texts[i : i + self.MAX_BATCH_SIZE]
            response = await self._create_embeddings(batch, input_type)
            batch_embeddings = [item["embedding"] for item in response["data"]]
            all_embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limits
            if i + self.MAX_BATCH_SIZE < len(non_empty_texts):
                await asyncio.sleep(0.1)

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
            input_type: Input type (not used by OpenAI)

        Returns:
            EmbeddingResult with vector and metadata
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        response = await self._create_embeddings([text], input_type)

        # Extract data
        embedding = response["data"][0]["embedding"]
        tokens = response["usage"]["total_tokens"]
        cost = self._calculate_cost(tokens)

        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self._model,
            dimensions=self._dimensions,
            provider="openai",
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
            input_type: Input type (not used by OpenAI)

        Returns:
            BatchEmbeddingResult with vectors and metadata
        """
        if not texts:
            return BatchEmbeddingResult(
                embeddings=[],
                texts=[],
                model=self._model,
                dimensions=self._dimensions,
                provider="openai",
                total_tokens=0,
                total_cost_usd=0.0,
            )

        # Filter out empty texts
        non_empty_texts = [t for t in texts if t.strip()]
        if not non_empty_texts:
            raise ValueError("All texts are empty")

        # Handle batching if needed
        all_embeddings = []
        total_tokens = 0

        if len(non_empty_texts) <= self.MAX_BATCH_SIZE:
            # Single batch
            response = await self._create_embeddings(non_empty_texts, input_type)
            all_embeddings = [item["embedding"] for item in response["data"]]
            total_tokens = response["usage"]["total_tokens"]
        else:
            # Multiple batches
            for i in range(0, len(non_empty_texts), self.MAX_BATCH_SIZE):
                batch = non_empty_texts[i : i + self.MAX_BATCH_SIZE]
                response = await self._create_embeddings(batch, input_type)
                batch_embeddings = [item["embedding"] for item in response["data"]]
                all_embeddings.extend(batch_embeddings)
                total_tokens += response["usage"]["total_tokens"]

                # Small delay between batches
                if i + self.MAX_BATCH_SIZE < len(non_empty_texts):
                    await asyncio.sleep(0.1)

        cost = self._calculate_cost(total_tokens)

        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            texts=non_empty_texts,
            model=self._model,
            dimensions=self._dimensions,
            provider="openai",
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
        return "openai"

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
def create_openai_embedding_service(
    api_key: str,
    model: str = "text-embedding-3-large",
    dimensions: Optional[int] = None,
    **kwargs,
) -> OpenAIEmbeddingAdapter:
    """
    Factory function to create OpenAI embedding service.

    Args:
        api_key: OpenAI API key
        model: Model name
        dimensions: Optional dimension reduction
        **kwargs: Additional arguments for adapter

    Returns:
        OpenAIEmbeddingAdapter instance
    """
    return OpenAIEmbeddingAdapter(
        api_key=api_key,
        model=model,
        dimensions=dimensions,
        **kwargs,
    )

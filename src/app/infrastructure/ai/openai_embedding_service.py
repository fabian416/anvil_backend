"""OpenAI embedding service implementation."""

from typing import List, Optional
import asyncio

from app.domain.ports.embedding_service import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    """
    OpenAI embedding service.

    Uses OpenAI's text-embedding-3-small model.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
    ):
        """
        Initialize OpenAI embedding service.

        Args:
            api_key: OpenAI API key (or None to use env var)
            model: Embedding model name
        """
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )
        return self._client

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-small)
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # OpenAI API has limits on batch size
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self._generate_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a single batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        client = self._get_client()

        # Clean texts (remove empty strings, limit length)
        cleaned_texts = []
        for text in texts:
            text = text.strip()
            if not text:
                text = " "  # OpenAI doesn't accept empty strings
            # Limit to ~8000 tokens (rough estimate: 4 chars = 1 token)
            if len(text) > 32000:
                text = text[:32000]
            cleaned_texts.append(text)

        try:
            response = await client.embeddings.create(
                model=self.model,
                input=cleaned_texts,
            )

            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            # Log error and return zero vectors as fallback
            import logging

            logging.error(f"Failed to generate embeddings: {e}")

            # Return zero vectors (1536 dimensions for text-embedding-3-small)
            dimension = 1536
            return [[0.0] * dimension for _ in texts]

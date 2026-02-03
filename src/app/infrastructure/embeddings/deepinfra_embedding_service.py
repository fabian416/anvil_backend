"""
DeepInfra Embedding Service

Implementation using DeepInfra's OpenAI-compatible API for embeddings.
Uses multilingual models that support multiple languages.
"""

from typing import List
import httpx
import logging

from app.domain.ports.embeddings import EmbeddingService, EmbeddingResult


logger = logging.getLogger(__name__)


class DeepInfraEmbeddingService(EmbeddingService):
    """
    DeepInfra embedding service implementation.

    Uses OpenAI-compatible API with multilingual models.
    Default: BAAI/bge-m3 (1024 dimensions, supports 100+ languages)

    Supported models:
    - BAAI/bge-m3: Multilingual, 1024 dims, best for multi-language
    - BAAI/bge-large-en-v1.5: English-only, 1024 dims, high quality
    - sentence-transformers/all-MiniLM-L6-v2: 384 dims, fast
    - thenlper/gte-large: 1024 dims, good quality
    """

    DEFAULT_BASE_URL = "https://api.deepinfra.com/v1/openai"

    # Multilingual model - supports 100+ languages including EN, ES, PT, ZH, FR
    DEFAULT_MODEL = "BAAI/bge-m3"
    DEFAULT_DIMENSIONS = 1024

    # Model dimension mapping
    MODEL_DIMENSIONS = {
        "BAAI/bge-m3": 1024,
        "BAAI/bge-large-en-v1.5": 1024,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "thenlper/gte-large": 1024,
        "intfloat/multilingual-e5-large-instruct": 1024,
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = 30,
    ):
        """
        Initialize DeepInfra embedding service.

        Args:
            api_key: DeepInfra API key
            base_url: API base URL (default: DeepInfra OpenAI-compatible endpoint)
            model: Model name (default: BAAI/bge-m3 for multilingual)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

        # Get dimensions for the model
        self._dimensions = self.MODEL_DIMENSIONS.get(model, self.DEFAULT_DIMENSIONS)

        logger.info(
            f"DeepInfra Embedding Service initialized: model={model}, dims={self._dimensions}"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text (supports multiple languages)"""

        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self._dimensions

        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={
                    "input": text,
                    "model": self.model,
                },
            )
            response.raise_for_status()
            data = response.json()

            embedding = data["data"][0]["embedding"]
            logger.debug(
                f"Generated embedding: {len(embedding)} dims for text: {text[:50]}..."
            )
            return embedding

        except httpx.HTTPError as e:
            logger.error(f"DeepInfra embedding error: {e}")
            # Return zero vector on error
            return [0.0] * self._dimensions

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch, multilingual)"""

        if not texts:
            return []

        # Filter empty texts
        filtered_texts = [t if t and t.strip() else "empty" for t in texts]

        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={
                    "input": filtered_texts,
                    "model": self.model,
                },
            )
            response.raise_for_status()
            data = response.json()

            # Sort by index to maintain order
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            result = [item["embedding"] for item in embeddings]

            logger.debug(f"Generated {len(result)} embeddings in batch")
            return result

        except httpx.HTTPError as e:
            logger.error(f"DeepInfra batch embedding error: {e}")
            # Return zero vectors on error
            return [[0.0] * self._dimensions for _ in texts]

    async def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """Generate embedding with metadata"""

        embedding = await self.embed_text(text)

        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self.model,
            dimensions=len(embedding),
        )

    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self._dimensions

"""
OpenAI Embedding Service

Implementation using OpenAI's text-embedding models.
"""

from typing import List
import httpx
import logging

from app.domain.ports.embeddings import EmbeddingService, EmbeddingResult


logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(EmbeddingService):
    """
    OpenAI embedding service implementation.
    
    Uses OpenAI's text-embedding-3-small model (1536 dimensions).
    """
    
    API_URL = "https://api.openai.com/v1/embeddings"
    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    
    def __init__(
        self,
        api_key: str,
        model: str = MODEL,
        timeout: int = 30,
    ):
        """
        Initialize OpenAI embedding service.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: text-embedding-3-small)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
    
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
        """Generate embedding for a single text"""
        
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.DIMENSIONS
        
        client = await self._get_client()
        
        try:
            response = await client.post(
                self.API_URL,
                json={
                    "input": text,
                    "model": self.model,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return data["data"][0]["embedding"]
            
        except httpx.HTTPError as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Return zero vector on error
            return [0.0] * self.DIMENSIONS
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch)"""
        
        if not texts:
            return []
        
        # Filter empty texts
        filtered_texts = [t if t and t.strip() else "empty" for t in texts]
        
        client = await self._get_client()
        
        try:
            response = await client.post(
                self.API_URL,
                json={
                    "input": filtered_texts,
                    "model": self.model,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            # Sort by index to maintain order
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings]
            
        except httpx.HTTPError as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            # Return zero vectors on error
            return [[0.0] * self.DIMENSIONS for _ in texts]
    
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
        return self.DIMENSIONS

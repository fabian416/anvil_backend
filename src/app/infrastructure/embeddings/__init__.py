"""Embedding implementations"""

# OpenAI removed - using only DeepInfra for embeddings
# from .openai_embedding_service import OpenAIEmbeddingService
from .deepinfra_embedding_service import DeepInfraEmbeddingService
from .noop_embedding_service import NoopEmbeddingService

__all__ = ["DeepInfraEmbeddingService", "NoopEmbeddingService"]

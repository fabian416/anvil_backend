"""Embedding implementations"""

# OpenAI removed - using only DeepInfra for embeddings
# from .openai_embedding_service import OpenAIEmbeddingService
from .deepinfra_embedding_service import DeepInfraEmbeddingService

__all__ = ["DeepInfraEmbeddingService"]  # OpenAIEmbeddingService removed

"""Knowledge retrieval service."""
from typing import List, Tuple
from uuid import UUID

from app.domain.entities.knowledge_base import KnowledgeChunk
from app.domain.ports.embedding_service import EmbeddingService
from app.domain.ports.knowledge_repository import KnowledgeChunkRepository


class KnowledgeRetriever:
    """
    Service for retrieving relevant knowledge chunks.
    
    Implements semantic search with vector similarity.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_repository: KnowledgeChunkRepository,
    ):
        """
        Initialize knowledge retriever.
        
        Args:
            embedding_service: Embedding generation service
            chunk_repository: Chunk storage repository
        """
        self.embedding_service = embedding_service
        self.chunk_repository = chunk_repository
    
    async def retrieve(
        self,
        knowledge_base_id: UUID,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Retrieve relevant knowledge chunks for a query.
        
        Args:
            knowledge_base_id: Knowledge base to search
            query: User query
            limit: Maximum results
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of (chunk, similarity_score) tuples, ordered by relevance
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Search for similar chunks
        results = await self.chunk_repository.search_chunks(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )
        
        return results
    
    async def retrieve_with_reranking(
        self,
        knowledge_base_id: UUID,
        query: str,
        initial_limit: int = 20,
        final_limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Retrieve with two-stage ranking (vector search + reranking).
        
        This is a placeholder for future implementation with cross-encoder.
        
        Args:
            knowledge_base_id: Knowledge base to search
            query: User query
            initial_limit: Initial results from vector search
            final_limit: Final results after reranking
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of (chunk, similarity_score) tuples, ordered by relevance
        """
        # Stage 1: Vector search (broad recall)
        initial_results = await self.retrieve(
            knowledge_base_id=knowledge_base_id,
            query=query,
            limit=initial_limit,
            similarity_threshold=similarity_threshold,
        )
        
        # Stage 2: Reranking (precision)
        # TODO: Implement cross-encoder reranking
        # For now, just return top N from vector search
        reranked = initial_results[:final_limit]
        
        return reranked
    
    def format_context(
        self,
        chunks: List[Tuple[KnowledgeChunk, float]],
        max_context_length: int = 2000,
    ) -> str:
        """
        Format retrieved chunks into context string.
        
        Args:
            chunks: List of (chunk, score) tuples
            max_context_length: Maximum context length in characters
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = []
        total_length = 0
        
        for chunk, score in chunks:
            # Format chunk with metadata
            chunk_text = f"[{chunk.metadata.get('document_title', 'Unknown')}]\n{chunk.chunk_text}"
            chunk_length = len(chunk_text)
            
            # Check if adding this chunk would exceed limit
            if total_length + chunk_length > max_context_length and context_parts:
                break
            
            context_parts.append(chunk_text)
            total_length += chunk_length
        
        return "\n\n---\n\n".join(context_parts)

"""
Vector Repository Port

Interface for storing and querying vector embeddings.
"""

from typing import Protocol, List, Optional
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class VectorDocument:
    """Document with vector embedding"""
    id: UUID
    entity_id: UUID
    entity_type: str
    entity_name: str
    text_content: str
    embedding: List[float]
    model: str
    dimensions: int
    created_at: datetime
    updated_at: datetime


@dataclass
class SimilarityResult:
    """Result of similarity search"""
    document: VectorDocument
    similarity: float


class VectorRepository(Protocol):
    """
    Port for vector storage and similarity search.
    
    Implementations:
    - PostgreSQL with pgvector
    - PostgreSQL with array operations
    - Dedicated vector databases (Pinecone, Weaviate, etc.)
    """
    
    async def store_embedding(
        self,
        entity_id: UUID,
        entity_type: str,
        entity_name: str,
        text_content: str,
        embedding: List[float],
        model: str,
    ) -> UUID:
        """
        Store an embedding.
        
        Args:
            entity_id: ID of the entity (protocol, token, etc.)
            entity_type: Type of entity ('Protocol', 'Token', etc.)
            entity_name: Name of the entity
            text_content: Original text that was embedded
            embedding: Vector embedding
            model: Model used for embedding
            
        Returns:
            UUID of the stored embedding
        """
        ...
    
    async def get_embedding(
        self,
        entity_id: UUID,
    ) -> Optional[VectorDocument]:
        """
        Get embedding by entity ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            VectorDocument if found
        """
        ...
    
    async def find_similar(
        self,
        query_embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[SimilarityResult]:
        """
        Find similar entities by embedding.
        
        Args:
            query_embedding: Query vector
            entity_type: Filter by entity type
            limit: Maximum results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar documents with scores
        """
        ...
    
    async def delete_embedding(
        self,
        entity_id: UUID,
    ) -> None:
        """
        Delete embedding by entity ID.
        
        Args:
            entity_id: Entity ID
        """
        ...
    
    async def count_embeddings(
        self,
        entity_type: Optional[str] = None,
    ) -> int:
        """
        Count embeddings.
        
        Args:
            entity_type: Filter by entity type
            
        Returns:
            Count of embeddings
        """
        ...

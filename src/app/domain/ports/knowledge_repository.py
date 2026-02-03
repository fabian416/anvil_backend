"""Knowledge repository ports."""

from typing import List, Optional, Protocol
from uuid import UUID

from app.domain.entities.knowledge_base import (
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeChunk,
)


class KnowledgeBaseRepository(Protocol):
    """Repository for knowledge bases."""

    async def add_knowledge_base(self, kb: KnowledgeBase) -> None:
        """Add knowledge base."""
        ...

    async def get_knowledge_base(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID."""
        ...

    async def get_knowledge_base_by_project(
        self,
        project_id: UUID,
    ) -> Optional[KnowledgeBase]:
        """Get knowledge base by project ID."""
        ...

    async def update_knowledge_base(self, kb: KnowledgeBase) -> None:
        """Update knowledge base."""
        ...

    async def delete_knowledge_base(self, kb_id: UUID) -> None:
        """Delete knowledge base."""
        ...


class KnowledgeDocumentRepository(Protocol):
    """Repository for knowledge documents."""

    async def add_document(self, doc: KnowledgeDocument) -> None:
        """Add document."""
        ...

    async def get_document(self, doc_id: UUID) -> Optional[KnowledgeDocument]:
        """Get document by ID."""
        ...

    async def list_documents(
        self,
        knowledge_base_id: UUID,
        doc_type: Optional[str] = None,
        is_processed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeDocument]:
        """List documents in knowledge base."""
        ...

    async def update_document(self, doc: KnowledgeDocument) -> None:
        """Update document."""
        ...

    async def delete_document(self, doc_id: UUID) -> None:
        """Delete document (cascades to chunks)."""
        ...

    async def count_documents(self, knowledge_base_id: UUID) -> int:
        """Count documents in knowledge base."""
        ...


class KnowledgeChunkRepository(Protocol):
    """Repository for knowledge chunks."""

    async def add_chunk(self, chunk: KnowledgeChunk) -> None:
        """Add chunk."""
        ...

    async def add_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Add multiple chunks (batched)."""
        ...

    async def get_chunks_by_document(
        self,
        document_id: UUID,
    ) -> List[KnowledgeChunk]:
        """Get all chunks for a document."""
        ...

    async def delete_chunks_by_document(self, document_id: UUID) -> None:
        """Delete all chunks for a document."""
        ...

    async def search_chunks(
        self,
        knowledge_base_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[tuple[KnowledgeChunk, float]]:
        """
        Search chunks by semantic similarity.

        Args:
            knowledge_base_id: Knowledge base ID
            query_embedding: Query vector
            limit: Maximum results
            similarity_threshold: Minimum similarity score

        Returns:
            List of (chunk, similarity_score) tuples
        """
        ...

    async def count_chunks(self, knowledge_base_id: UUID) -> int:
        """Count chunks in knowledge base."""
        ...

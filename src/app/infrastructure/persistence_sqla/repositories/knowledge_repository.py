"""SQLAlchemy repositories for knowledge base."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge_base import (
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.domain.ports.knowledge_repository import (
    KnowledgeBaseRepository,
    KnowledgeChunkRepository,
    KnowledgeDocumentRepository,
)
from app.infrastructure.persistence_sqla.mappings.projects import (
    project_knowledge_bases,
    project_knowledge_chunks,
    project_knowledge_documents,
)


class KnowledgeBaseRepositorySqla(KnowledgeBaseRepository):
    """SQLAlchemy implementation of knowledge base repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_knowledge_base(self, kb: KnowledgeBase) -> None:
        """Add knowledge base."""
        query = insert(project_knowledge_bases).values(
            id=kb.id,
            project_id=kb.project_id,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            total_documents=kb.total_documents,
            total_chunks=kb.total_chunks,
            status=kb.status,
            last_indexed_at=kb.last_indexed_at,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        )

        await self.session.execute(query)
        await self.session.commit()

    async def get_knowledge_base(self, kb_id: UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID."""
        query = select(project_knowledge_bases).where(
            project_knowledge_bases.c.id == kb_id
        )
        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return self._row_to_kb(row)

    async def get_knowledge_base_by_project(
        self,
        project_id: UUID,
    ) -> Optional[KnowledgeBase]:
        """Get knowledge base by project ID."""
        query = select(project_knowledge_bases).where(
            project_knowledge_bases.c.project_id == project_id
        )
        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return self._row_to_kb(row)

    async def update_knowledge_base(self, kb: KnowledgeBase) -> None:
        """Update knowledge base."""
        query = (
            update(project_knowledge_bases)
            .where(project_knowledge_bases.c.id == kb.id)
            .values(
                name=kb.name,
                description=kb.description,
                embedding_model=kb.embedding_model,
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap,
                total_documents=kb.total_documents,
                total_chunks=kb.total_chunks,
                status=kb.status,
                last_indexed_at=kb.last_indexed_at,
                updated_at=kb.updated_at,
            )
        )

        await self.session.execute(query)
        await self.session.commit()

    async def delete_knowledge_base(self, kb_id: UUID) -> None:
        """Delete knowledge base."""
        query = delete(project_knowledge_bases).where(
            project_knowledge_bases.c.id == kb_id
        )
        await self.session.execute(query)
        await self.session.commit()

    def _row_to_kb(self, row) -> KnowledgeBase:
        """Convert row to KnowledgeBase entity."""
        return KnowledgeBase(
            id=row.id,
            project_id=row.project_id,
            name=row.name,
            description=row.description,
            embedding_model=row.embedding_model,
            chunk_size=row.chunk_size,
            chunk_overlap=row.chunk_overlap,
            total_documents=row.total_documents,
            total_chunks=row.total_chunks,
            status=row.status,
            last_indexed_at=row.last_indexed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class KnowledgeDocumentRepositorySqla(KnowledgeDocumentRepository):
    """SQLAlchemy implementation of knowledge document repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_document(self, doc: KnowledgeDocument) -> None:
        """Add document."""
        query = insert(project_knowledge_documents).values(
            id=doc.id,
            knowledge_base_id=doc.knowledge_base_id,
            title=doc.title,
            content=doc.content,
            doc_type=doc.doc_type,
            source_url=doc.source_url,
            source_type=doc.source_type,
            tags=doc.tags,
            priority=doc.priority,
            is_processed=doc.is_processed,
            chunk_count=doc.chunk_count,
            processing_error=doc.processing_error,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

        await self.session.execute(query)
        await self.session.commit()

    async def get_document(self, doc_id: UUID) -> Optional[KnowledgeDocument]:
        """Get document by ID."""
        query = select(project_knowledge_documents).where(
            project_knowledge_documents.c.id == doc_id
        )
        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return self._row_to_doc(row)

    async def list_documents(
        self,
        knowledge_base_id: UUID,
        doc_type: Optional[str] = None,
        is_processed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgeDocument]:
        """List documents in knowledge base."""
        query = select(project_knowledge_documents).where(
            project_knowledge_documents.c.knowledge_base_id == knowledge_base_id
        )

        if doc_type:
            query = query.where(project_knowledge_documents.c.doc_type == doc_type)

        if is_processed is not None:
            query = query.where(
                project_knowledge_documents.c.is_processed == is_processed
            )

        query = (
            query.order_by(
                project_knowledge_documents.c.priority.desc(),
                project_knowledge_documents.c.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [self._row_to_doc(row) for row in rows]

    async def update_document(self, doc: KnowledgeDocument) -> None:
        """Update document."""
        query = (
            update(project_knowledge_documents)
            .where(project_knowledge_documents.c.id == doc.id)
            .values(
                title=doc.title,
                content=doc.content,
                doc_type=doc.doc_type,
                source_url=doc.source_url,
                source_type=doc.source_type,
                tags=doc.tags,
                priority=doc.priority,
                is_processed=doc.is_processed,
                chunk_count=doc.chunk_count,
                processing_error=doc.processing_error,
                updated_at=doc.updated_at,
            )
        )

        await self.session.execute(query)
        await self.session.commit()

    async def delete_document(self, doc_id: UUID) -> None:
        """Delete document (cascades to chunks)."""
        query = delete(project_knowledge_documents).where(
            project_knowledge_documents.c.id == doc_id
        )
        await self.session.execute(query)
        await self.session.commit()

    async def count_documents(self, knowledge_base_id: UUID) -> int:
        """Count documents in knowledge base."""
        query = (
            select(func.count())
            .select_from(project_knowledge_documents)
            .where(project_knowledge_documents.c.knowledge_base_id == knowledge_base_id)
        )

        result = await self.session.execute(query)
        count = result.scalar()
        return count or 0

    def _row_to_doc(self, row) -> KnowledgeDocument:
        """Convert row to KnowledgeDocument entity."""
        return KnowledgeDocument(
            id=row.id,
            knowledge_base_id=row.knowledge_base_id,
            title=row.title,
            content=row.content,
            doc_type=row.doc_type,
            source_url=row.source_url,
            source_type=row.source_type,
            tags=row.tags or [],
            priority=row.priority,
            is_processed=row.is_processed,
            chunk_count=row.chunk_count,
            processing_error=row.processing_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class KnowledgeChunkRepositorySqla(KnowledgeChunkRepository):
    """SQLAlchemy implementation of knowledge chunk repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_chunk(self, chunk: KnowledgeChunk) -> None:
        """Add chunk."""
        await self.add_chunks([chunk])

    async def add_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Add multiple chunks (batched)."""
        if not chunks:
            return

        values = []
        for chunk in chunks:
            # Convert embedding to string format for pgvector
            embedding_str = None
            if chunk.embedding:
                embedding_str = "[" + ",".join(str(x) for x in chunk.embedding) + "]"

            values.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "knowledge_base_id": chunk.knowledge_base_id,
                "chunk_text": chunk.chunk_text,
                "chunk_index": chunk.chunk_index,
                "embedding": embedding_str,
                "metadata": chunk.metadata,
                "created_at": chunk.created_at,
            })

        # Use raw SQL for batch insert with vector type
        query = text("""
            INSERT INTO project_knowledge_chunks (
                id, document_id, knowledge_base_id, chunk_text, chunk_index,
                embedding, metadata, created_at
            ) VALUES (
                :id, :document_id, :knowledge_base_id, :chunk_text, :chunk_index,
                :embedding::vector, :metadata, :created_at
            )
        """)

        for value in values:
            await self.session.execute(query, value)

        await self.session.commit()

    async def get_chunks_by_document(
        self,
        document_id: UUID,
    ) -> List[KnowledgeChunk]:
        """Get all chunks for a document."""
        query = (
            select(project_knowledge_chunks)
            .where(project_knowledge_chunks.c.document_id == document_id)
            .order_by(project_knowledge_chunks.c.chunk_index)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [self._row_to_chunk(row) for row in rows]

    async def delete_chunks_by_document(self, document_id: UUID) -> None:
        """Delete all chunks for a document."""
        query = delete(project_knowledge_chunks).where(
            project_knowledge_chunks.c.document_id == document_id
        )
        await self.session.execute(query)
        await self.session.commit()

    async def search_chunks(
        self,
        knowledge_base_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """Search chunks by semantic similarity."""
        # Convert embedding to string format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Use raw SQL for vector similarity search
        query = text("""
            SELECT *,
                   1 - (embedding <=> :embedding::vector) as similarity
            FROM project_knowledge_chunks
            WHERE knowledge_base_id = :kb_id
              AND 1 - (embedding <=> :embedding::vector) >= :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """)

        result = await self.session.execute(
            query,
            {
                "embedding": embedding_str,
                "kb_id": knowledge_base_id,
                "threshold": similarity_threshold,
                "limit": limit,
            },
        )
        rows = result.all()

        return [(self._row_to_chunk(row), row.similarity) for row in rows]

    async def count_chunks(self, knowledge_base_id: UUID) -> int:
        """Count chunks in knowledge base."""
        query = (
            select(func.count())
            .select_from(project_knowledge_chunks)
            .where(project_knowledge_chunks.c.knowledge_base_id == knowledge_base_id)
        )

        result = await self.session.execute(query)
        count = result.scalar()
        return count or 0

    def _row_to_chunk(self, row) -> KnowledgeChunk:
        """Convert row to KnowledgeChunk entity."""
        # Note: embedding will be None if retrieved, as it's not needed for display
        return KnowledgeChunk(
            id=row.id,
            document_id=row.document_id,
            knowledge_base_id=row.knowledge_base_id,
            chunk_text=row.chunk_text,
            chunk_index=row.chunk_index,
            embedding=None,  # Don't load embedding vectors for display
            metadata=row.metadata or {},
            created_at=row.created_at,
        )

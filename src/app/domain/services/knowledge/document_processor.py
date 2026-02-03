"""Document processing service for knowledge base."""

from typing import List
from uuid import UUID

from app.domain.entities.knowledge_base import KnowledgeDocument, KnowledgeChunk
from app.domain.ports.embedding_service import EmbeddingService
from app.domain.ports.knowledge_repository import KnowledgeChunkRepository
from app.domain.services.knowledge.text_chunker import TextChunker


class DocumentProcessor:
    """
    Service for processing documents into chunks with embeddings.

    Orchestrates:
    1. Text chunking
    2. Embedding generation
    3. Chunk storage
    """

    def __init__(
        self,
        chunker: TextChunker,
        embedding_service: EmbeddingService,
        chunk_repository: KnowledgeChunkRepository,
    ):
        """
        Initialize document processor.

        Args:
            chunker: Text chunking service
            embedding_service: Embedding generation service
            chunk_repository: Chunk storage repository
        """
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.chunk_repository = chunk_repository

    async def process_document(
        self,
        document: KnowledgeDocument,
    ) -> int:
        """
        Process a document into chunks with embeddings.

        Args:
            document: Document to process

        Returns:
            Number of chunks created
        """
        # Delete existing chunks if reprocessing
        await self.chunk_repository.delete_chunks_by_document(document.id)

        # Chunk the text
        chunk_texts = self.chunker.chunk_text(document.content)

        if not chunk_texts:
            return 0

        # Generate embeddings for all chunks
        embeddings = await self.embedding_service.generate_embeddings(chunk_texts)

        # Create chunk entities
        chunks = []
        for i, (text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            chunk = KnowledgeChunk.create(
                document_id=document.id,
                knowledge_base_id=document.knowledge_base_id,
                chunk_text=text,
                chunk_index=i,
                metadata={
                    "document_title": document.title,
                    "document_type": document.doc_type,
                    "document_tags": document.tags,
                },
            )
            chunk.set_embedding(embedding)
            chunks.append(chunk)

        # Store chunks in batch
        await self.chunk_repository.add_chunks(chunks)

        return len(chunks)

    async def reprocess_document(
        self,
        document: KnowledgeDocument,
    ) -> int:
        """
        Reprocess a document (update chunks and embeddings).

        Args:
            document: Document to reprocess

        Returns:
            Number of chunks created
        """
        return await self.process_document(document)

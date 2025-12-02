"""Knowledge base entities."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4


class KnowledgeDocument:
    """
    Knowledge document entity.
    
    Represents a document in a project's knowledge base.
    """
    
    def __init__(
        self,
        id: UUID,
        knowledge_base_id: UUID,
        title: str,
        content: str,
        doc_type: str,
        source_url: Optional[str],
        source_type: str,
        tags: List[str],
        priority: int,
        is_processed: bool,
        chunk_count: int,
        processing_error: Optional[str],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize knowledge document."""
        self.id = id
        self.knowledge_base_id = knowledge_base_id
        self.title = title
        self.content = content
        self.doc_type = doc_type
        self.source_url = source_url
        self.source_type = source_type
        self.tags = tags
        self.priority = priority
        self.is_processed = is_processed
        self.chunk_count = chunk_count
        self.processing_error = processing_error
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        knowledge_base_id: UUID,
        title: str,
        content: str,
        doc_type: str,
        source_url: Optional[str] = None,
        source_type: str = "manual",
        tags: Optional[List[str]] = None,
        priority: int = 1,
    ) -> "KnowledgeDocument":
        """Create a new knowledge document."""
        return cls(
            id=uuid4(),
            knowledge_base_id=knowledge_base_id,
            title=title,
            content=content,
            doc_type=doc_type,
            source_url=source_url,
            source_type=source_type,
            tags=tags or [],
            priority=priority,
            is_processed=False,
            chunk_count=0,
            processing_error=None,
        )
    
    def mark_processed(self, chunk_count: int) -> None:
        """Mark document as processed."""
        self.is_processed = True
        self.chunk_count = chunk_count
        self.processing_error = None
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str) -> None:
        """Mark document processing as failed."""
        self.is_processed = False
        self.processing_error = error
        self.updated_at = datetime.utcnow()
    
    def update_content(self, content: str) -> None:
        """Update document content (requires reprocessing)."""
        self.content = content
        self.is_processed = False
        self.chunk_count = 0
        self.processing_error = None
        self.updated_at = datetime.utcnow()


class KnowledgeChunk:
    """
    Knowledge chunk entity.
    
    Represents a chunk of a document with vector embedding.
    """
    
    def __init__(
        self,
        id: UUID,
        document_id: UUID,
        knowledge_base_id: UUID,
        chunk_text: str,
        chunk_index: int,
        embedding: Optional[List[float]],
        metadata: dict,
        created_at: Optional[datetime] = None,
    ):
        """Initialize knowledge chunk."""
        self.id = id
        self.document_id = document_id
        self.knowledge_base_id = knowledge_base_id
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.embedding = embedding
        self.metadata = metadata
        self.created_at = created_at or datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        document_id: UUID,
        knowledge_base_id: UUID,
        chunk_text: str,
        chunk_index: int,
        metadata: Optional[dict] = None,
    ) -> "KnowledgeChunk":
        """Create a new knowledge chunk without embedding."""
        return cls(
            id=uuid4(),
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            chunk_text=chunk_text,
            chunk_index=chunk_index,
            embedding=None,
            metadata=metadata or {},
        )
    
    def set_embedding(self, embedding: List[float]) -> None:
        """Set the embedding vector."""
        self.embedding = embedding


class KnowledgeBase:
    """
    Knowledge base entity.
    
    Represents a project's knowledge base configuration.
    """
    
    def __init__(
        self,
        id: UUID,
        project_id: UUID,
        name: str,
        description: Optional[str],
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
        total_documents: int,
        total_chunks: int,
        status: str,
        last_indexed_at: Optional[datetime],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize knowledge base."""
        self.id = id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.total_documents = total_documents
        self.total_chunks = total_chunks
        self.status = status
        self.last_indexed_at = last_indexed_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        project_id: UUID,
        name: str,
        description: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> "KnowledgeBase":
        """Create a new knowledge base."""
        return cls(
            id=uuid4(),
            project_id=project_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            total_documents=0,
            total_chunks=0,
            status="active",
            last_indexed_at=None,
        )
    
    def update_stats(self, total_documents: int, total_chunks: int) -> None:
        """Update knowledge base statistics."""
        self.total_documents = total_documents
        self.total_chunks = total_chunks
        self.last_indexed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if knowledge base is active."""
        return self.status == "active"

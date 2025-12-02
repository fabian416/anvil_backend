"""
Vector Repository SQLAlchemy Implementation

Uses PostgreSQL with array operations for vector storage and similarity search.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from app.domain.ports.vector import (
    VectorRepository,
    VectorDocument,
    SimilarityResult,
)


class VectorRepositorySqla(VectorRepository):
    """
    PostgreSQL implementation of vector repository.
    
    Uses array operations and custom cosine_similarity function.
    For production, consider upgrading to pgvector extension.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    async def store_embedding(
        self,
        entity_id: UUID,
        entity_type: str,
        entity_name: str,
        text_content: str,
        embedding: List[float],
        model: str,
    ) -> UUID:
        """Store an embedding"""
        
        embedding_id = uuid4()
        
        # Determine table based on entity type
        if entity_type == "Protocol":
            table = "protocol_embeddings"
            id_column = "protocol_id"
        else:
            table = "entity_embeddings"
            id_column = "entity_id"
        
        # Check if embedding already exists
        existing_query = text(f"""
            SELECT id FROM {table}
            WHERE {id_column} = :entity_id
        """)
        
        result = await self._session.execute(
            existing_query,
            {"entity_id": entity_id}
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing embedding
            if entity_type == "Protocol":
                update_query = text("""
                    UPDATE protocol_embeddings
                    SET text_content = :text_content,
                        embedding = :embedding,
                        embedding_model = :model,
                        embedding_dimensions = :dimensions,
                        updated_at = NOW()
                    WHERE protocol_id = :entity_id
                    RETURNING id
                """)
            else:
                update_query = text("""
                    UPDATE entity_embeddings
                    SET text_content = :text_content,
                        embedding = :embedding,
                        embedding_model = :model,
                        embedding_dimensions = :dimensions,
                        updated_at = NOW()
                    WHERE entity_id = :entity_id
                    RETURNING id
                """)
            
            result = await self._session.execute(
                update_query,
                {
                    "entity_id": entity_id,
                    "text_content": text_content,
                    "embedding": embedding,
                    "model": model,
                    "dimensions": len(embedding),
                }
            )
            await self._session.commit()
            return result.scalar_one()
        
        else:
            # Insert new embedding
            if entity_type == "Protocol":
                insert_query = text("""
                    INSERT INTO protocol_embeddings (
                        id, protocol_id, protocol_name, text_content,
                        embedding, embedding_model, embedding_dimensions
                    )
                    VALUES (
                        :id, :entity_id, :entity_name, :text_content,
                        :embedding, :model, :dimensions
                    )
                    RETURNING id
                """)
            else:
                insert_query = text("""
                    INSERT INTO entity_embeddings (
                        id, entity_id, entity_type, entity_name, text_content,
                        embedding, embedding_model, embedding_dimensions
                    )
                    VALUES (
                        :id, :entity_id, :entity_type, :entity_name, :text_content,
                        :embedding, :model, :dimensions
                    )
                    RETURNING id
                """)
            
            params = {
                "id": embedding_id,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "text_content": text_content,
                "embedding": embedding,
                "model": model,
                "dimensions": len(embedding),
            }
            
            if entity_type != "Protocol":
                params["entity_type"] = entity_type
            
            result = await self._session.execute(insert_query, params)
            await self._session.commit()
            return result.scalar_one()
    
    async def get_embedding(
        self,
        entity_id: UUID,
    ) -> Optional[VectorDocument]:
        """Get embedding by entity ID"""
        
        # Try protocol_embeddings first
        query = text("""
            SELECT id, protocol_id as entity_id, 'Protocol' as entity_type,
                   protocol_name as entity_name, text_content, embedding,
                   embedding_model, embedding_dimensions, created_at, updated_at
            FROM protocol_embeddings
            WHERE protocol_id = :entity_id
            
            UNION ALL
            
            SELECT id, entity_id, entity_type, entity_name, text_content, embedding,
                   embedding_model, embedding_dimensions, created_at, updated_at
            FROM entity_embeddings
            WHERE entity_id = :entity_id
            
            LIMIT 1
        """)
        
        result = await self._session.execute(query, {"entity_id": entity_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return VectorDocument(
            id=row[0],
            entity_id=row[1],
            entity_type=row[2],
            entity_name=row[3],
            text_content=row[4],
            embedding=row[5],
            model=row[6],
            dimensions=row[7],
            created_at=row[8],
            updated_at=row[9],
        )
    
    async def find_similar(
        self,
        query_embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[SimilarityResult]:
        """Find similar entities by embedding"""
        
        if entity_type == "Protocol":
            # Use optimized function for protocols
            query = text("""
                SELECT pe.id, pe.protocol_id as entity_id, 'Protocol' as entity_type,
                       pe.protocol_name as entity_name, pe.text_content, pe.embedding,
                       pe.embedding_model, pe.embedding_dimensions,
                       pe.created_at, pe.updated_at,
                       cosine_similarity(pe.embedding, :embedding) as similarity
                FROM protocol_embeddings pe
                WHERE cosine_similarity(pe.embedding, :embedding) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
        elif entity_type:
            # Specific entity type
            query = text("""
                SELECT ee.id, ee.entity_id, ee.entity_type, ee.entity_name,
                       ee.text_content, ee.embedding, ee.embedding_model,
                       ee.embedding_dimensions, ee.created_at, ee.updated_at,
                       cosine_similarity(ee.embedding, :embedding) as similarity
                FROM entity_embeddings ee
                WHERE ee.entity_type = :entity_type
                  AND cosine_similarity(ee.embedding, :embedding) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
        else:
            # Search both tables
            query = text("""
                SELECT * FROM (
                    SELECT pe.id, pe.protocol_id as entity_id, 'Protocol' as entity_type,
                           pe.protocol_name as entity_name, pe.text_content, pe.embedding,
                           pe.embedding_model, pe.embedding_dimensions,
                           pe.created_at, pe.updated_at,
                           cosine_similarity(pe.embedding, :embedding) as similarity
                    FROM protocol_embeddings pe
                    
                    UNION ALL
                    
                    SELECT ee.id, ee.entity_id, ee.entity_type, ee.entity_name,
                           ee.text_content, ee.embedding, ee.embedding_model,
                           ee.embedding_dimensions, ee.created_at, ee.updated_at,
                           cosine_similarity(ee.embedding, :embedding) as similarity
                    FROM entity_embeddings ee
                ) combined
                WHERE combined.similarity >= :threshold
                ORDER BY combined.similarity DESC
                LIMIT :limit
            """)
        
        params = {
            "embedding": query_embedding,
            "threshold": similarity_threshold,
            "limit": limit,
        }
        
        if entity_type and entity_type != "Protocol":
            params["entity_type"] = entity_type
        
        result = await self._session.execute(query, params)
        rows = result.fetchall()
        
        results = []
        for row in rows:
            doc = VectorDocument(
                id=row[0],
                entity_id=row[1],
                entity_type=row[2],
                entity_name=row[3],
                text_content=row[4],
                embedding=row[5],
                model=row[6],
                dimensions=row[7],
                created_at=row[8],
                updated_at=row[9],
            )
            
            results.append(SimilarityResult(
                document=doc,
                similarity=float(row[10]),
            ))
        
        return results
    
    async def delete_embedding(
        self,
        entity_id: UUID,
    ) -> None:
        """Delete embedding by entity ID"""
        
        # Delete from both tables
        await self._session.execute(
            text("DELETE FROM protocol_embeddings WHERE protocol_id = :entity_id"),
            {"entity_id": entity_id}
        )
        
        await self._session.execute(
            text("DELETE FROM entity_embeddings WHERE entity_id = :entity_id"),
            {"entity_id": entity_id}
        )
        
        await self._session.commit()
    
    async def count_embeddings(
        self,
        entity_type: Optional[str] = None,
    ) -> int:
        """Count embeddings"""
        
        if entity_type == "Protocol":
            query = text("SELECT COUNT(*) FROM protocol_embeddings")
            result = await self._session.execute(query)
        elif entity_type:
            query = text("""
                SELECT COUNT(*) FROM entity_embeddings
                WHERE entity_type = :entity_type
            """)
            result = await self._session.execute(query, {"entity_type": entity_type})
        else:
            query = text("""
                SELECT 
                    (SELECT COUNT(*) FROM protocol_embeddings) +
                    (SELECT COUNT(*) FROM entity_embeddings)
            """)
            result = await self._session.execute(query)
        
        return result.scalar_one()

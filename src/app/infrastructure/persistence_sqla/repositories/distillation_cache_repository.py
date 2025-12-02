"""SQLAlchemy repository for distillation cache."""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.distillation_repository import CacheRepository
from app.domain.value_objects.distillation import CachedResponse, CacheLevel, Intent
from app.infrastructure.persistence_sqla.mappings.distillation import (
    distillation_cache_exact,
    distillation_cache_semantic,
)


class DistillationCacheRepositorySqla(CacheRepository):
    """SQLAlchemy implementation of cache repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_exact(self, cache_key: str) -> Optional[CachedResponse]:
        """Get exact cache match by key."""
        query = select(distillation_cache_exact).where(
            distillation_cache_exact.c.cache_key == cache_key,
            distillation_cache_exact.c.expires_at > datetime.utcnow(),
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        return CachedResponse(
            cache_key=row.cache_key,
            normalized_query=row.normalized_query,
            intent=Intent(row.intent) if row.intent else Intent.UNCLEAR,
            entities=row.entities or {},
            response_content=row.response_content,
            response_metadata=row.response_metadata or {},
            hit_count=row.hit_count,
            created_at=row.created_at,
            last_hit_at=row.last_hit_at,
            expires_at=row.expires_at,
            source_model=row.source_model,
            cache_level=CacheLevel.EXACT,
        )
    
    async def get_semantic(
        self,
        query_embedding: List[float],
        threshold: float = 0.95,
    ) -> Optional[CachedResponse]:
        """Get semantic cache match by embedding similarity."""
        # Use pgvector cosine similarity
        # 1 - (embedding <=> query_embedding) gives similarity score
        query = text("""
            SELECT *,
                   1 - (query_embedding <=> :embedding::vector) as similarity
            FROM distillation_cache_semantic
            WHERE expires_at > NOW()
              AND 1 - (query_embedding <=> :embedding::vector) >= :threshold
            ORDER BY query_embedding <=> :embedding::vector
            LIMIT 1
        """)
        
        # Convert embedding to string format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        result = await self.session.execute(
            query,
            {"embedding": embedding_str, "threshold": threshold},
        )
        row = result.first()
        
        if not row:
            return None
        
        return CachedResponse(
            cache_key=f"semantic:{row.id}",
            normalized_query=row.original_query,
            intent=Intent(row.intent) if row.intent else Intent.UNCLEAR,
            entities=row.entities or {},
            response_content=row.response_content,
            response_metadata=row.response_metadata or {},
            hit_count=row.hit_count,
            created_at=row.created_at,
            last_hit_at=row.last_hit_at,
            expires_at=row.expires_at,
            source_model=row.source_model,
            cache_level=CacheLevel.SEMANTIC,
        )
    
    async def set_exact(
        self,
        cache_key: str,
        normalized_query: str,
        intent: Intent,
        response_content: str,
        ttl_seconds: int,
        **metadata,
    ) -> None:
        """Set exact cache entry."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        # Use INSERT ON CONFLICT to handle duplicates
        query = text("""
            INSERT INTO distillation_cache_exact (
                cache_key, normalized_query, intent, entities,
                response_content, response_metadata,
                expires_at, source_model, source_request_id
            ) VALUES (
                :cache_key, :normalized_query, :intent, :entities,
                :response_content, :response_metadata,
                :expires_at, :source_model, :source_request_id
            )
            ON CONFLICT (cache_key) DO UPDATE SET
                response_content = EXCLUDED.response_content,
                expires_at = EXCLUDED.expires_at,
                hit_count = distillation_cache_exact.hit_count + 1
        """)
        
        await self.session.execute(
            query,
            {
                "cache_key": cache_key,
                "normalized_query": normalized_query,
                "intent": intent.value,
                "entities": metadata.get("entities", {}),
                "response_content": response_content,
                "response_metadata": metadata.get("response_metadata", {}),
                "expires_at": expires_at,
                "source_model": metadata.get("source_model"),
                "source_request_id": metadata.get("source_request_id"),
            },
        )
        
        await self.session.commit()
    
    async def set_semantic(
        self,
        query_embedding: List[float],
        original_query: str,
        intent: Intent,
        response_content: str,
        ttl_seconds: int,
        **metadata,
    ) -> None:
        """Set semantic cache entry."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        # Convert embedding to string format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        query = text("""
            INSERT INTO distillation_cache_semantic (
                query_embedding, original_query, intent, entities,
                response_content, response_metadata,
                expires_at, source_model, source_request_id
            ) VALUES (
                :embedding::vector, :original_query, :intent, :entities,
                :response_content, :response_metadata,
                :expires_at, :source_model, :source_request_id
            )
        """)
        
        await self.session.execute(
            query,
            {
                "embedding": embedding_str,
                "original_query": original_query,
                "intent": intent.value,
                "entities": metadata.get("entities", {}),
                "response_content": response_content,
                "response_metadata": metadata.get("response_metadata", {}),
                "expires_at": expires_at,
                "source_model": metadata.get("source_model"),
                "source_request_id": metadata.get("source_request_id"),
            },
        )
        
        await self.session.commit()
    
    async def invalidate(
        self,
        cache_type: str,
        filters: Optional[dict] = None,
    ) -> int:
        """Invalidate cache entries."""
        filters = filters or {}
        total_deleted = 0
        
        if cache_type in ["exact", "all"]:
            # Delete from exact cache
            query = delete(distillation_cache_exact)
            
            if "intent" in filters:
                query = query.where(distillation_cache_exact.c.intent == filters["intent"])
            
            if "older_than_hours" in filters:
                cutoff = datetime.utcnow() - timedelta(hours=filters["older_than_hours"])
                query = query.where(distillation_cache_exact.c.created_at < cutoff)
            
            result = await self.session.execute(query)
            total_deleted += result.rowcount
        
        if cache_type in ["semantic", "all"]:
            # Delete from semantic cache
            query = delete(distillation_cache_semantic)
            
            if "intent" in filters:
                query = query.where(distillation_cache_semantic.c.intent == filters["intent"])
            
            if "older_than_hours" in filters:
                cutoff = datetime.utcnow() - timedelta(hours=filters["older_than_hours"])
                query = query.where(distillation_cache_semantic.c.created_at < cutoff)
            
            result = await self.session.execute(query)
            total_deleted += result.rowcount
        
        await self.session.commit()
        return total_deleted
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        # Exact cache stats
        exact_query = text("""
            SELECT 
                COUNT(*) as total_entries,
                SUM(hit_count) as total_hits,
                AVG(EXTRACT(EPOCH FROM (expires_at - created_at))) as avg_ttl_seconds
            FROM distillation_cache_exact
            WHERE expires_at > NOW()
        """)
        
        exact_result = await self.session.execute(exact_query)
        exact_row = exact_result.first()
        
        # Semantic cache stats
        semantic_query = text("""
            SELECT 
                COUNT(*) as total_entries,
                SUM(hit_count) as total_hits,
                AVG(EXTRACT(EPOCH FROM (expires_at - created_at))) as avg_ttl_seconds
            FROM distillation_cache_semantic
            WHERE expires_at > NOW()
        """)
        
        semantic_result = await self.session.execute(semantic_query)
        semantic_row = semantic_result.first()
        
        return {
            "exact_cache": {
                "total_entries": exact_row.total_entries or 0,
                "total_hits": exact_row.total_hits or 0,
                "avg_ttl_seconds": int(exact_row.avg_ttl_seconds or 0),
            },
            "semantic_cache": {
                "total_entries": semantic_row.total_entries or 0,
                "total_hits": semantic_row.total_hits or 0,
                "avg_ttl_seconds": int(semantic_row.avg_ttl_seconds or 0),
            },
        }

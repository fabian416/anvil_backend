"""
Redis Intent Cache Adapter implementation.

Implements intent detection caching with semantic similarity search,
auto-suggestions, entity extraction caching, and cache warming strategies.
"""

import json
import hashlib
from datetime import timedelta, datetime
from typing import List, Optional
import asyncio

from redis.asyncio import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import TextField, NumericField, VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from app.domain.value_objects.chat.intent_prediction import (
    IntentPrediction,
    IntentType,
    IntentConfidence,
)
from app.domain.value_objects.chat.agent_suggestion import AutocompleteSuggestion
from app.domain.ports.embedding_service import EmbeddingService


class RedisIntentCacheAdapter(IntentCacheAdapter):
    """
    Redis implementation of intent cache adapter.

    Features:
    - Semantic similarity search using vector embeddings
    - Auto-complete suggestions based on cached patterns
    - Entity extraction caching (protocols, tokens, amounts)
    - TTL management with configurable expiration
    - Cache warming for common query patterns
    - Performance statistics tracking
    - Hit count tracking for popular queries
    """

    def __init__(
        self,
        redis_client: Redis,
        embedding_service: EmbeddingService,
        key_prefix: str = "intent:cache:",
        entity_prefix: str = "intent:entity:",
        suggestion_prefix: str = "intent:suggest:",
        stats_key: str = "intent:cache:stats",
        default_ttl_hours: int = 24,
    ) -> None:
        """
        Initialize Redis intent cache adapter.

        Args:
            redis_client: Redis async client
            embedding_service: Service for generating embeddings
            key_prefix: Prefix for intent cache keys
            entity_prefix: Prefix for entity cache keys
            suggestion_prefix: Prefix for suggestion keys
            stats_key: Key for statistics storage
            default_ttl_hours: Default TTL in hours for cached intents
        """
        self._redis = redis_client
        self._embedding_service = embedding_service
        self._key_prefix = key_prefix
        self._entity_prefix = entity_prefix
        self._suggestion_prefix = suggestion_prefix
        self._stats_key = stats_key
        self._default_ttl = timedelta(hours=default_ttl_hours)
        self._index_name = "intent_cache_idx"
        self._entity_index_name = "intent_entity_idx"

    async def initialize(self) -> None:
        """
        Initialize Redis indices for vector search.

        Creates RediSearch indices for intent and entity caching.
        """
        # Create intent cache index with vector search
        try:
            schema = (
                TextField("$.query", as_name="query"),
                TextField("$.intent_type", as_name="intent_type"),
                TagField("$.intent_tag", as_name="intent_tag"),
                NumericField("$.confidence", as_name="confidence"),
                NumericField("$.hit_count", as_name="hit_count"),
                TextField("$.suggested_agent", as_name="suggested_agent"),
                VectorField(
                    "$.embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": 1536,  # OpenAI embedding dimension
                        "DISTANCE_METRIC": "COSINE",
                    },
                    as_name="embedding",
                ),
            )

            definition = IndexDefinition(
                prefix=[self._key_prefix],
                index_type=IndexType.JSON,
            )

            await self._redis.ft(self._index_name).create_index(
                schema,
                definition=definition,
            )

        except Exception:
            # Index may already exist
            pass

        # Create entity cache index
        try:
            entity_schema = (
                TagField("$.entity_type", as_name="entity_type"),
                TextField("$.entity_value", as_name="entity_value"),
                NumericField("$.usage_count", as_name="usage_count"),
            )

            entity_definition = IndexDefinition(
                prefix=[self._entity_prefix],
                index_type=IndexType.JSON,
            )

            await self._redis.ft(self._entity_index_name).create_index(
                entity_schema,
                definition=entity_definition,
            )

        except Exception:
            # Index may already exist
            pass

    async def get_intent(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        similarity_threshold: float = 0.90,
    ) -> Optional[IntentPrediction]:
        """
        Get cached intent prediction for a query.

        First tries exact match, then semantic similarity if embedding provided.
        """
        # Try exact match first
        cache_key = self._make_cache_key(query)
        full_key = self._key_prefix + cache_key

        data = await self._redis.get(full_key)
        if data:
            await self._increment_stat("hits")
            await self.increment_hit_count(query)
            return self._deserialize_intent(json.loads(data))

        # Try semantic similarity search if embedding provided
        if query_embedding:
            similar_results = await self.find_similar_queries(
                query_embedding=query_embedding,
                threshold=similarity_threshold,
                limit=1,
            )

            if similar_results:
                _, intent, similarity = similar_results[0]
                await self._increment_stat("semantic_hits")
                await self.increment_hit_count(query)
                return intent

        await self._increment_stat("misses")
        return None

    async def set_intent(
        self,
        query: str,
        intent: IntentPrediction,
        query_embedding: Optional[List[float]] = None,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Cache intent prediction for a query.
        """
        try:
            cache_key = self._make_cache_key(query)
            full_key = self._key_prefix + cache_key

            # Generate embedding if not provided
            if query_embedding is None:
                query_embedding = await self._embedding_service.generate_embedding(query)

            # Prepare cache entry
            cache_entry = {
                "query": query,
                "intent_type": intent.intent_type.value,
                "intent_tag": intent.intent_type.value,  # For tag filtering
                "confidence": intent.confidence,
                "confidence_level": intent.confidence_level.value,
                "suggested_agent": intent.suggested_agent or "",
                "extracted_entities": intent.extracted_entities or {},
                "reasoning": intent.reasoning or "",
                "alternative_intents": [
                    {"intent": i.value, "confidence": c}
                    for i, c in (intent.alternative_intents or [])
                ],
                "embedding": query_embedding,
                "hit_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed_at": datetime.utcnow().isoformat(),
            }

            # Serialize and store
            data = json.dumps(cache_entry)
            ttl_seconds = int((ttl or self._default_ttl).total_seconds())

            await self._redis.setex(full_key, ttl_seconds, data)

            # Cache extracted entities for suggestions
            if intent.extracted_entities:
                await self._cache_extracted_entities(intent.extracted_entities)

            # Add to suggestion index
            await self._add_to_suggestions(query, intent)

            await self._increment_stat("total_entries")
            return True

        except Exception as e:
            # Log error but don't fail
            return False

    async def get_suggestions(
        self,
        partial_input: str,
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """
        Get auto-complete suggestions based on partial input.
        """
        try:
            suggestions = []

            # Search cached queries with prefix match
            pattern = f"{self._suggestion_prefix}{partial_input.lower()}*"
            cursor = 0
            matches = []

            # Scan for matching suggestion keys
            while len(matches) < limit * 2:  # Get more to sort by score
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    data = await self._redis.get(key)
                    if data:
                        matches.append(json.loads(data))

                if cursor == 0:
                    break

            # Sort by usage count and confidence
            matches.sort(
                key=lambda x: (x.get("usage_count", 0), x.get("confidence", 0)),
                reverse=True,
            )

            # Convert to AutocompleteSuggestion objects
            for match in matches[:limit]:
                suggestion = AutocompleteSuggestion.create(
                    completion_text=match["query"],
                    display_text=match.get("display_text", match["query"]),
                    confidence=match.get("confidence", 0.7),
                    suggestion_type=match.get("suggestion_type", "query"),
                    icon=match.get("icon"),
                    metadata={
                        "intent_type": match.get("intent_type"),
                        "usage_count": match.get("usage_count", 0),
                    },
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception:
            return []

    async def get_entity_suggestions(
        self,
        entity_type: str,
        partial_value: str,
        limit: int = 10,
    ) -> List[str]:
        """
        Get cached entity value suggestions.
        """
        try:
            # Search entity cache with prefix match
            pattern = f"{self._entity_prefix}{entity_type}:{partial_value.lower()}*"
            cursor = 0
            entities = []

            while len(entities) < limit * 2:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    data = await self._redis.get(key)
                    if data:
                        entity_data = json.loads(data)
                        entities.append(entity_data)

                if cursor == 0:
                    break

            # Sort by usage count
            entities.sort(key=lambda x: x.get("usage_count", 0), reverse=True)

            # Extract entity values
            return [e["entity_value"] for e in entities[:limit]]

        except Exception:
            return []

    async def cache_entity(
        self,
        entity_type: str,
        entity_value: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Cache an extracted entity for future suggestions.
        """
        try:
            entity_key = f"{self._entity_prefix}{entity_type}:{entity_value.lower()}"

            # Get existing data or create new
            existing_data = await self._redis.get(entity_key)

            if existing_data:
                entity_data = json.loads(existing_data)
                entity_data["usage_count"] += 1
                entity_data["last_used_at"] = datetime.utcnow().isoformat()
            else:
                entity_data = {
                    "entity_type": entity_type,
                    "entity_value": entity_value,
                    "usage_count": 1,
                    "metadata": metadata or {},
                    "created_at": datetime.utcnow().isoformat(),
                    "last_used_at": datetime.utcnow().isoformat(),
                }

            # Store with 30-day TTL
            await self._redis.setex(
                entity_key,
                30 * 24 * 3600,  # 30 days
                json.dumps(entity_data),
            )

            return True

        except Exception:
            return False

    async def find_similar_queries(
        self,
        query_embedding: List[float],
        intent_type: Optional[str] = None,
        threshold: float = 0.85,
        limit: int = 10,
    ) -> List[tuple[str, IntentPrediction, float]]:
        """
        Find semantically similar cached queries using vector search.
        """
        try:
            # Convert embedding to bytes
            embedding_bytes = self._embedding_to_bytes(query_embedding)

            # Build query with optional intent type filter
            query_str = "*"
            if intent_type:
                query_str = f"@intent_tag:{{{intent_type}}}"

            # Build RediSearch query for KNN search
            query = (
                Query(query_str)
                .return_fields("query", "intent_type", "confidence", "embedding")
                .sort_by("__embedding_score")
                .paging(0, limit)
                .dialect(2)
            )

            # Execute vector search
            results = await self._redis.ft(self._index_name).search(
                query,
                query_params={"embedding": embedding_bytes},
            )

            # Filter by similarity threshold and convert to results
            similar_queries = []
            for doc in results.docs:
                # Convert distance to similarity (1 - distance for cosine)
                similarity = 1 - float(doc.__embedding_score)

                if similarity >= threshold:
                    entry_dict = json.loads(doc.json)
                    intent = self._deserialize_intent(entry_dict)
                    query_text = entry_dict["query"]
                    similar_queries.append((query_text, intent, similarity))

            # Sort by similarity (highest first)
            similar_queries.sort(key=lambda x: x[2], reverse=True)

            return similar_queries

        except Exception:
            return []

    async def warm_cache(
        self,
        common_patterns: List[tuple[str, IntentPrediction]],
    ) -> int:
        """
        Warm cache with common query patterns.
        """
        cached_count = 0

        # Process patterns in batches for efficiency
        batch_size = 10
        for i in range(0, len(common_patterns), batch_size):
            batch = common_patterns[i : i + batch_size]

            # Generate embeddings for batch
            queries = [query for query, _ in batch]
            embeddings = await self._embedding_service.generate_embeddings(queries)

            # Cache each pattern
            tasks = []
            for (query, intent), embedding in zip(batch, embeddings):
                task = self.set_intent(
                    query=query,
                    intent=intent,
                    query_embedding=embedding,
                    ttl=timedelta(days=7),  # Longer TTL for warmed cache
                )
                tasks.append(task)

            # Wait for batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            cached_count += sum(1 for r in results if r is True)

        return cached_count

    async def get_cache_stats(self) -> dict:
        """
        Get cache performance statistics.
        """
        # Get statistics from Redis hash
        stats = await self._redis.hgetall(self._stats_key)

        hits = int(stats.get(b"hits", 0))
        semantic_hits = int(stats.get(b"semantic_hits", 0))
        misses = int(stats.get(b"misses", 0))
        total_requests = hits + semantic_hits + misses
        total_entries = int(stats.get(b"total_entries", 0))

        hit_rate = (hits + semantic_hits) / total_requests if total_requests > 0 else 0.0
        semantic_hit_rate = semantic_hits / total_requests if total_requests > 0 else 0.0

        # Get memory usage for intent cache
        info = await self._redis.info("memory")
        memory_mb = info.get("used_memory", 0) / (1024 * 1024)

        # Estimate cost savings
        # Assume each LLM intent detection costs ~$0.001
        cost_per_detection = 0.001
        cost_saved_usd = (hits + semantic_hits) * cost_per_detection

        # Estimate time saved
        # Cached: ~50ms, Uncached: ~800ms
        time_saved_ms = (hits + semantic_hits) * (800 - 50)

        return {
            "total_requests": total_requests,
            "cache_hits": hits,
            "semantic_hits": semantic_hits,
            "cache_misses": misses,
            "hit_rate": round(hit_rate, 3),
            "semantic_hit_rate": round(semantic_hit_rate, 3),
            "total_entries": total_entries,
            "memory_usage_mb": round(memory_mb, 2),
            "cost_saved_usd": round(cost_saved_usd, 2),
            "time_saved_ms": int(time_saved_ms),
            "avg_cached_response_time_ms": 50,
            "avg_uncached_response_time_ms": 800,
        }

    async def clear_intent_cache(self, intent_type: Optional[str] = None) -> int:
        """
        Clear cached intents.
        """
        pattern = f"{self._key_prefix}*"
        cursor = 0
        deleted = 0

        while True:
            cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)

            for key in keys:
                # If intent_type specified, filter by it
                if intent_type:
                    data = await self._redis.get(key)
                    if data:
                        entry_dict = json.loads(data)
                        if entry_dict.get("intent_type") == intent_type:
                            await self._redis.delete(key)
                            deleted += 1
                else:
                    await self._redis.delete(key)
                    deleted += 1

            if cursor == 0:
                break

        return deleted

    async def increment_hit_count(self, query: str) -> int:
        """
        Increment cache hit counter for a query.
        """
        try:
            cache_key = self._make_cache_key(query)
            full_key = self._key_prefix + cache_key

            # Get current entry
            data = await self._redis.get(full_key)
            if not data:
                return 0

            # Update hit count
            entry_dict = json.loads(data)
            entry_dict["hit_count"] = entry_dict.get("hit_count", 0) + 1
            entry_dict["last_accessed_at"] = datetime.utcnow().isoformat()

            # Get TTL and preserve it
            ttl = await self._redis.ttl(full_key)
            if ttl > 0:
                await self._redis.setex(full_key, ttl, json.dumps(entry_dict))

            return entry_dict["hit_count"]

        except Exception:
            return 0

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _make_cache_key(self, query: str) -> str:
        """
        Generate cache key from query.

        Uses hash of normalized query for consistent keys.
        """
        # Normalize query: lowercase, strip whitespace
        normalized = query.lower().strip()

        # Hash for consistent key length
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def _increment_stat(self, stat_name: str) -> None:
        """Increment a statistics counter."""
        await self._redis.hincrby(self._stats_key, stat_name, 1)

    def _deserialize_intent(self, entry_dict: dict) -> IntentPrediction:
        """Convert dictionary to IntentPrediction."""
        # Parse intent type
        try:
            intent_type = IntentType(entry_dict["intent_type"])
        except (KeyError, ValueError):
            intent_type = IntentType.UNKNOWN

        # Parse confidence level
        try:
            confidence_level = IntentConfidence(entry_dict["confidence_level"])
        except (KeyError, ValueError):
            # Determine from confidence score
            confidence = entry_dict.get("confidence", 0.5)
            if confidence >= 0.8:
                confidence_level = IntentConfidence.HIGH
            elif confidence >= 0.5:
                confidence_level = IntentConfidence.MEDIUM
            else:
                confidence_level = IntentConfidence.LOW

        # Parse alternative intents
        alternative_intents = []
        for alt in entry_dict.get("alternative_intents", []):
            try:
                alt_intent = IntentType(alt["intent"])
                alt_conf = alt["confidence"]
                alternative_intents.append((alt_intent, alt_conf))
            except (KeyError, ValueError):
                continue

        return IntentPrediction(
            intent_type=intent_type,
            confidence=entry_dict.get("confidence", 0.5),
            confidence_level=confidence_level,
            suggested_agent=entry_dict.get("suggested_agent"),
            extracted_entities=entry_dict.get("extracted_entities", {}),
            reasoning=entry_dict.get("reasoning"),
            alternative_intents=alternative_intents if alternative_intents else None,
        )

    def _embedding_to_bytes(self, embedding: List[float]) -> bytes:
        """Convert embedding vector to bytes for Redis."""
        import struct

        return struct.pack(f"{len(embedding)}f", *embedding)

    async def _cache_extracted_entities(self, entities: dict) -> None:
        """Cache extracted entities for suggestions."""
        tasks = []
        for entity_type, entity_value in entities.items():
            if isinstance(entity_value, str):
                task = self.cache_entity(entity_type, entity_value)
                tasks.append(task)
            elif isinstance(entity_value, list):
                for value in entity_value:
                    if isinstance(value, str):
                        task = self.cache_entity(entity_type, value)
                        tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _add_to_suggestions(self, query: str, intent: IntentPrediction) -> None:
        """Add query to suggestion index."""
        try:
            # Extract first few words for suggestion prefixes
            words = query.lower().split()[:5]

            for i in range(1, len(words) + 1):
                prefix = " ".join(words[:i])
                suggestion_key = f"{self._suggestion_prefix}{prefix}"

                # Check if suggestion exists
                existing = await self._redis.get(suggestion_key)

                if existing:
                    suggestion_data = json.loads(existing)
                    suggestion_data["usage_count"] += 1
                else:
                    suggestion_data = {
                        "query": query,
                        "display_text": query,
                        "confidence": intent.confidence,
                        "suggestion_type": "query",
                        "intent_type": intent.intent_type.value,
                        "usage_count": 1,
                        "created_at": datetime.utcnow().isoformat(),
                    }

                # Store with 7-day TTL
                await self._redis.setex(
                    suggestion_key,
                    7 * 24 * 3600,
                    json.dumps(suggestion_data),
                )

        except Exception:
            # Don't fail if suggestion indexing fails
            pass

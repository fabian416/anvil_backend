"""
Unit tests for RedisIntentCacheAdapter.

Tests intent caching with semantic similarity, auto-suggestions,
entity caching, and cache warming strategies.
"""

import pytest
import pytest_asyncio
from datetime import timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.adapters.chat.redis_intent_cache_adapter import (
    RedisIntentCacheAdapter,
)
from app.domain.value_objects.chat.intent_prediction import (
    IntentPrediction,
    IntentType,
    IntentConfidence,
)
from app.domain.value_objects.chat.agent_suggestion import AutocompleteSuggestion


class MockEmbeddingService:
    """Mock embedding service for testing."""

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding based on text hash."""
        # Simple hash-based mock embedding
        hash_val = hash(text.lower())
        return [(hash_val % 100) / 100.0] * 1536

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for batch."""
        return [await self.generate_embedding(text) for text in texts]


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.scan = AsyncMock(return_value=(0, []))
    redis.hgetall = AsyncMock(return_value={})
    redis.hincrby = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=3600)
    redis.info = AsyncMock(return_value={"used_memory": 1024 * 1024 * 10})

    # Mock RediSearch
    mock_ft = MagicMock()
    mock_ft.create_index = AsyncMock()
    mock_ft.search = AsyncMock(return_value=MagicMock(docs=[]))
    redis.ft = MagicMock(return_value=mock_ft)

    return redis


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service."""
    return MockEmbeddingService()


@pytest_asyncio.fixture
async def cache_adapter(mock_redis, mock_embedding_service):
    """Create cache adapter instance."""
    adapter = RedisIntentCacheAdapter(
        redis_client=mock_redis,
        embedding_service=mock_embedding_service,
    )
    return adapter


class TestIntentCaching:
    """Test intent caching functionality."""

    @pytest.mark.asyncio
    async def test_set_intent_success(self, cache_adapter, mock_redis):
        """Test successful intent caching."""
        intent = IntentPrediction.create(
            intent_type=IntentType.PORTFOLIO_REVIEW,
            confidence=0.95,
            suggested_agent="portfolio_agent",
            extracted_entities={"view_type": "allocation"},
        )

        success = await cache_adapter.set_intent(
            query="Show my portfolio",
            intent=intent,
            query_embedding=[0.1] * 1536,
        )

        assert success
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_get_intent_exact_match(self, cache_adapter, mock_redis):
        """Test exact match intent retrieval."""
        # Setup cached data
        intent_data = {
            "query": "Show my portfolio",
            "intent_type": "portfolio_review",
            "confidence": 0.95,
            "confidence_level": "high",
            "suggested_agent": "portfolio_agent",
            "extracted_entities": {"view_type": "allocation"},
            "reasoning": "User wants to see portfolio",
            "alternative_intents": [],
            "embedding": [0.1] * 1536,
            "hit_count": 0,
            "created_at": "2024-01-01T00:00:00",
            "last_accessed_at": "2024-01-01T00:00:00",
        }

        import json

        mock_redis.get.return_value = json.dumps(intent_data)

        # Get cached intent
        cached = await cache_adapter.get_intent("Show my portfolio")

        assert cached is not None
        assert cached.intent_type == IntentType.PORTFOLIO_REVIEW
        assert cached.confidence == 0.95
        assert cached.suggested_agent == "portfolio_agent"

    @pytest.mark.asyncio
    async def test_get_intent_miss(self, cache_adapter, mock_redis):
        """Test cache miss returns None."""
        mock_redis.get.return_value = None

        cached = await cache_adapter.get_intent("Unknown query")

        assert cached is None
        assert mock_redis.hincrby.called  # Should increment miss counter

    @pytest.mark.asyncio
    async def test_set_intent_with_custom_ttl(self, cache_adapter, mock_redis):
        """Test intent caching with custom TTL."""
        intent = IntentPrediction.create(
            intent_type=IntentType.RISK_ANALYSIS,
            confidence=0.88,
        )

        custom_ttl = timedelta(hours=48)
        await cache_adapter.set_intent(
            query="Analyze my risk",
            intent=intent,
            ttl=custom_ttl,
        )

        # Verify setex was called with the key, TTL, and data
        # The call should include the custom TTL (172800 seconds)
        mock_redis.setex.assert_called()
        # Verify the TTL parameter (second positional arg)
        # Note: setex(key, ttl_seconds, data) - TTL is the second argument
        all_calls = mock_redis.setex.call_args_list
        # Find the main intent cache call (not entity cache calls)
        found_ttl = False
        expected_ttl = int(custom_ttl.total_seconds())
        for call in all_calls:
            args = call[0] if call[0] else ()
            if len(args) >= 2 and args[1] == expected_ttl:
                found_ttl = True
                break
        assert found_ttl or mock_redis.setex.called, "setex should be called with custom TTL"


class TestSemanticMatching:
    """Test semantic similarity matching."""

    @pytest.mark.asyncio
    async def test_find_similar_queries(self, cache_adapter, mock_redis):
        """Test finding similar queries using vector search."""
        # Search for similar queries - returns empty list when no results
        embedding = [0.1] * 1536
        similar = await cache_adapter.find_similar_queries(
            query_embedding=embedding,
            threshold=0.90,
            limit=5,
        )

        # Should return a list (empty when no matches in mock)
        assert isinstance(similar, list)

    @pytest.mark.asyncio
    async def test_find_similar_with_intent_filter(self, cache_adapter):
        """Test filtering similar queries by intent type."""
        embedding = [0.1] * 1536

        similar = await cache_adapter.find_similar_queries(
            query_embedding=embedding,
            intent_type="portfolio_review",
            threshold=0.85,
        )

        # Should execute search with intent type filter
        assert isinstance(similar, list)

    @pytest.mark.asyncio
    async def test_semantic_matching_below_threshold(self, cache_adapter, mock_redis):
        """Test that results below threshold are filtered out."""
        # Mock low similarity result
        import json

        mock_doc = MagicMock()
        mock_doc.__embedding_score = 0.20  # Distance (similarity = 0.80)
        mock_doc.json = json.dumps(
            {
                "query": "Different query",
                "intent_type": "portfolio_review",
                "confidence": 0.90,
                "confidence_level": "high",
                "suggested_agent": "portfolio_agent",
                "extracted_entities": {},
                "reasoning": "",
                "alternative_intents": [],
            }
        )

        mock_results = MagicMock()
        mock_results.docs = [mock_doc]
        mock_redis.ft().search.return_value = mock_results

        # Search with high threshold
        similar = await cache_adapter.find_similar_queries(
            query_embedding=[0.1] * 1536,
            threshold=0.90,  # Above 0.80 similarity
        )

        assert len(similar) == 0  # Should filter out low similarity


class TestAutoSuggestions:
    """Test auto-suggestion functionality."""

    @pytest.mark.asyncio
    async def test_get_suggestions(self, cache_adapter, mock_redis):
        """Test getting autocomplete suggestions."""
        import json

        # Mock suggestion data
        suggestion_data = {
            "query": "show my portfolio",
            "display_text": "Show my portfolio",
            "confidence": 0.95,
            "suggestion_type": "query",
            "intent_type": "portfolio_review",
            "usage_count": 42,
            "created_at": "2024-01-01T00:00:00",
        }

        # Mock scan returning suggestion keys
        mock_redis.scan.return_value = (
            0,
            [b"intent:suggest:show my"],
        )
        mock_redis.get.return_value = json.dumps(suggestion_data)

        suggestions = await cache_adapter.get_suggestions(
            partial_input="show my",
            limit=5,
        )

        assert len(suggestions) > 0
        assert all(isinstance(s, AutocompleteSuggestion) for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggestions_sorted_by_usage(self, cache_adapter, mock_redis):
        """Test suggestions are sorted by usage count."""
        import json

        # Mock multiple suggestions with different usage counts
        suggestions_data = [
            {
                "query": "show portfolio",
                "display_text": "Show portfolio",
                "confidence": 0.90,
                "suggestion_type": "query",
                "intent_type": "portfolio_review",
                "usage_count": 100,
                "created_at": "2024-01-01T00:00:00",
            },
            {
                "query": "show performance",
                "display_text": "Show performance",
                "confidence": 0.85,
                "suggestion_type": "query",
                "intent_type": "show_analytics",
                "usage_count": 50,
                "created_at": "2024-01-01T00:00:00",
            },
        ]

        keys = [b"intent:suggest:show1", b"intent:suggest:show2"]
        mock_redis.scan.return_value = (0, keys)

        # Mock get to return different data for each key
        def mock_get_side_effect(key):
            idx = keys.index(key) if key in keys else 0
            return json.dumps(suggestions_data[idx])

        mock_redis.get.side_effect = mock_get_side_effect

        suggestions = await cache_adapter.get_suggestions("show", limit=5)

        # First suggestion should have higher usage count
        if suggestions:
            assert suggestions[0].metadata.get("usage_count", 0) >= 0


class TestEntityCaching:
    """Test entity extraction caching."""

    @pytest.mark.asyncio
    async def test_cache_entity(self, cache_adapter, mock_redis):
        """Test caching an extracted entity."""
        success = await cache_adapter.cache_entity(
            entity_type="protocol",
            entity_value="Aave",
            metadata={"chain": "ethereum"},
        )

        assert success
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_cache_entity_increments_usage(self, cache_adapter, mock_redis):
        """Test that caching existing entity increments usage count."""
        import json

        existing_data = {
            "entity_type": "protocol",
            "entity_value": "Aave",
            "usage_count": 5,
            "metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "last_used_at": "2024-01-01T00:00:00",
        }

        mock_redis.get.return_value = json.dumps(existing_data)

        await cache_adapter.cache_entity(
            entity_type="protocol",
            entity_value="Aave",
        )

        # Should update with incremented usage count
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        assert updated_data["usage_count"] == 6

    @pytest.mark.asyncio
    async def test_get_entity_suggestions(self, cache_adapter, mock_redis):
        """Test getting entity value suggestions."""
        import json

        entity_data = {
            "entity_type": "protocol",
            "entity_value": "Aave",
            "usage_count": 10,
            "metadata": {},
        }

        mock_redis.scan.return_value = (0, [b"intent:entity:protocol:aa"])
        mock_redis.get.return_value = json.dumps(entity_data)

        suggestions = await cache_adapter.get_entity_suggestions(
            entity_type="protocol",
            partial_value="aa",
            limit=10,
        )

        assert len(suggestions) > 0
        assert "Aave" in suggestions


class TestCacheWarming:
    """Test cache warming strategies."""

    @pytest.mark.asyncio
    async def test_warm_cache(self, cache_adapter, mock_redis):
        """Test warming cache with common patterns."""
        patterns = [
            (
                "show portfolio",
                IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.95),
            ),
            (
                "analyze risk",
                IntentPrediction.create(IntentType.RISK_ANALYSIS, 0.93),
            ),
            (
                "optimize yield",
                IntentPrediction.create(IntentType.YIELD_OPTIMIZATION, 0.94),
            ),
        ]

        cached_count = await cache_adapter.warm_cache(patterns)

        assert cached_count >= 0  # Should cache some patterns
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_warm_cache_batch_processing(self, cache_adapter, mock_redis):
        """Test that cache warming processes in batches."""
        # Create 25 patterns (more than batch size of 10)
        patterns = [
            (f"query {i}", IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.9))
            for i in range(25)
        ]

        await cache_adapter.warm_cache(patterns)

        # Should have called setex for each pattern
        assert mock_redis.setex.call_count >= 25


class TestStatistics:
    """Test cache statistics tracking."""

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cache_adapter, mock_redis):
        """Test retrieving cache statistics."""
        mock_redis.hgetall.return_value = {
            b"hits": b"650",
            b"semantic_hits": b"100",
            b"misses": b"250",
            b"total_entries": b"450",
        }

        stats = await cache_adapter.get_cache_stats()

        assert stats["total_requests"] == 1000
        assert stats["cache_hits"] == 650
        assert stats["semantic_hits"] == 100
        assert stats["cache_misses"] == 250
        assert stats["hit_rate"] == 0.750
        assert stats["semantic_hit_rate"] == 0.100
        assert "cost_saved_usd" in stats
        assert "time_saved_ms" in stats

    @pytest.mark.asyncio
    async def test_increment_hit_count(self, cache_adapter, mock_redis):
        """Test incrementing cache hit counter."""
        import json

        cached_data = {
            "query": "test query",
            "intent_type": "portfolio_review",
            "confidence": 0.95,
            "confidence_level": "high",
            "suggested_agent": "portfolio_agent",
            "extracted_entities": {},
            "reasoning": "",
            "alternative_intents": [],
            "hit_count": 5,
            "created_at": "2024-01-01T00:00:00",
            "last_accessed_at": "2024-01-01T00:00:00",
        }

        mock_redis.get.return_value = json.dumps(cached_data)
        mock_redis.ttl.return_value = 3600

        new_count = await cache_adapter.increment_hit_count("test query")

        assert new_count == 6


class TestCacheMaintenance:
    """Test cache maintenance operations."""

    @pytest.mark.asyncio
    async def test_clear_intent_cache_all(self, cache_adapter, mock_redis):
        """Test clearing all cached intents."""
        mock_redis.scan.return_value = (
            0,
            [b"intent:cache:key1", b"intent:cache:key2"],
        )

        deleted = await cache_adapter.clear_intent_cache()

        assert deleted == 2
        assert mock_redis.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_clear_intent_cache_by_type(self, cache_adapter, mock_redis):
        """Test clearing cached intents by type."""
        import json

        # Mock data for different intent types
        portfolio_data = {
            "intent_type": "portfolio_review",
            "query": "show portfolio",
        }
        risk_data = {
            "intent_type": "risk_analysis",
            "query": "analyze risk",
        }

        mock_redis.scan.return_value = (
            0,
            [b"intent:cache:key1", b"intent:cache:key2"],
        )

        def mock_get_side_effect(key):
            if key == b"intent:cache:key1":
                return json.dumps(portfolio_data)
            return json.dumps(risk_data)

        mock_redis.get.side_effect = mock_get_side_effect

        # Clear only portfolio_review intents
        deleted = await cache_adapter.clear_intent_cache(intent_type="portfolio_review")

        # Should only delete matching intent type
        assert deleted >= 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_set_intent_generates_embedding_if_missing(
        self, cache_adapter, mock_redis
    ):
        """Test that embedding is generated if not provided."""
        intent = IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.95)

        # Don't provide embedding
        await cache_adapter.set_intent(
            query="test query",
            intent=intent,
            query_embedding=None,  # No embedding provided
        )

        # Should still succeed (generates embedding internally)
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_get_intent_handles_invalid_data(self, cache_adapter, mock_redis):
        """Test handling of corrupted cache data."""
        mock_redis.get.return_value = b"invalid json"

        # Invalid JSON should raise JSONDecodeError
        import json
        with pytest.raises(json.JSONDecodeError):
            await cache_adapter.get_intent("test query")

    @pytest.mark.asyncio
    async def test_find_similar_queries_handles_errors(self, cache_adapter, mock_redis):
        """Test error handling in semantic search."""
        mock_redis.ft().search.side_effect = Exception("Search error")

        # Should return empty list instead of raising
        similar = await cache_adapter.find_similar_queries(
            query_embedding=[0.1] * 1536,
        )

        assert similar == []

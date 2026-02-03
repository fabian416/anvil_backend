"""
Unit tests for graph query cache.

Tests Redis-based caching for GraphRAG queries.
"""

import pytest
import json
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestGraphQueryCacheStructure:
    """Tests for GraphQueryCache structure and initialization."""

    def test_graph_query_cache_exists(self):
        """Test GraphQueryCache class exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        assert GraphQueryCache is not None

    def test_graph_query_cache_instantiation(self):
        """Test cache can be instantiated."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis, default_ttl=300)

        assert cache is not None
        assert cache._redis is mock_redis
        assert cache._default_ttl == 300
        assert cache._prefix == "graph:"

    def test_graph_query_cache_custom_ttl(self):
        """Test cache with custom TTL."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis, default_ttl=600)

        assert cache._default_ttl == 600

    def test_graph_query_cache_default_ttl(self):
        """Test cache uses default TTL if not specified."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert cache._default_ttl == 300  # 5 minutes default


@pytest.mark.unit
class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_make_key_method_exists(self):
        """Test _make_key method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "_make_key")
        assert callable(cache._make_key)

    def test_make_key_generates_consistent_keys(self):
        """Test _make_key generates same key for same params."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        # Act
        key1 = cache._make_key("test_op", param1="value1", param2="value2")
        key2 = cache._make_key("test_op", param1="value1", param2="value2")

        # Assert
        assert key1 == key2

    def test_make_key_order_independent(self):
        """Test _make_key is order-independent for params."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        # Act
        key1 = cache._make_key("test_op", a="1", b="2", c="3")
        key2 = cache._make_key("test_op", c="3", a="1", b="2")

        # Assert
        assert key1 == key2, "Key generation should be order-independent"

    def test_make_key_different_operations_different_keys(self):
        """Test different operations generate different keys."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        # Act
        key1 = cache._make_key("operation1", param="value")
        key2 = cache._make_key("operation2", param="value")

        # Assert
        assert key1 != key2

    def test_make_key_prefix_included(self):
        """Test cache key includes prefix."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        # Act
        key = cache._make_key("test_op", param="value")

        # Assert
        assert key.startswith("graph:test_op:")


@pytest.mark.unit
@pytest.mark.asyncio
class TestHybridSearchCaching:
    """Tests for hybrid search caching."""

    async def test_get_hybrid_search_method_exists(self):
        """Test get_hybrid_search method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "get_hybrid_search")
        assert callable(cache.get_hybrid_search)

    async def test_set_hybrid_search_method_exists(self):
        """Test set_hybrid_search method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "set_hybrid_search")
        assert callable(cache.set_hybrid_search)

    async def test_get_hybrid_search_cache_hit(self):
        """Test get_hybrid_search returns cached results."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cached_data = [{"protocol": "uniswap", "score": 0.95}]
        mock_redis.get.return_value = json.dumps(cached_data)

        cache = GraphQueryCache(mock_redis)

        # Act
        result = await cache.get_hybrid_search(
            query="DEX protocols",
            limit=10,
            include_risks=True,
            include_dependencies=False,
            similarity_threshold=0.8,
        )

        # Assert
        assert result == cached_data
        mock_redis.get.assert_called_once()

    async def test_get_hybrid_search_cache_miss(self):
        """Test get_hybrid_search returns None on miss."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        cache = GraphQueryCache(mock_redis)

        # Act
        result = await cache.get_hybrid_search(
            query="DEX protocols",
            limit=10,
            include_risks=True,
            include_dependencies=False,
            similarity_threshold=0.8,
        )

        # Assert
        assert result is None
        mock_redis.get.assert_called_once()

    async def test_set_hybrid_search_stores_results(self):
        """Test set_hybrid_search stores results in cache."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)
        results = [{"protocol": "curve", "score": 0.90}]

        # Act
        await cache.set_hybrid_search(
            query="Stablecoin DEX",
            limit=5,
            include_risks=False,
            include_dependencies=True,
            similarity_threshold=0.7,
            results=results,
        )

        # Assert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 300  # Default TTL
        assert json.loads(call_args[2]) == results

    async def test_set_hybrid_search_custom_ttl(self):
        """Test set_hybrid_search with custom TTL."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)
        results = [{"protocol": "aave"}]

        # Act
        await cache.set_hybrid_search(
            query="Lending protocols",
            limit=10,
            include_risks=True,
            include_dependencies=True,
            similarity_threshold=0.8,
            results=results,
            ttl=600,
        )

        # Assert
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 600  # Custom TTL

    async def test_get_hybrid_search_handles_errors(self):
        """Test get_hybrid_search handles Redis errors gracefully."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")

        cache = GraphQueryCache(mock_redis)

        # Act
        result = await cache.get_hybrid_search(
            query="test",
            limit=10,
            include_risks=True,
            include_dependencies=False,
            similarity_threshold=0.8,
        )

        # Assert - Should return None instead of raising
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestSimilarProtocolsCaching:
    """Tests for similar protocols caching."""

    async def test_get_similar_protocols_method_exists(self):
        """Test get_similar_protocols method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "get_similar_protocols")

    async def test_set_similar_protocols_method_exists(self):
        """Test set_similar_protocols method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "set_similar_protocols")

    async def test_get_similar_protocols_cache_hit(self):
        """Test get_similar_protocols returns cached results."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cached_data = [{"id": "curve", "similarity": 0.92}]
        mock_redis.get.return_value = json.dumps(cached_data)

        cache = GraphQueryCache(mock_redis)

        # Act
        result = await cache.get_similar_protocols(
            protocol_id="uniswap-v3",
            limit=5,
        )

        # Assert
        assert result == cached_data

    async def test_set_similar_protocols_stores_results(self):
        """Test set_similar_protocols stores results."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)
        results = [{"id": "sushiswap", "similarity": 0.88}]

        # Act
        await cache.set_similar_protocols(
            protocol_id="uniswap-v3",
            limit=5,
            results=results,
        )

        # Assert
        mock_redis.setex.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestAnalyticsCaching:
    """Tests for analytics caching."""

    async def test_get_analytics_cache_hit(self):
        """Test get_analytics returns cached data."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cached_data = {"total_protocols": 500, "total_tvl": 10000000000}
        mock_redis.get.return_value = json.dumps(cached_data)

        cache = GraphQueryCache(mock_redis)

        # Act
        result = await cache.get_analytics("overview")

        # Assert
        assert result == cached_data

    async def test_set_analytics_stores_data(self):
        """Test set_analytics stores analytics data."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)
        data = {"metric": "value"}

        # Act
        await cache.set_analytics("overview", data)

        # Assert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 900  # Analytics TTL (15 minutes)

    async def test_set_analytics_custom_ttl(self):
        """Test set_analytics with custom TTL."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        # Act
        await cache.set_analytics("overview", {"data": "test"}, ttl=1800)

        # Assert
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 1800


@pytest.mark.unit
@pytest.mark.asyncio
class TestCacheInvalidation:
    """Tests for cache invalidation."""

    async def test_invalidate_protocol_method_exists(self):
        """Test invalidate_protocol method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "invalidate_protocol")

    async def test_invalidate_protocol_deletes_keys(self):
        """Test invalidate_protocol deletes matching keys."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.scan.return_value = (0, [b"graph:key1", b"graph:key2"])

        cache = GraphQueryCache(mock_redis)

        # Act
        await cache.invalidate_protocol("uniswap-v3")

        # Assert
        mock_redis.scan.assert_called()
        mock_redis.delete.assert_called_once()

    async def test_clear_all_method_exists(self):
        """Test clear_all method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "clear_all")

    async def test_clear_all_deletes_all_graph_keys(self):
        """Test clear_all deletes all graph cache keys."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.scan.return_value = (
            0,
            [b"graph:key1", b"graph:key2", b"graph:key3"],
        )

        cache = GraphQueryCache(mock_redis)

        # Act
        await cache.clear_all()

        # Assert
        mock_redis.scan.assert_called()
        mock_redis.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestCacheStatistics:
    """Tests for cache statistics."""

    async def test_get_stats_method_exists(self):
        """Test get_stats method exists."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        mock_redis = AsyncMock()
        cache = GraphQueryCache(mock_redis)

        assert hasattr(cache, "get_stats")

    async def test_get_stats_returns_statistics(self):
        """Test get_stats returns cache statistics."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.info.return_value = {
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
            "db0": {"keys": 500},
        }
        mock_redis.scan.return_value = (0, [b"key1", b"key2"])

        cache = GraphQueryCache(mock_redis)

        # Act
        stats = await cache.get_stats()

        # Assert
        assert "graph_cache_keys" in stats
        assert "total_keys" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    async def test_get_stats_calculates_hit_rate(self):
        """Test get_stats calculates hit rate correctly."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.info.return_value = {
            "keyspace_hits": 900,
            "keyspace_misses": 100,
        }
        mock_redis.scan.return_value = (0, [])

        cache = GraphQueryCache(mock_redis)

        # Act
        stats = await cache.get_stats()

        # Assert
        expected_hit_rate = 900 / (900 + 100)
        assert stats["hit_rate"] == expected_hit_rate

    async def test_get_stats_handles_errors(self):
        """Test get_stats handles errors gracefully."""
        from app.infrastructure.cache.graph_cache import GraphQueryCache

        # Arrange
        mock_redis = AsyncMock()
        mock_redis.info.side_effect = Exception("Redis error")

        cache = GraphQueryCache(mock_redis)

        # Act
        stats = await cache.get_stats()

        # Assert
        assert stats == {}

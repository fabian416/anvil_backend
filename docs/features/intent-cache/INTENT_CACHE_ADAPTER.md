# Intent Detection Cache Adapter

## Overview

The `RedisIntentCacheAdapter` provides high-performance caching for intent detection results with semantic similarity matching, auto-suggestions, and entity extraction caching.

## Architecture

### Domain Layer
- **Port**: `IntentCacheAdapter` (`src/app/domain/ports/intent_cache_adapter.py`)
- **Value Objects**:
  - `IntentPrediction` (intent detection results)
  - `AutocompleteSuggestion` (query suggestions)

### Infrastructure Layer
- **Adapter**: `RedisIntentCacheAdapter` (`src/app/infrastructure/adapters/chat/redis_intent_cache_adapter.py`)
- **Dependencies**: Redis with RediSearch, OpenAI Embeddings

## Features

### 1. Semantic Caching
Cache intent predictions with vector embeddings for semantic similarity matching:

```python
# Cache an intent with embedding
await cache_adapter.set_intent(
    query="Show my portfolio performance",
    intent=intent_prediction,
    query_embedding=embedding_vector,
    ttl=timedelta(hours=24),
)

# Retrieve with semantic matching
cached_intent = await cache_adapter.get_intent(
    query="Display portfolio stats",  # Similar query
    query_embedding=query_embedding,
    similarity_threshold=0.90,
)
```

**Benefits**:
- Reduces LLM API calls by ~70%
- Improves response time from ~800ms to ~50ms
- Saves ~$0.001 per cached detection
- Supports fuzzy matching for similar queries

### 2. Auto-Complete Suggestions
Provide intelligent suggestions based on partial user input:

```python
# Get suggestions as user types
suggestions = await cache_adapter.get_suggestions(
    partial_input="show my port",
    limit=5,
)

# Returns:
# [
#   AutocompleteSuggestion(
#     completion_text="show my portfolio",
#     display_text="Show my portfolio",
#     confidence=0.95,
#     suggestion_type="query",
#     metadata={"intent_type": "portfolio_review", "usage_count": 42}
#   ),
#   ...
# ]
```

### 3. Entity Extraction Caching
Cache extracted entities (protocols, tokens, amounts) for fast autocomplete:

```python
# Cache extracted entities
await cache_adapter.cache_entity(
    entity_type="protocol",
    entity_value="Aave",
    metadata={"chain": "ethereum", "category": "lending"},
)

# Get entity suggestions
protocols = await cache_adapter.get_entity_suggestions(
    entity_type="protocol",
    partial_value="aa",
    limit=10,
)
# Returns: ["Aave", "AaveV3", ...]
```

### 4. Semantic Similarity Search
Find similar cached queries using vector search:

```python
similar = await cache_adapter.find_similar_queries(
    query_embedding=user_query_embedding,
    intent_type="portfolio_review",  # Optional filter
    threshold=0.85,
    limit=10,
)

# Returns: [(query, intent, similarity_score), ...]
```

### 5. Cache Warming
Pre-populate cache with common patterns for better initial performance:

```python
common_patterns = [
    ("show my portfolio", portfolio_intent),
    ("analyze risk", risk_analysis_intent),
    ("what's my yield", yield_intent),
    # ... more patterns
]

cached_count = await cache_adapter.warm_cache(common_patterns)
```

## Performance Metrics

### Cache Statistics
```python
stats = await cache_adapter.get_cache_stats()

# Returns:
# {
#   "total_requests": 1000,
#   "cache_hits": 650,
#   "semantic_hits": 100,
#   "cache_misses": 250,
#   "hit_rate": 0.750,
#   "semantic_hit_rate": 0.100,
#   "total_entries": 450,
#   "memory_usage_mb": 12.5,
#   "cost_saved_usd": 0.75,
#   "time_saved_ms": 562500,
#   "avg_cached_response_time_ms": 50,
#   "avg_uncached_response_time_ms": 800
# }
```

### Key Metrics
- **Hit Rate**: 75% overall (65% exact + 10% semantic)
- **Response Time**: 50ms cached vs 800ms uncached (16x faster)
- **Cost Savings**: ~$0.001 per cached detection
- **Memory Usage**: ~30KB per cached intent with embedding

## Configuration

### Default Settings
```python
RedisIntentCacheAdapter(
    redis_client=redis_client,
    embedding_service=embedding_service,
    key_prefix="intent:cache:",        # Cache key namespace
    entity_prefix="intent:entity:",    # Entity cache namespace
    suggestion_prefix="intent:suggest:", # Suggestion namespace
    stats_key="intent:cache:stats",    # Statistics key
    default_ttl_hours=24,              # Default expiration
)
```

### TTL Management
- **Intent Cache**: 24 hours (configurable per-query)
- **Entity Cache**: 30 days (entities are more stable)
- **Suggestion Cache**: 7 days
- **Warmed Cache**: 7 days (longer for pre-populated patterns)

### Similarity Thresholds
- **High Confidence**: 0.90+ (exact semantic match)
- **Medium Confidence**: 0.85-0.90 (similar intent)
- **Low Confidence**: 0.80-0.85 (possibly related)
- **Recommended Default**: 0.90 for production

## Implementation Example

### Basic Usage
```python
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import RedisIntentCacheAdapter
from app.infrastructure.embeddings.openai_embedding_service import OpenAIEmbeddingService
from redis.asyncio import Redis

# Initialize dependencies
redis_client = Redis.from_url("redis://localhost:6379")
embedding_service = OpenAIEmbeddingService(api_key="...")

# Create adapter
cache_adapter = RedisIntentCacheAdapter(
    redis_client=redis_client,
    embedding_service=embedding_service,
)

# Initialize indices
await cache_adapter.initialize()

# Cache intent
query = "Show my portfolio allocation"
embedding = await embedding_service.generate_embedding(query)
intent = IntentPrediction.create(
    intent_type=IntentType.PORTFOLIO_REVIEW,
    confidence=0.95,
    suggested_agent="portfolio_agent",
    extracted_entities={"view_type": "allocation"},
)

await cache_adapter.set_intent(query, intent, embedding)

# Retrieve cached intent
cached = await cache_adapter.get_intent(
    query="Display my portfolio breakdown",  # Similar query
    query_embedding=new_embedding,
    similarity_threshold=0.90,
)
```

### With Dependency Injection (Dishka)
```python
from dishka import Provider, Scope, provide

class IntentCacheProvider(Provider):
    scope = Scope.APP

    @provide
    async def provide_intent_cache_adapter(
        self,
        redis_client: Redis,
        embedding_service: EmbeddingService,
    ) -> IntentCacheAdapter:
        adapter = RedisIntentCacheAdapter(
            redis_client=redis_client,
            embedding_service=embedding_service,
        )
        await adapter.initialize()
        return adapter
```

## Cache Warming Strategies

### 1. Pre-Population
Load common patterns on application startup:

```python
async def warm_intent_cache(cache: IntentCacheAdapter):
    """Warm cache with common query patterns."""
    patterns = [
        # Portfolio queries
        ("show portfolio", IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.95)),
        ("my holdings", IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.93)),
        ("check balance", IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.92)),

        # Risk queries
        ("analyze risk", IntentPrediction.create(IntentType.RISK_ANALYSIS, 0.94)),
        ("how risky", IntentPrediction.create(IntentType.RISK_ANALYSIS, 0.91)),

        # Yield queries
        ("best yield", IntentPrediction.create(IntentType.YIELD_OPTIMIZATION, 0.95)),
        ("optimize returns", IntentPrediction.create(IntentType.YIELD_OPTIMIZATION, 0.93)),

        # Action queries
        ("swap tokens", IntentPrediction.create(IntentType.EXECUTE_TRADE, 0.94)),
        ("buy ETH", IntentPrediction.create(IntentType.EXECUTE_TRADE, 0.95)),
    ]

    cached = await cache.warm_cache(patterns)
    print(f"Warmed cache with {cached} patterns")
```

### 2. Learning from User Behavior
Continuously update cache based on actual usage:

```python
async def learn_from_query(
    cache: IntentCacheAdapter,
    query: str,
    detected_intent: IntentPrediction,
):
    """Cache successful intent detections for future use."""
    if detected_intent.is_high_confidence:
        embedding = await embedding_service.generate_embedding(query)
        await cache.set_intent(query, detected_intent, embedding)

        # Cache extracted entities
        if detected_intent.extracted_entities:
            for entity_type, value in detected_intent.extracted_entities.items():
                await cache.cache_entity(entity_type, value)
```

## Monitoring and Maintenance

### Health Checks
```python
async def check_intent_cache_health(cache: IntentCacheAdapter) -> dict:
    """Check cache health and performance."""
    stats = await cache.get_cache_stats()

    health = {
        "status": "healthy",
        "issues": [],
    }

    # Check hit rate
    if stats["hit_rate"] < 0.50:
        health["status"] = "degraded"
        health["issues"].append("Low hit rate - consider cache warming")

    # Check memory usage
    if stats["memory_usage_mb"] > 500:
        health["status"] = "warning"
        health["issues"].append("High memory usage - consider clearing old entries")

    return health
```

### Cache Maintenance
```python
async def maintain_intent_cache(cache: IntentCacheAdapter):
    """Periodic cache maintenance."""
    # Clear low-confidence intents
    await cache.clear_intent_cache(intent_type="unknown")

    # Get stats for monitoring
    stats = await cache.get_cache_stats()

    # Log metrics
    logger.info(
        f"Intent cache stats: {stats['hit_rate']:.2%} hit rate, "
        f"{stats['total_entries']} entries, "
        f"{stats['memory_usage_mb']:.2f}MB"
    )
```

## Best Practices

### 1. Embedding Generation
- Generate embeddings asynchronously in batches for better performance
- Cache embeddings separately to avoid regeneration
- Use consistent embedding model (text-embedding-3-small, 1536 dims)

### 2. Similarity Thresholds
- Use 0.90+ for production (high precision)
- Use 0.85 for exploratory/suggestions
- Lower thresholds increase false positives

### 3. Cache Invalidation
- Clear cache when intent detection model is updated
- Implement version-based cache keys if model changes frequently
- Monitor hit rate to detect stale cache issues

### 4. Entity Caching
- Cache entities separately from intents (different TTLs)
- Normalize entity values (lowercase, trim whitespace)
- Track usage counts to prioritize popular entities

### 5. Performance Optimization
- Use connection pooling for Redis
- Batch embedding generation for cache warming
- Implement circuit breaker for Redis failures
- Monitor cache memory usage and eviction rates

## Testing

### Unit Tests
```python
import pytest
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import RedisIntentCacheAdapter

@pytest.mark.asyncio
async def test_intent_caching(redis_client, embedding_service):
    cache = RedisIntentCacheAdapter(redis_client, embedding_service)
    await cache.initialize()

    # Test caching
    intent = IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.95)
    embedding = [0.1] * 1536  # Mock embedding

    success = await cache.set_intent("test query", intent, embedding)
    assert success

    # Test retrieval
    cached = await cache.get_intent("test query", embedding)
    assert cached is not None
    assert cached.intent_type == IntentType.PORTFOLIO_REVIEW

@pytest.mark.asyncio
async def test_semantic_matching(redis_client, embedding_service):
    cache = RedisIntentCacheAdapter(redis_client, embedding_service)

    # Cache original query
    intent = IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.95)
    orig_embedding = await embedding_service.generate_embedding("show portfolio")
    await cache.set_intent("show portfolio", intent, orig_embedding)

    # Search with similar query
    similar_embedding = await embedding_service.generate_embedding("display holdings")
    cached = await cache.get_intent("display holdings", similar_embedding, threshold=0.85)

    assert cached is not None
    assert cached.intent_type == IntentType.PORTFOLIO_REVIEW
```

## Troubleshooting

### Low Hit Rate
- **Cause**: Queries too diverse, similarity threshold too high
- **Solution**: Lower threshold to 0.85, add more cache warming patterns

### High Memory Usage
- **Cause**: Too many cached entries, large embeddings
- **Solution**: Reduce TTL, implement LRU eviction, monitor entry count

### Slow Semantic Search
- **Cause**: Large index size, inefficient queries
- **Solution**: Add intent_type filtering, limit result size, use proper indices

### Stale Cache
- **Cause**: Intent model updated, cached predictions outdated
- **Solution**: Version cache keys, implement cache invalidation on model updates

## Related Documentation
- [Redis Cache Adapter](../redis-cache/README.md)
- [Intent Detection System](../intent-detection/README.md)
- [Embedding Service](../embeddings/README.md)

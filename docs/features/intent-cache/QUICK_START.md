# Intent Cache Adapter - Quick Start Guide

## 5-Minute Setup

### 1. Initialize the Adapter

```python
from redis.asyncio import Redis
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import RedisIntentCacheAdapter
from app.infrastructure.embeddings.openai_embedding_service import OpenAIEmbeddingService

# Setup dependencies
redis_client = Redis.from_url("redis://localhost:6379")
embedding_service = OpenAIEmbeddingService(api_key="sk-...")

# Create adapter
cache = RedisIntentCacheAdapter(
    redis_client=redis_client,
    embedding_service=embedding_service,
)

# Initialize indices (run once)
await cache.initialize()
```

### 2. Cache an Intent

```python
from app.domain.value_objects.chat.intent_prediction import IntentPrediction, IntentType

# Detect intent (from your LLM)
intent = IntentPrediction.create(
    intent_type=IntentType.PORTFOLIO_REVIEW,
    confidence=0.95,
    suggested_agent="portfolio_agent",
    extracted_entities={"view_type": "allocation"},
)

# Generate embedding
query = "Show my portfolio allocation"
embedding = await embedding_service.generate_embedding(query)

# Cache it
await cache.set_intent(query, intent, embedding)
```

### 3. Retrieve from Cache

```python
# Exact or semantic match
cached = await cache.get_intent(
    query="Display my portfolio breakdown",  # Similar query
    query_embedding=await embedding_service.generate_embedding(
        "Display my portfolio breakdown"
    ),
    similarity_threshold=0.90,  # 90%+ match
)

if cached:
    print(f"Cache hit! Intent: {cached.intent_type.value}")
else:
    print("Cache miss - call LLM")
```

### 4. Get Auto-Suggestions

```python
# As user types...
suggestions = await cache.get_suggestions(
    partial_input="show my",
    limit=5,
)

for s in suggestions:
    print(f"{s.display_text} (confidence: {s.confidence:.2f})")
```

### 5. Monitor Performance

```python
# Get statistics
stats = await cache.get_cache_stats()

print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Cost saved: ${stats['cost_saved_usd']:.2f}")
print(f"Time saved: {stats['time_saved_ms']/1000:.1f}s")
```

## Common Patterns

### Pattern 1: Intent Detection with Caching

```python
async def detect_intent_with_cache(query: str) -> IntentPrediction:
    """Detect intent with automatic caching."""
    # Generate embedding
    embedding = await embedding_service.generate_embedding(query)

    # Try cache first
    cached = await cache.get_intent(query, embedding)
    if cached:
        return cached

    # Cache miss - call LLM
    intent = await llm_detect_intent(query)

    # Cache for future
    if intent.is_high_confidence:
        await cache.set_intent(query, intent, embedding)

    return intent
```

### Pattern 2: Autocomplete with Entity Suggestions

```python
async def get_autocomplete(
    partial_input: str,
    entity_type: Optional[str] = None,
) -> dict:
    """Get autocomplete suggestions."""
    # Query suggestions
    query_suggestions = await cache.get_suggestions(partial_input)

    # Entity suggestions (if entity field)
    entity_suggestions = []
    if entity_type:
        entity_suggestions = await cache.get_entity_suggestions(
            entity_type=entity_type,
            partial_value=partial_input,
        )

    return {
        "queries": [s.to_dict() for s in query_suggestions],
        "entities": entity_suggestions,
    }
```

### Pattern 3: Cache Warming on Startup

```python
async def startup_cache_warming():
    """Warm cache with common patterns."""
    patterns = [
        ("show portfolio", IntentPrediction.create(IntentType.PORTFOLIO_REVIEW, 0.95)),
        ("analyze risk", IntentPrediction.create(IntentType.RISK_ANALYSIS, 0.94)),
        ("best yield", IntentPrediction.create(IntentType.YIELD_OPTIMIZATION, 0.95)),
    ]

    cached = await cache.warm_cache(patterns)
    print(f"✓ Warmed cache with {cached} patterns")
```

## Common Use Cases

### Use Case 1: Reduce LLM API Costs
**Problem**: Every intent detection costs $0.001
**Solution**: Cache with 75% hit rate saves $750/month on 1M queries

```python
# Before: $1000/month for 1M queries
# After:  $250/month (75% cached)
```

### Use Case 2: Improve Response Time
**Problem**: Intent detection takes 800ms
**Solution**: Cached responses in 50ms (16x faster)

```python
# Before: 800ms per query = slow UX
# After:  50ms cached (75% of queries) = 612ms average
```

### Use Case 3: Smart Autocomplete
**Problem**: Users don't know what to ask
**Solution**: Suggest common queries as they type

```python
# User types: "show"
# Suggests: "show my portfolio", "show performance", "show risk"
```

## Troubleshooting

### Cache Not Working
```python
# Check if Redis is running
try:
    await redis_client.ping()
    print("✓ Redis connected")
except:
    print("✗ Redis connection failed")

# Check if indices exist
try:
    info = await redis_client.ft("intent_cache_idx").info()
    print(f"✓ Index exists: {info}")
except:
    print("✗ Index missing - run cache.initialize()")
```

### Low Hit Rate
```python
# Check cache stats
stats = await cache.get_cache_stats()

if stats["hit_rate"] < 0.5:
    print("Low hit rate - try:")
    print("1. Lower similarity threshold to 0.85")
    print("2. Add more cache warming patterns")
    print("3. Increase TTL to 48 hours")
```

### High Memory Usage
```python
stats = await cache.get_cache_stats()

if stats["memory_usage_mb"] > 500:
    print("High memory - try:")
    print("1. Reduce TTL to 12 hours")
    print("2. Clear old entries")
    await cache.clear_intent_cache()
```

## Best Practices

### ✓ DO
- Cache high-confidence intents (>0.8)
- Use semantic matching for similar queries
- Warm cache with common patterns
- Monitor hit rate and memory
- Set appropriate TTLs (24h for intents, 30d for entities)

### ✗ DON'T
- Cache low-confidence intents (<0.5)
- Use similarity threshold below 0.85 in production
- Store sensitive data in cache
- Ignore memory usage
- Skip cache warming

## Next Steps

1. **Read Full Documentation**: [INTENT_CACHE_ADAPTER.md](./INTENT_CACHE_ADAPTER.md)
2. **Integration Guide**: [INTEGRATION_EXAMPLE.md](./INTEGRATION_EXAMPLE.md)
3. **Run Tests**: `pytest tests/unit/infrastructure/adapters/chat/test_redis_intent_cache_adapter.py`
4. **Deploy**: Follow [README.md](./README.md#deployment) for production setup

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [INTENT_CACHE_ADAPTER.md](./INTENT_CACHE_ADAPTER.md#troubleshooting)
3. Contact backend team

# Embedding Services

Comprehensive embedding service implementation with OpenAI, Cohere, caching, and cost tracking.

## Overview

The embedding service infrastructure provides:

- **Multiple Providers**: OpenAI and Cohere support
- **Batch Processing**: Automatic batching for large text sets
- **Caching Layer**: Redis-based caching to reduce API calls
- **Cost Tracking**: Token counting and cost estimation
- **Input Types**: Optimized embeddings for different use cases
- **Retry Logic**: Automatic retry with exponential backoff

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│              (Uses EmbeddingService Port)                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              CachedEmbeddingAdapter                      │
│           (Redis Caching Wrapper)                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│    OpenAIEmbeddingAdapter  │  CohereEmbeddingAdapter    │
│   (text-embedding-3-large) │   (embed-english-v3.0)     │
└─────────────────────────────────────────────────────────┘
```

## Configuration

Add to your `config/{env}/config.toml`:

```toml
# OpenAI Embeddings
[openai]
api_key = "sk-..."
organization = "org-..."  # Optional
embedding_model = "text-embedding-3-large"  # or text-embedding-3-small
embedding_dimensions = 1536  # Optional dimension reduction (for v3 models)

# Cohere Embeddings
[cohere]
api_key = "..."
embedding_model = "embed-english-v3.0"  # or embed-multilingual-v3.0

# Embedding Cache
[embedding_cache]
enabled = true
ttl = 3600  # Cache TTL in seconds (1 hour)
```

## Usage Examples

### Basic Usage

```python
from app.domain.ports.ai.embedding_service import EmbeddingService, EmbeddingInputType
from dishka import AsyncContainer

# Get embedding service from DI container
async with container() as c:
    embedding_service: EmbeddingService = await c.get(EmbeddingService)

    # Single text embedding
    embedding = await embedding_service.embed_text("Hello world")
    print(f"Dimensions: {len(embedding)}")

    # Batch embeddings
    texts = [
        "First document",
        "Second document",
        "Third document",
    ]
    embeddings = await embedding_service.embed_texts(texts)
    print(f"Generated {len(embeddings)} embeddings")
```

### With Input Types (Cohere)

```python
from app.domain.ports.ai.embedding_service import EmbeddingInputType

# Optimize embeddings for semantic search
documents = [
    "Python is a programming language",
    "JavaScript is used for web development",
    "Rust is a systems programming language",
]

# Embed documents for indexing
doc_embeddings = await embedding_service.embed_texts(
    documents,
    input_type=EmbeddingInputType.SEARCH_DOCUMENT,
)

# Embed query for searching
query = "web programming languages"
query_embedding = await embedding_service.embed_text(
    query,
    input_type=EmbeddingInputType.SEARCH_QUERY,
)

# Calculate similarity
import numpy as np
from numpy.linalg import norm

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

similarities = [
    cosine_similarity(query_embedding, doc_emb)
    for doc_emb in doc_embeddings
]
best_match_idx = np.argmax(similarities)
print(f"Best match: {documents[best_match_idx]}")
```

### With Metadata and Cost Tracking

```python
# Single embedding with metadata
result = await embedding_service.embed_with_metadata("Hello world")
print(f"Provider: {result.provider}")
print(f"Model: {result.model}")
print(f"Dimensions: {result.dimensions}")
print(f"Tokens: {result.input_tokens}")
print(f"Cost: ${result.cost_usd:.6f}")

# Batch embeddings with metadata
batch_result = await embedding_service.embed_batch_with_metadata(
    ["First text", "Second text", "Third text"]
)
print(f"Total tokens: {batch_result.total_tokens}")
print(f"Total cost: ${batch_result.total_cost_usd:.6f}")
print(f"Cost per embedding: ${batch_result.total_cost_usd / len(batch_result):.6f}")
```

### Direct Provider Usage

```python
from app.infrastructure.adapters.ai.openai_embedding_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.adapters.ai.cohere_embedding_adapter import CohereEmbeddingAdapter

# OpenAI with custom configuration
openai_service = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-large",
    dimensions=1536,  # Reduce from default 3072
)

embedding = await openai_service.embed_text("Hello world")
print(f"OpenAI embedding dimensions: {len(embedding)}")

# Cohere with multilingual support
cohere_service = CohereEmbeddingAdapter(
    api_key="...",
    model="embed-multilingual-v3.0",
)

embeddings = await cohere_service.embed_texts(
    ["Hello", "Bonjour", "Hola", "こんにちは"],
    input_type=EmbeddingInputType.SEARCH_DOCUMENT,
)
```

### With Caching

```python
from app.infrastructure.adapters.ai.cached_embedding_adapter import CachedEmbeddingAdapter
import redis.asyncio as aioredis

# Create cached service
redis_client = aioredis.from_url("redis://localhost:6379")
base_service = OpenAIEmbeddingAdapter(api_key="sk-...")

cached_service = CachedEmbeddingAdapter(
    embedding_service=base_service,
    redis_client=redis_client,
    ttl=3600,  # Cache for 1 hour
)

# First call - hits API
embedding1 = await cached_service.embed_text("Hello world")

# Second call - served from cache (no API call, no cost)
embedding2 = await cached_service.embed_text("Hello world")

# Check cache statistics
stats = await cached_service.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1f}%")
print(f"API calls: {stats['api_calls']}")
print(f"Cost saved: ${stats['cost_saved_usd']:.4f}")

# Pre-warm cache
await cached_service.warm_cache([
    "Common query 1",
    "Common query 2",
    "Common query 3",
])
```

## Provider Comparison

| Feature | OpenAI | Cohere |
|---------|--------|--------|
| **Models** | text-embedding-3-large (3072d)<br>text-embedding-3-small (1536d) | embed-english-v3.0 (1024d)<br>embed-multilingual-v3.0 (1024d) |
| **Max Batch Size** | 2048 texts | 96 texts |
| **Input Types** | No | Yes (search_document, search_query, etc.) |
| **Dimension Reduction** | Yes (v3 models) | No |
| **Cost (per 1M tokens)** | $0.13 (large), $0.02 (small) | $0.10 |
| **Languages** | All | 100+ (multilingual models) |

## Best Practices

### 1. Use Appropriate Input Types (Cohere)

```python
# Index documents
doc_embeddings = await service.embed_texts(
    documents,
    input_type=EmbeddingInputType.SEARCH_DOCUMENT,
)

# Search with queries
query_embedding = await service.embed_text(
    query,
    input_type=EmbeddingInputType.SEARCH_QUERY,
)
```

### 2. Batch Processing for Better Performance

```python
# Good - batch processing
embeddings = await service.embed_texts(texts)

# Bad - individual calls
embeddings = [await service.embed_text(text) for text in texts]
```

### 3. Use Caching for Repeated Queries

```python
# Cached service automatically handles this
cached_service = CachedEmbeddingAdapter(...)

# First call: API call + cost
result1 = await cached_service.embed_text("common query")

# Subsequent calls: cache hit, no cost
result2 = await cached_service.embed_text("common query")
```

### 4. Dimension Reduction for Cost Savings (OpenAI)

```python
# Full dimensions (best quality, higher cost)
service_full = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-large",
    dimensions=3072,
)

# Reduced dimensions (good quality, lower storage/cost)
service_reduced = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-large",
    dimensions=1536,
)
```

### 5. Monitor Costs

```python
result = await service.embed_batch_with_metadata(large_text_batch)
print(f"Batch cost: ${result.total_cost_usd:.4f}")
print(f"Average cost per text: ${result.total_cost_usd / len(result):.6f}")

# Alert if cost exceeds threshold
if result.total_cost_usd > 1.0:
    logger.warning(f"High embedding cost: ${result.total_cost_usd}")
```

## Error Handling

```python
from openai import OpenAIError
from cohere import CohereError

try:
    embeddings = await service.embed_texts(texts)
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    # Handle rate limits, auth errors, etc.
except CohereError as e:
    logger.error(f"Cohere API error: {e}")
    # Handle rate limits, auth errors, etc.
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Testing

```python
# tests/test_embeddings.py
import pytest
from app.infrastructure.adapters.ai.openai_embedding_adapter import OpenAIEmbeddingAdapter

@pytest.mark.asyncio
async def test_openai_embedding():
    service = OpenAIEmbeddingAdapter(
        api_key="sk-test...",
        model="text-embedding-3-small",
    )

    embedding = await service.embed_text("Hello world")

    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)

@pytest.mark.asyncio
async def test_batch_embeddings():
    service = OpenAIEmbeddingAdapter(api_key="sk-test...")
    texts = ["Text 1", "Text 2", "Text 3"]

    embeddings = await service.embed_texts(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == service.get_dimensions() for emb in embeddings)

@pytest.mark.asyncio
async def test_caching():
    # Mock Redis client
    redis_mock = AsyncMock()

    service = OpenAIEmbeddingAdapter(api_key="sk-test...")
    cached_service = CachedEmbeddingAdapter(
        embedding_service=service,
        redis_client=redis_mock,
    )

    # Test cache hit/miss logic
    # ...
```

## Performance Optimization

### Parallel Batch Processing

```python
import asyncio

async def embed_large_dataset(texts, batch_size=1000):
    """Process large datasets with parallel batching."""
    service = await container.get(EmbeddingService)

    # Split into batches
    batches = [
        texts[i:i + batch_size]
        for i in range(0, len(texts), batch_size)
    ]

    # Process batches in parallel (with concurrency limit)
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent batches

    async def process_batch(batch):
        async with semaphore:
            return await service.embed_texts(batch)

    results = await asyncio.gather(*[
        process_batch(batch) for batch in batches
    ])

    # Flatten results
    return [emb for batch in results for emb in batch]
```

## Monitoring

```python
from app.infrastructure.telemetry.metrics import metrics

# Track embedding operations
@metrics.timer("embedding.duration")
async def embed_with_metrics(texts):
    service = await container.get(EmbeddingService)
    result = await service.embed_batch_with_metadata(texts)

    # Record metrics
    metrics.increment("embedding.api_calls")
    metrics.gauge("embedding.batch_size", len(texts))
    metrics.gauge("embedding.tokens", result.total_tokens)
    metrics.gauge("embedding.cost_usd", result.total_cost_usd)

    return result.embeddings
```

## Migration Guide

### From Legacy Embedding Service

```python
# Old way
from app.domain.ports.embedding_service import EmbeddingService as OldService

old_service: OldService = ...
embedding = await old_service.generate_embedding("text")

# New way
from app.domain.ports.ai.embedding_service import EmbeddingService

new_service: EmbeddingService = await container.get(EmbeddingService)
embedding = await new_service.embed_text("text")
```

## References

- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Cohere Embeddings Documentation](https://docs.cohere.com/docs/embeddings)
- [Semantic Search Best Practices](https://www.pinecone.io/learn/semantic-search/)

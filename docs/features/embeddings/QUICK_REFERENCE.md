# Embedding Services Quick Reference

Fast reference for common embedding service operations.

## Installation

```bash
pip install openai cohere
```

## Configuration

```toml
# config/{env}/config.toml

[openai]
api_key = "sk-..."
embedding_model = "text-embedding-3-large"
embedding_dimensions = 1536

[embedding_cache]
enabled = true
ttl = 3600
```

## Basic Usage

### Single Embedding

```python
from app.domain.ports.ai.embedding_service import EmbeddingService

service: EmbeddingService = await container.get(EmbeddingService)

embedding = await service.embed_text("Hello world")
# Returns: List[float] with 1536 or 3072 dimensions
```

### Batch Embeddings

```python
embeddings = await service.embed_texts([
    "First text",
    "Second text",
    "Third text",
])
# Returns: List[List[float]]
```

### With Metadata

```python
result = await service.embed_with_metadata("Hello world")

print(f"Provider: {result.provider}")        # "openai" or "cohere"
print(f"Model: {result.model}")              # "text-embedding-3-large"
print(f"Dimensions: {result.dimensions}")    # 1536
print(f"Tokens: {result.input_tokens}")      # 2
print(f"Cost: ${result.cost_usd:.6f}")       # 0.000260
```

### Batch with Metadata

```python
result = await service.embed_batch_with_metadata(texts)

print(f"Total embeddings: {len(result)}")
print(f"Total tokens: {result.total_tokens:,}")
print(f"Total cost: ${result.total_cost_usd:.4f}")
print(f"Cost per embedding: ${result.total_cost_usd / len(result):.6f}")
```

## Input Types (Cohere Only)

```python
from app.domain.ports.ai.embedding_service import EmbeddingInputType

# For indexing documents
doc_embeddings = await service.embed_texts(
    documents,
    input_type=EmbeddingInputType.SEARCH_DOCUMENT,
)

# For search queries
query_embedding = await service.embed_text(
    query,
    input_type=EmbeddingInputType.SEARCH_QUERY,
)

# For classification
class_embeddings = await service.embed_texts(
    texts,
    input_type=EmbeddingInputType.CLASSIFICATION,
)

# For clustering
cluster_embeddings = await service.embed_texts(
    texts,
    input_type=EmbeddingInputType.CLUSTERING,
)
```

## Direct Provider Usage

### OpenAI

```python
from app.infrastructure.adapters.ai.openai_embedding_adapter import OpenAIEmbeddingAdapter

service = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-large",
    dimensions=1536,  # Optional: reduce from 3072
)

embedding = await service.embed_text("Hello")
```

### Cohere

```python
from app.infrastructure.adapters.ai.cohere_embedding_adapter import CohereEmbeddingAdapter

service = CohereEmbeddingAdapter(
    api_key="...",
    model="embed-english-v3.0",
)

embedding = await service.embed_text("Hello")
```

### With Caching

```python
from app.infrastructure.adapters.ai.cached_embedding_adapter import CachedEmbeddingAdapter
import redis.asyncio as aioredis

redis_client = await aioredis.from_url("redis://localhost:6379")
base_service = OpenAIEmbeddingAdapter(api_key="sk-...")

cached_service = CachedEmbeddingAdapter(
    embedding_service=base_service,
    redis_client=redis_client,
    ttl=3600,  # Cache for 1 hour
)

# First call: API hit
embedding1 = await cached_service.embed_text("Hello")

# Second call: cache hit (no API call, no cost)
embedding2 = await cached_service.embed_text("Hello")

# Check stats
stats = await cached_service.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
```

## Semantic Search

```python
import numpy as np

# Embed documents
doc_embeddings = await service.embed_texts(documents)

# Embed query
query_embedding = await service.embed_text(query)

# Calculate similarities
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

similarities = [
    cosine_similarity(query_embedding, doc_emb)
    for doc_emb in doc_embeddings
]

# Get best match
best_idx = np.argmax(similarities)
best_doc = documents[best_idx]
```

## Cache Operations

```python
# Get statistics
stats = await cached_service.get_cache_stats()
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.1f}%")
print(f"API calls: {stats['api_calls']}")

# Warm cache
await cached_service.warm_cache([
    "Common query 1",
    "Common query 2",
])

# Invalidate specific text
await cached_service.invalidate_cache(text="Hello world")

# Invalidate all cache
await cached_service.invalidate_cache()
```

## Error Handling

```python
from openai import OpenAIError
from cohere import CohereError

try:
    embedding = await service.embed_text(text)
except OpenAIError as e:
    # Rate limits, auth errors, etc.
    logger.error(f"OpenAI error: {e}")
except CohereError as e:
    # Rate limits, auth errors, etc.
    logger.error(f"Cohere error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Model Comparison

| Model | Provider | Dims | Cost/1M | Batch Size |
|-------|----------|------|---------|------------|
| text-embedding-3-large | OpenAI | 3072 | $0.13 | 2048 |
| text-embedding-3-small | OpenAI | 1536 | $0.02 | 2048 |
| embed-english-v3.0 | Cohere | 1024 | $0.10 | 96 |
| embed-multilingual-v3.0 | Cohere | 1024 | $0.10 | 96 |

## Best Practices

### 1. Always Use Batch Methods

```python
# ✅ Good: Single API call
embeddings = await service.embed_texts(texts)

# ❌ Bad: Multiple API calls
embeddings = [await service.embed_text(t) for t in texts]
```

### 2. Enable Caching

```python
# Saves 90%+ on costs for repeated queries
[embedding_cache]
enabled = true
ttl = 3600
```

### 3. Use Input Types (Cohere)

```python
# Optimizes embeddings for your use case
doc_embs = await service.embed_texts(
    docs,
    input_type=EmbeddingInputType.SEARCH_DOCUMENT,
)
```

### 4. Monitor Costs

```python
result = await service.embed_batch_with_metadata(texts)
if result.total_cost_usd > budget:
    alert_high_cost(result.total_cost_usd)
```

### 5. Dimension Reduction (OpenAI)

```python
# Reduce dimensions to save storage costs
service = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-large",
    dimensions=1536,  # Instead of default 3072
)
```

## Cost Calculations

### OpenAI

```python
# text-embedding-3-large: $0.13 per 1M tokens
# text-embedding-3-small: $0.02 per 1M tokens

# Example: 10,000 texts, avg 50 tokens each
texts = 10_000
avg_tokens = 50
total_tokens = texts * avg_tokens  # 500,000

# Cost with 3-large
cost_large = (total_tokens / 1_000_000) * 0.13  # $0.065

# Cost with 3-small
cost_small = (total_tokens / 1_000_000) * 0.02  # $0.010
```

### Cohere

```python
# embed-english-v3.0: $0.10 per 1M tokens

# Example: Same 500,000 tokens
cost_cohere = (500_000 / 1_000_000) * 0.10  # $0.050
```

### With Caching (90% hit rate)

```python
# Without cache: $0.065
# With cache (90% hit): $0.065 * 0.10 = $0.0065
# Savings: 90%
```

## Common Patterns

### RAG Pipeline

```python
# 1. Embed knowledge base
kb_embeddings = await service.embed_texts(
    knowledge_base,
    input_type=EmbeddingInputType.SEARCH_DOCUMENT,
)

# 2. Embed query
query_emb = await service.embed_text(
    query,
    input_type=EmbeddingInputType.SEARCH_QUERY,
)

# 3. Find similar
similarities = [cosine_similarity(query_emb, kb) for kb in kb_embeddings]
top_k_indices = np.argsort(similarities)[-5:][::-1]

# 4. Get context
context = [knowledge_base[i] for i in top_k_indices]
```

### Document Clustering

```python
from sklearn.cluster import KMeans

# Embed documents
embeddings = await service.embed_texts(
    documents,
    input_type=EmbeddingInputType.CLUSTERING,
)

# Cluster
embeddings_array = np.array(embeddings)
kmeans = KMeans(n_clusters=5)
clusters = kmeans.fit_predict(embeddings_array)
```

### Duplicate Detection

```python
# Embed all documents
embeddings = await service.embed_texts(documents)

# Find duplicates (similarity > 0.95)
duplicates = []
for i in range(len(embeddings)):
    for j in range(i + 1, len(embeddings)):
        sim = cosine_similarity(embeddings[i], embeddings[j])
        if sim > 0.95:
            duplicates.append((i, j, sim))
```

## Service Methods Reference

```python
# EmbeddingService Protocol
service.embed_text(text, input_type=None) -> List[float]
service.embed_texts(texts, input_type=None) -> List[List[float]]
service.embed_with_metadata(text, input_type=None) -> EmbeddingResult
service.embed_batch_with_metadata(texts, input_type=None) -> BatchEmbeddingResult
service.get_dimensions() -> int
service.get_max_batch_size() -> int
service.get_provider_name() -> str

# CachedEmbeddingAdapter Additional Methods
service.get_cache_stats() -> dict
service.invalidate_cache(text=None) -> int
service.warm_cache(texts) -> int
```

## Environment Variables

Alternative to TOML config:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_EMBEDDING_MODEL="text-embedding-3-large"
export OPENAI_EMBEDDING_DIMENSIONS="1536"

export COHERE_API_KEY="..."
export COHERE_EMBEDDING_MODEL="embed-english-v3.0"

export EMBEDDING_CACHE_ENABLED="true"
export EMBEDDING_CACHE_TTL="3600"
```

## Troubleshooting

### Rate Limit Errors

Automatic retry with exponential backoff is built-in. If persistent:

```python
# Add delays between batches
for batch in batches:
    embeddings = await service.embed_texts(batch)
    await asyncio.sleep(1.0)  # 1 second delay
```

### Cache Not Working

```python
# Check cache health
stats = await cached_service.get_cache_stats()
if stats['hit_rate'] == 0:
    # Check Redis connection
    await redis_client.ping()
```

### High Costs

```python
# Use smaller/cheaper model
service = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-small",  # $0.02 vs $0.13
)

# Increase cache TTL
[embedding_cache]
ttl = 86400  # 24 hours instead of 1 hour

# Use dimension reduction
dimensions = 512  # Instead of 1536 or 3072
```

## Links

- [Full Documentation](./EMBEDDING_SERVICES.md)
- [Examples](./EXAMPLES.py)
- [Configuration](./CONFIGURATION_EXAMPLE.toml)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)

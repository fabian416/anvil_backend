# Embedding Services Documentation Index

Complete documentation for the OpenAI and Cohere embedding service implementation.

## Quick Navigation

- **New to embeddings?** Start with [Quick Reference](./QUICK_REFERENCE.md)
- **Setting up?** See [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- **Need details?** Read [Full Documentation](./EMBEDDING_SERVICES.md)
- **Want examples?** Check [Code Examples](./EXAMPLES.py)
- **Configuring?** See [Configuration Examples](./CONFIGURATION_EXAMPLE.toml)

## Documentation Files

### 1. Quick Reference

**File**: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

Fast reference for common operations:
- Installation
- Basic usage patterns
- Common code snippets
- Model comparison table
- Best practices
- Troubleshooting tips

**Use this for**: Quick lookups, copy-paste code, common patterns

### 2. Implementation Summary

**File**: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

Overview of the complete implementation:
- Files created and their purposes
- Architecture overview
- Configuration guide
- Integration steps
- Key features summary
- Performance benchmarks

**Use this for**: Understanding the implementation, setup guide, architecture reference

### 3. Full Documentation

**File**: [EMBEDDING_SERVICES.md](./EMBEDDING_SERVICES.md)

Comprehensive documentation:
- Detailed architecture
- All configuration options
- Complete usage examples
- Provider comparison
- Best practices
- Performance optimization
- Monitoring and testing
- Migration guide

**Use this for**: Deep dives, advanced usage, optimization, production deployment

### 4. Code Examples

**File**: [EXAMPLES.py](./EXAMPLES.py)

Working Python examples:
1. Basic usage
2. Semantic search
3. Cost tracking
4. Caching benefits
5. Document clustering
6. Multi-provider comparison
7. Batch processing
8. RAG pipeline

**Use this for**: Learning by example, starting templates, testing

### 5. Configuration Examples

**File**: [CONFIGURATION_EXAMPLE.toml](./CONFIGURATION_EXAMPLE.toml)

TOML configuration templates:
- Production configuration
- Development configuration
- Multilingual configuration
- High-volume configuration
- Testing configuration

**Use this for**: Configuration setup, environment-specific configs

## Source Code Files

### Domain Layer

**File**: `/home/ubuntu/anvil_backend/src/app/domain/ports/ai/embedding_service.py`

Port interface (Protocol):
- `EmbeddingService` protocol
- `EmbeddingInputType` enum
- `EmbeddingResult` dataclass
- `BatchEmbeddingResult` dataclass

### Infrastructure Layer

**OpenAI Adapter**: `/home/ubuntu/anvil_backend/src/app/infrastructure/adapters/ai/openai_embedding_adapter.py`

Implementation for OpenAI:
- Models: text-embedding-3-large, text-embedding-3-small
- Batch size: Up to 2048 texts
- Dimension reduction support
- Cost tracking

**Cohere Adapter**: `/home/ubuntu/anvil_backend/src/app/infrastructure/adapters/ai/cohere_embedding_adapter.py`

Implementation for Cohere:
- Models: embed-english-v3.0, embed-multilingual-v3.0
- Input type support
- Batch size: Up to 96 texts
- Multilingual support

**Cached Adapter**: `/home/ubuntu/anvil_backend/src/app/infrastructure/adapters/ai/cached_embedding_adapter.py`

Caching wrapper:
- Redis-based caching
- Cache statistics
- Cache warming
- Invalidation support

### Setup Layer

**Dependency Injection**: `/home/ubuntu/anvil_backend/src/app/setup/ioc/embeddings.py`

Dishka provider:
- Provider selection logic
- Configuration binding
- Auto-caching setup

## Getting Started Path

### For Beginners

1. Read [Quick Reference](./QUICK_REFERENCE.md) - Basic concepts
2. Check [Configuration Examples](./CONFIGURATION_EXAMPLE.toml) - Setup config
3. Try [Code Examples](./EXAMPLES.py) - Run example 1 (Basic Usage)
4. Read [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) - Understand structure

### For Implementation

1. Read [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) - Overview
2. Check [Configuration Examples](./CONFIGURATION_EXAMPLE.toml) - Configure
3. Review source files - Understand implementation
4. Read [Full Documentation](./EMBEDDING_SERVICES.md) - Deep dive

### For Production Deployment

1. Read [Full Documentation](./EMBEDDING_SERVICES.md) - All details
2. Check [EMBEDDING_SERVICES.md](./EMBEDDING_SERVICES.md#performance-optimization) - Optimization
3. Review [EMBEDDING_SERVICES.md](./EMBEDDING_SERVICES.md#monitoring) - Monitoring setup
4. Check [Quick Reference](./QUICK_REFERENCE.md#troubleshooting) - Troubleshooting

## Key Topics

### Configuration

- [Quick Reference > Configuration](./QUICK_REFERENCE.md#configuration)
- [Configuration Examples](./CONFIGURATION_EXAMPLE.toml)
- [Implementation Summary > Configuration](./IMPLEMENTATION_SUMMARY.md#configuration)
- [Full Documentation > Configuration](./EMBEDDING_SERVICES.md#configuration)

### Usage Patterns

- [Quick Reference > Basic Usage](./QUICK_REFERENCE.md#basic-usage)
- [Code Examples](./EXAMPLES.py)
- [Full Documentation > Usage Examples](./EMBEDDING_SERVICES.md#usage-examples)

### Semantic Search

- [Quick Reference > Semantic Search](./QUICK_REFERENCE.md#semantic-search)
- [Code Examples > Example 2](./EXAMPLES.py) (example_semantic_search)
- [Full Documentation > With Input Types](./EMBEDDING_SERVICES.md#with-input-types-cohere)

### Cost Optimization

- [Quick Reference > Best Practices](./QUICK_REFERENCE.md#best-practices)
- [Quick Reference > Cost Calculations](./QUICK_REFERENCE.md#cost-calculations)
- [Code Examples > Example 3](./EXAMPLES.py) (example_cost_tracking)
- [Full Documentation > Cost Optimization](./EMBEDDING_SERVICES.md#cost-optimization)

### Caching

- [Quick Reference > Cache Operations](./QUICK_REFERENCE.md#cache-operations)
- [Quick Reference > With Caching](./QUICK_REFERENCE.md#with-caching)
- [Code Examples > Example 4](./EXAMPLES.py) (example_caching_benefits)
- [Full Documentation > With Caching](./EMBEDDING_SERVICES.md#with-caching)

### Performance

- [Implementation Summary > Performance](./IMPLEMENTATION_SUMMARY.md#performance)
- [Full Documentation > Performance Optimization](./EMBEDDING_SERVICES.md#performance-optimization)

### Troubleshooting

- [Quick Reference > Troubleshooting](./QUICK_REFERENCE.md#troubleshooting)
- [Full Documentation > Troubleshooting](./EMBEDDING_SERVICES.md#troubleshooting)

## Comparison Tables

### Provider Comparison

See [Full Documentation > Provider Comparison](./EMBEDDING_SERVICES.md#provider-comparison):
- Feature comparison
- Cost comparison
- Performance comparison

### Model Comparison

See [Quick Reference > Model Comparison](./QUICK_REFERENCE.md#model-comparison):
- Dimensions
- Cost per 1M tokens
- Batch sizes
- Use cases

## Code Examples Index

All examples in [EXAMPLES.py](./EXAMPLES.py):

1. **example_basic_usage()** - Simple embedding generation
2. **example_semantic_search()** - Search with embeddings
3. **example_cost_tracking()** - Monitor costs
4. **example_caching_benefits()** - Cache performance
5. **example_document_clustering()** - Cluster documents
6. **example_multi_provider()** - Compare providers
7. **example_batch_processing()** - Large datasets
8. **example_rag_pipeline()** - RAG implementation

## API Reference

### EmbeddingService Protocol

```python
embed_text(text, input_type=None) -> List[float]
embed_texts(texts, input_type=None) -> List[List[float]]
embed_with_metadata(text, input_type=None) -> EmbeddingResult
embed_batch_with_metadata(texts, input_type=None) -> BatchEmbeddingResult
get_dimensions() -> int
get_max_batch_size() -> int
get_provider_name() -> str
```

See [Quick Reference > Service Methods Reference](./QUICK_REFERENCE.md#service-methods-reference)

### Data Classes

```python
EmbeddingInputType - Enum (SEARCH_DOCUMENT, SEARCH_QUERY, etc.)
EmbeddingResult - Single result with metadata
BatchEmbeddingResult - Batch result with aggregated metadata
```

See [Implementation Summary > Domain Layer](./IMPLEMENTATION_SUMMARY.md#1-domain-layer---port-interface)

## External Resources

- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Cohere Embeddings Documentation](https://docs.cohere.com/docs/embeddings)
- [Vector Database Integration Guides](https://www.pinecone.io/learn/semantic-search/)

## Support

For questions or issues:

1. Check [Troubleshooting](./QUICK_REFERENCE.md#troubleshooting)
2. Review [Full Documentation](./EMBEDDING_SERVICES.md)
3. See [Code Examples](./EXAMPLES.py)
4. Consult provider docs (OpenAI/Cohere)

## Updates and Maintenance

This implementation includes:
- ✅ OpenAI text-embedding-3-large, text-embedding-3-small
- ✅ Cohere embed-english-v3.0, embed-multilingual-v3.0
- ✅ Redis caching
- ✅ Cost tracking
- ✅ Batch processing
- ✅ Input type optimization
- ✅ Async support
- ✅ Dependency injection
- ✅ Comprehensive documentation

Last updated: 2025-12-16

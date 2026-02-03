"""
Embedding Service Examples.

Demonstrates various usage patterns for the embedding services.
"""

import asyncio
import numpy as np
from typing import List


# Example 1: Basic Usage
async def example_basic_usage():
    """Basic embedding generation."""
    from app.domain.ports.ai.embedding_service import EmbeddingService
    from dishka import AsyncContainer

    # Get service from DI container
    async with container() as c:
        service: EmbeddingService = await c.get(EmbeddingService)

        # Single embedding
        text = "The quick brown fox jumps over the lazy dog"
        embedding = await service.embed_text(text)
        print(f"Generated embedding with {len(embedding)} dimensions")

        # Batch embeddings
        texts = [
            "Python is a programming language",
            "JavaScript is used for web development",
            "Rust is a systems programming language",
        ]
        embeddings = await service.embed_texts(texts)
        print(f"Generated {len(embeddings)} embeddings")


# Example 2: Semantic Search
async def example_semantic_search():
    """Semantic search with embeddings."""
    from app.domain.ports.ai.embedding_service import (
        EmbeddingService,
        EmbeddingInputType,
    )
    from dishka import AsyncContainer

    async with container() as c:
        service: EmbeddingService = await c.get(EmbeddingService)

        # Index documents
        documents = [
            "Python is a high-level programming language known for its simplicity",
            "JavaScript is the language of the web, running in browsers",
            "Rust provides memory safety without garbage collection",
            "Go is designed for building scalable network services",
            "TypeScript adds static typing to JavaScript",
        ]

        # Embed documents for indexing
        doc_embeddings = await service.embed_texts(
            documents,
            input_type=EmbeddingInputType.SEARCH_DOCUMENT,
        )

        # Search with a query
        query = "Which language is best for web development?"
        query_embedding = await service.embed_text(
            query,
            input_type=EmbeddingInputType.SEARCH_QUERY,
        )

        # Calculate similarities
        similarities = [
            cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_embeddings
        ]

        # Rank results
        ranked = sorted(
            zip(documents, similarities),
            key=lambda x: x[1],
            reverse=True,
        )

        print("Search results:")
        for i, (doc, score) in enumerate(ranked[:3], 1):
            print(f"{i}. [{score:.3f}] {doc}")


# Example 3: Cost Tracking
async def example_cost_tracking():
    """Track embedding costs."""
    from app.domain.ports.ai.embedding_service import EmbeddingService
    from dishka import AsyncContainer

    async with container() as c:
        service: EmbeddingService = await c.get(EmbeddingService)

        # Large batch with metadata
        texts = [f"Document {i}" for i in range(1000)]

        result = await service.embed_batch_with_metadata(texts)

        print(f"Provider: {result.provider}")
        print(f"Model: {result.model}")
        print(f"Total embeddings: {len(result)}")
        print(f"Total tokens: {result.total_tokens:,}")
        print(f"Total cost: ${result.total_cost_usd:.4f}")
        print(f"Cost per embedding: ${result.total_cost_usd / len(result):.6f}")

        # Project monthly costs
        daily_embeddings = 10000
        cost_per_embedding = result.total_cost_usd / len(result)
        monthly_cost = cost_per_embedding * daily_embeddings * 30

        print(f"\nProjected monthly cost (10k/day): ${monthly_cost:.2f}")


# Example 4: Caching Benefits
async def example_caching_benefits():
    """Demonstrate caching benefits."""
    from app.infrastructure.adapters.ai.openai_embedding_adapter import (
        OpenAIEmbeddingAdapter,
    )
    from app.infrastructure.adapters.ai.cached_embedding_adapter import (
        CachedEmbeddingAdapter,
    )
    import redis.asyncio as aioredis
    import time

    # Setup
    redis_client = await aioredis.from_url("redis://localhost:6379")
    base_service = OpenAIEmbeddingAdapter(
        api_key="sk-...",
        model="text-embedding-3-small",
    )
    cached_service = CachedEmbeddingAdapter(
        embedding_service=base_service,
        redis_client=redis_client,
        ttl=3600,
    )

    # Common queries (would be repeated in real usage)
    common_queries = [
        "What is machine learning?",
        "How do neural networks work?",
        "What is deep learning?",
    ] * 10  # Simulate 10 repetitions

    # First run (populate cache)
    start = time.time()
    for query in common_queries:
        await cached_service.embed_text(query)
    first_run_time = time.time() - start

    # Second run (from cache)
    start = time.time()
    for query in common_queries:
        await cached_service.embed_text(query)
    second_run_time = time.time() - start

    # Stats
    stats = await cached_service.get_cache_stats()

    print(f"First run (with cache misses): {first_run_time:.2f}s")
    print(f"Second run (all cache hits): {second_run_time:.2f}s")
    print(f"Speedup: {first_run_time / second_run_time:.1f}x")
    print(f"\nCache hit rate: {stats['hit_rate']:.1f}%")
    print(f"API calls: {stats['api_calls']}")
    print(f"Cached embeddings: {stats['cached_embeddings']}")


# Example 5: Document Clustering
async def example_document_clustering():
    """Cluster documents using embeddings."""
    from app.domain.ports.ai.embedding_service import (
        EmbeddingService,
        EmbeddingInputType,
    )
    from sklearn.cluster import KMeans
    from dishka import AsyncContainer

    async with container() as c:
        service: EmbeddingService = await c.get(EmbeddingService)

        # Documents to cluster
        documents = [
            # Tech
            "Machine learning is a subset of artificial intelligence",
            "Neural networks are inspired by biological brains",
            "Deep learning uses multiple layers of processing",
            # Finance
            "Stock markets track company valuations",
            "Bonds are fixed-income securities",
            "Cryptocurrency uses blockchain technology",
            # Sports
            "Basketball is played with five players per team",
            "Soccer is the world's most popular sport",
            "Tennis is played on different court surfaces",
        ]

        # Generate embeddings
        embeddings = await service.embed_texts(
            documents,
            input_type=EmbeddingInputType.CLUSTERING,
        )

        # Cluster using k-means
        embeddings_array = np.array(embeddings)
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(embeddings_array)

        # Display results
        print("Document Clusters:")
        for i in range(3):
            cluster_docs = [
                doc for doc, cluster in zip(documents, clusters) if cluster == i
            ]
            print(f"\nCluster {i + 1}:")
            for doc in cluster_docs:
                print(f"  - {doc}")


# Example 6: Multi-Provider Comparison
async def example_multi_provider():
    """Compare OpenAI vs Cohere embeddings."""
    from app.infrastructure.adapters.ai.openai_embedding_adapter import (
        OpenAIEmbeddingAdapter,
    )
    from app.infrastructure.adapters.ai.cohere_embedding_adapter import (
        CohereEmbeddingAdapter,
    )

    # Setup both services
    openai_service = OpenAIEmbeddingAdapter(
        api_key="sk-...",
        model="text-embedding-3-small",
    )
    cohere_service = CohereEmbeddingAdapter(
        api_key="...",
        model="embed-english-v3.0",
    )

    text = "Artificial intelligence is transforming technology"

    # Compare both
    openai_result = await openai_service.embed_with_metadata(text)
    cohere_result = await cohere_service.embed_with_metadata(text)

    print("OpenAI:")
    print(f"  Dimensions: {openai_result.dimensions}")
    print(f"  Tokens: {openai_result.input_tokens}")
    print(f"  Cost: ${openai_result.cost_usd:.6f}")

    print("\nCohere:")
    print(f"  Dimensions: {cohere_result.dimensions}")
    print(f"  Tokens: {cohere_result.input_tokens}")
    print(f"  Cost: ${cohere_result.cost_usd:.6f}")


# Example 7: Batch Processing Large Dataset
async def example_batch_processing():
    """Efficiently process large datasets."""
    from app.domain.ports.ai.embedding_service import EmbeddingService
    from dishka import AsyncContainer

    async with container() as c:
        service: EmbeddingService = await c.get(EmbeddingService)

        # Simulate large dataset
        large_dataset = [f"Document {i} content here..." for i in range(10000)]

        # Process in batches
        batch_size = service.get_max_batch_size()
        all_embeddings = []

        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i : i + batch_size]
            embeddings = await service.embed_texts(batch)
            all_embeddings.extend(embeddings)

            print(f"Processed {i + len(batch)}/{len(large_dataset)} documents")

        print(f"\nTotal embeddings generated: {len(all_embeddings)}")


# Example 8: RAG (Retrieval Augmented Generation)
async def example_rag_pipeline():
    """RAG pipeline with embeddings."""
    from app.domain.ports.ai.embedding_service import (
        EmbeddingService,
        EmbeddingInputType,
    )
    from dishka import AsyncContainer

    async with container() as c:
        service: EmbeddingService = await c.get(EmbeddingService)

        # Knowledge base
        knowledge_base = [
            "The Eiffel Tower is located in Paris, France",
            "The Great Wall of China is over 13,000 miles long",
            "The Statue of Liberty was a gift from France",
            "The Colosseum is an ancient amphitheater in Rome",
            "Machu Picchu is an Incan citadel in Peru",
        ]

        # Embed knowledge base
        kb_embeddings = await service.embed_texts(
            knowledge_base,
            input_type=EmbeddingInputType.SEARCH_DOCUMENT,
        )

        # User query
        query = "What famous landmark is in France?"

        # Embed query
        query_embedding = await service.embed_text(
            query,
            input_type=EmbeddingInputType.SEARCH_QUERY,
        )

        # Find most relevant context
        similarities = [
            cosine_similarity(query_embedding, kb_emb) for kb_emb in kb_embeddings
        ]
        best_match_idx = np.argmax(similarities)
        context = knowledge_base[best_match_idx]

        print(f"Query: {query}")
        print(f"Retrieved Context: {context}")
        print(f"Similarity Score: {similarities[best_match_idx]:.3f}")


# Utility Functions
def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_array = np.array(a)
    b_array = np.array(b)
    return np.dot(a_array, b_array) / (
        np.linalg.norm(a_array) * np.linalg.norm(b_array)
    )


def euclidean_distance(a: List[float], b: List[float]) -> float:
    """Calculate Euclidean distance between two vectors."""
    a_array = np.array(a)
    b_array = np.array(b)
    return np.linalg.norm(a_array - b_array)


if __name__ == "__main__":
    # Run examples
    print("=" * 80)
    print("Example 1: Basic Usage")
    print("=" * 80)
    asyncio.run(example_basic_usage())

    print("\n" + "=" * 80)
    print("Example 2: Semantic Search")
    print("=" * 80)
    asyncio.run(example_semantic_search())

    print("\n" + "=" * 80)
    print("Example 3: Cost Tracking")
    print("=" * 80)
    asyncio.run(example_cost_tracking())

    # Add more example calls as needed

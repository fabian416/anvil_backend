"""
GraphRAG fixtures for tests.

Provides mock GraphRAG search results, embeddings, and
graph-related test data.
"""

import pytest
from uuid import uuid4


@pytest.fixture
def mock_graphrag_search_results():
    """Mock GraphRAG hybrid search results."""
    return {
        "results": [
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Aave V3",
                "similarity_score": 0.95,
                "risk_score": 2.1,
                "risk_level": "LOW",
                "tvl": 6200000000,
                "apy": 3.5,
                "audit_count": 12,
                "description": "Decentralized lending protocol",
                "category": "LENDING",
                "chain": "ethereum",
                "why_relevant": "High similarity to query, strong fundamentals"
            },
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Compound",
                "similarity_score": 0.87,
                "risk_score": 2.5,
                "risk_level": "LOW",
                "tvl": 3800000000,
                "apy": 3.2,
                "audit_count": 10,
                "description": "Algorithmic money market protocol",
                "category": "LENDING",
                "chain": "ethereum",
                "why_relevant": "Similar lending mechanics"
            },
        ],
        "total": 2,
        "query": "safe lending protocols",
    }


@pytest.fixture
def mock_protocol_similarity_results():
    """Mock similar protocols results."""
    return {
        "base_protocol": {
            "protocol_id": str(uuid4()),
            "protocol_name": "Aave V3",
            "risk_score": 2.1,
            "tvl": 6200000000,
        },
        "similar_protocols": [
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Compound",
                "similarity_score": 0.92,
                "risk_score": 2.5,
                "tvl": 3800000000,
                "why_similar": "Both are lending protocols with similar risk profiles"
            },
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Spark Protocol",
                "similarity_score": 0.85,
                "risk_score": 2.3,
                "tvl": 1200000000,
                "why_similar": "Fork of Aave with similar mechanisms"
            },
        ],
    }


@pytest.fixture
def mock_graph_analytics_overview():
    """Mock graph analytics overview."""
    return {
        "total_nodes": 1250,
        "total_edges": 3400,
        "node_types": {
            "PROTOCOL": 850,
            "TOKEN": 250,
            "CHAIN": 15,
            "CATEGORY": 35,
        },
        "edge_types": {
            "DEPENDS_ON": 1200,
            "PROVIDES": 800,
            "SUPPORTS": 600,
            "SIMILAR_TO": 800,
        },
        "average_degree": 5.44,
        "graph_density": 0.0022,
    }


@pytest.fixture
def mock_embedding_vector():
    """Mock embedding vector (384 dimensions for testing)."""
    import random
    return [random.random() for _ in range(384)]

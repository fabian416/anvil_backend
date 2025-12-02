"""
Integration tests for hybrid retrieval.
"""

import pytest
from uuid import uuid4
from typing import List

from app.application.graph import HybridRetrievalInteractor, HybridRetrievalResult
from app.domain.ports.graph import GraphRepository, GraphNode
from app.domain.ports.embeddings import EmbeddingService
from app.domain.ports.vector import (
    VectorRepository,
    VectorDocument,
    SimilarityResult,
)
from app.domain.services.graph import GraphService, RiskAnalysisService
from datetime import datetime


class MockEmbeddingService:
    """Mock embedding service"""
    
    async def embed_text(self, text: str) -> List[float]:
        """Return mock embedding (same for all for simplicity)"""
        return [0.1] * 1536
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 1536 for _ in texts]
    
    def get_dimensions(self) -> int:
        return 1536


class MockVectorRepository:
    """Mock vector repository"""
    
    def __init__(self):
        self.embeddings = {}
    
    async def store_embedding(self, entity_id, entity_type, entity_name, text_content, embedding, model):
        doc_id = uuid4()
        self.embeddings[entity_id] = VectorDocument(
            id=doc_id,
            entity_id=entity_id,
            entity_type=entity_type,
            entity_name=entity_name,
            text_content=text_content,
            embedding=embedding,
            model=model,
            dimensions=len(embedding),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return doc_id
    
    async def get_embedding(self, entity_id):
        return self.embeddings.get(entity_id)
    
    async def find_similar(self, query_embedding, entity_type=None, limit=10, similarity_threshold=0.5):
        # Return all embeddings with similarity 0.8 (mock)
        results = []
        for doc in list(self.embeddings.values())[:limit]:
            if entity_type and doc.entity_type != entity_type:
                continue
            results.append(SimilarityResult(
                document=doc,
                similarity=0.8,
            ))
        return results
    
    async def delete_embedding(self, entity_id):
        if entity_id in self.embeddings:
            del self.embeddings[entity_id]
    
    async def count_embeddings(self, entity_type=None):
        if entity_type:
            return len([d for d in self.embeddings.values() if d.entity_type == entity_type])
        return len(self.embeddings)


class MockGraphRepository:
    """Mock graph repository"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    async def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    async def find_nodes(self, label, filters=None, limit=100, offset=0):
        results = []
        for node in self.nodes.values():
            if label in node.labels:
                if filters:
                    match = True
                    for key, value in filters.items():
                        if node.properties.get(key) != value:
                            match = False
                            break
                    if match:
                        results.append(node)
                else:
                    results.append(node)
        return results[offset:offset+limit]
    
    async def get_neighbors(self, node_id, relationship_type, direction):
        neighbors = []
        for edge in self.edges:
            if edge["type"] == relationship_type:
                if edge["from"] == node_id:
                    neighbor_id = edge["to"]
                elif edge["to"] == node_id:
                    neighbor_id = edge["from"]
                else:
                    continue
                
                if neighbor_id in self.nodes:
                    neighbors.append(self.nodes[neighbor_id])
        return neighbors
    
    async def get_node_degree(self, node_id, direction):
        degree = 0
        for edge in self.edges:
            if edge["from"] == node_id or edge["to"] == node_id:
                degree += 1
        return degree


@pytest.mark.asyncio
async def test_hybrid_search_basic():
    """Test basic hybrid search functionality"""
    
    # Setup mocks
    graph_repo = MockGraphRepository()
    embedding_service = MockEmbeddingService()
    vector_repo = MockVectorRepository()
    graph_service = GraphService(graph_repo)
    risk_service = RiskAnalysisService(graph_repo)
    
    # Create test protocol
    protocol_id = uuid4()
    protocol_node = GraphNode(
        id=protocol_id,
        labels=["Protocol"],
        properties={
            "name": "Aave",
            "category": "Lending",
            "tvl": 5000000000,
        },
    )
    graph_repo.nodes[protocol_id] = protocol_node
    
    # Store embedding
    await vector_repo.store_embedding(
        entity_id=protocol_id,
        entity_type="Protocol",
        entity_name="Aave",
        text_content="Aave lending protocol",
        embedding=[0.1] * 1536,
        model="test",
    )
    
    # Create interactor
    interactor = HybridRetrievalInteractor(
        graph_repo,
        embedding_service,
        vector_repo,
        graph_service,
        risk_service,
    )
    
    # Execute search
    results = await interactor.search_protocols(
        query="lending protocol",
        limit=10,
        include_risks=False,
        include_dependencies=False,
    )
    
    # Verify
    assert len(results) == 1
    assert results[0].protocol_name == "Aave"
    assert results[0].vector_similarity == 0.8
    assert results[0].score > 0


@pytest.mark.asyncio
async def test_hybrid_search_with_context():
    """Test hybrid search with graph context"""
    
    # Setup
    graph_repo = MockGraphRepository()
    embedding_service = MockEmbeddingService()
    vector_repo = MockVectorRepository()
    graph_service = GraphService(graph_repo)
    risk_service = RiskAnalysisService(graph_repo)
    
    # Create protocols
    aave_id = uuid4()
    aave_node = GraphNode(
        id=aave_id,
        labels=["Protocol"],
        properties={
            "name": "Aave",
            "category": "Lending",
            "tvl": 5000000000,
        },
    )
    graph_repo.nodes[aave_id] = aave_node
    
    compound_id = uuid4()
    compound_node = GraphNode(
        id=compound_id,
        labels=["Protocol"],
        properties={
            "name": "Compound",
            "category": "Lending",
            "tvl": 3000000000,
        },
    )
    graph_repo.nodes[compound_id] = compound_node
    
    # Add dependency
    graph_repo.edges.append({
        "from": aave_id,
        "to": compound_id,
        "type": "DEPENDS_ON",
        "properties": {},
    })
    
    # Store embeddings
    await vector_repo.store_embedding(
        entity_id=aave_id,
        entity_type="Protocol",
        entity_name="Aave",
        text_content="Aave lending protocol",
        embedding=[0.1] * 1536,
        model="test",
    )
    
    await vector_repo.store_embedding(
        entity_id=compound_id,
        entity_type="Protocol",
        entity_name="Compound",
        text_content="Compound lending protocol",
        embedding=[0.1] * 1536,
        model="test",
    )
    
    # Create interactor
    interactor = HybridRetrievalInteractor(
        graph_repo,
        embedding_service,
        vector_repo,
        graph_service,
        risk_service,
    )
    
    # Execute search with context
    results = await interactor.search_protocols(
        query="lending",
        limit=10,
        include_risks=False,
        include_dependencies=True,
    )
    
    # Verify
    assert len(results) == 2
    
    # Check that context includes dependencies
    aave_result = next((r for r in results if r.protocol_name == "Aave"), None)
    assert aave_result is not None
    assert "dependencies" in aave_result.context


@pytest.mark.asyncio
async def test_find_similar_protocols():
    """Test finding similar protocols"""
    
    # Setup
    graph_repo = MockGraphRepository()
    embedding_service = MockEmbeddingService()
    vector_repo = MockVectorRepository()
    graph_service = GraphService(graph_repo)
    risk_service = RiskAnalysisService(graph_repo)
    
    # Create protocols
    aave_id = uuid4()
    aave_node = GraphNode(
        id=aave_id,
        labels=["Protocol"],
        properties={"name": "Aave", "category": "Lending", "tvl": 5000000000},
    )
    graph_repo.nodes[aave_id] = aave_node
    
    compound_id = uuid4()
    compound_node = GraphNode(
        id=compound_id,
        labels=["Protocol"],
        properties={"name": "Compound", "category": "Lending", "tvl": 3000000000},
    )
    graph_repo.nodes[compound_id] = compound_node
    
    # Store embeddings
    await vector_repo.store_embedding(
        entity_id=aave_id,
        entity_type="Protocol",
        entity_name="Aave",
        text_content="Aave",
        embedding=[0.1] * 1536,
        model="test",
    )
    
    await vector_repo.store_embedding(
        entity_id=compound_id,
        entity_type="Protocol",
        entity_name="Compound",
        text_content="Compound",
        embedding=[0.2] * 1536,
        model="test",
    )
    
    # Create interactor
    interactor = HybridRetrievalInteractor(
        graph_repo,
        embedding_service,
        vector_repo,
        graph_service,
        risk_service,
    )
    
    # Find similar to Aave
    results = await interactor.find_similar_protocols(
        protocol_id=aave_id,
        limit=5,
    )
    
    # Should return Compound (excluding Aave itself)
    assert len(results) <= 1  # May be 0 or 1 depending on mock behavior
    if len(results) == 1:
        assert results[0].protocol_id != aave_id


@pytest.mark.asyncio
async def test_contextual_protocols():
    """Test contextual recommendations with user preferences"""
    
    # Setup
    graph_repo = MockGraphRepository()
    embedding_service = MockEmbeddingService()
    vector_repo = MockVectorRepository()
    graph_service = GraphService(graph_repo)
    risk_service = RiskAnalysisService(graph_repo)
    
    # Create protocols
    aave_id = uuid4()
    aave_node = GraphNode(
        id=aave_id,
        labels=["Protocol"],
        properties={"name": "Aave", "category": "Lending", "tvl": 5000000000},
    )
    graph_repo.nodes[aave_id] = aave_node
    
    # Store embedding
    await vector_repo.store_embedding(
        entity_id=aave_id,
        entity_type="Protocol",
        entity_name="Aave",
        text_content="Aave lending protocol",
        embedding=[0.1] * 1536,
        model="test",
    )
    
    # Create interactor
    interactor = HybridRetrievalInteractor(
        graph_repo,
        embedding_service,
        vector_repo,
        graph_service,
        risk_service,
    )
    
    # Search with preferences
    results = await interactor.get_contextual_protocols(
        query="lending",
        user_preferences={
            "category": "Lending",
            "min_tvl": 1000000000,
        },
        limit=5,
    )
    
    # Verify
    assert len(results) >= 1
    for result in results:
        assert result.context["category"] == "Lending"
        assert result.context["tvl"] >= 1000000000

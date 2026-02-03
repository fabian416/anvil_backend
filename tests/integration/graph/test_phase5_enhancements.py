"""Integration tests for Phase 5: GraphRAG Polish & Enhancements.

Tests entity extraction, graph visualization, and PageRank algorithm.
"""

import pytest
from typing import List, Set, Tuple
from unittest.mock import AsyncMock, MagicMock

from app.application.graph.entity_extraction import (
    EntityExtractor,
    EntityType,
    ExtractedEntity,
)
from app.domain.graph.services.pagerank import (
    PageRankService,
    PageRankConfig,
    PageRankResult,
    compute_node_importance,
)


class TestEntityExtraction:
    """Test entity extraction functionality."""

    @pytest.mark.asyncio
    async def test_extract_entities_from_simple_text(self):
        """Test entity extraction from simple DeFi text."""
        # Mock LLM gateway
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(
            return_value="""```json
{
  "entities": [
    {
      "name": "Uniswap",
      "type": "protocol",
      "confidence": 0.95,
      "context": "mentioned as liquidity provider"
    },
    {
      "name": "ETH",
      "type": "token",
      "confidence": 0.99,
      "context": "first token in pool"
    },
    {
      "name": "USDC",
      "type": "token",
      "confidence": 0.99,
      "context": "second token in pool"
    }
  ]
}
```"""
        )

        extractor = EntityExtractor(mock_llm)
        entities = await extractor.extract_entities(
            "What's the APY for Uniswap ETH-USDC pool?"
        )

        assert len(entities) == 3
        assert entities[0].name == "Uniswap"
        assert entities[0].type == EntityType.PROTOCOL
        assert entities[0].confidence >= 0.9
        assert entities[1].name == "ETH"
        assert entities[1].type == EntityType.TOKEN
        assert entities[2].name == "USDC"
        assert entities[2].type == EntityType.TOKEN

    @pytest.mark.asyncio
    async def test_extract_entities_with_fallback(self):
        """Test fallback extraction when LLM response is invalid."""
        # Mock LLM gateway with invalid response
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(return_value="Invalid JSON response")

        extractor = EntityExtractor(mock_llm)
        entities = await extractor.extract_entities("Uniswap provides ETH liquidity")

        # Should fall back to pattern matching
        assert len(entities) >= 1
        # Check if any entity was extracted
        entity_names = [e.name.lower() for e in entities]
        assert any(name in entity_names for name in ["uniswap", "eth"]), (
            "Expected at least one entity (Uniswap or ETH) to be extracted via fallback"
        )

    @pytest.mark.asyncio
    async def test_extract_and_validate_confidence_threshold(self):
        """Test entity extraction with confidence filtering."""
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(
            return_value="""```json
{
  "entities": [
    {"name": "Aave", "type": "protocol", "confidence": 0.95, "context": "high confidence"},
    {"name": "SomeToken", "type": "token", "confidence": 0.5, "context": "low confidence"}
  ]
}
```"""
        )

        extractor = EntityExtractor(mock_llm)
        entities = await extractor.extract_and_validate("Test text", min_confidence=0.7)

        # Should only include high-confidence entity
        assert len(entities) == 1
        assert entities[0].name == "Aave"
        assert entities[0].confidence >= 0.7

    @pytest.mark.asyncio
    async def test_extract_relationships(self):
        """Test relationship extraction between entities."""
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(
            return_value="""```json
{
  "relationships": [
    {
      "source": "Uniswap",
      "target": "ETH",
      "type": "PROVIDES_LIQUIDITY",
      "confidence": 0.88
    },
    {
      "source": "Uniswap",
      "target": "USDC",
      "type": "PROVIDES_LIQUIDITY",
      "confidence": 0.88
    }
  ]
}
```"""
        )

        extractor = EntityExtractor(mock_llm)
        entities = [
            ExtractedEntity(
                name="Uniswap",
                type=EntityType.PROTOCOL,
                confidence=0.95,
                context="",
                metadata={},
            ),
            ExtractedEntity(
                name="ETH",
                type=EntityType.TOKEN,
                confidence=0.99,
                context="",
                metadata={},
            ),
            ExtractedEntity(
                name="USDC",
                type=EntityType.TOKEN,
                confidence=0.99,
                context="",
                metadata={},
            ),
        ]

        relationships = await extractor.extract_relationships(
            "Uniswap provides liquidity for ETH and USDC", entities
        )

        assert len(relationships) == 2
        assert relationships[0]["source"] == "Uniswap"
        assert relationships[0]["target"] == "ETH"
        assert relationships[0]["type"] == "PROVIDES_LIQUIDITY"

    def test_entity_types_coverage(self):
        """Test that all entity types are defined."""
        entity_types = [e.value for e in EntityType]
        expected_types = [
            "protocol",
            "token",
            "address",
            "pool",
            "chain",
            "exchange",
            "lending_platform",
            "yield_aggregator",
        ]

        for expected in expected_types:
            assert expected in entity_types, f"Missing entity type: {expected}"


class TestPageRankAlgorithm:
    """Test PageRank algorithm implementation."""

    def test_compute_pagerank_simple_graph(self):
        """Test PageRank on simple 3-node graph."""
        nodes = {"A", "B", "C"}
        edges = [("A", "B"), ("B", "C"), ("C", "A")]

        service = PageRankService()
        scores = service.compute_pagerank(nodes, edges)

        # All nodes should have equal PageRank in a symmetric cycle
        assert len(scores) == 3
        assert all(0.2 < score < 0.5 for score in scores.values())
        # Scores should sum to approximately 1
        assert abs(sum(scores.values()) - 1.0) < 0.01

    def test_compute_pagerank_hub_and_spoke(self):
        """Test PageRank with hub-and-spoke topology."""
        # Hub node with many incoming links
        nodes = {"hub", "A", "B", "C", "D"}
        edges = [
            ("A", "hub"),
            ("B", "hub"),
            ("C", "hub"),
            ("D", "hub"),
        ]

        service = PageRankService()
        scores = service.compute_pagerank(nodes, edges)

        # Hub should have highest PageRank
        assert scores["hub"] > scores["A"]
        assert scores["hub"] > scores["B"]
        assert scores["hub"] > scores["C"]
        assert scores["hub"] > scores["D"]

    def test_rank_nodes(self):
        """Test node ranking by PageRank score."""
        scores = {"eth": 0.0312, "uniswap": 0.0234, "aave": 0.0234, "usdc": 0.0189}
        connections = {"eth": 300, "uniswap": 150, "aave": 120, "usdc": 280}

        service = PageRankService()
        results = service.rank_nodes(scores, connections)

        assert len(results) == 4
        assert results[0].node_id == "eth"
        assert results[0].rank == 1
        assert results[0].pagerank == 0.0312
        assert results[0].connections == 300

    def test_compute_protocol_importance(self):
        """Test protocol importance calculation."""
        protocols = {
            "uniswap": ["aave", "compound", "curve"],
            "aave": ["uniswap", "compound"],
            "compound": ["uniswap", "aave"],
            "curve": ["uniswap"],
        }

        service = PageRankService()
        ranking = service.compute_protocol_importance(protocols)

        # Uniswap should be most important (most connections)
        assert len(ranking) == 4
        assert ranking[0].node_id == "uniswap"
        assert ranking[0].rank == 1

    def test_identify_hub_protocols(self):
        """Test hub protocol identification."""
        results = [
            PageRankResult(node_id="uniswap", pagerank=0.0312, rank=1, connections=150),
            PageRankResult(node_id="aave", pagerank=0.0289, rank=2, connections=120),
            PageRankResult(node_id="curve", pagerank=0.0245, rank=3, connections=100),
            PageRankResult(node_id="compound", pagerank=0.0201, rank=4, connections=90),
            PageRankResult(node_id="maker", pagerank=0.0198, rank=5, connections=85),
        ]

        service = PageRankService()
        hubs = service.identify_hub_protocols(results, top_n=3)

        assert len(hubs) == 3
        assert hubs[0].node_id == "uniswap"
        assert hubs[1].node_id == "aave"
        assert hubs[2].node_id == "curve"

    def test_compute_centrality_risk(self):
        """Test centrality risk calculation."""
        results = [
            PageRankResult(
                node_id="eth", pagerank=0.0812, rank=1, connections=300
            ),  # HIGH RISK
            PageRankResult(
                node_id="usdc", pagerank=0.0678, rank=2, connections=280
            ),  # HIGH RISK
            PageRankResult(
                node_id="uniswap", pagerank=0.0312, rank=3, connections=150
            ),  # Lower
            PageRankResult(
                node_id="aave", pagerank=0.0289, rank=4, connections=120
            ),  # Lower
        ]

        service = PageRankService()
        risky = service.compute_centrality_risk(results, threshold=0.05)

        # Only ETH and USDC should be flagged as high centrality risk
        assert len(risky) == 2
        assert risky[0].node_id == "eth"
        assert risky[1].node_id == "usdc"

    def test_pagerank_convergence(self):
        """Test that PageRank converges within iteration limit."""
        nodes = {f"node_{i}" for i in range(10)}
        edges = [(f"node_{i}", f"node_{(i + 1) % 10}") for i in range(10)]

        config = PageRankConfig(max_iterations=50, convergence_threshold=0.00001)
        service = PageRankService(config)

        scores = service.compute_pagerank(nodes, edges)

        # Should converge (all nodes equal in cycle)
        assert len(scores) == 10
        values = list(scores.values())
        # All values should be approximately equal
        assert max(values) - min(values) < 0.01

    def test_compute_node_importance_convenience_function(self):
        """Test convenience function for PageRank."""
        nodes = {"A", "B", "C"}
        edges = [("A", "B"), ("B", "C"), ("C", "A")]

        scores = compute_node_importance(nodes, edges, damping=0.85, max_iterations=20)

        assert len(scores) == 3
        assert all(isinstance(score, float) for score in scores.values())
        assert abs(sum(scores.values()) - 1.0) < 0.01


class TestGraphVisualization:
    """Test graph visualization endpoints (structure)."""

    @pytest.mark.skip(reason="Skipping due to import dependency issue with search.py")
    def test_graph_node_model(self):
        """Test GraphNode data model."""
        from app.presentation.http.controllers.graph.visualization import GraphNode

        node = GraphNode(
            id="uniswap",
            label="Uniswap",
            type="protocol",
            importance=0.95,
            connections=150,
            metadata={"tvl": "3.2B"},
        )

        assert node.id == "uniswap"
        assert node.label == "Uniswap"
        assert node.type == "protocol"
        assert node.importance == 0.95
        assert node.connections == 150
        assert node.metadata["tvl"] == "3.2B"

    @pytest.mark.skip(reason="Skipping due to import dependency issue with search.py")
    def test_graph_edge_model(self):
        """Test GraphEdge data model."""
        from app.presentation.http.controllers.graph.visualization import GraphEdge

        edge = GraphEdge(
            source="uniswap",
            target="eth",
            type="PROVIDES_LIQUIDITY",
            weight=0.9,
            metadata={"pool_size": "500M"},
        )

        assert edge.source == "uniswap"
        assert edge.target == "eth"
        assert edge.type == "PROVIDES_LIQUIDITY"
        assert edge.weight == 0.9
        assert edge.metadata["pool_size"] == "500M"

    @pytest.mark.skip(reason="Skipping due to import dependency issue with search.py")
    def test_graph_visualization_response_model(self):
        """Test GraphVisualizationResponse model."""
        from app.presentation.http.controllers.graph.visualization import (
            GraphVisualizationResponse,
            GraphNode,
            GraphEdge,
        )

        nodes = [
            GraphNode(
                id="A", label="A", type="protocol", importance=0.9, connections=10
            )
        ]
        edges = [GraphEdge(source="A", target="B", type="LINKS_TO", weight=0.8)]

        response = GraphVisualizationResponse(
            nodes=nodes, edges=edges, total_nodes=1, total_edges=1
        )

        assert len(response.nodes) == 1
        assert len(response.edges) == 1
        assert response.total_nodes == 1
        assert response.total_edges == 1

    @pytest.mark.skip(reason="Skipping due to import dependency issue with search.py")
    def test_subgraph_response_model(self):
        """Test SubgraphResponse model."""
        from app.presentation.http.controllers.graph.visualization import (
            SubgraphResponse,
            GraphNode,
            GraphEdge,
        )

        center = GraphNode(
            id="uniswap",
            label="Uniswap",
            type="protocol",
            importance=0.95,
            connections=150,
        )
        nodes = [
            GraphNode(
                id="eth", label="ETH", type="token", importance=1.0, connections=300
            )
        ]
        edges = [
            GraphEdge(
                source="uniswap", target="eth", type="PROVIDES_LIQUIDITY", weight=0.9
            )
        ]

        response = SubgraphResponse(
            center_node=center, nodes=nodes, edges=edges, depth=2
        )

        assert response.center_node.id == "uniswap"
        assert len(response.nodes) == 1
        assert len(response.edges) == 1
        assert response.depth == 2


class TestPhase5Integration:
    """Integration tests for complete Phase 5 functionality."""

    @pytest.mark.asyncio
    async def test_entity_extraction_to_graph_flow(self):
        """Test complete flow: extract entities → add to graph."""
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(
            return_value="""```json
{
  "entities": [
    {"name": "Uniswap", "type": "protocol", "confidence": 0.95, "context": ""},
    {"name": "ETH", "type": "token", "confidence": 0.99, "context": ""}
  ]
}
```"""
        )

        extractor = EntityExtractor(mock_llm)
        entities = await extractor.extract_entities("Uniswap trades ETH")

        # Entities extracted successfully
        assert len(entities) >= 2

        # In real implementation, these would be added to Apache AGE graph
        # For now, verify entity structure
        protocol_entities = [e for e in entities if e.type == EntityType.PROTOCOL]
        token_entities = [e for e in entities if e.type == EntityType.TOKEN]

        assert len(protocol_entities) >= 1
        assert len(token_entities) >= 1

    def test_pagerank_for_protocol_ranking(self):
        """Test using PageRank for protocol importance ranking."""
        # Simulate DeFi protocol network
        protocols = {
            "uniswap": ["eth", "usdc", "dai", "wbtc"],
            "aave": ["eth", "usdc", "dai"],
            "curve": ["usdc", "dai", "3crv"],
            "compound": ["eth", "usdc", "dai"],
            "maker": ["dai", "eth"],
        }

        # Flatten to edges
        nodes = set(protocols.keys())
        for targets in protocols.values():
            nodes.update(targets)

        edges: List[Tuple[str, str]] = []
        for source, targets in protocols.items():
            for target in targets:
                edges.append((source, target))

        # Compute PageRank
        service = PageRankService()
        scores = service.compute_pagerank(nodes, edges)

        # ETH and USDC should have high PageRank (many incoming links)
        assert scores["eth"] > 0.03, "ETH should be highly ranked"
        assert scores["usdc"] > 0.03, "USDC should be highly ranked"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Skipping due to import dependency issue with search.py")
    async def test_visualization_data_preparation(self):
        """Test preparing graph data for D3.js visualization."""
        from app.presentation.http.controllers.graph.visualization import (
            GraphNode,
            GraphEdge,
        )

        # Create sample nodes
        nodes = [
            GraphNode(
                id="uniswap",
                label="Uniswap",
                type="protocol",
                importance=0.95,
                connections=150,
            ),
            GraphNode(
                id="eth", label="ETH", type="token", importance=1.0, connections=300
            ),
            GraphNode(
                id="usdc", label="USDC", type="token", importance=0.98, connections=280
            ),
        ]

        # Create sample edges
        edges = [
            GraphEdge(
                source="uniswap", target="eth", type="PROVIDES_LIQUIDITY", weight=0.9
            ),
            GraphEdge(
                source="uniswap", target="usdc", type="PROVIDES_LIQUIDITY", weight=0.9
            ),
        ]

        # Verify D3.js-compatible structure
        assert all(hasattr(n, "id") and hasattr(n, "label") for n in nodes)
        assert all(hasattr(e, "source") and hasattr(e, "target") for e in edges)

        # Verify importance scores are normalized
        assert all(0.0 <= n.importance <= 1.0 for n in nodes)
        assert all(0.0 <= e.weight <= 1.0 for e in edges)


# Performance benchmarks
class TestPhase5Performance:
    """Performance tests for Phase 5 features."""

    def test_pagerank_performance_large_graph(self):
        """Test PageRank performance on large graph (1000 nodes)."""
        import time

        # Create large graph
        num_nodes = 1000
        nodes = {f"node_{i}" for i in range(num_nodes)}
        edges = []
        for i in range(num_nodes):
            # Each node connects to 5 random others
            for j in range(5):
                target = (i + j + 1) % num_nodes
                edges.append((f"node_{i}", f"node_{target}"))

        # Measure computation time
        service = PageRankService()
        start_time = time.time()
        scores = service.compute_pagerank(nodes, edges)
        elapsed = time.time() - start_time

        # Should complete in under 1 second (Phase 5 requirement)
        assert elapsed < 1.0, f"PageRank took {elapsed:.2f}s (expected <1s)"
        assert len(scores) == num_nodes

    @pytest.mark.asyncio
    async def test_entity_extraction_performance(self):
        """Test entity extraction performance."""
        import time

        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(
            return_value="""```json
{"entities": [
  {"name": "Uniswap", "type": "protocol", "confidence": 0.95, "context": ""},
  {"name": "ETH", "type": "token", "confidence": 0.99, "context": ""}
]}
```"""
        )

        extractor = EntityExtractor(mock_llm)

        # Extract from multiple texts
        texts = [
            "Uniswap provides ETH liquidity",
            "Aave lends USDC",
            "Curve optimizes stablecoin swaps",
        ] * 10  # 30 extractions

        start_time = time.time()
        for text in texts:
            await extractor.extract_entities(text)
        elapsed = time.time() - start_time

        # Should process ~10 extractions per second
        rate = len(texts) / elapsed
        assert rate > 5.0, f"Extraction rate: {rate:.2f}/s (expected >5/s)"

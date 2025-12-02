"""
Integration tests for graph population.
"""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from app.application.graph import PopulateGraphInteractor
from app.domain.ports.graph import GraphRepository, GraphNode
from app.domain.ports.external_data import (
    DefiDataProvider,
    ProtocolData,
)


class MockDefiDataProvider:
    """Mock DeFi data provider for testing"""
    
    async def get_all_protocols(self, limit=None):
        """Return mock protocol data"""
        protocols = [
            ProtocolData(
                name="Aave",
                slug="aave",
                description="Decentralized lending protocol",
                category="Lending",
                chains=["Ethereum", "Polygon"],
                tvl=Decimal("5000000000"),
                change_24h=2.5,
                website="https://aave.com",
                twitter="@aave",
                github="https://github.com/aave",
                logo="https://example.com/aave.png",
                audit_links=["https://example.com/audit1.pdf"],
                token_symbol="AAVE",
                raw_data={},
                last_updated=datetime.utcnow(),
            ),
            ProtocolData(
                name="Uniswap",
                slug="uniswap",
                description="Decentralized exchange",
                category="DEX",
                chains=["Ethereum"],
                tvl=Decimal("3000000000"),
                change_24h=-1.2,
                website="https://uniswap.org",
                twitter="@uniswap",
                github="https://github.com/uniswap",
                logo="https://example.com/uni.png",
                audit_links=[],
                token_symbol="UNI",
                raw_data={},
                last_updated=datetime.utcnow(),
            ),
        ]
        
        return protocols[:limit] if limit else protocols
    
    async def get_protocol(self, slug):
        protocols = await self.get_all_protocols()
        for p in protocols:
            if p.slug == slug:
                return p
        return None
    
    async def get_protocol_tvl(self, slug):
        return []
    
    async def get_chains(self):
        return []
    
    async def get_chain_protocols(self, chain):
        return []
    
    async def get_token_price(self, address, chain):
        return None
    
    async def search_protocols(self, query, limit=10):
        return []
    
    async def get_audits(self, protocol_slug):
        return []


class MockGraphRepository:
    """Mock graph repository for testing"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    async def create_node(self, label, properties):
        node_id = uuid4()
        self.nodes[node_id] = GraphNode(
            id=node_id,
            labels=[label],
            properties=properties,
        )
        return node_id
    
    async def update_node(self, node_id, properties):
        if node_id in self.nodes:
            self.nodes[node_id].properties.update(properties)
    
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
    
    async def create_edge(self, from_id, to_id, relationship_type, properties):
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "type": relationship_type,
            "properties": properties,
        })
    
    async def find_edges(self, from_id=None, to_id=None, relationship_type=None):
        results = []
        for edge in self.edges:
            if from_id and edge["from"] != from_id:
                continue
            if to_id and edge["to"] != to_id:
                continue
            if relationship_type and edge["type"] != relationship_type:
                continue
            results.append(edge)
        return results


@pytest.mark.asyncio
async def test_populate_protocols():
    """Test populating protocols from external source"""
    
    # Setup
    graph_repo = MockGraphRepository()
    data_provider = MockDefiDataProvider()
    interactor = PopulateGraphInteractor(graph_repo, data_provider)
    
    # Execute
    stats = await interactor.populate_protocols(limit=2)
    
    # Verify
    assert stats["protocols_fetched"] == 2
    assert stats["protocols_created"] == 2
    assert stats["chains_created"] == 2  # Ethereum, Polygon
    assert stats["tokens_created"] == 2  # AAVE, UNI
    assert stats["relationships_created"] == 5  # 2 DEPLOYED_ON (Aave) + 1 DEPLOYED_ON (Uni) + 2 USES_TOKEN
    assert stats["errors"] == 0
    
    # Verify protocols created
    protocols = await graph_repo.find_nodes("Protocol")
    assert len(protocols) == 2
    
    # Verify chains created
    chains = await graph_repo.find_nodes("Chain")
    assert len(chains) == 2
    
    # Verify tokens created
    tokens = await graph_repo.find_nodes("Token")
    assert len(tokens) == 2


@pytest.mark.asyncio
async def test_populate_protocols_updates_existing():
    """Test that existing protocols are updated, not duplicated"""
    
    # Setup
    graph_repo = MockGraphRepository()
    data_provider = MockDefiDataProvider()
    interactor = PopulateGraphInteractor(graph_repo, data_provider)
    
    # First population
    stats1 = await interactor.populate_protocols(limit=1)
    assert stats1["protocols_created"] == 1
    
    # Second population (should update)
    stats2 = await interactor.populate_protocols(limit=1)
    assert stats2["protocols_created"] == 0  # No new protocols
    assert stats2["protocols_updated"] == 1  # Updated existing
    
    # Verify only 1 protocol exists
    protocols = await graph_repo.find_nodes("Protocol")
    assert len(protocols) == 1


@pytest.mark.asyncio
async def test_populate_dependencies():
    """Test populating protocol dependencies"""
    
    # Setup
    graph_repo = MockGraphRepository()
    data_provider = MockDefiDataProvider()
    interactor = PopulateGraphInteractor(graph_repo, data_provider)
    
    # Populate protocols first
    await interactor.populate_protocols()
    
    # Populate dependencies
    dependency_map = {
        "Aave": ["Uniswap"],  # Aave depends on Uniswap
    }
    
    stats = await interactor.populate_dependencies(dependency_map)
    
    # Verify
    assert stats["dependencies_created"] == 1
    assert stats["errors"] == 0
    
    # Verify DEPENDS_ON relationship exists
    aave_node = (await graph_repo.find_nodes("Protocol", filters={"name": "Aave"}))[0]
    uniswap_node = (await graph_repo.find_nodes("Protocol", filters={"name": "Uniswap"}))[0]
    
    edges = await graph_repo.find_edges(
        from_id=aave_node.id,
        to_id=uniswap_node.id,
        relationship_type="DEPENDS_ON",
    )
    
    assert len(edges) == 1


@pytest.mark.asyncio
async def test_populate_handles_errors_gracefully():
    """Test that errors in individual protocols don't stop entire population"""
    
    class FailingDataProvider(MockDefiDataProvider):
        async def get_all_protocols(self, limit=None):
            # Return one invalid protocol that will cause error
            protocols = await super().get_all_protocols(limit)
            # Modify first protocol to cause error
            protocols[0].chains = ["InvalidChain" * 100]  # Cause some error
            return protocols
    
    # Setup
    graph_repo = MockGraphRepository()
    data_provider = FailingDataProvider()
    interactor = PopulateGraphInteractor(graph_repo, data_provider)
    
    # Execute
    stats = await interactor.populate_protocols()
    
    # Should still process successfully
    assert stats["protocols_fetched"] == 2
    # May have errors but should continue
    assert stats["protocols_created"] + stats["protocols_updated"] > 0

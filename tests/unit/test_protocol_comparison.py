"""
Unit tests for Protocol Comparison Service.

Tests side-by-side protocol comparison across risk, yield,
security, and network dimensions.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.application.comparison.protocol_comparison_service import (
    ProtocolComparisonService,
    ProtocolMetrics,
)


@pytest.fixture
def comparison_service():
    """Create protocol comparison service."""
    return ProtocolComparisonService()


@pytest.fixture
def sample_protocols():
    """Sample protocol metrics for comparison."""
    return [
        ProtocolMetrics(
            protocol_id=uuid4(),
            protocol_name="Aave V3",
            risk_score=2.1,
            apy=4.5,
            tvl_usd=8_200_000_000,
            audit_count=12,
            network_centrality=0.92,
        ),
        ProtocolMetrics(
            protocol_id=uuid4(),
            protocol_name="Compound",
            risk_score=2.5,
            apy=3.8,
            tvl_usd=3_800_000_000,
            audit_count=10,
            network_centrality=0.88,
        ),
        ProtocolMetrics(
            protocol_id=uuid4(),
            protocol_name="New Protocol",
            risk_score=6.5,
            apy=12.0,
            tvl_usd=50_000_000,
            audit_count=1,
            network_centrality=0.15,
        ),
    ]


class TestProtocolComparison:
    """Test suite for Protocol Comparison Service."""

    @pytest.mark.asyncio
    async def test_compare_protocols_basic(self, comparison_service):
        """Test basic protocol comparison."""
        protocol_ids = [uuid4(), uuid4()]
        
        result = await comparison_service.compare_protocols(protocol_ids)
        
        # Should return comparison structure
        assert "protocols" in result
        assert "comparison_matrix" in result
        assert "winner_by_dimension" in result
        assert "trade_offs" in result
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_minimum_protocols_validation(self, comparison_service):
        """Test that at least 2 protocols are required."""
        with pytest.raises(ValueError, match="at least 2 protocols"):
            await comparison_service.compare_protocols([uuid4()])

    @pytest.mark.asyncio
    async def test_maximum_protocols_validation(self, comparison_service):
        """Test that max 5 protocols can be compared."""
        protocol_ids = [uuid4() for _ in range(6)]
        
        with pytest.raises(ValueError, match="more than 5 protocols"):
            await comparison_service.compare_protocols(protocol_ids)

    @pytest.mark.asyncio
    async def test_comparison_matrix(self, comparison_service, sample_protocols):
        """Test comparison matrix generation."""
        # Mock the fetch to return sample protocols
        comparison_service._fetch_protocol_metrics = AsyncMock(
            return_value=sample_protocols
        )
        
        protocol_ids = [p.protocol_id for p in sample_protocols]
        result = await comparison_service.compare_protocols(protocol_ids)
        
        matrix = result["comparison_matrix"]
        
        # Should have entries for each dimension
        assert "risk" in matrix
        assert "yield" in matrix
        assert "security" in matrix
        
        # Each dimension should have protocol comparisons
        for dimension, comparisons in matrix.items():
            assert len(comparisons) == 3  # 3 protocols

    @pytest.mark.asyncio
    async def test_winner_determination(self, comparison_service, sample_protocols):
        """Test that winners are correctly determined for each dimension."""
        comparison_service._fetch_protocol_metrics = AsyncMock(
            return_value=sample_protocols
        )
        
        protocol_ids = [p.protocol_id for p in sample_protocols]
        result = await comparison_service.compare_protocols(protocol_ids)
        
        winners = result["winner_by_dimension"]
        
        # Risk winner should be lowest risk (Aave at 2.1)
        assert winners["risk"]["protocol_name"] == "Aave V3"
        
        # Yield winner should be highest APY (New Protocol at 12.0)
        assert winners["yield"]["protocol_name"] == "New Protocol"
        
        # Security winner should be most audits (Aave at 12)
        assert winners["security"]["protocol_name"] == "Aave V3"
        
        # Network winner should be highest centrality (Aave at 0.92)
        assert winners["network"]["protocol_name"] == "Aave V3"

    @pytest.mark.asyncio
    async def test_tradeoffs_identification(self, comparison_service, sample_protocols):
        """Test identification of trade-offs between protocols."""
        comparison_service._fetch_protocol_metrics = AsyncMock(
            return_value=sample_protocols
        )
        
        protocol_ids = [p.protocol_id for p in sample_protocols]
        result = await comparison_service.compare_protocols(protocol_ids)
        
        tradeoffs = result["trade_offs"]
        
        # Should identify key trade-offs
        assert len(tradeoffs) > 0
        
        # Should mention yield vs risk trade-off
        # (New Protocol has high yield but also high risk)
        tradeoff_text = " ".join(t["description"] for t in tradeoffs)
        assert "yield" in tradeoff_text.lower() or "apy" in tradeoff_text.lower()

    @pytest.mark.asyncio
    async def test_ai_recommendation(self, comparison_service, sample_protocols):
        """Test AI-powered recommendation generation."""
        comparison_service._fetch_protocol_metrics = AsyncMock(
            return_value=sample_protocols
        )
        
        protocol_ids = [p.protocol_id for p in sample_protocols]
        result = await comparison_service.compare_protocols(protocol_ids)
        
        recommendation = result["recommendation"]
        
        # Should provide a recommendation
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0
        
        # Should mention at least one protocol
        protocol_names = [p.protocol_name for p in sample_protocols]
        assert any(name in recommendation for name in protocol_names)

    @pytest.mark.asyncio
    async def test_custom_dimensions(self, comparison_service):
        """Test comparison with custom dimension selection."""
        protocol_ids = [uuid4(), uuid4()]
        dimensions = ["risk", "yield"]  # Only compare these
        
        result = await comparison_service.compare_protocols(
            protocol_ids, dimensions=dimensions
        )
        
        # Matrix should only contain selected dimensions
        matrix = result["comparison_matrix"]
        assert set(matrix.keys()) == {"risk", "yield"}

    @pytest.mark.asyncio
    async def test_protocol_serialization(self, comparison_service, sample_protocols):
        """Test that protocol metrics are correctly serialized."""
        comparison_service._fetch_protocol_metrics = AsyncMock(
            return_value=sample_protocols
        )
        
        protocol_ids = [p.protocol_id for p in sample_protocols]
        result = await comparison_service.compare_protocols(protocol_ids)
        
        protocols = result["protocols"]
        
        # Should serialize all protocols
        assert len(protocols) == 3
        
        # Each should have required fields
        for p in protocols:
            assert "protocol_id" in p
            assert "protocol_name" in p
            assert "risk_score" in p
            assert "apy" in p
            assert "tvl_usd" in p

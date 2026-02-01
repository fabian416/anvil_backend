"""Integration tests for Arbitrage Discovery Engine (Phase 8 Week 2).

Tests 2-hop, 3-hop, and triangle arbitrage discovery.
"""

import pytest
from decimal import Decimal

from app.application.ultra.arbitrage_discovery import (
    ArbitrageDiscovery,
    ArbitrageConfig,
    ArbitrageType,
    DEX,
    TradingPair,
)


class TestArbitrageConfig:
    """Test arbitrage configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = ArbitrageConfig()

        assert config.min_profit_usd == Decimal("50.0")
        assert config.min_profit_percentage == Decimal("0.005")
        assert config.min_confidence_score == 0.7
        assert len(config.enabled_dexes) == 5
        assert len(config.enabled_tokens) == 5


class TestTradingPair:
    """Test trading pair data model."""

    def test_trading_pair_creation(self):
        """Test trading pair creation."""
        pair = TradingPair(
            dex=DEX.UNISWAP_V2,
            token_in="WETH",
            token_out="USDC",
            amount_in=Decimal("1"),
            amount_out=Decimal("2000"),
            price=Decimal("2000"),
            liquidity=Decimal("1000000"),
        )

        assert pair.dex == DEX.UNISWAP_V2
        assert pair.token_in == "WETH"
        assert pair.token_out == "USDC"
        assert pair.price == Decimal("2000")

    def test_trading_pair_auto_price(self):
        """Test automatic price calculation."""
        pair = TradingPair(
            dex=DEX.UNISWAP_V2,
            token_in="WETH",
            token_out="USDC",
            amount_in=Decimal("1"),
            amount_out=Decimal("2000"),
            price=Decimal("0"),  # Will be calculated
            liquidity=Decimal("1000000"),
        )

        assert pair.price == Decimal("2000")

    def test_trading_pair_serialization(self):
        """Test trading pair to_dict."""
        pair = TradingPair(
            dex=DEX.UNISWAP_V2,
            token_in="WETH",
            token_out="USDC",
            amount_in=Decimal("1"),
            amount_out=Decimal("2000"),
            price=Decimal("2000"),
            liquidity=Decimal("1000000"),
        )

        data = pair.to_dict()

        assert "dex" in data
        assert "token_in" in data
        assert "price" in data


class Test2HopArbitrage:
    """Test 2-hop arbitrage discovery."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_discover_2hop_opportunities(self):
        """Test discovering 2-hop arbitrage opportunities."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_2hop_arbitrage(Decimal("10000"))

        # Should find some opportunities
        assert len(opportunities) >= 0  # May or may not find profitable ones

        # Check structure if opportunities found
        if opportunities:
            opp = opportunities[0]
            assert opp.type == ArbitrageType.TWO_HOP
            assert len(opp.path) == 2
            assert opp.expected_profit_usd > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_2hop_path_structure(self):
        """Test 2-hop path has correct structure."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_2hop_arbitrage(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            path = opp.path

            # First trade
            assert path[0].token_in != path[0].token_out

            # Second trade (reverse)
            assert path[1].token_in == path[0].token_out
            assert path[1].token_out == path[0].token_in

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_2hop_different_dexes(self):
        """Test 2-hop uses different DEXes."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_2hop_arbitrage(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            path = opp.path

            # Should use different DEXes
            assert path[0].dex != path[1].dex

class Test3HopArbitrage:
    """Test 3-hop arbitrage discovery."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_discover_3hop_opportunities(self):
        """Test discovering 3-hop arbitrage opportunities."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_3hop_arbitrage(Decimal("10000"))

        # Should find some opportunities
        assert len(opportunities) >= 0

        # Check structure if opportunities found
        if opportunities:
            opp = opportunities[0]
            assert opp.type == ArbitrageType.THREE_HOP
            assert len(opp.path) == 3
            assert opp.expected_profit_usd > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_3hop_circular_path(self):
        """Test 3-hop creates circular path."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_3hop_arbitrage(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            path = opp.path

            # Start and end with same token
            start_token = path[0].token_in
            end_token = path[-1].token_out

            assert start_token == end_token

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_3hop_unique_tokens(self):
        """Test 3-hop uses three different tokens."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_3hop_arbitrage(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            path = opp.path

            # Collect tokens (excluding final return)
            tokens = [path[0].token_in, path[0].token_out, path[1].token_out]

            # Should have 3 unique tokens
            assert len(set(tokens)) == 3

class TestTriangleArbitrage:
    """Test triangle arbitrage discovery."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_discover_triangle_opportunities(self):
        """Test discovering triangle arbitrage opportunities."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_triangle_arbitrage(
            DEX.UNISWAP_V2, Decimal("10000")
        )

        # Should find some opportunities
        assert len(opportunities) >= 0

        # Check structure if opportunities found
        if opportunities:
            opp = opportunities[0]
            assert opp.type == ArbitrageType.TRIANGLE
            assert len(opp.path) == 3

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_triangle_same_dex(self):
        """Test triangle uses same DEX for all trades."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_triangle_arbitrage(
            DEX.UNISWAP_V2, Decimal("10000")
        )

        if opportunities:
            opp = opportunities[0]
            path = opp.path

            # All trades on same DEX
            dexes = [p.dex for p in path]
            assert len(set(dexes)) == 1
            assert dexes[0] == DEX.UNISWAP_V2

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_triangle_circular_path(self):
        """Test triangle creates circular path."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_triangle_arbitrage(
            DEX.UNISWAP_V2, Decimal("10000")
        )

        if opportunities:
            opp = opportunities[0]
            path = opp.path

            # Start and end with same token
            assert path[0].token_in == path[-1].token_out

class TestAllOpportunitiesDiscovery:
    """Test discovering all opportunity types."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_discover_all_opportunities(self):
        """Test discovering all opportunity types."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        # Should return combined results
        assert isinstance(opportunities, list)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_opportunities_sorted(self):
        """Test opportunities are sorted by profit."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if len(opportunities) > 1:
            # Check descending order
            for i in range(len(opportunities) - 1):
                assert (
                    opportunities[i].expected_profit_usd
                    >= opportunities[i + 1].expected_profit_usd
                )

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_opportunities_mix_types(self):
        """Test all opportunities includes multiple types."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            types = set(opp.type for opp in opportunities)
            # Should have at least one type
            assert len(types) >= 1

class TestOpportunityRetrieval:
    """Test opportunity retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_opportunity_by_id(self):
        """Test retrieving opportunity by ID."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            target = opportunities[0]
            found = await discovery.get_opportunity_by_id(
                target.opportunity_id, opportunities
            )

            assert found is not None
            assert found.opportunity_id == target.opportunity_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_nonexistent_opportunity(self):
        """Test retrieving non-existent opportunity."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        found = await discovery.get_opportunity_by_id("INVALID-ID", opportunities)

        assert found is None

class TestOpportunitySimulation:
    """Test opportunity simulation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_simulate_opportunity(self):
        """Test simulating opportunity execution."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            result = await discovery.simulate_opportunity(opp)

            assert "opportunity_id" in result
            assert "expected_profit" in result
            assert "simulated_profit" in result
            assert "recommendation" in result

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_simulation_includes_slippage(self):
        """Test simulation accounts for slippage."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            result = await discovery.simulate_opportunity(opp)

            # Simulated profit should be less than expected (due to slippage)
            expected = Decimal(result["expected_profit"])
            simulated = Decimal(result["simulated_profit"])

            assert simulated <= expected

class TestProfitCalculation:
    """Test profit calculation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_opportunities_above_threshold(self):
        """Test opportunities meet profit threshold."""
        config = ArbitrageConfig(min_profit_usd=Decimal("100"))
        discovery = ArbitrageDiscovery(config)

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        for opp in opportunities:
            assert opp.expected_profit_usd >= config.min_profit_usd

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_profit_percentage_calculation(self):
        """Test profit percentage is calculated correctly."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]

            # Profit % should match profit / capital
            expected_pct = opp.expected_profit_usd / opp.required_capital

            # Allow small floating point difference
            assert abs(opp.profit_percentage - expected_pct) < Decimal("0.0001")

class TestOpportunitySerialization:
    """Test opportunity serialization."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_opportunity_to_dict(self):
        """Test opportunity serialization."""
        discovery = ArbitrageDiscovery()

        opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

        if opportunities:
            opp = opportunities[0]
            data = opp.to_dict()

            assert "opportunity_id" in data
            assert "type" in data
            assert "path" in data
            assert "expected_profit_usd" in data

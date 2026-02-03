"""
Unit tests for Hyperliquid perpetual futures adapter.

Tests the HyperliquidAdapter structure and protocol compliance.
Integration tests with actual API should be in tests/integration/.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_hyperliquid_client():
    """Create a mocked HyperliquidClient."""
    client = MagicMock()
    client.get_markets = AsyncMock(return_value=[])
    client.get_funding_rates = AsyncMock(return_value={})
    client.get_order_book = AsyncMock(return_value={})
    client.get_positions = AsyncMock(return_value=[])
    client.get_account = AsyncMock(return_value={})
    return client


@pytest.fixture
def mock_cache():
    """Create a mocked ExternalAPICache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.mark.unit
class TestHyperliquidAdapterStructure:
    """Tests for HyperliquidAdapter structure and protocol compliance."""

    def test_hyperliquid_adapter_imports(self):
        """Test HyperliquidAdapter can be imported."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        assert HyperliquidAdapter is not None

    def test_hyperliquid_adapter_implements_gateway(self):
        """Test HyperliquidAdapter implements PerpetualGateway protocol."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        # Verify it has all required methods from the protocol
        assert hasattr(HyperliquidAdapter, "get_markets")
        assert hasattr(HyperliquidAdapter, "get_funding_rates")
        assert hasattr(HyperliquidAdapter, "get_order_book")
        assert hasattr(HyperliquidAdapter, "get_positions")

    def test_hyperliquid_adapter_init(self, mock_hyperliquid_client, mock_cache):
        """Test HyperliquidAdapter can be initialized."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        adapter = HyperliquidAdapter(client=mock_hyperliquid_client, cache=mock_cache)
        assert adapter is not None


@pytest.mark.unit
class TestHyperliquidAdapterMethods:
    """Tests for HyperliquidAdapter methods existence."""

    @pytest.mark.asyncio
    async def test_get_markets_exists(self, mock_hyperliquid_client, mock_cache):
        """Test get_markets method exists."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        adapter = HyperliquidAdapter(client=mock_hyperliquid_client, cache=mock_cache)
        assert hasattr(adapter, "get_markets")
        assert callable(adapter.get_markets)

    @pytest.mark.asyncio
    async def test_get_funding_rates_exists(self, mock_hyperliquid_client, mock_cache):
        """Test get_funding_rates method exists."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        adapter = HyperliquidAdapter(client=mock_hyperliquid_client, cache=mock_cache)
        assert hasattr(adapter, "get_funding_rates")
        assert callable(adapter.get_funding_rates)

    @pytest.mark.asyncio
    async def test_get_order_book_exists(self, mock_hyperliquid_client, mock_cache):
        """Test get_order_book method exists."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        adapter = HyperliquidAdapter(client=mock_hyperliquid_client, cache=mock_cache)
        assert hasattr(adapter, "get_order_book")
        assert callable(adapter.get_order_book)

    @pytest.mark.asyncio
    async def test_get_positions_exists(self, mock_hyperliquid_client, mock_cache):
        """Test get_positions method exists."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import (
            HyperliquidAdapter,
        )

        adapter = HyperliquidAdapter(client=mock_hyperliquid_client, cache=mock_cache)
        assert hasattr(adapter, "get_positions")
        assert callable(adapter.get_positions)


@pytest.mark.unit
class TestHyperliquidClientStructure:
    """Tests for HyperliquidClient structure."""

    def test_hyperliquid_client_imports(self):
        """Test HyperliquidClient can be imported."""
        from app.infrastructure.adapters.external.hyperliquid_client import (
            HyperliquidClient,
        )

        assert HyperliquidClient is not None

    def test_funding_rate_dataclass(self):
        """Test FundingRate dataclass."""
        from app.infrastructure.adapters.external.hyperliquid_client import FundingRate

        rate = FundingRate(
            symbol="BTC-PERP",
            funding_rate=Decimal("0.0001"),
            next_funding_time="2024-01-01T00:00:00Z",
            timestamp=1704067200,
        )

        assert rate.symbol == "BTC-PERP"
        assert rate.funding_rate == Decimal("0.0001")


@pytest.mark.unit
class TestHyperliquidExceptions:
    """Tests for Hyperliquid exceptions."""

    def test_hyperliquid_api_error(self):
        """Test HyperliquidAPIError exists."""
        try:
            from app.domain.exceptions.perpetual import HyperliquidAPIError

            error = HyperliquidAPIError("Test error")
            assert "Test error" in str(error)
        except ImportError:
            pytest.skip("Perpetual exceptions not implemented")

    def test_market_not_found_error(self):
        """Test MarketNotFoundError exists."""
        try:
            from app.domain.exceptions.perpetual import MarketNotFoundError

            error = MarketNotFoundError("BTC-PERP")
            assert "BTC-PERP" in str(error)
        except ImportError:
            pytest.skip("Perpetual exceptions not implemented")

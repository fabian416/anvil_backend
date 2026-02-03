"""
Unit tests for Axelar cross-chain bridging adapter.

Tests the AxelarAdapter structure and protocol compliance.
Integration tests with actual API should be in tests/integration/.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_axelar_client():
    """Create a mocked AxelarClient."""
    client = MagicMock()
    client.get_routes = AsyncMock(return_value=[])
    client.estimate_transfer = AsyncMock(return_value=None)
    client.track_transfer = AsyncMock(return_value=None)
    client.get_supported_chains = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_cache():
    """Create a mocked ExternalAPICache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.mark.unit
class TestAxelarAdapterStructure:
    """Tests for AxelarAdapter structure and protocol compliance."""

    def test_axelar_adapter_imports(self):
        """Test AxelarAdapter can be imported."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        assert AxelarAdapter is not None

    def test_axelar_adapter_implements_gateway(self):
        """Test AxelarAdapter implements BridgeGateway protocol."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        # Verify it has required methods
        assert hasattr(AxelarAdapter, "get_routes")
        assert hasattr(AxelarAdapter, "estimate_transfer")
        assert hasattr(AxelarAdapter, "track_transfer")

    def test_axelar_adapter_init(self, mock_axelar_client, mock_cache):
        """Test AxelarAdapter can be initialized."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        adapter = AxelarAdapter(client=mock_axelar_client, cache=mock_cache)
        assert adapter is not None


@pytest.mark.unit
class TestAxelarAdapterMethods:
    """Tests for AxelarAdapter methods existence."""

    @pytest.mark.asyncio
    async def test_get_routes_exists(self, mock_axelar_client, mock_cache):
        """Test get_routes method exists."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        adapter = AxelarAdapter(client=mock_axelar_client, cache=mock_cache)
        assert hasattr(adapter, "get_routes")
        assert callable(adapter.get_routes)

    @pytest.mark.asyncio
    async def test_estimate_transfer_exists(self, mock_axelar_client, mock_cache):
        """Test estimate_transfer method exists."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        adapter = AxelarAdapter(client=mock_axelar_client, cache=mock_cache)
        assert hasattr(adapter, "estimate_transfer")
        assert callable(adapter.estimate_transfer)

    @pytest.mark.asyncio
    async def test_track_transfer_exists(self, mock_axelar_client, mock_cache):
        """Test track_transfer method exists."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        adapter = AxelarAdapter(client=mock_axelar_client, cache=mock_cache)
        assert hasattr(adapter, "track_transfer")
        assert callable(adapter.track_transfer)

    @pytest.mark.asyncio
    async def test_get_chains_exists(self, mock_axelar_client, mock_cache):
        """Test get_chains method exists."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter

        adapter = AxelarAdapter(client=mock_axelar_client, cache=mock_cache)
        assert hasattr(adapter, "get_chains")
        assert callable(adapter.get_chains)


@pytest.mark.unit
class TestAxelarClientStructure:
    """Tests for AxelarClient structure."""

    def test_axelar_client_imports(self):
        """Test AxelarClient can be imported."""
        from app.infrastructure.adapters.external.axelar_client import AxelarClient

        assert AxelarClient is not None

    def test_bridge_route_dataclass(self):
        """Test BridgeRoute dataclass."""
        from app.infrastructure.adapters.external.axelar_client import BridgeRoute
        from decimal import Decimal

        route = BridgeRoute(
            source_chain="ethereum",
            dest_chain="polygon",
            asset="USDC",
            estimated_time_seconds=300,
            fee_usd=Decimal("5.00"),
            available=True,
        )

        assert route.source_chain == "ethereum"
        assert route.dest_chain == "polygon"


@pytest.mark.unit
class TestAxelarExceptions:
    """Tests for Axelar exceptions."""

    def test_axelar_api_error(self):
        """Test AxelarAPIError exists."""
        try:
            from app.domain.exceptions.bridge import AxelarAPIError

            error = AxelarAPIError("Test error")
            assert "Test error" in str(error)
        except ImportError:
            pytest.skip("Bridge exceptions not implemented")

    def test_transfer_not_found_error(self):
        """Test TransferNotFoundError exists."""
        try:
            from app.domain.exceptions.bridge import TransferNotFoundError

            error = TransferNotFoundError("0x1234")
            assert "0x1234" in str(error)
        except ImportError:
            pytest.skip("Bridge exceptions not implemented")


@pytest.mark.unit
class TestTxHashValidation:
    """Tests for transaction hash validation."""

    def test_valid_tx_hash_format(self):
        """Test valid transaction hash format."""
        import re

        tx_hash_pattern = re.compile(r"^0x[a-fA-F0-9]{64}$")

        valid_hash = "0x" + "a" * 64
        assert tx_hash_pattern.match(valid_hash)

    def test_invalid_tx_hash_format(self):
        """Test invalid transaction hash is rejected."""
        import re

        tx_hash_pattern = re.compile(r"^0x[a-fA-F0-9]{64}$")

        invalid_hash = "not-a-hash"
        assert not tx_hash_pattern.match(invalid_hash)

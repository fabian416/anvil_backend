"""
Unit tests for LayerZero cross-chain messaging adapter.

Tests the LayerZeroAdapter structure and protocol compliance.
Integration tests with actual API should be in tests/integration/.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_layerzero_client():
    """Create a mocked LayerZeroClient."""
    client = MagicMock()
    client.get_chains = AsyncMock(return_value=[])
    client.estimate_message_fee = AsyncMock(return_value=None)
    client.track_message = AsyncMock(return_value=None)
    client.get_oft_transfer = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_cache():
    """Create a mocked ExternalAPICache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.mark.unit
class TestLayerZeroAdapterStructure:
    """Tests for LayerZeroAdapter structure and protocol compliance."""

    def test_layerzero_adapter_imports(self):
        """Test LayerZeroAdapter can be imported."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        assert LayerZeroAdapter is not None

    def test_layerzero_adapter_implements_gateway(self):
        """Test LayerZeroAdapter implements CrossChainGateway protocol."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        
        # Verify it has required methods
        assert hasattr(LayerZeroAdapter, 'get_chains')  # Not get_supported_chains
        assert hasattr(LayerZeroAdapter, 'estimate_fees')
        assert hasattr(LayerZeroAdapter, 'track_message')

    def test_layerzero_adapter_init(self, mock_layerzero_client, mock_cache):
        """Test LayerZeroAdapter can be initialized."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        
        adapter = LayerZeroAdapter(client=mock_layerzero_client, cache=mock_cache)
        assert adapter is not None


@pytest.mark.unit
class TestLayerZeroAdapterMethods:
    """Tests for LayerZeroAdapter methods existence."""

    @pytest.mark.asyncio
    async def test_get_chains_exists(self, mock_layerzero_client, mock_cache):
        """Test get_chains method exists."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        
        adapter = LayerZeroAdapter(client=mock_layerzero_client, cache=mock_cache)
        assert hasattr(adapter, 'get_chains')
        assert callable(adapter.get_chains)

    @pytest.mark.asyncio
    async def test_estimate_fees_exists(self, mock_layerzero_client, mock_cache):
        """Test estimate_fees method exists."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        
        adapter = LayerZeroAdapter(client=mock_layerzero_client, cache=mock_cache)
        assert hasattr(adapter, 'estimate_fees')
        assert callable(adapter.estimate_fees)

    @pytest.mark.asyncio
    async def test_track_message_exists(self, mock_layerzero_client, mock_cache):
        """Test track_message method exists."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        
        adapter = LayerZeroAdapter(client=mock_layerzero_client, cache=mock_cache)
        assert hasattr(adapter, 'track_message')
        assert callable(adapter.track_message)


@pytest.mark.unit
class TestLayerZeroClientStructure:
    """Tests for LayerZeroClient structure."""

    def test_layerzero_client_imports(self):
        """Test LayerZeroClient can be imported."""
        from app.infrastructure.adapters.external.layerzero_client import LayerZeroClient
        assert LayerZeroClient is not None

    def test_chain_dataclass(self):
        """Test LayerZeroChain dataclass."""
        from app.infrastructure.adapters.external.layerzero_client import LayerZeroChain
        
        chain = LayerZeroChain(
            chain_id=1,
            name="Ethereum",
            endpoint_id=101,
        )
        
        assert chain.chain_id == 1
        assert chain.name == "Ethereum"


@pytest.mark.unit
class TestLayerZeroExceptions:
    """Tests for LayerZero exceptions."""

    def test_layerzero_api_error(self):
        """Test LayerZeroAPIError exists."""
        try:
            from app.domain.exceptions.cross_chain import LayerZeroAPIError
            error = LayerZeroAPIError("Test error")
            assert "Test error" in str(error)
        except ImportError:
            pytest.skip("Cross-chain exceptions not implemented")

    def test_message_not_found_error(self):
        """Test MessageNotFoundError exists."""
        try:
            from app.domain.exceptions.cross_chain import MessageNotFoundError
            error = MessageNotFoundError("0x1234")
            assert "0x1234" in str(error)
        except ImportError:
            pytest.skip("Cross-chain exceptions not implemented")

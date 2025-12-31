"""
Unit tests for Morpho Protocol lending adapter.

Tests the MorphoAdapter structure and protocol compliance.
Integration tests with actual API should be in tests/integration/.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_morpho_client():
    """Create a mocked MorphoClient."""
    client = MagicMock()
    client.get_vaults = AsyncMock(return_value=[])
    client.get_vault = AsyncMock(return_value=None)
    client.get_user_positions = AsyncMock(return_value=[])
    client.get_markets = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_cache():
    """Create a mocked ExternalAPICache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.mark.unit
class TestMorphoAdapterStructure:
    """Tests for MorphoAdapter structure and protocol compliance."""

    def test_morpho_adapter_imports(self):
        """Test MorphoAdapter can be imported."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        assert MorphoAdapter is not None

    def test_morpho_adapter_implements_gateway(self):
        """Test MorphoAdapter implements MorphoGateway protocol."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        
        # Verify it has required methods
        assert hasattr(MorphoAdapter, 'get_vaults')
        assert hasattr(MorphoAdapter, 'get_vault_apy')
        assert hasattr(MorphoAdapter, 'get_user_positions')

    def test_morpho_adapter_init(self, mock_morpho_client, mock_cache):
        """Test MorphoAdapter can be initialized."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        
        adapter = MorphoAdapter(client=mock_morpho_client, cache=mock_cache)
        assert adapter is not None


@pytest.mark.unit
class TestMorphoAdapterMethods:
    """Tests for MorphoAdapter methods existence."""

    @pytest.mark.asyncio
    async def test_get_vaults_exists(self, mock_morpho_client, mock_cache):
        """Test get_vaults method exists."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        
        adapter = MorphoAdapter(client=mock_morpho_client, cache=mock_cache)
        assert hasattr(adapter, 'get_vaults')
        assert callable(adapter.get_vaults)

    @pytest.mark.asyncio
    async def test_get_vault_apy_exists(self, mock_morpho_client, mock_cache):
        """Test get_vault_apy method exists."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        
        adapter = MorphoAdapter(client=mock_morpho_client, cache=mock_cache)
        assert hasattr(adapter, 'get_vault_apy')
        assert callable(adapter.get_vault_apy)

    @pytest.mark.asyncio
    async def test_get_user_positions_exists(self, mock_morpho_client, mock_cache):
        """Test get_user_positions method exists."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        
        adapter = MorphoAdapter(client=mock_morpho_client, cache=mock_cache)
        assert hasattr(adapter, 'get_user_positions')
        assert callable(adapter.get_user_positions)


@pytest.mark.unit
class TestMorphoClientStructure:
    """Tests for MorphoClient structure."""

    def test_morpho_client_imports(self):
        """Test MorphoClient can be imported."""
        from app.infrastructure.adapters.external.morpho_client import MorphoClient
        assert MorphoClient is not None

    def test_vault_data_dataclass(self):
        """Test MorphoVaultData dataclass."""
        from app.infrastructure.adapters.external.morpho_client import MorphoVaultData
        
        vault = MorphoVaultData(
            id="0x1234",
            name="USDC Vault",
            symbol="mvUSDC",
            asset_address="0x5678",
            asset_symbol="USDC",
            asset_decimals=6,
            total_assets="1000000",
            total_supply="1000000",
            performance_fee="0.1",
            curator="0xcurator",
            guardian="0xguardian",
            allocations=[],
            chain_id=1,
            whitelisted=False,
            net_apy="0.05",
            daily_apy="0.05",
        )
        
        assert vault.id == "0x1234"
        assert vault.name == "USDC Vault"
        assert vault.chain_id == 1
        
    def test_vault_data_base_chain(self):
        """Test MorphoVaultData for Base chain."""
        from app.infrastructure.adapters.external.morpho_client import MorphoVaultData, BASE_USDC_ADDRESS
        
        vault = MorphoVaultData(
            id="0xabcd",
            name="Base USDC Vault",
            symbol="mvUSDC",
            asset_address=BASE_USDC_ADDRESS,
            asset_symbol="USDC",
            asset_decimals=6,
            total_assets="1000000",
            total_supply="1000000",
            performance_fee="0.05",
            curator=None,
            guardian=None,
            chain_id=8453,  # Base
            whitelisted=True,
            net_apy="0.12",
        )
        
        assert vault.chain_id == 8453
        assert vault.whitelisted is True
        assert vault.asset_address == BASE_USDC_ADDRESS


@pytest.mark.unit
class TestMorphoExceptions:
    """Tests for Morpho exceptions."""

    def test_morpho_api_error(self):
        """Test MorphoAPIError exists."""
        from app.domain.exceptions.morpho import MorphoAPIError
        
        error = MorphoAPIError("Test error")
        assert "Test error" in str(error)

    def test_vault_not_found_error(self):
        """Test VaultNotFoundError exists."""
        from app.domain.exceptions.morpho import VaultNotFoundError
        
        error = VaultNotFoundError("0x1234")
        assert "0x1234" in str(error)


@pytest.mark.unit
class TestAddressValidation:
    """Tests for address validation."""

    def test_valid_address_format(self):
        """Test valid Ethereum address format."""
        import re
        address_pattern = re.compile(r"^0x[a-fA-F0-9]{40}$")
        
        valid_address = "0x1234567890123456789012345678901234567890"
        assert address_pattern.match(valid_address)

    def test_invalid_address_format(self):
        """Test invalid address is rejected."""
        import re
        address_pattern = re.compile(r"^0x[a-fA-F0-9]{40}$")
        
        invalid_address = "not-an-address"
        assert not address_pattern.match(invalid_address)

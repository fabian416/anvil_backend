"""
Unit tests for AaveAdapter.

Tests the Aave V3 gateway adapter implementation:
- Market data retrieval
- User position tracking
- Health factor calculations
- Caching behavior
- Error handling
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.domain.exceptions.aave import (
    AaveError,
    AaveAPIError,
    InvalidAddressError,
    MarketNotFoundError,
    PositionNotFoundError,
    UnsupportedChainError,
    HealthFactorTooLowError,
    InsufficientCollateralError,
    BorrowCapReachedError,
    SupplyCapReachedError,
    SubgraphError,
    RateLimitError,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_cache():
    """Create a mock ExternalAPICache."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    return mock


# =============================================================================
# Adapter Structure Tests
# =============================================================================


@pytest.mark.unit
class TestAaveAdapterStructure:
    """Test AaveAdapter basic structure and imports."""

    def test_aave_adapter_imports(self):
        """Test AaveAdapter can be imported."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        assert AaveAdapter is not None

    def test_aave_adapter_implements_gateway(self):
        """Test AaveAdapter has required gateway methods."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        # Check all required gateway methods
        assert hasattr(AaveAdapter, "get_markets")
        assert hasattr(AaveAdapter, "get_market_details")
        assert hasattr(AaveAdapter, "get_user_position")
        assert hasattr(AaveAdapter, "get_health_factor")
        assert hasattr(AaveAdapter, "calculate_health_factor")
        assert hasattr(AaveAdapter, "get_available_to_borrow")
        assert hasattr(AaveAdapter, "get_liquidation_threshold")
        assert hasattr(AaveAdapter, "get_protocol_stats")
        assert hasattr(AaveAdapter, "get_supply_apy")
        assert hasattr(AaveAdapter, "get_borrow_apy")

    def test_aave_adapter_init(self, mock_cache):
        """Test AaveAdapter initialization."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(
            cache=mock_cache,
            api_key="test-key",
        )
        assert adapter is not None
        assert adapter._cache is mock_cache
        assert adapter._api_key == "test-key"

    def test_aave_adapter_cache_ttl_config(self, mock_cache):
        """Test AaveAdapter cache TTL configuration."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(
            cache=mock_cache,
            market_cache_ttl=600,
            position_cache_ttl=180,
            stats_cache_ttl=900,
        )
        assert adapter._market_cache_ttl == 600
        assert adapter._position_cache_ttl == 180
        assert adapter._stats_cache_ttl == 900


# =============================================================================
# Gateway Port Tests
# =============================================================================


@pytest.mark.unit
class TestAaveGateway:
    """Test AaveGateway port definition."""

    def test_aave_gateway_imports(self):
        """Test AaveGateway can be imported."""
        from app.domain.ports.aave_gateway import AaveGateway

        assert AaveGateway is not None

    def test_aave_gateway_methods(self):
        """Test AaveGateway defines required protocol methods."""
        from app.domain.ports.aave_gateway import AaveGateway
        import inspect

        # Get all methods from protocol
        methods = inspect.getmembers(AaveGateway, predicate=inspect.isfunction)
        method_names = [name for name, _ in methods if not name.startswith("_")]

        # Required methods
        required_methods = [
            "get_markets",
            "get_market_details",
            "get_user_position",
            "get_health_factor",
            "calculate_health_factor",
            "get_available_to_borrow",
            "get_liquidation_threshold",
            "get_protocol_stats",
            "get_supply_apy",
            "get_borrow_apy",
        ]

        for method in required_methods:
            assert method in method_names, f"Gateway missing method: {method}"


# =============================================================================
# Domain Entity Tests
# =============================================================================


@pytest.mark.unit
class TestAaveEntities:
    """Test Aave domain entities."""

    def test_aave_market_entity(self):
        """Test AaveMarket entity structure."""
        from app.domain.entities.lending.aave_market import AaveMarket

        market = AaveMarket(
            asset_address="0x1234",
            symbol="USDC",
            name="USD Coin",
            chain="ethereum",
            supply_apy=Decimal("0.05"),
            borrow_apy_variable=Decimal("0.08"),
            total_supplied=Decimal("1000000"),
            total_supplied_usd=Decimal("1000000"),
            utilization_rate=Decimal("75"),
            ltv=Decimal("0.8"),
            liquidation_threshold=Decimal("0.85"),
        )

        assert market.symbol == "USDC"
        assert market.supply_apy == Decimal("0.05")
        assert market.is_active is True

    def test_aave_market_serialization(self):
        """Test AaveMarket serialization."""
        from app.domain.entities.lending.aave_market import AaveMarket

        market = AaveMarket(
            asset_address="0x1234",
            symbol="WETH",
            name="Wrapped Ether",
        )

        data = market.to_dict()
        assert "asset_address" in data
        assert "symbol" in data
        assert data["symbol"] == "WETH"

        # Test deserialization
        restored = AaveMarket.from_dict(data)
        assert restored.symbol == market.symbol

    def test_aave_position_entity(self):
        """Test AavePosition entity structure."""
        from app.domain.entities.lending.aave_position import (
            AavePosition,
            AaveSupplyPosition,
            AaveBorrowPosition,
        )

        position = AavePosition(
            user_address="0xuser",
            chain="ethereum",
            total_collateral_usd=Decimal("10000"),
            total_debt_usd=Decimal("5000"),
            health_factor=Decimal("1.65"),
            supplies=[
                AaveSupplyPosition(
                    asset_address="0x1",
                    symbol="USDC",
                    balance=Decimal("10000"),
                    balance_usd=Decimal("10000"),
                    apy=Decimal("0.05"),
                    is_collateral=True,
                )
            ],
            borrows=[
                AaveBorrowPosition(
                    asset_address="0x2",
                    symbol="WETH",
                    balance=Decimal("2.5"),
                    balance_usd=Decimal("5000"),
                    apy=Decimal("0.08"),
                    borrow_type="variable",
                )
            ],
        )

        assert position.is_healthy is True
        assert position.is_at_risk is False
        assert len(position.supplies) == 1
        assert len(position.borrows) == 1

    def test_aave_position_liquidatable(self):
        """Test AavePosition liquidation detection."""
        from app.domain.entities.lending.aave_position import AavePosition

        position = AavePosition(
            user_address="0xuser",
            health_factor=Decimal("0.95"),  # Below 1
        )

        assert position.is_healthy is False
        assert position.is_liquidatable is True


# =============================================================================
# Value Object Tests
# =============================================================================


@pytest.mark.unit
class TestAaveValueObjects:
    """Test Aave value objects."""

    def test_health_factor_value_object(self):
        """Test HealthFactor value object."""
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("5000"),
            liquidation_threshold=Decimal("0.825"),
        )

        assert hf.value > 1
        assert hf.risk_level == RiskLevel.MODERATE
        assert not hf.is_liquidatable

    def test_health_factor_infinity(self):
        """Test HealthFactor with no debt."""
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("0"),  # No debt
        )

        assert hf.value == Decimal("inf")
        assert hf.risk_level == RiskLevel.SAFE
        assert not hf.is_liquidatable

    def test_health_factor_liquidatable(self):
        """Test HealthFactor liquidation threshold."""
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("1000"),
            debt_usd=Decimal("1000"),  # HF < 1
            liquidation_threshold=Decimal("0.825"),
        )

        assert hf.value < 1
        assert hf.risk_level == RiskLevel.LIQUIDATABLE
        assert hf.is_liquidatable


# =============================================================================
# Exception Tests
# =============================================================================


@pytest.mark.unit
class TestAaveExceptions:
    """Test Aave domain exceptions."""

    def test_aave_base_error(self):
        """Test AaveError base exception."""
        error = AaveError("Test error")
        assert str(error) == "Test error"
        assert error.error_code == "AAVE_ERROR"

    def test_market_not_found_error(self):
        """Test MarketNotFoundError."""
        error = MarketNotFoundError("USDC", "ethereum")
        assert error.asset == "USDC"
        assert error.chain == "ethereum"
        assert error.error_code == "AAVE_MARKET_NOT_FOUND"
        assert "USDC" in str(error)

    def test_position_not_found_error(self):
        """Test PositionNotFoundError."""
        error = PositionNotFoundError("0x1234", "ethereum")
        assert error.user_address == "0x1234"
        assert error.error_code == "AAVE_POSITION_NOT_FOUND"

    def test_invalid_address_error(self):
        """Test InvalidAddressError."""
        error = InvalidAddressError("invalid-address")
        assert error.address == "invalid-address"
        assert error.error_code == "AAVE_INVALID_ADDRESS"

    def test_unsupported_chain_error(self):
        """Test UnsupportedChainError."""
        error = UnsupportedChainError("solana")
        assert error.chain == "solana"
        assert error.error_code == "AAVE_UNSUPPORTED_CHAIN"

    def test_health_factor_too_low_error(self):
        """Test HealthFactorTooLowError."""
        error = HealthFactorTooLowError("0.95", "1.0")
        assert error.health_factor == "0.95"
        assert error.threshold == "1.0"
        assert error.error_code == "AAVE_HEALTH_FACTOR_TOO_LOW"

    def test_insufficient_collateral_error(self):
        """Test InsufficientCollateralError."""
        error = InsufficientCollateralError("0xuser", "10000", "5000")
        assert error.required == "10000"
        assert error.available == "5000"
        assert error.error_code == "AAVE_INSUFFICIENT_COLLATERAL"

    def test_borrow_cap_reached_error(self):
        """Test BorrowCapReachedError."""
        error = BorrowCapReachedError("USDC", "1000000")
        assert error.asset == "USDC"
        assert error.cap == "1000000"
        assert error.error_code == "AAVE_BORROW_CAP_REACHED"

    def test_supply_cap_reached_error(self):
        """Test SupplyCapReachedError."""
        error = SupplyCapReachedError("WETH", "500000")
        assert error.asset == "WETH"
        assert error.error_code == "AAVE_SUPPLY_CAP_REACHED"

    def test_aave_api_error(self):
        """Test AaveAPIError."""
        error = AaveAPIError("Connection failed", status_code=503)
        assert error.status_code == 503
        assert error.error_code == "AAVE_API_ERROR"
        assert "503" in str(error)

    def test_subgraph_error(self):
        """Test SubgraphError."""
        error = SubgraphError("Query failed", query="{ users { id } }")
        assert error.query == "{ users { id } }"
        assert error.error_code == "AAVE_SUBGRAPH_ERROR"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError(retry_after=60)
        assert error.retry_after == 60
        assert error.error_code == "AAVE_RATE_LIMIT"
        assert "60" in str(error)


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.unit
class TestAaveValidation:
    """Test Aave adapter validation logic."""

    def test_validate_chain_supported(self, mock_cache):
        """Test chain validation for supported chains."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)

        # Should not raise for supported chains
        supported_chains = [
            "ethereum",
            "polygon",
            "arbitrum",
            "optimism",
            "avalanche",
            "base",
        ]
        for chain in supported_chains:
            adapter._validate_chain(chain)

    def test_validate_chain_unsupported(self, mock_cache):
        """Test chain validation raises for unsupported chains."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)

        with pytest.raises(UnsupportedChainError) as exc_info:
            adapter._validate_chain("solana")

        assert exc_info.value.chain == "solana"

    def test_validate_address_valid(self, mock_cache):
        """Test address validation for valid addresses."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)

        # Should not raise for valid address
        adapter._validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD21")

    def test_validate_address_invalid(self, mock_cache):
        """Test address validation raises for invalid addresses."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)

        invalid_addresses = [
            "invalid",
            "0x123",  # Too short
            "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD21extra",  # Too long
            "742d35Cc6634C0532925a3b844Bc9e7595f2bD21",  # Missing 0x
        ]

        for addr in invalid_addresses:
            with pytest.raises(InvalidAddressError):
                adapter._validate_address(addr)


# =============================================================================
# Adapter Functionality Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestAaveAdapterFunctionality:
    """Test AaveAdapter async functionality."""

    async def test_get_markets(self, mock_cache):
        """Test get_markets returns fallback data."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        markets = await adapter.get_markets(chain="ethereum")

        assert len(markets) > 0
        assert all(m.chain == "ethereum" for m in markets)

    async def test_get_markets_filter_by_asset(self, mock_cache):
        """Test get_markets filters by asset."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        markets = await adapter.get_markets(asset="USDC", chain="ethereum")

        assert len(markets) == 1
        assert markets[0].symbol == "USDC"

    async def test_get_market_details(self, mock_cache):
        """Test get_market_details returns single market."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        market = await adapter.get_market_details(asset="WETH", chain="ethereum")

        assert market.symbol == "WETH"

    async def test_get_market_details_not_found(self, mock_cache):
        """Test get_market_details raises for unknown asset."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)

        with pytest.raises(MarketNotFoundError) as exc_info:
            await adapter.get_market_details(asset="UNKNOWN", chain="ethereum")

        assert exc_info.value.asset == "UNKNOWN"

    async def test_get_user_position(self, mock_cache):
        """Test get_user_position returns fallback position."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        position = await adapter.get_user_position(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD21",
            chain="ethereum",
        )

        assert position.user_address == "0x742d35cc6634c0532925a3b844bc9e7595f2bd21"
        assert position.total_collateral_usd > 0

    async def test_get_health_factor(self, mock_cache):
        """Test get_health_factor calculates from position."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        hf = await adapter.get_health_factor(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD21",
            chain="ethereum",
        )

        assert hf.value > 0
        assert not hf.is_liquidatable

    async def test_calculate_health_factor(self, mock_cache):
        """Test calculate_health_factor with given values."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter
        from app.domain.value_objects.lending.health_factor import RiskLevel

        adapter = AaveAdapter(cache=mock_cache)
        hf = await adapter.calculate_health_factor(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("5000"),
            liquidation_threshold=Decimal("0.825"),
        )

        assert hf.value > 1
        assert hf.risk_level == RiskLevel.MODERATE

    async def test_get_protocol_stats(self, mock_cache):
        """Test get_protocol_stats returns fallback stats."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        stats = await adapter.get_protocol_stats(chain="ethereum")

        assert "chain" in stats
        assert stats["chain"] == "ethereum"
        assert "total_tvl_usd" in stats

    async def test_get_supply_apy(self, mock_cache):
        """Test get_supply_apy returns APY for asset."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        apy = await adapter.get_supply_apy(asset="USDC", chain="ethereum")

        assert apy > 0

    async def test_get_borrow_apy(self, mock_cache):
        """Test get_borrow_apy returns APY for asset."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        adapter = AaveAdapter(cache=mock_cache)
        apy = await adapter.get_borrow_apy(asset="USDC", chain="ethereum")

        assert apy > 0

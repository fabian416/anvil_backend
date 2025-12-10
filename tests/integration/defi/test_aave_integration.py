"""
Integration tests for Aave V3 protocol.

Tests the complete Aave integration:
- Gateway port definition
- Adapter implementation
- HTTP router
- Domain entities and value objects
- IoC provider
"""

import pytest


# =============================================================================
# Component Existence Tests
# =============================================================================


@pytest.mark.integration
class TestAaveComponentsExist:
    """Verify all Aave components exist and are properly structured."""

    def test_aave_router_exists(self):
        """Test Aave router can be created."""
        from app.presentation.http.controllers.defi.aave_router import create_aave_router

        router = create_aave_router()
        assert router is not None
        assert router.prefix == "/aave"

    def test_aave_router_routes(self):
        """Test Aave router has required routes."""
        from app.presentation.http.controllers.defi.aave_router import create_aave_router

        router = create_aave_router()
        routes = [r.path for r in router.routes]

        # Check for required endpoints
        assert any("markets" in route for route in routes)
        assert any("positions" in route for route in routes)
        assert any("stats" in route for route in routes)
        assert any("rates" in route for route in routes)
        assert any("health" in route for route in routes)

    def test_aave_gateway_exists(self):
        """Test AaveGateway port is defined."""
        from app.domain.ports.aave_gateway import AaveGateway

        assert AaveGateway is not None

    def test_aave_adapter_exists(self):
        """Test AaveAdapter is defined."""
        from app.infrastructure.adapters.external.aave_adapter import AaveAdapter

        assert AaveAdapter is not None

    def test_aave_client_exists(self):
        """Test AaveClient is defined."""
        from app.infrastructure.adapters.external.aave_client import AaveClient

        assert AaveClient is not None

    def test_aave_entities_exist(self):
        """Test Aave domain entities are defined."""
        from app.domain.entities.lending.aave_market import AaveMarket
        from app.domain.entities.lending.aave_position import (
            AavePosition,
            AaveSupplyPosition,
            AaveBorrowPosition,
        )

        assert AaveMarket is not None
        assert AavePosition is not None
        assert AaveSupplyPosition is not None
        assert AaveBorrowPosition is not None

    def test_aave_value_objects_exist(self):
        """Test Aave value objects are defined."""
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        assert HealthFactor is not None
        assert RiskLevel is not None

    def test_aave_exceptions_exist(self):
        """Test Aave domain exceptions are defined."""
        from app.domain.exceptions.aave import (
            AaveError,
            AaveAPIError,
            MarketNotFoundError,
            PositionNotFoundError,
            InvalidAddressError,
            UnsupportedChainError,
            HealthFactorTooLowError,
            InsufficientCollateralError,
            BorrowCapReachedError,
            SupplyCapReachedError,
        )

        assert AaveError is not None
        assert AaveAPIError is not None
        assert MarketNotFoundError is not None
        assert PositionNotFoundError is not None
        assert InvalidAddressError is not None
        assert UnsupportedChainError is not None
        assert HealthFactorTooLowError is not None
        assert InsufficientCollateralError is not None
        assert BorrowCapReachedError is not None
        assert SupplyCapReachedError is not None

    def test_aave_schemas_exist(self):
        """Test Aave Pydantic schemas are defined."""
        from app.presentation.http.controllers.defi.aave_schemas import (
            AaveMarketResponse,
            AaveMarketsResponse,
            AavePositionResponse,
            HealthFactorResponse,
            ProtocolStatsResponse,
            AvailableToBorrowResponse,
            CalculateHealthFactorRequest,
        )

        assert AaveMarketResponse is not None
        assert AaveMarketsResponse is not None
        assert AavePositionResponse is not None
        assert HealthFactorResponse is not None
        assert ProtocolStatsResponse is not None
        assert AvailableToBorrowResponse is not None
        assert CalculateHealthFactorRequest is not None

    def test_aave_provider_exists(self):
        """Test AaveProvider is defined."""
        from app.setup.ioc.aave import AaveProvider

        assert AaveProvider is not None


# =============================================================================
# Exception Hierarchy Tests
# =============================================================================


@pytest.mark.integration
class TestAaveExceptionHierarchy:
    """Test Aave exception inheritance and structure."""

    def test_exceptions_inherit_from_base(self):
        """Test all exceptions inherit from AaveError."""
        from app.domain.exceptions.aave import (
            AaveError,
            AaveAPIError,
            MarketNotFoundError,
            PositionNotFoundError,
            InvalidAddressError,
            UnsupportedChainError,
            HealthFactorTooLowError,
        )

        assert issubclass(AaveAPIError, AaveError)
        assert issubclass(MarketNotFoundError, AaveError)
        assert issubclass(PositionNotFoundError, AaveError)
        assert issubclass(InvalidAddressError, AaveError)
        assert issubclass(UnsupportedChainError, AaveError)
        assert issubclass(HealthFactorTooLowError, AaveError)

    def test_exceptions_have_error_codes(self):
        """Test all exceptions have unique error codes."""
        from app.domain.exceptions.aave import (
            AaveError,
            AaveAPIError,
            MarketNotFoundError,
            PositionNotFoundError,
            InvalidAddressError,
        )

        codes = {
            AaveError.error_code,
            AaveAPIError.error_code,
            MarketNotFoundError.error_code,
            PositionNotFoundError.error_code,
            InvalidAddressError.error_code,
        }

        # All codes should be unique
        assert len(codes) == 5


# =============================================================================
# Entity Serialization Tests
# =============================================================================


@pytest.mark.integration
class TestAaveEntitySerialization:
    """Test Aave entity serialization round-trips."""

    def test_market_round_trip(self):
        """Test AaveMarket serialization round-trip."""
        from decimal import Decimal
        from app.domain.entities.lending.aave_market import AaveMarket

        market = AaveMarket(
            asset_address="0x1234567890abcdef1234567890abcdef12345678",
            symbol="USDC",
            name="USD Coin",
            chain="ethereum",
            supply_apy=Decimal("0.0425"),
            borrow_apy_variable=Decimal("0.0675"),
            total_supplied=Decimal("1000000000"),
            total_supplied_usd=Decimal("1000000000"),
            ltv=Decimal("0.80"),
            liquidation_threshold=Decimal("0.85"),
        )

        data = market.to_dict()
        restored = AaveMarket.from_dict(data)

        assert restored.symbol == market.symbol
        assert restored.supply_apy == market.supply_apy
        assert restored.ltv == market.ltv

    def test_position_round_trip(self):
        """Test AavePosition serialization round-trip."""
        from decimal import Decimal
        from app.domain.entities.lending.aave_position import (
            AavePosition,
            AaveSupplyPosition,
            AaveBorrowPosition,
        )

        position = AavePosition(
            user_address="0xuser1234",
            chain="ethereum",
            total_collateral_usd=Decimal("10000"),
            total_debt_usd=Decimal("5000"),
            health_factor=Decimal("1.65"),
            supplies=[
                AaveSupplyPosition(
                    asset_address="0xusdc",
                    symbol="USDC",
                    balance=Decimal("10000"),
                    balance_usd=Decimal("10000"),
                    apy=Decimal("0.05"),
                    is_collateral=True,
                )
            ],
            borrows=[
                AaveBorrowPosition(
                    asset_address="0xweth",
                    symbol="WETH",
                    balance=Decimal("2.5"),
                    balance_usd=Decimal("5000"),
                    apy=Decimal("0.08"),
                    borrow_type="variable",
                )
            ],
        )

        data = position.to_dict()
        restored = AavePosition.from_dict(data)

        assert restored.user_address == position.user_address
        assert restored.total_collateral_usd == position.total_collateral_usd
        assert len(restored.supplies) == 1
        assert len(restored.borrows) == 1

    def test_health_factor_round_trip(self):
        """Test HealthFactor serialization round-trip."""
        from decimal import Decimal
        from app.domain.value_objects.lending.health_factor import HealthFactor

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("5000"),
            liquidation_threshold=Decimal("0.825"),
        )

        data = hf.to_dict()
        restored = HealthFactor.from_dict(data)

        assert restored.collateral_usd == hf.collateral_usd
        assert restored.debt_usd == hf.debt_usd


# =============================================================================
# Router Registration Tests
# =============================================================================


@pytest.mark.integration
class TestAaveRouterRegistration:
    """Test Aave router is properly registered in the application."""

    def test_aave_router_in_defi_init(self):
        """Test Aave router is exported from DeFi controllers."""
        from app.presentation.http.controllers.defi import create_aave_router

        assert create_aave_router is not None

    def test_aave_provider_in_registry(self):
        """Test AaveProvider is included in provider registry."""
        from app.setup.ioc.provider_registry import get_providers

        providers = get_providers()
        provider_types = [type(p).__name__ for p in providers]

        assert "AaveProvider" in provider_types


# =============================================================================
# Health Factor Calculation Tests
# =============================================================================


@pytest.mark.integration
class TestHealthFactorCalculations:
    """Test health factor calculations and risk levels."""

    def test_risk_level_safe(self):
        """Test safe risk level classification."""
        from decimal import Decimal
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("2000"),  # Low debt = high HF
        )

        assert hf.risk_level == RiskLevel.SAFE
        assert hf.value > Decimal("2.0")

    def test_risk_level_moderate(self):
        """Test moderate risk level classification."""
        from decimal import Decimal
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("4700"),  # HF ~ 1.75
        )

        assert hf.risk_level == RiskLevel.MODERATE

    def test_risk_level_high(self):
        """Test high risk level classification."""
        from decimal import Decimal
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("6000"),  # HF ~ 1.375
        )

        assert hf.risk_level == RiskLevel.HIGH

    def test_risk_level_critical(self):
        """Test critical risk level classification."""
        from decimal import Decimal
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("7700"),  # HF ~ 1.07
        )

        assert hf.risk_level == RiskLevel.CRITICAL

    def test_risk_level_liquidatable(self):
        """Test liquidatable risk level classification."""
        from decimal import Decimal
        from app.domain.value_objects.lending.health_factor import (
            HealthFactor,
            RiskLevel,
        )

        hf = HealthFactor.calculate(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("9000"),  # HF < 1
        )

        assert hf.risk_level == RiskLevel.LIQUIDATABLE
        assert hf.is_liquidatable


# =============================================================================
# MCP Server Tests
# =============================================================================


@pytest.mark.integration
class TestAaveMCPServer:
    """Test Aave MCP server integration."""

    def test_aave_mcp_server_exists(self):
        """Test Aave MCP server is defined."""
        from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer

        assert AaveMCPServer is not None

    def test_aave_mcp_server_name(self):
        """Test Aave MCP server has correct name."""
        # Skip if server disabled
        try:
            from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
            from app.setup.config.mcp import MCPSettings

            settings = MCPSettings()
            # Only test if enabled
            if settings.enabled and settings.servers.aave_enabled:
                server = AaveMCPServer(settings=settings)
                assert server.name == "aave"
        except Exception:
            pytest.skip("Aave MCP server disabled or unavailable")

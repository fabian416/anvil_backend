"""
Integration tests for DeFi protocol APIs.

Tests the structure and protocol compliance of DeFi integrations.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.integration
class TestCurveIntegration:
    """Integration tests for Curve Finance API."""

    def test_curve_router_exists(self):
        """Test Curve router can be created."""
        from app.presentation.http.controllers.defi.curve_router import create_curve_router
        
        router = create_curve_router()
        assert router is not None

    def test_curve_router_has_routes(self):
        """Test Curve router has expected routes."""
        from app.presentation.http.controllers.defi.curve_router import create_curve_router
        
        router = create_curve_router()
        routes = [r.path for r in router.routes]
        
        # Routes include the prefix
        assert any("pools" in route for route in routes)
        assert len(routes) > 0

    def test_curve_gateway_port_exists(self):
        """Test CurveGateway port is defined."""
        from app.domain.ports.curve_gateway import CurveGateway
        
        assert CurveGateway is not None

    def test_curve_adapter_exists(self):
        """Test CurveAdapter exists."""
        from app.infrastructure.adapters.external.curve_adapter import CurveAdapter
        
        assert CurveAdapter is not None

    def test_curve_entities_exist(self):
        """Test Curve domain entities exist."""
        from app.domain.entities.curve.pool import Pool
        from app.domain.entities.curve.gauge import Gauge
        
        assert Pool is not None
        assert Gauge is not None

    def test_curve_value_objects_exist(self):
        """Test Curve value objects exist."""
        from app.domain.value_objects.curve.pool_apy import PoolAPY
        from app.domain.value_objects.curve.swap_quote import SwapQuote
        from app.domain.value_objects.curve.tvl_data import TVLData
        
        assert PoolAPY is not None
        assert SwapQuote is not None
        assert TVLData is not None


@pytest.mark.integration
class TestHyperliquidIntegration:
    """Integration tests for Hyperliquid perpetuals API."""

    def test_hyperliquid_router_exists(self):
        """Test Hyperliquid router can be created."""
        from app.presentation.http.controllers.defi.hyperliquid_router import create_hyperliquid_router
        
        router = create_hyperliquid_router()
        assert router is not None

    def test_perpetual_gateway_port_exists(self):
        """Test PerpetualGateway port is defined."""
        from app.domain.ports.perpetual_gateway import PerpetualGateway
        
        assert PerpetualGateway is not None

    def test_hyperliquid_adapter_exists(self):
        """Test HyperliquidAdapter exists."""
        from app.infrastructure.adapters.external.hyperliquid_adapter import HyperliquidAdapter
        
        assert HyperliquidAdapter is not None

    def test_perpetual_entities_exist(self):
        """Test Perpetual domain entities exist."""
        from app.domain.entities.perpetual.market import PerpMarket
        from app.domain.entities.perpetual.position import Position
        from app.domain.entities.perpetual.liquidation import Liquidation
        
        assert PerpMarket is not None
        assert Position is not None
        assert Liquidation is not None

    def test_perpetual_value_objects_exist(self):
        """Test Perpetual value objects exist."""
        from app.domain.value_objects.perpetual.funding_rate import FundingRate
        from app.domain.value_objects.perpetual.order_book import OrderBook
        from app.domain.value_objects.perpetual.risk_metrics import RiskMetrics
        
        assert FundingRate is not None
        assert OrderBook is not None
        assert RiskMetrics is not None


@pytest.mark.integration
class TestMorphoIntegration:
    """Integration tests for Morpho Protocol API."""

    def test_morpho_router_exists(self):
        """Test Morpho router can be created."""
        from app.presentation.http.controllers.defi.morpho_router import create_morpho_router
        
        router = create_morpho_router()
        assert router is not None

    def test_morpho_gateway_port_exists(self):
        """Test MorphoGateway port is defined."""
        from app.domain.ports.morpho_gateway import MorphoGateway
        
        assert MorphoGateway is not None

    def test_morpho_adapter_exists(self):
        """Test MorphoAdapter exists."""
        from app.infrastructure.adapters.external.morpho_adapter import MorphoAdapter
        
        assert MorphoAdapter is not None

    def test_morpho_entities_exist(self):
        """Test Morpho domain entities exist."""
        from app.domain.entities.lending.morpho_vault import MorphoVault
        from app.domain.entities.lending.morpho_market import MorphoMarket
        from app.domain.entities.lending.morpho_position import MorphoPosition
        
        assert MorphoVault is not None
        assert MorphoMarket is not None
        assert MorphoPosition is not None

    def test_morpho_value_objects_exist(self):
        """Test Morpho value objects exist."""
        from app.domain.value_objects.lending.vault_apy import VaultAPY
        from app.domain.value_objects.lending.risk_tier import RiskTier
        from app.domain.value_objects.lending.market_allocation import MarketAllocation
        
        assert VaultAPY is not None
        assert RiskTier is not None
        assert MarketAllocation is not None


@pytest.mark.integration
class TestLayerZeroIntegration:
    """Integration tests for LayerZero cross-chain API."""

    def test_layerzero_router_exists(self):
        """Test LayerZero router can be created."""
        from app.presentation.http.controllers.defi.layerzero_router import create_layerzero_router
        
        router = create_layerzero_router()
        assert router is not None

    def test_layerzero_gateway_port_exists(self):
        """Test LayerZeroGateway port is defined."""
        from app.domain.ports.layerzero_gateway import LayerZeroGateway
        
        assert LayerZeroGateway is not None

    def test_layerzero_adapter_exists(self):
        """Test LayerZeroAdapter exists."""
        from app.infrastructure.adapters.external.layerzero_adapter import LayerZeroAdapter
        
        assert LayerZeroAdapter is not None

    def test_layerzero_entities_exist(self):
        """Test LayerZero domain entities exist."""
        from app.domain.entities.cross_chain.lz_message import LZMessage
        from app.domain.entities.cross_chain.oft_transfer import OFTTransfer
        
        assert LZMessage is not None
        assert OFTTransfer is not None

    def test_layerzero_value_objects_exist(self):
        """Test LayerZero value objects exist."""
        from app.domain.value_objects.cross_chain.message_status import MessageStatus
        from app.domain.value_objects.cross_chain.lz_chain import LZChain
        from app.domain.value_objects.cross_chain.message_fee import MessageFee
        
        assert MessageStatus is not None
        assert LZChain is not None
        assert MessageFee is not None


@pytest.mark.integration
class TestAxelarIntegration:
    """Integration tests for Axelar bridge API."""

    def test_axelar_router_exists(self):
        """Test Axelar router can be created."""
        from app.presentation.http.controllers.defi.axelar_router import create_axelar_router
        
        router = create_axelar_router()
        assert router is not None

    def test_axelar_gateway_port_exists(self):
        """Test AxelarGateway port is defined."""
        from app.domain.ports.axelar_gateway import AxelarGateway
        
        assert AxelarGateway is not None

    def test_axelar_adapter_exists(self):
        """Test AxelarAdapter exists."""
        from app.infrastructure.adapters.external.axelar_adapter import AxelarAdapter
        
        assert AxelarAdapter is not None

    def test_axelar_entities_exist(self):
        """Test Axelar domain entities exist."""
        from app.domain.entities.bridge.axelar_transfer import AxelarTransfer
        
        assert AxelarTransfer is not None

    def test_axelar_value_objects_exist(self):
        """Test Axelar value objects exist."""
        from app.domain.value_objects.bridge.transfer_status import TransferStatus
        from app.domain.value_objects.bridge.bridge_route import BridgeRoute
        from app.domain.value_objects.bridge.transfer_estimate import TransferEstimate
        
        assert TransferStatus is not None
        assert BridgeRoute is not None
        assert TransferEstimate is not None


@pytest.mark.integration
class TestDeFiExceptionsIntegration:
    """Integration tests for DeFi exceptions."""

    def test_curve_exceptions_defined(self):
        """Test Curve exceptions are defined."""
        from app.domain.exceptions.curve import (
            CurveError,
            PoolNotFoundError,
            InsufficientLiquidityError,
        )
        
        assert CurveError is not None
        assert PoolNotFoundError is not None
        assert InsufficientLiquidityError is not None

    def test_perpetual_exceptions_defined(self):
        """Test Perpetual exceptions are defined."""
        from app.domain.exceptions.perpetual import (
            PerpetualError,
            SymbolNotFoundError,
            InvalidAddressError,
        )
        
        assert PerpetualError is not None
        assert SymbolNotFoundError is not None
        assert InvalidAddressError is not None

    def test_morpho_exceptions_defined(self):
        """Test Morpho exceptions are defined."""
        from app.domain.exceptions.morpho import (
            MorphoError,
            VaultNotFoundError,
            InvalidAddressError,
        )
        
        assert MorphoError is not None
        assert VaultNotFoundError is not None
        assert InvalidAddressError is not None

    def test_layerzero_exceptions_defined(self):
        """Test LayerZero exceptions are defined."""
        from app.domain.exceptions.layerzero import (
            LayerZeroError,
            MessageNotFoundError,
            InvalidTxHashError,
            UnsupportedChainError,
        )
        
        assert LayerZeroError is not None
        assert MessageNotFoundError is not None
        assert InvalidTxHashError is not None
        assert UnsupportedChainError is not None

    def test_axelar_exceptions_defined(self):
        """Test Axelar exceptions are defined."""
        from app.domain.exceptions.axelar import (
            AxelarError,
            TransferNotFoundError,
            UnsupportedChainError,
            UnsupportedTokenError,
        )
        
        assert AxelarError is not None
        assert TransferNotFoundError is not None
        assert UnsupportedChainError is not None
        assert UnsupportedTokenError is not None

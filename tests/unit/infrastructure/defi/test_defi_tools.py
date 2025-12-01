"""
Tests for DeFi tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.infrastructure.defi.tools.swap_tools import (
    get_swap_quote_tool,
    explain_swap_tool,
    get_token_info_tool,
)
from app.infrastructure.defi.tools.trading_tools import (
    get_position_info_tool,
    explain_perp_trading_tool,
    calculate_pnl_tool,
)


class TestSwapTools:
    """Test swap tools."""
    
    @pytest.mark.asyncio
    async def test_get_swap_quote_tool(self):
        """Test getting swap quote."""
        mock_client = AsyncMock()
        mock_client.get_quote.return_value = {
            "toAmount": "50000000000000000000",  # 50 ETH (18 decimals)
            "estimatedGas": "150000",
        }
        
        result = await get_swap_quote_tool(
            src_token="USDC",
            dst_token="ETH",
            amount="100",
            oneinch_client=mock_client,
        )
        
        assert "Swap Quote" in result
        assert "100 USDC" in result
        assert "ETH" in result
        assert "Gas" in result
    
    @pytest.mark.asyncio
    async def test_explain_swap_tool(self):
        """Test swap explanation."""
        result = await explain_swap_tool(
            src_token="USDC",
            dst_token="ETH",
        )
        
        assert "Token Approval" in result
        assert "1inch" in result
        assert "Slippage" in result
        assert "Gas Fees" in result
    
    @pytest.mark.asyncio
    async def test_get_token_info_tool(self):
        """Test getting token info."""
        mock_client = AsyncMock()
        
        result = await get_token_info_tool(
            token="USDC",
            oneinch_client=mock_client,
        )
        
        assert "USDC" in result
        assert "Address" in result
        assert "0x" in result


class TestTradingTools:
    """Test trading tools."""
    
    @pytest.mark.asyncio
    async def test_get_position_info_tool(self):
        """Test getting position info."""
        mock_client = AsyncMock()
        mock_client.get_market_price.return_value = {}
        mock_client.get_funding_rate.return_value = {
            "funding_rate": "0.01",
        }
        mock_client.calculate_liquidation_price.return_value = Decimal("45000")
        
        result = await get_position_info_tool(
            symbol="BTC",
            leverage=10,
            collateral="1000",
            is_long=True,
            hyperliquid_client=mock_client,
        )
        
        assert "Position Preview" in result
        assert "10x" in result
        assert "LONG" in result
        assert "BTC" in result
        assert "Liquidation Price" in result
    
    @pytest.mark.asyncio
    async def test_explain_perp_trading_tool(self):
        """Test perpetual trading explanation."""
        result = await explain_perp_trading_tool(symbol="BTC")
        
        assert "Perpetual Futures" in result
        assert "Leverage" in result
        assert "Liquidation" in result
        assert "Funding Rate" in result
        assert "Risk Management" in result
    
    @pytest.mark.asyncio
    async def test_calculate_pnl_tool(self):
        """Test PnL calculation."""
        result = await calculate_pnl_tool(
            entry_price="50000",
            current_price="55000",
            position_size="10000",
            is_long=True,
        )
        
        assert "PnL Calculation" in result
        assert "LONG" in result
        assert "PROFIT" in result or "LOSS" in result
        assert "$" in result


class TestDeFiProviders:
    """Test DeFi provider clients."""
    
    def test_oneinch_client_creation(self):
        """Test 1inch client can be created."""
        from app.infrastructure.defi.providers.oneinch import OneInchClient
        
        client = OneInchClient(api_key="test_key", chain_id=1)
        
        assert client.api_key == "test_key"
        assert client.chain_id == 1
        assert client.BASE_URL == "https://api.1inch.dev"
    
    def test_hyperliquid_client_creation(self):
        """Test Hyperliquid client can be created."""
        from app.infrastructure.defi.providers.hyperliquid import HyperliquidClient
        
        client = HyperliquidClient(testnet=True)
        
        assert client.testnet is True
        assert "testnet" in client.base_url.lower()
    
    @pytest.mark.asyncio
    async def test_hyperliquid_liquidation_calculation(self):
        """Test liquidation price calculation."""
        from app.infrastructure.defi.providers.hyperliquid import HyperliquidClient
        
        client = HyperliquidClient(testnet=True)
        
        # Test long position
        liq_price = await client.calculate_liquidation_price(
            entry_price=Decimal("50000"),
            leverage=10,
            is_long=True,
        )
        
        # Liquidation should be below entry for longs
        assert liq_price < Decimal("50000")
        
        # Test short position
        liq_price_short = await client.calculate_liquidation_price(
            entry_price=Decimal("50000"),
            leverage=10,
            is_long=False,
        )
        
        # Liquidation should be above entry for shorts
        assert liq_price_short > Decimal("50000")

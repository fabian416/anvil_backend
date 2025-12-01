"""
Tests for portfolio tools and providers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.infrastructure.defi.tools.portfolio_tools import (
    get_wallet_balance_tool,
    get_protocol_info_tool,
    get_top_protocols_tool,
    get_token_price_tool,
    get_market_overview_tool,
    get_yield_opportunities_tool,
)


class TestPortfolioTools:
    """Test portfolio tools."""
    
    @pytest.mark.asyncio
    async def test_get_wallet_balance_tool(self):
        """Test getting wallet balance."""
        mock_wallet = AsyncMock()
        mock_wallet.get_portfolio_balances.return_value = {
            "address": "0x123",
            "network": "ethereum",
            "native": {
                "token": "ETH",
                "balance": "1.5",
                "formatted": "1.500000",
            },
            "tokens": [
                {
                    "symbol": "USDC",
                    "balance": "1000.0",
                    "formatted": "1000.000000",
                }
            ],
            "total_tokens": 1,
        }
        
        mock_coingecko = AsyncMock()
        mock_coingecko.get_price.return_value = {
            "price": 2000.0,
            "change_24h": 2.5,
        }
        mock_coingecko.resolve_token_symbol.return_value = "usd-coin"
        
        result = await get_wallet_balance_tool(
            address="0x123",
            network="ethereum",
            wallet_provider=mock_wallet,
            coingecko_client=mock_coingecko,
        )
        
        assert "0x123" in result
        assert "ETH" in result
        assert "USDC" in result
        assert "$" in result
    
    @pytest.mark.asyncio
    async def test_get_protocol_info_tool(self):
        """Test getting protocol info."""
        mock_llama = AsyncMock()
        mock_llama.search_protocol.return_value = [
            {"slug": "aave", "name": "Aave"}
        ]
        mock_llama.get_protocol_tvl.return_value = {
            "protocol": "Aave",
            "slug": "aave",
            "current_tvl_usd": 5_000_000_000,
            "category": "Lending",
            "chains": ["Ethereum", "Polygon"],
            "url": "https://aave.com",
            "description": "Lending protocol",
        }
        
        result = await get_protocol_info_tool(
            protocol="aave",
            defillama_client=mock_llama,
        )
        
        assert "Aave" in result
        assert "Lending" in result
        assert "TVL" in result or "Value Locked" in result
    
    @pytest.mark.asyncio
    async def test_get_top_protocols_tool(self):
        """Test getting top protocols."""
        mock_llama = AsyncMock()
        mock_llama.get_top_protocols.return_value = [
            {
                "name": "Protocol 1",
                "tvl": 1_000_000_000,
                "category": "DEX",
            },
            {
                "name": "Protocol 2",
                "tvl": 500_000_000,
                "category": "Lending",
            },
        ]
        
        result = await get_top_protocols_tool(
            limit=2,
            defillama_client=mock_llama,
        )
        
        assert "Protocol 1" in result
        assert "Protocol 2" in result
        assert "DEX" in result
    
    @pytest.mark.asyncio
    async def test_get_token_price_tool(self):
        """Test getting token price."""
        mock_coingecko = AsyncMock()
        mock_coingecko.resolve_token_symbol.return_value = "bitcoin"
        mock_coingecko.get_price.return_value = {
            "price": 50000.0,
            "change_24h": 3.5,
        }
        
        result = await get_token_price_tool(
            token="BTC",
            coingecko_client=mock_coingecko,
        )
        
        assert "BTC" in result
        assert "50,000" in result or "50000" in result
        assert "24h" in result
    
    @pytest.mark.asyncio
    async def test_get_market_overview_tool(self):
        """Test getting market overview."""
        mock_coingecko = AsyncMock()
        mock_coingecko.get_multiple_prices.return_value = {
            "bitcoin": {
                "price": 50000.0,
                "change_24h": 2.5,
                "market_cap": 1_000_000_000_000,
            },
            "ethereum": {
                "price": 3000.0,
                "change_24h": -1.2,
                "market_cap": 400_000_000_000,
            },
        }
        
        result = await get_market_overview_tool(
            coingecko_client=mock_coingecko,
        )
        
        assert "Bitcoin" in result or "BTC" in result
        assert "Ethereum" in result or "ETH" in result
        assert "$" in result
    
    @pytest.mark.asyncio
    async def test_get_yield_opportunities_tool(self):
        """Test getting yield opportunities."""
        mock_llama = AsyncMock()
        mock_llama.get_protocol_yields.return_value = [
            {
                "project": "Aave",
                "symbol": "USDC",
                "apy": 5.5,
                "tvlUsd": 10_000_000,
                "chain": "Ethereum",
            }
        ]
        
        result = await get_yield_opportunities_tool(
            defillama_client=mock_llama,
        )
        
        assert "Aave" in result
        assert "APY" in result
        assert "5.5" in result or "5.50" in result


class TestDeFiProviders:
    """Test DeFi provider clients."""
    
    def test_wallet_provider_creation(self):
        """Test wallet provider can be created."""
        from app.infrastructure.defi.providers.wallet_provider import WalletProvider
        
        provider = WalletProvider()
        
        assert provider is not None
        assert "ethereum" in provider.rpc_endpoints
    
    def test_defillama_client_creation(self):
        """Test DeFiLlama client can be created."""
        from app.infrastructure.defi.providers.defillama import DeFiLlamaClient
        
        client = DeFiLlamaClient()
        
        assert client is not None
        assert client.BASE_URL == "https://api.llama.fi"
    
    def test_coingecko_client_creation(self):
        """Test CoinGecko client can be created."""
        from app.infrastructure.defi.providers.coingecko import CoinGeckoClient
        
        client = CoinGeckoClient()
        
        assert client is not None
        assert client.BASE_URL == "https://api.coingecko.com/api/v3"
    
    def test_coingecko_token_resolution(self):
        """Test token symbol resolution."""
        from app.infrastructure.defi.providers.coingecko import CoinGeckoClient
        
        client = CoinGeckoClient()
        
        assert client.resolve_token_symbol("BTC") == "bitcoin"
        assert client.resolve_token_symbol("ETH") == "ethereum"
        assert client.resolve_token_symbol("USDC") == "usd-coin"
        assert client.resolve_token_symbol("UNKNOWN") is None

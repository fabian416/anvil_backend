"""
Integration tests for DeFi provider APIs.

Tests real API interactions (can be mocked or use test networks).
"""

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

from app.infrastructure.defi.providers.oneinch import OneInchClient
from app.infrastructure.defi.providers.hyperliquid import HyperliquidClient
from app.infrastructure.defi.providers.wallet_provider import WalletProvider
from app.infrastructure.defi.providers.defillama import DeFiLlamaClient
from app.infrastructure.defi.providers.coingecko import CoinGeckoClient


class TestOneInchIntegration:
    """Integration tests for 1inch API client."""
    
    @pytest.mark.asyncio
    async def test_get_quote_integration(self):
        """Test getting swap quote from 1inch (mocked)."""
        client = OneInchClient(api_key="test_key", chain_id=1)
        
        # Mock the HTTP client
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "toAmount": "50000000000000000000",
                "estimatedGas": "150000",
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get quote
            result = await client.get_quote(
                src="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                dst="0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
                amount="100000000",  # 100 USDC
            )
            
            assert result is not None
            assert "toAmount" in result
            assert "estimatedGas" in result
    
    @pytest.mark.asyncio
    async def test_get_tokens_integration(self):
        """Test getting supported tokens from 1inch (mocked)."""
        client = OneInchClient(api_key="test_key", chain_id=1)
        
        # Mock the HTTP client
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "tokens": {
                    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": {
                        "symbol": "USDC",
                        "name": "USD Coin",
                        "decimals": 6,
                    }
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get tokens
            result = await client.get_tokens()
            
            assert result is not None
            assert "tokens" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test 1inch client handles API errors gracefully."""
        client = OneInchClient(api_key="test_key", chain_id=1)
        
        # Mock HTTP error
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_get.return_value = mock_response
            
            # Should handle error gracefully
            with pytest.raises(Exception):
                await client.get_quote(
                    src="invalid",
                    dst="invalid",
                    amount="0",
                )


class TestHyperliquidIntegration:
    """Integration tests for Hyperliquid API client."""
    
    @pytest.mark.asyncio
    async def test_get_market_price_integration(self):
        """Test getting market price from Hyperliquid (mocked)."""
        client = HyperliquidClient(testnet=True)
        
        # Mock the HTTP client
        with patch.object(client._client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "price": "45000.00",
                "timestamp": 1234567890,
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Get market price
            result = await client.get_market_price(symbol="BTC")
            
            assert result is not None
            assert "price" in result
    
    @pytest.mark.asyncio
    async def test_calculate_liquidation_price(self):
        """Test liquidation price calculation."""
        client = HyperliquidClient(testnet=True)
        
        # Test long position
        liq_price = await client.calculate_liquidation_price(
            entry_price=Decimal("45000"),
            leverage=10,
            is_long=True,
        )
        
        assert liq_price < 45000  # Long liquidation is below entry
        assert liq_price > 0
        
        # Test short position
        liq_price_short = await client.calculate_liquidation_price(
            entry_price=Decimal("45000"),
            leverage=10,
            is_long=False,
        )
        
        assert liq_price_short > 45000  # Short liquidation is above entry


class TestWalletProviderIntegration:
    """Integration tests for WalletProvider."""
    
    @pytest.mark.asyncio
    async def test_get_native_balance_integration(self):
        """Test getting native balance (mocked RPC)."""
        provider = WalletProvider()
        
        # Mock the HTTP client
        mock_client = provider._clients["ethereum"]
        with patch.object(mock_client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "result": "0x1b1ae4d6e2ef500000"  # 31.1 ETH in hex
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Get balance
            result = await provider.get_native_balance(
                address="0x123",
                network="ethereum",
            )
            
            assert result is not None
            assert "balance" in result
            assert "symbol" in result
            assert result["symbol"] == "ETH"
    
    @pytest.mark.asyncio
    async def test_get_portfolio_balances_integration(self):
        """Test getting complete portfolio (mocked)."""
        provider = WalletProvider()
        
        # Mock native balance
        mock_client = provider._clients["ethereum"]
        with patch.object(mock_client, 'post') as mock_post:
            # Mock responses for native and token balances
            mock_post.side_effect = [
                # Native balance
                AsyncMock(
                    json=AsyncMock(return_value={"result": "0x1b1ae4d6e2ef500000"}),
                    raise_for_status=AsyncMock(),
                ),
                # Token balance 1
                AsyncMock(
                    json=AsyncMock(return_value={"result": "0x3b9aca00"}),  # 1000 USDC
                    raise_for_status=AsyncMock(),
                ),
            ]
            
            # Get portfolio
            result = await provider.get_portfolio_balances(
                address="0x123",
                network="ethereum",
                tokens=["USDC"],
            )
            
            assert result is not None
            assert "native" in result
            assert "tokens" in result


class TestDeFiLlamaIntegration:
    """Integration tests for DeFiLlama API client."""
    
    @pytest.mark.asyncio
    async def test_get_protocol_tvl_integration(self):
        """Test getting protocol TVL (mocked)."""
        client = DeFiLlamaClient()
        
        # Mock the HTTP client
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "tvl": [
                    {"date": 1234567890, "totalLiquidityUSD": 1000000000}
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get TVL
            result = await client.get_protocol_tvl(protocol="aave")
            
            assert result is not None
            assert "tvl" in result
    
    @pytest.mark.asyncio
    async def test_get_top_protocols_integration(self):
        """Test getting top protocols (mocked)."""
        client = DeFiLlamaClient()
        
        # Mock the HTTP client
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = [
                {
                    "name": "Aave",
                    "tvl": 5000000000,
                    "chain": "Ethereum",
                }
            ]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get top protocols
            result = await client.get_top_protocols(limit=10)
            
            assert result is not None
            assert len(result) > 0
            assert "tvl" in result[0]


class TestCoinGeckoIntegration:
    """Integration tests for CoinGecko API client."""
    
    @pytest.mark.asyncio
    async def test_get_price_integration(self):
        """Test getting token price (mocked)."""
        client = CoinGeckoClient()
        
        # Mock the HTTP client
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "bitcoin": {
                    "usd": 45000.0,
                    "usd_24h_change": 2.5,
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get price
            result = await client.get_price(coin_id="bitcoin")
            
            assert result is not None
            assert "usd" in result
            assert result["usd"] == 45000.0
    
    @pytest.mark.asyncio
    async def test_resolve_token_symbol(self):
        """Test resolving token symbol to CoinGecko ID."""
        client = CoinGeckoClient()
        
        # Test known tokens
        assert client.resolve_token_symbol("BTC") == "bitcoin"
        assert client.resolve_token_symbol("ETH") == "ethereum"
        assert client.resolve_token_symbol("USDC") == "usd-coin"
        
        # Test unknown token
        assert client.resolve_token_symbol("UNKNOWN") is None
    
    @pytest.mark.asyncio
    async def test_get_multiple_prices_integration(self):
        """Test getting multiple token prices (mocked)."""
        client = CoinGeckoClient()
        
        # Mock the HTTP client
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "bitcoin": {"usd": 45000.0},
                "ethereum": {"usd": 3000.0},
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get prices
            result = await client.get_multiple_prices(
                coin_ids=["bitcoin", "ethereum"]
            )
            
            assert result is not None
            assert "bitcoin" in result
            assert "ethereum" in result


class TestProviderErrorHandling:
    """Integration tests for provider error handling."""
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test providers handle network timeouts gracefully."""
        client = CoinGeckoClient()
        
        # Mock timeout
        with patch.object(client._client, 'get') as mock_get:
            mock_get.side_effect = TimeoutError("Request timeout")
            
            with pytest.raises(TimeoutError):
                await client.get_price("bitcoin")
    
    @pytest.mark.asyncio
    async def test_invalid_response_handling(self):
        """Test providers handle invalid API responses."""
        client = DeFiLlamaClient()
        
        # Mock invalid JSON
        with patch.object(client._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            with pytest.raises(ValueError):
                await client.get_protocol_tvl("aave")

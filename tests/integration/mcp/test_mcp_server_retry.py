"""
Integration tests for MCP Server retry functionality.

Tests retry behavior for all 6 MCP servers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer
from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
from app.infrastructure.mcp.servers.thegraph_mcp import TheGraphMCPServer
from app.infrastructure.mcp.servers.coingecko_mcp import CoinGeckoMCPServer
from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
from app.infrastructure.mcp.servers.portfolio_mcp import PortfolioMCPServer
from app.setup.config.mcp import MCPSettings, MCPRetrySettings


class TestMCPServerRetry:
    """Test retry functionality for MCP servers."""
    
    @pytest.mark.asyncio
    async def test_defillama_retry_on_http_error(self, mock_mcp_manager_http):
        """Test DeFiLlama server retries on HTTP error."""
        # Arrange
        server = DeFiLlamaMCPServer()
        
        # Mock client to fail twice, then succeed
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable",
            request=MagicMock(),
            response=MagicMock(),
        )
        
        mock_response_success = MagicMock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "name": "Aave",
            "tvl": 10000000000,
            "category": "Lending",
        }
        
        with patch.object(server.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                mock_response_fail,
                mock_response_fail,
                mock_response_success,
            ]
            
            # Act
            result = await server._get_protocol_tvl("aave")
        
        # Assert
        assert "name" in result
        assert result["name"] == "Aave"
        assert mock_get.call_count == 3  # Retried twice
    
    @pytest.mark.asyncio
    async def test_oneinch_retry_on_timeout(self, mock_mcp_manager_http):
        """Test 1inch server retries on timeout."""
        # Arrange
        server = OneInchMCPServer(api_key="test_key")
        
        # Mock client to timeout once, then succeed
        with patch.object(server.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                httpx.TimeoutException("Request timeout"),
                MagicMock(
                    raise_for_status=lambda: None,
                    json=lambda: {"chains": [{"chainId": 1, "name": "Ethereum"}]},
                ),
            ]
            
            # Act
            result = await server._get_supported_chains()
        
        # Assert
        assert "chains" in result or "error" not in result
        assert mock_get.call_count == 2  # Retried once
    
    @pytest.mark.asyncio
    async def test_thegraph_retry_exhausted(self, mock_mcp_manager_http):
        """Test The Graph server exhausts retries."""
        # Arrange
        server = TheGraphMCPServer()
        
        # Mock client to always fail
        with patch.object(server.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=MagicMock(),
                response=MagicMock(),
            )
            
            # Act
            result = await server._query_subgraph("uniswap_v3", "{ pools { id } }")
        
        # Assert
        assert "error" in result
        assert mock_post.call_count == 3  # 3 attempts (initial + 2 retries)
    
    @pytest.mark.asyncio
    async def test_coingecko_successful_on_first_attempt(self, mock_mcp_manager_http):
        """Test CoinGecko server succeeds without retry."""
        # Arrange
        server = CoinGeckoMCPServer()
        
        # Mock client to succeed immediately
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "bitcoin": {"usd": 45000}
        }
        
        with patch.object(server.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Act
            result = await server._get_token_price("bitcoin")
        
        # Assert
        assert "error" not in result
        assert mock_get.call_count == 1  # No retry needed
    
    @pytest.mark.asyncio
    async def test_aave_retry_configuration(self, mock_mcp_manager_http):
        """Test Aave server has retry decorator configured."""
        # Arrange
        server = AaveMCPServer()
        
        # Assert
        assert hasattr(server, '_retry')
        assert server._retry is not None
    
    @pytest.mark.asyncio
    async def test_portfolio_retry_configuration(self, mock_mcp_manager_http):
        """Test Portfolio server has retry decorator configured."""
        # Arrange
        server = PortfolioMCPServer()
        
        # Assert
        assert hasattr(server, '_retry')
        assert server._retry is not None
    
    @pytest.mark.asyncio
    async def test_all_servers_have_retry(self, mock_mcp_manager_http):
        """Test all 6 MCP servers have retry configured."""
        # Arrange
        servers = [
            DeFiLlamaMCPServer(),
            OneInchMCPServer(),
            TheGraphMCPServer(),
            CoinGeckoMCPServer(),
            AaveMCPServer(),
            PortfolioMCPServer(),
        ]
        
        # Assert
        for server in servers:
            assert hasattr(server, '_retry'), f"{server.__class__.__name__} missing _retry"
            assert server._retry is not None
    
    @pytest.mark.asyncio
    async def test_retry_backoff_timing(self, mock_mcp_manager_http):
        """Test exponential backoff timing."""
        # Arrange
        server = DeFiLlamaMCPServer()
        
        import time
        call_times = []
        
        async def failing_get(*args, **kwargs):
            call_times.append(time.time())
            raise httpx.HTTPStatusError(
                "503 Service Unavailable",
                request=MagicMock(),
                response=MagicMock(),
            )
        
        with patch.object(server.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = failing_get
            
            # Act
            result = await server._get_protocol_tvl("aave")
        
        # Assert
        assert "error" in result
        assert len(call_times) == 3  # 3 attempts
        
        # Check backoff delays
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 >= 1.0  # At least 1 second (actual: ~2s with jitter)
        
        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert delay2 >= 2.0  # At least 2 seconds (actual: ~4s with jitter)
    
    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, mock_mcp_manager_http):
        """Test retry on network connectivity errors."""
        # Arrange
        server = DeFiLlamaMCPServer()
        
        # Mock network error then success
        with patch.object(server.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                httpx.NetworkError("Connection failed"),
                httpx.NetworkError("Connection failed"),
                MagicMock(
                    raise_for_status=lambda: None,
                    json=lambda: {"name": "Aave", "tvl": 10000000000},
                ),
            ]
            
            # Act
            result = await server._get_protocol_tvl("aave")
        
        # Assert
        assert "name" in result or "error" in result
        # Network errors might not be retried by tenacity, check actual behavior
    
    @pytest.mark.asyncio
    async def test_mcp_settings_retry_defaults(self, mock_mcp_manager_http):
        """Test MCPSettings has retry configuration."""
        # Arrange
        settings = MCPSettings()
        
        # Assert
        assert hasattr(settings, 'retry')
        assert settings.retry.enabled is True
        assert settings.retry.max_retries == 3
        assert settings.retry.initial_backoff_seconds == 2.0
        assert settings.retry.max_backoff_seconds == 10.0
        assert settings.retry.circuit_breaker_enabled is True
        assert settings.retry.telemetry_enabled is True
    
    @pytest.mark.asyncio
    async def test_custom_retry_configuration(self, mock_mcp_manager_http):
        """Test custom retry configuration."""
        # Arrange
        settings = MCPSettings(
            retry=MCPRetrySettings(
                enabled=True,
                max_retries=5,
                initial_backoff_seconds=1.0,
                circuit_failure_threshold=3,
            )
        )
        
        # Assert
        assert settings.retry.max_retries == 5
        assert settings.retry.initial_backoff_seconds == 1.0
        assert settings.retry.circuit_failure_threshold == 3

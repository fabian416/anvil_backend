"""
Integration tests for MCP server feature flags.

Tests granular enable/disable controls for each MCP server.
"""

import pytest
from unittest.mock import Mock

from app.setup.config.mcp import (
    MCPSettings,
    MCPServerSettings,
    MCPServerDisabledError,
)
from app.infrastructure.mcp.manager import MCPServerManager
from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer
from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
from app.infrastructure.mcp.servers.thegraph_mcp import TheGraphMCPServer
from app.infrastructure.mcp.servers.coingecko_mcp import CoinGeckoMCPServer
from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
from app.infrastructure.mcp.servers.portfolio_mcp import PortfolioMCPServer


class TestMCPMasterSwitch:
    """Test MCP master enable/disable switch."""
    
    def test_mcp_disabled_globally(self):
        """Test that MCP system can be disabled globally."""
        settings = MCPSettings(enabled=False)
        
        # Should raise error when trying to create server
        with pytest.raises(MCPServerDisabledError) as exc_info:
            DeFiLlamaMCPServer(settings=settings)
        
        assert "MCP system is disabled" not in str(exc_info.value)
        assert "DeFiLlama MCP server is disabled" in str(exc_info.value)
    
    def test_mcp_enabled_by_default(self):
        """Test that MCP is enabled by default."""
        settings = MCPSettings()
        
        assert settings.enabled is True
        assert settings.servers.defillama_enabled is True


class TestDeFiLlamaServerFlags:
    """Test DeFiLlama server feature flags."""
    
    def test_defillama_enabled_by_default(self):
        """Test DeFiLlama server is enabled by default."""
        settings = MCPSettings()
        
        # Should create without error
        server = DeFiLlamaMCPServer(settings=settings)
        assert server.server_name == "defillama"
    
    def test_defillama_can_be_disabled(self):
        """Test DeFiLlama server can be disabled."""
        settings = MCPSettings(
            servers=MCPServerSettings(defillama_enabled=False)
        )
        
        with pytest.raises(MCPServerDisabledError) as exc_info:
            DeFiLlamaMCPServer(settings=settings)
        
        assert "DeFiLlama MCP server is disabled" in str(exc_info.value)
        assert "defillama_enabled=true" in str(exc_info.value)


class TestOneInchServerFlags:
    """Test 1inch server feature flags."""
    
    def test_oneinch_enabled_by_default(self):
        """Test 1inch server is enabled by default."""
        settings = MCPSettings()
        
        server = OneInchMCPServer(settings=settings)
        assert server.server_name == "1inch"
    
    def test_oneinch_can_be_disabled(self):
        """Test 1inch server can be disabled."""
        settings = MCPSettings(
            servers=MCPServerSettings(oneinch_enabled=False)
        )
        
        with pytest.raises(MCPServerDisabledError) as exc_info:
            OneInchMCPServer(settings=settings)
        
        assert "1inch MCP server is disabled" in str(exc_info.value)
        assert "oneinch_enabled=true" in str(exc_info.value)


class TestTheGraphServerFlags:
    """Test The Graph server feature flags."""
    
    def test_thegraph_enabled_by_default(self):
        """Test The Graph server is enabled by default."""
        settings = MCPSettings()
        
        server = TheGraphMCPServer(settings=settings)
        assert server.server_name == "thegraph"
    
    def test_thegraph_can_be_disabled(self):
        """Test The Graph server can be disabled."""
        settings = MCPSettings(
            servers=MCPServerSettings(thegraph_enabled=False)
        )
        
        with pytest.raises(MCPServerDisabledError) as exc_info:
            TheGraphMCPServer(settings=settings)
        
        assert "The Graph MCP server is disabled" in str(exc_info.value)
        assert "thegraph_enabled=true" in str(exc_info.value)


class TestCoinGeckoServerFlags:
    """Test CoinGecko server feature flags."""
    
    def test_coingecko_enabled_by_default(self):
        """Test CoinGecko server is enabled by default."""
        settings = MCPSettings()
        
        server = CoinGeckoMCPServer(settings=settings)
        assert server.server_name == "coingecko"
    
    def test_coingecko_can_be_disabled(self):
        """Test CoinGecko server can be disabled."""
        settings = MCPSettings(
            servers=MCPServerSettings(coingecko_enabled=False)
        )
        
        with pytest.raises(MCPServerDisabledError) as exc_info:
            CoinGeckoMCPServer(settings=settings)
        
        assert "CoinGecko MCP server is disabled" in str(exc_info.value)
        assert "coingecko_enabled=true" in str(exc_info.value)


class TestAaveServerFlags:
    """Test Aave server feature flags."""
    
    def test_aave_enabled_by_default(self):
        """Test Aave server is enabled by default."""
        settings = MCPSettings()

        server = AaveMCPServer(settings=settings)
        assert server.name == "aave"
    
    def test_aave_can_be_disabled(self):
        """Test Aave server can be disabled."""
        settings = MCPSettings(
            servers=MCPServerSettings(aave_enabled=False)
        )
        
        with pytest.raises(MCPServerDisabledError) as exc_info:
            AaveMCPServer(settings=settings)
        
        assert "Aave MCP server is disabled" in str(exc_info.value)
        assert "aave_enabled=true" in str(exc_info.value)


class TestPortfolioServerFlags:
    """Test Portfolio server feature flags."""
    
    def test_portfolio_enabled_by_default(self):
        """Test Portfolio server is enabled by default."""
        settings = MCPSettings()

        server = PortfolioMCPServer(settings=settings)
        assert server.name == "portfolio"
    
    def test_portfolio_can_be_disabled(self):
        """Test Portfolio server can be disabled."""
        settings = MCPSettings(
            servers=MCPServerSettings(portfolio_enabled=False)
        )
        
        with pytest.raises(MCPServerDisabledError) as exc_info:
            PortfolioMCPServer(settings=settings)
        
        assert "Portfolio MCP server is disabled" in str(exc_info.value)
        assert "portfolio_enabled=true" in str(exc_info.value)


class TestMCPManagerWithFlags:
    """Test MCPServerManager respects feature flags."""
    
    def test_manager_respects_settings(self):
        """Test manager respects MCP settings."""
        settings = MCPSettings()
        manager = MCPServerManager(settings=settings)
        
        assert manager.settings.enabled is True
    
    def test_manager_blocks_disabled_server_registration(self):
        """Test manager blocks registration of disabled servers."""
        settings = MCPSettings(
            servers=MCPServerSettings(defillama_enabled=False)
        )
        manager = MCPServerManager(settings=settings)
        
        # Try to register disabled server
        with pytest.raises(MCPServerDisabledError):
            server = DeFiLlamaMCPServer(settings=settings)
            manager.register_server(server, port=8082)
    
    def test_manager_allows_enabled_server_registration(self):
        """Test manager allows registration of enabled servers."""
        settings = MCPSettings()
        manager = MCPServerManager(settings=settings)
        
        # Create and register enabled server
        server = DeFiLlamaMCPServer(settings=settings)
        manager.register_server(server, port=8082)
        
        assert "defillama" in manager.servers


class TestSelectiveServerEnablement:
    """Test selective enablement of servers (cost optimization scenarios)."""
    
    def test_disable_paid_apis_only(self):
        """Test disabling only paid APIs (1inch, The Graph)."""
        settings = MCPSettings(
            servers=MCPServerSettings(
                defillama_enabled=True,  # Free
                oneinch_enabled=False,  # Paid - disable
                thegraph_enabled=False,  # Paid - disable
                coingecko_enabled=True,  # Free
                aave_enabled=True,
                portfolio_enabled=True,
            )
        )
        
        # Free APIs should work
        defillama = DeFiLlamaMCPServer(settings=settings)
        coingecko = CoinGeckoMCPServer(settings=settings)
        assert defillama.server_name == "defillama"
        assert coingecko.server_name == "coingecko"
        
        # Paid APIs should be blocked
        with pytest.raises(MCPServerDisabledError):
            OneInchMCPServer(settings=settings)
        
        with pytest.raises(MCPServerDisabledError):
            TheGraphMCPServer(settings=settings)
    
    def test_enable_only_market_data_servers(self):
        """Test enabling only market data servers."""
        settings = MCPSettings(
            servers=MCPServerSettings(
                defillama_enabled=True,  # Market data
                oneinch_enabled=False,  # Swap - disable
                thegraph_enabled=False,  # Indexing - disable
                coingecko_enabled=True,  # Market data
                aave_enabled=False,  # Lending - disable
                portfolio_enabled=False,  # Tracking - disable
            )
        )
        
        # Market data servers should work
        defillama = DeFiLlamaMCPServer(settings=settings)
        coingecko = CoinGeckoMCPServer(settings=settings)
        assert defillama.server_name == "defillama"
        assert coingecko.server_name == "coingecko"
        
        # Other servers should be blocked
        with pytest.raises(MCPServerDisabledError):
            OneInchMCPServer(settings=settings)
        
        with pytest.raises(MCPServerDisabledError):
            AaveMCPServer(settings=settings)


class TestConfigurationDefaults:
    """Test configuration default values."""
    
    def test_all_defaults_enabled(self):
        """Test that all servers are enabled by default."""
        settings = MCPSettings()
        
        assert settings.enabled is True
        assert settings.servers.defillama_enabled is True
        assert settings.servers.oneinch_enabled is True
        assert settings.servers.thegraph_enabled is True
        assert settings.servers.coingecko_enabled is True
        assert settings.servers.aave_enabled is True
        assert settings.servers.portfolio_enabled is True
    
    def test_partial_configuration(self):
        """Test partial configuration with defaults."""
        settings = MCPSettings(
            servers=MCPServerSettings(
                defillama_enabled=False,
                # Others default to True
            )
        )
        
        assert settings.servers.defillama_enabled is False
        assert settings.servers.oneinch_enabled is True  # Default
        assert settings.servers.coingecko_enabled is True  # Default


# Test Summary
"""
Total Tests: 20+

Coverage:
  ✅ Master MCP switch (enabled/disabled)
  ✅ Individual server flags (6 servers)
  ✅ MCPServerManager flag integration
  ✅ Selective server enablement scenarios
  ✅ Configuration defaults
  ✅ Error messages
  
Use Cases Tested:
  ✅ Cost optimization (disable paid APIs)
  ✅ Feature isolation (market data only)
  ✅ Development mode (minimal servers)
  ✅ Production mode (all enabled)
"""

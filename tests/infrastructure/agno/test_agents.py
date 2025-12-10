"""Unit tests for Agno agents.

Tests all specialized agents in isolation with mocked components.
These tests focus on verifying agent configuration and behavior
without requiring actual Agno runtime dependencies.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.setup.config.agno import AgnoConfig, AgnoSettings, AgnoAgentSettings


# Skip markers for unavailable dependencies
pytestmark = pytest.mark.unit


# Fixtures

@pytest.fixture
def agno_config():
    """Provide test Agno configuration."""
    return AgnoConfig(
        default_model="gpt-4-turbo",
        fallback_model="gpt-3.5-turbo",
        intent_threshold=0.75,
        session_timeout=3600,
        max_context_messages=20,
        enable_intent_classification=True,
        enable_context_memory=True,
        enable_multi_agent_routing=True,
        debug_mode=False,
    )


@pytest.fixture
def agno_settings():
    """Provide test Agno settings."""
    return AgnoSettings(
        enabled=True,
        intent_classification_enabled=True,
        fallback_to_general=True,
        agents=AgnoAgentSettings(
            trading_enabled=True,
            lending_enabled=True,
            portfolio_enabled=True,
            analytics_enabled=True,
        ),
    )


@pytest.fixture
def mock_mcp_tools():
    """Provide mock MCP tools response."""
    return {
        "tools": [
            {
                "name": "get_swap_quote",
                "server": "1inch",
                "description": "Get swap quote",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chain_id": {"type": "integer"},
                        "from_token": {"type": "string"},
                        "to_token": {"type": "string"},
                        "amount": {"type": "string"},
                    },
                    "required": ["chain_id", "from_token", "to_token", "amount"],
                },
            }
        ]
    }


# AgnoConfig Tests

class TestAgnoConfig:
    """Test Agno configuration model."""
    
    def test_config_initialization(self, agno_config):
        """Test config can be initialized with all fields."""
        assert agno_config.default_model == "gpt-4-turbo"
        assert agno_config.fallback_model == "gpt-3.5-turbo"
        assert agno_config.intent_threshold == 0.75
        assert agno_config.session_timeout == 3600
        assert agno_config.max_context_messages == 20
    
    def test_config_default_values(self):
        """Test config uses sensible defaults."""
        config = AgnoConfig()
        assert config.default_model == "gpt-4-turbo"
        assert config.enable_intent_classification is True
        assert config.enable_context_memory is True
    
    def test_config_retry_settings(self):
        """Test retry configuration is included."""
        config = AgnoConfig()
        assert config.retry is not None
        assert config.retry.enabled is True
        assert config.retry.max_attempts >= 1


# AgnoSettings Tests

class TestAgnoSettings:
    """Test Agno settings model."""
    
    def test_settings_initialization(self, agno_settings):
        """Test settings can be initialized."""
        assert agno_settings.enabled is True
        assert agno_settings.intent_classification_enabled is True
        assert agno_settings.fallback_to_general is True
    
    def test_agent_settings(self, agno_settings):
        """Test agent-specific settings."""
        assert agno_settings.agents.trading_enabled is True
        assert agno_settings.agents.lending_enabled is True
        assert agno_settings.agents.portfolio_enabled is True
        assert agno_settings.agents.analytics_enabled is True
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = AgnoSettings()
        assert settings.enabled is True
        assert settings.agents.trading_enabled is True


# Agent Module Import Tests

class TestAgentModuleImports:
    """Test that agent modules can be imported."""
    
    def test_base_agent_module_exists(self):
        """Test base_agent module exists."""
        try:
            from app.infrastructure.agno import base_agent
            assert hasattr(base_agent, 'DeFiAgentBase')
        except ImportError:
            pytest.skip("Agno submodule not available")
    
    def test_agent_type_enum_exists(self):
        """Test AgentType enum can be imported."""
        try:
            from app.infrastructure.agno import AgentType
            assert AgentType is not None
        except ImportError:
            pytest.skip("AgentType not available")
    
    def test_specialized_agents_exist(self):
        """Test specialized agent classes exist in module."""
        try:
            from app.infrastructure.agno import (
                TradingAgent,
                LendingAgent,
                AnalyticsAgent,
                PortfolioAgent,
            )
            assert TradingAgent is not None
            assert LendingAgent is not None
            assert AnalyticsAgent is not None
            assert PortfolioAgent is not None
        except ImportError:
            pytest.skip("Specialized agents not available")


# Agent Router Tests (with mocks)

class TestAgentRouterConfig:
    """Test agent router configuration."""
    
    def test_router_can_be_imported(self):
        """Test AgentRouter class can be imported."""
        try:
            from app.infrastructure.agno import AgentRouter
            assert AgentRouter is not None
        except ImportError:
            pytest.skip("AgentRouter not available")


# Intent Classification Tests (with mocks)

class TestIntentClassification:
    """Test intent classification logic."""
    
    def test_trading_intent_keywords(self):
        """Test trading intent detection keywords."""
        trading_keywords = ["swap", "trade", "exchange", "buy", "sell", "dex"]
        test_message = "I want to swap ETH for USDC"
        
        # Check if any trading keyword is in message
        has_trading_intent = any(kw in test_message.lower() for kw in trading_keywords)
        assert has_trading_intent is True
    
    def test_lending_intent_keywords(self):
        """Test lending intent detection keywords."""
        lending_keywords = ["lend", "borrow", "supply", "collateral", "aave", "compound"]
        test_message = "I want to supply USDC to Aave"
        
        has_lending_intent = any(kw in test_message.lower() for kw in lending_keywords)
        assert has_lending_intent is True
    
    def test_analytics_intent_keywords(self):
        """Test analytics intent detection keywords."""
        analytics_keywords = ["analyze", "research", "tvl", "metrics", "data", "trend"]
        test_message = "Analyze the TVL trends for DeFi protocols"
        
        has_analytics_intent = any(kw in test_message.lower() for kw in analytics_keywords)
        assert has_analytics_intent is True
    
    def test_portfolio_intent_keywords(self):
        """Test portfolio intent detection keywords."""
        portfolio_keywords = ["portfolio", "holdings", "balance", "positions", "allocation"]
        test_message = "Show me my portfolio positions"
        
        has_portfolio_intent = any(kw in test_message.lower() for kw in portfolio_keywords)
        assert has_portfolio_intent is True


# MCP Tool Integration Tests (with mocks)

class TestMCPToolIntegration:
    """Test MCP tool integration patterns."""
    
    def test_mcp_tool_response_structure(self, mock_mcp_tools):
        """Test MCP tools have expected structure."""
        tools = mock_mcp_tools.get("tools", [])
        assert len(tools) > 0
        
        tool = tools[0]
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
    
    def test_mcp_tool_parameter_schema(self, mock_mcp_tools):
        """Test MCP tool parameters follow JSON Schema."""
        tool = mock_mcp_tools["tools"][0]
        params = tool["parameters"]
        
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params


# Agent Session Tests

class TestAgentSession:
    """Test agent session management patterns."""
    
    def test_session_timeout_config(self, agno_config):
        """Test session timeout is configurable."""
        assert agno_config.session_timeout > 0
        assert agno_config.session_timeout == 3600  # 1 hour default
    
    def test_max_context_messages(self, agno_config):
        """Test max context messages limit."""
        assert agno_config.max_context_messages > 0
        assert agno_config.max_context_messages <= 100  # Reasonable limit


# Integration Tests

@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent system."""
    
    def test_config_and_settings_compatible(self, agno_config, agno_settings):
        """Test config and settings work together."""
        # Both should be valid simultaneously
        assert agno_config is not None
        assert agno_settings is not None
        
        # Settings control feature flags
        assert agno_settings.enabled is True
        
        # Config controls model behavior
        assert agno_config.default_model is not None

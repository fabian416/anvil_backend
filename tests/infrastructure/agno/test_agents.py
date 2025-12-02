"""Unit tests for Agno agents.

Tests all specialized agents in isolation with mocked MCP tools.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.infrastructure.agno import (
    DeFiAgentBase,
    TradingAgent,
    LendingAgent,
    AnalyticsAgent,
    PortfolioAgent,
    AgentRouter,
    AgentType,
)
from app.setup.config.agno import AgnoConfig


# Fixtures

@pytest.fixture
def agno_config():
    """Provide test Agno configuration."""
    return AgnoConfig(
        model_id="gpt-4-turbo",
        temperature=0.7,
        max_tokens=2000,
        show_tool_calls=False,
        mcp_manager_url="http://localhost:8080",
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


# DeFiAgentBase Tests

@pytest.mark.asyncio
class TestDeFiAgentBase:
    """Test base agent functionality."""
    
    async def test_agent_initialization(self, agno_config):
        """Test agent can be initialized."""
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test role",
            config=agno_config,
            mcp_servers=["portfolio"],
        )
        
        assert agent.name == "Test Agent"
        assert agent.role == "Test role"
        assert agent.mcp_servers == ["portfolio"]
        assert agent.mcp_tools == []
    
    @patch('httpx.AsyncClient.get')
    async def test_load_mcp_tools(self, mock_get, agno_config, mock_mcp_tools):
        """Test MCP tool loading."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_mcp_tools
        mock_get.return_value = mock_response
        
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test role",
            config=agno_config,
            mcp_servers=["1inch"],
        )
        
        await agent.load_mcp_tools()
        
        assert len(agent.mcp_tools) == 1
        assert agent.mcp_tools[0].name == "get_swap_quote"
        assert agent.mcp_tools[0].server == "1inch"
    
    async def test_get_available_tools(self, agno_config):
        """Test getting available tools."""
        agent = DeFiAgentBase(
            name="Test Agent",
            role="Test role",
            config=agno_config,
            mcp_servers=["portfolio"],
        )
        
        tools = agent.get_available_tools()
        assert isinstance(tools, list)


# TradingAgent Tests

@pytest.mark.asyncio
class TestTradingAgent:
    """Test trading agent."""
    
    async def test_trading_agent_initialization(self, agno_config):
        """Test trading agent can be initialized."""
        agent = TradingAgent(agno_config)
        
        assert agent.name == "Trading Agent"
        assert "trading" in agent.role.lower()
        assert "1inch" in agent.mcp_servers
    
    async def test_trading_agent_has_safety_instructions(self, agno_config):
        """Test trading agent has safety instructions."""
        agent = TradingAgent(agno_config)
        
        # Check for key safety instructions
        instructions_str = " ".join(agent.instructions).lower()
        assert "confirmation" in instructions_str
        assert "never execute" in instructions_str or "always get" in instructions_str


# LendingAgent Tests

@pytest.mark.asyncio
class TestLendingAgent:
    """Test lending agent."""
    
    async def test_lending_agent_initialization(self, agno_config):
        """Test lending agent can be initialized."""
        agent = LendingAgent(agno_config)
        
        assert agent.name == "Lending Agent"
        assert "lending" in agent.role.lower()
        assert "aave" in agent.mcp_servers
    
    async def test_lending_agent_has_risk_warnings(self, agno_config):
        """Test lending agent has risk warning instructions."""
        agent = LendingAgent(agno_config)
        
        # Check for health factor warnings
        instructions_str = " ".join(agent.instructions).lower()
        assert "health factor" in instructions_str
        assert "liquidation" in instructions_str


# AnalyticsAgent Tests

@pytest.mark.asyncio
class TestAnalyticsAgent:
    """Test analytics agent."""
    
    async def test_analytics_agent_initialization(self, agno_config):
        """Test analytics agent can be initialized."""
        agent = AnalyticsAgent(agno_config)
        
        assert agent.name == "Analytics Agent"
        assert "analytics" in agent.role.lower() or "analyst" in agent.role.lower()
        assert "defillama" in agent.mcp_servers
    
    async def test_analytics_agent_has_research_instructions(self, agno_config):
        """Test analytics agent has research instructions."""
        agent = AnalyticsAgent(agno_config)
        
        instructions_str = " ".join(agent.instructions).lower()
        assert "tvl" in instructions_str or "protocol" in instructions_str


# PortfolioAgent Tests

@pytest.mark.asyncio
class TestPortfolioAgent:
    """Test portfolio agent."""
    
    async def test_portfolio_agent_initialization(self, agno_config):
        """Test portfolio agent can be initialized."""
        agent = PortfolioAgent(agno_config)
        
        assert agent.name == "Portfolio Agent"
        assert "portfolio" in agent.role.lower()
        assert "portfolio" in agent.mcp_servers


# AgentRouter Tests

@pytest.mark.asyncio
class TestAgentRouter:
    """Test agent router."""
    
    async def test_router_initialization(self, agno_config):
        """Test router can be initialized."""
        router = AgentRouter(agno_config)
        
        assert not router._initialized
        assert len(router.agents) == 0
    
    @patch('httpx.AsyncClient.get')
    async def test_router_initialize(self, mock_get, agno_config, mock_mcp_tools):
        """Test router initialization loads all agents."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_mcp_tools
        mock_get.return_value = mock_response
        
        router = AgentRouter(agno_config)
        await router.initialize()
        
        assert router._initialized
        assert len(router.agents) == 4
        assert AgentType.TRADING in router.agents
        assert AgentType.LENDING in router.agents
        assert AgentType.ANALYTICS in router.agents
        assert AgentType.PORTFOLIO in router.agents
    
    def test_classify_intent_trading(self, agno_config):
        """Test intent classification for trading queries."""
        router = AgentRouter(agno_config)
        
        queries = [
            "Swap 1 ETH for USDC",
            "What's the price of WBTC?",
            "Trade ETH for DAI",
        ]
        
        for query in queries:
            agent_type, confidence = router.classify_intent(query)
            assert agent_type == AgentType.TRADING
            assert confidence > 0.5
    
    def test_classify_intent_lending(self, agno_config):
        """Test intent classification for lending queries."""
        router = AgentRouter(agno_config)
        
        queries = [
            "Supply 1000 USDC to Aave",
            "What's my health factor?",
            "Borrow USDC against ETH collateral",
        ]
        
        for query in queries:
            agent_type, confidence = router.classify_intent(query)
            assert agent_type == AgentType.LENDING
            assert confidence > 0.5
    
    def test_classify_intent_analytics(self, agno_config):
        """Test intent classification for analytics queries."""
        router = AgentRouter(agno_config)
        
        queries = [
            "What's the TVL of Uniswap?",
            "Find best yield opportunities",
            "Compare Aave and Compound protocols",
        ]
        
        for query in queries:
            agent_type, confidence = router.classify_intent(query)
            assert agent_type == AgentType.ANALYTICS
            assert confidence > 0.5
    
    def test_classify_intent_portfolio(self, agno_config):
        """Test intent classification for portfolio queries."""
        router = AgentRouter(agno_config)
        
        queries = [
            "Show me my portfolio",
            "What's my ETH balance?",
            "What positions do I have?",
        ]
        
        for query in queries:
            agent_type, confidence = router.classify_intent(query)
            assert agent_type == AgentType.PORTFOLIO
            assert confidence > 0.5
    
    def test_get_agent_info(self, agno_config):
        """Test getting agent information."""
        router = AgentRouter(agno_config)
        
        info = router.get_agent_info()
        assert "router_status" in info
        assert info["router_status"] == "not_initialized"
        assert info["agents_count"] == 0


# Integration-style tests (still mocked but more realistic)

@pytest.mark.asyncio
class TestAgentIntegration:
    """Test agent integration scenarios."""
    
    @patch('httpx.AsyncClient.get')
    async def test_router_end_to_end_flow(self, mock_get, agno_config, mock_mcp_tools):
        """Test complete routing flow."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_mcp_tools
        mock_get.return_value = mock_response
        
        # Create and initialize router
        router = AgentRouter(agno_config, debug_mode=False)
        await router.initialize()
        
        # Test classification
        agent_type, confidence = router.classify_intent("Swap ETH for USDC")
        assert agent_type == AgentType.TRADING
        
        # Verify agent is available
        assert AgentType.TRADING in router.agents
        trading_agent = router.agents[AgentType.TRADING]
        assert trading_agent.name == "Trading Agent"

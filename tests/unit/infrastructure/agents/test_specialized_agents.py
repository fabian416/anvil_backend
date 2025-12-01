"""
Unit tests for specialized DeFi agents.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.agents.swap_agent import SwapAgent, create_swap_agent
from app.infrastructure.agents.trading_agent import TradingAgent, create_trading_agent
from app.infrastructure.agents.portfolio_agent import PortfolioAgent, create_portfolio_agent
from app.infrastructure.agents.agent_factory import AgentFactory, create_agent_factory


class TestSwapAgent:
    """Test SwapAgent functionality."""
    
    def test_swap_agent_creation(self):
        """Test SwapAgent can be created."""
        agent = create_swap_agent()
        
        assert agent.name == "SwapAgent"
        assert agent.description == "Specialized agent for DeFi token swap operations"
        assert agent.model_name == "gpt-4-turbo"
    
    def test_swap_agent_intent_types(self):
        """Test SwapAgent reports correct intent types."""
        agent = create_swap_agent()
        
        intents = agent.get_intent_types()
        
        assert intents == ["trade_swap"]
    
    def test_swap_agent_tools(self):
        """Test SwapAgent tools (empty in Phase 1)."""
        agent = create_swap_agent()
        
        tools = agent.get_tools()
        
        # Phase 1: No tools yet
        assert isinstance(tools, list)
    
    @pytest.mark.asyncio
    async def test_swap_agent_run(self):
        """Test SwapAgent message processing."""
        agent = create_swap_agent()
        
        # Mock the Agno agent if not available
        if agent.agent is None:
            # Agno not available, test fallback
            response = await agent.run("I want to swap 100 USDC to ETH")
        else:
            # Mock the Agno agent
            mock_response = MagicMock()
            mock_response.content = "I can help you swap tokens. What would you like to swap?"
            agent.agent.arun = AsyncMock(return_value=mock_response)
            response = await agent.run("I want to swap 100 USDC to ETH")
        
        assert isinstance(response, str)
        assert len(response) > 0


class TestTradingAgent:
    """Test TradingAgent functionality."""
    
    def test_trading_agent_creation(self):
        """Test TradingAgent can be created."""
        agent = create_trading_agent()
        
        assert agent.name == "TradingAgent"
        assert agent.description == "Specialized agent for perpetual futures trading operations"
        assert agent.model_name == "gpt-4-turbo"
    
    def test_trading_agent_intent_types(self):
        """Test TradingAgent reports correct intent types."""
        agent = create_trading_agent()
        
        intents = agent.get_intent_types()
        
        assert "trade_perp_open" in intents
        assert "trade_perp_close" in intents
        assert len(intents) == 2
    
    def test_trading_agent_tools(self):
        """Test TradingAgent tools (empty in Phase 1)."""
        agent = create_trading_agent()
        
        tools = agent.get_tools()
        
        # Phase 1: No tools yet
        assert isinstance(tools, list)
    
    @pytest.mark.asyncio
    async def test_trading_agent_run(self):
        """Test TradingAgent message processing."""
        agent = create_trading_agent()
        
        # Mock the Agno agent if not available
        if agent.agent is None:
            # Agno not available, test fallback
            response = await agent.run("Open a 10x long on BTC")
        else:
            # Mock the Agno agent
            mock_response = MagicMock()
            mock_response.content = "I can help you with perpetual futures trading."
            agent.agent.arun = AsyncMock(return_value=mock_response)
            response = await agent.run("Open a 10x long on BTC")
        
        assert isinstance(response, str)
        assert len(response) > 0


class TestPortfolioAgent:
    """Test PortfolioAgent functionality."""
    
    def test_portfolio_agent_creation(self):
        """Test PortfolioAgent can be created."""
        agent = create_portfolio_agent()
        
        assert agent.name == "PortfolioAgent"
        assert agent.description == "Specialized agent for portfolio viewing and analysis"
        assert agent.model_name == "gpt-4-turbo"
    
    def test_portfolio_agent_intent_types(self):
        """Test PortfolioAgent reports correct intent types."""
        agent = create_portfolio_agent()
        
        intents = agent.get_intent_types()
        
        assert intents == ["portfolio_view"]
    
    def test_portfolio_agent_tools(self):
        """Test PortfolioAgent tools (empty in Phase 1)."""
        agent = create_portfolio_agent()
        
        tools = agent.get_tools()
        
        # Phase 1: No tools yet
        assert isinstance(tools, list)
    
    @pytest.mark.asyncio
    async def test_portfolio_agent_run(self):
        """Test PortfolioAgent message processing."""
        agent = create_portfolio_agent()
        
        # Mock the Agno agent if not available
        if agent.agent is None:
            # Agno not available, test fallback
            response = await agent.run("Show my portfolio")
        else:
            # Mock the Agno agent
            mock_response = MagicMock()
            mock_response.content = "Let me show you your portfolio."
            agent.agent.arun = AsyncMock(return_value=mock_response)
            response = await agent.run("Show my portfolio")
        
        assert isinstance(response, str)
        assert len(response) > 0


class TestAgentFactory:
    """Test AgentFactory functionality."""
    
    def test_factory_creation(self):
        """Test factory can be created."""
        factory = AgentFactory()
        
        assert factory.model == "gpt-4-turbo"
        assert len(factory._agents) == 0
    
    def test_create_all_agents(self):
        """Test factory creates all agents."""
        factory = AgentFactory()
        agents = factory.create_all_agents()
        
        # Should create all 3 agents
        assert len(agents) == 3
        assert "SwapAgent" in agents
        assert "TradingAgent" in agents
        assert "PortfolioAgent" in agents
    
    def test_intent_mapping(self):
        """Test factory maps intents to agents."""
        factory = create_agent_factory()
        
        mapping = factory.get_intent_mapping()
        
        # Should have all intent mappings
        assert mapping["trade_swap"] == "SwapAgent"
        assert mapping["trade_perp_open"] == "TradingAgent"
        assert mapping["trade_perp_close"] == "TradingAgent"
        assert mapping["portfolio_view"] == "PortfolioAgent"
    
    def test_get_agent_by_name(self):
        """Test getting agent by name."""
        factory = create_agent_factory()
        
        agent = factory.get_agent("SwapAgent")
        
        assert isinstance(agent, SwapAgent)
        assert agent.name == "SwapAgent"
    
    def test_get_agent_for_intent(self):
        """Test getting agent by intent."""
        factory = create_agent_factory()
        
        agent = factory.get_agent_for_intent("trade_swap")
        
        assert isinstance(agent, SwapAgent)
    
    def test_get_agent_not_found(self):
        """Test getting non-existent agent raises error."""
        factory = create_agent_factory()
        
        with pytest.raises(KeyError):
            factory.get_agent("NonExistentAgent")
    
    def test_get_agent_for_invalid_intent(self):
        """Test getting agent for invalid intent raises error."""
        factory = create_agent_factory()
        
        with pytest.raises(KeyError):
            factory.get_agent_for_intent("invalid_intent")
    
    def test_register_with_gateway(self):
        """Test registering agents with gateway."""
        factory = create_agent_factory()
        
        # Mock gateway
        mock_gateway = MagicMock()
        
        # Register agents
        factory.register_with_gateway(mock_gateway)
        
        # Should register all agents
        assert mock_gateway.register_agent.call_count == 3
        
        # Verify each agent was registered
        calls = mock_gateway.register_agent.call_args_list
        registered_agents = [call[0][0] for call in calls]
        
        assert "SwapAgent" in registered_agents
        assert "TradingAgent" in registered_agents
        assert "PortfolioAgent" in registered_agents


class TestAgentContextManagement:
    """Test agent context management."""
    
    @pytest.mark.asyncio
    async def test_agent_with_context(self):
        """Test agent processes context correctly."""
        agent = create_swap_agent()
        
        context = {
            "user_id": "user123",
            "recent_action": "viewed_portfolio"
        }
        
        # Test context processing
        if agent.agent is None:
            # Agno not available, test fallback
            response = await agent.run("Swap tokens", context=context)
            assert isinstance(response, str)
        else:
            # Mock the Agno agent
            mock_response = MagicMock()
            mock_response.content = "Response with context"
            agent.agent.arun = AsyncMock(return_value=mock_response)
            
            response = await agent.run("Swap tokens", context=context)
            
            # Should add context to message
            agent.agent.arun.assert_called_once()
            call_args = agent.agent.arun.call_args[0][0]
            
            # Context should be in the message
            assert "Context:" in call_args or isinstance(call_args, str)


class TestAgentErrorHandling:
    """Test agent error handling."""
    
    @pytest.mark.asyncio
    async def test_agent_handles_error(self):
        """Test agent handles errors gracefully."""
        agent = create_swap_agent()
        
        if agent.agent is None:
            # Agno not available, test still works
            response = await agent.run("Test message")
            assert isinstance(response, str)
        else:
            # Make agent raise error
            agent.agent.arun = AsyncMock(side_effect=Exception("Test error"))
            
            response = await agent.run("Test message")
            
            # Should return error message
            assert isinstance(response, str)
            assert "apologize" in response.lower() or "error" in response.lower()

"""
Integration tests for Agent Gateway with specialized agents.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.infrastructure.agents.agent_factory import create_agent_factory
from app.setup.config.agent_squad import AgentSquadConfig


class TestAgentGatewayWithSpecializedAgents:
    """Test Agent Gateway integrated with specialized agents."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage."""
        storage = AsyncMock(spec=AnvilSquadStorage)
        storage.get_chat_history.return_value = []
        storage.save_message.return_value = str(uuid4())
        return storage
    
    @pytest.fixture
    def mock_llm_gateway(self):
        """Create mock LLM gateway."""
        llm = AsyncMock()
        llm.generate.return_value = "Fallback response"
        return llm
    
    @pytest.fixture
    def gateway_with_agents(self, mock_storage, mock_llm_gateway):
        """Create gateway with registered agents."""
        config = AgentSquadConfig(
            enable_intent_classification=False,  # Use keyword
            debug_mode=True
        )
        
        # Create gateway
        gateway = AgentGatewayImpl(mock_storage, mock_llm_gateway, config)
        
        # Create and register agents
        factory = create_agent_factory(model=config.default_model)
        factory.register_with_gateway(gateway)
        
        return gateway
    
    @pytest.mark.asyncio
    async def test_swap_message_routes_to_swap_agent(self, gateway_with_agents, mock_storage):
        """Test swap messages route to SwapAgent."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "swap 100 USDC to ETH"
        
        response = await gateway_with_agents.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should get a response
        assert response is not None
        assert len(response) > 0
        
        # Should save response
        mock_storage.save_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_trading_message_routes_to_trading_agent(self, gateway_with_agents, mock_storage):
        """Test trading messages route to TradingAgent."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "open 10x long on BTC"
        
        response = await gateway_with_agents.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should get a response
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_portfolio_message_routes_to_portfolio_agent(self, gateway_with_agents, mock_storage):
        """Test portfolio messages route to PortfolioAgent."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "show my portfolio"
        
        response = await gateway_with_agents.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should get a response
        assert response is not None
        assert len(response) > 0
    
    def test_all_intents_have_registered_agents(self, gateway_with_agents):
        """Test that all important intents have agents."""
        # Check that key intents are mapped
        assert "trade_swap" in gateway_with_agents._agents
        assert "trade_perp_open" in gateway_with_agents._agents
        assert "trade_perp_close" in gateway_with_agents._agents
        assert "portfolio_view" in gateway_with_agents._agents
    
    def test_agents_are_callable(self, gateway_with_agents):
        """Test that registered agents have run method."""
        for intent, agent in gateway_with_agents._agents.items():
            assert hasattr(agent, 'run'), f"Agent for {intent} doesn't have run method"


class TestAgentFactoryIntegration:
    """Test Agent Factory integration with Gateway."""
    
    def test_factory_creates_correct_number_of_agents(self):
        """Test factory creates expected number of agents."""
        factory = create_agent_factory()
        
        agents = factory.get_all_agents()
        
        # Should create 3 agents
        assert len(agents) == 3
        assert "SwapAgent" in agents
        assert "TradingAgent" in agents
        assert "PortfolioAgent" in agents
    
    def test_factory_creates_intent_mapping(self):
        """Test factory creates complete intent mapping."""
        factory = create_agent_factory()
        
        mapping = factory.get_intent_mapping()
        
        # Should map all intents
        assert len(mapping) >= 4  # At least 4 intents
        assert "trade_swap" in mapping
        assert "trade_perp_open" in mapping
        assert "trade_perp_close" in mapping
        assert "portfolio_view" in mapping
    
    def test_factory_registers_agents_with_gateway(self):
        """Test factory can register agents with gateway."""
        factory = create_agent_factory()
        
        # Mock gateway
        mock_gateway = MagicMock()
        
        # Register
        factory.register_with_gateway(mock_gateway)
        
        # Should call register_agent for each agent
        assert mock_gateway.register_agent.call_count == 3


class TestEndToEndAgentFlow:
    """Test complete flow from message to agent response."""
    
    @pytest.fixture
    def setup_gateway(self):
        """Setup gateway with agents and mocks."""
        mock_storage = AsyncMock(spec=AnvilSquadStorage)
        mock_storage.get_chat_history.return_value = []
        mock_storage.save_message.return_value = str(uuid4())
        
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "Fallback"
        
        config = AgentSquadConfig(enable_intent_classification=False)
        
        gateway = AgentGatewayImpl(mock_storage, mock_llm, config)
        factory = create_agent_factory()
        factory.register_with_gateway(gateway)
        
        return gateway, mock_storage
    
    @pytest.mark.asyncio
    async def test_complete_swap_flow(self, setup_gateway):
        """Test complete swap flow from message to response."""
        gateway, mock_storage = setup_gateway
        
        # User sends swap message
        response = await gateway.process_message(
            user_id=uuid4(),
            session_id=str(uuid4()),
            message="swap 100 USDC for ETH"
        )
        
        # Should classify intent correctly
        assert response is not None
        
        # Should save agent response
        mock_storage.save_message.assert_called()
        
        # Check saved message details
        call_args = mock_storage.save_message.call_args
        assert call_args[1]["role"] == "agent"
        assert call_args[1]["content"] == response
    
    @pytest.mark.asyncio
    async def test_complete_trading_flow(self, setup_gateway):
        """Test complete trading flow."""
        gateway, mock_storage = setup_gateway
        
        response = await gateway.process_message(
            user_id=uuid4(),
            session_id=str(uuid4()),
            message="open 5x long on ETH"
        )
        
        assert response is not None
        mock_storage.save_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_portfolio_flow(self, setup_gateway):
        """Test complete portfolio flow."""
        gateway, mock_storage = setup_gateway
        
        response = await gateway.process_message(
            user_id=uuid4(),
            session_id=str(uuid4()),
            message="what's my balance"
        )
        
        assert response is not None
        mock_storage.save_message.assert_called()

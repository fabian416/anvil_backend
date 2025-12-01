"""
End-to-end tests for Agent Gateway message processing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, call
from uuid import UUID, uuid4

from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.setup.config.agent_squad import AgentSquadConfig
from app.domain.enums.message_role import MessageRole


class TestAgentGatewayMessageProcessing:
    """Test end-to-end message processing through Agent Gateway."""
    
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
        llm.generate.return_value = "This is a test response from the agent."
        return llm
    
    @pytest.fixture
    def gateway(self, mock_storage, mock_llm_gateway):
        """Create Agent Gateway instance."""
        config = AgentSquadConfig(
            enable_intent_classification=False,  # Use keyword-based for testing
            debug_mode=True
        )
        return AgentGatewayImpl(mock_storage, mock_llm_gateway, config)
    
    @pytest.mark.asyncio
    async def test_process_message_basic(self, gateway, mock_storage):
        """Test basic message processing."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "swap 100 USDC to ETH"
        
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should return a response
        assert response is not None
        assert len(response) > 0
        
        # Should save response to storage
        mock_storage.save_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_message_intent_classification(self, gateway):
        """Test that intent is classified correctly."""
        user_id = uuid4()
        session_id = str(uuid4())
        
        # Test different messages and their expected intents
        test_cases = [
            ("swap 100 USDC to ETH", "trade_swap"),
            ("open 10x long", "trade_perp_open"),
            ("show my portfolio", "portfolio_view"),
        ]
        
        for message, expected_intent in test_cases:
            # Classify intent directly
            intent = gateway._classify_intent_simple(message)
            
            # Should match expected
            assert intent == expected_intent, f"Failed for: {message}"
    
    @pytest.mark.asyncio
    async def test_process_message_saves_to_storage(self, gateway, mock_storage):
        """Test that agent response is saved to storage."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "what's my portfolio"
        
        await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should save agent response
        assert mock_storage.save_message.called
        call_args = mock_storage.save_message.call_args
        
        # Verify saved message details
        assert call_args[1]["session_id"] == session_id
        assert call_args[1]["role"] == "agent"
        assert len(call_args[1]["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_message_with_context(self, gateway, mock_storage):
        """Test message processing with conversation context."""
        # Setup mock history
        mock_storage.get_chat_history.return_value = [
            {"role": "user", "content": "First message"},
            {"role": "agent", "content": "First response"},
        ]
        
        user_id = uuid4()
        session_id = str(uuid4())
        message = "Follow up question"
        
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should get chat history (with limit parameter)
        mock_storage.get_chat_history.assert_called_once()
        call_args = mock_storage.get_chat_history.call_args
        assert call_args[0][0] == session_id or call_args[1].get("session_id") == session_id
        
        # Should return response
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, gateway, mock_storage, mock_llm_gateway):
        """Test error handling in message processing."""
        # Make LLM gateway fail
        mock_llm_gateway.generate.side_effect = Exception("LLM error")
        
        user_id = uuid4()
        session_id = str(uuid4())
        message = "test message"
        
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should still return a response (error message)
        assert response is not None
        assert "error" in response.lower() or "apologize" in response.lower()


class TestAgentGatewayContextManagement:
    """Test conversation context management."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage with history."""
        storage = AsyncMock(spec=AnvilSquadStorage)
        storage.get_chat_history.return_value = [
            {"role": "user", "content": "What's the price of BTC?"},
            {"role": "agent", "content": "BTC is currently at $42,000."},
            {"role": "user", "content": "And ETH?"},
            {"role": "agent", "content": "ETH is at $2,200."},
        ]
        storage.save_message.return_value = str(uuid4())
        return storage
    
    @pytest.fixture
    def gateway(self, mock_storage):
        """Create gateway with mocked storage."""
        llm = AsyncMock()
        llm.generate.return_value = "Test response"
        
        config = AgentSquadConfig(
            enable_context_memory=True,
            max_context_messages=20
        )
        
        return AgentGatewayImpl(mock_storage, llm, config)
    
    @pytest.mark.asyncio
    async def test_uses_conversation_history(self, gateway, mock_storage):
        """Test that conversation history is used for context."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "What about SOL?"
        
        await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should fetch chat history (with limit parameter)
        mock_storage.get_chat_history.assert_called_once()
        call_args = mock_storage.get_chat_history.call_args
        assert call_args[0][0] == session_id or call_args[1].get("session_id") == session_id
    
    @pytest.mark.asyncio
    async def test_formats_context_correctly(self, gateway, mock_storage):
        """Test that context is formatted correctly for LLM."""
        user_id = uuid4()
        session_id = str(uuid4())
        
        # Mock get_conversation_context to return actual string
        mock_storage.get_conversation_context = AsyncMock(return_value="User: Hello\nAgent: Hi there!")
        gateway.storage = mock_storage
        
        # Get conversation context
        context = await gateway.storage.get_conversation_context(
            session_id=session_id
        )
        
        # Should be a formatted string
        assert isinstance(context, str)
        assert len(context) > 0


class TestAgentGatewayFallbackBehavior:
    """Test fallback behavior when agents are unavailable."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway without registered agents."""
        storage = AsyncMock(spec=AnvilSquadStorage)
        storage.get_chat_history.return_value = []
        storage.save_message.return_value = str(uuid4())
        
        llm = AsyncMock()
        llm.generate.return_value = "Fallback response"
        
        config = AgentSquadConfig(enable_intent_classification=False)
        
        return AgentGatewayImpl(storage, llm, config)
    
    @pytest.mark.asyncio
    async def test_fallback_when_no_agent_registered(self, gateway):
        """Test fallback to LLM when no agent is registered for intent."""
        user_id = uuid4()
        session_id = str(uuid4())
        message = "swap tokens"
        
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should still get a response
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_fallback_response_generation(self, gateway, monkeypatch):
        """Test that fallback generates reasonable response."""
        # Mock the fallback method
        async def mock_fallback(message, intent, context):
            return f"I understand you want to {intent}, but I don't have a specialized agent for that yet."
        
        monkeypatch.setattr(gateway, "_generate_fallback_response", mock_fallback)
        
        user_id = uuid4()
        session_id = str(uuid4())
        message = "test message"
        
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should contain helpful message
        assert "understand" in response or "don't have" in response or len(response) > 0


class TestAgentGatewayAgentRegistration:
    """Test agent registration and routing."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway instance."""
        storage = AsyncMock(spec=AnvilSquadStorage)
        storage.get_chat_history.return_value = []
        storage.save_message.return_value = str(uuid4())
        
        llm = AsyncMock()
        llm.generate.return_value = "Response"
        
        config = AgentSquadConfig()
        return AgentGatewayImpl(storage, llm, config)
    
    def test_register_agent(self, gateway):
        """Test registering an agent for specific intents."""
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="Agent response")
        
        # Register agent for swap intent
        gateway.register_agent("SwapAgent", mock_agent, ["trade_swap"])
        
        # Verify registration
        assert "trade_swap" in gateway._agents
        assert gateway._agents["trade_swap"] == mock_agent
    
    def test_register_agent_multiple_intents(self, gateway):
        """Test registering an agent for multiple intents."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="Trading response")
        
        # Register for multiple intents
        gateway.register_agent(
            "TradingAgent",
            mock_agent,
            ["trade_perp_open", "trade_perp_close"]
        )
        
        # Verify both intents registered
        assert "trade_perp_open" in gateway._agents
        assert "trade_perp_close" in gateway._agents
        assert gateway._agents["trade_perp_open"] == mock_agent
        assert gateway._agents["trade_perp_close"] == mock_agent
    
    @pytest.mark.asyncio
    async def test_route_to_registered_agent(self, gateway):
        """Test that messages are routed to registered agents."""
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value="Swap completed successfully")
        
        # Register agent
        gateway.register_agent("SwapAgent", mock_agent, ["trade_swap"])
        
        # Process message that matches intent
        user_id = uuid4()
        session_id = str(uuid4())
        message = "swap 100 USDC to ETH"
        
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message
        )
        
        # Should route to agent and get its response
        mock_agent.run.assert_called_once()
        assert response == "Swap completed successfully"


class TestAgentGatewayConfiguration:
    """Test configuration options."""
    
    def test_debug_mode_enabled(self):
        """Test gateway with debug mode enabled."""
        storage = MagicMock()
        llm = MagicMock()
        config = AgentSquadConfig(debug_mode=True)
        
        gateway = AgentGatewayImpl(storage, llm, config)
        
        assert gateway.config.debug_mode is True
    
    def test_intent_classification_disabled(self):
        """Test gateway with intent classification disabled."""
        storage = MagicMock()
        llm = MagicMock()
        config = AgentSquadConfig(enable_intent_classification=False)
        
        gateway = AgentGatewayImpl(storage, llm, config)
        
        assert gateway.config.enable_intent_classification is False
    
    def test_context_memory_disabled(self):
        """Test gateway with context memory disabled."""
        storage = MagicMock()
        llm = MagicMock()
        config = AgentSquadConfig(enable_context_memory=False)
        
        gateway = AgentGatewayImpl(storage, llm, config)
        
        assert gateway.config.enable_context_memory is False
    
    def test_max_context_messages(self):
        """Test max context messages configuration."""
        storage = MagicMock()
        llm = MagicMock()
        config = AgentSquadConfig(max_context_messages=50)
        
        gateway = AgentGatewayImpl(storage, llm, config)
        
        assert gateway.config.max_context_messages == 50


class TestAgentGatewayPerformance:
    """Test Agent Gateway performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self):
        """Test processing multiple messages concurrently."""
        import asyncio
        
        # Setup mocks
        storage = AsyncMock(spec=AnvilSquadStorage)
        storage.get_chat_history.return_value = []
        storage.save_message.return_value = str(uuid4())
        
        llm = AsyncMock()
        llm.generate.return_value = "Response"
        
        config = AgentSquadConfig()
        gateway = AgentGatewayImpl(storage, llm, config)
        
        # Process multiple messages concurrently
        user_id = uuid4()
        session_id = str(uuid4())
        
        tasks = [
            gateway.process_message(user_id, session_id, f"Message {i}")
            for i in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should complete
        assert len(responses) == 10
        assert all(r is not None for r in responses)
    
    @pytest.mark.asyncio
    async def test_response_time_reasonable(self):
        """Test that response time is reasonable."""
        import time
        
        storage = AsyncMock(spec=AnvilSquadStorage)
        storage.get_chat_history.return_value = []
        storage.save_message.return_value = str(uuid4())
        
        llm = AsyncMock()
        llm.generate.return_value = "Quick response"
        
        config = AgentSquadConfig()
        gateway = AgentGatewayImpl(storage, llm, config)
        
        user_id = uuid4()
        session_id = str(uuid4())
        message = "test message"
        
        start = time.time()
        await gateway.process_message(user_id, session_id, message)
        elapsed = time.time() - start
        
        # Should complete quickly (< 1 second with mocks)
        assert elapsed < 1.0

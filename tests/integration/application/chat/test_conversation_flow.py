"""
End-to-end conversation flow tests.

Tests complete user conversation flows from HTTP request to agent response.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4, UUID

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.message_role import MessageRole
from app.application.chat.commands.create_conversation import CreateConversation
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.queries.get_conversation import GetConversation


class TestConversationFlowE2E:
    """End-to-end conversation flow tests."""
    
    @pytest.mark.asyncio
    async def test_complete_swap_conversation_flow(self):
        """Test complete swap conversation from creation to execution."""
        # Mock repository
        mock_repo = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()
        
        # Create conversation
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
        )
        mock_repo.get_by_id.return_value = conversation
        mock_repo.save.return_value = None
        
        # Mock agent gateway
        mock_agent_gateway = AsyncMock()
        mock_agent_gateway.process_message.return_value = "I can help you swap 100 USDC to ETH. Let me get a quote... You'll receive approximately 0.033 ETH. The estimated gas cost is 0.003 ETH. Would you like to proceed?"
        
        # Mock context manager
        mock_context_manager = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_id = user_id
        mock_context.conversation_id = conversation_id
        mock_context_manager.get_or_create_context.return_value = mock_context
        mock_context_manager.get_agent_context.return_value = {"preferences": {}}
        
        # Create interactor
        send_message = SendMessage(
            repository=mock_repo,
            agent_gateway=mock_agent_gateway,
            context_manager=mock_context_manager,
        )
        
        # Send swap request
        user_msg, agent_msg = await send_message.execute(
            conversation_id=conversation_id,
            content="Swap 100 USDC to ETH",
        )
        
        # Verify flow
        assert user_msg is not None
        assert user_msg.role == MessageRole.USER
        assert "100 USDC" in user_msg.content
        
        assert agent_msg is not None
        assert agent_msg.role == MessageRole.ASSISTANT
        assert "ETH" in agent_msg.content
        
        # Verify agent was called with context
        mock_agent_gateway.process_message.assert_called_once()
        call_args = mock_agent_gateway.process_message.call_args
        assert call_args.kwargs["message"] == "Swap 100 USDC to ETH"
        assert "context" in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_multi_turn_trading_conversation(self):
        """Test multi-turn trading conversation with follow-ups."""
        # Mock repository
        mock_repo = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
        )
        mock_repo.get_by_id.return_value = conversation
        
        # Mock agent gateway with progressive responses
        mock_agent_gateway = AsyncMock()
        
        # Mock context manager
        mock_context_manager = AsyncMock()
        mock_context = AsyncMock()
        mock_context_manager.get_or_create_context.return_value = mock_context
        mock_context_manager.get_agent_context.return_value = {"preferences": {}}
        
        # Create interactor
        send_message = SendMessage(
            repository=mock_repo,
            agent_gateway=mock_agent_gateway,
            context_manager=mock_context_manager,
        )
        
        # Turn 1: Initial incomplete request
        mock_agent_gateway.process_message.return_value = "I can help you open a BTC position. What leverage would you like? (e.g., 5x, 10x)"
        
        user_msg1, agent_msg1 = await send_message.execute(
            conversation_id=conversation_id,
            content="Open long BTC",
        )
        
        assert "leverage" in agent_msg1.content.lower()
        
        # Turn 2: Provide leverage
        mock_agent_gateway.process_message.return_value = "Perfect, 10x leverage. How much collateral in USD?"
        
        user_msg2, agent_msg2 = await send_message.execute(
            conversation_id=conversation_id,
            content="10x",
        )
        
        assert "collateral" in agent_msg2.content.lower()
        
        # Turn 3: Provide collateral
        mock_agent_gateway.process_message.return_value = "Great! Opening 10x long BTC with $1000 collateral. Your position size will be $10,000. Liquidation price: $40,500. Confirm?"
        
        user_msg3, agent_msg3 = await send_message.execute(
            conversation_id=conversation_id,
            content="$1000",
        )
        
        assert "liquidation" in agent_msg3.content.lower()
        assert "10x" in agent_msg3.content
    
    @pytest.mark.asyncio
    async def test_portfolio_view_with_context(self):
        """Test portfolio view uses user context and preferences."""
        # Mock repository
        mock_repo = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
        )
        mock_repo.get_by_id.return_value = conversation
        
        # Mock agent gateway
        mock_agent_gateway = AsyncMock()
        mock_agent_gateway.process_message.return_value = """
        Here's your portfolio for 0x123:
        
        **Assets:**
        - 1.5 ETH ($4,500)
        - 1000 USDC ($1,000)
        
        **Total Value:** $5,500
        
        Based on your medium risk tolerance, your portfolio looks balanced.
        """
        
        # Mock context manager with user preferences
        mock_context_manager = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_id = user_id
        mock_context.conversation_id = conversation_id
        mock_context_manager.get_or_create_context.return_value = mock_context
        mock_context_manager.get_agent_context.return_value = {
            "preferences": {
                "risk_tolerance": "medium",
                "preferred_chains": ["ethereum"],
            },
            "recent_intents": ["portfolio_view"],
        }
        
        # Create interactor
        send_message = SendMessage(
            repository=mock_repo,
            agent_gateway=mock_agent_gateway,
            context_manager=mock_context_manager,
        )
        
        # Request portfolio
        user_msg, agent_msg = await send_message.execute(
            conversation_id=conversation_id,
            content="Show my portfolio for 0x123",
        )
        
        # Verify context was used
        assert agent_msg is not None
        assert "portfolio" in agent_msg.content.lower()
        
        # Verify agent received context
        call_args = mock_agent_gateway.process_message.call_args
        context_param = call_args.kwargs["context"]
        assert "preferences" in context_param
        assert context_param["preferences"]["risk_tolerance"] == "medium"
    
    @pytest.mark.asyncio
    async def test_conversation_with_memory_learning(self):
        """Test conversation learns and adapts to user preferences."""
        # Mock repository
        mock_repo = AsyncMock()
        user_id = uuid4()
        conversation_id = uuid4()
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
        )
        mock_repo.get_by_id.return_value = conversation
        
        # Mock agent gateway
        mock_agent_gateway = AsyncMock()
        
        # Mock context manager
        mock_context_manager = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_preferences = {"slippage": 0.5}
        mock_context_manager.get_or_create_context.return_value = mock_context
        mock_context_manager.get_agent_context.return_value = {
            "preferences": {"slippage": 0.5},
        }
        
        # Create interactor
        send_message = SendMessage(
            repository=mock_repo,
            agent_gateway=mock_agent_gateway,
            context_manager=mock_context_manager,
        )
        
        # First swap: user specifies 0.5% slippage
        mock_agent_gateway.process_message.return_value = "Swap executed with 0.5% slippage"
        
        user_msg1, agent_msg1 = await send_message.execute(
            conversation_id=conversation_id,
            content="Swap 100 USDC to ETH with 0.5% slippage",
        )
        
        # Verify context update was called
        mock_context_manager.update_context_with_message.assert_called()
        
        # Second swap: user doesn't specify, should use learned preference
        mock_context_manager.get_agent_context.return_value = {
            "preferences": {"slippage": 0.5},  # Learned from first swap
        }
        
        mock_agent_gateway.process_message.return_value = "Using your preferred 0.5% slippage. Swap executed."
        
        user_msg2, agent_msg2 = await send_message.execute(
            conversation_id=conversation_id,
            content="Swap 200 USDC to ETH",
        )
        
        # Verify learned preference was used
        call_args = mock_agent_gateway.process_message.call_args
        context_param = call_args.kwargs["context"]
        assert context_param["preferences"]["slippage"] == 0.5


class TestConversationQueryIntegration:
    """Integration tests for conversation queries."""
    
    @pytest.mark.asyncio
    async def test_get_conversation_with_messages(self):
        """Test retrieving conversation with all messages."""
        # Mock repository
        mock_repo = AsyncMock()
        conversation_id = uuid4()
        user_id = uuid4()
        
        # Create conversation with messages
        messages = [
            Message(
                id=uuid4(),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content="Swap 100 USDC to ETH",
            ),
            Message(
                id=uuid4(),
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content="I can help you with that swap.",
            ),
        ]
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=messages,
        )
        
        mock_repo.get_by_id.return_value = conversation
        
        # Create query
        get_conversation = GetConversation(repository=mock_repo)
        
        # Execute query
        result = await get_conversation.execute(conversation_id=conversation_id)
        
        # Verify result
        assert result is not None
        assert result.id == conversation_id
        assert len(result.messages) == 2
        assert result.messages[0].role == MessageRole.USER
        assert result.messages[1].role == MessageRole.ASSISTANT

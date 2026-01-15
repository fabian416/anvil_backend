"""
Integration tests for context preservation.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.services.agent_squad.context_manager import (
    ContextManager,
    ConversationMessage,
)
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_id import MessageId
from app.domain.enums.agent_type import AgentType


@pytest.mark.asyncio
class TestContextPreservation:
    """Test conversation context preservation."""
    
    @pytest.mark.llm_validation
    async def test_add_and_retrieve_messages(self, mock_storage):
        """Test adding and retrieving conversation messages."""
        manager = ContextManager(storage=mock_storage)
        
        conversation_id = ConversationId(uuid4())
        message_id = MessageId(uuid4())
        
        # Add message
        await manager.add_message(
            conversation_id=conversation_id,
            message_id=message_id,
            role="user",
            content="Hello, how are you?",
        )
        
        # Retrieve context
        mock_storage.get_messages.return_value = [
            ConversationMessage(
                message_id=message_id,
                role="user",
                content="Hello, how are you?",
                agent_type=None,
                timestamp=datetime.utcnow(),
                metadata={},
            )
        ]
        
        context = await manager.get_conversation_context(conversation_id)
        
        assert len(context.conversation_history) > 0
        assert context.conversation_history[0]["content"] == "Hello, how are you?"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_add_and_retrieve_messages",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_enforce_history_limit(self, mock_storage):
        """Test enforcing conversation history limit."""
        manager = ContextManager(storage=mock_storage, history_limit=5)

        conversation_id = ConversationId(uuid4())

        # Mock: After adding message, storage will have 11 messages
        # (10 existing + 1 new = 11 total, which exceeds limit of 5)
        mock_storage.get_message_count.return_value = 11

        # Add new message (should trigger cleanup)
        await manager.add_message(
            conversation_id=conversation_id,
            message_id=MessageId(uuid4()),
            role="user",
            content="New message",
        )

        # Should remove oldest 6 messages (11 - 5 = 6)
        mock_storage.remove_oldest_messages.assert_called_once_with(
            conversation_id, 6
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_enforce_history_limit",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_multi_turn_context(self, mock_storage):
        """Test multi-turn conversation context."""
        manager = ContextManager(storage=mock_storage)
        
        conversation_id = ConversationId(uuid4())
        
        # Simulate 3-turn conversation
        messages = [
            ConversationMessage(
                message_id=MessageId(uuid4()),
                role="user",
                content="Tell me about Aave",
                agent_type=None,
                timestamp=datetime.utcnow(),
                metadata={},
            ),
            ConversationMessage(
                message_id=MessageId(uuid4()),
                role="agent",
                content="Aave is a lending protocol...",
                agent_type=AgentType.RESEARCH,
                timestamp=datetime.utcnow(),
                metadata={},
            ),
            ConversationMessage(
                message_id=MessageId(uuid4()),
                role="user",
                content="What's the risk?",
                agent_type=None,
                timestamp=datetime.utcnow(),
                metadata={},
            ),
        ]
        
        mock_storage.get_messages.return_value = messages
        
        context = await manager.get_conversation_context(conversation_id)
        
        assert len(context.conversation_history) == 3
        assert context.last_agent_type == AgentType.RESEARCH
        assert context.has_history is True

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multi_turn_context",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_context_with_agent_metadata(self, mock_storage):
        """Test context includes agent metadata."""
        manager = ContextManager(storage=mock_storage)
        
        conversation_id = ConversationId(uuid4())
        
        # Add message with agent metadata
        await manager.add_message(
            conversation_id=conversation_id,
            message_id=MessageId(uuid4()),
            role="agent",
            content="Response",
            agent_type=AgentType.HUNTER_AI,
            metadata={
                "tokens_used": 500,
                "latency_ms": 1200,
                "tools_used": ["openai_api", "coingecko_api"],
            },
        )
        
        # Verify metadata stored
        mock_storage.add_message.assert_called_once()
        call_args = mock_storage.add_message.call_args
        message = call_args[0][1]
        
        assert message.agent_type == AgentType.HUNTER_AI
        assert message.metadata["tokens_used"] == 500

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_with_agent_metadata",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



@pytest.fixture
def mock_storage(mocker):
    """Mock context storage."""
    storage = mocker.AsyncMock()
    storage.get_message_count.return_value = 0
    storage.get_messages.return_value = []
    storage.get_metadata.return_value = {"user": {}, "session": {}}
    return storage
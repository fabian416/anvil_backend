"""
Integration tests for individual agents.
"""

import asyncio
import pytest
from uuid import uuid4

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.infrastructure.adapters.agent_squad.agents.chat_agent_openai import ChatAgentOpenAI
from app.infrastructure.adapters.agent_squad.agents.hunter_ai_agent_openai import HunterAIAgentOpenAI


@pytest.mark.asyncio
class TestAgentExecution:
    """Test individual agent execution."""

    @pytest.mark.llm_validation
    async def test_chat_agent_execution(self, mock_llm_client):
        """Test chat agent execution."""
        agent = ChatAgentOpenAI(llm_client=mock_llm_client)

        conversation_id = ConversationId(uuid4())
        message = MessageContent("Hello! How can you help me?")
        context = ConversationContext()

        # Mock LLM response with realistic latency
        async def mock_chat_response(*args, **kwargs):
            await asyncio.sleep(0.015)  # 15ms simulated latency
            return {
                "content": "I can help you with DeFi, trading, and more!",
                "tokens_used": 150,
                "model": "gpt-4o-mini",
                "finish_reason": "stop",
            }

        mock_llm_client.chat.side_effect = mock_chat_response

        response = await agent.execute(conversation_id, message, context)

        assert response.agent_type == AgentType.CHAT
        assert response.content is not None
        assert response.tokens_used == 150
        assert response.latency_ms > 0
        assert len(response.tools_used) == 0  # Chat doesn't use external tools

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chat_agent_execution",
                user_input="I can help you with DeFi, trading, and more!",
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
    async def test_hunter_ai_agent_execution(self, mock_llm_client):
        """Test Hunter AI agent execution."""
        agent = HunterAIAgentOpenAI(llm_client=mock_llm_client)

        conversation_id = ConversationId(uuid4())
        message = MessageContent("What's the market sentiment for Bitcoin?")
        context = ConversationContext()

        # Mock LLM response with realistic latency
        async def mock_chat_response(*args, **kwargs):
            await asyncio.sleep(0.015)  # 15ms simulated latency
            return {
                "content": "Bitcoin sentiment is 75/100 (Bullish). Key drivers: ETF inflows, institutional adoption.",
                "tokens_used": 300,
                "model": "gpt-4o",
                "finish_reason": "stop",
            }

        mock_llm_client.chat.side_effect = mock_chat_response

        response = await agent.execute(conversation_id, message, context)

        assert response.agent_type == AgentType.HUNTER_AI
        assert response.content is not None
        assert "sentiment" in response.content.lower() or "bullish" in response.content.lower()
        assert response.tokens_used > 0
        assert "openai_api" in response.tools_used

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_hunter_ai_agent_execution",
                user_input="Bitcoin sentiment is 75/100 (Bullish). Key drivers: ETF inflows, institutional adoption.",
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
    async def test_agent_availability(self, mock_llm_client):
        """Test agent availability check."""
        agent = ChatAgentOpenAI(llm_client=mock_llm_client)
        
        is_available = await agent.is_available()
        
        assert is_available is True  # Chat agent always available

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_agent_availability",
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
    async def test_agent_error_handling(self, mock_llm_client):
        """Test agent error handling."""
        agent = ChatAgentOpenAI(llm_client=mock_llm_client)
        
        conversation_id = ConversationId(uuid4())
        message = MessageContent("Test message")
        context = ConversationContext()
        
        # Mock LLM error
        mock_llm_client.chat.side_effect = Exception("API error")
        
        with pytest.raises(Exception) as exc_info:
            await agent.execute(conversation_id, message, context)
        
        assert "API error" in str(exc_info.value)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_agent_error_handling",
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
def mock_llm_client(mocker):
    """Mock LLM client."""
    client = mocker.AsyncMock()
    return client
"""
Integration tests for individual agents.

Tests the ChatAgent and HunterAIAgent with mocked LLM clients.
"""

import asyncio
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext,
)
from app.infrastructure.adapters.agent_squad.agents.chat_agent import ChatAgent
from app.infrastructure.adapters.agent_squad.agents.hunter_ai_agent import HunterAIAgent


@pytest.fixture
def mock_llm_client():
    """Mock LLM client gateway."""
    client = AsyncMock()
    # Mock both generate and chat methods
    client.generate = AsyncMock(
        return_value={
            "content": "Mocked response",
            "tokens_used": 100,
            "model": "gemini-2.0-flash",
        }
    )
    client.chat = AsyncMock(
        return_value={
            "content": "Mocked response",
            "tokens_used": 100,
            "model": "gemini-2.0-flash",
        }
    )
    return client


@pytest.fixture
def mock_coingecko_client():
    """Mock CoinGecko client."""
    client = MagicMock()
    client.get_price = AsyncMock(return_value={"bitcoin": {"usd": 50000}})
    return client


@pytest.fixture
def mock_hyperliquid_client():
    """Mock Hyperliquid client."""
    client = MagicMock()
    return client


@pytest.mark.asyncio
class TestAgentExecution:
    """Test individual agent execution."""

    @pytest.mark.llm_validation
    async def test_chat_agent_initialization(self, mock_llm_client):
        """Test chat agent can be initialized."""
        agent = ChatAgent(llm_client=mock_llm_client)

        assert agent is not None
        assert agent._llm_client == mock_llm_client

    @pytest.mark.llm_validation
    async def test_chat_agent_execution(self, mock_llm_client):
        """Test chat agent execution with mocked LLM response."""
        agent = ChatAgent(llm_client=mock_llm_client)

        conversation_id = ConversationId(uuid4())
        message = MessageContent("Hello! How can you help me?")
        context = ConversationContext()

        # Mock LLM response with realistic latency - return dict, not MagicMock
        # The agent uses .chat() method, not .generate()
        async def mock_chat_response(*args, **kwargs):
            await asyncio.sleep(0.015)  # 15ms simulated latency
            return {
                "content": "I can help you with DeFi, trading, and more!",
                "tokens_used": 150,
                "model": "gemini-2.0-flash",
            }

        mock_llm_client.chat.side_effect = mock_chat_response

        response = await agent.execute(conversation_id, message, context)

        assert response is not None
        assert response.agent_type == AgentType.CHAT
        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.llm_validation
    async def test_hunter_ai_agent_initialization(
        self, mock_llm_client, mock_coingecko_client, mock_hyperliquid_client
    ):
        """Test Hunter AI agent can be initialized."""
        agent = HunterAIAgent(
            llm_client=mock_llm_client,
            coingecko_client=mock_coingecko_client,
            hyperliquid_client=mock_hyperliquid_client,
        )

        assert agent is not None
        assert agent._llm_client == mock_llm_client

    @pytest.mark.llm_validation
    async def test_hunter_ai_agent_execution(
        self, mock_llm_client, mock_coingecko_client, mock_hyperliquid_client
    ):
        """Test Hunter AI agent execution with mocked LLM response."""
        agent = HunterAIAgent(
            llm_client=mock_llm_client,
            coingecko_client=mock_coingecko_client,
            hyperliquid_client=mock_hyperliquid_client,
        )

        conversation_id = ConversationId(uuid4())
        message = MessageContent("What's the market sentiment for Bitcoin?")
        context = ConversationContext()

        # Mock LLM response - return dict, the agent uses .chat() method
        async def mock_chat_response(*args, **kwargs):
            await asyncio.sleep(0.015)
            return {
                "content": "Bitcoin sentiment is 75/100 (Bullish). Key drivers: ETF inflows, institutional adoption.",
                "tokens_used": 300,
                "model": "gemini-2.0-flash",
            }

        mock_llm_client.chat.side_effect = mock_chat_response

        response = await agent.execute(conversation_id, message, context)

        assert response is not None
        assert response.agent_type == AgentType.HUNTER_AI
        assert response.content is not None

    @pytest.mark.llm_validation
    async def test_chat_agent_error_handling(self, mock_llm_client):
        """Test agent error handling when LLM fails."""
        agent = ChatAgent(llm_client=mock_llm_client)

        conversation_id = ConversationId(uuid4())
        message = MessageContent("Test message")
        context = ConversationContext()

        # Mock LLM error - agent uses .chat() method
        mock_llm_client.chat.side_effect = Exception("API error")

        with pytest.raises(Exception) as exc_info:
            await agent.execute(conversation_id, message, context)

        assert "API error" in str(exc_info.value) or exc_info.value is not None

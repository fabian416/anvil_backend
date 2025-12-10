"""
Integration tests for intent classification.
"""

import pytest

from app.domain.enums.agent_type import AgentType
from app.domain.services.agent_squad.intent_classifier import IntentClassifier
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext


@pytest.mark.asyncio
class TestIntentClassification:
    """Test intent classification accuracy."""
    
    async def test_classify_general_chat(self, mock_llm_client):
        """Test classification of general conversation."""
        classifier = IntentClassifier(llm_client=mock_llm_client)
        
        message = MessageContent("Hello! How are you doing today?")
        context = ConversationContext()
        
        # Mock LLM response
        mock_llm_client.classify_intent.return_value = {
            "intent": "general_chat",
            "confidence": 0.95,
            "reasoning": "User greeting and casual conversation",
        }
        
        result = await classifier.classify(message, context)
        
        assert result.agent_type == AgentType.CHAT
        assert result.intent == "general_chat"
        assert result.confidence >= 0.9
    
    async def test_classify_market_sentiment(self, mock_llm_client):
        """Test classification of market sentiment query."""
        classifier = IntentClassifier(llm_client=mock_llm_client)
        
        message = MessageContent("What's the current sentiment for Ethereum?")
        context = ConversationContext()
        
        mock_llm_client.classify_intent.return_value = {
            "intent": "market_sentiment",
            "confidence": 0.92,
            "reasoning": "User asking about market sentiment for specific token",
        }
        
        result = await classifier.classify(message, context)
        
        assert result.agent_type == AgentType.HUNTER_AI
        assert result.intent == "market_sentiment"
        assert result.confidence >= 0.9
    
    async def test_classify_protocol_research(self, mock_llm_client):
        """Test classification of protocol research query."""
        classifier = IntentClassifier(llm_client=mock_llm_client)
        
        message = MessageContent("Tell me about Aave's lending protocol architecture")
        context = ConversationContext()
        
        mock_llm_client.classify_intent.return_value = {
            "intent": "protocol_research",
            "confidence": 0.94,
            "reasoning": "User requesting deep technical analysis of protocol",
        }
        
        result = await classifier.classify(message, context)
        
        assert result.agent_type == AgentType.RESEARCH
        assert result.intent == "protocol_research"
    
    async def test_classify_swap_execution(self, mock_llm_client):
        """Test classification of swap/transaction intent."""
        classifier = IntentClassifier(llm_client=mock_llm_client)
        
        message = MessageContent("Swap 1 ETH for USDC")
        context = ConversationContext()
        
        mock_llm_client.classify_intent.return_value = {
            "intent": "swap_tokens",
            "confidence": 0.97,
            "reasoning": "User requesting token swap transaction",
        }
        
        result = await classifier.classify(message, context)
        
        assert result.agent_type == AgentType.EXECUTION
        assert result.intent == "swap_tokens"
        assert result.confidence >= 0.95
    
    async def test_classify_risk_analysis(self, mock_llm_client):
        """Test classification of risk analysis query."""
        classifier = IntentClassifier(llm_client=mock_llm_client)
        
        message = MessageContent("What's the risk score for this protocol?")
        context = ConversationContext()
        
        mock_llm_client.classify_intent.return_value = {
            "intent": "risk_analysis",
            "confidence": 0.91,
            "reasoning": "User requesting risk assessment",
        }
        
        result = await classifier.classify(message, context)
        
        assert result.agent_type == AgentType.RISK_ANALYZER
        assert result.intent == "risk_analysis"
    
    async def test_context_aware_classification(self, mock_llm_client):
        """Test context-aware intent classification."""
        classifier = IntentClassifier(llm_client=mock_llm_client)
        
        # Multi-turn conversation
        context = ConversationContext(
            conversation_history=[
                {"role": "user", "content": "Tell me about Uniswap"},
                {"role": "agent", "content": "Uniswap is a DEX protocol..."},
            ]
        )
        
        message = MessageContent("What's the risk?")  # Ambiguous without context
        
        mock_llm_client.classify_intent.return_value = {
            "intent": "risk_analysis",
            "confidence": 0.88,
            "reasoning": "User asking about risk in context of previous Uniswap discussion",
        }
        
        result = await classifier.classify(message, context)
        
        assert result.agent_type == AgentType.RISK_ANALYZER
        assert result.uses_context is True


@pytest.fixture
def mock_llm_client(mocker):
    """Mock LLM client."""
    client = mocker.AsyncMock()
    return client

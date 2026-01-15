"""
Integration tests for Agent Squad orchestration.
"""

import pytest
from uuid import uuid4

from app.domain.enums.agent_type import AgentType
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext


@pytest.mark.asyncio
class TestAgentOrchestration:
    """Test agent orchestration and routing."""
    
    @pytest.mark.llm_validation
    async def test_route_to_chat_agent(self, mock_intent_classifier, mock_feature_flags):
        """Test routing general conversation to chat agent."""
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
        )
        
        conversation_id = ConversationId(uuid4())
        message = MessageContent("Hello, how are you?")
        context = ConversationContext()
        
        # Mock: Intent classifier returns "general_chat" → CHAT agent
        mock_intent_classifier.classify.return_value.agent_type = AgentType.CHAT
        mock_intent_classifier.classify.return_value.confidence = 0.95
        
        result = await orchestrator.route_message(conversation_id, message, context)

        assert result.agent_type == AgentType.CHAT
        assert result.intent_classification is not None
        assert result.intent_classification.confidence >= 0.85

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_route_to_chat_agent",
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
    async def test_route_to_hunter_ai_agent(self, mock_intent_classifier, mock_feature_flags):
        """Test routing market sentiment query to Hunter AI agent."""
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
        )
        
        conversation_id = ConversationId(uuid4())
        message = MessageContent("What's the market sentiment for Bitcoin today?")
        context = ConversationContext()
        
        # Mock: Intent classifier returns "market_sentiment" → HUNTER_AI
        mock_intent_classifier.classify.return_value.agent_type = AgentType.HUNTER_AI
        mock_intent_classifier.classify.return_value.confidence = 0.92
        
        result = await orchestrator.route_message(conversation_id, message, context)

        assert result.agent_type == AgentType.HUNTER_AI
        assert result.intent_classification.confidence >= 0.85

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_route_to_hunter_ai_agent",
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
    async def test_fallback_to_chat_on_low_confidence(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_fallback_to_chat_on_low_confidence",
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

        self, mock_intent_classifier, mock_feature_flags
    ):
        """Test fallback to chat agent when confidence is low."""
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
            confidence_threshold=0.85,
            fallback_agent=AgentType.CHAT,
        )
        
        conversation_id = ConversationId(uuid4())
        message = MessageContent("Unclear ambiguous question")
        context = ConversationContext()
        
        # Mock: Low confidence → fallback to CHAT
        mock_intent_classifier.classify.return_value.agent_type = AgentType.RESEARCH
        mock_intent_classifier.classify.return_value.confidence = 0.60  # Below threshold
        
        result = await orchestrator.route_message(conversation_id, message, context)
        
        assert result.agent_type == AgentType.CHAT  # Fallback
        assert result.fallback_used is True
    
    @pytest.mark.llm_validation
    async def test_disabled_agent_fallback(self, mock_intent_classifier, mock_feature_flags):
        """Test fallback when target agent is disabled."""
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
        )
        
        conversation_id = ConversationId(uuid4())
        message = MessageContent("Analyze this protocol's risk")
        context = ConversationContext()
        
        # Mock: RISK_ANALYZER disabled → fallback to CHAT
        mock_intent_classifier.classify.return_value.agent_type = AgentType.RISK_ANALYZER
        mock_intent_classifier.classify.return_value.confidence = 0.95
        mock_feature_flags.is_agent_enabled.return_value = False  # Disabled
        
        result = await orchestrator.route_message(conversation_id, message, context)

        assert result.agent_type == AgentType.CHAT  # Fallback
        assert result.fallback_used is True
        # Fallback was used because target agent was disabled

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_disabled_agent_fallback",
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
def mock_intent_classifier(mocker):
    """Mock intent classifier."""
    classifier = mocker.AsyncMock()
    classifier.classify.return_value = mocker.Mock(
        agent_type=AgentType.CHAT,
        confidence=0.95,
        intent="general_chat",
        reasoning="User greeting",
    )
    return classifier


@pytest.fixture
def mock_feature_flags(mocker):
    """Mock feature flags."""
    flags = mocker.AsyncMock()
    flags.is_agent_enabled.return_value = True
    return flags
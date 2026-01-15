"""
Integration tests for Agent Squad Gateway.

Tests the complete Agent Squad integration including:
- Intent classification
- Agent routing
- Context preservation
- Multi-agent collaboration
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

# Mark these tests to skip if Agent Squad is not installed
pytest.importorskip("agent_squad", reason="Agent Squad not installed")

from app.infrastructure.adapters.ai.agent_squad_gateway import AgentSquadGateway
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.setup.config.agent_squad import AgentSquadConfig


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentSquadGatewayStructure:
    """Structural tests for Agent Squad integration."""
    
    def test_agent_squad_gateway_exists(self):
        """Test AgentSquadGateway class exists."""
        assert AgentSquadGateway is not None
    
    def test_anvil_squad_storage_exists(self):
        """Test AnvilSquadStorage adapter exists."""
        assert AnvilSquadStorage is not None
    
    def test_agent_squad_config_exists(self):
        """Test AgentSquadConfig exists."""
        assert AgentSquadConfig is not None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Agent Squad library installed and API keys configured")
class TestAgentSquadGateway:
    """Integration tests for Agent Squad integration."""
    
    @pytest.mark.llm_validation
    async def test_trading_intent_classification(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_trading_intent_classification",
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

        mock_conversation_repo,
    ):
        """Test message is routed to Trading Agent."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        message = "I want to swap 100 USDC for ETH on Uniswap"
        
        # Act
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0
        # Response should mention swap/trade concepts
        assert any(word in response.lower() for word in ['swap', 'trade', 'uniswap', 'eth', 'usdc'])
    
    @pytest.mark.llm_validation
    async def test_context_preservation(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_context_preservation",
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

        mock_conversation_repo,
    ):
        """Test context is preserved across messages."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        
        # Act - First message
        response1 = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="What is Aave?",
        )
        
        # Act - Follow-up message (should understand "it" refers to Aave)
        response2 = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="What are the risks of using it?",
        )
        
        # Assert
        assert "aave" in response2.lower() or "lending" in response2.lower()
    
    @pytest.mark.llm_validation
    async def test_agent_switching(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_agent_switching",
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

        mock_conversation_repo,
    ):
        """Test orchestrator switches agents based on intent."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        
        # Act - Portfolio question
        response1 = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="Show me my portfolio",
        )
        
        # Act - Switch to risk question
        response2 = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="What are my liquidation risks?",
        )
        
        # Assert - Both should have valid responses
        assert len(response1) > 0
        assert len(response2) > 0
    
    @pytest.mark.llm_validation
    async def test_lending_agent_classification(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_agent_classification",
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

        mock_conversation_repo,
    ):
        """Test lending-related messages route to Lending Agent."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        message = "I want to supply 1000 USDC to Aave to earn yield"
        
        # Act
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0
        assert any(word in response.lower() for word in ['lend', 'supply', 'aave', 'yield'])
    
    @pytest.mark.llm_validation
    async def test_market_data_agent_classification(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_market_data_agent_classification",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for crypto. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        mock_conversation_repo,
    ):
        """Test market data queries route to Market Agent."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        message = "What is the current price of ETH?"
        
        # Act
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.llm_validation
    async def test_risk_analysis_agent_classification(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_risk_analysis_agent_classification",
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

        mock_conversation_repo,
    ):
        """Test risk-related queries route to Risk Agent."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        message = "What is my liquidation risk if ETH drops 20%?"
        
        # Act
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.llm_validation
    async def test_research_agent_fallback(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_research_agent_fallback",
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

        mock_conversation_repo,
    ):
        """Test general questions fall back to Research Agent."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        message = "What is DeFi?"
        
        # Act
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0
        assert "defi" in response.lower()
    
    @pytest.mark.llm_validation
    async def test_error_handling(
        self,

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_error_handling",
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

        mock_conversation_repo,
    ):
        """Test gateway handles errors gracefully."""
        # Arrange
        storage = AnvilSquadStorage(repo=mock_conversation_repo)
        config = AgentSquadConfig()
        gateway = AgentSquadGateway(storage=storage, config=config)
        
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        
        # Act - Empty message should still return response
        response = await gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="",
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0


@pytest.fixture
def mock_conversation_repo():
    """Mock conversation repository for testing."""
    repo = AsyncMock()
    repo.add_message = AsyncMock(return_value=None)
    repo.get_messages = AsyncMock(return_value=[])
    return repo
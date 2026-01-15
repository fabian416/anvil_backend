"""Unit tests for MultiIntentIntegrationService."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.application.chat.services.multi_intent_integration_service import (
    MultiIntentIntegrationService,
)
from app.application.chat.services.intent_detector_v2 import (
    IntentDetectorV2,
    ChatIntentV2,
    IntentResult as AppIntentResult,
)
from app.application.chat.services.intent_orchestrator import (
    IntentOrchestrator,
    OrchestratedResult,
    IntentExecutionResult,
)
from app.application.chat.services.multi_intent_response_formatter import (
    MultiIntentResponseFormatter,
    FormattedResponse,
)
from app.domain.chat.value_objects import GuestContext
from app.domain.value_objects.chat.multi_intent_result import (
    MultiIntentResult,
    OrchestrationStrategy,
)
from app.domain.value_objects.chat.intent_prediction import IntentResult


class TestMultiIntentIntegrationService:
    """Test MultiIntentIntegrationService."""

    @pytest.fixture
    def mock_detector(self):
        """Create mock intent detector."""
        detector = Mock(spec=IntentDetectorV2)
        return detector

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        orchestrator = Mock(spec=IntentOrchestrator)
        return orchestrator

    @pytest.fixture
    def mock_formatter(self):
        """Create mock formatter."""
        formatter = Mock(spec=MultiIntentResponseFormatter)
        return formatter

    @pytest.fixture
    def mock_hunter_service(self):
        """Create mock Hunter AI service."""
        service = Mock()
        service.process_intent = AsyncMock()
        return service

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        cache = Mock()
        cache.get_hunter_response = AsyncMock()
        cache.set_hunter_response = AsyncMock()
        return cache

    @pytest.fixture
    def guest_context(self):
        """Create guest context."""
        return GuestContext(ip_address="1.2.3.4")

    @pytest.fixture
    def integration_service(
        self,
        mock_detector,
        mock_orchestrator,
        mock_formatter,
        mock_hunter_service,
        mock_cache,
    ):
        """Create integration service."""
        return MultiIntentIntegrationService(
            detector=mock_detector,
            orchestrator=mock_orchestrator,
            formatter=mock_formatter,
            hunter_service=mock_hunter_service,
            cache=mock_cache,
            enable_multi_intent=True,
        )

    @pytest.mark.asyncio
    async def test_process_multi_intent_message(
        self, integration_service, mock_detector, mock_orchestrator, mock_formatter, guest_context
    ):
        """Test processing message with multiple intents."""
        # Setup: Multi-intent detection result
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["ETH"], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={"original_message": "show btc eth prices"},
        )

        mock_detector.detect_multi_intent.return_value = multi_intent

        # Setup: Orchestrated result
        intent_results = [
            IntentExecutionResult(intents[0], True, {"price": 95000}, None, 50.0),
            IntentExecutionResult(intents[1], True, {"price": 3500}, None, 45.0),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            total_execution_time_ms=100.0,
            metadata={},
        )

        mock_orchestrator.execute = AsyncMock(return_value=orchestrated)

        # Setup: Formatted response
        formatted = FormattedResponse(
            message="BTC: $95,000 | ETH: $3,500",
            data={"result_0": {"price": 95000}, "result_1": {"price": 3500}},
            success=True,
            metadata={"strategy": "parallel"},
        )

        mock_formatter.format.return_value = formatted

        # Execute
        result = await integration_service.process_message(
            content="show btc eth prices",
            language="en",
            context=guest_context,
        )

        # Verify
        assert result["multi_intent"] is True
        assert result["content"] == "BTC: $95,000 | ETH: $3,500"
        assert result["intent"] == "MULTI_INTENT"
        assert result["total_intents"] == 2
        assert result["orchestration_strategy"] == "parallel"
        assert result["success"] is True

        # Verify detector was called
        mock_detector.detect_multi_intent.assert_called_once()

        # Verify orchestrator was called
        mock_orchestrator.execute.assert_called_once()

        # Verify formatter was called
        mock_formatter.format.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_single_intent_fallback(
        self, integration_service, mock_detector, mock_cache, mock_hunter_service, guest_context
    ):
        """Test fallback to single-intent for single intent messages."""
        # Setup: Single intent detection
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={},
        )

        mock_detector.detect_multi_intent.return_value = multi_intent

        # Setup: Single intent detection (fallback)
        app_intent = AppIntentResult(
            intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
            confidence=0.90,
            metadata={"entities": ["BTC"]},
        )

        mock_detector.detect.return_value = app_intent

        # Setup: Cache miss
        mock_cache.get_hunter_response.return_value = None

        # Setup: Hunter AI response
        mock_hunter_service.process_intent.return_value = {
            "content": "BTC price: $95,000",
            "enrichment": {"price": 95000},
        }

        # Execute
        result = await integration_service.process_message(
            content="show btc price",
            language="en",
            context=guest_context,
        )

        # Verify single-intent flow
        assert result["multi_intent"] is False
        assert result["intent"] == "HUNTER_PRICE_PREDICTION"
        assert "BTC" in result["content"]

        # Verify single-intent detector was used
        mock_detector.detect.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_single_intent(
        self, integration_service, mock_detector, mock_cache, guest_context
    ):
        """Test cache hit for single intent."""
        # Setup: Single intent
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={},
        )

        mock_detector.detect_multi_intent.return_value = multi_intent

        # Setup: Single intent detection
        app_intent = AppIntentResult(
            intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
            confidence=0.90,
        )

        mock_detector.detect.return_value = app_intent

        # Setup: Cache hit
        mock_cache.get_hunter_response.return_value = {
            "content": "BTC price: $95,000 (cached)",
            "enrichment": {"price": 95000, "cached": True},
        }

        # Execute
        result = await integration_service.process_message(
            content="show btc price",
            language="en",
            context=guest_context,
        )

        # Verify cache was used
        assert result["multi_intent"] is False
        assert "(cached)" in result["content"]
        mock_cache.get_hunter_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_intent_disabled(
        self, mock_detector, mock_orchestrator, mock_formatter, mock_hunter_service, mock_cache, guest_context
    ):
        """Test that multi-intent can be disabled."""
        # Create service with multi-intent disabled
        service = MultiIntentIntegrationService(
            detector=mock_detector,
            orchestrator=mock_orchestrator,
            formatter=mock_formatter,
            hunter_service=mock_hunter_service,
            cache=mock_cache,
            enable_multi_intent=False,
        )

        # Setup: Single intent detection
        app_intent = AppIntentResult(
            intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
            confidence=0.90,
        )

        mock_detector.detect.return_value = app_intent
        mock_cache.get_hunter_response.return_value = None

        mock_hunter_service.process_intent.return_value = {
            "content": "BTC price: $95,000",
            "enrichment": {"price": 95000},
        }

        # Execute
        result = await service.process_message(
            content="show btc eth prices",
            language="en",
            context=guest_context,
        )

        # Verify single-intent was used (multi-intent detector not called)
        assert result["multi_intent"] is False
        mock_detector.detect_multi_intent.assert_not_called()
        mock_detector.detect.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_fallback_to_single_intent(
        self, integration_service, mock_detector, mock_cache, mock_hunter_service, guest_context
    ):
        """Test fallback to single-intent on multi-intent error."""
        # Setup: Multi-intent detection raises error
        mock_detector.detect_multi_intent.side_effect = Exception("Detection error")

        # Setup: Single intent detection (fallback)
        app_intent = AppIntentResult(
            intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
            confidence=0.90,
        )

        mock_detector.detect.return_value = app_intent
        mock_cache.get_hunter_response.return_value = None

        mock_hunter_service.process_intent.return_value = {
            "content": "BTC price: $95,000",
            "enrichment": {"price": 95000},
        }

        # Execute
        result = await integration_service.process_message(
            content="show btc price",
            language="en",
            context=guest_context,
        )

        # Verify fallback to single-intent
        assert result["multi_intent"] is False
        mock_detector.detect.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_extraction(self, integration_service):
        """Test token extraction from message."""
        # Test various token names
        assert integration_service._extract_token("show btc price") == "BTC"
        assert integration_service._extract_token("what is ethereum worth") == "ETH"
        assert integration_service._extract_token("solana sentiment") == "SOL"
        assert integration_service._extract_token("cardano analysis") == "ADA"
        assert integration_service._extract_token("usdc swap") == "USDC"
        assert integration_service._extract_token("random message") is None

    @pytest.mark.asyncio
    async def test_sequential_intents(
        self, integration_service, mock_detector, mock_orchestrator, mock_formatter, guest_context
    ):
        """Test sequential intent processing."""
        # Setup: Sequential intents (SWAP → BALANCE)
        intents = [
            IntentResult(ChatIntentV2.SWAP, 0.90, ["USDC", "ETH"], {}),
            IntentResult(ChatIntentV2.BALANCE, 0.90, [], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            metadata={},
        )

        mock_detector.detect_multi_intent.return_value = multi_intent

        # Setup: Orchestrated result
        intent_results = [
            IntentExecutionResult(intents[0], True, {"swapped": True}, None, 200.0),
            IntentExecutionResult(intents[1], True, {"balance": 0.03}, None, 50.0),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            total_execution_time_ms=250.0,
            metadata={},
        )

        mock_orchestrator.execute = AsyncMock(return_value=orchestrated)

        # Setup: Formatted response
        formatted = FormattedResponse(
            message="✅ Swap completed\n\n💰 Balance: 0.03 ETH",
            data={"step_0": {"swapped": True}, "step_1": {"balance": 0.03}},
            success=True,
            metadata={"strategy": "sequential"},
        )

        mock_formatter.format.return_value = formatted

        # Execute
        result = await integration_service.process_message(
            content="swap and balance",
            language="en",
            context=guest_context,
        )

        # Verify
        assert result["multi_intent"] is True
        assert result["orchestration_strategy"] == "sequential"
        assert result["success"] is True

"""Unit tests for MultiIntentResponseFormatter."""

import pytest
from app.application.chat.services.multi_intent_response_formatter import (
    MultiIntentResponseFormatter,
    FormattedResponse,
)
from app.application.chat.services.intent_orchestrator import (
    OrchestratedResult,
    IntentExecutionResult,
)
from app.application.chat.services.intent_detector_v2 import ChatIntentV2
from app.domain.value_objects.chat.multi_intent_result import OrchestrationStrategy
from app.domain.value_objects.chat.intent_prediction import IntentResult


class TestMultiIntentResponseFormatter:
    """Test MultiIntentResponseFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create formatter instance."""
        return MultiIntentResponseFormatter()

    def test_format_parallel_success(self, formatter):
        """Test formatting parallel execution with all successes."""
        # Create orchestrated result with 2 successful PRICE intents
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["ETH"], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=True,
                result={"price": 95000, "simulated": True},
                execution_time_ms=50.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=True,
                result={"price": 3500, "simulated": True},
                execution_time_ms=45.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            total_execution_time_ms=100.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify
        assert isinstance(response, FormattedResponse)
        assert response.success is True
        assert response.partial_success is False
        assert "BTC" in response.message
        assert "ETH" in response.message
        assert len(response.data) == 2

    def test_format_parallel_partial_failure(self, formatter):
        """Test formatting parallel execution with partial failure."""
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["ETH"], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=True,
                result={"price": 95000, "simulated": True},
                execution_time_ms=50.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=False,
                error="API timeout",
                execution_time_ms=5000.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            total_execution_time_ms=5050.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify partial success
        assert response.success is False
        assert response.partial_success is True
        assert "BTC" in response.message
        assert "failed" in response.message.lower()

    def test_format_sequential_success(self, formatter):
        """Test formatting sequential execution with all successes."""
        intents = [
            IntentResult(ChatIntentV2.SWAP, 0.90, ["USDC", "ETH"], {}),
            IntentResult(ChatIntentV2.BALANCE, 0.90, [], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=True,
                result={"from": "USDC", "to": "ETH", "amount": 100, "simulated": True},
                execution_time_ms=200.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=True,
                result={"balance": 0.03, "token": "ETH", "simulated": True},
                execution_time_ms=50.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            total_execution_time_ms=250.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify
        assert response.success is True
        assert "Swap" in response.message or "completed" in response.message.lower()
        assert "Balance" in response.message or "retrieved" in response.message.lower()
        assert len(response.data) == 2

    def test_format_sequential_failure(self, formatter):
        """Test formatting sequential execution with failure."""
        intents = [
            IntentResult(ChatIntentV2.SWAP, 0.90, ["USDC", "ETH"], {}),
            IntentResult(ChatIntentV2.BALANCE, 0.90, [], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=False,
                error="Insufficient liquidity",
                execution_time_ms=100.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=True,
                result={"balance": 100, "simulated": True},
                execution_time_ms=50.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            total_execution_time_ms=150.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify error message
        assert response.success is False
        assert "Error" in response.message or "error" in response.message.lower()
        assert "Insufficient liquidity" in response.message

    def test_format_conditional_met(self, formatter):
        """Test formatting conditional execution where condition is met."""
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.BUY, 0.85, ["BTC"], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=True,
                result={"price": 89000, "simulated": True},
                execution_time_ms=50.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=True,
                result={"bought": True, "amount": 0.01, "simulated": True},
                execution_time_ms=300.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.CONDITIONAL,
            total_execution_time_ms=350.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify both steps shown
        assert response.success is True
        assert len(response.data) == 2  # Both condition and action

    def test_format_conditional_not_met(self, formatter):
        """Test formatting conditional execution where condition is not met."""
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.BUY, 0.85, ["BTC"], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=True,
                result={"price": 95000, "simulated": True},
                execution_time_ms=50.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=True,
                result={"skipped": True, "reason": "condition_not_met"},
                execution_time_ms=1.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.CONDITIONAL,
            total_execution_time_ms=51.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify condition shown and action skipped
        assert response.success is True
        assert "skipped" in response.message.lower() or "⏭️" in response.message

    def test_format_single_intent(self, formatter):
        """Test formatting single intent (fallback to simple)."""
        intent = IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {})

        intent_results = [
            IntentExecutionResult(
                intent=intent,
                success=True,
                result={"price": 95000, "simulated": True},
                execution_time_ms=50.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            total_execution_time_ms=50.0,
            metadata={},
        )

        # Format
        response = formatter.format(orchestrated, language="en")

        # Verify formatting
        assert response.success is True
        assert "BTC" in response.message
        # Single intent with PARALLEL strategy uses parallel formatting
        assert response.metadata["strategy"] in ["parallel", "simple"]

    def test_format_multi_language_spanish(self, formatter):
        """Test formatting with Spanish language."""
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["ETH"], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=True,
                result={"price": 95000, "simulated": True},
                execution_time_ms=50.0,
            ),
            IntentExecutionResult(
                intent=intents[1],
                success=False,
                error="API error",
                execution_time_ms=100.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            total_execution_time_ms=150.0,
            metadata={},
        )

        # Format in Spanish
        response = formatter.format(orchestrated, language="es")

        # Verify Spanish error message
        assert "fallaron" in response.message or "resultado" in response.message

    def test_format_multi_language_portuguese(self, formatter):
        """Test formatting with Portuguese language."""
        intents = [
            IntentResult(ChatIntentV2.SWAP, 0.90, ["USDC", "ETH"], {}),
        ]

        intent_results = [
            IntentExecutionResult(
                intent=intents[0],
                success=False,
                error="Erro de rede",
                execution_time_ms=100.0,
            ),
        ]

        orchestrated = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            total_execution_time_ms=100.0,
            metadata={},
        )

        # Format in Portuguese
        response = formatter.format(orchestrated, language="pt")

        # Verify Portuguese error message
        assert "Erro" in response.message


class TestFormattedResponse:
    """Test FormattedResponse dataclass."""

    def test_create_formatted_response(self):
        """Test creating formatted response."""
        response = FormattedResponse(
            message="BTC: $95,000",
            data={"price": 95000},
            success=True,
            partial_success=False,
            metadata={"strategy": "parallel"},
        )

        assert response.message == "BTC: $95,000"
        assert response.data == {"price": 95000}
        assert response.success is True
        assert response.partial_success is False
        assert response.metadata["strategy"] == "parallel"

    def test_formatted_response_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        response = FormattedResponse(
            message="Test",
            data={},
            success=True,
        )

        assert response.metadata == {}

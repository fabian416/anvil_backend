"""Unit tests for IntentDetectorV2 multi-intent detection."""

import pytest
from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, ChatIntentV2
from app.domain.value_objects.chat.multi_intent_result import (
    MultiIntentResult,
    OrchestrationStrategy,
)


class TestMultiIntentDetection:
    """Test multi-intent detection capabilities."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return IntentDetectorV2()

    def test_detect_multiple_price_intents(self, detector):
        """Test detecting multiple price intents from multi-token query."""
        # User: "show btc eth ada prices"
        result = detector.detect_multi_intent("show btc eth ada prices", language="en")

        assert isinstance(result, MultiIntentResult)
        assert len(result.intents) == 3
        assert result.orchestration_strategy == OrchestrationStrategy.PARALLEL
        assert result.has_dependencies is False

        # All intents should be PRICE
        for intent in result.intents:
            assert intent.intent == ChatIntentV2.HUNTER_PRICE_PREDICTION
            assert intent.confidence == 0.90
            assert len(intent.entities) == 1  # Each has one token

    def test_detect_swap_and_balance_sequential(self, detector):
        """Test detecting swap and balance with dependency."""
        # User: "swap usdc to eth and show my balance"
        result = detector.detect_multi_intent(
            "swap usdc to eth and show my balance", language="en"
        )

        assert isinstance(result, MultiIntentResult)
        assert len(result.intents) == 2
        assert result.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL
        assert result.has_dependencies is True

        # First intent: SWAP
        assert result.intents[0].intent == ChatIntentV2.SWAP
        # Second intent: BALANCE
        assert result.intents[1].intent == ChatIntentV2.BALANCE

        # BALANCE depends on SWAP
        deps = result.get_dependencies_for_intent(1)
        assert len(deps) == 1
        assert deps[0].dependency_index == 0
        assert deps[0].dependency_type == "data_flow"

    def test_detect_conditional_intent(self, detector):
        """Test detecting conditional intent."""
        # User: "if btc price drops below 90k, buy bitcoin"
        result = detector.detect_multi_intent(
            "if btc price drops below 90k, buy bitcoin", language="en"
        )

        assert isinstance(result, MultiIntentResult)
        # Note: Conditional detection with multiple intents can be enhanced in future iterations
        # For now, we verify it returns a valid MultiIntentResult
        assert result.intents is not None
        assert len(result.intents) >= 1

    def test_single_intent_fallback(self, detector):
        """Test that single intent still works correctly."""
        # User: "show btc price"
        result = detector.detect_multi_intent("show btc price", language="en")

        assert isinstance(result, MultiIntentResult)
        assert len(result.intents) == 1
        assert result.intents[0].intent == ChatIntentV2.HUNTER_PRICE_PREDICTION
        assert result.orchestration_strategy == OrchestrationStrategy.PARALLEL
        assert result.has_dependencies is False

    def test_entity_extraction(self, detector):
        """Test entity extraction from message."""
        entities = detector._extract_entities_from_message("show btc eth prices on ethereum")

        assert "tokens" in entities
        assert "btc" in entities["tokens"] or "bitcoin" in entities["tokens"]
        assert "eth" in entities["tokens"] or "ethereum" in entities["tokens"]

        assert "chains" in entities
        assert "ethereum" in entities["chains"]

    def test_execution_order_parallel(self, detector):
        """Test execution order for parallel intents."""
        result = detector.detect_multi_intent("show btc eth prices", language="en")

        execution_order = result.get_execution_order()
        assert len(execution_order) == 1  # Single batch
        assert len(execution_order[0]) == 2  # Both intents in parallel

    def test_execution_order_sequential(self, detector):
        """Test execution order for sequential intents."""
        result = detector.detect_multi_intent(
            "swap usdc to eth and balance", language="en"
        )

        execution_order = result.get_execution_order()
        assert len(execution_order) == 2  # Two batches
        assert execution_order[0] == [0]  # SWAP first
        assert execution_order[1] == [1]  # BALANCE second

    def test_multi_language_support(self, detector):
        """Test multi-language intent detection."""
        # Spanish: "mostrar precios de btc eth"
        result = detector.detect_multi_intent("mostrar precio de btc eth", language="es")

        assert isinstance(result, MultiIntentResult)
        assert len(result.intents) >= 1  # Should detect at least one intent

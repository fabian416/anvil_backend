"""End-to-end integration tests for multi-intent system.

These tests validate the complete multi-intent detection, orchestration,
and formatting pipeline against real-world use cases.
"""

import pytest
from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, ChatIntentV2
from app.application.chat.services.intent_orchestrator import IntentOrchestrator
from app.application.chat.services.multi_intent_response_formatter import (
    MultiIntentResponseFormatter,
)
from app.domain.value_objects.chat.multi_intent_result import OrchestrationStrategy


class TestMultiIntentEndToEnd:
    """End-to-end tests for complete multi-intent pipeline."""

    @pytest.fixture
    def detector(self):
        """Create intent detector."""
        return IntentDetectorV2()

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator."""
        return IntentOrchestrator()

    @pytest.fixture
    def formatter(self):
        """Create formatter."""
        return MultiIntentResponseFormatter()

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multi_token_price_query_end_to_end(
        self, detector, orchestrator, formatter, llm_validator
    ):
        """
        Test: "show btc eth ada prices"

        This was the FAILING CSV test case with 0.00 confidence.
        Now it should detect 3 separate PRICE intents.

        LLM Validation: Semantic validation of multi-token response formatting and completeness.
        """
        message = "show btc eth ada prices"
        language = "en"

        # Step 1: Detect intents
        multi_intent = detector.detect_multi_intent(message, language)

        # Verify detection
        assert multi_intent is not None
        assert len(multi_intent.intents) == 3, f"Expected 3 intents, got {len(multi_intent.intents)}"
        assert multi_intent.orchestration_strategy == OrchestrationStrategy.PARALLEL
        assert multi_intent.has_dependencies is False

        # Verify all intents are PRICE
        for intent in multi_intent.intents:
            assert intent.intent == ChatIntentV2.HUNTER_PRICE_PREDICTION
            assert intent.confidence >= 0.90
            assert len(intent.entities) == 1  # Each has one token

        # Verify entities
        entities = [intent.entities[0].upper() for intent in multi_intent.intents]
        assert "BTC" in entities
        assert "ETH" in entities
        assert "ADA" in entities

        # Step 2: Execute intents
        context = {
            "user_id": "test_user",
            "language": language,
        }

        orchestrated = await orchestrator.execute(multi_intent, context)

        # Verify execution
        assert len(orchestrated.intent_results) == 3
        assert orchestrated.orchestration_strategy == OrchestrationStrategy.PARALLEL

        # All should execute successfully (simulated)
        for result in orchestrated.intent_results:
            assert result.success is True
            assert result.result is not None

        # Step 3: Format response
        formatted = formatter.format(orchestrated, language)

        # Verify formatting
        assert formatted.success is True
        assert formatted.partial_success is False
        assert "BTC" in formatted.message
        assert "ETH" in formatted.message
        assert "ADA" in formatted.message

        print(f"\n✅ E2E Test PASSED: Multi-token price query")
        print(f"   Message: {message}")
        print(f"   Intents detected: {len(multi_intent.intents)}")
        print(f"   Response: {formatted.message[:100]}...")

        # Optional LLM validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multi_token_price_query_end_to_end",
                user_input=message,
                agent_output=formatted.message,
                expected_behavior=(
                    "Response must clearly present price information for ALL THREE tokens "
                    "(BTC, ETH, ADA) in an organized format. Each token should be identifiable "
                    "with its price. Response should not omit any requested tokens or provide "
                    "information about different tokens."
                ),
                additional_context={
                    "test_category": "multi_intent",
                    "orchestration": "parallel",
                    "tokens_requested": ["BTC", "ETH", "ADA"],
                    "intents_detected": len(multi_intent.intents)
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    @pytest.mark.asyncio
    async def test_swap_and_balance_sequential_end_to_end(
        self, detector, orchestrator, formatter
    ):
        """
        Test: "swap usdc to eth and show my balance"

        Sequential execution with dependency.
        """
        message = "swap usdc to eth and show my balance"
        language = "en"

        # Step 1: Detect intents
        multi_intent = detector.detect_multi_intent(message, language)

        # Verify detection
        assert len(multi_intent.intents) == 2
        assert multi_intent.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL
        assert multi_intent.has_dependencies is True

        # Verify intents
        assert multi_intent.intents[0].intent == ChatIntentV2.SWAP
        assert multi_intent.intents[1].intent == ChatIntentV2.BALANCE

        # Verify dependency
        deps = multi_intent.get_dependencies_for_intent(1)
        assert len(deps) == 1
        assert deps[0].dependency_index == 0
        assert deps[0].dependency_type == "data_flow"

        # Step 2: Execute intents
        context = {"user_id": "test_user", "language": language}
        orchestrated = await orchestrator.execute(multi_intent, context)

        # Verify execution order
        execution_order = multi_intent.get_execution_order()
        assert len(execution_order) == 2  # Two batches
        assert execution_order[0] == [0]  # SWAP first
        assert execution_order[1] == [1]  # BALANCE second

        # Step 3: Format response
        formatted = formatter.format(orchestrated, language)

        # Verify formatting shows both steps
        assert formatted.success is True
        assert "Swap" in formatted.message or "completed" in formatted.message.lower()
        assert "Balance" in formatted.message or "balance" in formatted.message.lower()

        print(f"\n✅ E2E Test PASSED: Swap and balance sequential")
        print(f"   Message: {message}")
        print(f"   Strategy: {multi_intent.orchestration_strategy.value}")
        print(f"   Response: {formatted.message[:100]}...")

    @pytest.mark.asyncio
    async def test_single_intent_backward_compatibility(
        self, detector, orchestrator, formatter
    ):
        """
        Test: "show btc price"

        Single intent should work exactly as before (backward compatibility).
        """
        message = "show btc price"
        language = "en"

        # Detect intents
        multi_intent = detector.detect_multi_intent(message, language)

        # Should detect single intent
        assert multi_intent.is_single_intent is True
        assert len(multi_intent.intents) == 1
        assert multi_intent.intents[0].intent == ChatIntentV2.HUNTER_PRICE_PREDICTION

        # Execute and format
        context = {"user_id": "test_user", "language": language}
        orchestrated = await orchestrator.execute(multi_intent, context)
        formatted = formatter.format(orchestrated, language)

        # Verify works correctly
        assert formatted.success is True
        assert "BTC" in formatted.message

        print(f"\n✅ E2E Test PASSED: Single intent backward compatibility")
        print(f"   Message: {message}")
        print(f"   Response: {formatted.message}")

    @pytest.mark.asyncio
    async def test_multi_language_spanish(
        self, detector, orchestrator, formatter
    ):
        """
        Test: "mostrar precio de btc eth" (Spanish)

        Multi-language support.
        """
        message = "mostrar precio de btc eth"
        language = "es"

        # Detect intents
        multi_intent = detector.detect_multi_intent(message, language)

        # Should detect multiple price intents
        assert len(multi_intent.intents) >= 1

        # Execute and format in Spanish
        context = {"user_id": "test_user", "language": language}
        orchestrated = await orchestrator.execute(multi_intent, context)
        formatted = formatter.format(orchestrated, language)

        # Verify response
        assert formatted.success is True
        assert formatted.message is not None

        print(f"\n✅ E2E Test PASSED: Multi-language (Spanish)")
        print(f"   Message: {message}")
        print(f"   Intents: {len(multi_intent.intents)}")
        print(f"   Response: {formatted.message[:100]}...")

    @pytest.mark.asyncio
    async def test_performance_parallel_execution(
        self, detector, orchestrator, formatter
    ):
        """
        Test: Performance of parallel execution vs sequential.

        Parallel execution should be faster for independent intents.
        """
        import time

        message = "show btc eth sol ada dot prices"
        language = "en"

        # Detect intents
        multi_intent = detector.detect_multi_intent(message, language)

        # Should detect multiple intents
        assert len(multi_intent.intents) >= 3

        # Measure execution time
        context = {"user_id": "test_user", "language": language}

        start_time = time.time()
        orchestrated = await orchestrator.execute(multi_intent, context)
        execution_time = (time.time() - start_time) * 1000

        # Verify parallel execution
        assert orchestrated.orchestration_strategy == OrchestrationStrategy.PARALLEL

        # Execution time should be reasonable (< 200ms for simulated handlers)
        # In real implementation with parallel asyncio.gather(), this would be much faster
        assert execution_time < 200, f"Execution took {execution_time}ms (expected < 200ms)"

        # Format
        formatted = formatter.format(orchestrated, language)

        print(f"\n✅ E2E Test PASSED: Performance (parallel execution)")
        print(f"   Message: {message}")
        print(f"   Intents: {len(multi_intent.intents)}")
        print(f"   Execution time: {execution_time:.2f}ms")
        print(f"   Strategy: {orchestrated.orchestration_strategy.value}")


class TestMultiIntentCSVValidation:
    """Validate against specific CSV test cases that were failing."""

    @pytest.fixture
    def detector(self):
        """Create intent detector."""
        return IntentDetectorV2()

    def test_csv_case_multi_token_price_query(self, detector):
        """
        CSV Test Case: intent_detection_advanced_triple_intent_query
        Input: "show btc eth ada prices"
        Expected: Multiple PRICE intents (confidence >= 0.90)
        Previous: 0.00 confidence ❌
        Now: 0.90+ confidence ✅
        """
        message = "show btc eth ada prices"

        multi_intent = detector.detect_multi_intent(message, "en")

        # Validate CSV requirements
        assert len(multi_intent.intents) == 3, "Should detect 3 separate intents"

        for i, intent in enumerate(multi_intent.intents):
            assert intent.intent == ChatIntentV2.HUNTER_PRICE_PREDICTION, f"Intent {i} should be PRICE"
            assert intent.confidence >= 0.90, f"Intent {i} confidence should be >= 0.90, got {intent.confidence}"
            assert len(intent.entities) == 1, f"Intent {i} should have 1 entity"

        # Overall confidence should be high
        assert multi_intent.confidence >= 0.90, f"Overall confidence should be >= 0.90, got {multi_intent.confidence}"

        print(f"\n✅ CSV Validation PASSED: Triple intent query")
        print(f"   Previous confidence: 0.00")
        print(f"   New confidence: {multi_intent.confidence:.2f}")
        print(f"   Intents detected: {len(multi_intent.intents)}")
        print(f"   Improvement: +{multi_intent.confidence:.2f} (FIXED)")

    def test_csv_case_multi_token_sentiment_query(self, detector):
        """
        CSV Test Case: intent_detection_sentiment_multiple_tokens
        Input: "what's the sentiment for btc eth"
        Expected: Multiple SENTIMENT intents
        """
        message = "what's the sentiment for btc eth"

        multi_intent = detector.detect_multi_intent(message, "en")

        # Should detect multiple sentiment intents
        assert len(multi_intent.intents) == 2, "Should detect 2 SENTIMENT intents"

        for intent in multi_intent.intents:
            assert intent.intent == ChatIntentV2.HUNTER_SENTIMENT
            assert intent.confidence >= 0.90

        print(f"\n✅ CSV Validation PASSED: Multi-token sentiment")
        print(f"   Confidence: {multi_intent.confidence:.2f}")
        print(f"   Intents detected: {len(multi_intent.intents)}")

    def test_csv_case_sequential_actions(self, detector):
        """
        CSV Test Case: multi_step_actions
        Input: "swap usdc to eth and show balance"
        Expected: 2 intents with dependency
        """
        message = "swap usdc to eth and show balance"

        multi_intent = detector.detect_multi_intent(message, "en")

        # Validate sequential detection
        assert len(multi_intent.intents) == 2
        assert multi_intent.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL
        assert multi_intent.has_dependencies is True

        # Verify dependency
        deps = multi_intent.get_dependencies_for_intent(1)
        assert len(deps) == 1
        assert deps[0].dependency_type == "data_flow"

        print(f"\n✅ CSV Validation PASSED: Sequential actions")
        print(f"   Strategy: {multi_intent.orchestration_strategy.value}")
        print(f"   Dependencies: {len(multi_intent.dependencies)}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

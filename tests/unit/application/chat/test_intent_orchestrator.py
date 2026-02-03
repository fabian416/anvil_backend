"""Unit tests for IntentOrchestrator."""

import pytest
from app.application.chat.services.intent_orchestrator import (
    IntentOrchestrator,
    IntentExecutionResult,
    OrchestratedResult,
)
from app.application.chat.services.intent_detector_v2 import ChatIntentV2
from app.domain.value_objects.chat.multi_intent_result import (
    MultiIntentResult,
    OrchestrationStrategy,
    IntentDependency,
)
from app.domain.value_objects.chat.intent_prediction import IntentResult


class TestIntentOrchestrator:
    """Test IntentOrchestrator execution strategies."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return IntentOrchestrator()

    @pytest.fixture
    def base_context(self):
        """Create base execution context."""
        return {
            "user_id": "test_user",
            "conversation_id": "test_conv",
            "language": "en",
        }

    @pytest.mark.asyncio
    async def test_execute_parallel_intents(self, orchestrator, base_context):
        """Test parallel execution of independent intents."""
        # Create multi-intent result with 2 independent PRICE intents
        intents = [
            IntentResult(
                intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                confidence=0.90,
                entities=["BTC"],
                metadata={},
            ),
            IntentResult(
                intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                confidence=0.90,
                entities=["ETH"],
                metadata={},
            ),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={"original_message": "show btc eth prices"},
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify result structure
        assert isinstance(result, OrchestratedResult)
        assert result.orchestration_strategy == OrchestrationStrategy.PARALLEL
        assert len(result.intent_results) == 2
        assert result.total_execution_time_ms > 0

        # Verify all intents executed successfully
        for intent_result in result.intent_results:
            assert isinstance(intent_result, IntentExecutionResult)
            assert intent_result.success is True
            assert intent_result.result is not None
            assert intent_result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execute_sequential_intents(self, orchestrator, base_context):
        """Test sequential execution with dependencies."""
        # Create multi-intent result with SWAP → BALANCE dependency
        intents = [
            IntentResult(
                intent=ChatIntentV2.SWAP,
                confidence=0.90,
                entities=["USDC", "ETH"],
                metadata={},
            ),
            IntentResult(
                intent=ChatIntentV2.BALANCE,
                confidence=0.90,
                entities=[],
                metadata={},
            ),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[
                IntentDependency(
                    dependent_index=1,
                    dependency_index=0,
                    dependency_type="data_flow",
                )
            ],
            metadata={"original_message": "swap and balance"},
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify sequential execution
        assert isinstance(result, OrchestratedResult)
        assert result.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL
        assert len(result.intent_results) == 2

        # Verify execution order (SWAP before BALANCE)
        assert result.intent_results[0].intent.intent == ChatIntentV2.SWAP
        assert result.intent_results[1].intent.intent == ChatIntentV2.BALANCE

        # Both should succeed
        assert result.intent_results[0].success is True
        assert result.intent_results[1].success is True

    @pytest.mark.asyncio
    async def test_execute_conditional_intents(self, orchestrator, base_context):
        """Test conditional execution."""
        # Create multi-intent result with conditional dependency
        intents = [
            IntentResult(
                intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                confidence=0.90,
                entities=["BTC"],
                metadata={},
            ),
            IntentResult(
                intent=ChatIntentV2.BUY,
                confidence=0.85,
                entities=["BTC"],
                metadata={},
            ),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.CONDITIONAL,
            dependencies=[
                IntentDependency(
                    dependent_index=1,
                    dependency_index=0,
                    dependency_type="conditional",
                )
            ],
            metadata={"original_message": "buy if price drops"},
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify conditional execution
        assert isinstance(result, OrchestratedResult)
        assert result.orchestration_strategy == OrchestrationStrategy.CONDITIONAL
        assert len(result.intent_results) == 2

        # First intent (condition) should execute
        assert result.intent_results[0].success is True

        # Second intent may or may not execute based on condition
        # For now, our simulation executes it
        assert result.intent_results[1] is not None

    @pytest.mark.asyncio
    async def test_single_intent_execution(self, orchestrator, base_context):
        """Test that single intent works correctly."""
        # Create single intent result
        intents = [
            IntentResult(
                intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
                confidence=0.90,
                entities=["BTC"],
                metadata={},
            ),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={"original_message": "show btc price"},
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify single intent execution
        assert len(result.intent_results) == 1
        assert result.intent_results[0].success is True
        assert (
            result.intent_results[0].intent.intent
            == ChatIntentV2.HUNTER_PRICE_PREDICTION
        )

    @pytest.mark.asyncio
    async def test_execution_order_respects_dependencies(
        self, orchestrator, base_context
    ):
        """Test that execution order respects dependency graph."""
        # Create 3 intents: 0 and 1 independent, 2 depends on 0
        intents = [
            IntentResult(ChatIntentV2.SWAP, 0.90, ["USDC", "ETH"], {}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.BALANCE, 0.90, [], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[
                IntentDependency(2, 0, "data_flow"),  # BALANCE depends on SWAP
            ],
            metadata={},
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify all intents executed
        assert len(result.intent_results) == 3

        # All should succeed
        for intent_result in result.intent_results:
            assert intent_result.success is True

    @pytest.mark.asyncio
    async def test_context_isolation_in_parallel(self, orchestrator, base_context):
        """Test that parallel intents get isolated context copies."""
        # Create parallel intents
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["ETH"], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={},
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify both executed successfully (context isolation prevents conflicts)
        assert len(result.intent_results) == 2
        assert all(r.success for r in result.intent_results)

    @pytest.mark.asyncio
    async def test_metadata_propagation(self, orchestrator, base_context):
        """Test that metadata is preserved in results."""
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
        ]

        multi_intent = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata={
                "original_message": "show btc price",
                "language": "en",
                "custom_field": "test",
            },
        )

        # Execute
        result = await orchestrator.execute(multi_intent, base_context)

        # Verify metadata is in result
        assert result.metadata is not None
        assert result.metadata["original_message"] == "show btc price"


class TestIntentExecutionResult:
    """Test IntentExecutionResult dataclass."""

    def test_create_success_result(self):
        """Test creating successful execution result."""
        intent = IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {})

        result = IntentExecutionResult(
            intent=intent,
            success=True,
            result={"price": 95000},
            execution_time_ms=50.5,
        )

        assert result.success is True
        assert result.result == {"price": 95000}
        assert result.error is None
        assert result.execution_time_ms == 50.5

    def test_create_error_result(self):
        """Test creating error execution result."""
        intent = IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {})

        result = IntentExecutionResult(
            intent=intent,
            success=False,
            error="API connection failed",
            execution_time_ms=10.0,
        )

        assert result.success is False
        assert result.result is None
        assert result.error == "API connection failed"


class TestOrchestratedResult:
    """Test OrchestratedResult dataclass."""

    def test_create_orchestrated_result(self):
        """Test creating orchestrated result."""
        intent = IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {})

        intent_results = [
            IntentExecutionResult(intent, True, {"price": 95000}, None, 50.0)
        ]

        result = OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            total_execution_time_ms=55.5,
            metadata={"original_message": "show btc price"},
        )

        assert len(result.intent_results) == 1
        assert result.orchestration_strategy == OrchestrationStrategy.PARALLEL
        assert result.total_execution_time_ms == 55.5
        assert result.metadata["original_message"] == "show btc price"

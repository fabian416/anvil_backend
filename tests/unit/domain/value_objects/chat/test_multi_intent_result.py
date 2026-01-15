"""Unit tests for MultiIntentResult domain value objects."""

import pytest
from app.domain.value_objects.chat.multi_intent_result import (
    MultiIntentResult,
    OrchestrationStrategy,
    IntentDependency,
)
from app.domain.value_objects.chat.intent_prediction import IntentResult
from app.application.chat.services.intent_detector_v2 import ChatIntentV2


class TestOrchestrationStrategy:
    """Test OrchestrationStrategy enum."""

    def test_orchestration_strategies(self):
        """Test all orchestration strategy values."""
        assert OrchestrationStrategy.PARALLEL == "parallel"
        assert OrchestrationStrategy.SEQUENTIAL == "sequential"
        assert OrchestrationStrategy.CONDITIONAL == "conditional"

    def test_orchestration_strategy_from_string(self):
        """Test creating strategy from string."""
        assert OrchestrationStrategy("parallel") == OrchestrationStrategy.PARALLEL
        assert OrchestrationStrategy("sequential") == OrchestrationStrategy.SEQUENTIAL


class TestIntentDependency:
    """Test IntentDependency value object."""

    def test_create_dependency(self):
        """Test creating a valid dependency."""
        dep = IntentDependency(
            dependent_index=1,
            dependency_index=0,
            dependency_type="data_flow"
        )

        assert dep.dependent_index == 1
        assert dep.dependency_index == 0
        assert dep.dependency_type == "data_flow"

    def test_default_dependency_type(self):
        """Test default dependency type is sequential."""
        dep = IntentDependency(dependent_index=1, dependency_index=0)
        assert dep.dependency_type == "sequential"

    def test_self_dependency_raises_error(self):
        """Test that intent cannot depend on itself."""
        with pytest.raises(ValueError, match="Intent cannot depend on itself"):
            IntentDependency(dependent_index=0, dependency_index=0)

    def test_negative_index_raises_error(self):
        """Test that negative indices are not allowed."""
        with pytest.raises(ValueError, match="Dependency indices must be non-negative"):
            IntentDependency(dependent_index=-1, dependency_index=0)

        with pytest.raises(ValueError, match="Dependency indices must be non-negative"):
            IntentDependency(dependent_index=1, dependency_index=-1)


class TestMultiIntentResult:
    """Test MultiIntentResult value object."""

    @pytest.fixture
    def single_intent_result(self):
        """Create a single intent result for testing."""
        return IntentResult(
            intent=ChatIntentV2.HUNTER_PRICE_PREDICTION,
            confidence=0.95,
            entities=["BTC"],
            metadata={}
        )

    @pytest.fixture
    def multiple_intent_results(self):
        """Create multiple intent results for testing."""
        return [
            IntentResult(
                intent=ChatIntentV2.SWAP,
                confidence=0.95,
                entities=["USDC", "ETH"],
                metadata={}
            ),
            IntentResult(
                intent=ChatIntentV2.BALANCE,
                confidence=0.90,
                entities=[],
                metadata={}
            ),
        ]

    def test_create_single_intent_result(self, single_intent_result):
        """Test creating multi-intent result with single intent."""
        result = MultiIntentResult(
            intents=[single_intent_result],
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )

        assert len(result.intents) == 1
        assert result.is_single_intent is True
        assert result.confidence == 0.95
        assert result.has_dependencies is False

    def test_create_multi_intent_result(self, multiple_intent_results):
        """Test creating multi-intent result with multiple intents."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
        )

        assert len(result.intents) == 2
        assert result.is_single_intent is False
        assert result.confidence == 0.925  # Average of 0.95 and 0.90
        assert result.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL

    def test_confidence_calculation(self, multiple_intent_results):
        """Test that confidence is calculated as average."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )

        expected_confidence = (0.95 + 0.90) / 2
        assert result.confidence == expected_confidence

    def test_empty_intents_raises_error(self):
        """Test that empty intents list raises error."""
        with pytest.raises(ValueError, match="must have at least one intent"):
            MultiIntentResult(
                intents=[],
                orchestration_strategy=OrchestrationStrategy.PARALLEL,
            )

    def test_intent_types_property(self, multiple_intent_results):
        """Test intent_types property returns correct values."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
        )

        assert result.intent_types == ["SWAP", "BALANCE"]

    def test_has_dependencies_property(self, multiple_intent_results):
        """Test has_dependencies property."""
        # Without dependencies
        result_no_deps = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )
        assert result_no_deps.has_dependencies is False

        # With dependencies
        result_with_deps = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0)],
        )
        assert result_with_deps.has_dependencies is True

    def test_independent_intent_indices(self, multiple_intent_results):
        """Test getting independent intent indices."""
        # No dependencies - all independent
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )
        assert result.independent_intent_indices == [0, 1]

        # With dependency - only first is independent
        result_with_dep = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0)],
        )
        assert result_with_dep.independent_intent_indices == [0]

    def test_get_dependencies_for_intent(self, multiple_intent_results):
        """Test getting dependencies for a specific intent."""
        deps = [
            IntentDependency(1, 0, "data_flow"),
            IntentDependency(2, 0, "sequential"),
            IntentDependency(2, 1, "data_flow"),
        ]

        intents = multiple_intent_results + [
            IntentResult(
                intent=ChatIntentV2.PORTFOLIO,
                confidence=0.85,
                entities=[],
                metadata={}
            )
        ]

        result = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=deps,
        )

        # Intent 0 has no dependencies
        assert result.get_dependencies_for_intent(0) == []

        # Intent 1 depends on intent 0
        intent_1_deps = result.get_dependencies_for_intent(1)
        assert len(intent_1_deps) == 1
        assert intent_1_deps[0].dependency_index == 0

        # Intent 2 depends on both 0 and 1
        intent_2_deps = result.get_dependencies_for_intent(2)
        assert len(intent_2_deps) == 2

    def test_can_execute_intent_no_dependencies(self, multiple_intent_results):
        """Test can_execute_intent with no dependencies."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )

        # All intents can execute (no dependencies)
        assert result.can_execute_intent(0, set()) is True
        assert result.can_execute_intent(1, set()) is True

    def test_can_execute_intent_with_dependencies(self, multiple_intent_results):
        """Test can_execute_intent with dependencies."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0)],
        )

        # Intent 0 can always execute (no dependencies)
        assert result.can_execute_intent(0, set()) is True

        # Intent 1 cannot execute without intent 0
        assert result.can_execute_intent(1, set()) is False

        # Intent 1 can execute after intent 0
        assert result.can_execute_intent(1, {0}) is True

    def test_get_execution_order_no_dependencies(self, multiple_intent_results):
        """Test execution order with no dependencies (parallel)."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )

        execution_order = result.get_execution_order()

        # All intents in single batch (parallel execution)
        assert len(execution_order) == 1
        assert execution_order[0] == [0, 1]

    def test_get_execution_order_sequential(self, multiple_intent_results):
        """Test execution order with sequential dependencies."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0)],
        )

        execution_order = result.get_execution_order()

        # Two batches: [0], [1]
        assert len(execution_order) == 2
        assert execution_order[0] == [0]
        assert execution_order[1] == [1]

    def test_get_execution_order_complex(self):
        """Test execution order with complex dependency graph."""
        intents = [
            IntentResult(ChatIntentV2.SWAP, confidence=0.95, entities=["USDC", "ETH"], metadata={}),
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, confidence=0.90, entities=["BTC"], metadata={}),
            IntentResult(ChatIntentV2.HUNTER_SENTIMENT, confidence=0.85, entities=["ETH"], metadata={}),
            IntentResult(ChatIntentV2.BALANCE, confidence=0.90, entities=[], metadata={}),
        ]

        # Dependencies:
        # Intent 3 (BALANCE) depends on Intent 0 (SWAP)
        # Intent 1 and 2 are independent
        deps = [IntentDependency(3, 0)]

        result = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=deps,
        )

        execution_order = result.get_execution_order()

        # Expected: [0, 1, 2] in first batch (0 independent, 1 & 2 independent)
        # Then [3] in second batch (depends on 0)
        assert len(execution_order) == 2
        assert set(execution_order[0]) == {0, 1, 2}  # All independent can run in parallel
        assert execution_order[1] == [3]

    def test_dependency_index_validation(self, single_intent_result):
        """Test that invalid dependency indices raise error."""
        with pytest.raises(ValueError, match="Dependency index out of range"):
            MultiIntentResult(
                intents=[single_intent_result],
                orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
                dependencies=[IntentDependency(1, 0)],  # Index 1 doesn't exist
            )

    def test_to_dict(self, multiple_intent_results):
        """Test conversion to dictionary."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0, "data_flow")],
            metadata={"original_message": "swap and check balance"},
        )

        result_dict = result.to_dict()

        assert result_dict["orchestration_strategy"] == "sequential"
        assert result_dict["is_single_intent"] is False
        assert result_dict["has_dependencies"] is True
        assert result_dict["confidence"] == 0.925
        assert len(result_dict["intents"]) == 2
        assert len(result_dict["dependencies"]) == 1
        assert result_dict["dependencies"][0]["type"] == "data_flow"
        assert result_dict["metadata"]["original_message"] == "swap and check balance"

    def test_repr(self, multiple_intent_results):
        """Test string representation."""
        result = MultiIntentResult(
            intents=multiple_intent_results,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0)],
        )

        repr_str = repr(result)

        assert "MultiIntentResult" in repr_str
        assert "SWAP, BALANCE" in repr_str
        assert "sequential" in repr_str
        assert "dependencies=1" in repr_str
        assert "0.92" in repr_str or "0.93" in repr_str  # Confidence

    def test_metadata_storage(self, single_intent_result):
        """Test that metadata is stored correctly."""
        metadata = {
            "original_message": "show btc price",
            "segments": ["show btc price"],
            "detection_time_ms": 50,
        }

        result = MultiIntentResult(
            intents=[single_intent_result],
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
            metadata=metadata,
        )

        assert result.metadata == metadata
        assert result.metadata["original_message"] == "show btc price"
        assert result.metadata["detection_time_ms"] == 50


class TestMultiIntentResultIntegration:
    """Integration tests for multi-intent scenarios."""

    def test_parallel_independent_intents(self):
        """Test parallel execution of independent intents."""
        # User: "show btc price and eth sentiment"
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.95, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_SENTIMENT, 0.90, ["ETH"], {}),
        ]

        result = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.PARALLEL,
        )

        assert result.orchestration_strategy == OrchestrationStrategy.PARALLEL
        assert result.has_dependencies is False
        assert result.get_execution_order() == [[0, 1]]  # Execute in parallel

    def test_sequential_dependent_intents(self):
        """Test sequential execution of dependent intents."""
        # User: "swap 100 usdc to eth and show my balance"
        intents = [
            IntentResult(ChatIntentV2.SWAP, 0.95, ["USDC", "ETH"], {}),
            IntentResult(ChatIntentV2.BALANCE, 0.90, [], {}),
        ]

        result = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=[IntentDependency(1, 0, "data_flow")],
        )

        assert result.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL
        assert result.has_dependencies is True
        assert result.get_execution_order() == [[0], [1]]  # Execute sequentially

    def test_conditional_intent(self):
        """Test conditional intent execution."""
        # User: "buy bitcoin if price drops below 90k"
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.90, ["BTC"], {}),
            IntentResult(ChatIntentV2.BUY, 0.85, ["BTC"], {}),
        ]

        result = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.CONDITIONAL,
            dependencies=[IntentDependency(1, 0, "conditional")],
        )

        assert result.orchestration_strategy == OrchestrationStrategy.CONDITIONAL
        assert result.dependencies[0].dependency_type == "conditional"

    def test_mixed_parallel_sequential(self):
        """Test mixed parallel and sequential execution."""
        # User: "show btc price, eth sentiment, swap usdc to eth, and check balance"
        # BTC price and ETH sentiment can run in parallel
        # SWAP must run before BALANCE
        intents = [
            IntentResult(ChatIntentV2.HUNTER_PRICE_PREDICTION, 0.95, ["BTC"], {}),
            IntentResult(ChatIntentV2.HUNTER_SENTIMENT, 0.90, ["ETH"], {}),
            IntentResult(ChatIntentV2.SWAP, 0.95, ["USDC", "ETH"], {}),
            IntentResult(ChatIntentV2.BALANCE, 0.90, [], {}),
        ]

        deps = [IntentDependency(3, 2, "data_flow")]

        result = MultiIntentResult(
            intents=intents,
            orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
            dependencies=deps,
        )

        execution_order = result.get_execution_order()

        # First batch: 0, 1, 2 (all independent)
        # Second batch: 3 (depends on 2)
        assert len(execution_order) == 2
        assert set(execution_order[0]) == {0, 1, 2}
        assert execution_order[1] == [3]

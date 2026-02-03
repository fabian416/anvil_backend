"""Multi-Intent Detection Value Objects.

This module defines value objects for multi-intent detection results,
enabling the system to handle multiple intents in a single user message.

Example:
    User: "swap 100 usdc to eth and show me my new balance"

    MultiIntentResult(
        intents=[
            IntentResult(SWAP, confidence=0.95, entities=[USDC, ETH]),
            IntentResult(BALANCE, confidence=0.90, entities=[])
        ],
        orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
        dependencies=[IntentDependency(dependent_index=1, dependency_index=0)],
    )
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

from .intent_prediction import IntentResult


class OrchestrationStrategy(str, Enum):
    """
    Strategy for executing multiple intents.

    Attributes:
        PARALLEL: Independent intents that can run concurrently.
            Example: "show btc price and eth sentiment"

        SEQUENTIAL: Dependent intents that must run in order.
            Example: "swap 100 usdc to eth and show my balance"
            (balance depends on swap completing first)

        CONDITIONAL: Intents with if-then logic.
            Example: "buy bitcoin if price drops below 90k"
            (buy only executes if condition is true)
    """

    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"


@dataclass
class IntentDependency:
    """
    Represents a dependency relationship between two intents.

    Attributes:
        dependent_index: Index of the intent that depends on another
        dependency_index: Index of the intent it depends on
        dependency_type: Type of dependency (sequential, data_flow, conditional)

    Example:
        IntentDependency(
            dependent_index=1,  # BALANCE intent
            dependency_index=0,  # Depends on SWAP intent
            dependency_type="data_flow"  # BALANCE needs swap result
        )
    """

    dependent_index: int
    dependency_index: int
    dependency_type: str = "sequential"  # sequential, data_flow, conditional

    def __post_init__(self):
        """Validate dependency indices."""
        if self.dependent_index == self.dependency_index:
            raise ValueError("Intent cannot depend on itself")
        if self.dependent_index < 0 or self.dependency_index < 0:
            raise ValueError("Dependency indices must be non-negative")


@dataclass
class MultiIntentResult:
    """
    Result of detecting multiple intents in a single user message.

    This value object encapsulates:
    - The detected intents (one or more)
    - How they should be orchestrated (parallel, sequential, conditional)
    - Dependencies between intents
    - Overall confidence score
    - Metadata about the detection process

    Attributes:
        intents: List of detected intents (minimum 1)
        orchestration_strategy: How to execute the intents
        dependencies: List of dependencies between intents
        confidence: Overall confidence score (0.0-1.0)
        metadata: Additional detection metadata

    Properties:
        is_single_intent: True if only one intent detected
        intent_types: List of intent type strings
        has_dependencies: True if any dependencies exist
        independent_intent_indices: Indices of intents with no dependencies

    Example:
        >>> multi_intent = MultiIntentResult(
        ...     intents=[
        ...         IntentResult(SWAP, confidence=0.95),
        ...         IntentResult(BALANCE, confidence=0.90)
        ...     ],
        ...     orchestration_strategy=OrchestrationStrategy.SEQUENTIAL,
        ...     dependencies=[IntentDependency(1, 0, "data_flow")]
        ... )
        >>> multi_intent.confidence
        0.925
        >>> multi_intent.is_single_intent
        False
        >>> multi_intent.has_dependencies
        True
    """

    intents: List[IntentResult]
    orchestration_strategy: OrchestrationStrategy
    dependencies: List[IntentDependency] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Validate and initialize multi-intent result.

        - Ensures at least one intent is present
        - Calculates overall confidence as average
        - Validates dependency indices
        """
        if not self.intents:
            raise ValueError("MultiIntentResult must have at least one intent")

        # Calculate overall confidence as average of intent confidences
        if self.intents:
            self.confidence = sum(intent.confidence for intent in self.intents) / len(
                self.intents
            )

        # Validate dependency indices
        max_index = len(self.intents) - 1
        for dep in self.dependencies:
            if dep.dependent_index > max_index or dep.dependency_index > max_index:
                raise ValueError(
                    f"Dependency index out of range. "
                    f"Max index: {max_index}, "
                    f"Dependency: {dep.dependent_index} -> {dep.dependency_index}"
                )

    @property
    def is_single_intent(self) -> bool:
        """
        Check if this is effectively a single intent.

        Returns:
            True if only one intent detected (optimization path)
        """
        return len(self.intents) == 1

    @property
    def intent_types(self) -> List[str]:
        """
        Get list of intent type strings.

        Returns:
            List of intent type values (e.g., ["SWAP", "BALANCE"])
        """
        return [intent.intent.value for intent in self.intents]

    @property
    def has_dependencies(self) -> bool:
        """
        Check if any dependencies exist between intents.

        Returns:
            True if dependencies list is not empty
        """
        return len(self.dependencies) > 0

    @property
    def independent_intent_indices(self) -> List[int]:
        """
        Get indices of intents that have no dependencies.

        These intents can be executed first or in parallel.

        Returns:
            List of indices for independent intents

        Example:
            >>> # Intent 0: SWAP (no dependencies)
            >>> # Intent 1: BALANCE (depends on 0)
            >>> multi_intent.independent_intent_indices
            [0]
        """
        dependent_indices = {dep.dependent_index for dep in self.dependencies}
        return [i for i in range(len(self.intents)) if i not in dependent_indices]

    def get_dependencies_for_intent(self, intent_index: int) -> List[IntentDependency]:
        """
        Get all dependencies for a specific intent.

        Args:
            intent_index: Index of the intent to check

        Returns:
            List of dependencies where this intent is the dependent

        Example:
            >>> multi_intent.get_dependencies_for_intent(1)
            [IntentDependency(dependent_index=1, dependency_index=0)]
        """
        return [dep for dep in self.dependencies if dep.dependent_index == intent_index]

    def can_execute_intent(self, intent_index: int, executed_indices: set[int]) -> bool:
        """
        Check if an intent can be executed based on its dependencies.

        An intent can execute if all its dependencies have been executed.

        Args:
            intent_index: Index of intent to check
            executed_indices: Set of already executed intent indices

        Returns:
            True if all dependencies are satisfied

        Example:
            >>> # Intent 1 depends on Intent 0
            >>> multi_intent.can_execute_intent(1, {0})
            True
            >>> multi_intent.can_execute_intent(1, set())
            False
        """
        intent_deps = self.get_dependencies_for_intent(intent_index)

        if not intent_deps:
            # No dependencies, can always execute
            return True

        # Check if all dependencies have been executed
        for dep in intent_deps:
            if dep.dependency_index not in executed_indices:
                return False

        return True

    def get_execution_order(self) -> List[List[int]]:
        """
        Get execution order for intents based on dependencies.

        Returns list of batches where each batch contains intent indices
        that can be executed in parallel.

        Returns:
            List of batches (list of intent indices per batch)

        Example:
            >>> # Intent 0: independent
            >>> # Intent 1: depends on 0
            >>> # Intent 2: depends on 0
            >>> # Intent 3: depends on 1 and 2
            >>> multi_intent.get_execution_order()
            [[0], [1, 2], [3]]
        """
        if self.is_single_intent:
            return [[0]]

        if not self.has_dependencies:
            # All independent, can execute in parallel
            return [list(range(len(self.intents)))]

        # Build execution order using topological sort
        batches = []
        executed = set()
        remaining = set(range(len(self.intents)))

        while remaining:
            # Find intents that can execute in this batch
            batch = []
            for intent_index in remaining:
                if self.can_execute_intent(intent_index, executed):
                    batch.append(intent_index)

            if not batch:
                # Circular dependency detected (shouldn't happen with proper validation)
                raise ValueError("Circular dependency detected in intent graph")

            batches.append(batch)
            executed.update(batch)
            remaining.difference_update(batch)

        return batches

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of multi-intent result
        """
        return {
            "intents": [
                {
                    "intent": intent.intent.value,
                    "confidence": intent.confidence,
                    "entities": intent.entities,
                }
                for intent in self.intents
            ],
            "orchestration_strategy": self.orchestration_strategy.value,
            "dependencies": [
                {
                    "dependent": dep.dependent_index,
                    "dependency": dep.dependency_index,
                    "type": dep.dependency_type,
                }
                for dep in self.dependencies
            ],
            "confidence": self.confidence,
            "is_single_intent": self.is_single_intent,
            "has_dependencies": self.has_dependencies,
            "execution_order": self.get_execution_order(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        intent_types_str = ", ".join(self.intent_types)
        return (
            f"MultiIntentResult("
            f"intents=[{intent_types_str}], "
            f"strategy={self.orchestration_strategy.value}, "
            f"dependencies={len(self.dependencies)}, "
            f"confidence={self.confidence:.2f})"
        )

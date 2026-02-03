"""
Intent Orchestrator for Multi-Intent Execution.

This module implements the orchestration layer for executing multiple intents
detected in a single user message. It handles parallel, sequential, and
conditional execution strategies based on intent dependencies.

Architecture:
    User Message → IntentDetectorV2 → MultiIntentResult → IntentOrchestrator → Results

Features:
    - Parallel execution using asyncio.gather() for independent intents
    - Sequential execution with dependency-aware batching
    - Context propagation between dependent intents (copy-on-write)
    - Conditional execution with result-based branching
    - Error handling and partial failure recovery

Example:
    >>> orchestrator = IntentOrchestrator(handler_registry)
    >>> multi_intent = detector.detect_multi_intent("show btc eth prices")
    >>> results = await orchestrator.execute(multi_intent, context)
    >>> # Returns: [BTC price result, ETH price result]
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.domain.value_objects.chat.multi_intent_result import (
    MultiIntentResult,
    OrchestrationStrategy,
)
from app.domain.value_objects.chat.intent_prediction import IntentResult

logger = logging.getLogger(__name__)


@dataclass
class IntentExecutionResult:
    """
    Result of executing a single intent.

    Attributes:
        intent: The intent that was executed
        success: Whether execution was successful
        result: The execution result (response, data, etc.)
        error: Error message if execution failed
        execution_time_ms: Time taken to execute (milliseconds)
    """

    intent: IntentResult
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class OrchestratedResult:
    """
    Aggregated result of orchestrated multi-intent execution.

    Attributes:
        intent_results: List of individual intent execution results
        orchestration_strategy: Strategy used for execution
        total_execution_time_ms: Total time for all intents
        metadata: Additional orchestration metadata
    """

    intent_results: List[IntentExecutionResult]
    orchestration_strategy: OrchestrationStrategy
    total_execution_time_ms: float
    metadata: Dict[str, Any]


class IntentOrchestrator:
    """
    Orchestrates execution of multiple intents based on dependencies.

    This orchestrator implements three execution strategies:

    1. PARALLEL: Execute independent intents concurrently
       - Uses asyncio.gather() for maximum throughput
       - Example: "show btc eth ada prices" → 3 parallel PRICE requests

    2. SEQUENTIAL: Execute intents in dependency order
       - Batches independent intents within each level
       - Propagates context between dependent intents
       - Example: "swap and balance" → swap first, then balance with swap result

    3. CONDITIONAL: Execute with condition checking
       - Executes first intent, evaluates condition, then executes second
       - Example: "buy if price drops" → check price, then conditionally buy

    The orchestrator uses a handler registry to map intents to their handlers
    and manages context propagation for dependent intents.
    """

    def __init__(self, handler_registry: Optional[Dict[str, Any]] = None):
        """
        Initialize intent orchestrator.

        Args:
            handler_registry: Map of handler names to handler instances
                              If None, will be injected via dependency injection
        """
        self.handler_registry = handler_registry or {}
        logger.info("IntentOrchestrator initialized")

    async def execute(
        self,
        multi_intent: MultiIntentResult,
        context: Dict[str, Any],
    ) -> OrchestratedResult:
        """
        Execute multiple intents based on orchestration strategy.

        This is the main entry point for multi-intent execution. It delegates
        to strategy-specific execution methods based on the orchestration strategy.

        Args:
            multi_intent: MultiIntentResult from IntentDetectorV2
            context: Execution context (conversation, user, etc.)

        Returns:
            OrchestratedResult with all intent execution results

        Example:
            >>> result = await orchestrator.execute(multi_intent, context)
            >>> for intent_result in result.intent_results:
            ...     print(f"Intent: {intent_result.intent.intent.value}")
            ...     print(f"Success: {intent_result.success}")
            ...     print(f"Result: {intent_result.result}")
        """
        import time

        start_time = time.time()

        logger.info(
            f"🎭 Orchestrating {len(multi_intent.intents)} intents with strategy: {multi_intent.orchestration_strategy.value}"
        )

        # Execute based on strategy
        if multi_intent.orchestration_strategy == OrchestrationStrategy.PARALLEL:
            intent_results = await self._execute_parallel(multi_intent, context)
        elif multi_intent.orchestration_strategy == OrchestrationStrategy.SEQUENTIAL:
            intent_results = await self._execute_sequential(multi_intent, context)
        elif multi_intent.orchestration_strategy == OrchestrationStrategy.CONDITIONAL:
            intent_results = await self._execute_conditional(multi_intent, context)
        else:
            raise ValueError(
                f"Unknown orchestration strategy: {multi_intent.orchestration_strategy}"
            )

        total_time = (time.time() - start_time) * 1000

        logger.info(
            f"✅ Orchestration complete: {len(intent_results)} intents executed in {total_time:.2f}ms"
        )

        return OrchestratedResult(
            intent_results=intent_results,
            orchestration_strategy=multi_intent.orchestration_strategy,
            total_execution_time_ms=total_time,
            metadata={
                "original_message": multi_intent.metadata.get("original_message", ""),
                "execution_batches": len(multi_intent.get_execution_order()),
            },
        )

    async def _execute_parallel(
        self,
        multi_intent: MultiIntentResult,
        context: Dict[str, Any],
    ) -> List[IntentExecutionResult]:
        """
        Execute all intents in parallel using asyncio.gather().

        This strategy maximizes throughput by executing all intents concurrently.
        Each intent executes with a copy of the context to prevent race conditions.

        Args:
            multi_intent: MultiIntentResult with independent intents
            context: Base execution context

        Returns:
            List of intent execution results
        """
        logger.info(f"⚡ Executing {len(multi_intent.intents)} intents in parallel")

        # Create tasks for all intents
        tasks = []
        for intent in multi_intent.intents:
            # Each intent gets a copy of context (immutable pattern)
            intent_context = context.copy()
            task = self._execute_single_intent(intent, intent_context)
            tasks.append(task)

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        intent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                intent_results.append(
                    IntentExecutionResult(
                        intent=multi_intent.intents[i],
                        success=False,
                        error=str(result),
                    )
                )
            else:
                intent_results.append(result)

        return intent_results

    async def _execute_sequential(
        self,
        multi_intent: MultiIntentResult,
        context: Dict[str, Any],
    ) -> List[IntentExecutionResult]:
        """
        Execute intents in dependency order with context propagation.

        This strategy executes intents in batches based on the dependency graph.
        Within each batch, intents execute in parallel. Between batches, context
        is propagated from completed intents to dependent intents.

        Args:
            multi_intent: MultiIntentResult with dependencies
            context: Base execution context

        Returns:
            List of intent execution results in execution order
        """
        execution_order = multi_intent.get_execution_order()
        logger.info(
            f"🔗 Executing {len(multi_intent.intents)} intents in {len(execution_order)} batches"
        )

        all_results = [None] * len(multi_intent.intents)  # Track by index
        current_context = context.copy()

        # Execute each batch
        for batch_num, batch_indices in enumerate(execution_order):
            logger.info(f"  Batch {batch_num + 1}: Executing intents {batch_indices}")

            # Execute batch in parallel
            batch_tasks = []
            for intent_index in batch_indices:
                intent = multi_intent.intents[intent_index]
                # Use current context (which may include results from previous batches)
                task = self._execute_single_intent(intent, current_context.copy())
                batch_tasks.append((intent_index, task))

            # Wait for batch to complete
            batch_results = await asyncio.gather(
                *[task for _, task in batch_tasks], return_exceptions=True
            )

            # Store results and update context
            for (intent_index, _), result in zip(batch_tasks, batch_results):
                if isinstance(result, Exception):
                    all_results[intent_index] = IntentExecutionResult(
                        intent=multi_intent.intents[intent_index],
                        success=False,
                        error=str(result),
                    )
                else:
                    all_results[intent_index] = result

                    # Propagate successful results to context for dependent intents
                    if result.success:
                        current_context[f"intent_{intent_index}_result"] = result.result

        return all_results

    async def _execute_conditional(
        self,
        multi_intent: MultiIntentResult,
        context: Dict[str, Any],
    ) -> List[IntentExecutionResult]:
        """
        Execute intents with conditional branching.

        This strategy executes the first intent (condition), evaluates the result,
        and then conditionally executes the second intent based on the condition.

        Args:
            multi_intent: MultiIntentResult with conditional dependency
            context: Base execution context

        Returns:
            List of intent execution results
        """
        logger.info(f"🔀 Executing conditional intents")

        results = []

        # Execute first intent (condition)
        condition_intent = multi_intent.intents[0]
        condition_result = await self._execute_single_intent(
            condition_intent, context.copy()
        )
        results.append(condition_result)

        # Evaluate condition
        if condition_result.success:
            condition_met = self._evaluate_condition(condition_result, multi_intent)

            if condition_met:
                logger.info("  ✅ Condition met, executing dependent intent")
                # Execute second intent with condition result in context
                dependent_context = context.copy()
                dependent_context["condition_result"] = condition_result.result

                dependent_intent = multi_intent.intents[1]
                dependent_result = await self._execute_single_intent(
                    dependent_intent, dependent_context
                )
                results.append(dependent_result)
            else:
                logger.info("  ❌ Condition not met, skipping dependent intent")
                results.append(
                    IntentExecutionResult(
                        intent=multi_intent.intents[1],
                        success=True,
                        result={"skipped": True, "reason": "condition_not_met"},
                    )
                )
        else:
            logger.warning("  ⚠️ Condition intent failed, skipping dependent intent")
            results.append(
                IntentExecutionResult(
                    intent=multi_intent.intents[1],
                    success=False,
                    error="Condition intent failed",
                )
            )

        return results

    async def _execute_single_intent(
        self,
        intent: IntentResult,
        context: Dict[str, Any],
    ) -> IntentExecutionResult:
        """
        Execute a single intent using the appropriate handler.

        This method looks up the handler for the intent, executes it with the
        provided context, and returns an IntentExecutionResult.

        Args:
            intent: Intent to execute
            context: Execution context

        Returns:
            IntentExecutionResult with execution outcome
        """
        import time

        start_time = time.time()

        try:
            logger.debug(
                f"  Executing intent: {intent.intent.value} (confidence: {intent.confidence:.2f})"
            )

            # Get handler from registry (placeholder for now)
            # In actual implementation, this would look up and invoke the real handler
            handler_name = f"{intent.intent.value.lower()}_handler"

            # Simulate handler execution for now
            # TODO: Replace with actual handler invocation in Day 3
            result = await self._simulate_handler_execution(intent, context)

            execution_time = (time.time() - start_time) * 1000

            return IntentExecutionResult(
                intent=intent,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"  ❌ Intent execution failed: {e}", exc_info=True)

            return IntentExecutionResult(
                intent=intent,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def _simulate_handler_execution(
        self,
        intent: IntentResult,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Simulate handler execution for testing.

        TODO: Replace with actual handler invocation in Day 3 (DI wiring).

        Args:
            intent: Intent to execute
            context: Execution context

        Returns:
            Simulated handler result
        """
        # Simulate some async work
        await asyncio.sleep(0.01)

        return {
            "intent": intent.intent.value,
            "entities": intent.entities,
            "confidence": intent.confidence,
            "simulated": True,
            "message": f"Successfully executed {intent.intent.value}",
        }

    def _evaluate_condition(
        self,
        condition_result: IntentExecutionResult,
        multi_intent: MultiIntentResult,
    ) -> bool:
        """
        Evaluate whether a conditional intent's condition is met.

        This is a placeholder implementation that always returns True.
        In a real implementation, this would check the condition based on
        the result type and expected condition.

        Args:
            condition_result: Result of the condition intent
            multi_intent: Full multi-intent result with metadata

        Returns:
            True if condition is met, False otherwise
        """
        # TODO: Implement actual condition evaluation based on intent type
        # For now, return True if the condition intent succeeded
        return condition_result.success

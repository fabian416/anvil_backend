"""
Multi-Intent Response Formatter.

This module formats the results of multi-intent execution into unified,
user-friendly responses. It handles aggregation, formatting, and presentation
of multiple intent results based on the orchestration strategy used.

Architecture:
    IntentOrchestrator → OrchestratedResult → MultiIntentResponseFormatter → Unified Response

Features:
    - Parallel response aggregation (e.g., "BTC: $95k, ETH: $3.5k, ADA: $0.50")
    - Sequential response chaining (e.g., "Swap completed. New balance: 100 ETH")
    - Conditional response formatting (e.g., "Price is above threshold. Skipping buy.")
    - Error handling and partial success messaging
    - Multi-language support

Example:
    >>> formatter = MultiIntentResponseFormatter()
    >>> response = formatter.format(orchestrated_result, language="en")
    >>> print(response.message)
    "BTC: $95,000 | ETH: $3,500"
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.application.chat.services.intent_orchestrator import (
    OrchestratedResult,
    IntentExecutionResult,
)
from app.domain.value_objects.chat.multi_intent_result import OrchestrationStrategy

logger = logging.getLogger(__name__)


@dataclass
class FormattedResponse:
    """
    Formatted response for multi-intent execution.

    Attributes:
        message: User-facing response message
        data: Structured data from all intent results
        success: Overall success status
        partial_success: True if some intents succeeded and some failed
        metadata: Additional formatting metadata
    """

    message: str
    data: Dict[str, Any]
    success: bool
    partial_success: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MultiIntentResponseFormatter:
    """
    Formats multi-intent execution results into unified responses.

    This formatter implements strategy-specific formatting:

    1. PARALLEL: Aggregate independent results
       - Example: "BTC: $95k, ETH: $3.5k" (multiple prices)
       - Uses separators and compact formatting

    2. SEQUENTIAL: Chain dependent results
       - Example: "Swap completed. New balance: 100 ETH"
       - Shows workflow progression

    3. CONDITIONAL: Show condition and result
       - Example: "Price is $95k. Condition not met, skipping buy."
       - Explains conditional branching
    """

    def __init__(self):
        """Initialize response formatter."""
        logger.info("MultiIntentResponseFormatter initialized")

    def format(
        self,
        orchestrated_result: OrchestratedResult,
        language: str = "en",
    ) -> FormattedResponse:
        """
        Format orchestrated result into user-friendly response.

        Args:
            orchestrated_result: Result from IntentOrchestrator
            language: Language code for response formatting

        Returns:
            FormattedResponse with formatted message and data

        Example:
            >>> result = formatter.format(orchestrated_result, "en")
            >>> print(result.message)
        """
        logger.info(
            f"📝 Formatting {len(orchestrated_result.intent_results)} intent results "
            f"with strategy: {orchestrated_result.orchestration_strategy.value}"
        )

        # Format based on strategy
        if orchestrated_result.orchestration_strategy == OrchestrationStrategy.PARALLEL:
            return self._format_parallel(orchestrated_result, language)
        elif (
            orchestrated_result.orchestration_strategy
            == OrchestrationStrategy.SEQUENTIAL
        ):
            return self._format_sequential(orchestrated_result, language)
        elif (
            orchestrated_result.orchestration_strategy
            == OrchestrationStrategy.CONDITIONAL
        ):
            return self._format_conditional(orchestrated_result, language)
        else:
            # Fallback to simple formatting
            return self._format_simple(orchestrated_result, language)

    def _format_parallel(
        self,
        orchestrated_result: OrchestratedResult,
        language: str,
    ) -> FormattedResponse:
        """
        Format parallel execution results.

        Aggregates independent results with separators.

        Example:
            Input: [BTC price result, ETH price result, ADA price result]
            Output: "BTC: $95,000 | ETH: $3,500 | ADA: $0.50"
        """
        intent_results = orchestrated_result.intent_results
        successful_results = [r for r in intent_results if r.success]
        failed_results = [r for r in intent_results if not r.success]

        # Check if all succeeded
        all_success = len(failed_results) == 0
        partial_success = len(successful_results) > 0 and len(failed_results) > 0

        # Format each result
        formatted_parts = []
        aggregated_data = {}

        for i, result in enumerate(successful_results):
            formatted_part = self._format_single_result(result, language)
            formatted_parts.append(formatted_part["message"])
            aggregated_data[f"result_{i}"] = formatted_part["data"]

        # Join with separator based on language
        separator = " | " if language == "en" else " | "
        message = separator.join(formatted_parts)

        # Add error message if partial failure
        if partial_success:
            error_count = len(failed_results)
            if language == "es":
                message += f"\n\n⚠️ {error_count} resultado(s) fallaron"
            elif language == "pt":
                message += f"\n\n⚠️ {error_count} resultado(s) falharam"
            else:
                message += f"\n\n⚠️ {error_count} result(s) failed"

        return FormattedResponse(
            message=message,
            data=aggregated_data,
            success=all_success,
            partial_success=partial_success,
            metadata={
                "strategy": "parallel",
                "total_results": len(intent_results),
                "successful_results": len(successful_results),
            },
        )

    def _format_sequential(
        self,
        orchestrated_result: OrchestratedResult,
        language: str,
    ) -> FormattedResponse:
        """
        Format sequential execution results.

        Shows workflow progression with context.

        Example:
            Input: [SWAP result, BALANCE result]
            Output: "✅ Swap completed: 100 USDC → 0.03 ETH\n💰 New balance: 0.03 ETH"
        """
        intent_results = orchestrated_result.intent_results

        # Format each step
        formatted_steps = []
        aggregated_data = {}
        all_success = True

        for i, result in enumerate(intent_results):
            if result.success:
                formatted_step = self._format_single_result(result, language)
                formatted_steps.append(formatted_step["message"])
                aggregated_data[f"step_{i}"] = formatted_step["data"]
            else:
                all_success = False
                # Add error message
                intent_name = result.intent.intent.value
                if language == "es":
                    error_msg = (
                        f"❌ Error en {intent_name}: {result.error or 'Unknown error'}"
                    )
                elif language == "pt":
                    error_msg = f"❌ Erro em {intent_name}: {result.error or 'Erro desconhecido'}"
                else:
                    error_msg = (
                        f"❌ Error in {intent_name}: {result.error or 'Unknown error'}"
                    )
                formatted_steps.append(error_msg)

        # Join steps with newlines
        message = "\n\n".join(formatted_steps)

        return FormattedResponse(
            message=message,
            data=aggregated_data,
            success=all_success,
            partial_success=False,
            metadata={
                "strategy": "sequential",
                "total_steps": len(intent_results),
            },
        )

    def _format_conditional(
        self,
        orchestrated_result: OrchestratedResult,
        language: str,
    ) -> FormattedResponse:
        """
        Format conditional execution results.

        Shows condition evaluation and outcome.

        Example:
            Input: [PRICE result (condition), BUY result (skipped)]
            Output: "BTC price: $95,000\n⏭️ Price above threshold. Buy order skipped."
        """
        intent_results = orchestrated_result.intent_results

        if len(intent_results) < 2:
            # Fallback for invalid conditional
            return self._format_simple(orchestrated_result, language)

        # Format condition result
        condition_result = intent_results[0]
        dependent_result = intent_results[1]

        formatted_parts = []
        aggregated_data = {}

        # Condition
        if condition_result.success:
            condition_formatted = self._format_single_result(condition_result, language)
            formatted_parts.append(condition_formatted["message"])
            aggregated_data["condition"] = condition_formatted["data"]
        else:
            if language == "es":
                formatted_parts.append(
                    f"❌ Error verificando condición: {condition_result.error}"
                )
            elif language == "pt":
                formatted_parts.append(
                    f"❌ Erro verificando condição: {condition_result.error}"
                )
            else:
                formatted_parts.append(
                    f"❌ Error checking condition: {condition_result.error}"
                )

        # Dependent result
        if dependent_result.success:
            # Check if skipped
            if isinstance(
                dependent_result.result, dict
            ) and dependent_result.result.get("skipped"):
                if language == "es":
                    formatted_parts.append("⏭️ Condición no cumplida. Acción omitida.")
                elif language == "pt":
                    formatted_parts.append("⏭️ Condição não atendida. Ação ignorada.")
                else:
                    formatted_parts.append("⏭️ Condition not met. Action skipped.")
            else:
                dependent_formatted = self._format_single_result(
                    dependent_result, language
                )
                formatted_parts.append(dependent_formatted["message"])
                aggregated_data["action"] = dependent_formatted["data"]
        else:
            if language == "es":
                formatted_parts.append(
                    f"❌ Error ejecutando acción: {dependent_result.error}"
                )
            elif language == "pt":
                formatted_parts.append(
                    f"❌ Erro executando ação: {dependent_result.error}"
                )
            else:
                formatted_parts.append(
                    f"❌ Error executing action: {dependent_result.error}"
                )

        message = "\n\n".join(formatted_parts)

        return FormattedResponse(
            message=message,
            data=aggregated_data,
            success=condition_result.success,
            partial_success=False,
            metadata={"strategy": "conditional"},
        )

    def _format_simple(
        self,
        orchestrated_result: OrchestratedResult,
        language: str,
    ) -> FormattedResponse:
        """
        Simple fallback formatting for single intent or unknown strategy.

        Args:
            orchestrated_result: Orchestrated result
            language: Language code

        Returns:
            Simple formatted response
        """
        if len(orchestrated_result.intent_results) == 1:
            result = orchestrated_result.intent_results[0]
            if result.success:
                formatted = self._format_single_result(result, language)
                return FormattedResponse(
                    message=formatted["message"],
                    data=formatted["data"],
                    success=True,
                    metadata={"strategy": "simple"},
                )
            else:
                return FormattedResponse(
                    message=f"❌ Error: {result.error}",
                    data={},
                    success=False,
                    metadata={"strategy": "simple"},
                )

        # Multiple results, simple concatenation
        messages = []
        data = {}
        for i, result in enumerate(orchestrated_result.intent_results):
            if result.success:
                formatted = self._format_single_result(result, language)
                messages.append(formatted["message"])
                data[f"result_{i}"] = formatted["data"]

        return FormattedResponse(
            message="\n\n".join(messages),
            data=data,
            success=all(r.success for r in orchestrated_result.intent_results),
            metadata={"strategy": "simple"},
        )

    def _format_single_result(
        self,
        result: IntentExecutionResult,
        language: str,
    ) -> Dict[str, Any]:
        """
        Format a single intent execution result.

        Args:
            result: Single intent execution result
            language: Language code

        Returns:
            Dictionary with formatted message and data
        """
        intent_type = result.intent.intent.value
        entities = result.intent.entities
        result_data = result.result or {}

        # Format based on intent type (placeholder implementation)
        # In real implementation, this would use intent-specific formatters

        if "PRICE" in intent_type:
            entity = entities[0] if entities else "Token"
            # Simulated result formatting
            message = (
                f"{entity}: $95,000"
                if result_data.get("simulated")
                else str(result_data)
            )
            return {"message": message, "data": result_data}

        elif "SENTIMENT" in intent_type:
            entity = entities[0] if entities else "Token"
            message = f"{entity} sentiment: Bullish 📈"
            return {"message": message, "data": result_data}

        elif intent_type == "SWAP":
            message = "✅ Swap completed successfully"
            return {"message": message, "data": result_data}

        elif intent_type == "BALANCE":
            message = "💰 Balance retrieved successfully"
            return {"message": message, "data": result_data}

        else:
            # Generic formatting
            message = f"✅ {intent_type} completed"
            return {"message": message, "data": result_data}

"""
LLM Test Validator - AI-powered semantic validation for integration tests.

Uses DeepInfra (Meta Llama 3.1 70B) to validate test responses beyond assertion-based testing.
Provides semantic understanding of agent responses, multi-step conversation context, and
intelligent error analysis.

Cost: ~$0.08/1M tokens via DeepInfra (99% cheaper than OpenAI)
Performance: +2-3 seconds per test validation
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import (
    LLMClientDeepInfra,
)

logger = logging.getLogger(__name__)


class ValidationVerdict(str, Enum):
    """Test validation verdict."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"


@dataclass
class ValidationResult:
    """Result from LLM test validation."""

    verdict: ValidationVerdict
    confidence: float  # 0.0 - 1.0
    reasoning: str
    semantic_issues: list[str]
    tokens_used: int
    validation_time_ms: int
    timestamp: datetime


@dataclass
class MultiStepValidationResult:
    """Result from multi-step conversation validation."""

    verdict: ValidationVerdict
    confidence: float
    reasoning: str
    step_validations: list[ValidationResult]
    context_consistency_score: float  # 0.0 - 1.0
    tokens_used: int
    validation_time_ms: int


class LLMTestValidator:
    """
    AI-powered test validator using DeepInfra.

    Provides semantic validation of test responses:
    - Understands context and intent
    - Validates multi-step conversation flows
    - Identifies subtle semantic errors that assertions miss
    - Provides confidence scores and reasoning

    Environment Variables:
        ENABLE_LLM_VALIDATION: "true" to enable (default: "false")
        DEEPINFRA_API_KEY: DeepInfra API key (required if enabled)

    Usage:
        validator = LLMTestValidator()
        result = await validator.validate_single_response(
            test_name="test_guest_chat_bitcoin_query",
            user_input="What is Bitcoin?",
            agent_output="Bitcoin is a decentralized cryptocurrency...",
            expected_behavior="Should provide accurate Bitcoin information"
        )
        assert result.verdict == ValidationVerdict.PASS
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct",
        enabled: Optional[bool] = None,
    ):
        """
        Initialize LLM test validator.

        Args:
            api_key: DeepInfra API key (defaults to DEEPINFRA_API_KEY env var)
            model: DeepInfra model to use for validation
            enabled: Whether to enable validation (defaults to ENABLE_LLM_VALIDATION env var)
        """
        # Check if LLM validation is enabled
        self._enabled = enabled if enabled is not None else os.getenv("ENABLE_LLM_VALIDATION", "false").lower() == "true"

        if not self._enabled:
            logger.info("LLM test validation is DISABLED (set ENABLE_LLM_VALIDATION=true to enable)")
            self._client = None
            return

        # Get API key
        api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            logger.warning(
                "DEEPINFRA_API_KEY not set - LLM validation will be skipped. "
                "Set DEEPINFRA_API_KEY environment variable to enable."
            )
            self._enabled = False
            self._client = None
            return

        # Initialize DeepInfra client
        self._client = LLMClientDeepInfra(api_key=api_key)
        self._model = model
        logger.info(f"LLM test validator initialized with model={model}")

    @property
    def enabled(self) -> bool:
        """Check if LLM validation is enabled."""
        return self._enabled

    async def validate_single_response(
        self,
        test_name: str,
        user_input: str,
        agent_output: str,
        expected_behavior: str,
        conversation_id: Optional[str] = None,
        additional_context: Optional[dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate a single test response using LLM semantic analysis.

        Args:
            test_name: Name of the test (for logging)
            user_input: User's input/query
            agent_output: Agent's response
            expected_behavior: Description of what should happen
            conversation_id: Optional conversation ID for context
            additional_context: Optional additional context (e.g., test metadata)

        Returns:
            ValidationResult with verdict, confidence, reasoning, and metrics
        """
        if not self._enabled:
            return ValidationResult(
                verdict=ValidationVerdict.SKIP,
                confidence=0.0,
                reasoning="LLM validation is disabled",
                semantic_issues=[],
                tokens_used=0,
                validation_time_ms=0,
                timestamp=datetime.utcnow(),
            )

        start_time = datetime.utcnow()

        # Build validation prompt
        prompt = self._build_single_validation_prompt(
            test_name=test_name,
            user_input=user_input,
            agent_output=agent_output,
            expected_behavior=expected_behavior,
            conversation_id=conversation_id,
            additional_context=additional_context,
        )

        # Call LLM for validation
        try:
            response = await self._client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test validation assistant. Analyze test responses semantically and provide validation verdicts in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self._model,
                temperature=0.1,  # Low temperature for consistent validation
                max_tokens=1000,
            )

            # Parse validation result
            validation_data = self._parse_validation_response(response["content"])

            end_time = datetime.utcnow()
            validation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return ValidationResult(
                verdict=ValidationVerdict(validation_data.get("verdict", "FAIL")),
                confidence=validation_data.get("confidence", 0.0),
                reasoning=validation_data.get("reasoning", ""),
                semantic_issues=validation_data.get("semantic_issues", []),
                tokens_used=response.get("tokens_used", 0),
                validation_time_ms=validation_time_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"LLM validation failed for {test_name}: {e}")
            end_time = datetime.utcnow()
            validation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return ValidationResult(
                verdict=ValidationVerdict.SKIP,
                confidence=0.0,
                reasoning=f"LLM validation error: {str(e)}",
                semantic_issues=[],
                tokens_used=0,
                validation_time_ms=validation_time_ms,
                timestamp=datetime.utcnow(),
            )

    async def validate_multistep_flow(
        self,
        test_name: str,
        steps: list[dict[str, str]],
        expected_flow_behavior: str,
        conversation_id: Optional[str] = None,
    ) -> MultiStepValidationResult:
        """
        Validate a multi-step conversation flow.

        Args:
            test_name: Name of the test
            steps: List of conversation steps, each with:
                - user_input: User's input
                - agent_output: Agent's response
                - expected_behavior: Expected behavior for this step
            expected_flow_behavior: Overall expected behavior for the entire flow
            conversation_id: Optional conversation ID

        Returns:
            MultiStepValidationResult with flow-level validation
        """
        if not self._enabled:
            return MultiStepValidationResult(
                verdict=ValidationVerdict.SKIP,
                confidence=0.0,
                reasoning="LLM validation is disabled",
                step_validations=[],
                context_consistency_score=0.0,
                tokens_used=0,
                validation_time_ms=0,
            )

        start_time = datetime.utcnow()

        # Validate each step individually
        step_validations = []
        for i, step in enumerate(steps, 1):
            step_result = await self.validate_single_response(
                test_name=f"{test_name}_step{i}",
                user_input=step["user_input"],
                agent_output=step["agent_output"],
                expected_behavior=step.get("expected_behavior", ""),
                conversation_id=conversation_id,
            )
            step_validations.append(step_result)

        # Validate overall flow consistency
        flow_prompt = self._build_multistep_validation_prompt(
            test_name=test_name,
            steps=steps,
            expected_flow_behavior=expected_flow_behavior,
            step_validations=step_validations,
        )

        try:
            response = await self._client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test validation assistant analyzing multi-step conversation flows. "
                        "Evaluate context consistency, conversation coherence, and overall flow correctness. "
                        "Respond in JSON format.",
                    },
                    {"role": "user", "content": flow_prompt},
                ],
                model=self._model,
                temperature=0.1,
                max_tokens=1500,
            )

            # Parse flow validation result
            flow_data = self._parse_validation_response(response["content"])

            end_time = datetime.utcnow()
            validation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Calculate total tokens used
            total_tokens = sum(v.tokens_used for v in step_validations) + response.get("tokens_used", 0)

            return MultiStepValidationResult(
                verdict=ValidationVerdict(flow_data.get("verdict", "FAIL")),
                confidence=flow_data.get("confidence", 0.0),
                reasoning=flow_data.get("reasoning", ""),
                step_validations=step_validations,
                context_consistency_score=flow_data.get("context_consistency_score", 0.0),
                tokens_used=total_tokens,
                validation_time_ms=validation_time_ms,
            )

        except Exception as e:
            logger.error(f"Multi-step LLM validation failed for {test_name}: {e}")
            end_time = datetime.utcnow()
            validation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # If flow validation fails, determine verdict from step validations
            step_failures = sum(1 for v in step_validations if v.verdict == ValidationVerdict.FAIL)
            overall_verdict = ValidationVerdict.FAIL if step_failures > 0 else ValidationVerdict.WARNING

            return MultiStepValidationResult(
                verdict=overall_verdict,
                confidence=0.0,
                reasoning=f"Multi-step validation error: {str(e)}",
                step_validations=step_validations,
                context_consistency_score=0.0,
                tokens_used=sum(v.tokens_used for v in step_validations),
                validation_time_ms=validation_time_ms,
            )

    def _build_single_validation_prompt(
        self,
        test_name: str,
        user_input: str,
        agent_output: str,
        expected_behavior: str,
        conversation_id: Optional[str],
        additional_context: Optional[dict[str, Any]],
    ) -> str:
        """Build validation prompt for single response."""
        context_str = ""
        if additional_context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(additional_context, indent=2)}"

        conv_str = f"\nConversation ID: {conversation_id}" if conversation_id else ""

        return f"""Validate this test response semantically:

Test Name: {test_name}{conv_str}

User Input:
{user_input}

Agent Output:
{agent_output}

Expected Behavior:
{expected_behavior}{context_str}

Analyze the agent's response and determine:
1. Does the response match the expected behavior?
2. Is the response contextually appropriate?
3. Are there any semantic errors or inconsistencies?
4. Does the response show understanding of the user's intent?

Respond with JSON containing:
{{
  "verdict": "PASS" | "FAIL" | "WARNING",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of the verdict",
  "semantic_issues": ["list", "of", "issues"]
}}"""

    def _build_multistep_validation_prompt(
        self,
        test_name: str,
        steps: list[dict[str, str]],
        expected_flow_behavior: str,
        step_validations: list[ValidationResult],
    ) -> str:
        """Build validation prompt for multi-step flow."""
        steps_str = "\n\n".join(
            [
                f"Step {i+1}:\n  User: {step['user_input']}\n  Agent: {step['agent_output']}\n  Step Verdict: {step_validations[i].verdict.value}"
                for i, step in enumerate(steps)
            ]
        )

        return f"""Validate this multi-step conversation flow:

Test Name: {test_name}

Conversation Steps:
{steps_str}

Expected Flow Behavior:
{expected_flow_behavior}

Analyze the conversation flow and determine:
1. Is there context consistency across all steps?
2. Does the agent maintain conversation coherence?
3. Are there any context switches or memory issues?
4. Does the overall flow match expected behavior?

Respond with JSON containing:
{{
  "verdict": "PASS" | "FAIL" | "WARNING",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of flow analysis",
  "context_consistency_score": 0.0-1.0,
  "flow_issues": ["list", "of", "issues"]
}}"""

    def _parse_validation_response(self, content: str) -> dict[str, Any]:
        """Parse LLM validation response from JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
                return json.loads(content)
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                return json.loads(content)
            else:
                # Last resort: return minimal failure
                logger.warning(f"Failed to parse LLM validation response: {content}")
                return {
                    "verdict": "FAIL",
                    "confidence": 0.0,
                    "reasoning": f"Failed to parse LLM response: {content[:100]}",
                    "semantic_issues": ["Parse error"],
                }

"""Validation prompt generator using strategy pattern.

This module generates custom validation prompts for different test types using
a strategy pattern. Each test type has its own prompt strategy optimized for that
specific validation scenario.
"""

from typing import Optional, Protocol

from tests.helpers.test_metadata_extractor import TestMetadata, TestType


class PromptStrategy(Protocol):
    """Protocol for validation prompt strategies."""

    def build_prompt(
        self,
        test_metadata: TestMetadata,
        user_input: str,
        agent_output: str,
        expected_behavior: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> str:
        """Build custom validation prompt.

        Args:
            test_metadata: Extracted test metadata
            user_input: User's input/query
            agent_output: Agent's response to validate
            expected_behavior: Expected behavior description
            conversation_history: Optional conversation history for multi-step tests

        Returns:
            Custom validation prompt string
        """
        ...


class ValidationPromptGenerator:
    """Generate custom validation prompts based on test type."""

    def __init__(self):
        """Initialize the prompt generator with strategies."""
        # Import strategies here to avoid circular imports
        from tests.helpers.prompt_strategies.simple_query import SimpleQueryStrategy
        from tests.helpers.prompt_strategies.multi_step import MultiStepFlowStrategy
        from tests.helpers.prompt_strategies.intent_detection import (
            IntentDetectionStrategy,
        )
        from tests.helpers.prompt_strategies.security import SecurityTestStrategy

        self.strategies: dict[TestType, PromptStrategy] = {
            TestType.SIMPLE_QUERY: SimpleQueryStrategy(),
            TestType.MULTI_STEP: MultiStepFlowStrategy(),
            TestType.INTENT_DETECTION: IntentDetectionStrategy(),
            TestType.SECURITY: SecurityTestStrategy(),
            TestType.ERROR_HANDLING: SecurityTestStrategy(),  # Reuse security strategy
            TestType.KNOWLEDGE_QUERY: SimpleQueryStrategy(),  # Reuse simple query strategy
        }

    def generate_prompt(
        self,
        test_metadata: TestMetadata,
        user_input: str,
        agent_output: str,
        expected_behavior: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> str:
        """Generate custom validation prompt for test.

        Args:
            test_metadata: Extracted test metadata
            user_input: User's input/query
            agent_output: Agent's response to validate
            expected_behavior: Expected behavior description
            conversation_history: Optional conversation history for multi-step tests

        Returns:
            Custom validation prompt optimized for test type
        """
        strategy = self.strategies.get(
            test_metadata.test_type, self.strategies[TestType.SIMPLE_QUERY]
        )

        return strategy.build_prompt(
            test_metadata=test_metadata,
            user_input=user_input,
            agent_output=agent_output,
            expected_behavior=expected_behavior,
            conversation_history=conversation_history,
        )

"""
Template executor service for running conversation workflows.

Executes multi-agent conversation templates with dependency management
and parallel execution support.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, UTC

from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
)
from app.domain.chat.ports.template_repository import TemplateRepository
from app.domain.exceptions.chat import (
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateExecutionError,
)

logger = logging.getLogger(__name__)


class TemplateExecutionResult:
    """Result of template execution."""

    def __init__(
        self,
        template_id: UUID,
        success: bool,
        outputs: Dict[int, Any],
        execution_time_seconds: float,
        error: Optional[str] = None,
    ):
        self.template_id = template_id
        self.success = success
        self.outputs = outputs
        self.execution_time_seconds = execution_time_seconds
        self.error = error

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "template_id": str(self.template_id),
            "success": self.success,
            "outputs": self.outputs,
            "execution_time_seconds": self.execution_time_seconds,
            "error": self.error,
        }


class TemplateExecutorService:
    """
    Execute conversation templates with multi-agent workflows.

    Instead of manually orchestrating agents, users run templates:
    - "Run portfolio health check"
    - "Execute compliance audit template"
    - "Run yield optimization workflow"
    """

    def __init__(
        self,
        template_repository: TemplateRepository,
        # TODO: Add agent executor port for invoking individual agents
    ):
        """
        Initialize template executor.

        Args:
            template_repository: Repository for conversation templates
        """
        self._repository = template_repository

    async def execute_template(
        self,
        template_id: UUID,
        inputs: Dict[str, Any],
        user_id: UUID,
    ) -> TemplateExecutionResult:
        """
        Execute a conversation template.

        Args:
            template_id: Template identifier
            inputs: User-provided inputs
            user_id: User executing the template

        Returns:
            TemplateExecutionResult with outputs from all steps

        Raises:
            TemplateNotFoundError: Template not found
            TemplateValidationError: Invalid inputs
            TemplateExecutionError: Execution failed
        """
        start_time = datetime.now(UTC)

        # Load template
        template = await self._repository.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        # Validate inputs
        is_valid, error = template.validate_inputs(inputs)
        if not is_valid:
            raise TemplateValidationError(error)

        # Execute steps in dependency order
        try:
            outputs = await self._execute_steps(template, inputs, user_id)

            # Update template usage statistics
            template.increment_usage(success=True)
            await self._repository.save(template)

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return TemplateExecutionResult(
                template_id=template_id,
                success=True,
                outputs=outputs,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            logger.error(f"Template execution failed: {e}", exc_info=True)

            # Update template usage statistics
            template.increment_usage(success=False)
            await self._repository.save(template)

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return TemplateExecutionResult(
                template_id=template_id,
                success=False,
                outputs={},
                execution_time_seconds=execution_time,
                error=str(e),
            )

    async def _execute_steps(
        self,
        template: ConversationTemplate,
        inputs: Dict[str, Any],
        user_id: UUID,
    ) -> Dict[int, Any]:
        """
        Execute template steps respecting dependencies.

        Args:
            template: Template to execute
            inputs: User inputs
            user_id: User identifier

        Returns:
            Dictionary mapping step index to output
        """
        outputs: Dict[int, Any] = {}
        completed: set[int] = set()

        # Build dependency graph
        steps = template.agent_sequence
        total_steps = len(steps)

        while len(completed) < total_steps:
            # Find steps ready to execute (dependencies met)
            ready_steps = []
            for idx, step in enumerate(steps):
                if idx in completed:
                    continue

                # Check if all dependencies are completed
                if all(dep_idx in completed for dep_idx in step.depends_on):
                    ready_steps.append((idx, step))

            if not ready_steps:
                # Circular dependency or unreachable step
                incomplete = set(range(total_steps)) - completed
                raise TemplateExecutionError(
                    f"Cannot execute steps: {incomplete}. "
                    f"Possible circular dependency or unreachable steps."
                )

            # Separate parallel and sequential steps
            parallel_steps = [(idx, step) for idx, step in ready_steps if step.parallel_execution]
            sequential_steps = [(idx, step) for idx, step in ready_steps if not step.parallel_execution]

            # Execute parallel steps concurrently
            if parallel_steps:
                parallel_results = await asyncio.gather(
                    *[
                        self._execute_single_step(step, idx, inputs, outputs, user_id)
                        for idx, step in parallel_steps
                    ],
                    return_exceptions=True,
                )

                for (idx, _), result in zip(parallel_steps, parallel_results):
                    if isinstance(result, Exception):
                        raise TemplateExecutionError(
                            f"Step {idx} failed: {result}"
                        )
                    outputs[idx] = result
                    completed.add(idx)

            # Execute sequential steps one by one
            for idx, step in sequential_steps:
                try:
                    result = await self._execute_single_step(
                        step, idx, inputs, outputs, user_id
                    )
                    outputs[idx] = result
                    completed.add(idx)
                except Exception as e:
                    raise TemplateExecutionError(
                        f"Step {idx} failed: {e}"
                    )

        return outputs

    async def _execute_single_step(
        self,
        step: AgentStep,
        step_index: int,
        inputs: Dict[str, Any],
        previous_outputs: Dict[int, Any],
        user_id: UUID,
    ) -> Any:
        """
        Execute a single agent step.

        Args:
            step: Agent step to execute
            step_index: Step index
            inputs: User inputs
            previous_outputs: Outputs from previous steps
            user_id: User identifier

        Returns:
            Step output
        """
        # Build context for prompt
        context = {
            "inputs": inputs,
            "previous_outputs": {
                dep_idx: previous_outputs[dep_idx]
                for dep_idx in step.depends_on
                if dep_idx in previous_outputs
            },
        }

        # TODO: Invoke agent with prompt template
        # For now, return placeholder
        logger.info(
            f"Executing step {step_index}: {step.agent_name} "
            f"(timeout: {step.timeout_seconds}s)"
        )

        # Placeholder execution
        await asyncio.sleep(0.1)  # Simulate agent execution

        return {
            "agent": step.agent_name,
            "status": "completed",
            "result": f"Placeholder result from {step.agent_name}",
            "context": context,
        }

    async def execute_template_by_name(
        self,
        template_name: str,
        inputs: Dict[str, Any],
        user_id: UUID,
    ) -> TemplateExecutionResult:
        """
        Execute template by name.

        Args:
            template_name: Template name
            inputs: User inputs
            user_id: User identifier

        Returns:
            TemplateExecutionResult
        """
        template = await self._repository.get_by_name(template_name)
        if not template:
            raise TemplateNotFoundError(f"Template '{template_name}' not found")

        return await self.execute_template(template.id, inputs, user_id)

    async def list_available_templates(
        self,
        user_id: UUID,
        category: Optional[str] = None,
    ) -> List[ConversationTemplate]:
        """
        List available templates for user.

        Args:
            user_id: User identifier
            category: Optional category filter

        Returns:
            List of available templates
        """
        # Get public templates and user's private templates
        templates = await self._repository.get_available_for_user(user_id, category)
        return templates

    async def create_template(
        self,
        name: str,
        description: str,
        category: str,
        agent_sequence: List[AgentStep],
        required_inputs: Dict[str, Any],
        estimated_duration_seconds: int,
        user_id: UUID,
        is_public: bool = False,
    ) -> ConversationTemplate:
        """
        Create a new conversation template.

        Args:
            name: Template name
            description: Template description
            category: Template category
            agent_sequence: Sequence of agent steps
            required_inputs: Required input specifications
            estimated_duration_seconds: Estimated execution time
            user_id: User creating the template
            is_public: Whether template is public

        Returns:
            Created ConversationTemplate
        """
        template = ConversationTemplate.create(
            name=name,
            description=description,
            category=category,
            agent_sequence=agent_sequence,
            required_inputs=required_inputs,
            estimated_duration_seconds=estimated_duration_seconds,
            created_by=user_id,
            is_public=is_public,
        )

        await self._repository.save(template)
        return template

    def format_template_result(self, result: TemplateExecutionResult) -> str:
        """
        Format template execution result for chat display.

        Args:
            result: Template execution result

        Returns:
            Formatted markdown string
        """
        if result.success:
            lines = [
                f"✅ Template executed successfully in {result.execution_time_seconds:.1f}s",
                "",
                "**Results:**",
            ]

            for step_idx, output in sorted(result.outputs.items()):
                if isinstance(output, dict):
                    agent_name = output.get("agent", f"Step {step_idx}")
                    lines.append(f"  {step_idx + 1}. {agent_name}: ✓ Completed")
                else:
                    lines.append(f"  {step_idx + 1}. ✓ Completed")

            return "\n".join(lines)
        else:
            return (
                f"❌ Template execution failed after {result.execution_time_seconds:.1f}s\n"
                f"Error: {result.error}"
            )

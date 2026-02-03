"""
Execute Supervisor Workflow Command.

This interactor orchestrates complex multi-agent workflows:
1. Planning workflow with multiple agents
2. Executing agents in parallel or sequence
3. Aggregating results
4. Tracking workflow status
"""

from datetime import datetime, UTC
from uuid import UUID

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_role import MessageRole
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.chat.ports.message_repository import MessageRepository
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationMessage,
)
from app.domain.value_objects.conversation_id import ConversationId


class ExecuteSupervisorWorkflow:
    """
    Command interactor for executing supervisor-coordinated workflows.

    Responsibilities:
    - Plan multi-agent workflow based on user request
    - Execute agents in optimal order (parallel/sequential)
    - Aggregate and synthesize results
    - Track workflow progress and status
    """

    def __init__(
        self,
        supervisor: SupervisorCoordinator,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
        message_repository: MessageRepository,
    ):
        self._supervisor = supervisor
        self._context_manager = context_manager
        self._context_storage = context_storage
        self._message_repository = message_repository

    async def execute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        complex_task: str,
        max_agents: int = 5,
    ) -> dict:
        """
        Execute a supervisor-coordinated workflow.

        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            complex_task: Complex user task requiring multiple agents
            max_agents: Maximum number of agents to use (default: 5)

        Returns:
            dict with:
                - workflow_id: UUID of workflow execution
                - plan: List of agents and their tasks
                - tasks: List of task results with agent responses
                - final_synthesis: Aggregated and synthesized response
                - total_latency_ms: Total workflow execution time
                - agents_used: Number of agents used
                - tokens_used: Total tokens consumed across all agents

        Raises:
            ValueError: If max_agents exceeds limits or task is invalid
        """
        start_time = datetime.now(UTC)
        workflow_id = UUID(int=0)  # Placeholder for now

        # Validate max_agents
        if max_agents < 1 or max_agents > 10:
            raise ValueError("max_agents must be between 1 and 10")

        # Step 1: Build conversation context
        conv_id = ConversationId(conversation_id)
        context = await self._context_manager.build_context(
            conversation_id=conv_id,
            recent_messages_limit=10,
        )

        # Step 2: Plan workflow
        workflow_plan = await self._supervisor.plan_workflow(
            complex_task=complex_task,
            conversation_context=context,
            max_agents=max_agents,
        )

        # Step 3: Execute workflow
        workflow_result = await self._supervisor.execute_workflow(
            workflow_plan=workflow_plan,
            complex_task=complex_task,
            conversation_context=context,
        )

        # Step 4: Save workflow result to context storage
        await self._context_storage.add_message(
            conversation_id=conv_id,
            message=ConversationMessage(
                role=MessageRole.AGENT.value,
                content=workflow_result.final_response,
                timestamp=datetime.now(UTC).isoformat(),
                metadata={
                    "workflow_id": str(workflow_id),
                    "agents_used": [
                        task.agent_type.value for task in workflow_result.task_results
                    ],
                    "is_supervisor_workflow": True,
                },
            ),
        )

        # Step 5: Calculate metrics
        end_time = datetime.now(UTC)
        total_latency_ms = int((end_time - start_time).total_seconds() * 1000)
        total_tokens = sum(
            task.tokens_used or 0 for task in workflow_result.task_results
        )

        # Step 6: Format response
        return {
            "workflow_id": workflow_id,
            "plan": [
                {
                    "agent_type": task.agent_type.value,
                    "task_description": task.task_description,
                    "order": task.execution_order,
                    "dependencies": task.dependencies,
                }
                for task in workflow_plan.tasks
            ],
            "tasks": [
                {
                    "agent_type": task.agent_type.value,
                    "task_description": task.task_description,
                    "response": task.response,
                    "tools_used": task.tools_used,
                    "latency_ms": task.latency_ms,
                    "tokens_used": task.tokens_used,
                    "success": task.success,
                    "error": task.error,
                }
                for task in workflow_result.task_results
            ],
            "final_synthesis": workflow_result.final_response,
            "total_latency_ms": total_latency_ms,
            "agents_used": len(workflow_result.task_results),
            "tokens_used": total_tokens,
        }

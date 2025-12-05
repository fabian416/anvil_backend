"""
Supervisor Coordinator domain service - Coordinates multi-agent workflows.
"""

from typing import Protocol
from dataclasses import dataclass
from enum import Enum

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent


class TaskStatus(Enum):
    """Task status enum."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """
    Task for a single agent in complex workflow.
    
    Contains:
    - agent_type: Which agent to use
    - task_description: What the agent should do
    - depends_on: Task dependencies (must complete first)
    - status: Task status
    - result: Agent response (after completion)
    """
    agent_type: AgentType
    task_description: str
    depends_on: list[int]  # Task indices that must complete first
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_type": self.agent_type.value,
            "task_description": self.task_description,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class WorkflowPlan:
    """
    Multi-agent workflow plan.
    
    Contains:
    - tasks: List of agent tasks
    - execution_order: Optimal execution order
    - estimated_time: Estimated completion time
    """
    tasks: list[AgentTask]
    execution_order: list[int]  # Task indices in execution order
    estimated_time_seconds: int
    
    def get_next_task(self) -> AgentTask | None:
        """Get next pending task with satisfied dependencies."""
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check dependencies
            dependencies_satisfied = all(
                self.tasks[dep_idx].status == TaskStatus.COMPLETED
                for dep_idx in task.depends_on
            )
            
            if dependencies_satisfied:
                return task
        
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(task.status == TaskStatus.COMPLETED for task in self.tasks)
    
    @property
    def has_failures(self) -> bool:
        """Check if any tasks failed."""
        return any(task.status == TaskStatus.FAILED for task in self.tasks)


class SupervisorCoordinator:
    """
    Supervisor Coordinator domain service.
    
    Responsibilities:
    - Coordinate complex multi-agent workflows
    - Break down complex tasks into agent subtasks
    - Manage task dependencies and execution order
    - Aggregate results from multiple agents
    - Handle partial failures
    
    Architecture:
    - Domain service (framework-agnostic)
    - Uses LLM port for task planning
    - Uses agent executor port for running agents
    
    Example Workflow:
    User: "Create a balanced DeFi portfolio"
    
    Supervisor Plan:
    1. Research agent: Find top protocols
    2. Risk analyzer: Assess protocol risks
    3. Portfolio agent: Create optimal allocation
    4. Tax optimizer: Suggest tax-efficient timing
    5. Chat agent: Summarize recommendations
    """
    
    def __init__(
        self,
        llm_client: "LLMClientPort",
        agent_executor: "AgentExecutorPort",
        max_agents: int = 5,
        timeout_seconds: int = 120,
    ):
        """
        Initialize supervisor coordinator.
        
        Args:
            llm_client: LLM client for task planning
            agent_executor: Agent executor for running agents
            max_agents: Maximum agents per workflow (default 5)
            timeout_seconds: Workflow timeout (default 120s)
        """
        self._llm_client = llm_client
        self._agent_executor = agent_executor
        self._max_agents = max_agents
        self._timeout_seconds = timeout_seconds
    
    async def create_workflow_plan(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: "ConversationContext",
        available_agents: list[AgentType],
    ) -> WorkflowPlan:
        """
        Create multi-agent workflow plan for complex task.
        
        Args:
            conversation_id: Conversation identifier
            message: User message
            conversation_context: Conversation history
            available_agents: Available agents for workflow
            
        Returns:
            WorkflowPlan with agent tasks and execution order
        """
        # Build planning prompt
        prompt = self._build_planning_prompt(
            message,
            conversation_context,
            available_agents,
        )
        
        # Call LLM for workflow planning
        response = await self._llm_client.plan_workflow(
            prompt=prompt,
            max_agents=self._max_agents,
        )
        
        # Parse workflow plan
        tasks = []
        for task_data in response.get("tasks", []):
            agent_type_str = task_data.get("agent_type", "chat")
            try:
                agent_type = AgentType[agent_type_str.upper()]
            except KeyError:
                agent_type = AgentType.CHAT
            
            task = AgentTask(
                agent_type=agent_type,
                task_description=task_data.get("task_description", ""),
                depends_on=task_data.get("depends_on", []),
            )
            tasks.append(task)
        
        # Determine execution order
        execution_order = self._calculate_execution_order(tasks)
        
        # Estimate time (rough: 10s per agent)
        estimated_time = len(tasks) * 10
        
        return WorkflowPlan(
            tasks=tasks,
            execution_order=execution_order,
            estimated_time_seconds=estimated_time,
        )
    
    async def execute_workflow(
        self,
        conversation_id: ConversationId,
        workflow_plan: WorkflowPlan,
        conversation_context: "ConversationContext",
    ) -> str:
        """
        Execute multi-agent workflow.
        
        Args:
            conversation_id: Conversation identifier
            workflow_plan: Workflow plan to execute
            conversation_context: Conversation context
            
        Returns:
            Final aggregated response from all agents
        """
        # Execute tasks in order
        for task in workflow_plan.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check dependencies
            next_task = workflow_plan.get_next_task()
            if next_task is None:
                break
            
            # Execute task
            next_task.status = TaskStatus.IN_PROGRESS
            
            try:
                result = await self._agent_executor.execute_agent(
                    conversation_id=conversation_id,
                    agent_type=next_task.agent_type,
                    message=MessageContent(next_task.task_description),
                    conversation_context=conversation_context,
                )
                
                next_task.result = result
                next_task.status = TaskStatus.COMPLETED
                
            except Exception as e:
                next_task.error = str(e)
                next_task.status = TaskStatus.FAILED
        
        # Aggregate results
        final_response = await self._aggregate_results(workflow_plan)
        
        return final_response
    
    def _build_planning_prompt(
        self,
        message: MessageContent,
        conversation_context: "ConversationContext",
        available_agents: list[AgentType],
    ) -> str:
        """Build workflow planning prompt for LLM."""
        agents_str = ", ".join([agent.value for agent in available_agents])
        
        return f"""
You are a workflow supervisor coordinating multiple AI agents.

User Request:
{message.value}

Available Agents:
{agents_str}

Create a workflow plan with multiple agent tasks.

Respond with JSON:
{{
    "tasks": [
        {{
            "agent_type": "agent_name",
            "task_description": "what this agent should do",
            "depends_on": [0, 1]  // Task indices that must complete first
        }},
        ...
    ],
    "reasoning": "why this workflow makes sense"
}}

Guidelines:
- Break down complex task into agent-specific subtasks
- Use dependencies to ensure correct order
- Each agent should have a clear, specific task
- Final task should aggregate/summarize results
- Limit to {self._max_agents} agents
"""
    
    def _calculate_execution_order(
        self,
        tasks: list[AgentTask],
    ) -> list[int]:
        """Calculate optimal execution order based on dependencies."""
        # Topological sort
        order = []
        visited = set()
        
        def visit(task_idx: int):
            if task_idx in visited:
                return
            
            task = tasks[task_idx]
            for dep_idx in task.depends_on:
                visit(dep_idx)
            
            visited.add(task_idx)
            order.append(task_idx)
        
        for idx in range(len(tasks)):
            visit(idx)
        
        return order
    
    async def _aggregate_results(
        self,
        workflow_plan: WorkflowPlan,
    ) -> str:
        """Aggregate results from all completed tasks."""
        completed_tasks = [
            task for task in workflow_plan.tasks
            if task.status == TaskStatus.COMPLETED
        ]
        
        if not completed_tasks:
            return "No tasks completed successfully."
        
        # Build aggregated response
        parts = ["Here's the analysis from our specialist agents:\n"]
        
        for task in completed_tasks:
            parts.append(f"\n**{task.agent_type.value.upper()}**:")
            parts.append(task.result or "(No response)")
        
        return "\n".join(parts)


# Ports (interfaces) for dependency injection

class LLMClientPort(Protocol):
    """Port for LLM client (workflow planning)."""
    
    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """Plan multi-agent workflow."""
        ...


class AgentExecutorPort(Protocol):
    """Port for agent execution."""
    
    async def execute_agent(
        self,
        conversation_id: ConversationId,
        agent_type: AgentType,
        message: MessageContent,
        conversation_context: "ConversationContext",
    ) -> str:
        """Execute specific agent."""
        ...

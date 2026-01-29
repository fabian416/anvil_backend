"""
Send Message With Supervisor Command.

Application layer command for processing authenticated user messages
using the AuthenticatedSupervisorCoordinator for LLM-based multi-agent orchestration.

This command:
1. Receives user message and context
2. Uses AuthenticatedSupervisor for intelligent routing
3. Orchestrates multiple agents as needed
4. Returns aggregated response with sources

Architecture follows Hexagonal Architecture patterns:
- Command in Application layer
- Uses Domain services (SupervisorCoordinator)
- Receives ports via dependency injection
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any
from uuid import UUID

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class SupervisorMessageResult:
    """Result from supervisor-based message processing."""
    
    content: str
    """The aggregated response content."""
    
    agents_used: list[str] = field(default_factory=list)
    """List of agent types that contributed to the response."""
    
    sources: list[dict[str, Any]] = field(default_factory=list)
    """Source attribution for the response."""
    
    agent_timings: list[dict[str, Any]] = field(default_factory=list)
    """Timing information for each agent execution."""
    
    workflow_type: str = "authenticated_supervisor"
    """Type of workflow executed."""
    
    task_count: int = 0
    """Number of tasks in the workflow."""
    
    total_time_ms: int = 0
    """Total execution time in milliseconds."""
    
    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the execution."""
    
    execute_data: dict[str, Any] | None = None
    """Execute action data for frontend execution modal (from workflow agents like swap_workflow)."""


class SendMessageWithSupervisor:
    """
    Command to send a message using the AuthenticatedSupervisorCoordinator.
    
    This command provides LLM-based multi-agent orchestration for authenticated
    users, enabling complex workflows with real data access.
    
    Flow:
    1. Build conversation context from history
    2. Set user context (wallet, portfolio) on supervisor
    3. Create workflow plan via LLM
    4. Execute workflow (potentially parallel agents)
    5. Aggregate and return results
    
    Example:
        >>> cmd = SendMessageWithSupervisor(supervisor, orchestrator)
        >>> result = await cmd.execute(
        ...     conversation_id=uuid,
        ...     message="swap 1 ETH to USDC",
        ...     language="en",
        ...     conversation_history=[...],
        ...     user_context={"wallet_address": "0x..."}
        ... )
    """
    
    def __init__(
        self,
        supervisor_coordinator: Any,  # AuthenticatedSupervisorCoordinator
        agent_orchestrator: Any,  # AgentOrchestrator
    ):
        """
        Initialize command with required dependencies.
        
        Args:
            supervisor_coordinator: AuthenticatedSupervisorCoordinator instance
            agent_orchestrator: AgentOrchestrator for executing individual agents
        """
        self._supervisor = supervisor_coordinator
        self._orchestrator = agent_orchestrator
    
    async def execute(
        self,
        conversation_id: UUID,
        message: str,
        language: str = "en",
        conversation_history: list[dict[str, Any]] | None = None,
        user_context: dict[str, Any] | None = None,
    ) -> SupervisorMessageResult:
        """
        Execute message processing with supervisor orchestration.
        
        Args:
            conversation_id: The conversation UUID
            message: User's message content
            language: Language code (en, es, pt, zh)
            conversation_history: Recent messages for context
            user_context: User-specific context (wallet, portfolio, etc.)
        
        Returns:
            SupervisorMessageResult with aggregated response and metadata
        """
        start_time = time.time()
        
        # Build conversation context
        agent_context = ConversationContext(
            conversation_history=conversation_history or [],
            user_metadata={
                "language": language,
                "is_authenticated": True,
                **(user_context or {}),
            },
            session_metadata={},
        )
        
        # Set user context on supervisor
        if user_context:
            self._supervisor.set_user_context(
                user_id=user_context.get("user_id"),
                wallet_address=user_context.get("wallet_address"),
                portfolio_summary=user_context.get("portfolio_summary"),
                preferences=user_context.get("preferences"),
            )
            
            # Set context-aware data if provided
            # This enables personalized responses based on user classification
            if user_context.get("context_aware"):
                self._supervisor.set_context_aware(user_context["context_aware"])
            
            # Load full user data from repositories if available
            if user_context.get("user_id") and hasattr(self._supervisor, 'load_user_data'):
                try:
                    await self._supervisor.load_user_data(user_context["user_id"])
                except Exception as e:
                    logger.warning(f"Failed to load user data: {e}")
        
        # Get available agents
        # Includes workflow agents for multi-step operations
        available_agents = [
            AgentType.CHAT,
            AgentType.HUNTER_AI,
            AgentType.KNOWLEDGE,
            AgentType.RISK_ANALYZER,
            AgentType.PORTFOLIO,
            AgentType.DEFI_YIELD,
            AgentType.GAS_OPTIMIZER,
            AgentType.RESEARCH,
            AgentType.SECURITY_AUDITOR,
            AgentType.TAX_OPTIMIZER,
            # Authenticated-only agents
            AgentType.WALLET,
            AgentType.TRANSACTION_HISTORY,
            # Workflow agents (multi-step operations)
            AgentType.SWAP_WORKFLOW,  # Multi-step swap execution
            AgentType.LENDING_WORKFLOW,  # Multi-step deposit/yield
            AgentType.TRANSFER_WORKFLOW,  # Multi-step token transfer
            AgentType.BUY_WORKFLOW,  # Multi-step fiat on-ramp
            AgentType.MONEY_MARKET_WORKFLOW,  # Multi-step rate comparison
        ]
        
        try:
            # Track supervisor planning time
            planning_start = time.time()
            
            # Create workflow plan
            logger.info(
                f"🔄 Creating workflow plan for authenticated user",
                extra={
                    "conversation_id": str(conversation_id),
                    "message_preview": message[:100],
                    "has_wallet": bool(user_context and user_context.get("wallet_address")),
                }
            )
            
            workflow_plan = await self._supervisor.create_workflow_plan(
                conversation_id=ConversationId(conversation_id),
                message=MessageContent(message),
                conversation_context=agent_context,
                available_agents=available_agents,
            )
            
            planning_time_ms = int((time.time() - planning_start) * 1000)
            
            logger.info(
                f"📋 Workflow planned: {len(workflow_plan.tasks)} tasks in {planning_time_ms}ms",
                extra={
                    "tasks": [t.agent_type.value for t in workflow_plan.tasks],
                    "planning_time_ms": planning_time_ms,
                }
            )
            
            # Execute workflow - CRITICAL: pass message explicitly to prevent context pollution
            # Do NOT rely on conversation_history[-1] as it may contain previous messages
            execution_start = time.time()
            response_content, sources_raw, agent_timings = await self._supervisor.execute_workflow(
                conversation_id=ConversationId(conversation_id),
                workflow_plan=workflow_plan,
                conversation_context=agent_context,
                original_message=message,  # Explicitly pass current user message
            )
            execution_time_ms = int((time.time() - execution_start) * 1000)
            
            # Process sources
            sources = []
            for source in sources_raw:
                if hasattr(source, "to_dict"):
                    sources.append(source.to_dict())
                elif isinstance(source, dict):
                    sources.append(source)
                else:
                    sources.append({"raw": str(source)})
            
            # Add supervisor planning as a source (LLM used for routing)
            from datetime import datetime, UTC
            supervisor_source = {
                "source_type": "llm",
                "source_name": "gemini-2.0-flash",  # Default supervisor model
                "citation_text": "Supervisor LLM for workflow planning and routing",
                "fetched_at": datetime.now(UTC).isoformat(),
                "provider": "Vertex AI",
                "metadata": {
                    "role": "supervisor",
                    "planning_time_ms": planning_time_ms,
                    "tasks_planned": len(workflow_plan.tasks),
                },
            }
            sources.insert(0, supervisor_source)  # Add at beginning
            
            # Add supervisor timing entry at the beginning of agent_timings
            supervisor_timing = {
                "agent_type": "supervisor",
                "task_description": f"Plan workflow: {len(workflow_plan.tasks)} agent(s) | LLM: Vertex AI",
                "execution_time_ms": planning_time_ms,
                "status": "completed",
                "provider": "Vertex AI",
                "tools_used": ["workflow_planning"],
            }
            agent_timings.insert(0, supervisor_timing)  # Add at beginning
            
            # Debug: Log sources count
            logger.info(
                f"📊 Sources collected: {len(sources)} sources (including supervisor)",
                extra={"source_names": [s.get('source_name', 'unknown') for s in sources]}
            )
            
            # Extract execute_data and workflow_state from workflow agent responses
            # Workflow agents (like swap_workflow) store these in their response metadata
            execute_data = None
            workflow_state = None
            workflow_name = None
            from app.domain.ports.agent_squad.agent_gateway import AgentResponse
            for task in workflow_plan.tasks:
                if hasattr(task, 'result') and task.result:
                    result = task.result
                    if isinstance(result, AgentResponse) and result.metadata:
                        # Check for execute_data in metadata (from workflow agents)
                        task_execute_data = result.metadata.get('execute_data')
                        if task_execute_data:
                            execute_data = task_execute_data
                            logger.info(
                                f"📋 Found execute_data from {task.agent_type.value}",
                                extra={"execute_data": execute_data}
                            )
                        
                        # Check for workflow_state in metadata (for multi-step continuations)
                        task_workflow_state = result.metadata.get('workflow_state')
                        if task_workflow_state:
                            workflow_state = task_workflow_state
                            workflow_name = result.metadata.get('workflow_name')
                            logger.info(
                                f"📋 Found workflow_state from {task.agent_type.value}",
                                extra={"workflow_state": workflow_state}
                            )
            
            # Calculate total time
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # Build result metadata including workflow state for multi-step continuation
            result_metadata = {
                "conversation_id": str(conversation_id),
                "language": language,
                "has_user_context": bool(user_context),
            }
            
            # Include workflow state if present (for multi-step workflows)
            if workflow_state:
                result_metadata["workflow_state"] = workflow_state
            if workflow_name:
                result_metadata["workflow_name"] = workflow_name
            
            # Build result
            return SupervisorMessageResult(
                content=response_content,
                agents_used=[t.agent_type.value for t in workflow_plan.tasks],
                sources=sources,
                agent_timings=agent_timings,
                workflow_type="authenticated_supervisor",
                task_count=len(workflow_plan.tasks),
                total_time_ms=total_time_ms,
                metadata=result_metadata,
                execute_data=execute_data,
            )
            
        except Exception as e:
            import traceback
            print(f"[SUPERVISOR WORKFLOW ERROR] {e}")
            traceback.print_exc()
            
            logger.error(
                f"Supervisor workflow failed: {e}",
                extra={
                    "conversation_id": str(conversation_id),
                    "error": str(e),
                },
                exc_info=True,
            )
            
            # Return error result
            total_time_ms = int((time.time() - start_time) * 1000)
            return SupervisorMessageResult(
                content=f"I encountered an issue processing your request. Please try again or rephrase your question.",
                agents_used=[],
                sources=[],
                agent_timings=[],
                workflow_type="authenticated_supervisor_error",
                task_count=0,
                total_time_ms=total_time_ms,
                metadata={
                    "error": str(e),
                    "conversation_id": str(conversation_id),
                },
            )
    
    def is_simple_greeting(self, message: str) -> bool:
        """
        Check if message is a simple greeting (fast-path).
        
        Simple greetings can skip LLM planning and go directly to chat agent.
        """
        import re
        message_lower = message.lower().strip()
        return bool(re.search(
            r"^(hi|hello|hey|hola|holi|oi|olá|buenos dias|buenas tardes|buenas noches|good (morning|afternoon|evening))(\s|$|!|\?|\.)*$",
            message_lower
        ))
    
    async def execute_fast_path_greeting(
        self,
        conversation_id: UUID,
        message: str,
        language: str = "en",
    ) -> SupervisorMessageResult:
        """
        Fast-path execution for simple greetings.
        
        Bypasses LLM planning and directly invokes ChatAgent.
        """
        from app.domain.ports.agent_squad.agent_gateway import AgentResponse
        
        start_time = time.time()
        
        try:
            # Build minimal context
            agent_context = ConversationContext(
                conversation_history=[],
                user_metadata={"language": language, "is_authenticated": True},
                session_metadata={},
            )
            
            # Execute chat agent directly
            response = await self._orchestrator.execute_agent(
                agent_type=AgentType.CHAT,
                message=message,
                conversation_context=agent_context,
            )
            
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract sources from AgentResponse (same as guest endpoint)
            sources = []
            provider_info = None
            if isinstance(response, AgentResponse):
                if response.sources:
                    sources = [s.to_dict() for s in response.sources]
                # Extract provider info from metadata
                if hasattr(response, 'metadata') and isinstance(response.metadata, dict):
                    provider_info = response.metadata.get('provider')
            
            return SupervisorMessageResult(
                content=response.content if hasattr(response, "content") else str(response),
                agents_used=["chat"],
                sources=sources,
                agent_timings=[{
                    "agent_type": "chat",
                    "task_description": "Greet user warmly",
                    "execution_time_ms": total_time_ms,
                    "status": "completed",
                    "provider": provider_info,
                }],
                workflow_type="fast_path_greeting",
                task_count=1,
                total_time_ms=total_time_ms,
                metadata={
                    "fast_path": True,
                    "conversation_id": str(conversation_id),
                },
            )
            
        except Exception as e:
            logger.error(f"Fast-path greeting failed: {e}", exc_info=True)
            # Fall back to regular execution
            return await self.execute(
                conversation_id=conversation_id,
                message=message,
                language=language,
            )

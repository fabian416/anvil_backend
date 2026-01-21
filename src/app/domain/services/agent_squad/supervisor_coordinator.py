"""
Supervisor Coordinator domain service - Coordinates multi-agent workflows.
"""

from typing import Protocol, TYPE_CHECKING, Any
from dataclasses import dataclass
from enum import Enum

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent

if TYPE_CHECKING:
    from app.domain.ports.agent_squad.agent_gateway import AgentResponse


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
    - result: AgentResponse | str | None from execution (set after completion)
    - status: TaskStatus (pending, in_progress, completed, failed)
    - error: str | None (error message if failed)
    - execution_time_ms: int | None (execution time in milliseconds, for debug)
    """
    agent_type: AgentType
    task_description: str
    depends_on: list[int]  # Task indices that must complete first
    status: TaskStatus = TaskStatus.PENDING
    result: "AgentResponse | str | None" = None  # AgentResponse (preferred) or str (fallback)
    error: str | None = None
    execution_time_ms: int | None = None  # Execution time in milliseconds (for debug)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_type": self.agent_type.value,
            "task_description": self.task_description,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
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
        
        # Detect if this is a simple multi-intent query (for faster model selection)
        is_simple_multi_intent = self._is_simple_multi_intent(message.value)
        
        # Call LLM for workflow planning
        # Use faster model for simple multi-intent queries to reduce latency
        response = await self._llm_client.plan_workflow(
            prompt=prompt,
            max_agents=self._max_agents,
        )
        
        # Parse workflow plan
        tasks = []
        import logging
        logger = logging.getLogger(__name__)
        
        for task_data in response.get("tasks", []):
            # Support both "agent_type" and "agent" for backward compatibility
            agent_type_str = task_data.get("agent_type") or task_data.get("agent", "chat")
            # Normalize agent names (hunter_ai -> HUNTER_AI, hunter-ai -> HUNTER_AI, etc.)
            agent_type_str = agent_type_str.replace("-", "_").replace(" ", "_").lower()
            
            logger.info(f"🔍 Parsing workflow task: agent_type_str={agent_type_str}, task_data={task_data}")
            
            try:
                agent_type = AgentType[agent_type_str.upper()]
                logger.info(f"✅ Mapped '{agent_type_str}' to AgentType.{agent_type.name}")
            except KeyError:
                # Default to CHAT if agent type not recognized
                logger.warning(f"⚠️ Unknown agent type '{agent_type_str}', defaulting to CHAT. Available: {[e.name for e in AgentType]}")
                agent_type = AgentType.CHAT
            
            task = AgentTask(
                agent_type=agent_type,
                task_description=task_data.get("task_description", ""),
                depends_on=task_data.get("depends_on", []),
            )
            tasks.append(task)
        
        # For multi-agent workflows (3+ tasks), ensure CHAT agent is added as final aggregator
        if len(tasks) >= 3:
            # Check if CHAT agent already exists as aggregator
            has_chat_aggregator = any(
                task.agent_type.value == "chat" and "aggregate" in task.task_description.lower()
                for task in tasks
            )
            
            if not has_chat_aggregator:
                # Add CHAT agent as final aggregator
                all_previous_indices = list(range(len(tasks)))
                chat_task = AgentTask(
                    agent_type=AgentType.CHAT,
                    task_description="Aggregate and summarize the results from all previous agents, removing duplicates and creating a single coherent response with only ONE disclaimer",
                    depends_on=all_previous_indices,
                )
                tasks.append(chat_task)
        
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
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Execute multi-agent workflow.
        
        Returns:
            Tuple of (response_content, sources_list, agent_timings_list)
        """
        """
        Execute multi-agent workflow.
        
        Handles both single-agent and multi-agent workflows:
        - Single-agent: Returns agent response directly
        - Multi-agent: Aggregates results from all agents
        
        Args:
            conversation_id: Conversation identifier
            workflow_plan: Workflow plan to execute
            conversation_context: Conversation context
            
        Returns:
            Final response (single agent response or aggregated multi-agent response)
        """
        # ✨ SINGLE-AGENT WORKFLOW ✨
        # If only one task, execute and return directly (no aggregation needed)
        if len(workflow_plan.tasks) == 1:
            task = workflow_plan.tasks[0]
            task.status = TaskStatus.IN_PROGRESS
            
            try:
                import time
                start_time = time.time()
                
                # Use the original user message, not task_description
                # Task description is for planning, but agents need the actual user message
                from app.domain.value_objects.message_content import MessageContent
                
                # Get original message from conversation context if available
                original_message = conversation_context.conversation_history[-1].get("content", task.task_description) if conversation_context.conversation_history else task.task_description
                
                result = await self._agent_executor.execute_agent(
                    conversation_id=conversation_id,
                    agent_type=task.agent_type,
                    message=MessageContent(original_message),
                    conversation_context=conversation_context,
                )
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                task.execution_time_ms = execution_time_ms
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                # Return content and sources from AgentResponse
                from app.domain.ports.agent_squad.agent_gateway import AgentResponse
                if isinstance(result, AgentResponse):
                    sources = [s.to_dict() for s in result.sources] if result.sources else []
                    # Include timing for single-agent workflow
                    provider_info = None
                    if isinstance(result, AgentResponse):
                        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                            provider_info = result.metadata.get('provider')
                        elif hasattr(result, 'provider'):
                            provider_info = result.provider
                    
                    # Extract tools_used from AgentResponse if available
                    tools_used_info = []
                    if isinstance(result, AgentResponse):
                        if hasattr(result, 'tools_used'):
                            tools_used_info = result.tools_used if result.tools_used else []
                    
                    # Extract data sources from AgentResponse sources
                    data_sources = []
                    if isinstance(result, AgentResponse) and hasattr(result, 'sources') and result.sources:
                        for source in result.sources:
                            source_type = getattr(source, 'source_type', None)
                            source_name = getattr(source, 'source_name', '')
                            provider = getattr(source, 'provider', '')
                            
                            # Map source types to readable names
                            if source_type:
                                if source_type.value == "api":
                                    data_sources.append(f"{source_name} API" if source_name else "External API")
                                elif source_type.value == "database":
                                    data_sources.append("Database")
                                elif source_type.value == "mcp_server":
                                    data_sources.append(f"MCP: {source_name}" if source_name else "MCP Server")
                                elif source_type.value == "blockchain":
                                    data_sources.append(f"Blockchain ({source_name})" if source_name else "Blockchain")
                                elif source_type.value == "knowledge_base":
                                    data_sources.append("Knowledge Base")
                                elif source_type.value == "rss_feed":
                                    data_sources.append("RSS Feed")
                                elif source_type.value == "social_media":
                                    data_sources.append(f"Social Media ({source_name})" if source_name else "Social Media")
                            
                            # Add specific providers (non-LLM)
                            if provider and provider not in ["Vertex AI", "DeepInfra"]:
                                if provider not in data_sources:
                                    data_sources.append(provider)
                    
                    # Build enhanced task description
                    task_desc_parts = [task.task_description]
                    
                    # Add tools information
                    if tools_used_info:
                        tool_names = []
                        for tool in tools_used_info:
                            tool_lower = tool.lower()
                            if "knowledge_base" in tool_lower or "knowledge" in tool_lower:
                                tool_names.append("Knowledge Base")
                            elif "web3" in tool_lower or "web3_client" in tool_lower:
                                tool_names.append("Web3Client")
                            elif "coingecko" in tool_lower:
                                tool_names.append("CoinGecko API")
                            elif "defillama" in tool_lower or "defi_llama" in tool_lower:
                                tool_names.append("DeFiLlama API")
                            elif "1inch" in tool_lower or "oneinch" in tool_lower:
                                tool_names.append("1inch API")
                            elif "morpho" in tool_lower:
                                tool_names.append("Morpho")
                            elif "graphrag" in tool_lower or "graph_rag" in tool_lower:
                                tool_names.append("GraphRAG")
                            elif "database" in tool_lower or "db" in tool_lower:
                                tool_names.append("Database")
                            elif "llm" in tool_lower or "llm_gateway" in tool_lower:
                                tool_names.append("LLM Gateway")
                            elif "perplexity" in tool_lower:
                                tool_names.append("Perplexity")
                            elif "thegraph" in tool_lower or "the_graph" in tool_lower:
                                tool_names.append("The Graph")
                            else:
                                tool_names.append(tool.replace("_", " ").title())
                        
                        if tool_names:
                            task_desc_parts.append(f"Tools: {', '.join(tool_names)}")
                    
                    # Add data sources information
                    if data_sources:
                        task_desc_parts.append(f"Data Sources: {', '.join(data_sources)}")
                    
                    enhanced_task_description = " | ".join(task_desc_parts)
                    
                    agent_timings = [{
                        "agent_type": task.agent_type.value,
                        "task_description": enhanced_task_description,  # Enhanced with tools and data sources
                        "execution_time_ms": task.execution_time_ms,
                        "status": task.status.value,
                        "provider": provider_info,  # Include LLM provider for debugging
                        "tools_used": tools_used_info if tools_used_info else [],  # Include tools used (API clients, etc.)
                    }] if hasattr(task, 'execution_time_ms') and task.execution_time_ms is not None else []
                    return result.content, sources, agent_timings
                # Fallback if result is already a string (shouldn't happen with updated port)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Agent executor returned non-AgentResponse: {type(result)}")
                return str(result), [], []
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                raise
        
        # ✨ MULTI-AGENT WORKFLOW WITH PARALLEL EXECUTION ✨
        # Execute independent tasks in parallel for better performance
        import logging
        import asyncio
        import time
        logger = logging.getLogger(__name__)
        
        from app.domain.value_objects.message_content import MessageContent
        
        async def execute_single_task(task: AgentTask) -> None:
            """Execute a single task and update its status."""
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"🔄 Executing task: {task.agent_type.value} - {task.task_description[:50]}...")
            
            try:
                start_time = time.time()
                
                # For CHAT agent aggregation tasks, pass aggregated content from other agents
                if task.agent_type.value == "chat" and "aggregate" in task.task_description.lower():
                    # Build aggregated message from previous agent responses
                    aggregated_content = self._build_aggregation_message(workflow_plan, task)
                    message_content = MessageContent(aggregated_content)
                else:
                    # Use the original user message for other agents
                    original_message = conversation_context.conversation_history[-1].get("content", task.task_description) if conversation_context.conversation_history else task.task_description
                    message_content = MessageContent(original_message)
                
                result = await self._agent_executor.execute_agent(
                    conversation_id=conversation_id,
                    agent_type=task.agent_type,
                    message=message_content,
                    conversation_context=conversation_context,
                )
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                task.execution_time_ms = execution_time_ms
                
                # Store full AgentResponse in task result
                task.result = result
                task.status = TaskStatus.COMPLETED
                logger.info(f"✅ Task completed: {task.agent_type.value} ({execution_time_ms}ms)")
                
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                logger.error(f"❌ Task failed: {task.agent_type.value} - {str(e)}", exc_info=True)
        
        def get_ready_tasks() -> list[AgentTask]:
            """Get all tasks that are ready to execute (dependencies satisfied)."""
            ready = []
            for task in workflow_plan.tasks:
                if task.status != TaskStatus.PENDING:
                    continue
                
                # Check dependencies
                dependencies_satisfied = all(
                    workflow_plan.tasks[dep_idx].status == TaskStatus.COMPLETED
                    for dep_idx in task.depends_on
                )
                
                if dependencies_satisfied:
                    ready.append(task)
            return ready
        
        # Execute tasks in waves - parallel execution of independent tasks
        max_iterations = len(workflow_plan.tasks) + 1  # Safety limit
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            ready_tasks = get_ready_tasks()
            
            if not ready_tasks:
                # No more tasks ready to execute
                break
            
            if len(ready_tasks) == 1:
                # Single task - execute directly
                await execute_single_task(ready_tasks[0])
            else:
                # Multiple tasks ready - execute in parallel
                logger.info(f"⚡ Executing {len(ready_tasks)} tasks in parallel: {[t.agent_type.value for t in ready_tasks]}")
                await asyncio.gather(*[execute_single_task(task) for task in ready_tasks])
        
        # Aggregate results
        final_response = await self._aggregate_results(workflow_plan)
        
        # Collect sources from all completed tasks
        all_sources = []
        for task in workflow_plan.tasks:
            if task.status == TaskStatus.COMPLETED and hasattr(task, 'result'):
                from app.domain.ports.agent_squad.agent_gateway import AgentResponse
                if isinstance(task.result, AgentResponse) and task.result.sources:
                    all_sources.extend([s.to_dict() for s in task.result.sources])
        
        # Collect timing information for debug mode
        agent_timings = []
        for task in workflow_plan.tasks:
            if hasattr(task, 'execution_time_ms') and task.execution_time_ms is not None:
                # Extract provider info from task result if available
                provider_info = None
                if hasattr(task, 'result') and task.result:
                    # AgentResponse has metadata dict
                    if hasattr(task.result, 'metadata') and isinstance(task.result.metadata, dict):
                        provider_info = task.result.metadata.get('provider')
                    # Fallback: check if result has provider attribute directly
                    elif hasattr(task.result, 'provider'):
                        provider_info = task.result.provider
                
                # Extract tools_used from AgentResponse if available
                tools_used_info = []
                if hasattr(task, 'result') and task.result:
                    from app.domain.ports.agent_squad.agent_gateway import AgentResponse
                    if isinstance(task.result, AgentResponse):
                        if hasattr(task.result, 'tools_used'):
                            tools_used_info = task.result.tools_used if task.result.tools_used else []
                
                # Extract data sources from AgentResponse sources
                data_sources = []
                if hasattr(task, 'result') and task.result:
                    from app.domain.ports.agent_squad.agent_gateway import AgentResponse
                    if isinstance(task.result, AgentResponse) and hasattr(task.result, 'sources') and task.result.sources:
                        for source in task.result.sources:
                            source_type = getattr(source, 'source_type', None)
                            source_name = getattr(source, 'source_name', '')
                            provider = getattr(source, 'provider', '')
                            
                            # Map source types to readable names
                            if source_type:
                                if source_type.value == "api":
                                    data_sources.append(f"{source_name} API" if source_name else "External API")
                                elif source_type.value == "database":
                                    data_sources.append("Database")
                                elif source_type.value == "mcp_server":
                                    data_sources.append(f"MCP: {source_name}" if source_name else "MCP Server")
                                elif source_type.value == "blockchain":
                                    data_sources.append(f"Blockchain ({source_name})" if source_name else "Blockchain")
                                elif source_type.value == "knowledge_base":
                                    data_sources.append("Knowledge Base")
                                elif source_type.value == "rss_feed":
                                    data_sources.append("RSS Feed")
                                elif source_type.value == "social_media":
                                    data_sources.append(f"Social Media ({source_name})" if source_name else "Social Media")
                                # Skip LLM as it's already in provider
                            
                            # Add specific providers (non-LLM)
                            if provider and provider not in ["Vertex AI", "DeepInfra"]:
                                if provider not in data_sources:
                                    data_sources.append(provider)
                
                # Build enhanced task description with tools and data sources
                task_desc_parts = [task.task_description]
                
                # Add tools information
                if tools_used_info:
                    tool_names = []
                    for tool in tools_used_info:
                        tool_lower = tool.lower()
                        if "knowledge_base" in tool_lower or "knowledge" in tool_lower:
                            tool_names.append("Knowledge Base")
                        elif "web3" in tool_lower or "web3_client" in tool_lower:
                            tool_names.append("Web3Client")
                        elif "coingecko" in tool_lower:
                            tool_names.append("CoinGecko API")
                        elif "defillama" in tool_lower or "defi_llama" in tool_lower:
                            tool_names.append("DeFiLlama API")
                        elif "1inch" in tool_lower or "oneinch" in tool_lower:
                            tool_names.append("1inch API")
                        elif "morpho" in tool_lower:
                            tool_names.append("Morpho")
                        elif "graphrag" in tool_lower or "graph_rag" in tool_lower:
                            tool_names.append("GraphRAG")
                        elif "database" in tool_lower or "db" in tool_lower:
                            tool_names.append("Database")
                        elif "llm" in tool_lower or "llm_gateway" in tool_lower:
                            tool_names.append("LLM Gateway")
                        elif "perplexity" in tool_lower:
                            tool_names.append("Perplexity")
                        elif "thegraph" in tool_lower or "the_graph" in tool_lower:
                            tool_names.append("The Graph")
                        else:
                            tool_names.append(tool.replace("_", " ").title())
                    
                    if tool_names:
                        task_desc_parts.append(f"Tools: {', '.join(tool_names)}")
                
                # Add data sources information
                if data_sources:
                    task_desc_parts.append(f"Data Sources: {', '.join(data_sources)}")
                
                enhanced_task_description = " | ".join(task_desc_parts)
                
                agent_timings.append({
                    "agent_type": task.agent_type.value,
                    "task_description": enhanced_task_description,  # Enhanced with tools and data sources
                    "execution_time_ms": task.execution_time_ms,
                    "status": task.status.value,
                    "provider": provider_info,  # Include LLM provider for debugging
                    "tools_used": tools_used_info if tools_used_info else [],  # Include tools used (API clients, etc.)
                })
        
        return final_response, all_sources, agent_timings
    
    def _build_planning_prompt(
        self,
        message: MessageContent,
        conversation_context: "ConversationContext",
        available_agents: list[AgentType],
    ) -> str:
        """
        Build optimized workflow planning prompt for LLM.
        
        Prompt Engineering Techniques Used:
        - Clear role definition
        - Structured output format with examples
        - Decision tree for routing
        - Few-shot examples for common patterns
        - Concise guidelines (reduced from ~100 lines to ~50)
        """
        agents_str = ", ".join([agent.value for agent in available_agents])
        
        # Build conversation history context (keep minimal)
        context_section = ""
        if conversation_context.conversation_history:
            recent = conversation_context.conversation_history[-3:]  # Last 3 only
            if recent:
                context_section = "\n<context>\n"
                for msg in recent:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:150]
                    if content:
                        context_section += f"{role}: {content}\n"
                context_section += "</context>\n"
        
        return f"""Route this request to the right agent(s). Output JSON only.

<request>{message.value}</request>
{context_section}
<agents>{agents_str}</agents>

<routing_rules>
SINGLE-AGENT (prefer for speed):
- Greetings/chat → "chat"
- Price queries (any language: price/precio/preço) → "hunter_ai"  
- DeFi education/explanations → "knowledge"
- Yield/APY/lending rates → "defi_yield"
- Risk/TVL analysis → "risk_analyzer"
- Gas prices → "gas_optimizer"
- Wallet actions (balance/send/receive/portfolio) → "guest_auth"

OFF-TOPIC (cooking, recipes, non-crypto):
→ "chat" with task: "Decline politely, redirect to DeFi"

MULTI-AGENT (only if truly needed):
- Add "chat" as final aggregator with depends_on all previous tasks
</routing_rules>

<examples>
User: "hola" → {{"tasks":[{{"agent_type":"chat","task_description":"Greet user warmly","depends_on":[]}}]}}
User: "btc price" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get BTC price","depends_on":[]}}]}}
User: "what is defi" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain DeFi","depends_on":[]}}]}}
User: "make a cake" → {{"tasks":[{{"agent_type":"chat","task_description":"Decline off-topic, I specialize in DeFi","depends_on":[]}}]}}
User: "my balance" → {{"tasks":[{{"agent_type":"guest_auth","task_description":"Handle restricted feature","depends_on":[]}}]}}
</examples>

Output format:
{{"tasks":[{{"agent_type":"...","task_description":"...","depends_on":[]}}]}}"""
    
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
    
    def _is_simple_multi_intent(self, message: str) -> bool:
        """
        Detect simple multi-intent patterns that can use faster LLM model.
        
        Simple patterns:
        - Greeting + price query
        - Greeting + knowledge query
        - Price query + knowledge query
        
        Args:
            message: User message text
            
        Returns:
            True if this is a simple multi-intent query
        """
        import re
        message_lower = message.lower()
        
        # Pattern: greeting + price
        greeting_price_pattern = r"(hi|hello|hey|hola|how are you).*(price|cost|worth).*(btc|eth|usdc|bitcoin|ethereum)"
        if re.search(greeting_price_pattern, message_lower):
            return True
        
        # Pattern: greeting + knowledge
        greeting_knowledge_pattern = r"(hi|hello|hey|hola|how are you).*(what is|explain|tell me about)"
        if re.search(greeting_knowledge_pattern, message_lower):
            return True
        
        # Pattern: price + knowledge
        price_knowledge_pattern = r"(price|cost|worth).*(btc|eth|usdc|bitcoin|ethereum).*(what is|explain|tell me about)"
        if re.search(price_knowledge_pattern, message_lower):
            return True
        
        return False
    
    async def _aggregate_results(
        self,
        workflow_plan: WorkflowPlan,
    ) -> str:
        """Aggregate results from all completed tasks."""
        completed_tasks = [
            task for task in workflow_plan.tasks
            if task.status == TaskStatus.COMPLETED
        ]
        
        failed_tasks = [
            task for task in workflow_plan.tasks
            if task.status == TaskStatus.FAILED
        ]
        
        if not completed_tasks:
            # Check if all tasks failed due to rate limiting
            rate_limit_errors = [
                task for task in failed_tasks
                if task.error and ("429" in str(task.error) or "rate limit" in str(task.error).lower() or "resource exhausted" in str(task.error).lower())
            ]
            
            if rate_limit_errors:
                return "I'm currently experiencing high demand. Please try again in a few moments. If the issue persists, the service may be temporarily unavailable."
            
            # Check if all tasks failed for other reasons
            if failed_tasks:
                error_summary = f"Unable to process your request. {len(failed_tasks)} task(s) failed."
                # Include first error for debugging (but sanitize it)
                if failed_tasks[0].error:
                    error_msg = str(failed_tasks[0].error)
                    if "429" in error_msg or "rate limit" in error_msg.lower():
                        error_summary = "I'm currently experiencing high demand. Please try again in a few moments."
                    elif len(error_msg) < 200:  # Only include short error messages
                        error_summary += f" Error: {error_msg[:100]}"
                return error_summary
            
            return "No tasks completed successfully. Please try again."
        
        # If only one task, return its content directly (no aggregation header)
        if len(completed_tasks) == 1:
            task = completed_tasks[0]
            from app.domain.ports.agent_squad.agent_gateway import AgentResponse
            if isinstance(task.result, AgentResponse):
                return task.result.content or "(No response)"
            elif isinstance(task.result, str):
                return task.result
            else:
                return str(task.result) if task.result else "(No response)"
        
        # Multiple tasks - check if CHAT agent is the final aggregator
        chat_task = None
        other_tasks = []
        for task in completed_tasks:
            if task.agent_type.value == "chat" and "aggregate" in task.task_description.lower():
                chat_task = task
            else:
                other_tasks.append(task)
        
        # If CHAT agent was used as aggregator, use its response (it should have summarized)
        if chat_task:
            from app.domain.ports.agent_squad.agent_gateway import AgentResponse
            if isinstance(chat_task.result, AgentResponse):
                return chat_task.result.content or "(No response)"
            elif isinstance(chat_task.result, str):
                return chat_task.result
            else:
                return str(chat_task.result) if chat_task.result else "(No response)"
        
        # No CHAT aggregator - intelligently combine responses with deduplication
        parts = []
        seen_content = set()  # Track seen content to avoid duplicates
        
        for task in completed_tasks:
            # Extract content from AgentResponse if needed
            from app.domain.ports.agent_squad.agent_gateway import AgentResponse
            if isinstance(task.result, AgentResponse):
                content = task.result.content or "(No response)"
            elif isinstance(task.result, str):
                content = task.result
            else:
                content = str(task.result) if task.result else "(No response)"
            
            # Simple deduplication: check if similar content already exists
            # Use first 100 chars as a signature to detect duplicates
            content_sig = content[:100].lower().strip()
            if content_sig and content_sig not in seen_content:
                parts.append(content)
                seen_content.add(content_sig)
        
        # Join with double newline for readability
        return "\n\n".join(parts)
    
    def _build_aggregation_message(
        self,
        workflow_plan: WorkflowPlan,
        chat_task: AgentTask,
    ) -> str:
        """Build message for CHAT agent to aggregate other agent responses."""
        # Get all completed tasks except the CHAT aggregator task
        other_tasks = [
            task for task in workflow_plan.tasks
            if task.status == TaskStatus.COMPLETED and task != chat_task
        ]
        
        if not other_tasks:
            # No other tasks to aggregate, use original message
            return chat_task.task_description
        
        # Build aggregation message
        parts = [
            "Aggregate and summarize the following responses from specialist agents.",
            "Remove duplicates, create a coherent single response, and include only ONE disclaimer.",
            "",
            "CRITICAL: FILTER OUT authentication/registration messages (like 'Account Required', 'Wallet Required') UNLESS the user explicitly asked about account requirements. These are error messages, not answers to informational queries.",
            "",
            "Agent Responses:",
            "",
        ]
        
        for i, task in enumerate(other_tasks, 1):
            from app.domain.ports.agent_squad.agent_gateway import AgentResponse
            if isinstance(task.result, AgentResponse):
                content = task.result.content or "(No response)"
            elif isinstance(task.result, str):
                content = task.result
            else:
                content = str(task.result) if task.result else "(No response)"
            
            # Skip authentication messages unless explicitly about auth
            if content and any(kw in content.lower() for kw in ["account required", "wallet required", "sign up", "create an account"]) and "what type" in chat_task.task_description.lower():
                # This is likely an error - skip it
                continue
            
            parts.append(f"--- Response from {task.agent_type.value.upper()} Agent ---")
            parts.append(content)
            parts.append("")  # Empty line between responses
        
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
    ) -> "AgentResponse":
        """Execute specific agent and return full AgentResponse with sources."""
        ...

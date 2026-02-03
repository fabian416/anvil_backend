# Agent Sessions Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Agent Sessions module includes a comprehensive multi-agent orchestration system with:
- **Domain Services**: Orchestrator, Context Manager, Supervisor Coordinator, Intent Classifier
- **Infrastructure Adapters**: 25+ agents, LLM clients, context storage
- **Application Interactors**: Message sending, workflow execution

**Total Service Components**: 80+ Python modules

---

## 1. Domain Services

### 1.1 AgentOrchestrator
**Path**: `src/app/domain/services/agent_squad/agent_orchestrator.py`

Routes messages to appropriate agents based on intent classification.

```python
class AgentOrchestrator:
    """
    Agent Orchestrator domain service.
    
    Responsibilities:
    - Route messages to correct agent based on intent
    - Use IntentClassifier for intent detection
    - Handle low-confidence routing (fallback to chat agent)
    - Validate agent availability (feature flags)
    - Log routing decisions for telemetry
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassifierPort,
        feature_flags: FeatureFlagsPort,
        agent_registry: dict[AgentType, AgentGateway] | None = None,
        confidence_threshold: float = 0.85,
        fallback_agent: AgentType = AgentType.CHAT,
    ): ...
    
    async def route_message(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentRoutingResult:
        """Route message to appropriate agent."""
        
    async def select_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int = 5,
    ) -> list[AgentType]:
        """Select multiple agents for complex multi-agent task."""
        
    async def execute_agent(
        self,
        agent_type: AgentType,
        message: str,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute specific agent with message and context."""
```

**Key Data Classes**:
```python
@dataclass
class IntentClassification:
    intent: str           # e.g., "swap_tokens", "analyze_risk"
    confidence: float     # 0.0-1.0
    agent_type: AgentType # Recommended agent
    reasoning: str        # Explanation

@dataclass
class AgentRoutingResult:
    agent_type: AgentType
    intent_classification: IntentClassification
    fallback_used: bool
```

---

### 1.2 ContextManager
**Path**: `src/app/domain/services/agent_squad/context_manager.py`

Manages conversation history and context for multi-turn conversations.

```python
class ContextManager:
    """
    Context Manager domain service.
    
    Responsibilities:
    - Preserve conversation history across agent calls
    - Manage context window (token limits)
    - Provide conversation summary for new agents
    - Support multi-turn conversations with context
    
    Context Strategies:
    - Full history: Keep all messages (up to limit)
    - Sliding window: Keep last N messages
    - Summary: Summarize old messages, keep recent full
    """
    
    def __init__(
        self,
        storage: ContextStoragePort,
        history_limit: int = 20,   # Maximum messages to keep
        token_limit: int = 8000,   # Maximum context tokens
    ): ...
    
    async def add_message(
        self,
        conversation_id: ConversationId,
        message_id: MessageId,
        role: str,
        content: str,
        agent_type: AgentType | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Add message to conversation history."""
    
    async def get_conversation_context(
        self,
        conversation_id: ConversationId,
        max_messages: int | None = None,
    ) -> ConversationContext:
        """Get conversation context for agent."""
    
    async def get_summary(
        self,
        conversation_id: ConversationId,
    ) -> str:
        """Get conversation summary (for new agents joining)."""
    
    async def estimate_token_count(
        self,
        conversation_id: ConversationId,
    ) -> int:
        """Estimate token count for conversation context."""
```

**Key Data Class**:
```python
@dataclass
class ConversationMessage:
    message_id: MessageId
    role: str           # "user", "assistant", "system"
    content: str
    agent_type: AgentType | None
    timestamp: datetime
    metadata: dict = field(default_factory=dict)
```

---

### 1.3 SupervisorCoordinator
**Path**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

Coordinates complex multi-agent workflows.

```python
class SupervisorCoordinator:
    """
    Supervisor Coordinator domain service.
    
    Responsibilities:
    - Coordinate complex multi-agent workflows
    - Break down complex tasks into agent subtasks
    - Manage task dependencies and execution order
    - Aggregate results from multiple agents
    - Handle partial failures
    
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
        llm_client: LLMClientPort,
        agent_executor: AgentExecutorPort,
        max_agents: int = 5,
        timeout_seconds: int = 120,
    ): ...
    
    async def create_workflow_plan(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
        available_agents: list[AgentType],
    ) -> WorkflowPlan:
        """Create multi-agent workflow plan for complex task."""
    
    async def execute_workflow(
        self,
        conversation_id: ConversationId,
        workflow_plan: WorkflowPlan,
        conversation_context: ConversationContext,
        original_message: str | None = None,
    ) -> tuple[str, list[dict], list[dict]]:
        """Execute multi-agent workflow with parallel execution."""
```

**Key Data Classes**:
```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentTask:
    agent_type: AgentType
    task_description: str
    depends_on: list[int]  # Task indices
    status: TaskStatus = TaskStatus.PENDING
    result: AgentResponse | str | None = None
    error: str | None = None
    execution_time_ms: int | None = None

@dataclass
class WorkflowPlan:
    tasks: list[AgentTask]
    execution_order: list[int]
    estimated_time_seconds: int
    
    def get_next_task(self) -> AgentTask | None: ...
    @property
    def is_complete(self) -> bool: ...
    @property
    def has_failures(self) -> bool: ...
```

**Parallel Execution**: Tasks without dependencies execute simultaneously for performance.

---

### 1.4 IntentClassifier
**Path**: `src/app/domain/services/agent_squad/intent_classifier.py`

Classifies user intent to route to appropriate agent.

```python
class IntentClassifier:
    """
    Intent classification for agent routing.
    
    Categories:
    - general_chat: Greetings, casual conversation
    - market_data: Price queries, market sentiment
    - swap_tokens: Token exchange requests
    - research_protocol: Protocol analysis
    - analyze_risk: Risk assessment
    - yield_farming: APY/yield queries
    - gas_optimization: Gas fee queries
    - off_topic: Non-DeFi topics
    """
    
    async def classify(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> IntentClassification: ...
    
    async def recommend_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int,
    ) -> list[AgentType]: ...
```

---

## 2. Application Layer Commands

### 2.1 SendAgentSquadMessage
**Path**: `src/app/application/agent_squad/commands/send_agent_squad_message.py`

Interactor for sending messages through Agent Squad.

```python
class SendAgentSquadMessage:
    """
    Command interactor for sending messages to Agent Squad.

    Responsibilities:
    - Validate user has access to requested agent (subscription tier)
    - Build conversation context from history
    - Route message to appropriate agent
    - Save messages to database
    - Track telemetry metrics
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
        message_repository: MessageRepository,
        feature_flags: FeatureFlagsGateway,
    ): ...

    async def execute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        force_agent: str | None = None,
    ) -> dict:
        """
        Execute the send message command.
        
        Returns:
            dict with:
                - user_message_id: UUID of saved user message
                - agent_message_id: UUID of saved agent message
                - agent_type: Agent that handled the message
                - intent_classification: Classified intent
                - content: Agent response content
                - tools_used: List of tools the agent used
                - latency_ms: Total processing time
                - tokens_used: Total tokens consumed
                - sources: Data sources used
        """
```

**Processing Flow**:
1. Build conversation context from history
2. Save user message to database
3. Add user message to Redis context storage
4. Route to agent (or use forced agent)
5. Execute agent
6. Save agent response to database with sources
7. Add agent message to Redis context
8. Calculate metrics (latency, tokens)
9. Track telemetry
10. Return response

---

### 2.2 ExecuteSupervisorWorkflow
**Path**: `src/app/application/agent_squad/commands/execute_supervisor_workflow.py`

Interactor for complex multi-agent workflows.

```python
class ExecuteSupervisorWorkflow:
    """
    Command for executing multi-agent supervisor workflows.
    
    Used for complex tasks that require multiple agents
    working together (e.g., portfolio creation, research).
    """
```

---

## 3. Infrastructure Adapters

### 3.1 ContextStorageRedis
**Path**: `src/app/infrastructure/adapters/agent_squad/context_storage_redis.py`

Redis-based conversation context storage.

```python
class ContextStorageRedis:
    """
    Context Storage Redis adapter.
    
    Redis Keys:
    - conversation:{id}:messages - List of messages (JSON)
    - conversation:{id}:metadata - Conversation metadata (JSON)
    - conversation:{id}:count - Message count (integer)
    
    TTL: 24 hours
    """
    
    async def add_message(conversation_id, message) -> None
    async def get_messages(conversation_id, limit) -> list[ConversationMessage]
    async def get_metadata(conversation_id) -> dict
    async def update_metadata(conversation_id, user_metadata, session_metadata) -> None
    async def clear_messages(conversation_id) -> None
    async def get_message_count(conversation_id) -> int
    async def remove_oldest_messages(conversation_id, count) -> None
```

---

### 3.2 Agent Implementations (25+ Agents)

**Core Agents** (`src/app/infrastructure/adapters/agent_squad/agents/`):
| Agent | Path | Description |
|-------|------|-------------|
| ChatAgent | `chat_agent.py` | General conversation |
| GuestAuthAgent | `guest_auth_agent.py` | Auth prompts for guests |
| KnowledgeAgent | `knowledge_agent.py` | Educational queries |
| HunterAIAgent | `hunter_ai_agent.py` | Market data & sentiment |
| ResearchAgent | `research_agent_perplexity.py` | Protocol research |
| ExecutionAgent | `execution_agent_privy.py` | Transaction execution |
| RiskAnalyzerAgent | `risk_analyzer_agent.py` | Risk assessment |
| PortfolioAgent | `portfolio_agent.py` | Portfolio optimization |
| TaxOptimizerAgent | `tax_optimizer_agent.py` | Tax optimization |
| DefiYieldAgent | `defi_yield_agent.py` | Yield farming |
| SecurityAuditorAgent | `security_auditor_agent_slither.py` | Security analysis |
| GasOptimizerAgent | `gas_optimizer_agent.py` | Gas optimization |
| WalletAgent | `wallet_agent.py` | Wallet management |
| TransactionHistoryAgent | `transaction_history_agent.py` | TX history |

**Workflow Agents** (`src/app/infrastructure/adapters/agent_squad/agents/workflows/`):
| Agent | Path | Description |
|-------|------|-------------|
| SwapWorkflowAgent | `swap_workflow_agent.py` | Multi-step swap |
| LendingWorkflowAgent | `lending_workflow_agent.py` | Multi-step lending |
| BuyWorkflowAgent | `buy_workflow_agent.py` | Fiat on-ramp |
| TransferWorkflowAgent | `transfer_workflow_agent.py` | Token transfer |
| MoneyMarketWorkflowAgent | `money_market_workflow_agent.py` | Compare & select |

**Enterprise Agents** (`src/app/infrastructure/adapters/agent_squad/agents/enterprise/`):
| Agent | Path | Description |
|-------|------|-------------|
| ComplianceMonitorAgent | `compliance_monitor_agent_chainalysis.py` | AML/KYC |
| MultisigCoordinatorAgent | `multisig_coordinator_agent_gnosis.py` | Treasury |
| AlertMonitoringAgent | `alert_monitoring_agent_forta.py` | Alerts |
| CrisisManagerAgent | `crisis_manager_agent_forta.py` | Emergency |

**Advanced Agents** (`src/app/infrastructure/adapters/agent_squad/agents/advanced/`):
| Agent | Path | Description |
|-------|------|-------------|
| BridgeCrosschainAgent | `bridge_crosschain_agent_axelar.py` | Cross-chain |
| LendingBorrowingAgent | `lending_borrowing_agent_aave.py` | Leverage |
| NFTAssetManagerAgent | `nft_asset_manager_agent_opensea.py` | NFT portfolio |
| DAOGovernanceAgent | `dao_governance_agent_snapshot.py` | Voting |

---

### 3.3 LLM Clients

**Path**: `src/app/infrastructure/adapters/agent_squad/`

| Client | Path | Description |
|--------|------|-------------|
| Vertex AI | `llm_client_vertex_ai.py` | Primary LLM (Google) |
| DeepInfra | `llm_client_deepinfra.py` | Fallback LLM |
| OpenAI | `llm_client_openai.py` | Alternative |
| With Fallback | `llm_client_with_fallback.py` | Auto-failover |
| Gateway | `llm_client_gateway_adapter.py` | Unified interface |

**Cost Optimization**: Vertex AI at $0.10/1M tokens vs OpenAI at $30/1M tokens (99% savings).

---

### 3.4 Feature Flags
**Path**: `src/app/infrastructure/adapters/agent_squad/feature_flags_config.py`

Controls agent availability by subscription tier.

```python
# Agent availability by tier
AGENT_TIERS = {
    "free": ["chat", "guest_auth", "knowledge", "hunter_ai", "gas_optimizer"],
    "pro": ["chat", "guest_auth", "knowledge", "hunter_ai", ..., "defi_yield"],
    "enterprise": ["chat", ..., "compliance_monitor", "crisis_manager", ...],
}
```

---

## 4. Domain Entities

### 4.1 AgentSession
**Path**: `src/app/domain/entities/agent_session.py`

```python
@dataclass(eq=False, kw_only=True)
class AgentSession(Entity[AgentSessionId]):
    """Agent session entity for tracking per-conversation agent state."""
    conversation_id: ConversationId
    agent_type: AgentType
    state: dict[str, Any]
    created_at: CreatedAt
    updated_at: UpdatedAt

    @classmethod
    def create(
        cls, 
        conversation_id: ConversationId, 
        agent_type: AgentType,
        state: dict[str, Any]
    ) -> "AgentSession": ...
```

---

### 4.2 AgentTelemetry
**Path**: `src/app/domain/entities/agent_squad/agent_telemetry.py`

```python
@dataclass
class AgentTelemetry:
    """Performance metrics for agent execution."""
    id: UUID
    conversation_id: UUID
    user_id: UUID
    agent_type: AgentType
    intent_category: str | None
    latency_ms: int
    tokens_used: int | None
    tools_used: list[str]
    success: bool
    created_at: datetime
```

---

## 5. Ports (Interfaces)

### 5.1 AgentGateway
**Path**: `src/app/domain/ports/agent_squad/agent_gateway.py`

```python
class AgentGateway(Protocol):
    """Base interface for all 25 agents."""
    
    @property
    def agent_type(self) -> AgentType: ...
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse: ...
    
    async def is_available(self) -> bool: ...
```

---

### 5.2 ContextStorageGateway
**Path**: `src/app/domain/ports/agent_squad/context_storage_gateway.py`

```python
class ContextStorageGateway(Protocol):
    """Interface for context storage (Redis/PostgreSQL)."""
    
    async def add_message(conversation_id, message) -> None
    async def get_messages(conversation_id, limit) -> list[ConversationMessage]
    async def get_metadata(conversation_id) -> dict
    async def update_metadata(conversation_id, user_metadata, session_metadata) -> None
    async def clear_messages(conversation_id) -> None
```

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AGENT SESSIONS ARCHITECTURE                                       │
│                                                                                                      │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │                                   PRESENTATION LAYER                                              ││
│ │                                                                                                   ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                  Unified Chat API (/api/v1/conversations/{id}/messages)                    │ ││
│ │  │                              + Guest Chat (/api/v1/guest/chat)                             │ ││
│ │  └─────────────────────────────────────────┬──────────────────────────────────────────────────┘ ││
│ └────────────────────────────────────────────┼──────────────────────────────────────────────────────┘│
│                                              │                                                       │
│                                              ▼                                                       │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │                                    APPLICATION LAYER                                              ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                              SendAgentSquadMessage Command                                   │ ││
│ │  │                                                                                              │ ││
│ │  │  1. Build conversation context    4. Route to agent (or forced)   7. Add to Redis           │ ││
│ │  │  2. Save user message             5. Execute agent                8. Calculate metrics       │ ││
│ │  │  3. Add to Redis context          6. Save agent response          9. Track telemetry         │ ││
│ │  └─────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                           ExecuteSupervisorWorkflow Command                                  │ ││
│ │  │                              (Complex multi-agent tasks)                                     │ ││
│ │  └─────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                              │                                                       │
│                                              ▼                                                       │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │                                      DOMAIN LAYER                                                 ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                                   Domain Services                                            │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌───────────────────────┐  ┌────────────────────────┐  ┌──────────────────────────────┐   │ ││
│ │  │  │   AgentOrchestrator   │  │    ContextManager      │  │   SupervisorCoordinator      │   │ ││
│ │  │  │                       │  │                        │  │                              │   │ ││
│ │  │  │ • route_message()     │  │ • add_message()        │  │ • create_workflow_plan()     │   │ ││
│ │  │  │ • execute_agent()     │  │ • get_context()        │  │ • execute_workflow()         │   │ ││
│ │  │  │ • select_agents()     │  │ • get_summary()        │  │ • aggregate_results()        │   │ ││
│ │  │  │                       │  │ • estimate_tokens()    │  │ • parallel_execution()       │   │ ││
│ │  │  └───────────┬───────────┘  └────────────┬───────────┘  └──────────────┬───────────────┘   │ ││
│ │  │              │                           │                             │                    │ ││
│ │  │              │         ┌─────────────────┴─────────────────┐           │                    │ ││
│ │  │              │         │        IntentClassifier           │           │                    │ ││
│ │  │              │         │                                   │           │                    │ ││
│ │  │              │         │ • classify() → IntentClassification│          │                    │ ││
│ │  │              │         │ • recommend_agents_for_complex()   │          │                    │ ││
│ │  │              │         └───────────────────────────────────┘           │                    │ ││
│ │  └──────────────┼─────────────────────────────────────────────────────────┼────────────────────┘ ││
│ │                 │                                                         │                      ││
│ │  ┌──────────────┼─────────────────────────────────────────────────────────┼────────────────────┐ ││
│ │  │              ▼                                                         ▼                    │ ││
│ │  │                                     Entities                                                │ ││
│ │  │                                                                                             │ ││
│ │  │  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌────────────────────────┐   │ ││
│ │  │  │     AgentSession         │  │    AgentTelemetry        │  │   ConversationContext  │   │ ││
│ │  │  │                          │  │                          │  │                        │   │ ││
│ │  │  │ • conversation_id        │  │ • agent_type             │  │ • conversation_history │   │ ││
│ │  │  │ • agent_type             │  │ • latency_ms             │  │ • user_metadata        │   │ ││
│ │  │  │ • state (JSONB)          │  │ • tokens_used            │  │ • session_metadata     │   │ ││
│ │  │  │ • created_at/updated_at  │  │ • tools_used             │  │                        │   │ ││
│ │  │  └──────────────────────────┘  │ • success                │  └────────────────────────┘   │ ││
│ │  │                                └──────────────────────────┘                                │ ││
│ │  └────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                              │                                                       │
│                                              ▼                                                       │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │                                   INFRASTRUCTURE LAYER                                            ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                                    Agent Implementations                                     │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │ ││
│ │  │  │                           Core Agents (12)                                           │   │ ││
│ │  │  │  ChatAgent • GuestAuthAgent • KnowledgeAgent • HunterAIAgent • ResearchAgent        │   │ ││
│ │  │  │  ExecutionAgent • RiskAnalyzerAgent • PortfolioAgent • TaxOptimizerAgent            │   │ ││
│ │  │  │  DefiYieldAgent • SecurityAuditorAgent • GasOptimizerAgent                          │   │ ││
│ │  │  └─────────────────────────────────────────────────────────────────────────────────────┘   │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │ ││
│ │  │  │                         Workflow Agents (5)                                          │   │ ││
│ │  │  │  SwapWorkflow • LendingWorkflow • BuyWorkflow • TransferWorkflow • MoneyMarket      │   │ ││
│ │  │  └─────────────────────────────────────────────────────────────────────────────────────┘   │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │ ││
│ │  │  │                         Enterprise Agents (8)                                        │   │ ││
│ │  │  │  ComplianceMonitor • MultisigCoordinator • AlertMonitoring • CrisisManager          │   │ ││
│ │  │  │  BridgeCrosschain • LendingBorrowing • NFTAssetManager • DAOGovernance              │   │ ││
│ │  │  └─────────────────────────────────────────────────────────────────────────────────────┘   │ ││
│ │  └─────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                                    LLM Clients                                               │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────────────┐    │ ││
│ │  │  │  Vertex AI (Primary)│  │  DeepInfra (Fallback)│  │   LLMClientWithFallback        │    │ ││
│ │  │  │                     │  │                     │  │                                 │    │ ││
│ │  │  │  $0.10/1M tokens    │  │  Backup provider    │  │  Auto-failover with retry      │    │ ││
│ │  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────────────────┘    │ ││
│ │  └─────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                                   Context Storage                                            │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │ ││
│ │  │  │                        ContextStorageRedis                                           │   │ ││
│ │  │  │                                                                                      │   │ ││
│ │  │  │  Redis Keys:                                                                         │   │ ││
│ │  │  │  • conversation:{id}:messages  (List of messages, JSON)                              │   │ ││
│ │  │  │  • conversation:{id}:metadata  (User & session metadata)                             │   │ ││
│ │  │  │  • conversation:{id}:count     (Message count)                                       │   │ ││
│ │  │  │                                                                                      │   │ ││
│ │  │  │  TTL: 24 hours                                                                       │   │ ││
│ │  │  └─────────────────────────────────────────────────────────────────────────────────────┘   │ ││
│ │  └─────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ │                                                                                                   ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                                  Database Mappings                                           │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐ │ ││
│ │  │  │  agent_sessions   │  │  agent_telemetry  │  │  compliance_logs  │  │ multisig_props  │ │ ││
│ │  │  │                   │  │                   │  │  (Enterprise)     │  │ (Enterprise)    │ │ ││
│ │  │  └───────────────────┘  └───────────────────┘  └───────────────────┘  └─────────────────┘ │ ││
│ │  │                                                                                              │ ││
│ │  │  ┌───────────────────┐                                                                      │ ││
│ │  │  │  crisis_events    │                                                                      │ ││
│ │  │  │  (Enterprise)     │                                                                      │ ││
│ │  │  └───────────────────┘                                                                      │ ││
│ │  └─────────────────────────────────────────────────────────────────────────────────────────────┘ ││
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- **Domain Services**: `src/app/domain/services/agent_squad/`
- **Application Commands**: `src/app/application/agent_squad/commands/`
- **Agents**: `src/app/infrastructure/adapters/agent_squad/agents/`
- **LLM Clients**: `src/app/infrastructure/adapters/agent_squad/llm_client_*.py`
- **Context Storage**: `src/app/infrastructure/adapters/agent_squad/context_storage_redis.py`
- **Database Mappings**: `src/app/infrastructure/persistence_sqla/mappings/agent_session.py`

# Agent Orchestrator - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de Orquestación de Agentes proporciona:

1. **18 Specialized Agents**: Core (10) + Enterprise (8) agent types
2. **Intent Classification**: LLM-powered routing to optimal agent
3. **Multi-Agent Workflows**: Supervisor-coordinated complex tasks
4. **Agent Router**: Keyword-based quick routing for common queries
5. **Voting & Consensus**: Multi-agent decision making
6. **Fallback Chains**: Resilient routing with automatic failover
7. **Performance Tracking**: Agent metrics and efficiency scoring
8. **Custom Agents**: User-defined agent configurations
9. **Agent Library**: Pre-configured specialist agents

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           AGENT ORCHESTRATION ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   User Message  │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │    Intent Classifier     │
                              │  (LLM-based: gpt-4o-mini)│
                              └──────────┬───────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
           Simple Query           Complex Query        Low Confidence
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌─────────────┐     ┌─────────────────┐    ┌─────────────┐
           │   Agent     │     │   Supervisor    │    │   Fallback  │
           │ Orchestrator│     │  Coordinator    │    │    Chain    │
           └──────┬──────┘     └────────┬────────┘    └──────┬──────┘
                  │                     │                    │
                  ▼                     ▼                    ▼
           ┌─────────────┐     ┌─────────────────┐    ┌─────────────┐
           │Single Agent │     │  Multi-Agent    │    │  Priority   │
           │  Execution  │     │   Workflow      │    │   Routing   │
           └──────┬──────┘     └────────┬────────┘    └──────┬──────┘
                  │                     │                    │
                  └─────────────────────┼────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────────┐
                              │      Agent Response      │
                              └──────────────────────────┘
```

---

## Agent Types (18 Agents)

### Core User-Facing Agents (10)

| Agent | Type | Description |
|-------|------|-------------|
| **Chat** | `CHAT` | General conversation |
| **Hunter AI** | `HUNTER_AI` | Market sentiment & predictions |
| **Research** | `RESEARCH` | Deep protocol analysis |
| **Execution** | `EXECUTION` | Transaction execution (Privy wallet) |
| **Risk Analyzer** | `RISK_ANALYZER` | Risk assessment & scoring |
| **Portfolio** | `PORTFOLIO` | Portfolio optimization & rebalancing |
| **Tax Optimizer** | `TAX_OPTIMIZER` | Tax-loss harvesting & reporting |
| **DeFi Yield** | `DEFI_YIELD` | Yield farming & APY analysis |
| **Security Auditor** | `SECURITY_AUDITOR` | Smart contract security analysis |
| **Gas Optimizer** | `GAS_OPTIMIZER` | Gas fee optimization & timing |

### Enterprise Agents (8)

| Agent | Type | Description |
|-------|------|-------------|
| **Compliance Monitor** | `COMPLIANCE_MONITOR` | AML/KYC, regulatory compliance |
| **Multisig Coordinator** | `MULTISIG_COORDINATOR` | Multi-sig treasury management |
| **Alert Monitoring** | `ALERT_MONITORING` | Real-time alerts, anomaly detection |
| **Crisis Manager** | `CRISIS_MANAGER` | Emergency response, circuit breaker |
| **Bridge Crosschain** | `BRIDGE_CROSSCHAIN` | Layer 2, cross-chain operations |
| **Lending Borrowing** | `LENDING_BORROWING` | Leverage, collateral optimization |
| **NFT Asset Manager** | `NFT_ASSET_MANAGER` | NFT portfolio, valuation |
| **DAO Governance** | `DAO_GOVERNANCE` | Voting, proposals, delegation |

**Location**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core User-Facing Agents (10)
    CHAT = "chat"
    HUNTER_AI = "hunter_ai"
    RESEARCH = "research"
    EXECUTION = "execution"
    RISK_ANALYZER = "risk_analyzer"
    PORTFOLIO = "portfolio"
    TAX_OPTIMIZER = "tax_optimizer"
    DEFI_YIELD = "defi_yield"
    SECURITY_AUDITOR = "security_auditor"
    GAS_OPTIMIZER = "gas_optimizer"
    
    # Enterprise Agents (8)
    COMPLIANCE_MONITOR = "compliance_monitor"
    MULTISIG_COORDINATOR = "multisig_coordinator"
    ALERT_MONITORING = "alert_monitoring"
    CRISIS_MANAGER = "crisis_manager"
    BRIDGE_CROSSCHAIN = "bridge_crosschain"
    LENDING_BORROWING = "lending_borrowing"
    NFT_ASSET_MANAGER = "nft_asset_manager"
    DAO_GOVERNANCE = "dao_governance"
    
    @classmethod
    def is_enterprise_agent(cls, agent_type) -> bool:
        """Check if agent requires enterprise subscription."""
        ...
```

---

## Intent Classification

### Intent Classifier Domain Service

**Location**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
class IntentClassifier:
    """
    Classifies user intent and recommends appropriate agent.
    
    Uses LLM (gpt-4o-mini) for fast, accurate classification.
    """
    
    # Intent to Agent mapping
    INTENT_AGENT_MAP = {
        # Core user intents
        "general_chat": AgentType.CHAT,
        "market_sentiment": AgentType.HUNTER_AI,
        "research_protocol": AgentType.RESEARCH,
        "swap_tokens": AgentType.EXECUTION,
        "analyze_risk": AgentType.RISK_ANALYZER,
        "optimize_portfolio": AgentType.PORTFOLIO,
        "tax_optimization": AgentType.TAX_OPTIMIZER,
        "find_yield": AgentType.DEFI_YIELD,
        "audit_contract": AgentType.SECURITY_AUDITOR,
        "optimize_gas": AgentType.GAS_OPTIMIZER,
        
        # Enterprise intents
        "check_compliance": AgentType.COMPLIANCE_MONITOR,
        "manage_multisig": AgentType.MULTISIG_COORDINATOR,
        "setup_alerts": AgentType.ALERT_MONITORING,
        "crisis_response": AgentType.CRISIS_MANAGER,
        "bridge_tokens": AgentType.BRIDGE_CROSSCHAIN,
        "borrow_assets": AgentType.LENDING_BORROWING,
        "manage_nfts": AgentType.NFT_ASSET_MANAGER,
        "dao_voting": AgentType.DAO_GOVERNANCE,
    }
    
    async def classify(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> IntentClassification:
        """Classify user intent from message."""
        ...
    
    async def recommend_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int = 5,
    ) -> list[AgentType]:
        """Recommend multiple agents for complex task."""
        ...
```

### IntentClassification Result

```python
@dataclass
class IntentClassification:
    intent: str           # e.g., "swap_tokens", "analyze_risk"
    confidence: float     # 0.0 - 1.0
    agent_type: AgentType # Recommended agent
    reasoning: str        # Why this agent was selected
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence >= 0.85."""
        return self.confidence >= 0.85
```

---

## Agent Orchestrator

### Domain Service

**Location**: `src/app/domain/services/agent_squad/agent_orchestrator.py`

```python
class AgentOrchestrator:
    """
    Routes messages to correct agent based on intent.
    
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
        agent_registry: dict[AgentType, AgentGateway],
        confidence_threshold: float = 0.85,
        fallback_agent: AgentType = AgentType.CHAT,
    ): ...
    
    async def route_message(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentRoutingResult:
        """
        Route message to appropriate agent.
        
        Process:
        1. Classify user intent using IntentClassifier
        2. Check confidence threshold (default 0.85)
        3. Validate agent availability (feature flags)
        4. Return routing decision
        """
        ...
    
    async def select_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int = 5,
    ) -> list[AgentType]:
        """Select multiple agents for complex multi-agent task."""
        ...
    
    async def execute_agent(
        self,
        agent_type: AgentType,
        message: str,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute specific agent with message and context."""
        ...
```

### AgentRoutingResult

```python
@dataclass
class AgentRoutingResult:
    agent_type: AgentType
    intent_classification: IntentClassification
    fallback_used: bool
```

---

## Supervisor Coordinator (Multi-Agent Workflows)

### Domain Service

**Location**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

Coordinates complex multi-agent workflows for tasks requiring multiple specialists.

```python
class SupervisorCoordinator:
    """
    Coordinates complex multi-agent workflows.
    
    Example Workflow:
    User: "Create a balanced DeFi portfolio"
    
    Supervisor Plan:
    1. Research agent: Find top protocols
    2. Risk analyzer: Assess protocol risks
    3. Portfolio agent: Create optimal allocation
    4. Tax optimizer: Suggest tax-efficient timing
    5. Chat agent: Summarize recommendations
    """
    
    async def create_workflow_plan(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
        available_agents: list[AgentType],
    ) -> WorkflowPlan:
        """Create multi-agent workflow plan for complex task."""
        ...
    
    async def execute_workflow(
        self,
        conversation_id: ConversationId,
        workflow_plan: WorkflowPlan,
        conversation_context: ConversationContext,
    ) -> str:
        """Execute multi-agent workflow."""
        ...
```

### WorkflowPlan & AgentTask

```python
@dataclass
class AgentTask:
    agent_type: AgentType
    task_description: str
    depends_on: list[int]  # Task indices that must complete first
    status: TaskStatus     # PENDING, IN_PROGRESS, COMPLETED, FAILED
    result: str | None
    error: str | None

@dataclass
class WorkflowPlan:
    tasks: list[AgentTask]
    execution_order: list[int]
    estimated_time_seconds: int
    
    def get_next_task(self) -> AgentTask | None:
        """Get next pending task with satisfied dependencies."""
        ...
    
    @property
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        ...
```

### Execute Supervisor Workflow Command

**Location**: `src/app/application/agent_squad/commands/execute_supervisor_workflow.py`

```python
class ExecuteSupervisorWorkflow:
    """Command interactor for executing supervisor-coordinated workflows."""
    
    async def execute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        complex_task: str,
        max_agents: int = 5,
    ) -> dict:
        """
        Returns:
            - workflow_id: UUID
            - plan: List of agents and their tasks
            - tasks: List of task results
            - final_synthesis: Aggregated response
            - total_latency_ms: Total execution time
            - agents_used: Number of agents
            - tokens_used: Total tokens consumed
        """
```

---

## Agent Router (Keyword-Based Quick Routing)

### Infrastructure Implementation

**Location**: `src/app/infrastructure/agno/agent_router.py`

Fast keyword-based routing for common DeFi queries without LLM call.

```python
class AgentRouter:
    """
    Intelligent router for specialized DeFi agents.
    
    Routing Logic:
    - Trading queries → TradingAgent (1inch, Curve)
    - Lending queries → LendingAgent (Aave, Morpho)
    - Perpetual queries → PerpetualAgent (Hyperliquid)
    - Analytics queries → AnalyticsAgent (DeFiLlama)
    - Portfolio queries → PortfolioAgent
    - Multi-domain queries → Orchestrates multiple agents
    """
    
    # Intent keywords for fast routing
    intent_keywords = {
        AgentType.TRADING: [
            "swap", "trade", "exchange", "buy", "sell",
            "price", "quote", "route", "dex", "1inch",
        ],
        AgentType.LENDING: [
            "lend", "borrow", "supply", "withdraw",
            "collateral", "health factor", "aave", "morpho",
        ],
        AgentType.PERPETUAL: [
            "perpetual", "perp", "futures", "leverage",
            "long", "short", "funding rate", "hyperliquid",
        ],
        AgentType.ANALYTICS: [
            "tvl", "protocol", "yield", "apy", "farm",
            "compare", "analysis", "defillama",
        ],
        AgentType.PORTFOLIO: [
            "balance", "portfolio", "positions", "holdings",
            "wallet", "assets", "my", "show me",
        ],
    }
    
    def classify_intent(self, query: str) -> tuple[AgentType, float]:
        """Classify user intent based on query keywords."""
        ...
    
    async def route(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        stream: bool = False,
    ):
        """Route query to appropriate agent(s)."""
        ...
```

---

## Agent Orchestration Service (Advanced Features)

### Application Service

**Location**: `src/app/application/chat/services/agent_orchestration_service.py`

Provides advanced multi-agent coordination features.

#### Multi-Agent Voting

```python
async def conduct_multi_agent_vote(
    self,
    query: str,
    agent_names: List[str],
    conversation: Optional[Conversation] = None,
    strategy: VotingStrategy = VotingStrategy.WEIGHTED,
) -> Tuple[str, VotingRound]:
    """
    Multiple agents vote on best response.
    
    Example:
        User: "What's the risk of this Aave position?"
        Agents vote:
          - risk_analyzer: "High risk" (confidence: 0.85)
          - yield_optimizer: "Moderate risk" (confidence: 0.75)
          - portfolio_manager: "High risk" (confidence: 0.90)
        Winner: "High risk" (2 votes, avg confidence 0.875)
    """
```

#### Agent Debates

```python
async def conduct_agent_debate(
    self,
    query: str,
    agent_names: List[str],
    max_rounds: int = 3,
    conversation: Optional[Conversation] = None,
) -> AgentDebate:
    """
    Structured debate between agents.
    
    Phases:
    1. Opening Statements
    2. Arguments
    3. Rebuttals
    4. Synthesis
    5. Final Vote
    
    Example:
        Query: "Should I enter this leveraged farming position?"
        - risk_analyzer: "High risk due to IL and liquidation"
        - yield_optimizer: "High reward (45% APY) worth calculated risk"
        Synthesis: "Enter with 30% position size, hedge with options"
    """
```

#### Fallback Routing

```python
async def execute_with_fallback(
    self,
    query: str,
    fallback_chain: FallbackChain,
    conversation: Optional[Conversation] = None,
) -> Tuple[str, FallbackChain]:
    """
    Execute query with intelligent fallback routing.
    
    Tries agents in priority order until successful response.
    Falls back on timeout, error, or low confidence.
    
    Example:
        Chain: primary (risk_analyzer) → secondary (yield_optimizer) → tertiary (general)
        Attempt 1: risk_analyzer times out → FALLBACK
        Attempt 2: yield_optimizer responds with 40% confidence → FALLBACK
        Attempt 3: general agent responds with 75% confidence → SUCCESS
    """
```

#### Custom Agent Management

```python
async def create_custom_agent(
    self,
    user_id: UUID,
    config: CustomAgentConfig,
) -> CustomAgentConfig:
    """Create user-defined custom agent configuration."""

async def get_custom_agents(
    self,
    user_id: UUID,
    active_only: bool = True,
) -> List[CustomAgentConfig]:
    """Get user's custom agents."""
```

---

## Value Objects

### Voting Strategy

**Location**: `src/app/domain/value_objects/chat/orchestration.py`

```python
class VotingStrategy(Enum):
    MAJORITY = "majority"            # Simple majority wins
    WEIGHTED = "weighted"            # Weight by agent performance
    UNANIMOUS = "unanimous"          # All agents must agree
    RANKED_CHOICE = "ranked_choice"  # Ranked preference voting
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Min confidence required
```

### Fallback Reason

```python
class FallbackReason(Enum):
    TIMEOUT = "timeout"
    ERROR = "error"
    LOW_CONFIDENCE = "low_confidence"
    UNAVAILABLE = "unavailable"
    OVERLOADED = "overloaded"
```

### Agent Performance Metrics

```python
@dataclass
class AgentPerformanceMetrics:
    agent_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    avg_confidence: float = 0.0
    avg_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    uptime_percentage: float = 100.0
    
    def get_efficiency_score(self) -> float:
        """
        Calculate overall efficiency score (0-100).
        Combines success rate, speed, and confidence.
        """
        success_score = self.get_success_rate()
        speed_score = max(0, 100 - (self.avg_response_time_ms / 100))
        confidence_score = self.avg_confidence * 100
        return (success_score * 0.4) + (speed_score * 0.3) + (confidence_score * 0.3)
```

### Custom Agent Config

```python
@dataclass
class CustomAgentConfig:
    config_id: UUID
    name: str
    description: str
    system_prompt: str
    capabilities: List[AgentCapability]
    temperature: float = 0.7
    max_tokens: int = 1000
    personality_traits: Dict[str, float]  # e.g., {"formal": 0.8}
    expertise_areas: List[str]
    response_style: str  # "concise", "balanced", "detailed"
    preferred_llm_provider: str = "openai"
    fallback_llm_provider: Optional[str] = None
    is_active: bool = True
    created_by_user_id: UUID
    
    def to_llm_prompt(self) -> str:
        """Convert configuration to LLM system prompt."""
        ...
    
    def validate(self) -> List[str]:
        """Validate agent configuration."""
        ...
```

---

## Agent Library (Pre-Configured Agents)

### Registry

**Location**: `src/app/application/agents/library/agent_registry.py`

```python
class AgentLibraryRegistry:
    """
    Central registry for all pre-configured agents.
    
    Available Agents:
    - DeFi Specialists (5):
      - curve_finance_expert
      - aave_specialist
      - uniswap_expert
      - yearn_strategist
      - compound_advisor
    
    - Technical Experts (5):
      - smart_contract_auditor
      - gas_optimization_expert
      - mev_protection_advisor
      - bridge_specialist
      - wallet_security_expert
    """
    
    def get_agent(self, agent_id: str) -> Optional[CustomAgentConfig]: ...
    def get_all_agents(self) -> List[CustomAgentConfig]: ...
    def get_agents_by_category(self, category: AgentCategory) -> List[CustomAgentConfig]: ...
    def get_agents_by_tag(self, tag: str) -> List[CustomAgentConfig]: ...
    def get_agents_by_protocol(self, protocol: str) -> List[CustomAgentConfig]: ...
    def search_agents(self, query: str, category: Optional[AgentCategory] = None) -> List[CustomAgentConfig]: ...
    def get_library_stats(self) -> Dict: ...
```

### Usage

```python
from app.application.agents.library.agent_registry import get_agent_registry

registry = get_agent_registry()

# Get specific agent
aave_agent = registry.get_agent("aave_specialist")

# Get all DeFi specialists
defi_agents = registry.get_agents_by_category(AgentCategory.DEFI_SPECIALIST)

# Search agents
security_agents = registry.search_agents("security")

# Get library stats
stats = registry.get_library_stats()
# {"total_agents": 10, "defi_specialists": 5, "technical_experts": 5, ...}
```

---

## Dependency Injection

### Domain Provider

**Location**: `src/app/setup/ioc/agent_squad_domain.py`

```python
class AgentSquadDomainProvider(Provider):
    scope = Scope.REQUEST
    
    @provide
    def provide_intent_classifier(
        self,
        llm_client: LLMClientGateway,
    ) -> IntentClassifier:
        return IntentClassifier(
            llm_client=llm_client,
            classification_model="gpt-4o-mini",
        )
    
    @provide
    def provide_agent_orchestrator(
        self,
        intent_classifier: IntentClassifier,
        feature_flags: FeatureFlagsGateway,
        agent_registry: dict[AgentType, AgentGateway],
    ) -> AgentOrchestrator:
        return AgentOrchestrator(
            intent_classifier=intent_classifier,
            feature_flags=feature_flags,
            agent_registry=agent_registry,
        )
    
    @provide
    def provide_supervisor_coordinator(
        self,
        llm_client: LLMClientGateway,
    ) -> SupervisorCoordinator:
        return SupervisorCoordinator(
            llm_client=llm_client,
            agent_executor=agent_executor,
        )
```

---

## Routing Flow

### Single Agent Routing

```
User Message → IntentClassifier → AgentOrchestrator → Single Agent → Response
                    │
                    ├─ confidence >= 0.85 → Route to recommended agent
                    │
                    └─ confidence < 0.85 → Fallback to CHAT agent
```

### Multi-Agent Workflow

```
Complex Task → SupervisorCoordinator → WorkflowPlan → Execute Tasks → Aggregate → Response
                       │
                       ├─ Plan: Break task into subtasks
                       │
                       ├─ Execute: Run agents in dependency order
                       │
                       └─ Aggregate: Synthesize all responses
```

### Fallback Chain

```
Query → FallbackChain → Agent 1 (Primary)
                            │
                            ├─ Success → Return Response
                            │
                            └─ Timeout/Error/Low Confidence
                                     │
                                     ▼
                            Agent 2 (Secondary)
                                     │
                                     ├─ Success → Return Response
                                     │
                                     └─ Fail → Agent 3 (Tertiary) → ...
```

---

## Configuration

### Confidence Thresholds

| Threshold | Value | Behavior |
|-----------|-------|----------|
| High Confidence | ≥ 0.85 | Route to recommended agent |
| Low Confidence | < 0.50 | Fallback to CHAT agent |
| Multi-Agent Trigger | Complex task detected | Supervisor workflow |

### Feature Flags

```python
# Check if agent is enabled
if await feature_flags.is_agent_enabled(AgentType.EXECUTION):
    # Route to execution agent
    ...
else:
    # Use fallback agent
    ...
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Agent Types** | `domain/enums/agent_type.py` | 18 agent type enum |
| **Intent Classifier** | `domain/services/agent_squad/intent_classifier.py` | LLM-based classification |
| **Agent Orchestrator** | `domain/services/agent_squad/agent_orchestrator.py` | Message routing |
| **Supervisor** | `domain/services/agent_squad/supervisor_coordinator.py` | Multi-agent workflows |
| **Agent Router** | `infrastructure/agno/agent_router.py` | Keyword-based routing |
| **Orchestration Service** | `application/chat/services/agent_orchestration_service.py` | Voting, debates, fallback |
| **Value Objects** | `domain/value_objects/chat/orchestration.py` | Voting, debates, metrics |
| **Execute Workflow** | `application/agent_squad/commands/execute_supervisor_workflow.py` | Workflow command |
| **Agent Library** | `application/agents/library/agent_registry.py` | Pre-configured agents |
| **Intent Classifier OpenAI** | `infrastructure/adapters/agent_squad/intent_classifier_openai.py` | OpenAI adapter |
| **Domain Provider** | `setup/ioc/agent_squad_domain.py` | DI configuration |

---

## Usage Examples

### Simple Routing

```python
# Route message to appropriate agent
routing_result = await orchestrator.route_message(
    conversation_id=conv_id,
    message=MessageContent("Swap 1 ETH for USDC"),
    conversation_context=context,
)

# Check routing decision
print(f"Agent: {routing_result.agent_type}")      # EXECUTION
print(f"Confidence: {routing_result.intent_classification.confidence}")  # 0.92
print(f"Fallback: {routing_result.fallback_used}") # False
```

### Multi-Agent Workflow

```python
# Execute complex workflow
result = await execute_supervisor_workflow.execute(
    conversation_id=conv_id,
    user_id=user_id,
    complex_task="Create a balanced DeFi portfolio with yield optimization",
    max_agents=5,
)

# Access results
print(f"Agents used: {result['agents_used']}")  # 5
print(f"Plan: {result['plan']}")
print(f"Final synthesis: {result['final_synthesis']}")
```

### Multi-Agent Voting

```python
# Conduct vote on risk assessment
winning_response, voting_round = await orchestration_service.conduct_multi_agent_vote(
    query="What's the risk of this Aave position?",
    agent_names=["risk_analyzer", "yield_optimizer", "portfolio_manager"],
    strategy=VotingStrategy.WEIGHTED,
)

print(f"Winner: {winning_response}")
print(f"Votes: {voting_round.total_votes}")
print(f"Consensus confidence: {voting_round.consensus_confidence}")
```

### Fallback Routing

```python
# Create fallback chain
chain = orchestration_service.create_default_fallback_chain()

# Execute with fallback
response, updated_chain = await orchestration_service.execute_with_fallback(
    query="Analyze this protocol's security",
    fallback_chain=chain,
)

print(f"Final agent: {updated_chain.final_agent_used}")
print(f"Fallback reasons: {updated_chain.fallback_reasons}")
```

---

## Best Practices

### 1. Use Appropriate Confidence Thresholds

```python
# High-stakes operations require higher confidence
orchestrator = AgentOrchestrator(
    intent_classifier=classifier,
    feature_flags=flags,
    confidence_threshold=0.90,  # Higher threshold for transactions
)
```

### 2. Monitor Agent Performance

```python
# Track agent metrics
report = await orchestration_service.get_agent_performance_report()
print(report)
# Shows success rate, response time, efficiency score per agent
```

### 3. Use Feature Flags for Enterprise Agents

```python
# Check enterprise access before routing
if AgentType.is_enterprise_agent(agent_type):
    if not user.has_enterprise_subscription:
        raise AccessDeniedError("Enterprise subscription required")
```

### 4. Limit Multi-Agent Workflows

```python
# Cap agents per workflow to control costs
result = await execute_workflow(
    complex_task=task,
    max_agents=5,  # Reasonable limit
)
```

---

## Security Considerations

### 1. Enterprise Agent Access Control

Enterprise agents require subscription verification before access.

### 2. Agent Isolation

Each agent operates in isolated context with scoped permissions.

### 3. Workflow Limits

- Max agents per workflow: 10
- Workflow timeout: 120 seconds
- Rate limiting per user

### 4. Performance Tracking for Anomaly Detection

Monitor agent performance metrics to detect unusual behavior.

---

**Last Updated**: January 2, 2026

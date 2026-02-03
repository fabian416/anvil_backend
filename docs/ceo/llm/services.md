# LLM Orchestration System Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The LLM Orchestration System follows a hexagonal architecture with:
- **Domain Services**: Orchestrator, Ranking Engine, Circuit Breaker, Retry Engine
- **Infrastructure Adapters**: Vertex AI, DeepInfra, Bedrock providers
- **Application Layer**: Commands and Queries for ranking management
- **Agent Squad**: 18+ specialized AI agents for DeFi operations

**Total Service Components**: 80+ Python modules

---

## 1. Domain Services

### 1.1 LLM Orchestrator
**Path**: `src/app/domain/services/llm/orchestrator.py`

Core orchestration engine for multi-LLM routing.

```python
class LLMOrchestrator:
    """
    Main orchestration engine for multi-LLM routing.
    
    Responsibilities:
    - Model selection based on adaptive ranking
    - Retry with carousel fallback
    - Circuit breaker management
    - Telemetry collection
    - Cost tracking
    """
    
    async def execute(
        self,
        request: LLMRequest,
        agent_type: str,
        ranked_models: List[RankedModel],
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
    ) -> LLMResponse
    
    async def execute_stream(
        self,
        request: LLMRequest,
        agent_type: str,
        ranked_models: List[RankedModel],
    ) -> AsyncIterator[str]
```

**Configuration** (`OrchestratorConfig`):
- `max_retries_per_provider`: 2
- `max_total_retries`: 6
- `timeout_per_attempt_ms`: 30000
- `total_timeout_ms`: 120000
- `enable_caching`: True
- `enable_streaming`: True
- `enable_ranking`: True

---

### 1.2 Ranking Engine
**Path**: `src/app/domain/services/llm/ranking_engine.py`

Adaptive model ranking based on performance.

```python
class RankingEngine:
    """
    Adaptive model ranking based on performance.
    
    Calculates dynamic rankings using:
    - Success rate (50% weight by default)
    - Latency (25% weight)
    - Cost efficiency (15% weight)
    - Recency bonus (10% weight)
    """
    
    def calculate_ranking_score(
        self,
        agent_type: str,
        success_rate: Decimal,
        latency_score: Decimal,
        cost_score: Decimal,
        recency_bonus: Decimal,
    ) -> Decimal
```

**Weight Profiles** (per agent type):
| Agent Type | Success | Latency | Cost | Recency |
|------------|---------|---------|------|---------|
| swap_agent | 60% | 25% | 10% | 5% |
| trading_agent | 55% | 30% | 10% | 5% |
| portfolio_agent | 45% | 20% | 25% | 10% |
| researcher | 40% | 15% | 30% | 15% |
| risk_analyzer | 65% | 20% | 10% | 5% |
| default | 50% | 25% | 15% | 10% |

---

### 1.3 Circuit Breaker Manager
**Path**: `src/app/domain/services/llm/circuit_breaker.py`

Fault tolerance through circuit breaker pattern.

```python
class CircuitBreakerManager:
    """
    Manages circuit breakers for LLM providers.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failures exceeded threshold, rejecting requests
    - HALF_OPEN: Testing if service recovered
    """
    
    def is_open(self, model_id: UUID) -> bool
    def record_success(self, model_id: UUID) -> None
    def record_failure(self, model_id: UUID) -> None
    def reset(self, model_id: UUID) -> None
```

**Configuration**:
- `failure_threshold`: 5 consecutive failures
- `success_threshold`: 3 successes to close
- `timeout_seconds`: 60s before half-open

---

### 1.4 Retry Engine
**Path**: `src/app/domain/services/llm/retry_engine.py`

Intelligent retry with carousel fallback.

```python
class RetryEngine:
    """
    Retry engine with carousel fallback.
    
    Features:
    - Exponential backoff with jitter
    - Provider rotation (carousel)
    - Per-provider retry limits
    - Total retry limits
    """
    
    async def execute_with_retry(
        self,
        func: Callable,
        models: List[dict],
        on_attempt: Optional[Callable] = None,
    ) -> Any
```

**Configuration** (`RetryConfig`):
- `max_retries_per_provider`: 2
- `max_total_retries`: 6
- `initial_delay_ms`: 100
- `max_delay_ms`: 5000
- `backoff_multiplier`: 2.0
- `jitter`: True

---

### 1.5 Telemetry Collector
**Path**: `src/app/domain/services/llm/telemetry_collector.py`

Collects and aggregates LLM telemetry data.

---

## 2. Infrastructure Adapters (LLM Providers)

### 2.1 Vertex AI Adapter
**Path**: `src/app/infrastructure/adapters/agent_squad/llm_client_vertex_ai.py`

Google Gemini API integration.

```python
class LLMClientVertexAI:
    """
    Vertex AI adapter using Google Gemini API.
    
    Available models:
    - gemini-2.0-flash (fast, cost-effective)
    - gemini-1.5-pro (balanced)
    - gemini-1.5-flash (fast)
    """
    
    async def classify_intent(self, prompt: str, model: str) -> dict
    async def recommend_agents(self, prompt: str, model: str) -> dict
    async def plan_workflow(self, prompt: str, max_agents: int) -> dict
    async def chat(self, messages: list, model: str, temperature: float) -> dict
    async def generate(self, model: str, messages: list) -> str
```

---

### 2.2 DeepInfra Adapter
**Path**: `src/app/infrastructure/adapters/agent_squad/llm_client_deepinfra.py`

DeepInfra LLM API integration.

```python
class LLMClientDeepInfra:
    """
    DeepInfra adapter for LLM access.
    
    Available models:
    - meta-llama/Meta-Llama-3.1-70B-Instruct (default)
    - meta-llama/Meta-Llama-3.1-405B-Instruct (premium)
    - meta-llama/Llama-3.2-3B-Instruct (fast)
    """
```

---

### 2.3 Bedrock Adapter
**Path**: `src/app/infrastructure/llm/providers/bedrock_adapter.py`

AWS Bedrock integration.

---

### 2.4 LLM Client with Fallback
**Path**: `src/app/infrastructure/adapters/agent_squad/llm_client_with_fallback.py`

Wrapper providing automatic fallback between providers.

```python
class LLMClientWithFallback:
    """
    LLM Client with automatic fallback.
    
    Primary: Vertex AI (Gemini)
    Fallback: DeepInfra (LLaMA)
    
    Automatically falls back on:
    - Rate limiting
    - API errors
    - Timeouts
    """
```

---

### 2.5 Retry Handler
**Path**: `src/app/infrastructure/adapters/ai/llm/retry_handler.py`

Infrastructure-level retry handling.

---

### 2.6 Strategy Adapter
**Path**: `src/app/infrastructure/adapters/ai/llm/strategy.py`

Model selection strategy implementation.

---

## 3. Agent Squad Services

### 3.1 Agent Orchestrator (Domain)
**Path**: `src/app/domain/services/agent_squad/agent_orchestrator.py`

Routes messages to correct agent based on intent.

```python
class AgentOrchestrator:
    """
    Routes messages to correct agent based on intent.
    
    Responsibilities:
    - Route messages to correct agent
    - Use IntentClassifier for intent detection
    - Handle low-confidence routing (fallback)
    - Validate agent availability
    """
    
    async def route_message(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentRoutingResult
    
    async def select_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int = 5,
    ) -> list[AgentType]
```

---

### 3.2 Supervisor Coordinator
**Path**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

Coordinates multi-agent workflows.

---

### 3.3 Intent Classifier
**Path**: `src/app/domain/services/agent_squad/intent_classifier.py`

Classifies user intent using LLM.

---

### 3.4 Context Manager
**Path**: `src/app/domain/services/agent_squad/context_manager.py`

Manages conversation context across agents.

---

### 3.5 Authenticated Supervisor
**Path**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

Supervisor for authenticated user sessions.

---

### 3.6 Guest Supervisor
**Path**: `src/app/domain/services/agent_squad/guest_supervisor.py`

Supervisor for guest sessions.

---

## 4. Specialized Agents (18 Total)

### 4.1 Core Agents (10)

| Agent | Path | Purpose |
|-------|------|---------|
| Chat Agent | `agents/chat_agent.py` | General conversation |
| Hunter AI Agent | `agents/hunter_ai_agent.py` | Market analysis |
| Research Agent | `agents/research_agent_perplexity.py` | Research with Perplexity |
| Execution Agent | `agents/execution_agent_privy.py` | Transaction execution |
| Risk Analyzer | `agents/risk_analyzer_agent.py` | Risk assessment |
| Portfolio Agent | `agents/portfolio_agent.py` | Portfolio management |
| Tax Optimizer | `agents/tax_optimizer_agent.py` | Tax optimization |
| DeFi Yield Agent | `agents/defi_yield_agent.py` | Yield farming |
| Security Auditor | `agents/security_auditor_agent_slither.py` | Smart contract security |
| Gas Optimizer | `agents/gas_optimizer_agent.py` | Gas optimization |

---

### 4.2 Enterprise Agents (4)

| Agent | Path | Purpose |
|-------|------|---------|
| Compliance Monitor | `agents/enterprise/compliance_monitor_agent_chainalysis.py` | Regulatory compliance |
| Multi-Sig Coordinator | `agents/enterprise/multisig_coordinator_agent_gnosis.py` | Multi-sig operations |
| Alert Monitoring | `agents/enterprise/alert_monitoring_agent_forta.py` | Security alerts |
| Crisis Manager | `agents/enterprise/crisis_manager_agent_forta.py` | Crisis management |

---

### 4.3 Advanced Agents (4)

| Agent | Path | Purpose |
|-------|------|---------|
| Bridge Crosschain | `agents/advanced/bridge_crosschain_agent_axelar.py` | Cross-chain bridging |
| Lending Borrowing | `agents/advanced/lending_borrowing_agent_aave.py` | Lending/borrowing |
| NFT Asset Manager | `agents/advanced/nft_asset_manager_agent_opensea.py` | NFT management |
| DAO Governance | `agents/advanced/dao_governance_agent_snapshot.py` | DAO voting |

---

### 4.4 Workflow Agents (6)

| Agent | Path | Purpose |
|-------|------|---------|
| Swap Workflow | `agents/workflows/swap_workflow_agent.py` | Token swaps |
| Buy Workflow | `agents/workflows/buy_workflow_agent.py` | Crypto purchases |
| Lending Workflow | `agents/workflows/lending_workflow_agent.py` | Lending operations |
| Transfer Workflow | `agents/workflows/transfer_workflow_agent.py` | Asset transfers |
| Money Market Workflow | `agents/workflows/money_market_workflow_agent.py` | Money markets |
| Base Workflow | `agents/workflows/base_workflow_agent.py` | Base workflow class |

---

## 5. Application Layer (Commands & Queries)

### 5.1 Ranking Commands
**Path**: `src/app/application/llm/ranking/`

| Command | Purpose |
|---------|---------|
| `RegisterVertexAIModel` | Register new Vertex AI model |
| `RegisterDeepInfraModel` | Register new DeepInfra model |
| `RecalculateAgentRankings` | Recalculate rankings for agent |
| `RecalculateAllRankings` | Recalculate all rankings |
| `SetRankingOverride` | Set manual ranking override |
| `RemoveRankingOverride` | Remove ranking override |

---

### 5.2 Ranking Queries
**Path**: `src/app/application/llm/ranking/`

| Query | Purpose |
|-------|---------|
| `GetRankingsForAgent` | Get rankings for specific agent type |
| `GetAllRankingsOverview` | Get overview of all agent types |

---

### 5.3 Dashboard Query
**Path**: `src/app/application/llm/queries/get_dashboard_data.py`

```python
class GetDashboardData:
    """
    Get complete dashboard data.
    
    Returns:
    - System health summary
    - Provider status
    - Top models
    - Metrics summary
    - Cost summary
    - Recent requests
    - Active alerts
    """
```

---

### 5.4 Agent Squad Commands
**Path**: `src/app/application/agent_squad/commands/`

| Command | Purpose |
|---------|---------|
| `SendAgentSquadMessage` | Send message to agent squad |
| `ExecuteSupervisorWorkflow` | Execute multi-agent workflow |

---

### 5.5 Agent Squad Queries
**Path**: `src/app/application/agent_squad/queries/`

| Query | Purpose |
|-------|---------|
| `GetConversationContext` | Get conversation context |
| `GetEnabledAgents` | Get list of enabled agents |

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Admin LLM Router                                  │    │
│  │  /admin/llm/dashboard • /rankings • /providers • /telemetry        │    │
│  │  /models • /circuit-breakers • /budgets                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Commands & Queries                                │  │
│  │                                                                        │  │
│  │  RegisterModel • RecalculateRankings • SetOverride • GetRankings     │  │
│  │  GetDashboardData • SendAgentMessage • ExecuteWorkflow               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Domain Services                                  │  │
│  │                                                                        │  │
│  │  LLMOrchestrator • RankingEngine • CircuitBreakerManager             │  │
│  │  RetryEngine • TelemetryCollector • AgentOrchestrator                │  │
│  │  SupervisorCoordinator • IntentClassifier • ContextManager           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Value Objects                                     │  │
│  │                                                                        │  │
│  │  LLMRequest • LLMResponse • RetryConfig • ConversationContext        │  │
│  │  AgentSquadConfig • IntentClassification • RankedModel               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Ports                                         │  │
│  │                                                                        │  │
│  │  LLMProviderPort • LLMClientGateway • AgentGateway                   │  │
│  │  IntentClassifierPort • FeatureFlagsPort                             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      LLM Providers                                    │  │
│  │                                                                        │  │
│  │  LLMClientVertexAI • LLMClientDeepInfra • BedrockAdapter             │  │
│  │  LLMClientWithFallback • RetryHandler • StrategyAdapter              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Agent Squad (18 Agents)                         │  │
│  │                                                                        │  │
│  │  Core: Chat • Hunter • Research • Execution • Risk • Portfolio       │  │
│  │  Enterprise: Compliance • MultiSig • Alert • Crisis                  │  │
│  │  Advanced: Bridge • Lending • NFT • DAO                              │  │
│  │  Workflows: Swap • Buy • Lending • Transfer • MoneyMarket            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Repositories                                     │  │
│  │                                                                        │  │
│  │  RankingRepository • ContextStorageRedis • FeatureFlagsConfig        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                      │
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ Google   │ │DeepInfra │ │  AWS     │ │Perplexity│ │  OpenAI  │         │
│  │ Gemini   │ │ LLaMA    │ │ Bedrock  │ │   API    │ │   API    │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Agno Agents (Legacy)

### 7.1 Agent Pool
**Path**: `src/app/infrastructure/agno/pool.py`

Agent pooling for performance.

---

### 7.2 Agent Router
**Path**: `src/app/infrastructure/agno/agent_router.py`

Routes requests to appropriate Agno agents.

---

### 7.3 Specialized Agno Agents

| Agent | Path | Purpose |
|-------|------|---------|
| Base Agent | `agno/base_agent.py` | Base agent class |
| Trading Agent | `agno/trading_agent.py` | Trading operations |
| Lending Agent | `agno/lending_agent.py` | Lending operations |
| Portfolio Agent | `agno/portfolio_agent.py` | Portfolio management |
| Perpetual Agent | `agno/perpetual_agent.py` | Perpetual trading |
| Analytics Agent | `agno/analytics_agent.py` | Analytics |

---

## References

- **Domain Services**: `src/app/domain/services/llm/`
- **Agent Squad**: `src/app/infrastructure/adapters/agent_squad/`
- **LLM Providers**: `src/app/infrastructure/llm/providers/`
- **Application Commands**: `src/app/application/llm/ranking/`
- **Agno Agents**: `src/app/infrastructure/agno/`

# System Architecture

## Overview

The Multi-LLM Orchestration System is designed as a high-availability, fault-tolerant layer that abstracts multiple LLM providers into a unified interface for Anvil's AI agents.

---

## Design Principles

### 1. Provider Agnosticism
The system treats all LLM providers uniformly through a common interface, allowing seamless switching and fallback without agent modification.

### 2. Resilience First
Every component is designed with failure in mind:
- Automatic retries with exponential backoff
- Circuit breakers prevent cascade failures
- Graceful degradation when providers fail

### 3. Observable by Default
All operations emit metrics and logs:
- Request lifecycle tracking
- Performance telemetry
- Cost accounting

### 4. Business Control
Non-technical stakeholders can:
- Monitor system health
- Control costs via budgets
- Override model selection

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANVIL LLM ORCHESTRATION LAYER                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────────────────────────────────────────┐   │
│  │   Request    │───▶│              REQUEST ROUTER                       │   │
│  │   Ingress    │    │  • Agent Context Extraction                       │   │
│  └──────────────┘    │  • Model Selection (Ranking-Based)                │   │
│                      │  • Request Enrichment                              │   │
│                      │  • Capability Matching                             │   │
│                      └──────────────────────────────────────────────────┘   │
│                                         │                                    │
│                                         ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    PROVIDER ORCHESTRATOR                              │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │  VERTEX AI  │  │  DEEPINFRA  │  │   BEDROCK   │                   │   │
│  │  │  (Primary)  │  │ (Fallback 1)│  │ (Fallback 2)│                   │   │
│  │  │  Priority:1 │  │  Priority:2 │  │  Priority:3 │                   │   │
│  │  │             │  │             │  │             │                   │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │                   │   │
│  │  │ │Gemini   │ │  │ │Llama3.1 │ │  │ │Claude   │ │                   │   │
│  │  │ │Pro 1.5  │ │  │ │  405B   │ │  │ │Sonnet   │ │                   │   │
│  │  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │                   │   │
│  │  │ │Gemini   │ │  │ │Mixtral  │ │  │ │Claude   │ │                   │   │
│  │  │ │Flash    │ │  │ │ 8x22B   │ │  │ │Haiku    │ │                   │   │
│  │  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │                   │   │
│  │  │ │Gemini   │ │  │ │Qwen2    │ │  │ │Titan    │ │                   │   │
│  │  │ │2.0 Flash│ │  │ │  72B    │ │  │ │Express  │ │                   │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                         │                                    │
│                    ┌────────────────────┼────────────────────┐               │
│                    ▼                    ▼                    ▼               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   RETRY ENGINE      │  │   RANKING ENGINE    │  │  TELEMETRY ENGINE   │  │
│  │                     │  │                     │  │                     │  │
│  │  • Carousel Logic   │  │  • Success Rate     │  │  • Latency Metrics  │  │
│  │  • Exponential Back │  │  • Latency Score    │  │  • Cost Tracking    │  │
│  │  • Circuit Breaker  │  │  • Cost Efficiency  │  │  • Error Analysis   │  │
│  │  • Timeout Handling │  │  • Agent Affinity   │  │  • Usage Patterns   │  │
│  │  • Error Classify   │  │  • Recency Bonus    │  │  • Token Counting   │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                         │                                    │
│                                         ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    BUSINESS CONTROL PANEL                             │   │
│  │                                                                       │   │
│  │  • Real-time Dashboard    • Cost Alerts     • Provider Health        │   │
│  │  • Model Performance      • Budget Caps     • Manual Overrides       │   │
│  │  • Ranking Visualization  • Config Mgmt     • Audit Logs             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### 1. Request Router

**Purpose**: Receive incoming requests and prepare them for execution.

**Responsibilities**:
- Extract agent context (type, capabilities needed)
- Query ranking engine for optimal model
- Enrich request with metadata
- Validate request against rate limits

**Interfaces**:
```python
class RequestRouter:
    async def route(self, request: LLMRequest, agent_type: str) -> RoutingDecision
    async def validate(self, request: LLMRequest) -> ValidationResult
```

### 2. Provider Orchestrator

**Purpose**: Manage connections to all LLM providers and execute requests.

**Responsibilities**:
- Maintain provider client pool
- Execute requests on selected provider
- Handle streaming responses
- Report results to telemetry

**Interfaces**:
```python
class ProviderOrchestrator:
    async def execute(self, request: LLMRequest, model: RankedModel) -> LLMResponse
    async def execute_stream(self, request: LLMRequest, model: RankedModel) -> AsyncIterator[str]
    async def health_check(self, provider_id: str) -> ProviderStatus
```

### 3. Retry Engine

**Purpose**: Handle failures and implement retry strategies.

**Responsibilities**:
- Implement carousel retry logic
- Apply exponential backoff
- Classify errors as retryable/non-retryable
- Manage circuit breakers
- Track attempt history

**Interfaces**:
```python
class RetryEngine:
    async def execute_with_retry(
        self,
        request: LLMRequest,
        ranked_models: List[RankedModel]
    ) -> LLMResponse
    
    def should_retry(self, error: Exception) -> bool
    def calculate_backoff(self, attempt: int) -> float
```

### 4. Ranking Engine

**Purpose**: Determine optimal model selection for each request.

**Responsibilities**:
- Calculate dynamic rankings
- Apply agent-specific weights
- Incorporate real-time performance data
- Handle manual overrides

**Interfaces**:
```python
class RankingEngine:
    async def get_ranked_models(
        self,
        agent_type: str,
        capabilities: List[str]
    ) -> List[RankedModel]
    
    async def record_outcome(
        self,
        model_id: str,
        agent_type: str,
        success: bool,
        latency_ms: int,
        cost: float
    ) -> None
    
    async def recalculate_rankings(self, agent_type: str = None) -> None
```

### 5. Telemetry Engine

**Purpose**: Collect, aggregate, and expose metrics.

**Responsibilities**:
- Capture request lifecycle events
- Calculate aggregated metrics
- Store time-series data
- Expose metrics for dashboards

**Interfaces**:
```python
class TelemetryEngine:
    async def record_request(self, request: LLMRequest, response: LLMResponse) -> None
    async def record_error(self, request: LLMRequest, error: Exception) -> None
    async def get_metrics(self, period: str, dimensions: Dict) -> MetricsSummary
    async def aggregate_hourly(self) -> None
```

### 6. Business Control Panel

**Purpose**: Provide visibility and control for non-technical stakeholders.

**Responsibilities**:
- Aggregate data for dashboards
- Manage budgets and alerts
- Allow configuration changes
- Provide audit trail

**Interfaces**:
```python
class BusinessControlPanel:
    async def get_dashboard_data(self, period: str) -> DashboardData
    async def update_config(self, key: str, value: Any, user_id: str) -> None
    async def set_budget(self, budget: Budget) -> None
    async def check_budget(self) -> BudgetStatus
```

---

## Data Flow

### Request Execution Flow

```
1. Agent sends request
       │
       ▼
2. Request Router receives
   - Extracts agent context
   - Validates request
   - Queries Ranking Engine
       │
       ▼
3. Ranking Engine returns ordered models
   - Based on success rate, latency, cost
   - Filtered by capabilities
   - Agent-specific weights applied
       │
       ▼
4. Retry Engine manages execution
   - Tries first model
   - On failure: checks circuit breaker
   - Applies backoff
   - Rotates to next model (carousel)
       │
       ▼
5. Provider Orchestrator executes
   - Sends request to provider
   - Handles streaming if requested
   - Returns response
       │
       ▼
6. Telemetry Engine records
   - Request metadata
   - Response metrics
   - Cost calculation
       │
       ▼
7. Ranking Engine updates
   - Record success/failure
   - Update scores (async)
       │
       ▼
8. Response returned to Agent
```

---

## Scalability Considerations

### Horizontal Scaling

- Orchestrator is stateless
- Multiple instances behind load balancer
- Shared state in Redis/PostgreSQL

### Vertical Scaling

- Connection pooling for providers
- Async I/O throughout
- Batch telemetry writes

### Rate Limiting

- Per-user limits at request router
- Per-provider limits enforced
- Global budget limits

---

## Security Architecture

### API Key Management

```
┌─────────────────┐     ┌─────────────────┐
│  Secrets Store  │────▶│  Key Rotation   │
│  (Vault/SM)     │     │  Service        │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Provider Clients                 │
│  (Keys injected at runtime)             │
└─────────────────────────────────────────┘
```

### Request Sanitization

- PII stripped from logs
- Prompt hashing for deduplication
- No raw content in telemetry

### Access Control

- RBAC for admin endpoints
- Audit logging for config changes
- IP whitelisting for sensitive operations

---

## Deployment Architecture

### Production Topology

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Orchestrator  │    │ Orchestrator  │    │ Orchestrator  │
│   Pod 1       │    │   Pod 2       │    │   Pod 3       │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │    Redis      │    │  Prometheus   │
│  (Primary)    │    │   Cluster     │    │    Stack      │
└───────────────┘    └───────────────┘    └───────────────┘
```

### Kubernetes Resources

- **Deployment**: 3-10 replicas (HPA)
- **Service**: ClusterIP for internal
- **Ingress**: External API access
- **ConfigMap**: Non-sensitive config
- **Secret**: Provider API keys
- **PDB**: Min 2 pods available

---

## Integration Points

### Upstream (Consumers)

- **SwapAgent**: DeFi swap execution
- **TradingAgent**: Perpetual futures
- **PortfolioAgent**: Portfolio analysis
- **ResearchAgent**: Market research
- **RiskAgent**: Risk assessment

### Downstream (Providers)

- **Google Vertex AI**: Primary provider
- **DeepInfra**: First fallback
- **AWS Bedrock**: Second fallback

### Infrastructure

- **PostgreSQL**: Persistent storage
- **Redis**: Caching, rate limiting
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **PagerDuty**: Alerting

---

## Failure Modes

### Provider Unavailable

**Detection**: Health check failure, connection timeout
**Response**: Circuit breaker opens, traffic routed to fallback
**Recovery**: Half-open testing, automatic reset

### High Latency

**Detection**: P95 exceeds threshold
**Response**: Model demoted in ranking
**Recovery**: Automatic via ranking recalculation

### Budget Exceeded

**Detection**: Cost accumulator hits limit
**Response**: Requests rejected (hard limit) or alerts (soft limit)
**Recovery**: Manual budget adjustment or period reset

### Cascade Failure

**Detection**: Multiple circuit breakers open
**Response**: Emergency fallback to cheapest model
**Recovery**: Gradual circuit breaker reset

---

## Monitoring & Alerting

### Critical Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| All Providers Down | 0 healthy providers | Page on-call |
| High Error Rate | >5% errors in 5min | Page on-call |
| Budget Critical | >95% of daily budget | Notify finance |
| Latency Spike | P95 > 10s for 5min | Investigate |

### Warning Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| Provider Degraded | 1 provider unhealthy | Monitor |
| Elevated Retries | >10% retry rate | Investigate |
| Budget Warning | >80% of daily budget | Notify team |
| Circuit Breaker Open | Any breaker open >5min | Investigate |

---

## Next Steps

1. Review [Data Flow](DATA_FLOW.md) for detailed request lifecycle
2. See [Database Schema](../database/SCHEMA.md) for data models
3. Check [Provider Integration](../providers/OVERVIEW.md) for provider details

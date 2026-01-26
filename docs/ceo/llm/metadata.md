# LLM Orchestration System Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil LLM Orchestration System provides intelligent multi-model routing, adaptive ranking, fault tolerance, and comprehensive telemetry for AI agent operations.

**Supported Providers**: 3 (Vertex AI/Gemini, DeepInfra/LLaMA, AWS Bedrock)  
**Total Agents**: 18+ specialized AI agents  
**Features**: Adaptive ranking, circuit breakers, retry carousel, cost tracking

---

## 1. Module Status

| Component | Status | Health | Notes |
|-----------|--------|--------|-------|
| LLM Orchestrator | ✅ Production | Healthy | Multi-model routing |
| Ranking Engine | ✅ Production | Healthy | Adaptive scoring |
| Circuit Breaker | ✅ Production | Healthy | Fault tolerance |
| Retry Engine | ✅ Production | Healthy | Carousel fallback |
| Vertex AI Provider | ✅ Production | Healthy | Primary provider |
| DeepInfra Provider | ✅ Production | Healthy | Fallback provider |
| Bedrock Provider | ✅ Production | Healthy | Enterprise option |
| Agent Squad (18) | ✅ Production | Healthy | All agents active |
| Admin Dashboard | ⚠️ Partial | Limited | Some TODOs remain |
| Telemetry Aggregation | ⚠️ Partial | Limited | Hourly missing |
| Cost Tracking | ⚠️ Partial | Limited | Daily missing |

---

## 2. File Reference Index

### 2.1 Domain Layer

```
src/app/domain/
├── services/
│   └── llm/
│       ├── __init__.py
│       ├── orchestrator.py           # LLMOrchestrator - core routing engine
│       ├── ranking_engine.py         # RankingEngine - adaptive scoring
│       ├── circuit_breaker.py        # CircuitBreakerManager - fault tolerance
│       ├── retry_engine.py           # RetryEngine - carousel fallback
│       └── telemetry_collector.py    # TelemetryCollector - metrics
│   └── agent_squad/
│       ├── agent_orchestrator.py     # AgentOrchestrator - agent routing
│       ├── supervisor_coordinator.py # SupervisorCoordinator - multi-agent
│       ├── intent_classifier.py      # IntentClassifier - intent detection
│       ├── context_manager.py        # ContextManager - conversation context
│       ├── authenticated_supervisor.py
│       └── guest_supervisor.py
├── value_objects/
│   └── llm/
│       ├── __init__.py
│       ├── llm_request.py            # LLMRequest value object
│       ├── llm_response.py           # LLMResponse value object
│       └── retry_config.py           # RetryConfig value object
│   └── agent_squad/
│       ├── agent_squad_config.py     # AgentSquadConfig
│       └── conversation_context.py   # ConversationContext
├── ports/
│   ├── llm_provider_port.py          # LLMProviderPort protocol
│   └── agent_squad/
│       ├── agent_gateway.py          # AgentGateway protocol
│       └── llm_client_gateway.py     # LLMClientGateway protocol
└── entities/
    └── agent_squad/
        ├── crisis_event.py
        └── multisig_proposal.py
```

### 2.2 Application Layer

```
src/app/application/
├── llm/
│   ├── ranking/
│   │   ├── __init__.py
│   │   ├── register_model.py         # RegisterVertexAIModel, RegisterDeepInfraModel
│   │   ├── manage_overrides.py       # SetRankingOverride, RemoveRankingOverride
│   │   ├── recalculate_all_rankings.py
│   │   ├── recalculate_agent_rankings.py
│   │   └── get_rankings.py           # GetRankingsForAgent, GetAllRankingsOverview
│   └── queries/
│       ├── __init__.py
│       └── get_dashboard_data.py     # GetDashboardData query
└── agent_squad/
    ├── commands/
    │   ├── __init__.py
    │   ├── send_agent_squad_message.py
    │   └── execute_supervisor_workflow.py
    └── queries/
        ├── __init__.py
        ├── get_conversation_context.py
        └── get_enabled_agents.py
```

### 2.3 Infrastructure Layer (LLM Providers)

```
src/app/infrastructure/
├── adapters/
│   ├── ai/llm/
│   │   ├── retry_handler.py          # Infrastructure retry handling
│   │   ├── deepinfra.py              # DeepInfra adapter
│   │   ├── vertex.py                 # Vertex AI adapter
│   │   └── strategy.py               # Model selection strategy
│   └── agent_squad/
│       ├── __init__.py
│       ├── llm_client_vertex_ai.py   # LLMClientVertexAI adapter
│       ├── llm_client_deepinfra.py   # LLMClientDeepInfra adapter
│       ├── llm_client_openai.py      # LLMClientOpenAI adapter
│       ├── llm_client_with_fallback.py # Fallback wrapper
│       ├── llm_client_gateway_adapter.py
│       ├── agent_llm_gateway.py      # AgentLLMGateway implementation
│       ├── agent_executor_adapter.py
│       ├── intent_classifier_openai.py
│       ├── context_storage_redis.py
│       └── feature_flags_config.py
├── llm/
│   ├── __init__.py
│   ├── orchestrator_integration.py   # Orchestrator integration
│   └── providers/
│       ├── __init__.py
│       ├── vertex_ai_adapter.py      # Vertex AI provider
│       ├── deepinfra_adapter.py      # DeepInfra provider
│       └── bedrock_adapter.py        # AWS Bedrock provider
└── persistence_sqla/repositories/llm/
    ├── __init__.py
    └── ranking_repository.py         # RankingRepository
```

### 2.4 Infrastructure Layer (Agent Squad)

```
src/app/infrastructure/adapters/agent_squad/agents/
├── __init__.py
├── chat_agent.py                     # Chat Agent
├── hunter_ai_agent.py                # Hunter AI Agent
├── knowledge_agent.py                # Knowledge Agent
├── research_agent_perplexity.py      # Research Agent (Perplexity)
├── execution_agent_privy.py          # Execution Agent
├── portfolio_agent.py                # Portfolio Agent
├── risk_analyzer_agent.py            # Risk Analyzer Agent
├── tax_optimizer_agent.py            # Tax Optimizer Agent
├── defi_yield_agent.py               # DeFi Yield Agent
├── gas_optimizer_agent.py            # Gas Optimizer Agent
├── security_auditor_agent_slither.py # Security Auditor Agent
├── wallet_agent.py                   # Wallet Agent
├── transaction_history_agent.py      # Transaction History Agent
├── guest_auth_agent.py               # Guest Auth Agent
├── source_helpers.py                 # Helper functions
├── workflows/
│   ├── __init__.py
│   ├── base_workflow_agent.py        # Base Workflow
│   ├── swap_workflow_agent.py        # Swap Workflow
│   ├── buy_workflow_agent.py         # Buy Workflow
│   ├── lending_workflow_agent.py     # Lending Workflow
│   ├── transfer_workflow_agent.py    # Transfer Workflow
│   └── money_market_workflow_agent.py # Money Market Workflow
├── advanced/
│   ├── __init__.py
│   ├── bridge_crosschain_agent_axelar.py
│   ├── lending_borrowing_agent_aave.py
│   ├── nft_asset_manager_agent_opensea.py
│   └── dao_governance_agent_snapshot.py
└── enterprise/
    ├── __init__.py
    ├── compliance_monitor_agent_chainalysis.py
    ├── multisig_coordinator_agent_gnosis.py
    ├── alert_monitoring_agent_forta.py
    └── crisis_manager_agent_forta.py
```

### 2.5 Agno Agents (Legacy)

```
src/app/infrastructure/agno/
├── __init__.py
├── pool.py                           # Agent pooling
├── base_agent.py                     # Base agent class
├── agent_router.py                   # Agent routing
├── monitoring.py                     # Monitoring
├── batch.py                          # Batch processing
├── cache.py                          # Caching
├── trading_agent.py                  # Trading agent
├── lending_agent.py                  # Lending agent
├── portfolio_agent.py                # Portfolio agent
├── perpetual_agent.py                # Perpetual agent
└── analytics_agent.py                # Analytics agent
```

### 2.6 Presentation Layer

```
src/app/presentation/http/controllers/admin/llm/
├── __init__.py
├── router.py                         # Main admin LLM router
├── schemas.py                        # Pydantic schemas
├── dashboard.py                      # Dashboard endpoints
├── ranking_router.py                 # Ranking endpoints
├── rankings.py                       # Additional ranking logic
├── providers.py                      # Provider endpoints
├── models.py                         # Model endpoints
├── telemetry.py                      # Telemetry endpoints
├── circuit_breakers.py               # Circuit breaker endpoints
└── budgets.py                        # Budget endpoints
```

### 2.7 Celery Tasks

```
src/app/infrastructure/celery/
├── app.py                            # Celery app
├── tasks.py                          # Main tasks (includes LLM imports)
└── tasks/
    └── llm_ranking.py                # LLM ranking tasks
```

### 2.8 Test Files

```
tests/
├── unit/
│   ├── application/
│   │   ├── test_llm_dashboard_query.py
│   │   └── chat/
│   │       ├── test_intent_orchestrator.py
│   │       ├── test_multi_intent_integration_service.py
│   │       └── test_multi_intent_response_formatter.py
│   ├── presentation/admin/
│   │   └── test_llm_management_controllers.py
│   └── infrastructure/
│       ├── test_llm_gateway_tuple_handling.py
│       ├── test_llm_retry_handler.py
│       ├── test_agent_gateway_normalization.py
│       └── agents/
│           └── test_lending_borrowing_agent_aave.py
├── component/agent_squad/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_intent_classification.py
├── integration/agno/
│   ├── conftest.py
│   ├── test_agent_retry.py
│   └── test_agent_flags.py
└── e2e/agent_squad/
    └── test_api_endpoints.py
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                  │
│  │ Admin UI  │ │ Chat API  │ │ Agent API │ │ WebSocket │                  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                  │
└────────┼─────────────┼─────────────┼─────────────┼──────────────────────────┘
         │             │             │             │
         ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Admin LLM Controller                             │    │
│  │  /admin/llm/dashboard • /rankings • /providers • /telemetry        │    │
│  │  /models • /circuit-breakers • /budgets                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Chat Controller                                   │    │
│  │  Message routing to Agent Squad via IntentClassifier               │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                     │
│                                                                              │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐    │
│  │       LLM Ranking              │  │        Agent Squad             │    │
│  │                                │  │                                │    │
│  │  RegisterModel                 │  │  SendAgentSquadMessage         │    │
│  │  RecalculateRankings          │  │  ExecuteSupervisorWorkflow     │    │
│  │  SetOverride                  │  │  GetConversationContext        │    │
│  │  GetRankings                  │  │  GetEnabledAgents              │    │
│  │  GetDashboardData             │  │                                │    │
│  └────────────────────────────────┘  └────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      LLM Domain Services                              │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Orchestrator│  │RankingEngine│  │CircuitBreakr│  │ RetryEngine │  │  │
│  │  │             │  │             │  │   Manager   │  │             │  │  │
│  │  │ • Execute   │  │ • Calculate │  │ • is_open   │  │ • Execute   │  │  │
│  │  │ • Stream    │  │ • Weights   │  │ • record    │  │   w/ Retry  │  │  │
│  │  │ • Route     │  │ • Profiles  │  │ • reset     │  │ • Backoff   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Agent Squad Domain Services                        │  │
│  │                                                                        │  │
│  │  AgentOrchestrator • SupervisorCoordinator • IntentClassifier        │  │
│  │  ContextManager • AuthenticatedSupervisor • GuestSupervisor          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      LLM Provider Adapters                           │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Vertex AI  │  │  DeepInfra  │  │   Bedrock   │  │  Fallback   │  │  │
│  │  │  (Gemini)   │  │  (LLaMA)    │  │  (Claude)   │  │  Wrapper    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Agent Squad (18 Agents)                         │  │
│  │                                                                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │  │  Chat   │ │ Hunter  │ │Research │ │Execution│ │  Risk   │        │  │
│  │  │  Agent  │ │  AI     │ │ Agent   │ │ Agent   │ │Analyzer │        │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  │                                                                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │  │Portfolio│ │   Tax   │ │  DeFi   │ │Security │ │   Gas   │        │  │
│  │  │  Agent  │ │Optimizer│ │  Yield  │ │ Auditor │ │Optimizer│        │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  │                                                                        │  │
│  │  Enterprise: Compliance • MultiSig • Alert • Crisis                  │  │
│  │  Advanced: Bridge • Lending • NFT • DAO                              │  │
│  │  Workflows: Swap • Buy • Lending • Transfer • MoneyMarket            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                      │
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ Google   │ │DeepInfra │ │  AWS     │ │Perplexity│ │  Redis   │         │
│  │ Gemini   │ │ LLaMA    │ │ Bedrock  │ │   API    │ │ (Context)│         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Model Provider Comparison

| Provider | Models | Cost (per 1M tokens) | Latency | Use Case |
|----------|--------|---------------------|---------|----------|
| **Vertex AI** | Gemini 2.0 Flash, 1.5 Pro, 1.5 Flash | $0.10-0.30 | Low | Primary |
| **DeepInfra** | LLaMA 3.1 70B, 405B | $0.50-2.00 | Medium | Fallback |
| **Bedrock** | Claude 3, Titan | $3.00-15.00 | Medium | Enterprise |

---

## 5. Ranking Weight Profiles

```
┌────────────────────────────────────────────────────────────────────────┐
│                      RANKING WEIGHT PROFILES                           │
├────────────────┬──────────┬─────────┬───────┬─────────┬───────────────┤
│ Agent Type     │ Success  │ Latency │ Cost  │ Recency │ Notes         │
├────────────────┼──────────┼─────────┼───────┼─────────┼───────────────┤
│ swap_agent     │   60%    │   25%   │  10%  │   5%    │ Reliability   │
│ trading_agent  │   55%    │   30%   │  10%  │   5%    │ Speed focus   │
│ portfolio_agent│   45%    │   20%   │  25%  │  10%    │ Cost aware    │
│ researcher     │   40%    │   15%   │  30%  │  15%    │ Quality focus │
│ risk_analyzer  │   65%    │   20%   │  10%  │   5%    │ Accuracy      │
│ default        │   50%    │   25%   │  15%  │  10%    │ Balanced      │
└────────────────┴──────────┴─────────┴───────┴─────────┴───────────────┘
```

---

## 6. Improvements Roadmap

### 6.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Telemetry Aggregation** | Implement hourly telemetry aggregation | Medium | Dashboard accuracy |
| **Cost Tracking** | Implement daily cost aggregation | Medium | Budget control |
| **Unit Tests** | Add orchestrator/ranking tests | Medium | Code quality |
| **Provider Health Check** | Implement health monitoring | Low | Reliability |

### 6.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Admin E2E Tests** | Add full admin workflow tests | Medium | Quality |
| **Circuit Breaker Tests** | Add state transition tests | Low | Reliability |
| **Model Registration UI** | Admin UI for model management | High | UX |
| **Real-time Alerts** | Push alerts via WebSocket | Medium | Ops |

### 6.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **PDF Export** | Export dashboard as PDF | Medium | Feature |
| **Historical Comparison** | Compare metrics across periods | High | Analytics |
| **A/B Testing** | Model A/B testing framework | High | Optimization |

---

## 7. Performance Metrics

### 7.1 Current Performance

| Metric | Value | Target |
|--------|-------|--------|
| Average latency (Vertex AI) | ~1100ms | <1500ms |
| Average latency (DeepInfra) | ~1800ms | <2500ms |
| Success rate | 98.7% | >99% |
| Circuit breaker trips/day | <5 | <10 |
| Ranking recalc time | ~30s | <60s |

### 7.2 Cost Metrics

| Metric | Monthly Value |
|--------|---------------|
| Total LLM cost | ~$2,500 |
| Cost per request | ~$0.002 |
| Vertex AI % | 70% |
| DeepInfra % | 25% |
| Bedrock % | 5% |

---

## 8. Security Considerations

### 8.1 Implemented

- ✅ Admin endpoints require authentication
- ✅ API keys stored in secure configuration
- ✅ Rate limiting on LLM requests
- ✅ Cost budgets and alerts

### 8.2 Recommendations

- ⚠️ Add request signing for provider calls
- ⚠️ Implement prompt injection detection
- ⚠️ Add audit logging for admin actions
- ⚠️ Review PII handling in telemetry

---

## References

- **Endpoints Spec**: `docs/ceo/llm/endpoints.md`
- **Services Spec**: `docs/ceo/llm/services.md`
- **Celery Spec**: `docs/ceo/llm/celery.md`
- **Test Spec**: `docs/ceo/llm/test.md`
- **Vertex AI Docs**: https://cloud.google.com/vertex-ai/docs
- **DeepInfra Docs**: https://deepinfra.com/docs
- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/

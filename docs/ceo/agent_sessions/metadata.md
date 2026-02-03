# Agent Sessions Module Metadata

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## 1. Module Overview

### Agent Sessions System
**Purpose**: Manage stateful multi-agent interactions within conversations.

**Status**: ✅ Production Ready
- 25+ agents implemented and operational
- Multi-agent supervisor workflow functional
- Context storage via Redis (24h TTL)
- Agent telemetry tracking (partial)
- Enterprise features (compliance, multi-sig, crisis) defined

### Key Capabilities
- **Intent Classification**: Routes messages to appropriate agents
- **Multi-Agent Orchestration**: Coordinates complex workflows
- **Context Management**: Preserves conversation history
- **Session State**: Per-conversation agent state (JSONB)
- **Telemetry**: Performance tracking (latency, tokens, tools)

---

## 2. File Reference Index

### Domain Layer
| File | Description | Status |
|------|-------------|--------|
| `src/app/domain/entities/agent_session.py` | AgentSession entity | ✅ |
| `src/app/domain/value_objects/agent_session_id.py` | AgentSessionId value object | ✅ |
| `src/app/domain/enums/agent_type.py` | AgentType enum (25 agents) | ✅ |
| `src/app/domain/services/agent_squad/agent_orchestrator.py` | Agent routing service | ✅ |
| `src/app/domain/services/agent_squad/context_manager.py` | Context management | ✅ |
| `src/app/domain/services/agent_squad/supervisor_coordinator.py` | Multi-agent workflows | ✅ |
| `src/app/domain/services/agent_squad/intent_classifier.py` | Intent classification | ✅ |
| `src/app/domain/services/agent_squad/authenticated_supervisor.py` | Auth user supervisor | ✅ |
| `src/app/domain/services/agent_squad/guest_supervisor.py` | Guest user supervisor | ✅ |
| `src/app/domain/ports/agent_squad/agent_gateway.py` | AgentGateway port | ✅ |
| `src/app/domain/ports/agent_squad/context_storage_gateway.py` | ContextStorage port | ✅ |
| `src/app/domain/ports/agent_squad/feature_flags_gateway.py` | FeatureFlags port | ✅ |
| `src/app/domain/ports/agent_squad/llm_client_gateway.py` | LLMClient port | ✅ |
| `src/app/domain/value_objects/agent_squad/conversation_context.py` | ConversationContext | ✅ |
| `src/app/domain/value_objects/agent_squad/agent_squad_config.py` | Agent config | ✅ |
| `src/app/domain/entities/agent_squad/agent_telemetry.py` | Telemetry entity | ✅ |
| `src/app/domain/entities/agent_squad/crisis_event.py` | Crisis entity | ✅ |
| `src/app/domain/entities/agent_squad/multisig_proposal.py` | MultiSig entity | ✅ |

### Application Layer
| File | Description | Status |
|------|-------------|--------|
| `src/app/application/agent_squad/commands/send_agent_squad_message.py` | Send message command | ✅ |
| `src/app/application/agent_squad/commands/execute_supervisor_workflow.py` | Workflow command | ✅ |
| `src/app/application/agent_squad/queries/get_conversation_context.py` | Get context query | ✅ |
| `src/app/application/agent_squad/queries/get_enabled_agents.py` | List agents query | ✅ |

### Infrastructure Layer - Agents (25+)
| File | Description | Status |
|------|-------------|--------|
| `agents/chat_agent.py` | General conversation | ✅ |
| `agents/guest_auth_agent.py` | Auth prompts | ✅ |
| `agents/knowledge_agent.py` | Educational queries | ✅ |
| `agents/hunter_ai_agent.py` | Market sentiment | ✅ |
| `agents/research_agent_perplexity.py` | Protocol research | ✅ |
| `agents/execution_agent_privy.py` | Transaction execution | ✅ |
| `agents/risk_analyzer_agent.py` | Risk assessment | ✅ |
| `agents/portfolio_agent.py` | Portfolio optimization | ✅ |
| `agents/tax_optimizer_agent.py` | Tax optimization | ✅ |
| `agents/defi_yield_agent.py` | Yield farming | ✅ |
| `agents/security_auditor_agent_slither.py` | Security analysis | ✅ |
| `agents/gas_optimizer_agent.py` | Gas optimization | ✅ |
| `agents/wallet_agent.py` | Wallet management | ✅ |
| `agents/transaction_history_agent.py` | TX history | ✅ |
| `agents/workflows/swap_workflow_agent.py` | Multi-step swap | ✅ |
| `agents/workflows/lending_workflow_agent.py` | Multi-step lending | ✅ |
| `agents/workflows/buy_workflow_agent.py` | Fiat on-ramp | ✅ |
| `agents/workflows/transfer_workflow_agent.py` | Token transfer | ✅ |
| `agents/workflows/money_market_workflow_agent.py` | Compare & select | ✅ |
| `agents/enterprise/compliance_monitor_agent_chainalysis.py` | AML/KYC | ✅ |
| `agents/enterprise/multisig_coordinator_agent_gnosis.py` | Treasury | ✅ |
| `agents/enterprise/alert_monitoring_agent_forta.py` | Alerts | ✅ |
| `agents/enterprise/crisis_manager_agent_forta.py` | Emergency | ✅ |
| `agents/advanced/bridge_crosschain_agent_axelar.py` | Cross-chain | ✅ |
| `agents/advanced/lending_borrowing_agent_aave.py` | Leverage | ✅ |
| `agents/advanced/nft_asset_manager_agent_opensea.py` | NFT portfolio | ✅ |
| `agents/advanced/dao_governance_agent_snapshot.py` | Voting | ✅ |

### Infrastructure Layer - Other
| File | Description | Status |
|------|-------------|--------|
| `agent_squad/llm_client_vertex_ai.py` | Vertex AI client | ✅ |
| `agent_squad/llm_client_deepinfra.py` | DeepInfra client | ✅ |
| `agent_squad/llm_client_openai.py` | OpenAI client | ✅ |
| `agent_squad/llm_client_with_fallback.py` | Auto-failover | ✅ |
| `agent_squad/llm_client_gateway_adapter.py` | Unified gateway | ✅ |
| `agent_squad/context_storage_redis.py` | Redis context storage | ✅ |
| `agent_squad/feature_flags_config.py` | Agent feature flags | ✅ |
| `agent_squad/intent_classifier_openai.py` | OpenAI classifier | ✅ |
| `agent_squad/agent_executor_adapter.py` | Agent executor | ✅ |
| `agent_squad/agent_llm_gateway.py` | LLM gateway | ✅ |

### Database Layer
| File | Description | Status |
|------|-------------|--------|
| `mappings/agent_session.py` | SQLAlchemy mapping | ✅ |
| `migrations/.../20251201_004_add_agent_squad_tables.py` | Migration | ✅ |
| `alembic/.../2025_11_27_0100-a1b2c3d4e5f6_add_chat_feature_tables.py` | Chat tables | ✅ |

### Tests
| File | Description | Status |
|------|-------------|--------|
| `tests/e2e/agent_squad/test_api_endpoints.py` | E2E API tests | ✅ 10 tests |
| `tests/component/agent_squad/test_intent_classification.py` | Intent tests | ✅ 7 tests |
| `tests/component/agent_squad/conftest.py` | Test fixtures | ✅ |

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AGENT SESSIONS ARCHITECTURE                                       │
│                                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                   USER INTERFACE                                                 ││
│  │                                                                                                  ││
│  │    ┌────────────────────────────────────────────────────────────────────────────────────────┐  ││
│  │    │                              Chat API                                                   │  ││
│  │    │                                                                                         │  ││
│  │    │  POST /conversations/{id}/messages   POST /guest/chat   POST /agent-squad/supervisor   │  ││
│  │    └─────────────────────────────────────────────┬───────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────┼──────────────────────────────────────────────┘│
│                                                     │                                               │
│                                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                   ORCHESTRATION LAYER                                            ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                                 AgentOrchestrator                                          │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────────────────┐ │ ││
│  │  │  │IntentClassifier │────▶│    FeatureFlags     │────▶│      AgentRegistry              │ │ ││
│  │  │  │                 │     │                     │     │                                 │ │ ││
│  │  │  │ • classify()    │     │ • is_agent_enabled()│     │ • 25+ registered agents         │ │ ││
│  │  │  │ • confidence    │     │ • tier filtering    │     │ • execute_agent()               │ │ ││
│  │  │  └─────────────────┘     └─────────────────────┘     └─────────────────────────────────┘ │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                              SupervisorCoordinator                                         │ ││
│  │  │                                                                                            │ ││
│  │  │  create_workflow_plan() → WorkflowPlan → execute_workflow() → Parallel Execution          │ ││
│  │  │                                ↓                                   ↓                       │ ││
│  │  │                         [AgentTask, AgentTask, ...]         aggregate_results()            │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                                 ContextManager                                             │ ││
│  │  │                                                                                            │ ││
│  │  │  add_message() → get_conversation_context() → get_summary() → estimate_token_count()      │ ││
│  │  │       ↓                      ↓                                                             │ ││
│  │  │  ContextStorageRedis   ConversationContext                                                 │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                     │                                               │
│                                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                      AGENT LAYER (25+)                                           ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                              CORE AGENTS (12)                                              │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌─────────┐ ┌─────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │ ││
│  │  │  │  Chat   │ │ GuestAuth   │ │ Knowledge │ │ HunterAI │ │ Research │ │   Execution    │  │ ││
│  │  │  │         │ │             │ │           │ │          │ │          │ │   (Privy)      │  │ ││
│  │  │  └─────────┘ └─────────────┘ └───────────┘ └──────────┘ └──────────┘ └────────────────┘  │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌─────────────┐ ┌───────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ ││
│  │  │  │RiskAnalyzer │ │ Portfolio │ │ TaxOptimizer │ │DefiYield │ │ Security │ │   Gas    │  │ ││
│  │  │  │             │ │           │ │              │ │          │ │ Auditor  │ │ Optimizer│  │ ││
│  │  │  └─────────────┘ └───────────┘ └──────────────┘ └──────────┘ └──────────┘ └──────────┘  │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                            WORKFLOW AGENTS (5)                                             │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐ ┌───────────────────┐   │ ││
│  │  │  │SwapWorkflow│ │LendingWorkflow│ │BuyWorkflow │ │TransferWorkflow│ │MoneyMarketWorkflow│  │ ││
│  │  │  └────────────┘ └──────────────┘ └────────────┘ └──────────────┘ └───────────────────┘   │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                          ENTERPRISE AGENTS (8)                                             │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌──────────────┐ ┌──────────────────┐ ┌────────────────┐ ┌──────────────────────────┐   │ ││
│  │  │  │ Compliance   │ │ MultisigCoordinator│ │AlertMonitoring │ │     CrisisManager       │   │ ││
│  │  │  │  Monitor     │ │    (Gnosis)       │ │   (Forta)      │ │       (Forta)           │   │ ││
│  │  │  └──────────────┘ └──────────────────┘ └────────────────┘ └──────────────────────────┘   │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌──────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────────┐   │ ││
│  │  │  │   Bridge     │ │LendingBorrowing  │ │  NFTAssetManager │ │   DAOGovernance        │   │ ││
│  │  │  │ (Axelar)     │ │    (Aave)        │ │    (OpenSea)     │ │     (Snapshot)         │   │ ││
│  │  │  └──────────────┘ └──────────────────┘ └──────────────────┘ └────────────────────────┘   │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                     │                                               │
│                                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                    LLM LAYER                                                     ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                           LLMClientWithFallback                                            │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────────────┐   │ ││
│  │  │  │  Vertex AI (Primary)│───▶│ DeepInfra (Fallback)│───▶│     OpenAI (Alternative)    │   │ ││
│  │  │  │                     │    │                     │    │                             │   │ ││
│  │  │  │  $0.10/1M tokens    │    │   Backup provider   │    │   Legacy / Testing          │   │ ││
│  │  │  │  gemini-1.5-flash   │    │                     │    │   gpt-4-turbo               │   │ ││
│  │  │  └─────────────────────┘    └─────────────────────┘    └─────────────────────────────┘   │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                     │                                               │
│                                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                    STORAGE LAYER                                                 ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                                Redis (Context)                                             │ ││
│  │  │                                                                                            │ ││
│  │  │  conversation:{id}:messages  │  conversation:{id}:metadata  │  conversation:{id}:count    │ ││
│  │  │  TTL: 24 hours               │  TTL: 24 hours               │  TTL: 24 hours              │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                                  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │                               PostgreSQL (Persistence)                                     │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────────────────┐  │ ││
│  │  │  │   agent_sessions   │  │  agent_telemetry   │  │   compliance_screening_logs         │  │ ││
│  │  │  │                    │  │                    │  │          (Enterprise)               │  │ ││
│  │  │  │ • conversation_id  │  │ • agent_type       │  │                                     │  │ ││
│  │  │  │ • agent_type       │  │ • latency_ms       │  │ • wallet_address                    │  │ ││
│  │  │  │ • state (JSONB)    │  │ • tokens_used      │  │ • risk_score                        │  │ ││
│  │  │  │ • updated_at       │  │ • tools_used       │  │ • ofac_status                       │  │ ││
│  │  │  └────────────────────┘  │ • success          │  │ • screening_result                  │  │ ││
│  │  │                          └────────────────────┘  └────────────────────────────────────┘  │ ││
│  │  │                                                                                            │ ││
│  │  │  ┌────────────────────────────────┐  ┌────────────────────────────────────────────────┐  │ ││
│  │  │  │      multisig_proposals        │  │              crisis_events                     │  │ ││
│  │  │  │         (Enterprise)           │  │            (Enterprise)                        │  │ ││
│  │  │  │                                │  │                                                │  │ ││
│  │  │  │ • safe_address                 │  │ • event_type (exploit/depeg/...)              │  │ ││
│  │  │  │ • amount_usd                   │  │ • severity                                    │  │ ││
│  │  │  │ • approval_policy (2-of-3)     │  │ • losses_prevented_usd                        │  │ ││
│  │  │  │ • status                       │  │ • crisis_resolved                             │  │ ││
│  │  │  └────────────────────────────────┘  └────────────────────────────────────────────────┘  │ ││
│  │  └───────────────────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### agent_sessions Table
```sql
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    state JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_sessions_conversation ON agent_sessions(conversation_id);
CREATE INDEX idx_agent_sessions_agent_type ON agent_sessions(agent_type);
```

### agent_telemetry Table
```sql
CREATE TABLE agent_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    intent_classification VARCHAR(100),
    intent_confidence FLOAT,
    latency_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    tools_used JSONB DEFAULT '[]',
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_telemetry_agent_type ON agent_telemetry(agent_type);
CREATE INDEX idx_agent_telemetry_created_at ON agent_telemetry(created_at);
```

### compliance_screening_logs Table (Enterprise)
```sql
CREATE TABLE compliance_screening_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_address VARCHAR(42) NOT NULL,
    risk_score INTEGER NOT NULL,
    ofac_status VARCHAR(20) NOT NULL,
    pep_status VARCHAR(20) NOT NULL,
    mixer_exposure_pct FLOAT,
    high_risk_sources_pct FLOAT,
    screening_result VARCHAR(20) NOT NULL,
    screening_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 5. Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| Core Agents (12) | ✅ Production | All operational |
| Workflow Agents (5) | ✅ Production | Multi-step flows |
| Enterprise Agents (8) | ✅ Implemented | Need integration testing |
| Intent Classification | ✅ Production | 85%+ confidence threshold |
| Multi-Agent Workflows | ✅ Production | Parallel execution |
| Context Storage (Redis) | ✅ Production | 24h TTL |
| Session Persistence | ✅ Production | PostgreSQL |
| Telemetry Tracking | ⚠️ Partial | In-memory (TODO: async) |
| Compliance Screening | ⚠️ Stub | API integration needed |
| Crisis Monitoring | ⚠️ Stub | Forta integration needed |
| Unit Tests | ⚠️ Limited | ~35% coverage |

---

## 6. Improvements Roadmap

### Phase 1: Observability (High Priority)
1. **Async Telemetry Tracking**
   - Move telemetry to Celery task
   - Reduce request latency
   - Store in time-series DB

2. **Agent Performance Dashboard**
   - Aggregate telemetry metrics
   - Latency percentiles per agent
   - Success rate monitoring

### Phase 2: Enterprise Features (Medium Priority)
3. **Compliance Integration**
   - Chainalysis API integration
   - TRM Labs integration
   - Real-time wallet screening

4. **Crisis Monitoring**
   - Forta Network integration
   - TVL crash detection
   - Depeg alerts

### Phase 3: Testing & Reliability (Medium Priority)
5. **Increase Test Coverage**
   - Domain service unit tests
   - Infrastructure adapter tests
   - Integration tests

6. **Agent Session Cleanup**
   - Celery task for old sessions
   - Configurable retention

### Phase 4: Advanced Features (Lower Priority)
7. **Agent Collaboration**
   - Agent-to-agent communication
   - Shared context protocols
   - Workflow templates

8. **Custom Agents**
   - User-defined agent configs
   - Custom prompt templates
   - Agent marketplace

---

## 7. Configuration

### Agent Tiers
```python
AGENT_TIERS = {
    "free": [
        "chat", "guest_auth", "knowledge", "hunter_ai", "gas_optimizer"
    ],
    "pro": [
        "chat", "guest_auth", "knowledge", "hunter_ai", "gas_optimizer",
        "research", "risk_analyzer", "portfolio", "defi_yield",
        "security_auditor", "tax_optimizer", "execution"
    ],
    "enterprise": [
        # All pro agents plus:
        "compliance_monitor", "multisig_coordinator", "alert_monitoring",
        "crisis_manager", "bridge_crosschain", "lending_borrowing",
        "nft_asset_manager", "dao_governance",
        # Workflow agents:
        "swap_workflow", "lending_workflow", "buy_workflow",
        "transfer_workflow", "money_market_workflow"
    ],
}
```

### LLM Configuration
```python
LLM_CONFIG = {
    "primary": {
        "provider": "vertex_ai",
        "model": "gemini-1.5-flash",
        "cost_per_1m_tokens": 0.10,
    },
    "fallback": {
        "provider": "deepinfra",
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    },
}
```

### Context Configuration
```python
CONTEXT_CONFIG = {
    "history_limit": 20,      # Max messages in context
    "token_limit": 8000,      # Max context tokens
    "redis_ttl": 86400,       # 24 hours
}
```

---

## 8. Related Modules

| Module | Relationship |
|--------|--------------|
| Chat | Message storage, conversation management |
| Auth | User identity, subscription tier |
| Redis | Context storage |
| Celery | Background tasks (recommended) |
| MCP Servers | External data (CoinGecko, DeFiLlama, etc.) |

---

## References

- **Database Architecture Spec**: `docs/ceo/database-architecture-spec.md` (Section 15)
- **Agent Squad Documentation**: `docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md`
- **Domain Services**: `src/app/domain/services/agent_squad/`
- **Agent Implementations**: `src/app/infrastructure/adapters/agent_squad/agents/`
- **Migration**: `src/app/infrastructure/persistence_sqla/migrations/versions/20251201_004_add_agent_squad_tables.py`

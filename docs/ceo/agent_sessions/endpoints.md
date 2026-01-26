# Agent Sessions Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Agent Sessions module manages stateful agent interactions within conversations. It tracks:
- **Agent state** per conversation (JSONB)
- **Agent telemetry** (latency, tokens, tools used)
- **Enterprise data** (compliance logs, multi-sig proposals, crisis events)

**Note**: Agent Sessions is primarily a **backend infrastructure** module. It doesn't expose dedicated REST endpoints but integrates with the Chat API. Session state is managed internally by the agent orchestration system.

---

## 1. Integration with Chat API

Agent Sessions are created and updated automatically when messages are sent through the unified chat system.

### POST /api/v1/conversations/{conversation_id}/messages (User Chat)
**Path**: `src/app/presentation/http/controllers/chat/conversations_router.py`

When a message is sent, the Agent Squad system:
1. Classifies intent and routes to appropriate agent
2. Creates/updates `AgentSession` for conversation
3. Executes agent with session context
4. Stores response and telemetry

**Agent Session Flow**:
```
User Message → Intent Classification → Agent Routing
      ↓
AgentSession.state loaded (or created)
      ↓
Agent Execution with context
      ↓
AgentSession.state updated
      ↓
AgentTelemetry recorded
      ↓
Response returned
```

### POST /api/v1/guest/chat (Guest Chat)
**Path**: `src/app/presentation/http/controllers/guest/router.py`

Guest users also have agent sessions (stored in Redis with 24h TTL).

---

## 2. Agent Squad API Endpoints (Planned/Internal)

The following endpoints are defined in E2E tests but may not be fully exposed in production:

### POST /api/v1/chat/agent-squad/messages
**Status**: ⚠️ Internal/Planned

Send message to Agent Squad with explicit routing control.

**Authentication**: Required (Bearer Token)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | UUID | Conversation identifier |

**Request Body**:
```json
{
  "content": "What's the current price of ETH?",
  "force_agent": "hunter_ai"  // Optional: bypass intent classification
}
```

**Response**:
```json
{
  "user_message_id": "uuid",
  "agent_message_id": "uuid",
  "agent_type": "hunter_ai",
  "intent_classification": "market_data",
  "intent_confidence": 0.95,
  "content": "The current price of ETH is $2,450...",
  "tools_used": ["coingecko_api", "defillama_api"],
  "latency_ms": 1250,
  "tokens_used": 450,
  "sources": [
    {
      "source_type": "api",
      "source_name": "CoinGecko",
      "provider": "CoinGecko"
    }
  ]
}
```

---

### POST /api/v1/chat/agent-squad/supervisor
**Status**: ⚠️ Internal/Planned

Execute multi-agent supervisor workflow for complex tasks.

**Authentication**: Required (Bearer Token)

**Request Body**:
```json
{
  "complex_task": "Create a balanced DeFi portfolio with $10k",
  "max_agents": 5
}
```

**Response**:
```json
{
  "workflow_id": "uuid",
  "plan": [
    {"agent_type": "research", "task_description": "Find top protocols", "order": 1},
    {"agent_type": "risk_analyzer", "task_description": "Assess protocol risks", "order": 2},
    {"agent_type": "portfolio", "task_description": "Create allocation", "order": 3}
  ],
  "tasks": [
    {"agent_type": "research", "response": "Top protocols by TVL...", "success": true},
    {"agent_type": "risk_analyzer", "response": "Risk scores...", "success": true}
  ],
  "final_synthesis": "Based on analysis, here's your recommended portfolio...",
  "agents_used": 3
}
```

---

### GET /api/v1/chat/agent-squad/agents
**Status**: ⚠️ Internal/Planned

List enabled agents with metadata.

**Authentication**: Required (Bearer Token)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_subscription_tier` | string | Filter by tier (free, pro, enterprise) |

**Response**:
```json
{
  "agents": [
    {
      "agent_type": "chat",
      "name": "Chat Agent",
      "description": "General conversation and assistance",
      "capabilities": ["general_qa", "defi_education"],
      "model": "gemini-1.5-flash",
      "temperature": 0.7,
      "tier_required": "free"
    },
    {
      "agent_type": "hunter_ai",
      "name": "Hunter AI",
      "description": "Market sentiment and price analysis",
      "capabilities": ["price_tracking", "sentiment_analysis"],
      "model": "gemini-1.5-flash",
      "temperature": 0.5,
      "tier_required": "free"
    }
  ],
  "total_count": 18
}
```

**Agent Availability by Tier**:
| Tier | Agents Available |
|------|------------------|
| Free | 5 (chat, hunter_ai, knowledge, guest_auth, gas_optimizer) |
| Pro | 12 (core agents) |
| Enterprise | 25 (all agents including enterprise) |

---

## 3. Database Tables (No Direct API)

### agent_sessions Table
Stores agent state per conversation.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `conversation_id` | UUID | FK to chat_conversations |
| `agent_type` | Enum | Agent type (chat, hunter_ai, etc.) |
| `state` | JSONB | Agent-specific state data |
| `created_at` | DateTime | Session creation time |
| `updated_at` | DateTime | Last state update |

**Example State Data**:
```json
{
  "last_intent": "market_data",
  "tokens_analyzed": ["ETH", "BTC", "USDC"],
  "user_preferences": {
    "risk_tolerance": "moderate",
    "preferred_chains": ["ethereum", "arbitrum"]
  }
}
```

---

### agent_telemetry Table
Performance metrics for all agents.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `agent_type` | String | Agent type |
| `conversation_id` | UUID | FK to conversations |
| `message_id` | UUID | FK to messages |
| `intent_classification` | String | Classified intent |
| `intent_confidence` | Float | Confidence (0.0-1.0) |
| `latency_ms` | Integer | Response time |
| `tokens_used` | Integer | LLM tokens consumed |
| `tools_used` | JSONB | Tools/APIs used |
| `success` | Boolean | Call succeeded |
| `error_message` | Text | Error if failed |
| `created_at` | DateTime | Timestamp |

---

### compliance_screening_logs Table (Enterprise)
AML/KYC screening results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK to users |
| `wallet_address` | String(42) | Ethereum address |
| `risk_score` | Integer | Risk score (0-100) |
| `ofac_status` | String | clear / sanctioned |
| `pep_status` | String | clear / detected |
| `mixer_exposure_pct` | Float | Mixer fund % |
| `screening_result` | String | approved / blocked / review |
| `screening_data` | JSONB | Full API response |

---

### multisig_proposals Table (Enterprise)
Multi-sig treasury management.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `safe_address` | String(42) | Gnosis Safe address |
| `transaction_hash` | String(66) | TX hash (after execution) |
| `nonce` | Integer | Safe nonce |
| `amount_usd` | Numeric | Amount in USD |
| `destination_address` | String(42) | Destination wallet |
| `purpose` | Text | Transaction purpose |
| `budget_code` | String | Budget tracking code |
| `approval_policy` | String | 2-of-3, 3-of-5, etc. |
| `approvals` | JSONB | Approval signatures |
| `status` | String | pending / approved / executed |

---

### crisis_events Table (Enterprise)
Emergency response tracking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK to users |
| `event_type` | String | exploit / depeg / flash_crash / liquidation_risk |
| `protocol_name` | String | Affected protocol |
| `severity` | String | critical / high / medium / low |
| `user_exposure_usd` | Numeric | User's exposure |
| `response_time_ms` | Integer | Crisis response time |
| `actions_taken` | JSONB | Automated actions |
| `losses_prevented_usd` | Numeric | Estimated savings |
| `crisis_resolved` | Boolean | Resolution status |

---

## 4. Agent Types (25 Total)

### Core User-Facing Agents (12)
| Agent | Type | Description |
|-------|------|-------------|
| Chat | `chat` | General conversation |
| Guest Auth | `guest_auth` | Auth prompts for restricted features |
| Knowledge | `knowledge` | Educational/Anvil knowledge |
| Hunter AI | `hunter_ai` | Market sentiment & prices |
| Research | `research` | Deep protocol analysis |
| Execution | `execution` | Transaction execution |
| Risk Analyzer | `risk_analyzer` | Risk assessment |
| Portfolio | `portfolio` | Portfolio optimization |
| Tax Optimizer | `tax_optimizer` | Tax-loss harvesting |
| DeFi Yield | `defi_yield` | Yield farming analysis |
| Security Auditor | `security_auditor` | Smart contract security |
| Gas Optimizer | `gas_optimizer` | Gas fee optimization |

### Authenticated Agents (2)
| Agent | Type | Description |
|-------|------|-------------|
| Wallet | `wallet` | Wallet management |
| Transaction History | `transaction_history` | TX history queries |

### Workflow Agents (5)
| Agent | Type | Description |
|-------|------|-------------|
| Swap Workflow | `swap_workflow` | Multi-step swap |
| Lending Workflow | `lending_workflow` | Multi-step lending |
| Buy Workflow | `buy_workflow` | Fiat on-ramp |
| Transfer Workflow | `transfer_workflow` | Token transfer |
| Money Market | `money_market_workflow` | Compare & select |

### Enterprise Agents (8)
| Agent | Type | Description |
|-------|------|-------------|
| Compliance Monitor | `compliance_monitor` | AML/KYC |
| Multi-Sig Coordinator | `multisig_coordinator` | Treasury management |
| Alert Monitoring | `alert_monitoring` | Real-time alerts |
| Crisis Manager | `crisis_manager` | Emergency response |
| Bridge Crosschain | `bridge_crosschain` | Cross-chain ops |
| Lending Borrowing | `lending_borrowing` | Leverage/collateral |
| NFT Asset Manager | `nft_asset_manager` | NFT portfolio |
| DAO Governance | `dao_governance` | Voting/proposals |

---

## 5. Context Storage (Redis)

Agent sessions use Redis for fast context storage:

**Redis Keys**:
```
conversation:{id}:messages     # List of messages (JSON)
conversation:{id}:metadata     # Conversation metadata (JSON)
conversation:{id}:count        # Message count (integer)
```

**TTL**: 24 hours (86400 seconds)

---

## References

- **AgentSession Entity**: `src/app/domain/entities/agent_session.py`
- **AgentSession Mapping**: `src/app/infrastructure/persistence_sqla/mappings/agent_session.py`
- **Agent Type Enum**: `src/app/domain/enums/agent_type.py`
- **Agent Gateway Port**: `src/app/domain/ports/agent_squad/agent_gateway.py`
- **Context Storage Redis**: `src/app/infrastructure/adapters/agent_squad/context_storage_redis.py`
- **Conversation Router**: `src/app/presentation/http/controllers/chat/conversations_router.py`
- **E2E Tests**: `tests/e2e/agent_squad/test_api_endpoints.py`

# Agent Squad API Reference

**Document**: AgentSquad-APIReference  
**Date**: December 1, 2025  
**Version**: 1.0  
**Base URL**: `https://api.anvil.com/api/v1`

---

## 🔐 Authentication

All endpoints require authentication via Bearer token.

```http
Authorization: Bearer <your_jwt_token>
```

---

## 📡 Endpoints

### 1. Send Message (Intelligent Routing)

**Endpoint**: `POST /chat/agent-squad/messages`

**Description**: Send message with automatic agent routing

**Request**:

```json
{
  "content": "What's the market sentiment for Bitcoin?",
  "force_agent": "hunter_ai"  // Optional: Force specific agent
}
```

**Query Parameters**:
- `conversation_id` (required): UUID of conversation

**Response** (201 Created):

```json
{
  "user_message_id": "uuid",
  "agent_message_id": "uuid",
  "agent_type": "hunter_ai",
  "intent_classification": "market_sentiment",
  "intent_confidence": 0.92,
  "content": "Bitcoin sentiment is 75/100 (Bullish)...",
  "tools_used": ["openai_api", "coingecko_api"],
  "latency_ms": 1250,
  "tokens_used": 350
}
```

---

### 2. Execute Supervisor Workflow

**Endpoint**: `POST /chat/agent-squad/supervisor`

**Description**: Execute complex multi-agent workflow

**Request**:

```json
{
  "content": "Create a balanced DeFi portfolio with 10k USDC",
  "max_agents": 5,
  "timeout_seconds": 120
}
```

**Query Parameters**:
- `conversation_id` (required): UUID of conversation

**Response** (201 Created):

```json
{
  "workflow_id": "uuid",
  "conversation_id": "uuid",
  "status": "completed",
  "tasks": [
    {
      "agent_type": "research",
      "task_description": "Find top DeFi protocols",
      "status": "completed",
      "result": "Aave, Compound, Curve..."
    },
    {
      "agent_type": "risk_analyzer",
      "task_description": "Assess protocol risks",
      "status": "completed",
      "result": "Aave: 28/100, Compound: 32/100..."
    },
    {
      "agent_type": "portfolio",
      "task_description": "Create allocation",
      "status": "completed",
      "result": "40% Aave, 30% Compound, 20% Curve, 10% Cash"
    }
  ],
  "final_response": "Balanced portfolio created: 40% Aave (4.5% APY)...",
  "total_latency_ms": 8500,
  "agents_used": ["research", "risk_analyzer", "portfolio"]
}
```

---

### 3. List Enabled Agents

**Endpoint**: `GET /chat/agent-squad/agents`

**Description**: Get list of enabled agents for current user

**Response** (200 OK):

```json
{
  "agents": [
    {
      "agent_type": "chat",
      "name": "Chat Agent",
      "description": "General conversation and guidance",
      "model": "gpt-4o-mini",
      "temperature": 0.7,
      "enabled": true,
      "is_enterprise": false
    },
    {
      "agent_type": "hunter_ai",
      "name": "Hunter AI",
      "description": "Market sentiment & predictions",
      "model": "gpt-4o",
      "temperature": 0.3,
      "enabled": true,
      "is_enterprise": false
    },
    {
      "agent_type": "compliance_monitor",
      "name": "Compliance Monitor",
      "description": "AML/KYC compliance screening",
      "model": "gpt-4o",
      "temperature": 0.1,
      "enabled": false,  // Enterprise only
      "is_enterprise": true
    }
    // ... all 18 agents
  ],
  "total": 18,
  "core_agents": 10,
  "enterprise_agents": 8
}
```

---

## 🎯 Agent Types

### Core User Agents (10)

| Agent Type | Value | Tier |
|------------|-------|------|
| Chat | `chat` | Free |
| Hunter AI | `hunter_ai` | Basic |
| Research | `research` | Basic |
| Execution | `execution` | Pro |
| Risk Analyzer | `risk_analyzer` | Pro |
| Portfolio | `portfolio` | Pro |
| Tax Optimizer | `tax_optimizer` | Pro |
| DeFi Yield | `defi_yield` | Pro |
| Security Auditor | `security_auditor` | Pro |
| Gas Optimizer | `gas_optimizer` | Pro |

### Enterprise Agents (8)

| Agent Type | Value | Tier |
|------------|-------|------|
| Compliance Monitor | `compliance_monitor` | Enterprise |
| Multi-Sig Coordinator | `multisig_coordinator` | Enterprise |
| Alert Monitoring | `alert_monitoring` | Pro |
| Crisis Manager | `crisis_manager` | Enterprise |
| Bridge Crosschain | `bridge_crosschain` | Pro |
| Lending Borrowing | `lending_borrowing` | Pro |
| NFT Asset Manager | `nft_asset_manager` | Pro |
| DAO Governance | `dao_governance` | Basic |

---

## 📊 Intent Categories (30+)

**General**:
- `general_chat`, `greeting`, `help_request`

**Market**:
- `market_sentiment`, `price_prediction`, `market_analysis`

**Research**:
- `protocol_research`, `tokenomics_analysis`, `compare_protocols`

**Trading**:
- `swap_tokens`, `check_price`, `estimate_gas`

**Risk**:
- `risk_analysis`, `check_security`, `liquidation_risk`

**Portfolio**:
- `portfolio_optimization`, `rebalancing`, `diversification`

**... and 15+ more**

---

## ⚠️ Error Codes

| Code | Description | Action |
|------|-------------|--------|
| 401 | Unauthorized | Check Bearer token |
| 403 | Forbidden | Upgrade tier |
| 404 | Not Found | Check conversation_id |
| 429 | Rate Limited | Wait and retry |
| 500 | Internal Error | Contact support |
| 501 | Not Implemented | Feature in development |
| 503 | Service Unavailable | Retry with backoff |

---

## 🔄 Rate Limits

| Tier | Rate Limit | Burst |
|------|------------|-------|
| Free | 10 req/hour | 20 |
| Basic | 100 req/hour | 150 |
| Pro | 1000 req/hour | 1500 |
| Enterprise | Unlimited | Unlimited |

---

## 📝 Examples

### Example 1: Simple Chat

```bash
curl -X POST https://api.anvil.com/api/v1/chat/agent-squad/messages?conversation_id=<uuid> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello! What can you help me with?"
  }'
```

### Example 2: Force Specific Agent

```bash
curl -X POST https://api.anvil.com/api/v1/chat/agent-squad/messages?conversation_id=<uuid> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Analyze Aave protocol risk",
    "force_agent": "risk_analyzer"
  }'
```

### Example 3: Multi-Agent Workflow

```bash
curl -X POST https://api.anvil.com/api/v1/chat/agent-squad/supervisor?conversation_id=<uuid> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Create tax-optimized portfolio for 50k USDC",
    "max_agents": 5,
    "timeout_seconds": 120
  }'
```

---

## 🚀 SDK Support

### Python SDK (Coming Soon)

```python
from anvil import AgentSquad

client = AgentSquad(api_key="...")

# Send message
response = await client.send_message(
    conversation_id=conversation_id,
    content="What's the market sentiment?",
)

print(response.agent_type)  # "hunter_ai"
print(response.content)     # Agent response
```

### JavaScript SDK (Coming Soon)

```javascript
import { AgentSquad } from '@anvil/agent-squad';

const client = new AgentSquad({ apiKey: '...' });

// Send message
const response = await client.sendMessage({
  conversationId: conversationId,
  content: "What's the market sentiment?",
});

console.log(response.agentType);  // "hunter_ai"
console.log(response.content);    // Agent response
```

---

**OpenAPI Spec**: Available at `/api/v1/docs` (Swagger UI)

---

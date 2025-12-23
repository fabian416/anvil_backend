# FRONTEND_USER_CHAT_MAIN

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/chat` & `src/app/presentation/http/schemas/chat.py`

## 1. Module Overview
The **AI Chat Module** is the central intelligence hub of Anvil. It is not just a text interface but a multi-agent orchestration platform integrating **GraphRAG** (Graph Retrieval-Augmented Generation), **ML Risk Analysis**, and **Agent Squad** routing.

**Key Capabilities:**
*   **Multi-Agent Routing**: Automatically routes queries to the best agent (Chat, Hunter AI, Risk, etc.).
*   **GraphRAG Search**: Hybrid semantic + graph search for protocols.
*   **Real-Time Risk**: ML-powered risk analysis for any protocol mentioned.
*   **Intent Awareness**: Real-time intent detection while typing.

---

## 2. Core Conversation Endpoints

### 2.1 Create Conversation
**POST** `/api/v1/user/chat/conversations`

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `title` | `string` | No | Optional title (max 200 chars). If omitted, generated from first message. |

**Response (201 Created):**
```json
{
  "id": "uuid",
  "user_id": 123,
  "title": "DeFi Strategy",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 2.2 List Conversations
**GET** `/api/v1/user/chat/conversations`
*   Query Params: `limit` (int, default 20), `offset` (int, default 0).

**Response (200 OK):**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "user_id": 123,
      "title": "Portfolio Analysis",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 15
}
```

### 2.3 Send Message (Basic)
**POST** `/api/v1/user/chat/conversations/{conversation_id}/messages`

> **Note**: For advanced routing, use the Agent Squad endpoint (Section 4). This endpoint uses the default Chat Agent.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `content` | `string` | **Yes** | User message content (max 10,000 chars). |

**Response (201 Created):**
```json
{
  "user_message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "user",
    "content": "Hello",
    "created_at": "..."
  },
  "agent_message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "Hello! How can I help?",
    "agent_type": "chat_agent",
    "created_at": "..."
  }
}
```

---

## 3. GraphRAG & Intelligence Endpoints

### 3.1 Search Protocols (GraphRAG)
**POST** `/api/v1/user/chat/search-protocols`

Performs a hybrid search (Semantic + Graph) to find protocols.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `conversation_id` | `UUID` | **Yes** | Context for the search. |
| `query` | `string` | **Yes** | Search query (e.g., "high yield stablecoin pools"). |
| `user_preferences` | `dict` | No | Optional filters. |
| `limit` | `int` | No | Default 5 (max 20). |

**Response (200 OK):**
```json
{
  "results": [
    {
      "protocol_id": "string",
      "protocol_name": "Aave V3",
      "similarity_score": 0.95,
      "risk_score": 2.1,
      "risk_level": "LOW",
      "tvl": 5000000000.0,
      "apy": 4.5,
      "audit_count": 5,
      "description": "Liquidity protocol...",
      "category": "Lending",
      "chain": "Ethereum",
      "why_relevant": "Matches keyword 'lending' and high TVL."
    }
  ],
  "search_context": "Found 3 lending protocols with low risk...",
  "recommendations": ["Check Aave V3", "Compare with Compound"]
}
```

### 3.2 Analyze Risk (ML)
**POST** `/api/v1/user/chat/analyze-risk`

Real-time ML risk assessment for a specific protocol.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `conversation_id` | `UUID` | **Yes** | Context. |
| `protocol_name` | `string` | **Yes** | Protocol to analyze. |
| `operation_type` | `string` | No | `supply`, `borrow`, `swap`, `stake`, `bridge`. |
| `amount_usd` | `float` | No | Transaction amount for risk scaling. |

**Response (200 OK):**
```json
{
  "risk_analysis": {
    "protocol_id": "string",
    "protocol_name": "Euler",
    "risk_score": 7.8,
    "risk_level": "HIGH",
    "confidence": 0.92,
    "contributing_factors": [
      {
        "factor": "Audit History",
        "impact": 8.5,
        "description": "Previous hack in 2023",
        "is_critical": true
      }
    ],
    "should_warn": true,
    "warning_message": "High risk detected due to past incidents."
  },
  "alternatives": [
    {
      "protocol_name": "Aave V3",
      "risk_score": 2.1,
      "why_better": "Significantly lower historical risk."
    }
  ],
  "contextual_message": "Be careful with Euler..."
}
```

### 3.3 Find Similar Protocols
**POST** `/api/v1/user/chat/similar-protocols`

Uses graph embeddings to find semantically similar protocols.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `conversation_id` | `UUID` | **Yes** | Context. |
| `protocol_name` | `string` | **Yes** | Base protocol. |
| `limit` | `int` | No | Default 5. |

---

## 4. Agent Squad Endpoints (Advanced Routing)

### 4.1 Send Agent Squad Message
**POST** `/api/v1/user/chat/agent-squad/messages`

**The primary endpoint for "Smart" Chat.** Automatically classifies intent and routes to:
*   `hunter_ai`: For price predictions.
*   `risk_agent`: For risk analysis.
*   `security_auditor`: For contract checks.
*   `chat_agent`: For general chit-chat.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `content` | `string` | **Yes** | User message. |
| `force_agent` | `string` | No | Force routing (e.g., `hunter_ai`). |

**Response (200 OK):**
```json
{
  "user_message_id": "uuid",
  "agent_message_id": "uuid",
  "agent_type": "hunter_ai",
  "intent_classification": "market_analysis",
  "intent_confidence": 0.98,
  "content": "Bitcoin is currently bullish...",
  "tools_used": ["price_api", "sentiment_model"],
  "latency_ms": 450
}
```

### 4.2 Execute Supervisor Workflow
**POST** `/api/v1/user/chat/agent-squad/supervisor`

Orchestrates multiple agents for complex tasks (e.g., "Build me a low-risk portfolio").

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `conversation_id` | `UUID` | **Yes** | Context. |
| `complex_task` | `string` | **Yes** | Task description. |
| `max_agents` | `int` | No | Limit agents (default 5). |

**Response (200 OK):**
```json
{
  "workflow_id": "uuid",
  "status": "completed",
  "tasks": [
    {
      "agent_type": "research_agent",
      "task_description": "Find stablecoins",
      "status": "completed",
      "result": "Found USDC, DAI..."
    },
    {
      "agent_type": "risk_agent",
      "task_description": "Analyze risk",
      "status": "completed",
      "result": "USDC is safest..."
    }
  ],
  "final_response": "Here is your portfolio allocation..."
}
```

---

## 5. Intent Detection Endpoints

### 5.1 Detect Intent
**POST** `/api/v1/user/chat/intent/detect`

Used for "Real-time Intent" (while user types or before sending).

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `message` | `string` | **Yes** | Partial or full message. |
| `include_suggestions`| `bool` | No | Return suggested agents? (default True). |

**Response (200 OK):**
```json
{
  "intent": {
    "intent_type": "trade_execution",
    "confidence": 0.95,
    "confidence_level": "high",
    "suggested_agent": "transaction_executor"
  },
  "suggested_agents": [
    {
      "agent_name": "transaction_executor",
      "confidence": 0.95,
      "reasoning": "User wants to swap tokens."
    }
  ]
}
```

### 5.2 Autocomplete
**POST** `/api/v1/user/chat/intent/autocomplete`

Provides type-ahead suggestions for protocols, tokens, and actions.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `partial_message` | `string` | **Yes** | Text so far. |
| `limit` | `int` | No | Default 10. |

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "completion_text": "swap ETH for USDC",
      "display_text": "Swap ETH → USDC",
      "suggestion_type": "action",
      "confidence": 0.8
    }
  ]
}
```

## 6. Error Handling

| Status Code | Code | Message | UI Behavior |
| :--- | :--- | :--- | :--- |
| 401 | `UNAUTHORIZED` | "Not authenticated" | Redirect to Login. |
| 404 | `NOT_FOUND` | "Conversation/Protocol not found" | Show error toast. |
| 422 | `VALIDATION_ERROR`| "Field required" | Highlight input error. |
| 500 | `INTERNAL_ERROR` | "Agent execution failed" | Show retry button. |

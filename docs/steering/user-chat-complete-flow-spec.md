# User Chat Complete Flow Specification

**Version:** 1.0
**Created:** 2026-01-06
**Purpose:** Complete end-to-end flow specification for authenticated user chat (`/messages` and `/execute` endpoints).

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATED USER CHAT COMPLETE FLOW                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   HTTP API   │───▶│ CurrentUser  │───▶│  Orchestrator │───▶│   Handler    │       │
│  │  Controller  │    │   Service    │    │   (Unified)  │    │   Service    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                   │               │
│         ▼                   ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ JWT/Bearer   │    │ Rate Limiter │    │    Intent    │    │    Agent     │       │
│  │ Auth Scheme  │    │ (200/hour)   │    │   Detector   │    │ Orchestrator │       │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                     │               │
│                                                                     ▼               │
│                            ┌─────────────────────────────────────────┐              │
│                            │          18 Agents + Execute           │              │
│                            │    (Vertex AI gemini-2.0-flash-exp)    │              │
│                            └─────────────────────────────────────────┘              │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           EXECUTE ENDPOINT                                    │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐  │   │
│  │  │ Simulate │───▶│ Confirm  │───▶│  Wallet  │───▶│ Execute  │───▶│  Tx    │  │   │
│  │  │ (false)  │    │ (true)   │    │ (Privy)  │    │  Action  │    │  Hash  │  │   │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Endpoints Overview

### 2.1 Message Endpoint
```http
POST /api/v1/user/chat/conversations/{conversation_id}/messages
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "swap 1 ETH to USDC",
  "language": "en"
}
```

### 2.2 Execute Endpoint
```http
POST /api/v1/user/chat/conversations/{conversation_id}/execute
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "action_type": "swap",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "1.0",
  "chain": "base",
  "confirmed": false,
  "language": "en"
}
```

---

## 3. Message Flow (/messages)

### 3.1 Request Flow Stages
**File:** `src/app/presentation/http/controllers/chat/router.py`

```
POST /api/v1/user/chat/conversations/{conversation_id}/messages
│
├── Step 1: Authentication
│   └── Bearer JWT token validation
│       └── CurrentUserService.get_current_user()
│           ├── Decode JWT token
│           ├── Validate session
│           └── Return User entity
│
├── Step 2: Authorization
│   └── Verify conversation ownership
│       ├── Get conversation by ID
│       └── Check user_id matches
│
├── Step 3: Rate Limiting (Authenticated)
│   └── RateLimitService.check_and_increment(user)
│       ├── AUTHENTICATED: 200 messages/hour, 1000/day
│       ├── PREMIUM: Unlimited
│       └── Returns remaining quota
│
├── Step 4: Context Retrieval
│   └── ConversationMemory.get_context(conversation_id)
│       ├── Last 10 messages
│       ├── Pending actions
│       └── User wallet info
│
├── Step 5: Intent Detection
│   └── IntentDetectorService.detect_intent()
│       ├── LLM classification (primary)
│       ├── Keyword fallback
│       └── Returns: intent, confidence, entities
│
├── Step 6: Handler Routing
│   └── UnifiedChatOrchestrator.execute()
│       ├── GraphRAG handlers (search, risk, similar)
│       ├── Hunter AI handlers (6 intents)
│       ├── ULTRA handlers (4 intents)
│       ├── DeFi handlers (7 intents)
│       ├── Agent Squad (specialist, complex)
│       └── Regular chat (fallback)
│
├── Step 7: Message Persistence
│   └── Save to conversation history
│       ├── User message
│       ├── Assistant message
│       └── Metadata (intent, handler, pending_action)
│
└── Step 8: Response
    └── UnifiedChatResponse
        ├── user_message: {}
        ├── agent_message: {}
        ├── routing: {intent, confidence, handler}
        └── enrichment: {protocols, tools_used, etc.}
```

### 3.2 UnifiedChatOrchestrator Flow
**File:** `src/app/application/chat/commands/send_message_unified.py`

```
UnifiedChatOrchestrator.execute(user_id, conversation_id, content, language)
│
├── Validate language (en, es, fr, zh, pt)
├── Verify conversation ownership
├── Get conversation history (last 10)
├── Detect intent
│
├── Route by Intent:
│   │
│   ├── PROTOCOL_SEARCH → _handle_protocol_search()
│   │   └── GraphRAG hybrid search
│   │
│   ├── RISK_ASSESSMENT → _handle_risk_assessment()
│   │   └── ML-powered risk analysis
│   │
│   ├── SIMILAR_PROTOCOLS → _handle_similar_protocols()
│   │   └── GraphRAG similarity search
│   │
│   ├── HUNTER_SENTIMENT → _handle_hunter_sentiment()
│   │   └── SentimentAggregator (Twitter, Reddit, Discord, News)
│   │
│   ├── HUNTER_PRICE_PREDICTION → _handle_hunter_price_prediction()
│   │   └── LSTMPricePredictor (CoinGecko OHLCV)
│   │
│   ├── HUNTER_RISK_SIGNALS → _handle_hunter_risk_signals()
│   │   └── RiskAnalyzer
│   │
│   ├── HUNTER_TRADING_SIGNALS → _handle_hunter_trading_signals()
│   │   └── TradingSignalGenerator
│   │
│   ├── HUNTER_PATTERNS → _handle_hunter_patterns()
│   │   └── PatternRecognizer
│   │
│   ├── HUNTER_PORTFOLIO → _handle_hunter_portfolio()
│   │   └── PortfolioOptimizer
│   │
│   ├── ULTRA_ARBITRAGE → _handle_ultra_arbitrage()
│   │   └── ArbitrageDiscovery
│   │
│   ├── ULTRA_FLASH_LOANS → _handle_ultra_flash_loans()
│   │   └── FlashLoanEngine
│   │
│   ├── ULTRA_MEV_PROTECTION → _handle_ultra_mev_protection()
│   │   └── MEVProtection
│   │
│   ├── ULTRA_AUTO_EXECUTOR → _handle_ultra_auto_executor()
│   │   └── AutoExecutor
│   │
│   ├── LENDING → _handle_lending()
│   │   └── LendingHandler (Morpho, Aave, Compound)
│   │
│   ├── MONEY_MARKET → _handle_money_market()
│   │   └── MoneyMarketHandler
│   │
│   ├── SWAP → _handle_swap()
│   │   └── SwapHandler (1inch, LiFi)
│   │
│   ├── BALANCE → _handle_balance()
│   │   └── PortfolioHandler (Privy wallet)
│   │
│   ├── PORTFOLIO → _handle_portfolio()
│   │   └── PortfolioHandler (full enumeration)
│   │
│   ├── ACTIVITY → _handle_activity()
│   │   └── ActivityHandler (transaction history)
│   │
│   ├── RECEIVE → _handle_receive()
│   │   └── ReceiveHandler (QR, address, ENS)
│   │
│   ├── SPECIALIST_TASK → _handle_specialist_task()
│   │   └── AgentSquad.route_to_specialist()
│   │
│   ├── COMPLEX_WORKFLOW → _handle_complex_workflow()
│   │   └── Supervisor.coordinate_agents()
│   │
│   └── GENERAL_CONVERSATION → _handle_general_conversation()
│       └── RegularChat (tools + context)
│
└── Return unified response with routing metadata
```

---

## 4. Execute Flow (/execute)

### 4.1 Two-Step Confirmation Flow
**File:** `src/app/application/chat/commands/execute_action.py`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXECUTE ACTION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: SIMULATE (confirmed: false)                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Request → Validate → Get Wallet → Get Quote → Simulate → Preview   │   │
│  │                                                                      │   │
│  │  Response:                                                           │   │
│  │  {                                                                   │   │
│  │    "status": "awaiting_confirmation",                                │   │
│  │    "requires_confirmation": true,                                    │   │
│  │    "confirmation_message": "Swap 1.0 ETH → USDC on BASE?",          │   │
│  │    "simulation": {                                                   │   │
│  │      "success": true,                                                │   │
│  │      "estimated_gas": 200000,                                        │   │
│  │      "estimated_gas_usd": 0.50,                                      │   │
│  │      "output_amount": "3024.50",                                     │   │
│  │      "price_impact": 0.1%                                            │   │
│  │    },                                                                │   │
│  │    "expires_at": "2026-01-06T12:05:00Z"                             │   │
│  │  }                                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                         │                                    │
│                                         ▼                                    │
│  Step 2: EXECUTE (confirmed: true)                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Request → Validate → Get Wallet → Build Tx → Sign (Privy) → Send   │   │
│  │                                                                      │   │
│  │  Response:                                                           │   │
│  │  {                                                                   │   │
│  │    "status": "pending",                                              │   │
│  │    "requires_confirmation": false,                                   │   │
│  │    "transaction": {                                                  │   │
│  │      "hash": "0x1234...abcd",                                        │   │
│  │      "chain": "base",                                                │   │
│  │      "status": "pending"                                             │   │
│  │    }                                                                 │   │
│  │  }                                                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Supported Actions
**File:** `src/app/application/chat/commands/execute_action.py`

| Action | Description | Required Fields | Integrations |
|--------|-------------|-----------------|--------------|
| `swap` | Token swap via DEX | from_token, to_token, amount | 1inch, LiFi |
| `deposit` | Deposit to lending protocol | protocol, token, amount | Morpho, Aave, Compound |
| `withdraw` | Withdraw from lending protocol | protocol, token, amount | Morpho, Aave, Compound |
| `transfer` | Send tokens to address | to_address, token, amount | Privy wallet |
| `approve` | Approve token spending | spender, token, amount | ERC20 contracts |
| `bridge` | Cross-chain bridge | from_chain, to_chain, token, amount | LiFi |

### 4.3 Execute Command Flow
```
ExecuteActionCommand.execute()
│
├── Step 1: Validate Conversation Access
│   └── Check user owns conversation
│
├── Step 2: Get User Wallet (Privy)
│   └── WalletRepository.get_by_user_id()
│       ├── Return primary wallet address
│       └── Error if no wallet connected
│
├── Step 3: Route by Action Type
│   ├── swap → _handle_swap()
│   │   ├── Cross-chain: LiFi quote
│   │   └── Same-chain: 1inch quote
│   │
│   ├── deposit → _handle_deposit()
│   │   └── Morpho/Aave vault deposit
│   │
│   ├── withdraw → _handle_withdraw()
│   │   └── Morpho/Aave vault withdraw
│   │
│   ├── transfer → _handle_transfer()
│   │   └── Token transfer
│   │
│   ├── approve → _handle_approve()
│   │   └── ERC20 approval
│   │
│   └── bridge → _handle_bridge()
│       └── LiFi cross-chain bridge
│
├── Step 4: Simulation (if not confirmed)
│   ├── Get quote from aggregator
│   ├── Estimate gas costs
│   ├── Calculate output amount
│   └── Return preview with expiry (5 min)
│
└── Step 5: Execution (if confirmed)
    ├── Build transaction
    ├── Sign via Privy
    ├── Submit to network
    └── Return transaction hash
```

---

## 5. Authentication & Authorization

### 5.1 JWT Bearer Token
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5.2 CurrentUserService Flow
**File:** `src/app/application/common/services/current_user.py`

```
CurrentUserService.get_current_user()
├── Extract token from Authorization header
├── Validate JWT signature
├── Decode payload (user_id, session_id, exp)
├── Verify session is active
├── Load User entity from database
└── Return authenticated User
```

### 5.3 Rate Limits by User Type
| User Type | Hourly Limit | Daily Limit | Execute Limits |
|-----------|--------------|-------------|----------------|
| Guest | 20 | 50 | None (no execute) |
| Authenticated | 200 | 1000 | Standard limits |
| Premium | Unlimited | Unlimited | Higher limits |

### 5.4 Transaction Safety Limits
```python
MAX_SWAP_VALUE_USD = Decimal("50000")
MAX_DEPOSIT_VALUE_USD = Decimal("100000")
MAX_TRANSFER_VALUE_USD = Decimal("10000")
CONFIRMATION_EXPIRY_MINUTES = 5
```

---

## 6. Wallet Integration (Privy)

### 6.1 Wallet Repository
**File:** `src/app/domain/ports/wallet/wallet_repository.py`

```python
class WalletRepository(Protocol):
    async def get_by_user_id(self, user_id: UserId) -> list[Wallet]:
        """Get all wallets for user."""
        ...

    async def get_primary(self, user_id: UserId) -> Wallet | None:
        """Get primary wallet for user."""
        ...
```

### 6.2 Wallet Operations Flow
```
User Request → Check Wallet Connected → Get Quote → Simulate → Confirm → Execute
                     │
                     ▼
              ┌─────────────┐
              │   Privy     │
              │   Wallet    │
              ├─────────────┤
              │ - Address   │
              │ - Chain     │
              │ - Balance   │
              │ - Sign Tx   │
              └─────────────┘
```

---

## 7. Intent Classification (Authenticated)

### 7.1 Full Intent Access
Unlike guests, authenticated users have access to ALL 23 intents:

| Category | Intents | Handler |
|----------|---------|---------|
| **GraphRAG** | PROTOCOL_SEARCH, RISK_ASSESSMENT, SIMILAR_PROTOCOLS | GraphRAG |
| **Hunter AI** | HUNTER_SENTIMENT, HUNTER_PRICE_PREDICTION, HUNTER_RISK_SIGNALS, HUNTER_TRADING_SIGNALS, HUNTER_PATTERNS, HUNTER_PORTFOLIO | Hunter tools |
| **ULTRA** | ULTRA_ARBITRAGE, ULTRA_FLASH_LOANS, ULTRA_MEV_PROTECTION, ULTRA_AUTO_EXECUTOR | ULTRA tools |
| **DeFi** | LENDING, MONEY_MARKET, SWAP, BALANCE, PORTFOLIO, ACTIVITY, RECEIVE | DeFi handlers |
| **Agent Squad** | SPECIALIST_TASK, COMPLEX_WORKFLOW | Agent orchestration |
| **Fallback** | GENERAL_CONVERSATION | Chat agent |

### 7.2 No Restricted Intents
Authenticated users can access:
- `PORTFOLIO` - Full portfolio enumeration from Privy wallet
- `BALANCE` - Token balances across chains
- `ACTIVITY` - Transaction history
- `RECEIVE` - Wallet address, QR code, ENS

---

## 8. Agent Orchestration

### 8.1 Agent Squad Message Flow
**File:** `src/app/application/agent_squad/commands/send_agent_squad_message.py`

```
SendAgentSquadMessage.execute()
├── Get conversation context
├── Classify intent with LLM
├── Select best agent based on:
│   ├── Intent type
│   ├── Confidence score
│   ├── Agent availability
│   └── User subscription tier
├── Execute selected agent
├── Save to conversation history
└── Return response with agent metadata
```

### 8.2 Supervisor Workflow Flow
**File:** `src/app/application/agent_squad/commands/execute_supervisor_workflow.py`

```
ExecuteSupervisorWorkflow.execute()
├── Analyze complex task
├── Break into subtasks
├── Select agents for each subtask:
│   ├── Research agent: Find protocols
│   ├── Risk agent: Assess risks
│   ├── Portfolio agent: Create allocation
│   └── Chat agent: Summarize
├── Execute agents (parallel where possible)
├── Aggregate results
├── Generate final response
└── Save workflow to history
```

### 8.3 Agent Types by Subscription
| Tier | Agents Available | Count |
|------|------------------|-------|
| Free | chat, hunter_ai, research, portfolio, gas_optimizer | 5 |
| Pro | All core user-facing agents | 10 |
| Enterprise | All agents including enterprise/advanced | 18 |

---

## 9. Response Format

### 9.1 Message Response (UnifiedChatResponse)
```json
{
  "user_message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "user",
    "content": "swap 1 ETH to USDC",
    "created_at": "2026-01-06T12:00:00Z"
  },
  "agent_message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "I can help you swap 1 ETH to USDC...",
    "agent_type": "execution",
    "created_at": "2026-01-06T12:00:01Z"
  },
  "routing": {
    "intent": "SWAP",
    "confidence": 0.95,
    "handler": "swap_handler",
    "reasoning": "User explicitly requested token swap",
    "total_latency_ms": 850
  },
  "enrichment": {
    "from_token": "ETH",
    "to_token": "USDC",
    "estimated_output": "3024.50",
    "price_impact": "0.12%",
    "gas_estimate": "$6.05",
    "pending_action": {
      "action_type": "swap",
      "params": {...}
    }
  }
}
```

### 9.2 Execute Response (ExecuteActionResponse)
```json
{
  "action_id": "uuid",
  "action_type": "swap",
  "status": "awaiting_confirmation",
  "requires_confirmation": true,
  "confirmation_message": "Swap 1.0 ETH → USDC on BASE?",
  "simulation": {
    "success": true,
    "estimated_gas": 200000,
    "estimated_gas_usd": 0.50,
    "output_amount": "3024.50",
    "price_impact": 0.1,
    "warnings": [],
    "errors": []
  },
  "transaction": null,
  "summary": "Ready to swap 1.0 ETH to USDC",
  "enrichment": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0",
    "chain": "base",
    "aggregator": "1inch"
  },
  "created_at": "2026-01-06T12:00:00Z",
  "expires_at": "2026-01-06T12:05:00Z"
}
```

---

## 10. Multi-Language Support

### 10.1 Supported Languages
| Language | Code | Example Confirmation |
|----------|------|----------------------|
| English | `en` | "Swap 1.0 ETH → USDC on BASE?" |
| Spanish | `es` | "¿Intercambiar 1.0 ETH → USDC en BASE?" |
| French | `fr` | "Échanger 1.0 ETH → USDC sur BASE ?" |
| Chinese | `zh` | "在 BASE 上将 1.0 ETH 兑换为 USDC？" |
| Portuguese | `pt` | "Trocar 1.0 ETH → USDC em BASE?" |

### 10.2 Language Flow
```
Request (language: "es")
    │
    ▼
Intent Detection (language-aware)
    │
    ▼
Handler (localized responses)
    │
    ▼
Response (messages in Spanish)
```

---

## 11. Test Cases Matrix

### 11.1 Message Endpoint Tests
| Test ID | Auth | Input | Expected Handler | Expected Response |
|---------|------|-------|------------------|-------------------|
| M001 | JWT | "swap 1 ETH to USDC" | swap_handler | Swap preview |
| M002 | JWT | "deposit 100 USDC into Morpho" | lending_handler | Deposit preview |
| M003 | JWT | "show my portfolio" | portfolio_handler | Full portfolio |
| M004 | JWT | "what's my balance" | portfolio_handler | Token balances |
| M005 | JWT | "analyze Aave risk" | graphrag_risk | Risk analysis |
| M006 | JWT | "find arbitrage" | ultra_arbitrage | Opportunities |
| M007 | JWT | "create balanced portfolio" | supervisor | Multi-agent workflow |
| M008 | None | Any | 401 Unauthorized | Auth required |

### 11.2 Execute Endpoint Tests
| Test ID | Action | Confirmed | Expected Status | Expected Fields |
|---------|--------|-----------|-----------------|-----------------|
| E001 | swap | false | awaiting_confirmation | simulation, expires_at |
| E002 | swap | true | pending | transaction.hash |
| E003 | deposit | false | awaiting_confirmation | simulation |
| E004 | deposit | true | pending | transaction |
| E005 | bridge | false | awaiting_confirmation | simulation, warnings |
| E006 | transfer | false (no wallet) | failed | error: no wallet |
| E007 | invalid | any | failed | error: unsupported action |

### 11.3 Authentication Tests
| Test ID | Token | Expected | Error Code |
|---------|-------|----------|------------|
| A001 | Valid JWT | Success | - |
| A002 | Expired JWT | 401 | token_expired |
| A003 | Invalid JWT | 401 | invalid_token |
| A004 | Missing | 401 | missing_auth |
| A005 | Wrong user | 403 | access_denied |

### 11.4 Rate Limit Tests
| Test ID | User Type | Request # | Expected |
|---------|-----------|-----------|----------|
| R001 | Authenticated | 1-200 | Success |
| R002 | Authenticated | 201 | 429 Too Many Requests |
| R003 | Premium | Any | Success (unlimited) |

---

## 12. Error Handling

### 12.1 Error Response Format
```json
{
  "status": "error",
  "error_code": "INSUFFICIENT_BALANCE",
  "message": "Insufficient ETH balance. You have 0.5 ETH but need 1.0 ETH.",
  "details": {
    "required": "1.0",
    "available": "0.5",
    "token": "ETH"
  }
}
```

### 12.2 Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_ACTION | 400 | Unsupported action type |
| INSUFFICIENT_BALANCE | 400 | Not enough tokens |
| WALLET_NOT_CONNECTED | 400 | No Privy wallet |
| UNAUTHORIZED | 401 | Missing/invalid JWT |
| ACCESS_DENIED | 403 | Not conversation owner |
| NOT_FOUND | 404 | Conversation not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| EXECUTION_FAILED | 500 | Transaction failed |

---

## 13. Sequence Diagrams

### 13.1 Message Flow
```
┌────────┐     ┌──────────┐     ┌────────────┐     ┌───────────┐     ┌─────────┐
│ Client │     │Controller│     │CurrentUser │     │Orchestrator│     │ Handler │
└───┬────┘     └────┬─────┘     └──────┬─────┘     └─────┬─────┘     └────┬────┘
    │               │                  │                 │                │
    │  POST /messages (Bearer token)   │                 │                │
    │──────────────▶│                  │                 │                │
    │               │                  │                 │                │
    │               │ get_current_user │                 │                │
    │               │─────────────────▶│                 │                │
    │               │                  │                 │                │
    │               │◀────User─────────│                 │                │
    │               │                  │                 │                │
    │               │ execute(user_id, content)          │                │
    │               │───────────────────────────────────▶│                │
    │               │                  │                 │                │
    │               │                  │                 │ handle_intent()│
    │               │                  │                 │───────────────▶│
    │               │                  │                 │                │
    │               │                  │                 │◀───response────│
    │               │                  │                 │                │
    │               │◀─────────UnifiedChatResponse───────│                │
    │               │                  │                 │                │
    │◀──JSON────────│                  │                 │                │
```

### 13.2 Execute Flow
```
┌────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐     ┌─────────┐
│ Client │     │Controller│     │ExecuteCmd  │     │ Wallet   │     │ 1inch   │
└───┬────┘     └────┬─────┘     └──────┬─────┘     └────┬─────┘     └────┬────┘
    │               │                  │                │                │
    │  POST /execute (confirmed=false) │                │                │
    │──────────────▶│                  │                │                │
    │               │                  │                │                │
    │               │ execute()        │                │                │
    │               │─────────────────▶│                │                │
    │               │                  │                │                │
    │               │                  │ get_wallet()   │                │
    │               │                  │───────────────▶│                │
    │               │                  │                │                │
    │               │                  │◀──address──────│                │
    │               │                  │                │                │
    │               │                  │ get_quote()                     │
    │               │                  │───────────────────────────────▶│
    │               │                  │                                │
    │               │                  │◀──────────quote────────────────│
    │               │                  │                                │
    │               │◀──ActionResult (simulation)                       │
    │               │                  │                                │
    │◀──JSON (awaiting_confirmation)   │                                │
    │               │                  │                                │
    │  POST /execute (confirmed=true)  │                                │
    │──────────────▶│                  │                                │
    │               │                  │                                │
    │               │ execute()        │                                │
    │               │─────────────────▶│                                │
    │               │                  │                                │
    │               │                  │── build_tx → sign → submit ────│
    │               │                  │                                │
    │               │◀──ActionResult (tx_hash)                          │
    │               │                  │                                │
    │◀──JSON (pending, hash)           │                                │
```

---

## 14. Configuration Reference

### 14.1 Rate Limits
```python
# Authenticated user limits
RATE_LIMIT_AUTHENTICATED_HOURLY = 200
RATE_LIMIT_AUTHENTICATED_DAILY = 1000

# Premium user (unlimited)
RATE_LIMIT_PREMIUM_HOURLY = None
RATE_LIMIT_PREMIUM_DAILY = None
```

### 14.2 Execute Limits
```python
MAX_SWAP_VALUE_USD = Decimal("50000")
MAX_DEPOSIT_VALUE_USD = Decimal("100000")
MAX_TRANSFER_VALUE_USD = Decimal("10000")
CONFIRMATION_EXPIRY_MINUTES = 5
```

### 14.3 Context Settings
```python
CONVERSATION_HISTORY_LIMIT = 10  # Last N messages for context
CONTEXT_WINDOW_TOKENS = 8000     # Max tokens for context
```

---

## 15. Quick Test Commands

### 15.1 Message Endpoint
```bash
# Token required - replace with valid JWT
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Send message (swap intent)
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "swap 1 ETH to USDC", "language": "en"}'

# Send message (portfolio - requires wallet)
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "show my portfolio"}'

# Send message (complex workflow)
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "create a balanced 50k DeFi portfolio"}'
```

### 15.2 Execute Endpoint
```bash
# Step 1: Simulate swap
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "swap",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0",
    "chain": "base",
    "confirmed": false
  }'

# Step 2: Confirm and execute
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "swap",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0",
    "chain": "base",
    "confirmed": true
  }'

# Deposit to Morpho
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "deposit",
    "protocol": "morpho",
    "from_token": "USDC",
    "amount": "1000",
    "chain": "base",
    "confirmed": false
  }'

# Bridge to Arbitrum
curl -X POST http://localhost:8000/api/v1/user/chat/conversations/{id}/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "bridge",
    "from_token": "USDC",
    "amount": "500",
    "chain": "ethereum",
    "to_chain": "arbitrum",
    "confirmed": false
  }'
```

---

## 16. Related Documentation

- `docs/steering/guest-chat-complete-flow-spec.md` - Guest chat flow
- `docs/steering/guest-chat-intent-testing.md` - Intent testing examples
- `docs/api/examples/chat-execute.md` - Execute endpoint examples
- `docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md` - Agent configuration
- `docs/UNIFIED_CHAT_ROUTING_PROPOSAL.md` - Routing architecture

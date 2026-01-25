# Chat System Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Chat System services are organized in a hexagonal architecture pattern:
- **Application Layer**: Business logic, handlers, orchestration
- **Domain Layer**: Entities, value objects, ports
- **Infrastructure Layer**: Database adapters, external clients, Celery tasks

**Total Service Count**: 83+ Python modules

---

## 1. Core Chat Services

### 1.1 Conversation Service
**Path**: `src/app/application/chat/services/conversation_service.py`

Manages conversation lifecycle operations.

**Responsibilities**:
- Create/update/delete conversations
- Conversation state management
- Title generation
- Status transitions (active → archived → deleted)

**Dependencies**:
- `ChatConversationRepository`
- `UserService`

---

### 1.2 User Service
**Path**: `src/app/application/chat/services/user_service.py`

Manages chat user entities (unified for guest/authenticated).

**Responsibilities**:
- Get or create chat users
- Link Privy authenticated users
- User preferences management
- User blocking/unblocking

**Dependencies**:
- `ChatUserRepository`
- `CurrentUserService`

---

### 1.3 Rate Limit Service
**Path**: `src/app/application/chat/services/rate_limit_service.py`

Enforces rate limiting for chat operations.

**Configuration** (`rate_limit_config.py`):
```python
# Guest limits
GUEST_HOURLY_LIMIT = 5000
GUEST_DAILY_LIMIT = 10000

# Authenticated limits (per tier)
FREE_HOURLY_LIMIT = 100
PREMIUM_HOURLY_LIMIT = 1000
```

**Responsibilities**:
- Track message counts per window (hourly/daily)
- Check and enforce limits
- Return remaining quota

**Dependencies**:
- `ChatRateLimitRepository`

---

### 1.4 Conversation Memory
**Path**: `src/app/application/chat/services/conversation_memory.py`

Manages conversation context for multi-turn interactions.

**Responsibilities**:
- Build context string from message history
- Detect pending actions (swap confirmations, etc.)
- Track conversation state for workflows
- Handle multi-step flow continuation

**Dependencies**:
- `ChatMessageRepository`

---

## 2. Intent Detection Services

### 2.1 Intent Detector V2
**Path**: `src/app/application/chat/services/intent_detector_v2.py`

LLM-based intent classification with multi-intent support.

**Supported Intents**:
```python
class ChatIntentV2(Enum):
    SWAP = "SWAP"
    MOONPAY_SWAP = "MOONPAY_SWAP"
    BUY_CRYPTO = "BUY_CRYPTO"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER = "TRANSFER"
    PORTFOLIO = "PORTFOLIO"
    PRICE_CHECK = "PRICE_CHECK"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    LENDING = "LENDING"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
    # ... 20+ more intents
```

**Restricted Intents** (require authentication):
- `PORTFOLIO`, `BALANCE`, `ACTIVITY`
- `SWAP`, `DEPOSIT`, `WITHDRAW`, `TRANSFER`
- `RECEIVE_ADDRESS`

**Dependencies**:
- `LLMGateway`
- `IntentCacheAdapter` (Redis)

---

### 2.2 Advanced Intent Detector
**Path**: `src/app/application/chat/services/advanced_intent_detector.py`

Enhanced detection with entity extraction.

**Features**:
- Token symbol extraction
- Amount parsing
- Chain detection
- Protocol identification

---

### 2.3 Intent Orchestrator
**Path**: `src/app/application/chat/services/intent_orchestrator.py`

Coordinates multi-intent handling.

**Dependencies**:
- `IntentDetectorV2`
- `MultiIntentIntegrationService`

---

### 2.4 Flow Cancellation Detector
**Path**: `src/app/application/chat/services/flow_cancellation_detector.py`

Detects when user wants to cancel current workflow.

**Cancellation Phrases**:
- "cancel", "stop", "never mind"
- "no", "forget it", "abort"
- Multi-language support

---

## 3. Handler Services

### 3.1 SwapHandler V2
**Path**: `src/app/application/chat/handlers/swap_handler_v2.py`

Hyperliquid Spot swap handler for meme tokens.

**Supported Tokens** (HYPERLIQUID_SPOT_TOKENS):
- USDC (quote currency)
- PURR, HFUN, TRUMP, PEPE, MOG, POINTS, JEFF
- 50+ meme tokens

**Responsibilities**:
- Multi-turn swap flow
- Hyperliquid quote fetching
- Error messaging for unsupported tokens
- Execute data generation

**Dependencies**:
- `HyperliquidClient`

---

### 3.2 MoonPay Swap Handler
**Path**: `src/app/application/chat/handlers/moonpay_swap_handler.py`

Handles crypto purchases via MoonPay.

**Responsibilities**:
- Fiat-to-crypto purchase flow
- Quote generation
- Payment URL generation

---

### 3.3 Money Market Handler
**Path**: `src/app/application/chat/handlers/money_market_handler.py`

Handles lending/borrowing operations.

**Supported Protocols**:
- Morpho
- Aave
- Compound

**Responsibilities**:
- APY comparison
- Deposit/withdraw flows
- Risk assessment

---

### 3.4 Portfolio Handler
**Path**: `src/app/application/chat/handlers/portfolio_handler.py`

Portfolio analysis and display.

**Features**:
- Token balances
- Position tracking
- Performance metrics

---

### 3.5 Restricted Handler
**Path**: `src/app/application/chat/handlers/restricted_handler.py`

Handles restricted actions for guests.

**Responsibilities**:
- Generate registration prompts
- Multi-language CTA messages
- Feature gating

---

### 3.6 Activity Handler
**Path**: `src/app/application/chat/handlers/activity_handler.py`

Transaction history and activity tracking.

---

### 3.7 Lending Handler
**Path**: `src/app/application/chat/handlers/lending_handler.py`

Deprecated - use Money Market Handler.

---

## 4. Guest Services

### 4.1 Send Guest Message Command
**Path**: `src/app/application/guest/commands/send_guest_message.py`

Main command for processing guest messages.

**Flow**:
1. Get/create guest user by IP
2. Get/create conversation
3. Check rate limits
4. Detect intent
5. Route to handler
6. Save messages
7. Return response

**Dependencies**:
- `GuestRepository`
- `GuestHandlerService`
- `IntentDetectorV2`

---

### 4.2 Guest Handler Service
**Path**: `src/app/application/guest/handlers/guest_handler_service.py`

Routes guest requests to appropriate handlers.

**Handler Mapping**:
```python
INTENT_HANDLERS = {
    ChatIntent.SWAP: handle_swap_demo,
    ChatIntent.LENDING: handle_lending_demo,
    ChatIntent.PORTFOLIO: handle_restricted,
    ChatIntent.PRICE_CHECK: handle_price_check,
    # ...
}
```

---

### 4.3 Guest Multi-step Handlers

| Handler | Path | Purpose |
|---------|------|---------|
| `portfolio_multistep.py` | `application/guest/handlers/` | Demo portfolio flow |
| `lending_multistep.py` | `application/guest/handlers/` | Demo lending flow |
| `buy_multistep.py` | `application/guest/handlers/` | Demo buy flow |
| `send_multistep.py` | `application/guest/handlers/` | Demo transfer flow |
| `activity_multistep.py` | `application/guest/handlers/` | Demo activity flow |
| `moonpay_swap_multistep.py` | `application/guest/handlers/` | MoonPay demo flow |

---

## 5. Analytics Services

### 5.1 Admin Analytics Service
**Path**: `src/app/application/chat/services/admin_analytics_service.py`

Powers the admin dashboard endpoints.

**Methods**:
- `get_dashboard_summary()`
- `get_agent_performance()`
- `get_cache_efficiency()`
- `get_cost_tracking()`
- `get_error_monitoring()`
- `get_active_users()`
- `get_conversation_metrics()`
- `export_dashboard_data()`

---

### 5.2 Chat Analytics Service
**Path**: `src/app/application/chat/services/chat_analytics_service.py`

User-facing analytics.

**Features**:
- Conversation statistics
- Message counts
- Intent distribution

---

### 5.3 User Analytics Service
**Path**: `src/app/application/chat/services/user_analytics_service.py`

Per-user analytics tracking.

---

## 6. Context & Optimization Services

### 6.1 User Context Service
**Path**: `src/app/application/chat/services/user_context_service.py`

Provides context-aware agent selection.

**Context Data**:
- Recent intents
- Mentioned tokens/protocols
- Active positions
- User preferences
- Trading patterns

**Dependencies**:
- `ConversationContextRepository`
- Wallet data providers

---

### 6.2 Context Manager
**Path**: `src/app/application/chat/services/context_manager.py`

Manages conversation context windows.

---

### 6.3 Conversation State Manager
**Path**: `src/app/application/chat/services/conversation_state_manager.py`

Tracks workflow states across messages.

---

### 6.4 Performance Optimization Service
**Path**: `src/app/application/chat/services/performance_optimization_service.py`

Optimizes chat performance.

**Features**:
- Response caching
- Batch processing
- Connection pooling

---

## 7. Knowledge Services

### 7.1 Knowledge Injector
**Path**: `src/app/application/chat/services/knowledge_injector.py`

Injects domain knowledge into LLM context.

**Knowledge Sources**:
- `anvil_knowledge/features/`
- DeFi protocol data
- Token information

---

### 7.2 Knowledge Compressor
**Path**: `src/app/application/chat/services/knowledge_compressor.py`

Compresses knowledge for context window optimization.

---

## 8. Tool Executors

### 8.1 Hunter Tool Executor
**Path**: `src/app/application/chat/services/hunter_tool_executor.py`

Executes Hunter AI tools.

**Tools**:
- Price lookup
- Market analysis
- News aggregation

---

### 8.2 ULTRA Tool Executor
**Path**: `src/app/application/chat/services/ultra_tool_executor.py`

Executes ULTRA research tools.

**Tools**:
- Deep research
- Protocol analysis
- Yield optimization

---

## 9. Translation & i18n Services

### 9.1 Translation Service
**Path**: `src/app/application/chat/services/translation_service.py`

Handles response translation.

**Supported Languages**:
- English (en)
- Spanish (es)
- Portuguese (pt)
- Chinese (zh)

---

### 9.2 i18n Translations
**Path**: `src/app/application/chat/i18n/translations.py`

Static translation strings.

---

## 10. Commands

| Command | Path | Purpose |
|---------|------|---------|
| `create_conversation.py` | `application/chat/commands/` | Create new conversation |
| `send_message.py` | `application/chat/commands/` | Basic message sending |
| `send_message_unified.py` | `application/chat/commands/` | Unified message flow |
| `send_message_with_supervisor.py` | `application/chat/commands/` | Agent Squad supervisor |
| `send_message_with_distillation.py` | `application/chat/commands/` | Distillation-enabled |
| `execute_action.py` | `application/chat/commands/` | Execute pending actions |
| `get_or_create_chat_user.py` | `application/chat/commands/` | User management |
| `get_or_create_chat_conversation.py` | `application/chat/commands/` | Conversation management |
| `update_conversation_title.py` | `application/chat/commands/` | Title updates |
| `delete_conversation.py` | `application/chat/commands/` | Conversation deletion |
| `create_chat_message.py` | `application/chat/commands/` | Message creation |

---

## 11. Queries

| Query | Path | Purpose |
|-------|------|---------|
| `list_conversations.py` | `application/chat/queries/` | List user conversations |
| `get_conversation.py` | `application/chat/queries/` | Get single conversation |
| `get_messages.py` | `application/chat/queries/` | Get conversation messages |

---

## Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│  (conversations_router.py, guest/router.py, chat_dashboard.py)  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ SendGuestMessage│  │SendMessageWith  │  │  AdminAnalytics│  │
│  │    Command      │  │   Supervisor    │  │    Service     │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────┘  │
│           │                    │                     │          │
│           ▼                    ▼                     ▼          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Core Services                              │   │
│  │  ConversationService, UserService, RateLimitService      │   │
│  │  ConversationMemory, IntentDetectorV2, UserContextService│   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                    │                     │          │
│           ▼                    ▼                     ▼          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Handlers                                   │   │
│  │  SwapHandlerV2, MoneyMarketHandler, PortfolioHandler    │   │
│  │  MoonPaySwapHandler, RestrictedHandler, ActivityHandler │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                         │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Repositories   │  │ External Clients│  │  Celery Tasks  │  │
│  │  (SQLAlchemy)   │  │ (Hyperliquid,   │  │                │  │
│  │                 │  │  CoinGecko,etc) │  │                │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- **Chat Application**: `src/app/application/chat/`
- **Guest Application**: `src/app/application/guest/`
- **Infrastructure**: `src/app/infrastructure/`
- **Celery Tasks**: `src/app/infrastructure/celery/tasks.py`

# Chat System Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil Chat System is a comprehensive AI-powered conversational interface for DeFi operations. It supports guest and authenticated users with multi-agent orchestration, real-time market data, and transaction execution capabilities.

---

## 1. Module Status

| Module | Status | Health | Notes |
|--------|--------|--------|-------|
| Guest Chat | ✅ Production | Healthy | IP-based tracking, rate limiting |
| User Chat | ✅ Production | Healthy | Full Agent Squad integration |
| Admin Dashboard | ✅ Production | Healthy | Analytics, monitoring |
| WebSocket | ✅ Production | Healthy | Real-time messaging |
| Intent Detection | ✅ Production | Healthy | V2 with multi-intent support |
| Swap Handler V2 | ✅ Production | Healthy | Hyperliquid Spot integration |
| Agent Squad | ✅ Production | Healthy | 18 specialized agents |
| Celery Tasks | ✅ Production | Healthy | Background processing |

---

## 2. File Reference Index

### 2.1 Presentation Layer

```
src/app/presentation/http/controllers/
├── chat/
│   ├── conversations_router.py      # Main user chat endpoints
│   ├── universal_chat_router.py     # Unified chat interface
│   ├── analytics_dashboard.py       # User analytics
│   ├── intent_detection_router.py   # Intent API
│   └── websocket_router.py          # WebSocket handling
├── guest/
│   ├── router.py                    # Guest chat endpoints
│   └── __init__.py
└── admin/
    └── chat_dashboard.py            # Admin analytics endpoints
```

### 2.2 Application Layer

```
src/app/application/
├── chat/
│   ├── commands/
│   │   ├── create_conversation.py
│   │   ├── send_message.py
│   │   ├── send_message_unified.py
│   │   ├── send_message_with_supervisor.py
│   │   ├── send_message_with_distillation.py
│   │   ├── execute_action.py
│   │   ├── get_or_create_chat_user.py
│   │   ├── get_or_create_chat_conversation.py
│   │   ├── create_chat_message.py
│   │   ├── update_conversation_title.py
│   │   └── delete_conversation.py
│   ├── queries/
│   │   ├── list_conversations.py
│   │   ├── get_conversation.py
│   │   └── get_messages.py
│   ├── handlers/
│   │   ├── swap_handler_v2.py        # Hyperliquid integration
│   │   ├── swap_handler.py           # Legacy
│   │   ├── moonpay_swap_handler.py
│   │   ├── moonpay_swap_flow_handler.py
│   │   ├── money_market_handler.py
│   │   ├── portfolio_handler.py
│   │   ├── activity_handler.py
│   │   ├── lending_handler.py
│   │   ├── receive_handler.py
│   │   ├── buy_handler.py
│   │   ├── restricted_handler.py
│   │   └── unified_chat_handler.py
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── user_service.py
│   │   ├── rate_limit_service.py
│   │   ├── rate_limit_config.py
│   │   ├── conversation_memory.py
│   │   ├── intent_detector_v2.py
│   │   ├── intent_detector.py
│   │   ├── advanced_intent_detector.py
│   │   ├── intent_orchestrator.py
│   │   ├── multi_intent_integration_service.py
│   │   ├── multi_intent_response_formatter.py
│   │   ├── flow_cancellation_detector.py
│   │   ├── user_context_service.py
│   │   ├── admin_analytics_service.py
│   │   ├── chat_analytics_service.py
│   │   ├── user_analytics_service.py
│   │   ├── context_manager.py
│   │   ├── conversation_state_manager.py
│   │   ├── performance_optimization_service.py
│   │   ├── knowledge_injector.py
│   │   ├── knowledge_compressor.py
│   │   ├── hunter_tool_executor.py
│   │   ├── ultra_tool_executor.py
│   │   ├── template_executor_service.py
│   │   ├── response_template_service.py
│   │   ├── conversation_export_service.py
│   │   ├── translation_service.py
│   │   ├── user_preferences_service.py
│   │   ├── user_data_service.py
│   │   └── agent_orchestration_service.py
│   └── i18n/
│       └── translations.py
└── guest/
    ├── commands/
    │   ├── send_guest_message.py
    │   └── send_guest_message_v2.py
    ├── handlers/
    │   ├── guest_handler_service.py
    │   ├── portfolio_multistep.py
    │   ├── lending_multistep.py
    │   ├── buy_multistep.py
    │   ├── send_multistep.py
    │   ├── activity_multistep.py
    │   └── moonpay_swap_multistep.py
    └── i18n/
        └── translations.py
```

### 2.3 Infrastructure Layer

```
src/app/infrastructure/
├── persistence_sqla/mappings/
│   ├── chat_unified.py              # chat_users, chat_conversations, chat_messages
│   ├── chat.py                      # Legacy tables
│   ├── guest.py                     # guest_users, guest_conversations, guest_messages
│   ├── conversation_context.py      # conversation_contexts
│   └── conversation_analytics.py
├── adapters/
│   ├── chat_unified_repository_sqla.py
│   ├── external/
│   │   ├── hyperliquid_client.py    # Hyperliquid API
│   │   ├── oneinch_client.py        # 1inch API
│   │   ├── lifi_client.py           # LiFi API
│   │   ├── coingecko_client.py      # CoinGecko API
│   │   └── ...
│   └── agent_squad/
│       └── agents/workflows/
│           ├── swap_workflow_agent.py
│           ├── lending_workflow_agent.py
│           └── ...
└── celery/
    ├── app.py                       # Celery app configuration
    ├── tasks.py                     # Main tasks file
    └── tasks/
        ├── user_context_tasks.py
        ├── distillation_tasks.py
        └── llm_ranking.py
```

### 2.4 Domain Layer

```
src/app/domain/
├── chat/
│   ├── entities/
│   │   ├── chat_user.py
│   │   ├── chat_conversation.py
│   │   └── chat_message.py
│   ├── value_objects/
│   │   ├── message_role.py
│   │   └── message_content.py
│   └── ports/
│       ├── chat_user_repository.py
│       ├── chat_conversation_repository.py
│       └── chat_message_repository.py
└── guest/
    ├── entities/
    │   ├── guest_user.py
    │   └── guest_conversation.py
    └── ports/
        └── guest_repository.py
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web App   │  │ Mobile App  │  │   Admin     │  │  WebSocket  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │   Guest Router     │  │ Conversations Router│  │ Admin Chat Dashboard│   │
│  │   /api/v1/guest    │  │ /api/v1/conversations│ │ /api/v1/admin/chat │   │
│  └─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘    │
│            │                       │                       │                │
└────────────┼───────────────────────┼───────────────────────┼────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         COMMANDS                                      │   │
│  │  SendGuestMessage │ SendMessageWithSupervisor │ ExecuteAction        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐   │
│  │                         SERVICES                                      │   │
│  │  ┌─────────────────┐  ┌────────┴────────┐  ┌─────────────────┐      │   │
│  │  │ConversationSvc  │  │IntentDetectorV2 │  │ RateLimitService│      │   │
│  │  │UserService      │  │IntentOrchestrator│ │ ConversationMem │      │   │
│  │  │UserContextSvc   │  │FlowCancelDetect │  │ AdminAnalytics  │      │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐   │
│  │                         HANDLERS                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │SwapHandlerV2 │  │MoneyMarketHdl│  │PortfolioHdl │               │   │
│  │  │(Hyperliquid) │  │(Morpho/Aave) │  │              │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │MoonPaySwapHdl│  │RestrictedHdl │  │ ActivityHdl │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOMAIN LAYER                                       │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │     ENTITIES     │  │  VALUE OBJECTS   │  │      PORTS       │          │
│  │  - ChatUser      │  │  - MessageRole   │  │  - ChatUserRepo  │          │
│  │  - ChatConv      │  │  - MessageContent│  │  - ChatConvRepo  │          │
│  │  - ChatMessage   │  │  - IntentResult  │  │  - ChatMsgRepo   │          │
│  │  - GuestUser     │  │                  │  │  - GuestRepo     │          │
│  │  - GuestConv     │  │                  │  │  - LLMGateway    │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                                 │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   REPOSITORIES   │  │ EXTERNAL CLIENTS │  │   CELERY TASKS   │          │
│  │  - SQLAlchemy    │  │  - Hyperliquid   │  │  - ArchiveGuest  │          │
│  │  - PostgreSQL    │  │  - 1inch         │  │  - UpdateStats   │          │
│  │  - Redis (cache) │  │  - LiFi          │  │  - UserContext   │          │
│  │                  │  │  - CoinGecko     │  │  - LLMRanking    │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        AGENT SQUAD (18 Agents)                      │    │
│  │  Core: ChatAgent, HunterAI, Research, Execution, RiskAnalyzer       │    │
│  │  Workflows: SwapWorkflow, LendingWorkflow, TransferWorkflow         │    │
│  │  Enterprise: Compliance, MultiSig, AlertMonitoring, CrisisManager   │    │
│  │  Advanced: Bridge, Lending, NFT, DAO                                │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER (PostgreSQL)                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     UNIFIED CHAT TABLES                               │  │
│  │  chat_users ──────┐                                                   │  │
│  │       │           │                                                   │  │
│  │       ▼           │                                                   │  │
│  │  chat_conversations ──────┐                                           │  │
│  │       │                   │                                           │  │
│  │       ▼                   ▼                                           │  │
│  │  chat_messages    chat_rate_limits                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      GUEST TABLES                                     │  │
│  │  guest_users ──────┐                                                  │  │
│  │       │            │                                                  │  │
│  │       ▼            ▼                                                  │  │
│  │  guest_conversations    guest_telemetry                               │  │
│  │       │                                                               │  │
│  │       ▼                                                               │  │
│  │  guest_messages                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    CONTEXT TABLES                                     │  │
│  │  conversation_contexts                                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 Unified Chat Tables

```sql
-- chat_users
CREATE TABLE chat_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type VARCHAR(20) NOT NULL,  -- guest | authenticated | premium
    identifier VARCHAR(255) NOT NULL, -- IP for guest, privy_id for auth
    privy_id VARCHAR(255),
    email VARCHAR(255),
    preferred_language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

-- chat_conversations
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES chat_users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',  -- active | archived | deleted
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    metadata JSONB DEFAULT '{}'
);

-- chat_messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user | assistant | system
    content TEXT NOT NULL,
    intent VARCHAR(50),
    intent_confidence FLOAT,
    handler VARCHAR(100),
    is_restricted_action BOOLEAN DEFAULT FALSE,
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- chat_rate_limits
CREATE TABLE chat_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES chat_users(id) ON DELETE CASCADE,
    window_type VARCHAR(20) NOT NULL,  -- hourly | daily
    window_start TIMESTAMPTZ NOT NULL,
    message_count INTEGER DEFAULT 0,
    UNIQUE(user_id, window_type, window_start)
);
```

### 4.2 Guest Tables

```sql
-- guest_users
CREATE TABLE guest_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    fingerprint VARCHAR(255),
    first_seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    country_code VARCHAR(2),
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- guest_conversations
CREATE TABLE guest_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_user_id UUID REFERENCES guest_users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMPTZ
);

-- guest_messages
CREATE TABLE guest_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES guest_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(50),
    handler VARCHAR(50),
    confidence FLOAT,
    language VARCHAR(5) DEFAULT 'en',
    is_restricted_action BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- guest_telemetry
CREATE TABLE guest_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_user_id UUID REFERENCES guest_users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES guest_conversations(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    referer TEXT,
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 Context Tables

```sql
-- conversation_contexts
CREATE TABLE conversation_contexts (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    current_topic VARCHAR,
    recent_intents JSONB DEFAULT '[]',
    mentioned_tokens JSONB DEFAULT '[]',
    mentioned_protocols JSONB DEFAULT '[]',
    active_positions JSONB DEFAULT '[]',
    preferred_slippage FLOAT,
    preferred_leverage INTEGER,
    risk_tolerance VARCHAR,
    preferred_chains JSONB DEFAULT '[]',
    frequent_operations JSONB DEFAULT '{}',
    typical_trade_sizes JSONB DEFAULT '{}',
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

---

## 5. Improvements Roadmap

### 5.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **1inch Integration** | Enable 1inch for major token swaps | Medium | High |
| **Hyperliquid Perps** | Add perpetual futures trading | High | High |
| **Streaming Responses** | Implement SSE for real-time AI responses | Medium | High |
| **Test Coverage** | Add missing unit/integration tests | Medium | High |

### 5.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Voice Input** | Add speech-to-text for messages | High | Medium |
| **Message Reactions** | Allow users to rate responses | Low | Medium |
| **Conversation Export** | Export chat history to PDF/JSON | Low | Medium |
| **Intent Learning** | ML-based intent improvement | High | Medium |

### 5.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Dark Mode API** | Theme preferences per conversation | Low | Low |
| **Message Templates** | Predefined message shortcuts | Low | Low |
| **Analytics Webhooks** | Real-time analytics events | Medium | Low |

---

## 6. Performance Metrics

### 6.1 Current Performance

| Metric | Value | Target |
|--------|-------|--------|
| Guest message latency | ~2s | <2s |
| Auth message latency | ~3s | <3s |
| Intent detection | ~200ms | <500ms |
| Cache hit rate | ~85% | >80% |
| Error rate | <0.1% | <1% |

### 6.2 Scaling Considerations

- **Horizontal Scaling**: Stateless services, can scale pods
- **Database**: Read replicas for queries
- **Cache**: Redis cluster for high availability
- **Celery**: Multiple workers for background tasks

---

## 7. Security Considerations

### 7.1 Implemented

- ✅ JWT authentication for user endpoints
- ✅ Rate limiting (IP-based for guests, user-based for auth)
- ✅ Input validation (Pydantic schemas)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS prevention (response sanitization)
- ✅ CORS configuration

### 7.2 Recommendations

- ⚠️ Add prompt injection detection
- ⚠️ Implement PII redaction in logs
- ⚠️ Add content moderation for user messages
- ⚠️ Implement API key rotation

---

## References

- **Endpoints Spec**: `docs/ceo/chat/endpoints.md`
- **Services Spec**: `docs/ceo/chat/services.md`
- **Celery Spec**: `docs/ceo/chat/celery.md`
- **Test Spec**: `docs/ceo/chat/test.md`
- **Database Schema**: `docs/ceo/database-architecture-spec.md`

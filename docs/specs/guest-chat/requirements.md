# Guest Chat System - Requirements Specification

> **CTO Methodology Framework Analysis**
> 
> Date: December 29, 2025
> Version: 1.0

---

## Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Business Requirements

**Primary Goal:** Provide a limited demo chat experience for unauthenticated users to showcase the platform's capabilities and encourage registration.

**Core Features:**
1. Track guest users by IP address
2. Auto-create conversation when new/archived IP visits
3. Provide limited chat functionality (read-only DeFi info, no execution)
4. Prompt registration when user attempts restricted actions
5. Archive guest conversations hourly via Celery
6. Multi-language support (EN, ES, PT, ZH)
7. Track telemetry for analytics

### 1.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Track guest users by IP address | HIGH |
| FR-02 | Auto-create conversation for new/archived IP | HIGH |
| FR-03 | Show conversation history for active IP | HIGH |
| FR-04 | Return registration prompt for restricted actions | HIGH |
| FR-05 | Multi-language responses (en, es, pt, zh) | HIGH |
| FR-06 | Hourly archive of guest conversations | MEDIUM |
| FR-07 | Telemetry tracking for guest interactions | MEDIUM |
| FR-08 | Rate limiting per IP | MEDIUM |

### 1.3 Restricted Actions (Require Registration)

When a guest user attempts these actions, return a structured response indicating registration is required:

| Action | Intent | Registration Required |
|--------|--------|----------------------|
| Execute swap | SWAP (confirmed) | ✅ YES |
| Execute deposit | DEPOSIT (confirmed) | ✅ YES |
| Execute withdraw | WITHDRAW (confirmed) | ✅ YES |
| Execute transfer | TRANSFER (confirmed) | ✅ YES |
| View portfolio | PORTFOLIO | ✅ YES |
| View balance | BALANCE | ✅ YES |
| View activity | ACTIVITY | ✅ YES |
| Get receive address | RECEIVE | ✅ YES |

### 1.4 Allowed Actions (Demo Mode)

| Action | Intent | Allowed |
|--------|--------|---------|
| Protocol search | PROTOCOL_SEARCH | ✅ YES |
| Risk assessment | RISK_ASSESSMENT | ✅ YES |
| Similar protocols | SIMILAR_PROTOCOLS | ✅ YES |
| Lending rates (view) | LENDING | ✅ YES |
| Money market rates | MONEY_MARKET | ✅ YES |
| Swap quotes (view only) | SWAP (not confirmed) | ✅ YES |
| General questions | GENERAL_CONVERSATION | ✅ YES |

---

## Phase 2: Technical Design

### 2.1 Database Schema

#### Table: `guest_users`

```sql
CREATE TABLE guest_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    fingerprint VARCHAR(255) NULL,  -- Optional browser fingerprint
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    country_code VARCHAR(2) NULL,  -- From IP geolocation
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_guest_users_ip_address ON guest_users(ip_address);
CREATE INDEX ix_guest_users_last_seen_at ON guest_users(last_seen_at);
```

#### Table: `guest_conversations`

```sql
CREATE TABLE guest_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_user_id UUID NOT NULL REFERENCES guest_users(id) ON DELETE CASCADE,
    title VARCHAR(255) NULL,
    status VARCHAR(20) DEFAULT 'active',  -- active, archived
    message_count INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE NULL
);

CREATE INDEX ix_guest_conversations_guest_user_id ON guest_conversations(guest_user_id);
CREATE INDEX ix_guest_conversations_status ON guest_conversations(status);
CREATE INDEX ix_guest_conversations_created_at ON guest_conversations(created_at);
```

#### Table: `guest_messages`

```sql
CREATE TABLE guest_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES guest_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    intent VARCHAR(50) NULL,  -- detected intent
    handler VARCHAR(50) NULL,  -- handler used
    confidence FLOAT NULL,
    language VARCHAR(5) DEFAULT 'en',
    is_restricted_action BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_guest_messages_conversation_id ON guest_messages(conversation_id);
CREATE INDEX ix_guest_messages_created_at ON guest_messages(created_at);
```

#### Table: `guest_telemetry`

```sql
CREATE TABLE guest_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_user_id UUID NOT NULL REFERENCES guest_users(id) ON DELETE CASCADE,
    conversation_id UUID NULL REFERENCES guest_conversations(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,  -- message_sent, registration_prompt, rate_limited, etc.
    event_data JSONB NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NULL,
    referer TEXT NULL,
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_guest_telemetry_guest_user_id ON guest_telemetry(guest_user_id);
CREATE INDEX ix_guest_telemetry_event_type ON guest_telemetry(event_type);
CREATE INDEX ix_guest_telemetry_created_at ON guest_telemetry(created_at);
```

### 2.2 API Endpoints

#### Public Guest Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/public/guest/chat` | Send message (auto-creates conversation) |
| GET | `/api/v1/public/guest/chat/history` | Get conversation history for IP |
| GET | `/api/v1/public/guest/chat/status` | Check guest status for IP |

### 2.3 Request/Response Schemas

#### POST `/api/v1/public/guest/chat`

**Request:**
```json
{
  "content": "What are the best USDC yields?",
  "language": "en"
}
```

**Response (Success):**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "What are the best USDC yields?",
    "created_at": "2025-12-29T12:00:00Z"
  },
  "agent_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Here are the top USDC yields...",
    "created_at": "2025-12-29T12:00:01Z"
  },
  "routing": {
    "intent": "LENDING",
    "confidence": 0.92,
    "handler": "lending_handler",
    "language": "en",
    "is_demo_mode": true
  },
  "enrichment": {
    "protocols": [...],
    "disclaimer": "This is demo mode. Register for full access."
  },
  "guest_info": {
    "messages_remaining": 18,
    "session_expires_in": 3540
  }
}
```

**Response (Registration Required):**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "Show my portfolio",
    "created_at": "2025-12-29T12:00:00Z"
  },
  "agent_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Portfolio access requires registration...",
    "created_at": "2025-12-29T12:00:01Z"
  },
  "routing": {
    "intent": "PORTFOLIO",
    "confidence": 0.95,
    "handler": "portfolio_handler",
    "language": "en",
    "is_demo_mode": true
  },
  "registration_required": {
    "required": true,
    "reason": "portfolio_access",
    "message": {
      "en": "Create a free account to view your portfolio and track your DeFi positions.",
      "es": "Crea una cuenta gratuita para ver tu portafolio y rastrear tus posiciones DeFi.",
      "pt": "Crie uma conta gratuita para ver seu portfólio e rastrear suas posições DeFi.",
      "zh": "创建免费账户以查看您的投资组合并跟踪您的 DeFi 头寸。"
    },
    "cta": {
      "en": "Sign Up Free",
      "es": "Regístrate Gratis",
      "pt": "Cadastre-se Grátis",
      "zh": "免费注册"
    },
    "signup_url": "/signup"
  }
}
```

### 2.4 Guest Chat Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Guest User Request                                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Extract IP from request                                     │
│  2. Check if guest_user exists for IP                          │
│     ├─ NO → Create new guest_user                              │
│     └─ YES → Update last_seen_at                               │
│  3. Check if active conversation exists                         │
│     ├─ NO (or archived) → Create new conversation              │
│     └─ YES → Use existing conversation                         │
│  4. Detect intent from message                                  │
│  5. Check if intent requires registration                       │
│     ├─ YES → Return registration_required response             │
│     └─ NO → Process with demo handler                          │
│  6. Save messages to guest_messages                             │
│  7. Log telemetry event                                         │
│  8. Return response                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 Celery Task: Archive Guest Conversations

**Schedule:** Every hour

**Logic:**
1. Find all `guest_conversations` with `status = 'active'`
2. Where `updated_at < NOW() - INTERVAL '1 hour'`
3. Set `status = 'archived'` and `archived_at = NOW()`
4. Log telemetry event

```python
@celery_app.task(name="archive_guest_conversations")
def archive_guest_conversations():
    """Archive inactive guest conversations hourly."""
    ...

celery_app.conf.beat_schedule["archive-guest-conversations"] = {
    "task": "archive_guest_conversations",
    "schedule": crontab(minute=0),  # Every hour at :00
}
```

### 2.6 Rate Limiting

| Limit | Value |
|-------|-------|
| Messages per hour per IP | 20 |
| Messages per day per IP | 50 |
| Max message length | 500 chars |

---

## Phase 3: Multi-Language Support

### 3.1 Registration Required Messages

```python
GUEST_REGISTRATION_MESSAGES = {
    "portfolio_access": {
        "en": "Create a free account to view your portfolio and track your DeFi positions.",
        "es": "Crea una cuenta gratuita para ver tu portafolio y rastrear tus posiciones DeFi.",
        "pt": "Crie uma conta gratuita para ver seu portfólio e rastrear suas posições DeFi.",
        "zh": "创建免费账户以查看您的投资组合并跟踪您的 DeFi 头寸。",
    },
    "balance_access": {
        "en": "Sign up to connect your wallet and view your balance.",
        "es": "Regístrate para conectar tu billetera y ver tu saldo.",
        "pt": "Cadastre-se para conectar sua carteira e ver seu saldo.",
        "zh": "注册以连接您的钱包并查看余额。",
    },
    "activity_access": {
        "en": "Create an account to view your transaction history.",
        "es": "Crea una cuenta para ver tu historial de transacciones.",
        "pt": "Crie uma conta para ver seu histórico de transações.",
        "zh": "创建账户以查看您的交易历史。",
    },
    "receive_access": {
        "en": "Sign up to get your personal wallet address for receiving funds.",
        "es": "Regístrate para obtener tu dirección de billetera personal.",
        "pt": "Cadastre-se para obter seu endereço de carteira pessoal.",
        "zh": "注册以获取您的个人钱包地址。",
    },
    "execute_action": {
        "en": "Create an account to execute DeFi transactions securely.",
        "es": "Crea una cuenta para ejecutar transacciones DeFi de forma segura.",
        "pt": "Crie uma conta para executar transações DeFi com segurança.",
        "zh": "创建账户以安全执行 DeFi 交易。",
    },
}

GUEST_CTA_MESSAGES = {
    "en": "Sign Up Free",
    "es": "Regístrate Gratis",
    "pt": "Cadastre-se Grátis",
    "zh": "免费注册",
}

GUEST_DEMO_DISCLAIMER = {
    "en": "You're in demo mode. Some features require registration.",
    "es": "Estás en modo demo. Algunas funciones requieren registro.",
    "pt": "Você está no modo demo. Alguns recursos requerem registro.",
    "zh": "您处于演示模式。某些功能需要注册。",
}
```

---

## Phase 4: Implementation Plan

### 4.1 Files to Create

| File | Description |
|------|-------------|
| `domain/guest/entities/guest_user.py` | Guest user entity |
| `domain/guest/entities/guest_conversation.py` | Guest conversation entity |
| `domain/guest/entities/guest_message.py` | Guest message entity |
| `domain/guest/ports/guest_repository.py` | Repository port |
| `infrastructure/persistence_sqla/mappings/guest.py` | SQLAlchemy mappings |
| `infrastructure/adapters/guest_repository_sqla.py` | Repository adapter |
| `application/guest/commands/send_guest_message.py` | Send message command |
| `application/guest/queries/get_guest_history.py` | Get history query |
| `application/guest/i18n/translations.py` | Guest i18n |
| `presentation/http/controllers/guest/router.py` | Guest chat router |
| `presentation/http/schemas/guest.py` | Request/response schemas |
| `infrastructure/celery/tasks.py` | Add archive task |
| `alembic migration` | Create guest tables |

### 4.2 Task Breakdown

| Task | Estimated Time |
|------|----------------|
| Create domain entities | 30 min |
| Create SQLAlchemy mappings | 30 min |
| Create repository adapter | 45 min |
| Create send message command | 60 min |
| Create guest chat router | 45 min |
| Create i18n translations | 20 min |
| Create Celery archive task | 20 min |
| Create migration | 15 min |
| Testing | 45 min |
| **Total** | **~5 hours** |

---

## Phase 5: Risk Assessment

### 5.1 Security Risks

| Risk | Mitigation |
|------|------------|
| IP spoofing | Validate X-Forwarded-For, trust only proxy chain |
| Abuse/spam | Rate limiting, message length limits |
| Bot attacks | Optional CAPTCHA, fingerprinting |
| Data leakage | No sensitive data in guest responses |

### 5.2 Technical Risks

| Risk | Mitigation |
|------|------------|
| High traffic | Efficient queries, caching |
| Database growth | Hourly archival, data retention policy |
| IP changes | Accept some session loss, fingerprint as backup |

---

## Approval

**Ready to implement?** Reply with `si` to proceed.

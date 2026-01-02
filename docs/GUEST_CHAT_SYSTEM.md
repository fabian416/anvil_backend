# Guest Chat System

The Guest Chat system provides a demo experience for unauthenticated users, allowing them to explore Anvil's AI capabilities before signing up.

## Overview

**Endpoint**: `POST /api/v1/guest/chat`

**Features**:
- No authentication required
- IP-based session tracking
- Rate limiting (20 messages/hour)
- Multi-language support (en, es, pt, zh)
- Real data from Hunter AI and ULTRA
- Registration prompts for restricted actions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Guest Chat Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Request ──▶ IP Check ──▶ Rate Limit ──▶ Intent Detection      │
│                                              │                  │
│                    ┌─────────────────────────┼─────────────────┐│
│                    │                         ▼                 ││
│                    │  ┌─────────────────────────────────────┐  ││
│                    │  │         Intent Router               │  ││
│                    │  │  ┌─────────┬─────────┬────────────┐ │  ││
│                    │  │  │Hunter AI│  ULTRA  │   DeFi     │ │  ││
│                    │  │  │ (real)  │ (real)  │ (restrict) │ │  ││
│                    │  │  └─────────┴─────────┴────────────┘ │  ││
│                    │  └─────────────────────────────────────┘  ││
│                    │                         │                 ││
│                    │                         ▼                 ││
│                    │           Registration CTA if needed      ││
│                    └───────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## API Reference

### Send Message

```http
POST /api/v1/guest/chat
Content-Type: application/json

{
  "content": "What is the sentiment for ETH?",
  "language": "en"
}
```

**Response**:
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "What is the sentiment for ETH?",
    "created_at": "2024-01-02T12:00:00Z"
  },
  "agent_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "📊 **Sentiment Analysis for ETH**...",
    "created_at": "2024-01-02T12:00:01Z"
  },
  "routing": {
    "intent": "hunter_sentiment",
    "confidence": 0.85,
    "handler": "sentiment_handler",
    "language": "en",
    "is_demo_mode": false,
    "is_live_data": true
  },
  "enrichment": {
    "overall_score": 67.0,
    "classification": "bullish",
    "hunter_tool": "sentiment_aggregator"
  },
  "guest_info": {
    "messages_remaining": 18,
    "session_active": true
  }
}
```

### Check Status

```http
GET /api/v1/guest/chat/status
```

**Response**:
```json
{
  "active": true,
  "messages_remaining": 18,
  "rate_limit": {
    "hourly": 20,
    "daily": 50
  }
}
```

## Supported Intents

### Hunter AI (Real Data)

| Intent | Description | Data Source |
|--------|-------------|-------------|
| `hunter_sentiment` | Market sentiment analysis | Twitter, Reddit, Discord, News |
| `hunter_price_prediction` | LSTM-based price forecasts | CoinGecko (real) |
| `hunter_risk_signals` | Risk factor analysis | On-chain + market data |
| `hunter_trading_signals` | Buy/sell recommendations | Aggregated analysis |
| `hunter_patterns` | Chart pattern detection | Price data |
| `hunter_portfolio` | Portfolio optimization | MPT algorithm |

### ULTRA (Real Data)

| Intent | Description | Data Source |
|--------|-------------|-------------|
| `ultra_arbitrage` | Cross-DEX opportunities | DEX price feeds |
| `ultra_flash_loans` | Flash loan protocols | Protocol data |
| `ultra_mev_protection` | MEV protection status | Flashbots |
| `ultra_auto_executor` | Automation strategies | Strategy engine |

### DeFi Shortcuts (Restricted)

These intents require wallet connection and are restricted for guests:

| Intent | Description | Why Restricted |
|--------|-------------|----------------|
| `portfolio` | View portfolio | Requires wallet |
| `balance` | Check balance | Requires wallet |
| `activity` | Transaction history | Requires wallet |
| `receive` | Generate receive address | Requires wallet |
| `swap` | Execute swap | Requires wallet |
| `lending` | Deposit/withdraw | Requires wallet |
| `money_market` | Aave/Compound | Requires wallet |

## Rate Limiting

**Configuration**:
```python
RATE_LIMIT_MESSAGES_PER_HOUR = 20
RATE_LIMIT_MESSAGES_PER_DAY = 50
MAX_MESSAGE_LENGTH = 500
```

**Rate Limit Response**:
```json
{
  "rate_limited": true,
  "guest_info": {
    "messages_remaining": 0,
    "reset_time": "2024-01-02T13:00:00Z"
  }
}
```

## Multi-Language Support

Supported languages:
- `en` - English (default)
- `es` - Spanish
- `pt` - Portuguese
- `zh` - Mandarin Chinese

**Example (Spanish)**:
```http
POST /api/v1/guest/chat
{
  "content": "¿Cuál es el sentimiento para ETH?",
  "language": "es"
}
```

## Database Schema

### Tables

```sql
-- Guest users (tracked by IP)
CREATE TABLE guest_users (
    id UUID PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    fingerprint VARCHAR(255),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    preferred_language VARCHAR(5) DEFAULT 'en',
    is_blocked BOOLEAN DEFAULT FALSE
);

-- Guest conversations
CREATE TABLE guest_conversations (
    id UUID PRIMARY KEY,
    guest_user_id UUID REFERENCES guest_users(id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP,
    language VARCHAR(5) DEFAULT 'en'
);

-- Guest messages
CREATE TABLE guest_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES guest_conversations(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(50),
    handler VARCHAR(100),
    confidence FLOAT,
    language VARCHAR(5) DEFAULT 'en',
    is_restricted_action BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

-- Guest telemetry
CREATE TABLE guest_telemetry (
    id UUID PRIMARY KEY,
    guest_user_id UUID REFERENCES guest_users(id),
    conversation_id UUID,
    event_type VARCHAR(50),
    event_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referer TEXT,
    language VARCHAR(5),
    created_at TIMESTAMP
);
```

## Celery Tasks

### Archive Old Conversations

Runs hourly to archive inactive guest conversations:

```python
@celery_app.task(name="archive_guest_conversations")
def archive_guest_conversations():
    """Archive guest conversations older than 1 hour."""
    # Marks conversations as 'archived'
    # Preserves data for analytics
```

## Registration Prompts

When a guest tries to access restricted features, they receive a registration prompt:

```json
{
  "registration_required": {
    "required": true,
    "reason": "wallet_required",
    "message": {
      "en": "Sign up to view your portfolio",
      "es": "Regístrate para ver tu portafolio"
    },
    "cta": {
      "en": "Create Free Account",
      "es": "Crear Cuenta Gratis"
    },
    "signup_url": "/signup"
  }
}
```

## Implementation Files

```
src/app/
├── application/guest/
│   ├── commands/
│   │   └── send_guest_message.py    # Main command
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── guest_handler_service.py # Real data handlers
│   └── i18n/
│       └── translations.py          # Multi-language strings
├── domain/guest/
│   ├── entities/
│   │   ├── guest_user.py
│   │   ├── guest_conversation.py
│   │   └── guest_message.py
│   └── ports/
│       └── guest_repository.py
├── infrastructure/
│   ├── adapters/
│   │   └── guest_repository_sqla.py
│   └── celery/
│       └── tasks.py                 # Archive task
└── presentation/http/controllers/
    └── guest/
        └── router.py                # API endpoints
```

## Testing

```bash
# Test guest chat endpoint
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "What is the sentiment for ETH?", "language": "en"}'

# Test rate limiting
for i in {1..25}; do
  curl -s -X POST http://localhost:8080/api/v1/guest/chat \
    -H "Content-Type: application/json" \
    -d '{"content": "test message '$i'", "language": "en"}' | jq '.guest_info.messages_remaining'
done
```

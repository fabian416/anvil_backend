# Guest Chat API Reference

**Version:** 1.0
**Last Updated:** 2026-01-11
**Base URL:** `https://api.anvil.app`

## Overview

The Guest Chat API provides unauthenticated access to Anvil's AI-powered DeFi assistant. Users can explore features, view real-time market data, and receive AI-powered insights without creating an account.

**Key Features:**
- No authentication required
- Real-time DeFi data from live protocols
- Hunter AI market intelligence
- GraphRAG protocol discovery
- Multi-language support (en, es, pt, zh)
- IP-based rate limiting

---

## Table of Contents

1. [Endpoints](#endpoints)
2. [Request Format](#request-format)
3. [Response Format](#response-format)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Intent Detection](#intent-detection)
7. [Enrichment Data](#enrichment-data)
8. [Examples](#examples)

---

## Endpoints

### POST /api/v1/guest/chat

Send a message to the guest chat assistant.

**URL:** `/api/v1/guest/chat`
**Method:** `POST`
**Authentication:** None (IP-based tracking)
**Content-Type:** `application/json`

---

## Request Format

### Request Body

```json
{
  "content": "string (required)",
  "language": "string (optional, default: 'en')"
}
```

### Parameters

| Field | Type | Required | Description | Values |
|-------|------|----------|-------------|--------|
| `content` | string | ✅ Yes | The user's message or query | Any text (max 1000 chars) |
| `language` | string | ❌ No | Response language code | `en`, `es`, `pt`, `zh` (default: `en`) |

### Example Request

```bash
curl -X POST https://api.anvil.app/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is the sentiment for BTC?",
    "language": "en"
  }'
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "agent_message": {
    "content": "string",
    "intent": "string",
    "confidence": "number"
  },
  "enrichment": {
    "...": "varies by intent"
  },
  "registration_required": {
    "required": "boolean",
    "message": "string (optional)",
    "action": "string (optional)"
  },
  "metadata": {
    "conversation_id": "string",
    "message_id": "string",
    "timestamp": "string (ISO 8601)",
    "processing_time_ms": "number"
  }
}
```

### Response Fields

#### `agent_message`

The conversational response from the AI assistant.

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Rich markdown-formatted response with emojis |
| `intent` | string | Detected intent (e.g., `HUNTER_SENTIMENT`, `SWAP`) |
| `confidence` | number | Intent detection confidence (0.0 - 1.0) |

#### `enrichment`

Structured data specific to the detected intent. See [Enrichment Data](#enrichment-data) section.

#### `registration_required`

Information about whether the user needs to sign up to proceed.

| Field | Type | Description |
|-------|------|-------------|
| `required` | boolean | `true` if signup is needed for execution |
| `message` | string | User-friendly message explaining why signup is needed |
| `action` | string | Action that requires registration (e.g., `execute_swap`) |

#### `metadata`

Response metadata and tracking information.

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | string (UUID) | Guest conversation identifier |
| `message_id` | string (UUID) | Message identifier |
| `timestamp` | string | ISO 8601 timestamp |
| `processing_time_ms` | number | Server processing time in milliseconds |

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description | Solution |
|-------------|------------|-------------|----------|
| 400 | `INVALID_REQUEST` | Malformed request body | Check request format |
| 400 | `MISSING_CONTENT` | `content` field is required | Include `content` in request |
| 400 | `CONTENT_TOO_LONG` | Message exceeds 1000 characters | Shorten your message |
| 400 | `INVALID_LANGUAGE` | Unsupported language code | Use `en`, `es`, `pt`, or `zh` |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests | Wait before retrying (see `retry_after`) |
| 500 | `INTERNAL_ERROR` | Server error | Retry or contact support |
| 503 | `SERVICE_UNAVAILABLE` | Temporary outage | Retry after a few minutes |

### Rate Limit Error (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You've reached the hourly limit of 20 messages. Please try again in 45 minutes.",
    "details": {
      "limit": 20,
      "window": "1h",
      "retry_after": 2700,
      "resets_at": "2026-01-11T15:30:00Z"
    }
  }
}
```

---

## Rate Limiting

### Limits

- **Hourly:** 20 messages per IP address
- **Daily:** 100 messages per IP address

### Rate Limit Headers

Every response includes rate limit headers:

```http
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1641909000
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the window |
| `X-RateLimit-Remaining` | Remaining requests in current window |
| `X-RateLimit-Reset` | Unix timestamp when the limit resets |

### Bypassing Rate Limits

Register for a free account to remove rate limits entirely.

---

## Intent Detection

The AI automatically detects the user's intent from natural language. No explicit intent parameter is required.

### Supported Intents

#### DeFi Shortcuts

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `SWAP` | Token swapping via 1inch | "Swap 100 USDC to ETH" |
| `BUY` | Purchase crypto | "Buy $500 of BTC" |
| `LENDING` | Yield earning via Morpho | "Lend 1000 USDC" |
| `MONEY_MARKET` | Compare lending rates | "Best rates for USDC" |
| `PORTFOLIO` | Portfolio tracking | "Show my portfolio" |
| `ACTIVITY` | Transaction history | "Recent activity" |
| `SEND` | Send crypto | "Send ETH" |
| `RECEIVE` | Receive crypto | "Receive USDC" |
| `BALANCE` | Wallet balance | "Check balance" |

#### Hunter AI

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `HUNTER_SENTIMENT` | Social sentiment analysis | "ETH sentiment" |
| `HUNTER_PRICE_PREDICTION` | LSTM price forecasting | "BTC price prediction" |
| `HUNTER_RISK_SIGNALS` | Market risk warnings | "Risk signals for SOL" |
| `HUNTER_TRADING_SIGNALS` | Buy/sell recommendations | "Trading signals for BTC" |
| `HUNTER_PATTERNS` | Chart pattern detection | "BTC chart patterns" |
| `HUNTER_PORTFOLIO` | Portfolio optimization | "Optimize my portfolio" |

#### GraphRAG

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `PROTOCOL_SEARCH` | Find DeFi protocols | "Find lending protocols" |
| `RISK_ASSESSMENT` | Protocol security analysis | "Is Aave safe?" |
| `SIMILAR_PROTOCOLS` | Protocol alternatives | "Protocols like Compound" |

#### Fallback

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `UNKNOWN` | Unrecognized intent | "Hello there" |
| `HELP` | Request for help | "What can you do?" |

### Intent Confidence Scores

The `agent_message.confidence` field indicates how confident the AI is in the detected intent:

- **0.9 - 1.0**: Very confident (clear, direct query)
- **0.7 - 0.9**: Confident (slight ambiguity)
- **0.5 - 0.7**: Moderate (ambiguous query)
- **< 0.5**: Low confidence (very ambiguous, falls back to `UNKNOWN`)

---

## Enrichment Data

The `enrichment` object contains structured data specific to each intent. Below are the schemas for each intent type.

### SWAP

```json
{
  "from_token": "USDC",
  "to_token": "ETH",
  "from_amount": 100.0,
  "to_amount": 0.0512,
  "exchange_rate": 1952.34,
  "price_impact": 0.12,
  "gas_estimate_usd": 3.45,
  "route": "1inch",
  "quote_timestamp": "2026-01-11T12:00:00Z"
}
```

### HUNTER_SENTIMENT

```json
{
  "token": "BTC",
  "overall_score": 0.72,
  "classification": "bullish",
  "sources": {
    "twitter": {"score": 0.65, "volume": 12400},
    "reddit": {"score": 0.78, "volume": 850},
    "news": {"score": 0.74, "volume": 45}
  },
  "hunter_tool": "sentiment_aggregator",
  "timestamp": "2026-01-11T12:00:00Z"
}
```

### HUNTER_PRICE_PREDICTION

```json
{
  "token": "BTC",
  "predictions": {
    "24h": {"price": 46200, "confidence": 0.82},
    "7d": {"price": 48500, "confidence": 0.71},
    "30d": {"price": 52000, "confidence": 0.58}
  },
  "historical_accuracy": 0.76,
  "model": "LSTM",
  "hunter_tool": "lstm_price_predictor"
}
```

### HUNTER_RISK_SIGNALS

```json
{
  "token": "BTC",
  "risk_level": "medium",
  "signals": [
    {
      "type": "volatility",
      "severity": "medium",
      "description": "Higher than average volatility detected"
    },
    {
      "type": "liquidation_risk",
      "severity": "low",
      "description": "Low liquidation cascade risk"
    }
  ],
  "recommendations": ["Monitor position sizes", "Consider stop losses"],
  "hunter_tool": "risk_signal_analyzer"
}
```

### HUNTER_TRADING_SIGNALS

```json
{
  "token": "BTC",
  "signal": "buy",
  "strength": "moderate",
  "confidence": 0.68,
  "indicators": {
    "rsi": 42,
    "macd": "bullish_crossover",
    "moving_averages": "above_50_day"
  },
  "entry_point": 45000,
  "exit_point": 48000,
  "stop_loss": 43500,
  "hunter_tool": "trading_signal_generator"
}
```

### HUNTER_PATTERNS

```json
{
  "token": "BTC",
  "patterns": [
    {
      "type": "ascending_triangle",
      "timeframe": "4h",
      "confidence": 0.85,
      "bullish": true,
      "target": 48500
    }
  ],
  "hunter_tool": "pattern_detector"
}
```

### HUNTER_PORTFOLIO

```json
{
  "recommendations": [
    {"asset": "BTC", "allocation": 40},
    {"asset": "ETH", "allocation": 30},
    {"asset": "USDC", "allocation": 20},
    {"asset": "SOL", "allocation": 10}
  ],
  "risk_profile": "moderate",
  "expected_return": 0.18,
  "volatility": 0.32,
  "hunter_tool": "portfolio_optimizer"
}
```

### PROTOCOL_SEARCH

```json
{
  "protocols": [
    {
      "name": "Aave",
      "category": "lending",
      "tvl": 12500000000,
      "chains": ["ethereum", "polygon", "arbitrum"],
      "features": ["flash_loans", "collateral_swap"]
    },
    {
      "name": "Compound",
      "category": "lending",
      "tvl": 8200000000,
      "chains": ["ethereum"],
      "features": ["governance", "liquidations"]
    }
  ]
}
```

### RISK_ASSESSMENT

```json
{
  "protocol": "Aave",
  "risk_score": 2.5,
  "risk_level": "low",
  "audits": [
    {
      "auditor": "OpenZeppelin",
      "date": "2023-08-15",
      "findings": "No critical issues"
    }
  ],
  "exploits": [],
  "recommendations": ["Well-audited and battle-tested"]
}
```

### SIMILAR_PROTOCOLS

```json
{
  "base_protocol": "Aave",
  "similar_protocols": [
    {
      "name": "Compound",
      "similarity": 0.92,
      "category": "lending",
      "differences": ["Governance model", "Interest rate model"]
    },
    {
      "name": "Morpho",
      "similarity": 0.85,
      "category": "lending",
      "differences": ["P2P matching layer", "Optimizer design"]
    }
  ]
}
```

### BUY

```json
{
  "crypto": "BTC",
  "amount_usd": 500,
  "crypto_amount": 0.0108,
  "price_per_unit": 46200,
  "total_cost": 500,
  "data_source": "coingecko"
}
```

### LENDING

```json
{
  "asset": "USDC",
  "amount": 1000,
  "apy": 8.5,
  "protocol": "Morpho",
  "vault_name": "Morpho Aave USDC Optimizer",
  "projected_earnings": {
    "daily": 0.23,
    "monthly": 7.08,
    "yearly": 85
  }
}
```

### MONEY_MARKET

```json
{
  "asset": "USDC",
  "chain": "ethereum",
  "rates": {
    "aave": {"supply_apy": 5.2, "borrow_apy": 7.8},
    "compound": {"supply_apy": 4.8, "borrow_apy": 8.1},
    "morpho": {"supply_apy": 8.5, "borrow_apy": 7.5}
  },
  "best_supply_protocol": "morpho",
  "best_supply_apy": 8.5,
  "best_borrow_protocol": "morpho",
  "best_borrow_apy": 7.5,
  "latency_ms": 245
}
```

---

## Examples

### Example 1: Sentiment Analysis

**Request:**

```bash
POST /api/v1/guest/chat
Content-Type: application/json

{
  "content": "What's the sentiment for ETH?",
  "language": "en"
}
```

**Response:**

```json
{
  "agent_message": {
    "content": "📊 **ETH Sentiment Analysis**\n\n✅ **Overall**: Bullish (0.68)\n\n**Source Breakdown:**\n- 🐦 Twitter: Bullish (0.65) - 9,800 mentions\n- 🗣️ Reddit: Bullish (0.72) - 620 discussions\n- 📰 News: Neutral (0.60) - 32 articles\n\n**Key Talking Points:**\n- Upcoming network upgrades\n- Institutional adoption increasing\n- DeFi TVL growth\n\n*Data refreshed 5 minutes ago*",
    "intent": "HUNTER_SENTIMENT",
    "confidence": 0.95
  },
  "enrichment": {
    "token": "ETH",
    "overall_score": 0.68,
    "classification": "bullish",
    "sources": {
      "twitter": {"score": 0.65, "volume": 9800},
      "reddit": {"score": 0.72, "volume": 620},
      "news": {"score": 0.60, "volume": 32}
    },
    "hunter_tool": "sentiment_aggregator",
    "timestamp": "2026-01-11T12:05:00Z"
  },
  "registration_required": {
    "required": false
  },
  "metadata": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2026-01-11T12:05:12Z",
    "processing_time_ms": 523
  }
}
```

### Example 2: Swap Quote

**Request:**

```bash
POST /api/v1/guest/chat
Content-Type: application/json

{
  "content": "Swap 100 USDC to ETH",
  "language": "en"
}
```

**Response:**

```json
{
  "agent_message": {
    "content": "💱 **Swap Quote**\n\n**From:** 100 USDC\n**To:** ~0.0512 ETH\n\n**Exchange Rate:** 1 ETH = 1,952.34 USDC\n**Price Impact:** 0.12%\n**Gas Fee:** ~$3.45\n\n**Route:** 1inch Aggregator\n\n🔐 **Sign up to execute this swap!**\n\n*Quote valid for 60 seconds*",
    "intent": "SWAP",
    "confidence": 0.98
  },
  "enrichment": {
    "from_token": "USDC",
    "to_token": "ETH",
    "from_amount": 100.0,
    "to_amount": 0.0512,
    "exchange_rate": 1952.34,
    "price_impact": 0.12,
    "gas_estimate_usd": 3.45,
    "route": "1inch",
    "quote_timestamp": "2026-01-11T12:10:00Z"
  },
  "registration_required": {
    "required": true,
    "message": "Sign up to execute swaps and other DeFi transactions",
    "action": "execute_swap"
  },
  "metadata": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2026-01-11T12:10:15Z",
    "processing_time_ms": 387
  }
}
```

### Example 3: Protocol Search

**Request:**

```bash
POST /api/v1/guest/chat
Content-Type: application/json

{
  "content": "Find me the top lending protocols",
  "language": "en"
}
```

**Response:**

```json
{
  "agent_message": {
    "content": "🏦 **Top Lending Protocols**\n\n1. **Aave** - $12.5B TVL\n   - Multi-chain support\n   - Flash loans available\n   - Well-audited\n\n2. **Compound** - $8.2B TVL\n   - Ethereum native\n   - Governance token\n   - Battle-tested\n\n3. **Morpho** - $2.1B TVL\n   - P2P matching\n   - Higher yields\n   - Built on Aave/Compound\n\n**Want to compare rates?** Try: \"Compare rates for USDC\"",
    "intent": "PROTOCOL_SEARCH",
    "confidence": 0.92
  },
  "enrichment": {
    "protocols": [
      {
        "name": "Aave",
        "category": "lending",
        "tvl": 12500000000,
        "chains": ["ethereum", "polygon", "arbitrum"],
        "features": ["flash_loans", "collateral_swap"]
      },
      {
        "name": "Compound",
        "category": "lending",
        "tvl": 8200000000,
        "chains": ["ethereum"],
        "features": ["governance", "liquidations"]
      },
      {
        "name": "Morpho",
        "category": "lending",
        "tvl": 2100000000,
        "chains": ["ethereum"],
        "features": ["p2p_matching", "optimized_yields"]
      }
    ]
  },
  "registration_required": {
    "required": false
  },
  "metadata": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440003",
    "timestamp": "2026-01-11T12:15:20Z",
    "processing_time_ms": 612
  }
}
```

### Example 4: Rate Limit Error

**Request:**

```bash
POST /api/v1/guest/chat
Content-Type: application/json

{
  "content": "BTC price",
  "language": "en"
}
```

**Response (429 Too Many Requests):**

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You've reached the hourly limit of 20 messages. Please try again in 42 minutes, or sign up for unlimited access!",
    "details": {
      "limit": 20,
      "window": "1h",
      "retry_after": 2520,
      "resets_at": "2026-01-11T13:00:00Z",
      "signup_url": "https://anvil.app/signup"
    }
  }
}
```

### Example 5: Multi-Language (Spanish)

**Request:**

```bash
POST /api/v1/guest/chat
Content-Type: application/json

{
  "content": "sentimiento de BTC",
  "language": "es"
}
```

**Response:**

```json
{
  "agent_message": {
    "content": "📊 **Análisis de Sentimiento para BTC**\n\n✅ **General**: Alcista (0.72)\n\n**Desglose por Fuente:**\n- 🐦 Twitter: Alcista (0.68) - 15,200 menciones\n- 🗣️ Reddit: Alcista (0.75) - 980 discusiones\n- 📰 Noticias: Neutral (0.65) - 48 artículos\n\n**Temas Principales:**\n- Adopción institucional\n- Halving próximo\n- Regulación positiva\n\n*Datos actualizados hace 3 minutos*",
    "intent": "HUNTER_SENTIMENT",
    "confidence": 0.94
  },
  "enrichment": {
    "token": "BTC",
    "overall_score": 0.72,
    "classification": "bullish",
    "sources": {
      "twitter": {"score": 0.68, "volume": 15200},
      "reddit": {"score": 0.75, "volume": 980},
      "news": {"score": 0.65, "volume": 48}
    },
    "hunter_tool": "sentiment_aggregator",
    "timestamp": "2026-01-11T12:20:00Z"
  },
  "registration_required": {
    "required": false
  },
  "metadata": {
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440004",
    "timestamp": "2026-01-11T12:20:25Z",
    "processing_time_ms": 498
  }
}
```

---

## Integration Tips

### Best Practices

1. **Handle Rate Limits Gracefully**
   - Check `X-RateLimit-Remaining` header
   - Implement exponential backoff on 429 errors
   - Show users the `retry_after` countdown

2. **Cache Responses When Appropriate**
   - Price quotes are valid for ~60 seconds
   - Sentiment data refreshes every 5-10 minutes
   - Protocol data changes infrequently

3. **Display Rich Content**
   - Parse markdown in `agent_message.content`
   - Render emojis for visual appeal
   - Use structured `enrichment` data for charts/tables

4. **Progressive Disclosure**
   - Show `agent_message.content` immediately
   - Display `enrichment` data in expandable sections
   - Highlight `registration_required` with clear CTAs

5. **Error Handling**
   - Always check HTTP status codes
   - Display user-friendly error messages
   - Provide retry mechanisms for 5xx errors

### Client Libraries

**JavaScript/TypeScript:**

```typescript
import axios from 'axios';

const guestChat = async (content: string, language = 'en') => {
  try {
    const response = await axios.post('https://api.anvil.app/api/v1/guest/chat', {
      content,
      language
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 429) {
      const retryAfter = error.response.data.error.details.retry_after;
      console.log(`Rate limited. Retry after ${retryAfter} seconds`);
    }
    throw error;
  }
};
```

**Python:**

```python
import requests

def guest_chat(content: str, language: str = 'en') -> dict:
    url = 'https://api.anvil.app/api/v1/guest/chat'
    payload = {'content': content, 'language': language}

    response = requests.post(url, json=payload)

    if response.status_code == 429:
        error = response.json()['error']
        retry_after = error['details']['retry_after']
        print(f"Rate limited. Retry after {retry_after} seconds")
        raise Exception("Rate limit exceeded")

    response.raise_for_status()
    return response.json()
```

---

## Support

**API Questions?**
- 📧 Email: api@anvilcrypto.com
- 📚 Docs: [docs.anvil.app](https://docs.anvil.app)
- 💬 Discord: [discord.gg/anvil](https://discord.gg/anvil)

**Want Higher Limits?**
- Sign up for a free account for unlimited access
- Enterprise plans available for high-volume integrations

---

*API Reference Version 1.0 - Last Updated: 2026-01-11*

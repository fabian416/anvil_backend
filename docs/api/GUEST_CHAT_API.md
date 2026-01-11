# Guest Chat API Documentation

**Version:** 1.0
**Last Updated:** 2026-01-11
**Base URL:** `https://api.anvil.fi/api/v1`

---

## Overview

The Guest Chat API provides unauthenticated access to Anvil's AI-powered crypto intelligence platform. Guest users can interact with Hunter AI for market analysis, sentiment tracking, trading signals, and more without creating an account.

### Key Features

- **🚀 No Authentication Required**: IP-based guest identification
- **🤖 6 Hunter AI Tools**: Sentiment, signals, patterns, predictions, risk, portfolio
- **🌍 Multi-Language Support**: English, Spanish, Portuguese, Chinese
- **📊 Real Market Data**: Live prices, news, and analysis
- **⚡ Redis Caching**: <100ms response times for cached queries
- **🔒 Rate Limited**: 20 messages per hour per IP

---

## Authentication

### Guest Access (No Auth Required)

Guest users are identified by IP address. No registration or API key needed.

```http
POST /api/v1/guest/chat
Content-Type: application/json
X-Forwarded-For: 192.168.1.100
```

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/json` |
| `X-Forwarded-For` | No | Client IP (auto-detected if not provided) |
| `Accept-Language` | No | Preferred language (en, es, pt, zh) |

---

## Rate Limiting

### Limits

- **Guest Users**: 20 messages per hour per IP address
- **Window**: Rolling 60-minute window
- **Reset**: Automatically after 1 hour from first message

### Rate Limit Headers

```http
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 2026-01-11T15:30:00Z
```

### Rate Limit Exceeded

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You've reached the guest message limit of 20 per hour",
    "details": {
      "limit": 20,
      "reset_at": "2026-01-11T15:30:00Z",
      "suggestion": "Register for unlimited access at https://anvil.fi/signup"
    }
  }
}
```

**HTTP Status**: `429 Too Many Requests`

---

## Endpoints

### POST /api/v1/guest/chat

Send a message to the guest chat system and receive AI-powered responses.

#### Request Body

```json
{
  "content": "What is the sentiment for BTC?",
  "language": "en",
  "context": ""
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | User message (1-1000 characters) |
| `language` | string | No | Response language: `en`, `es`, `pt`, `zh` (default: `en`) |
| `context` | string | No | Previous conversation context |

#### Response

```json
{
  "message_id": "msg_a1b2c3d4e5f6",
  "content": "📊 **Sentiment Analysis for BTC**\n\n**Overall:** Bullish (72.5/100)\n**Confidence:** 85%\n\n**By Source:**\n- Twitter: 🟢 75/100\n- Reddit: 🟢 68/100\n- News: 🟡 74/100\n- Discord: 🟢 73/100\n\n💡 **Try Anvil Pro** for real-time alerts and unlimited access.\n[Sign up free →](https://anvil.fi/signup)",
  "intent": "hunter_sentiment",
  "enrichment": {
    "token": "BTC",
    "overall_score": 0.45,
    "overall_score_percentage": 72.5,
    "classification": "bullish",
    "sources": {
      "twitter": {"score": 75, "classification": "bullish"},
      "reddit": {"score": 68, "classification": "bullish"},
      "news": {"score": 74, "classification": "bullish"},
      "discord": {"score": 73, "classification": "bullish"}
    },
    "hunter_tool": "sentiment_aggregator"
  },
  "sources": [
    {
      "source_type": "SOCIAL_MEDIA",
      "source_name": "Twitter",
      "citation_text": "Twitter sentiment analysis for BTC",
      "fetched_at": "2026-01-11T14:30:00Z",
      "data_points_used": 450,
      "relevance_score": 0.25
    }
  ],
  "requires_registration": false,
  "created_at": "2026-01-11T14:30:15Z"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Unique message identifier |
| `content` | string | Formatted response text (Markdown) |
| `intent` | string | Detected intent (see Intent Types) |
| `enrichment` | object | Structured data from Hunter AI |
| `sources` | array | Data sources used (optional) |
| `requires_registration` | boolean | Whether action requires auth |
| `created_at` | string | ISO 8601 timestamp |

---

## Intent Types

The system automatically detects user intent and routes to appropriate handlers.

### Hunter AI Intents

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `hunter_sentiment` | Market sentiment analysis | "What's the sentiment for ETH?" |
| `hunter_trading_signals` | Trading signals with entry/exit | "Give me trading signals for SOL" |
| `hunter_patterns` | Chart pattern recognition | "What patterns do you see in BTC?" |
| `hunter_price_prediction` | 7-day price forecast | "Predict the price of ETH" |
| `hunter_risk_signals` | Risk analysis and warnings | "What are the risks for BTC?" |
| `hunter_portfolio` | Portfolio optimization | "Optimize my portfolio" |

### ULTRA Intents

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `ultra_mev_protection` | MEV protection analysis | "How to protect from MEV?" |
| `ultra_flash_loans` | Flash loan opportunities | "Find flash loan opportunities" |
| `ultra_arbitrage` | Cross-DEX arbitrage | "Show me arbitrage opportunities" |

### General Intents

| Intent | Description | Example Query |
|--------|-------------|---------------|
| `greeting` | Welcome message | "Hello", "Hi" |
| `help` | System help | "How does this work?" |
| `unknown` | Fallback for unclear queries | - |

---

## Hunter AI Tools

### 1. Sentiment Analysis

**Intent:** `hunter_sentiment`

Aggregate sentiment from Twitter, Reddit, Discord, and news sources.

**Example Request:**

```json
{
  "content": "What's the sentiment for BTC?",
  "language": "en"
}
```

**Example Response:**

```json
{
  "content": "📊 **Sentiment Analysis for BTC**\n\n**Overall:** Bullish (72.5/100)\n**Confidence:** 85%\n\n**By Source:**\n- Twitter: 🟢 75/100\n- Reddit: 🟢 68/100\n- News: 🟡 74/100\n- Discord: 🟢 73/100",
  "enrichment": {
    "token": "BTC",
    "overall_score": 0.45,
    "overall_score_percentage": 72.5,
    "classification": "bullish",
    "sources": {
      "twitter": {"score": 75, "classification": "bullish"},
      "reddit": {"score": 68, "classification": "bullish"},
      "news": {"score": 74, "classification": "bullish"},
      "discord": {"score": 73, "classification": "bullish"}
    },
    "hunter_tool": "sentiment_aggregator"
  }
}
```

**Enrichment Fields:**

- `token`: Token symbol (BTC, ETH, etc.)
- `overall_score`: Normalized sentiment (-1 to 1)
- `overall_score_percentage`: Raw score (0-100)
- `classification`: "bullish", "bearish", "neutral"
- `sources`: Breakdown by data source

### 2. Trading Signals

**Intent:** `hunter_trading_signals`

Generate actionable trading signals with entry, stop loss, and take profit prices.

**Example Request:**

```json
{
  "content": "Give me trading signals for ETH",
  "language": "en"
}
```

**Example Response:**

```json
{
  "content": "📈 **Trading Signals for ETH**\n\n🟢 **Signal:** BUY\n**Strength:** 63.5/100\n**Confidence:** 59%\n\n**Entry Price:** $1,964.57\n**Stop Loss:** $1,851.14\n**Take Profit:** $2,191.42",
  "enrichment": {
    "token": "ETH",
    "signal_type": "BUY",
    "signal_strength": 63.52,
    "confidence": 0.586,
    "entry_price": 1964.57,
    "stop_loss_price": 1851.14,
    "take_profit_price": 2191.42,
    "hunter_tool": "signal_generator"
  }
}
```

**Enrichment Fields:**

- `signal_type`: "BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"
- `signal_strength`: 0-100 score
- `confidence`: 0-1 confidence level
- `entry_price`, `stop_loss_price`, `take_profit_price`: USD prices

### 3. Pattern Recognition

**Intent:** `hunter_patterns`

Detect chart patterns (head & shoulders, triangles) and candlestick patterns.

**Example Request:**

```json
{
  "content": "What patterns do you see in BTC?",
  "language": "en"
}
```

**Example Response:**

```json
{
  "enrichment": {
    "token": "BTC",
    "chart_patterns": ["ascending_triangle", "double_bottom"],
    "candlestick_patterns": ["bullish_engulfing", "morning_star"],
    "hunter_tool": "pattern_recognizer"
  }
}
```

**Pattern Types:**

**Chart Patterns:**
- `head_and_shoulders`, `inverse_head_and_shoulders`
- `double_top`, `double_bottom`
- `ascending_triangle`, `descending_triangle`
- `bull_flag`, `bear_flag`

**Candlestick Patterns:**
- `bullish_engulfing`, `bearish_engulfing`
- `morning_star`, `evening_star`
- `hammer`, `shooting_star`
- `doji`, `marubozu`

### 4. Price Prediction

**Intent:** `hunter_price_prediction`

LSTM-based 7-day price forecast with confidence intervals.

**Example Request:**

```json
{
  "content": "Predict the price of SOL",
  "language": "en"
}
```

**Example Response:**

```json
{
  "enrichment": {
    "token": "SOL",
    "current_price": 98.45,
    "predicted_price": 105.23,
    "change_percent": 6.89,
    "direction": "up",
    "confidence": 0.72,
    "hunter_tool": "lstm_predictor"
  }
}
```

**Enrichment Fields:**

- `current_price`: Current USD price
- `predicted_price`: 7-day forecast
- `change_percent`: Expected % change
- `direction`: "up", "down", "neutral"
- `confidence`: 0-1 model confidence

### 5. Risk Signals

**Intent:** `hunter_risk_signals`

Comprehensive risk analysis including volatility, liquidity, and whale activity.

**Example Request:**

```json
{
  "content": "What are the risks for BTC?",
  "language": "en"
}
```

**Example Response:**

```json
{
  "enrichment": {
    "token": "BTC",
    "overall_risk_score": 35.8,
    "risk_level": "moderate",
    "risk_factors": {
      "volatility": {
        "risk_score": 42.5,
        "risk_level": "moderate",
        "indicator": "30-day volatility: 45%"
      },
      "liquidity": {
        "risk_score": 15.2,
        "risk_level": "low",
        "indicator": "Liquidity depth: $500M"
      },
      "whale_activity": {
        "risk_score": 58.3,
        "risk_level": "elevated",
        "indicator": "Large transfers: 12 in 24h"
      }
    },
    "recommendation": "Consider hedging positions during high volatility",
    "hunter_tool": "risk_analyzer"
  }
}
```

**Risk Levels:** `low`, `moderate`, `elevated`, `high`, `critical`

### 6. Portfolio Optimization

**Intent:** `hunter_portfolio`

Modern portfolio theory-based allocation recommendations.

**Example Request:**

```json
{
  "content": "Optimize my portfolio",
  "language": "en"
}
```

**Example Response:**

```json
{
  "enrichment": {
    "allocation": {
      "BTC": 0.45,
      "ETH": 0.35,
      "USDC": 0.20
    },
    "expected_return": 0.18,
    "sharpe_ratio": 1.25,
    "hunter_tool": "portfolio_optimizer"
  },
  "requires_registration": true
}
```

**Note:** Portfolio optimization requires registration to apply recommendations.

---

## ULTRA Tools

### MEV Protection

**Intent:** `ultra_mev_protection`

Analyze transaction for MEV risks and provide protection strategies.

**Example:**

```json
{
  "content": "How to protect from MEV?",
  "enrichment": {
    "protection_strategies": [
      "Use private transaction pools",
      "Enable MEV protection on wallet",
      "Split large orders"
    ],
    "ultra_tool": "mev_protection"
  }
}
```

### Flash Loan Opportunities

**Intent:** `ultra_flash_loans`

Discover flash loan arbitrage opportunities across DeFi protocols.

**Example:**

```json
{
  "content": "Find flash loan opportunities",
  "enrichment": {
    "opportunities": [
      {
        "profit": 125.50,
        "protocols": ["Aave", "Uniswap", "Curve"],
        "risk_score": 32.5
      }
    ],
    "ultra_tool": "flash_loan_engine"
  }
}
```

### Arbitrage Discovery

**Intent:** `ultra_arbitrage`

Find cross-DEX arbitrage opportunities in real-time.

**Example:**

```json
{
  "content": "Show me arbitrage opportunities",
  "enrichment": {
    "opportunities": [
      {
        "token_pair": "ETH/USDC",
        "buy_dex": "Uniswap",
        "sell_dex": "SushiSwap",
        "profit_percent": 0.85,
        "estimated_profit": 42.50
      }
    ],
    "ultra_tool": "arbitrage_discovery"
  }
}
```

---

## Multi-Language Support

### Supported Languages

| Code | Language | Example |
|------|----------|---------|
| `en` | English | "What's the price of BTC?" |
| `es` | Spanish | "¿Cuál es el precio de BTC?" |
| `pt` | Portuguese | "Qual é o preço do BTC?" |
| `zh` | Chinese | "BTC的价格是多少?" |

### Language Detection

The system automatically detects language from content if not specified:

```json
{
  "content": "¿Cuál es el sentimiento para BTC?"
}
```

Response will be in Spanish automatically.

### Explicit Language Setting

```json
{
  "content": "What's the sentiment for BTC?",
  "language": "es"
}
```

Response will be in Spanish despite English query.

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_REQUEST` | 400 | Malformed request body |
| `MESSAGE_TOO_LONG` | 400 | Content exceeds 1000 chars |
| `INVALID_LANGUAGE` | 400 | Unsupported language code |
| `SERVICE_UNAVAILABLE` | 503 | Hunter AI service down |
| `INTERNAL_ERROR` | 500 | Server error |

### Rate Limit Example

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-01-11T15:30:00Z
Retry-After: 1200
```

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You've reached the guest message limit of 20 per hour",
    "details": {
      "limit": 20,
      "reset_at": "2026-01-11T15:30:00Z"
    }
  }
}
```

### Service Unavailable Example

```http
HTTP/1.1 503 Service Unavailable
Retry-After: 60
```

```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Hunter AI sentiment service is temporarily unavailable",
    "details": {
      "service": "sentiment_aggregator",
      "retry_after": 60
    }
  }
}
```

---

## Code Examples

### cURL

```bash
# Basic sentiment query
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is the sentiment for BTC?",
    "language": "en"
  }'

# Trading signals
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Give me trading signals for ETH",
    "language": "en"
  }'
```

### JavaScript (Fetch API)

```javascript
async function getGuestChatResponse(content, language = 'en') {
  const response = await fetch('https://api.anvil.fi/api/v1/guest/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content, language }),
  });

  if (!response.ok) {
    if (response.status === 429) {
      const data = await response.json();
      throw new Error(`Rate limit exceeded. Reset at: ${data.error.details.reset_at}`);
    }
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Usage
try {
  const result = await getGuestChatResponse('What is the sentiment for BTC?');
  console.log('Response:', result.content);
  console.log('Enrichment:', result.enrichment);
} catch (error) {
  console.error('Error:', error.message);
}
```

### Python (requests)

```python
import requests

def get_guest_chat_response(content: str, language: str = "en"):
    """Send message to guest chat API."""
    url = "https://api.anvil.fi/api/v1/guest/chat"
    payload = {
        "content": content,
        "language": language
    }

    response = requests.post(url, json=payload)

    if response.status_code == 429:
        error_data = response.json()
        reset_at = error_data["error"]["details"]["reset_at"]
        raise Exception(f"Rate limit exceeded. Reset at: {reset_at}")

    response.raise_for_status()
    return response.json()

# Usage
try:
    result = get_guest_chat_response("What is the sentiment for BTC?")
    print("Response:", result["content"])
    print("Enrichment:", result["enrichment"])
except Exception as error:
    print("Error:", str(error))
```

### TypeScript (Axios)

```typescript
import axios, { AxiosError } from 'axios';

interface GuestChatRequest {
  content: string;
  language?: string;
}

interface GuestChatResponse {
  message_id: string;
  content: string;
  intent: string;
  enrichment: Record<string, any>;
  requires_registration: boolean;
  created_at: string;
}

async function getGuestChatResponse(
  content: string,
  language: string = 'en'
): Promise<GuestChatResponse> {
  try {
    const response = await axios.post<GuestChatResponse>(
      'https://api.anvil.fi/api/v1/guest/chat',
      { content, language }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 429) {
        const resetAt = error.response.data.error.details.reset_at;
        throw new Error(`Rate limit exceeded. Reset at: ${resetAt}`);
      }
    }
    throw error;
  }
}

// Usage
try {
  const result = await getGuestChatResponse('What is the sentiment for BTC?');
  console.log('Response:', result.content);
  console.log('Enrichment:', result.enrichment);
} catch (error) {
  console.error('Error:', error.message);
}
```

---

## Best Practices

### 1. Handle Rate Limits Gracefully

```javascript
async function chatWithRetry(content, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await getGuestChatResponse(content);
    } catch (error) {
      if (error.message.includes('Rate limit')) {
        // Extract reset time and wait
        const resetAt = new Date(error.details.reset_at);
        const waitTime = resetAt - new Date();

        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
      }
      throw error;
    }
  }
}
```

### 2. Cache Responses Client-Side

```javascript
const responseCache = new Map();

async function getCachedResponse(content) {
  const cacheKey = content.toLowerCase().trim();

  if (responseCache.has(cacheKey)) {
    const { data, timestamp } = responseCache.get(cacheKey);
    // Cache for 5 minutes
    if (Date.now() - timestamp < 5 * 60 * 1000) {
      return data;
    }
  }

  const response = await getGuestChatResponse(content);
  responseCache.set(cacheKey, {
    data: response,
    timestamp: Date.now()
  });

  return response;
}
```

### 3. Validate Input

```javascript
function validateMessage(content) {
  if (!content || content.trim().length === 0) {
    throw new Error('Message content cannot be empty');
  }

  if (content.length > 1000) {
    throw new Error('Message exceeds 1000 character limit');
  }

  return content.trim();
}
```

### 4. Parse Enrichment Data

```javascript
function formatSentimentResponse(response) {
  const { enrichment } = response;

  return {
    token: enrichment.token,
    sentiment: enrichment.classification,
    score: enrichment.overall_score_percentage,
    sources: Object.entries(enrichment.sources).map(([name, data]) => ({
      name,
      score: data.score,
      sentiment: data.classification
    }))
  };
}
```

---

## Performance Optimization

### Response Times

| Scenario | Expected Time | Cache Status |
|----------|---------------|--------------|
| Cached popular token (BTC/ETH) | <100ms | HIT |
| Cached less popular token | <100ms | HIT |
| Uncached query (first time) | 1-3s | MISS |
| Service rate limited | 500-1000ms | Fallback |

### Cache Strategy

- **Popular Tokens** (BTC, ETH, SOL): Pre-warmed, 5-minute TTL
- **Other Tokens**: Cached on-demand, 5-minute TTL
- **Portfolio/Risk Analysis**: 10-minute TTL
- **Cache Hit Rate**: >80% for guest queries

### Recommendations

1. **Batch Requests**: Group related queries when possible
2. **Client Caching**: Cache responses for 5 minutes
3. **Token Normalization**: Always use uppercase symbols (BTC, not btc)
4. **Language Consistency**: Use same language code for better cache hits

---

## Webhooks (Coming Soon)

Future support for real-time price alerts and signal notifications via webhooks.

---

## Changelog

### Version 1.0 (2026-01-11)

- Initial release
- 6 Hunter AI tools
- 3 ULTRA tools
- Multi-language support (4 languages)
- Rate limiting (20 msg/hour)
- Redis caching
- IP-based guest identification

---

## Support

- **Documentation**: https://docs.anvil.fi
- **Status Page**: https://status.anvil.fi
- **Discord**: https://discord.gg/anvil
- **Email**: support@anvil.fi

---

## Legal

- **Terms of Service**: https://anvil.fi/terms
- **Privacy Policy**: https://anvil.fi/privacy
- **Rate Limit Policy**: https://anvil.fi/rate-limits

---

**© 2026 Anvil. All rights reserved.**

# Guest Chat Testing Guide for CEO

This document provides a comprehensive testing guide for the Guest Chat API, allowing you to manually test all features and use cases.

## Base Configuration

**Base URL:** `http://localhost:8080` (or your server URL)  
**API Version:** `/api/v1`

## Quick Start

### 1. Test Shortcuts Endpoint (Public)

Get available chat shortcuts in different languages:

```bash
# English
curl -X GET "http://localhost:8080/api/v1/chat/shortcuts?lang=en"

# Spanish
curl -X GET "http://localhost:8080/api/v1/chat/shortcuts?lang=es"

# Portuguese
curl -X GET "http://localhost:8080/api/v1/chat/shortcuts?lang=pt"

# Chinese
curl -X GET "http://localhost:8080/api/v1/chat/shortcuts?lang=zh"

# Default (English)
curl -X GET "http://localhost:8080/api/v1/chat/shortcuts"
```

**Expected Response:**
- Status: `200 OK`
- Contains: `language`, `language_name`, `shortcuts` array
- Should have 7 shortcuts: `lending`, `swap`, `portfolio`, etc.

---

## Guest Chat Endpoint

**Endpoint:** `POST /api/v1/guest/chat`

**Headers Required:**
- `Content-Type: application/json`
- `X-Forwarded-For: <unique-ip>` (for session tracking)

**Request Format:**
```json
{
  "content": "Your message here",
  "language": "en"
}
```

**Languages Supported:** `en`, `es`, `pt`, `zh`

---

## Test Cases by Category

### 1. Basic Chat & General Messages

#### Test 1.1: General Greeting
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -d '{
    "content": "Hello, what can you help me with?",
    "language": "en"
  }'
```

**Expected:**
- Status: `200 OK`
- Contains: `conversation_id`, `message_id`, `user_message`, `agent_message`, `routing`
- Agent message should mention "DeFi", "AI", or "assistant"
- Routing intent: `general_conversation`

#### Test 1.2: Spanish Language
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.2" \
  -d '{
    "content": "Hola, ¿qué puedes hacer?",
    "language": "es"
  }'
```

**Expected:**
- Status: `200 OK`
- Routing language: `es`
- Response should contain Spanish words: "puedo", "ayudar", "protocolos", etc.

#### Test 1.3: Multi-turn Conversation
```bash
# First message
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.3" \
  -d '{
    "content": "What is the sentiment for ETH?",
    "language": "en"
  }'

# Second message (use same IP for context)
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.3" \
  -d '{
    "content": "And what about Bitcoin?",
    "language": "en"
  }'
```

**Expected:**
- Both messages should have same `conversation_id`
- Second response should reference "Bitcoin" or "BTC"

---

### 2. Hunter AI Features

#### Test 2.1: Sentiment Analysis (English)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.10" \
  -d '{
    "content": "What is the sentiment for ETH?",
    "language": "en"
  }'
```

**Expected:**
- Intent: `hunter_sentiment` or `general_conversation`
- Content mentions: "sentiment", "score", "twitter", "reddit", "news", "ETH"
- May include `enrichment` with `token`, `sources`, or `hunter_tool`

#### Test 2.2: Sentiment Analysis (Spanish)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.11" \
  -d '{
    "content": "¿Cuál es el sentimiento para ETH?",
    "language": "es"
  }'
```

#### Test 2.3: Sentiment Analysis (Portuguese)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.12" \
  -d '{
    "content": "Qual é o sentimento para ETH?",
    "language": "pt"
  }'
```

#### Test 2.4: Sentiment Analysis (Chinese)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.13" \
  -d '{
    "content": "ETH的情绪如何？",
    "language": "zh"
  }'
```

#### Test 2.5: Price Prediction
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.20" \
  -d '{
    "content": "What is the price prediction for BTC?",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "price", "prediction", "forecast", "BTC", "bitcoin", "model"
- May include `enrichment` with `token`, `current_price`, `predicted_price`, `model`

#### Test 2.6: Risk Signals
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.21" \
  -d '{
    "content": "What are the risk signals for ETH?",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "risk", "signal", "ETH", "whale", "liquidation", "danger", "warning"

#### Test 2.7: Trading Signals
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.22" \
  -d '{
    "content": "Show me trading signals for BTC",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "trading", "signal", "BTC", "buy", "sell", "entry", "stop loss", "confidence"

#### Test 2.8: Pattern Recognition
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.23" \
  -d '{
    "content": "What patterns do you see in ETH chart?",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "pattern", "chart", "ETH", "head and shoulders", "double bottom", "flag", "triangle", "breakout"

#### Test 2.9: Portfolio Optimization
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.24" \
  -d '{
    "content": "How should I optimize my portfolio?",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "portfolio", "optimize", "allocation", "strategy", "risk", "return"

---

### 3. ULTRA Features

#### Test 3.1: Arbitrage Discovery (English)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.30" \
  -d '{
    "content": "Find arbitrage opportunities",
    "language": "en"
  }'
```

**Expected:**
- Intent: `ultra_arbitrage` or `general_conversation`
- Content mentions: "arbitrage", "opportunity", "profit", "route", "ROI", "ULTRA", "DeFi", "trading"
- May include `enrichment` with `ultra_tool`, `arbitrage_discovery`, `opportunities_found`
- May require registration: `registration_required: true`

#### Test 3.2: Arbitrage Discovery (Spanish)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.31" \
  -d '{
    "content": "Encuentra oportunidades de arbitraje",
    "language": "es"
  }'
```

#### Test 3.3: Arbitrage Discovery (Portuguese)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.32" \
  -d '{
    "content": "Encontre oportunidades de arbitragem",
    "language": "pt"
  }'
```

#### Test 3.4: Arbitrage Discovery (Chinese)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.33" \
  -d '{
    "content": "寻找套利机会",
    "language": "zh"
  }'
```

#### Test 3.5: Flash Loans
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.40" \
  -d '{
    "content": "Show me flash loan protocols",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "flash loan", "protocol", "fee", "maximum", "DeFi", "lending"

#### Test 3.6: MEV Protection
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.41" \
  -d '{
    "content": "What is MEV protection?",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "MEV", "protection", "Flashbots", "sandwich", "private", "DeFi", "security"

#### Test 3.7: Auto-Executor
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.42" \
  -d '{
    "content": "Tell me about auto-executor",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "auto", "executor", "DCA", "limit order", "stop loss", "strategy", "trading", "ULTRA", "automated"

---

### 4. Agent Squad Features

#### Test 4.1: Specialist Tasks (English)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.50" \
  -d '{
    "content": "What specialist agents do you have?",
    "language": "en"
  }'
```

**Expected:**
- Intent: `specialist_task` or `general_conversation`
- Content mentions: "agent", "specialist", "research", "security", "gas", "tax", "portfolio", "DeFi", "AI", "assistant"
- May require registration: `registration_required: true`

#### Test 4.2: Specialist Tasks (Spanish)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.51" \
  -d '{
    "content": "¿Qué agentes especialistas tienes?",
    "language": "es"
  }'
```

#### Test 4.3: Specialist Tasks (Portuguese)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.52" \
  -d '{
    "content": "Quais agentes especialistas você tem?",
    "language": "pt"
  }'
```

#### Test 4.4: Specialist Tasks (Chinese)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.53" \
  -d '{
    "content": "你有什么专业代理？",
    "language": "zh"
  }'
```

#### Test 4.5: Complex Workflows
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.60" \
  -d '{
    "content": "How does multi-agent workflow work?",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "workflow", "supervisor", "multi-agent", "coordinate", "portfolio", "rebalancing", "DeFi", "AI", "assistant"

---

### 5. DeFi Operations

#### Test 5.1: Swap Quote
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.70" \
  -d '{
    "content": "I want to swap 100 USDC to ETH",
    "language": "en"
  }'
```

**Expected:**
- Intent: `swap` or `general_conversation`
- Content mentions: "swap", "USDC", "ETH", "rate", "quote", "exchange"
- May include `enrichment` with `from_token`, `to_token`, `rate`, `swap_demo`

#### Test 5.2: Lending / Yield Opportunities
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.71" \
  -d '{
    "content": "Where can I earn yield?",
    "language": "en"
  }'
```

**Expected:**
- Intent: `lending` or `general_conversation`
- Content mentions: "earn", "yield", "lending", "deposit", "rate", "APY", "Morpho", "Aave"
- Handler: `lending_handler` (if lending intent detected)

#### Test 5.3: Protocol Search
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.72" \
  -d '{
    "content": "Find lending protocols on Ethereum",
    "language": "en"
  }'
```

**Expected:**
- Content mentions: "protocol", "Aave", "Compound", "Morpho", "lending"
- May include `enrichment` with `graphrag`, `protocols`, `demo_protocols`

---

### 6. Restricted Actions

#### Test 6.1: Balance Check (Requires Registration)
```bash
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.80" \
  -d '{
    "content": "Show my balance",
    "language": "en"
  }'
```

**Expected:**
- Intent: `balance` or `general_conversation`
- `registration_required: { "required": true, "signup_url": "..." }`
- Content mentions: "sign up", "register", "registration", "wallet", "balance"

---

### 7. History & Status Endpoints

#### Test 7.1: Get History (Empty)
```bash
curl -X GET "http://localhost:8080/api/v1/guest/chat/history" \
  -H "X-Forwarded-For: 127.0.0.90"
```

**Expected:**
- Status: `200 OK`
- Contains: `messages` (empty array) or `is_active: false`

#### Test 7.2: Get History (With Messages)
```bash
# First, send some messages
curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.91" \
  -d '{"content": "Hello", "language": "en"}'

curl -X POST "http://localhost:8080/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.91" \
  -d '{"content": "What can you do?", "language": "en"}'

# Then get history
curl -X GET "http://localhost:8080/api/v1/guest/chat/history" \
  -H "X-Forwarded-For: 127.0.0.91"
```

**Expected:**
- Status: `200 OK`
- Contains: `messages` array with at least 2 messages
- Each message has: `id`, `role`, `content`, `created_at`
- Roles: `user` or `assistant`

#### Test 7.3: Get Status
```bash
curl -X GET "http://localhost:8080/api/v1/guest/chat/status" \
  -H "X-Forwarded-For: 127.0.0.92"
```

**Expected:**
- Status: `200 OK`
- Contains: `is_active`, `messages_remaining`, `messages_this_hour`, `messages_today`
- `messages_remaining` should be >= 0 (rate limit: 5000/hour, 10000/day for testing)

---

## Response Structure

### Successful Chat Response
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {
    "role": "user",
    "content": "Your message"
  },
  "agent_message": {
    "role": "assistant",
    "content": "AI response",
    "sources": [] // Optional
  },
  "routing": {
    "intent": "detected_intent",
    "confidence": 0.95,
    "handler": "handler_name",
    "language": "en"
  },
  "enrichment": {}, // Optional
  "registration_required": { // Optional
    "required": true,
    "signup_url": "..."
  },
  "guest_info": {
    "messages_remaining": 4999,
    "messages_this_hour": 1,
    "messages_today": 1
  }
}
```

---

## Testing Checklist

### Basic Functionality
- [ ] Shortcuts endpoint returns 7 shortcuts
- [ ] General greeting works
- [ ] Multi-language support (en, es, pt, zh)
- [ ] Multi-turn conversation maintains context

### Hunter AI Features
- [ ] Sentiment analysis (all languages)
- [ ] Price prediction
- [ ] Risk signals
- [ ] Trading signals
- [ ] Pattern recognition
- [ ] Portfolio optimization

### ULTRA Features
- [ ] Arbitrage discovery (all languages)
- [ ] Flash loans
- [ ] MEV protection
- [ ] Auto-executor

### Agent Squad Features
- [ ] Specialist tasks (all languages)
- [ ] Complex workflows

### DeFi Operations
- [ ] Swap quotes
- [ ] Lending/yield opportunities
- [ ] Protocol search

### Restricted Actions
- [ ] Balance check prompts registration

### History & Status
- [ ] Empty history returns correctly
- [ ] History with messages returns correctly
- [ ] Status endpoint shows rate limit info

---

## Notes

1. **Rate Limits:** Currently set to 5000 messages/hour and 10000 messages/day for testing
2. **Session Tracking:** Use unique `X-Forwarded-For` IP addresses for different sessions
3. **Language Support:** All features support 4 languages: English, Spanish, Portuguese, Chinese
4. **Registration:** Some features (arbitrage, agent squad, balance) require user registration
5. **Real Data:** All responses use real APIs and services, not mocked data

---

## Troubleshooting

### Issue: 405 Method Not Allowed
- **Solution:** Guest chat endpoint is `POST`, not `GET`

### Issue: Empty or Generic Responses
- **Solution:** Check that intent detection is working. Some queries may default to `general_conversation`

### Issue: Rate Limit Exceeded
- **Solution:** Use a different `X-Forwarded-For` IP address

### Issue: Database Errors
- **Solution:** Ensure migrations are applied: `alembic upgrade head`

---

## Quick Test Script

Save this as `test_guest_chat.sh`:

```bash
#!/bin/bash
BASE_URL="http://localhost:8080"
API_BASE="${BASE_URL}/api/v1"

echo "Testing Shortcuts..."
curl -s "${API_BASE}/chat/shortcuts?lang=en" | jq '.language, .shortcuts | length'

echo -e "\nTesting General Chat..."
curl -s -X POST "${API_BASE}/guest/chat" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 127.0.0.999" \
  -d '{"content": "Hello", "language": "en"}' | jq '.routing.intent, .agent_message.content[:100]'

echo -e "\nTesting History..."
curl -s -X GET "${API_BASE}/guest/chat/history" \
  -H "X-Forwarded-For: 127.0.0.999" | jq '.total_messages'

echo -e "\nTesting Status..."
curl -s -X GET "${API_BASE}/guest/chat/status" \
  -H "X-Forwarded-For: 127.0.0.999" | jq '.messages_remaining'
```

Make it executable: `chmod +x test_guest_chat.sh`  
Run: `./test_guest_chat.sh`

---

**Last Updated:** 2025-01-07  
**Version:** 1.0

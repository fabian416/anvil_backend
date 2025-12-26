# Anvil Unified Chat API - Quick Reference

Single endpoint for all interactions: `POST /api/v1/user/chat/conversations/{id}/messages`

## 📋 All 16 Intent Types

| Category | Intent | Example Query | Key Enrichment Fields | Handler |
|----------|--------|---------------|----------------------|---------|
| **GraphRAG** | `protocol_search` | "Show me DeFi lending protocols" | `protocols[]`, `search_context` | `graphrag_search` |
| **GraphRAG** | `risk_assessment` | "Is Aave safe to use?" | `risk_analysis`, `overall_risk_score` | `graphrag_search` |
| **GraphRAG** | `similar_protocols` | "What's similar to Uniswap?" | `similar_protocols[]`, `similarity_scores` | `graphrag_search` |
| **Hunter AI** | `hunter_sentiment` | "What's ETH sentiment on Twitter?" | `token_symbol`, `sources`, `sentiment_score` | `hunter_ai` |
| **Hunter AI** | `hunter_price_prediction` | "Predict BTC price for 7 days" | `token_symbol`, `time_horizon`, `predictions[]` | `hunter_ai` |
| **Hunter AI** | `hunter_risk_signals` | "Show risk signals for ETH" | `token_symbol`, `risk_signals[]` | `hunter_ai` |
| **Hunter AI** | `hunter_trading_signals` | "Should I buy SOL now?" | `token_symbol`, `signals[]`, `recommendation` | `hunter_ai` |
| **Hunter AI** | `hunter_patterns` | "Chart patterns for BTC?" | `token_symbol`, `patterns[]` | `hunter_ai` |
| **Hunter AI** | `hunter_portfolio` | "Optimize my BTC/ETH/SOL portfolio" | `tokens[]`, `risk_tolerance`, `allocation` | `hunter_ai` |
| **ULTRA** | `ultra_arbitrage` | "Find arbitrage with $10k" | `capital`, `arb_type`, `opportunities[]` | `ultra` |
| **ULTRA** | `ultra_flash_loans` | "Best flash loan for 100k USDC" | `token_symbol`, `amount`, `protocol` | `ultra` |
| **ULTRA** | `ultra_mev_protection` | "Execute ARB-001 with Flashbots" | `opportunity_id`, `protection_method` | `ultra` |
| **ULTRA** | `ultra_auto_executor` | "Start trading bot" | `action`, `status` | `ultra` |
| **Agent Squad** | `specialist_task` | "Analyze ETH/USDC liquidity on Uniswap" | `tools_used[]`, `analysis_type` | `agent_orchestrator` |
| **Agent Squad** | `complex_workflow` | "Create DeFi strategy for $50k" | `workflow_id`, `agents_involved[]` | `agent_orchestrator` |
| **Chat** | `general_conversation` | "Hello! What can you help with?" | `conversation_context` | `general_chat` |

## 🔑 Authentication

```bash
# Login
curl -X POST http://localhost:8080/api/v1/account/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

## 📨 Create Conversation

```bash
curl -X POST http://localhost:8080/api/v1/user/chat/conversations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Conversation"}'

# Response
{
  "id": "conv_123abc",
  "title": "My Conversation",
  "created_at": "2025-12-26T10:00:00Z"
}
```

## 💬 Send Message

```bash
curl -X POST http://localhost:8080/api/v1/user/chat/conversations/CONV_ID/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Show me DeFi lending protocols"}'
```

## 📊 Response Format

All responses include these sections:

```typescript
{
  user_message: {
    id: string
    content: string
    role: "user"
    timestamp: string
  }
  agent_message: {
    id: string
    content: string
    role: "assistant"
    agent_type: string
    timestamp: string
  }
  routing: {
    intent: string           // One of 16 intent types
    confidence: number       // 0.0 to 1.0
    handler: string          // Which handler processed it
    reasoning: string        // Why this intent was chosen
    total_latency_ms: number
  }
  enrichment: {
    // Intent-specific structured data
    // See table above for common fields per intent
  }
}
```

## 🎯 Intent Detection Keywords

### GraphRAG
- **Protocol Search**: "find", "show", "list", "search", "protocols", "DeFi"
- **Risk Assessment**: "risk", "safe", "secure", "audit", "vulnerabilities"
- **Similar Protocols**: "similar", "alternative", "like", "comparable"

### Hunter AI
- **Sentiment**: "sentiment", "opinion", "twitter", "reddit", "social"
- **Price Prediction**: "predict", "forecast", "price target", "future price"
- **Risk Signals**: "risk signals", "warnings", "red flags"
- **Trading Signals**: "buy", "sell", "trading signals", "should I"
- **Patterns**: "chart patterns", "technical patterns", "formations"
- **Portfolio**: "optimize", "portfolio", "allocation", "rebalance"

### ULTRA
- **Arbitrage**: "arbitrage", "arb opportunities", "price differences"
- **Flash Loans**: "flash loan", "borrow", "loan protocol"
- **MEV Protection**: "MEV", "Flashbots", "private transaction"
- **Auto Executor**: "start bot", "stop bot", "bot status", "auto execute"

### Agent Squad
- **Specialist Task**: "analyze", "calculate", "research", "investigate"
- **Complex Workflow**: "strategy", "plan", "complete solution", "workflow"
- **General**: Greetings, questions, casual conversation

## 🔍 Example Queries by Use Case

### DeFi Research
```
"Show me high-yield staking protocols on Ethereum"
"Compare Aave vs Compound lending rates"
"What are the risks of using Curve Finance?"
```

### Market Intelligence
```
"What's the sentiment for ETH this week?"
"Predict SOL price for next 30 days"
"Show me trading signals for BTC"
```

### Advanced Trading
```
"Find arbitrage opportunities with $5,000"
"Best flash loan protocol for leveraged trading"
"Execute my arbitrage strategy with MEV protection"
```

### Portfolio Management
```
"Optimize my portfolio: 40% BTC, 30% ETH, 30% SOL"
"Analyze risk signals for my current holdings"
"Create a balanced DeFi investment strategy"
```

## ⚙️ Configuration

### Base URLs
- **Development**: `http://localhost:8080/api/v1`
- **Production**: `https://api.anvil.com/api/v1`

### Rate Limits
- **Authenticated**: 100 requests/minute
- **Anonymous**: 10 requests/minute

### Intent Detection
- **Primary**: LLM-powered (gpt-4o-mini or gemini-2.0-flash-exp)
- **Fallback**: Keyword matching
- **Confidence Threshold**: 0.7 (routes to general_conversation if below)

## 📚 Additional Resources

### Full Documentation
- **Complete Examples**: `docs/UNIFIED_CHAT_EXAMPLES.md`
- **Postman Collection**: `docs/api/examples/unified-chat-postman-collection.json`
- **Python SDK**: `docs/api/examples/python_sdk_examples.py`
- **TypeScript SDK**: `docs/api/examples/typescript_sdk_examples.ts`
- **cURL Scripts**: `docs/api/examples/curl_test_scripts.sh`

### Integration Guides
```python
# Python
from anvil_chat import AnvilChatClient
client = AnvilChatClient(base_url="http://localhost:8080/api/v1")
client.login(email="user@example.com", password="password")
client.create_conversation()
response = client.send_message("Show me DeFi protocols")
```

```typescript
// TypeScript
import { AnvilChatClient } from './anvil_chat';
const client = new AnvilChatClient({
  baseUrl: 'http://localhost:8080/api/v1',
  email: 'user@example.com',
  password: 'password'
});
await client.login();
await client.createConversation();
const response = await client.sendMessage('Show me DeFi protocols');
```

```bash
# Bash/cURL
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/account/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

CONV_ID=$(curl -s -X POST http://localhost:8080/api/v1/user/chat/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}' \
  | jq -r '.id')

curl -X POST http://localhost:8080/api/v1/user/chat/conversations/$CONV_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Show me DeFi protocols"}'
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check Bearer token is valid and not expired |
| 404 Conversation Not Found | Verify conversation_id exists and belongs to user |
| 422 Validation Error | Check request body has required `content` field |
| 429 Rate Limited | Reduce request frequency, check `Retry-After` header |
| Low confidence (<0.7) | Query routes to general_conversation, try more specific keywords |

## 🎓 Best Practices

1. **Authentication**: Always include `Authorization: Bearer TOKEN` header
2. **Conversation Management**: Create one conversation per logical session
3. **Error Handling**: Check `routing.confidence` - values <0.7 may not route correctly
4. **Multi-turn Context**: System maintains conversation history automatically
5. **Intent Specificity**: Use keywords from the Intent Detection table for accurate routing
6. **Response Parsing**: Always check `routing.intent` to understand what data is in `enrichment`
7. **Rate Limiting**: Implement exponential backoff on 429 responses

## 📞 Support

- **Issues**: https://github.com/anvil/api/issues
- **Docs**: https://docs.anvil.com
- **Status**: https://status.anvil.com

---

**Version**: 1.0.0 | **Last Updated**: 2025-12-26

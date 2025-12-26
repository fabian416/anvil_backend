# Unified Chat Routing - API Examples

**Purpose**: Comprehensive examples for using the unified chat routing system
**Audience**: Frontend developers, API integrators

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Protocol Search Examples](#protocol-search-examples)
3. [Risk Assessment Examples](#risk-assessment-examples)
4. [Similar Protocols Examples](#similar-protocols-examples)
5. [Specialist Task Examples](#specialist-task-examples)
6. [Complex Workflow Examples](#complex-workflow-examples)
7. [General Conversation Examples](#general-conversation-examples)
8. [Using Routing Metadata](#using-routing-metadata)
9. [Error Handling](#error-handling)
10. [Frontend Integration](#frontend-integration)

---

## Basic Usage

### Simple Request

The unified endpoint automatically detects intent and routes appropriately:

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Show me the safest DeFi protocols"
}
```

**Response**:
```json
{
  "user_message": {
    "id": "user-msg-uuid",
    "conversation_id": "conv-uuid",
    "role": "user",
    "content": "Show me the safest DeFi protocols",
    "created_at": "2025-12-26T10:00:00Z"
  },
  "agent_message": {
    "id": "agent-msg-uuid",
    "conversation_id": "conv-uuid",
    "role": "assistant",
    "content": "I found 5 highly secure DeFi protocols:\n\n1. **Aave V3** (Risk: LOW)...",
    "agent_type": "graphrag_search",
    "created_at": "2025-12-26T10:00:01Z"
  },
  "routing": {
    "intent": "protocol_search",
    "confidence": 0.89,
    "handler": "graphrag_search",
    "agent_used": null,
    "reasoning": "User query requests protocol discovery with safety focus, routed to GraphRAG search",
    "total_latency_ms": 420
  },
  "enrichment": {
    "protocols": [
      {
        "protocol_name": "Aave V3",
        "risk_level": "LOW",
        "tvl": 8500000000
      }
    ],
    "search_context": "Filtered for protocols with low risk scores",
    "recommendations": [
      "Consider diversifying across multiple protocols",
      "Monitor risk scores regularly"
    ]
  }
}
```

---

## Protocol Search Examples

### Example 1: Find High-Yield Protocols

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Find me high-yield staking protocols on Arbitrum"
}
```

**Routing**:
- Intent: `protocol_search`
- Handler: `graphrag_search`
- Confidence: 0.92

**Response excerpt**:
```json
{
  "agent_message": {
    "content": "Top high-yield staking protocols on Arbitrum:\n\n1. **GMX V2** - 15.2% APY...",
    "agent_type": "graphrag_search"
  },
  "enrichment": {
    "protocols": [
      {"protocol_name": "GMX V2", "apy": 15.2, "chain": "Arbitrum"},
      {"protocol_name": "Radiant Capital", "apy": 12.8, "chain": "Arbitrum"}
    ]
  }
}
```

### Example 2: Category-Specific Search

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Show me lending protocols with TVL > $1B"
}
```

**Routing**:
- Intent: `protocol_search`
- Handler: `graphrag_search`
- Filters extracted: `category=Lending, min_tvl=1000000000`

---

## Risk Assessment Examples

### Example 1: Protocol Safety Check

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Is Curve Finance safe to use?"
}
```

**Routing**:
- Intent: `risk_assessment`
- Handler: `graphrag_risk`
- Confidence: 0.88

**Response excerpt**:
```json
{
  "agent_message": {
    "content": "Curve Finance Risk Analysis:\n\nRisk Score: 2.3/10 (LOW)\n\nKey Factors:\n✅ 12+ security audits...",
    "agent_type": "graphrag_risk"
  },
  "routing": {
    "intent": "risk_assessment",
    "handler": "graphrag_risk",
    "reasoning": "User asking about protocol safety, routed to risk analysis"
  },
  "enrichment": {
    "risk_analysis": {
      "protocol_name": "Curve Finance",
      "risk_score": 2.3,
      "risk_level": "LOW",
      "contributing_factors": [
        {
          "factor": "Multiple audits",
          "impact": -1.5,
          "is_critical": false
        }
      ],
      "should_warn": false
    },
    "alternatives_count": 3
  }
}
```

### Example 2: Operation-Specific Risk

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "What's the risk of supplying $50k to Aave?"
}
```

**Routing**:
- Intent: `risk_assessment`
- Entities extracted: `protocol=Aave, operation=supply, amount=50000`

---

## Similar Protocols Examples

### Example 1: Find Alternatives

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "What's similar to Uniswap?"
}
```

**Routing**:
- Intent: `similar_protocols`
- Handler: `graphrag_similar`
- Confidence: 0.90

**Response excerpt**:
```json
{
  "agent_message": {
    "content": "Protocols similar to Uniswap:\n\n1. **SushiSwap** (Similarity: 0.92)...",
    "agent_type": "graphrag_similar"
  },
  "enrichment": {
    "base_protocol": {
      "protocol_name": "Uniswap V3",
      "category": "DEX"
    },
    "similar_protocols": [
      {
        "protocol_name": "SushiSwap",
        "similarity_score": 0.92,
        "why_similar": "DEX protocol; Ethereum & multi-chain; AMM model"
      }
    ]
  }
}
```

### Example 2: Migration Planning

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "I want to move from Compound, what are safer alternatives?"
}
```

**Routing**:
- Intent: `similar_protocols`
- Filters: risk preference detected (safer = lower risk)

---

## Specialist Task Examples

### Example 1: Market Analysis (Hunter AI)

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Analyze ETH/USDC market depth on Uniswap"
}
```

**Routing**:
- Intent: `specialist_task`
- Handler: `agent_squad`
- Agent selected: `hunter_ai`
- Confidence: 0.85

**Response excerpt**:
```json
{
  "agent_message": {
    "content": "📊 ETH/USDC Market Depth Analysis:\n\nLiquidity: $450M...",
    "agent_type": "hunter_ai"
  },
  "routing": {
    "intent": "specialist_task",
    "handler": "agent_squad",
    "agent_used": "hunter_ai",
    "reasoning": "Market analysis query routed to Hunter AI specialist"
  },
  "enrichment": {
    "tools_used": ["uniswap_v3_api", "market_depth_analyzer"],
    "tokens_consumed": 650,
    "latency_ms": 2100
  }
}
```

### Example 2: Gas Optimization

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "How can I optimize gas for this Uniswap swap?"
}
```

**Routing**:
- Intent: `specialist_task`
- Agent selected: `gas_optimizer`

### Example 3: Security Audit

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Review this smart contract for vulnerabilities: 0x..."
}
```

**Routing**:
- Intent: `specialist_task`
- Agent selected: `security_auditor`

---

## Complex Workflow Examples

### Example 1: Portfolio Strategy

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Create an optimized DeFi portfolio strategy for $100k with moderate risk"
}
```

**Routing**:
- Intent: `complex_workflow`
- Handler: `supervisor`
- Confidence: 0.87

**Response excerpt**:
```json
{
  "agent_message": {
    "content": "I've coordinated 5 agents to create your portfolio strategy:\n\n**Allocation:**...",
    "agent_type": "supervisor"
  },
  "routing": {
    "intent": "complex_workflow",
    "handler": "supervisor",
    "reasoning": "Complex multi-agent task requiring portfolio, risk, and yield analysis"
  },
  "enrichment": {
    "workflow_id": "workflow-uuid",
    "workflow_status": "completed",
    "tasks_count": 5,
    "agents_involved": [
      "portfolio",
      "risk_analyzer",
      "defi_yield",
      "research",
      "tax_optimizer"
    ]
  }
}
```

### Example 2: Multi-Step Analysis

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Find safe protocols, analyze their risks, and suggest optimal allocation"
}
```

**Routing**:
- Intent: `complex_workflow`
- Tasks: Search → Risk Analysis → Portfolio Optimization
- Agents coordinated by Supervisor

---

## General Conversation Examples

### Example 1: Educational Q&A

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "What is impermanent loss?"
}
```

**Routing**:
- Intent: `general_conversation`
- Handler: `regular_chat`
- Confidence: 0.95

**Response excerpt**:
```json
{
  "agent_message": {
    "content": "Impermanent loss (IL) is the difference between...",
    "agent_type": "chat"
  },
  "routing": {
    "intent": "general_conversation",
    "handler": "regular_chat",
    "reasoning": "Educational question without specific action required"
  }
}
```

### Example 2: Greeting

```bash
POST /api/v1/user/chat/conversations/{conversation_id}/messages

{
  "content": "Hello! How are you?"
}
```

**Routing**:
- Intent: `general_conversation`
- Handler: `regular_chat`

---

## Using Routing Metadata

### Check Which Handler Was Used

```javascript
// JavaScript/TypeScript Example
async function sendMessage(conversationId, content) {
  const response = await fetch(
    `/api/v1/user/chat/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content })
    }
  );

  const data = await response.json();

  // Access routing metadata
  console.log('Intent detected:', data.routing.intent);
  console.log('Handler used:', data.routing.handler);
  console.log('Confidence:', data.routing.confidence);
  console.log('Reasoning:', data.routing.reasoning);

  // Handle based on handler type
  if (data.routing.handler === 'graphrag_search') {
    // Show protocol results with special UI
    displayProtocols(data.enrichment.protocols);
  } else if (data.routing.handler === 'agent_squad') {
    // Show which specialist agent was used
    console.log('Agent used:', data.routing.agent_used);
  }

  return data;
}
```

### Display Routing Information to Users

```javascript
// Show routing badge in UI
function getRoutingBadge(routing) {
  const badges = {
    'graphrag_search': '🔍 Protocol Search',
    'graphrag_risk': '⚠️ Risk Analysis',
    'graphrag_similar': '🔄 Similar Protocols',
    'agent_squad': `🤖 ${routing.agent_used || 'Specialist'}`,
    'supervisor': '🎯 Multi-Agent Workflow',
    'regular_chat': '💬 Chat'
  };

  return badges[routing.handler] || '💬 Chat';
}

// Show confidence indicator
function getConfidenceBadge(confidence) {
  if (confidence >= 0.9) return '🟢 High';
  if (confidence >= 0.7) return '🟡 Medium';
  return '🔴 Low';
}
```

---

## Error Handling

### Low Confidence Fallback

When intent detection confidence is low, the system falls back to regular chat:

```json
{
  "routing": {
    "intent": "general_conversation",
    "confidence": 0.65,
    "handler": "regular_chat",
    "reasoning": "Low confidence in intent classification, using general chat fallback"
  }
}
```

### Handler Failure Fallback

If a handler fails, system falls back gracefully:

```json
{
  "routing": {
    "intent": "protocol_search",
    "confidence": 0.91,
    "handler": "regular_chat",
    "reasoning": "GraphRAG search failed (timeout), fell back to regular chat"
  }
}
```

### Invalid Conversation ID

```bash
POST /api/v1/user/chat/conversations/invalid-uuid/messages

Response: 404 Not Found
{
  "detail": "Conversation not found"
}
```

### Rate Limiting

```bash
Response: 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}

Headers:
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000030
```

---

## Frontend Integration

### React Hook Example

```typescript
// useUnifiedChat.ts
import { useState } from 'react';

interface UnifiedChatResponse {
  user_message: Message;
  agent_message: Message;
  routing: RoutingMetadata;
  enrichment?: EnrichmentData;
}

export function useUnifiedChat(conversationId: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function sendMessage(content: string): Promise<UnifiedChatResponse> {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/user/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }

  return { sendMessage, loading, error };
}
```

### Vue Composable Example

```typescript
// useUnifiedChat.ts
import { ref } from 'vue';

export function useUnifiedChat(conversationId: string) {
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function sendMessage(content: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(
        `/api/v1/user/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return { sendMessage, loading, error };
}
```

### Display Enrichment Data

```typescript
// EnrichmentDisplay.tsx
interface Props {
  routing: RoutingMetadata;
  enrichment?: EnrichmentData;
}

export function EnrichmentDisplay({ routing, enrichment }: Props) {
  if (!enrichment) return null;

  // GraphRAG Search - Show protocols
  if (routing.handler === 'graphrag_search' && enrichment.protocols) {
    return (
      <ProtocolList protocols={enrichment.protocols} />
    );
  }

  // GraphRAG Risk - Show risk analysis
  if (routing.handler === 'graphrag_risk' && enrichment.risk_analysis) {
    return (
      <RiskAnalysis analysis={enrichment.risk_analysis} />
    );
  }

  // Agent Squad - Show tools used
  if (routing.handler === 'agent_squad' && enrichment.tools_used) {
    return (
      <ToolsBadges tools={enrichment.tools_used} />
    );
  }

  return null;
}
```

---

## Best Practices

### 1. Always Handle Routing Metadata

```typescript
// ✅ Good - Use routing info to enhance UX
function handleResponse(response: UnifiedChatResponse) {
  // Show routing badge
  showRoutingBadge(response.routing);

  // Display enrichment data if available
  if (response.enrichment) {
    renderEnrichment(response.enrichment, response.routing.handler);
  }

  // Log for analytics
  trackIntentClassification(response.routing);
}

// ❌ Bad - Ignore routing metadata
function handleResponse(response: UnifiedChatResponse) {
  // Just show message content, miss valuable context
  return response.agent_message.content;
}
```

### 2. Provide Feedback on Low Confidence

```typescript
if (response.routing.confidence < 0.7) {
  showWarning('The system had low confidence in understanding your request. Results may not be optimal.');
}
```

### 3. Track Handler Usage for Analytics

```typescript
// Track which handlers are used most
analytics.track('chat_message_sent', {
  intent: response.routing.intent,
  handler: response.routing.handler,
  confidence: response.routing.confidence,
  latency_ms: response.routing.total_latency_ms
});
```

### 4. Implement Retry Logic

```typescript
async function sendMessageWithRetry(content: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await sendMessage(content);
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await sleep(1000 * (i + 1)); // Exponential backoff
    }
  }
}
```

---

## Migration from Direct Endpoints

### Before (Multiple Endpoints)

```typescript
// Old approach - had to choose endpoint
async function sendChatMessage(type: string, content: string) {
  let endpoint;

  if (type === 'search') {
    endpoint = '/api/v1/user/chat/search-protocols';
  } else if (type === 'risk') {
    endpoint = '/api/v1/user/chat/analyze-risk';
  } else if (type === 'agent') {
    endpoint = '/api/v1/user/chat/agent-squad/messages';
  } else {
    endpoint = `/api/v1/user/chat/conversations/${conversationId}/messages`;
  }

  return fetch(endpoint, { ... });
}
```

### After (Unified Routing)

```typescript
// New approach - one endpoint handles everything
async function sendChatMessage(content: string) {
  return fetch(
    `/api/v1/user/chat/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      body: JSON.stringify({ content })
    }
  );
  // System automatically routes to best handler!
}
```

---

## Hunter AI Examples (Phase 8.1)

### Example 1: Sentiment Analysis

Query for social sentiment across multiple platforms:

```typescript
const response = await sendMessage("What's the ETH sentiment on Twitter and Reddit?");

// Response routing
{
  "routing": {
    "intent": "hunter_sentiment",
    "confidence": 0.92,
    "handler": "hunter_sentiment",
    "agent_used": "hunter_ai",
    "reasoning": "Message contains sentiment analysis keywords"
  },
  "enrichment": {
    "hunter_tool": "sentiment_analysis",
    "token_symbol": "ETH",
    "time_horizon": "24h",
    "sources": ["twitter", "reddit"]
  }
}
```

### Example 2: Price Prediction

Get ML-powered price forecasts:

```typescript
const response = await sendMessage("Predict BTC price for the next 7 days");

// Response routing
{
  "routing": {
    "intent": "hunter_price_prediction",
    "confidence": 0.90,
    "handler": "hunter_price_prediction",
    "agent_used": "hunter_ai"
  },
  "enrichment": {
    "hunter_tool": "price_prediction",
    "token_symbol": "BTC",
    "time_horizon": "7d"
  }
}
```

### Example 3: Risk Signals

Monitor market risk indicators:

```typescript
const response = await sendMessage("Show me risk signals for SOL");

// Response routing
{
  "routing": {
    "intent": "hunter_risk_signals",
    "confidence": 0.88,
    "handler": "hunter_risk_signals",
    "agent_used": "hunter_ai"
  },
  "enrichment": {
    "hunter_tool": "risk_signals",
    "token_symbol": "SOL"
  }
}
```

### Example 4: Trading Signals

Get buy/sell recommendations:

```typescript
const response = await sendMessage("Should I buy ETH now? Show trading signals");

// Response routing
{
  "routing": {
    "intent": "hunter_trading_signals",
    "confidence": 0.91,
    "handler": "hunter_trading_signals",
    "agent_used": "hunter_ai"
  },
  "enrichment": {
    "hunter_tool": "trading_signals",
    "token_symbol": "ETH"
  }
}
```

### Example 5: Chart Patterns

Detect technical analysis patterns:

```typescript
const response = await sendMessage("Analyze chart patterns for BTC");

// Response routing
{
  "routing": {
    "intent": "hunter_patterns",
    "confidence": 0.89,
    "handler": "hunter_patterns",
    "agent_used": "hunter_ai"
  },
  "enrichment": {
    "hunter_tool": "pattern_detection",
    "token_symbol": "BTC"
  }
}
```

### Example 6: Portfolio Optimization

Optimize asset allocation with Modern Portfolio Theory:

```typescript
const response = await sendMessage("Optimize my portfolio for BTC, ETH, and SOL with moderate risk");

// Response routing
{
  "routing": {
    "intent": "hunter_portfolio",
    "confidence": 0.87,
    "handler": "hunter_portfolio",
    "agent_used": "hunter_ai"
  },
  "enrichment": {
    "hunter_tool": "portfolio_optimization",
    "tokens": ["BTC", "ETH", "SOL"],
    "risk_tolerance": 0.5
  }
}
```

### Hunter AI React Hook Example

```typescript
// useHunterAI.ts
import { useState } from 'react';

interface HunterAIResponse {
  user_message: any;
  agent_message: any;
  routing: {
    intent: string;
    confidence: number;
    handler: string;
    agent_used: string;
  };
  enrichment: {
    hunter_tool?: string;
    token_symbol?: string;
    tokens?: string[];
    time_horizon?: string;
    sources?: string[];
    risk_tolerance?: number;
  };
}

export function useHunterAI(conversationId: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeSentiment = async (token: string, sources?: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const query = sources
        ? `${token} sentiment on ${sources.join(' and ')}`
        : `${token} sentiment`;

      const response = await fetch(
        `/api/v1/user/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content: query })
        }
      );

      const data: HunterAIResponse = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const predictPrice = async (token: string, timeHorizon: '24h' | '7d' | '30d' = '7d') => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/user/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: `Predict ${token} price for the next ${timeHorizon}`
          })
        }
      );

      const data: HunterAIResponse = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const optimizePortfolio = async (
    tokens: string[],
    riskTolerance: 'conservative' | 'moderate' | 'aggressive' = 'moderate'
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/user/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: `Optimize portfolio for ${tokens.join(', ')} with ${riskTolerance} risk`
          })
        }
      );

      const data: HunterAIResponse = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    analyzeSentiment,
    predictPrice,
    optimizePortfolio,
    loading,
    error
  };
}
```

### Usage Example

```typescript
function TradingDashboard() {
  const { conversationId } = useConversation();
  const {
    analyzeSentiment,
    predictPrice,
    optimizePortfolio,
    loading
  } = useHunterAI(conversationId);

  const handleSentimentCheck = async () => {
    const result = await analyzeSentiment('ETH', ['twitter', 'reddit']);
    console.log('Sentiment:', result.agent_message.content);
    console.log('Sources:', result.enrichment.sources);
  };

  const handlePriceForecast = async () => {
    const result = await predictPrice('BTC', '7d');
    console.log('Forecast:', result.agent_message.content);
    console.log('Time horizon:', result.enrichment.time_horizon);
  };

  const handlePortfolioOptimization = async () => {
    const result = await optimizePortfolio(['BTC', 'ETH', 'SOL'], 'moderate');
    console.log('Optimized allocation:', result.agent_message.content);
    console.log('Risk tolerance:', result.enrichment.risk_tolerance);
  };

  return (
    <div>
      <button onClick={handleSentimentCheck} disabled={loading}>
        Check ETH Sentiment
      </button>
      <button onClick={handlePriceForecast} disabled={loading}>
        Predict BTC Price
      </button>
      <button onClick={handlePortfolioOptimization} disabled={loading}>
        Optimize Portfolio
      </button>
    </div>
  );
}
```

---

## Related Documentation

- [Chat Endpoints Explained](../../CHAT_ENDPOINTS_EXPLAINED.md)
- [Unified Routing System](../../CHAT_ENDPOINTS_EXPLAINED.md#0-unified-routing-system-new)
- [API Reference](../reference/README.md)
- [Authentication Guide](../authentication.md)

---

**Last Updated**: December 26, 2025
**Status**: Production Ready

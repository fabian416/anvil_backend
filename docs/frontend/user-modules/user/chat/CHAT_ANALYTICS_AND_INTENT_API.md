# Chat Analytics & Intent Detection API

**Version:** 1.0
**Last Updated:** December 17, 2025
**Total Endpoints:** 11 (3 Intent + 8 Analytics)

---

## Overview

This document covers two major chat enhancement features:
1. **Intent Detection** - Real-time message understanding and agent routing
2. **Personal Analytics Dashboard** - User chat usage insights and metrics

---

## API Base URL

```
Production: https://api.anvil.defi/api/v1/chat
Staging:    https://staging-api.anvil.defi/api/v1/chat
Local:      http://localhost:8000/api/v1/chat
```

---

## Authentication

All endpoints require authentication via JWT token:

```
Authorization: Bearer <jwt_token>
```

---

# 🎯 Intent Detection Endpoints

## 1. Detect Intent

Analyzes user message to detect intent, extract entities, and suggest appropriate agents.

**Endpoint:** `POST /api/v1/chat/intent/detect`

### Request Body

```typescript
interface DetectIntentRequest {
  message: string;                    // User message to analyze
  conversation_id?: string;           // Optional conversation context
  include_agent_suggestions?: boolean; // Include agent recommendations (default: true)
}
```

### Response

```typescript
interface DetectIntentResponse {
  intent: {
    type: string;          // e.g., "defi_query", "portfolio_analysis", "risk_assessment"
    confidence: number;    // 0.0-1.0
    entities: {
      protocols?: string[];      // Detected DeFi protocols
      tokens?: string[];         // Detected token symbols
      chains?: string[];         // Detected blockchain networks
      actions?: string[];        // Detected actions (swap, stake, etc.)
      amounts?: number[];        // Detected numeric values
      addresses?: string[];      // Detected wallet/contract addresses
    };
  };
  suggested_agent?: {
    agent_type: string;    // e.g., "DEFI_YIELD", "RISK_ANALYZER"
    agent_name: string;
    reasoning: string;     // Why this agent was suggested
    confidence: number;    // 0.0-1.0
  };
  processing_time_ms: number;
}
```

### Example Request

```typescript
POST /api/v1/chat/intent/detect
Content-Type: application/json
Authorization: Bearer eyJ0eXAi...

{
  "message": "What's the best APY on Aave for USDC right now?",
  "include_agent_suggestions": true
}
```

### Example Response

```json
{
  "intent": {
    "type": "defi_yield_query",
    "confidence": 0.92,
    "entities": {
      "protocols": ["Aave"],
      "tokens": ["USDC"],
      "actions": ["supply", "lend"]
    }
  },
  "suggested_agent": {
    "agent_type": "DEFI_YIELD",
    "agent_name": "DeFi Yield Optimizer",
    "reasoning": "Query about lending rates on Aave requires yield analysis and protocol comparison",
    "confidence": 0.88
  },
  "processing_time_ms": 45
}
```

### Use Cases

- **Smart agent routing** - Automatically route messages to the most appropriate agent
- **Entity extraction** - Parse protocols, tokens, and actions from natural language
- **Intent classification** - Categorize user queries for analytics
- **Conversation context** - Improve responses using conversation history

---

## 2. Autocomplete Suggestions

Provides real-time autocomplete suggestions for partial messages.

**Endpoint:** `POST /api/v1/chat/intent/autocomplete`

### Request Body

```typescript
interface AutocompleteRequest {
  partial_message: string;     // Current partial message
  conversation_id?: string;    // Optional conversation context
  max_suggestions?: number;    // Max suggestions to return (default: 5)
}
```

### Response

```typescript
interface AutocompleteResponse {
  suggestions: Array<{
    completion_text: string;   // Full completion text
    display_text: string;      // Text to display in UI
    confidence: number;        // 0.0-1.0
    category: string;          // "protocol", "token", "action", "query"
    metadata?: {
      protocol?: string;
      chain?: string;
      icon_url?: string;
    };
  }>;
  processing_time_ms: number;
}
```

### Example Request

```typescript
POST /api/v1/chat/intent/autocomplete
Content-Type: application/json
Authorization: Bearer eyJ0eXAi...

{
  "partial_message": "What's the APY on Aa",
  "max_suggestions": 5
}
```

### Example Response

```json
{
  "suggestions": [
    {
      "completion_text": "What's the APY on Aave for USDC?",
      "display_text": "Aave (USDC)",
      "confidence": 0.95,
      "category": "protocol",
      "metadata": {
        "protocol": "Aave",
        "chain": "Ethereum",
        "icon_url": "https://..."
      }
    },
    {
      "completion_text": "What's the APY on Aave V3?",
      "display_text": "Aave V3",
      "confidence": 0.88,
      "category": "protocol"
    }
  ],
  "processing_time_ms": 23
}
```

### Use Cases

- **Real-time suggestions** - Show autocomplete dropdown as user types
- **Protocol discovery** - Help users discover available protocols
- **Query templates** - Suggest common query patterns
- **Faster input** - Reduce typing and improve UX

---

## 3. Find Similar Conversations

Finds semantically similar past conversations using vector similarity search.

**Endpoint:** `POST /api/v1/chat/intent/similar-conversations`

### Request Body

```typescript
interface SimilarConversationsRequest {
  message: string;              // Message to find similar conversations for
  max_results?: number;         // Max results to return (default: 5)
  similarity_threshold?: number; // Min similarity score 0.0-1.0 (default: 0.7)
  time_range_days?: number;     // Only search last N days (optional)
}
```

### Response

```typescript
interface SimilarConversationsResponse {
  conversations: Array<{
    conversation_id: string;
    title: string;
    created_at: string;       // ISO timestamp
    similarity_score: number; // 0.0-1.0
    snippet: string;          // Relevant message snippet
    metadata: {
      message_count: number;
      agents_used: string[];
      resolved: boolean;
    };
  }>;
  processing_time_ms: number;
}
```

### Example Request

```typescript
POST /api/v1/chat/intent/similar-conversations
Content-Type: application/json
Authorization: Bearer eyJ0eXAi...

{
  "message": "How do I stake ETH on Lido?",
  "max_results": 3,
  "similarity_threshold": 0.75
}
```

### Example Response

```json
{
  "conversations": [
    {
      "conversation_id": "conv_abc123",
      "title": "Lido Staking Guide",
      "created_at": "2025-12-10T14:30:00Z",
      "similarity_score": 0.92,
      "snippet": "To stake ETH on Lido, you need to...",
      "metadata": {
        "message_count": 8,
        "agents_used": ["DEFI_YIELD", "RESEARCH"],
        "resolved": true
      }
    }
  ],
  "processing_time_ms": 67
}
```

### Use Cases

- **Conversation history** - Show users their related past conversations
- **Quick answers** - Surface previous solutions to similar questions
- **Learning from history** - Build on previous conversations
- **Reduce redundancy** - Avoid repeating the same questions

---

# 📊 Personal Analytics Dashboard Endpoints

All analytics endpoints support date range filtering via query parameters:
- `date_from` (optional) - Start date (ISO format, defaults to 30 days ago)
- `date_to` (optional) - End date (ISO format, defaults to now)

---

## 1. Analytics Dashboard Overview

Get high-level personal analytics summary for the dashboard.

**Endpoint:** `GET /api/v1/chat/my-analytics`

### Query Parameters

```typescript
interface AnalyticsParams {
  date_from?: string;  // ISO date (default: 30 days ago)
  date_to?: string;    // ISO date (default: now)
}
```

### Response

```typescript
interface UserAnalyticsDashboardResponse {
  // Time period
  date_from: string;
  date_to: string;

  // High-level metrics
  total_conversations: number;
  total_messages: number;
  total_cost_usd: number;
  most_used_agent: string;

  // Quick insights
  conversation_completion_rate: number; // 0.0-1.0
  avg_response_satisfaction: number | null; // 1.0-5.0

  // Top agents (max 5)
  top_agents: Array<{
    agent_type: string;
    agent_name: string;
    usage_count: number;
    usage_percentage: number;      // 0-100
    success_rate: number;          // 0.0-1.0
    avg_response_time_ms: number;
    total_cost_usd: number;
    last_used: string | null;      // ISO timestamp
    personal_rating: number | null; // 1.0-5.0
  }>;

  // Activity summary
  most_active_day: string;   // Day of week
  most_active_hour: number;  // 0-23

  // Cost summary
  cost_this_period: number;
  cost_change_percentage: number; // vs previous period

  // Recent conversations (max 5)
  recent_conversations: Array<{
    conversation_id: string;
    title: string | null;
    created_at: string;
    message_count: number;
    duration_seconds: number;
    agents_used: string[];
    primary_topic: string | null;
    cost_usd: number;
    completed: boolean;
  }>;
}
```

### Example Request

```bash
GET /api/v1/chat/my-analytics?date_from=2025-11-17&date_to=2025-12-17
Authorization: Bearer eyJ0eXAi...
```

### Example Response

```json
{
  "date_from": "2025-11-17T00:00:00Z",
  "date_to": "2025-12-17T23:59:59Z",
  "total_conversations": 47,
  "total_messages": 312,
  "total_cost_usd": 15.75,
  "most_used_agent": "DEFI_YIELD",
  "conversation_completion_rate": 0.87,
  "avg_response_satisfaction": 4.2,
  "top_agents": [
    {
      "agent_type": "DEFI_YIELD",
      "agent_name": "DeFi Yield Optimizer",
      "usage_count": 23,
      "usage_percentage": 48.9,
      "success_rate": 0.92,
      "avg_response_time_ms": 1250,
      "total_cost_usd": 7.20,
      "last_used": "2025-12-16T15:30:00Z",
      "personal_rating": 4.5
    }
  ],
  "most_active_day": "Monday",
  "most_active_hour": 14,
  "cost_this_period": 15.75,
  "cost_change_percentage": -12.5,
  "recent_conversations": []
}
```

### Use Cases

- **Dashboard overview** - Display user's chat activity at a glance
- **Agent insights** - Show which agents are most valuable
- **Cost tracking** - Monitor AI spending
- **Activity patterns** - Identify usage trends

---

## 2. Detailed Usage Statistics

Get comprehensive usage statistics with activity breakdowns.

**Endpoint:** `GET /api/v1/chat/my-analytics/usage`

### Response

```typescript
interface PersonalUsageStatsResponse {
  date_from: string;
  date_to: string;

  // Detailed usage metrics
  usage_stats: {
    total_conversations: number;
    total_messages: number;
    avg_messages_per_conversation: number;
    total_session_time_hours: number;
    avg_session_duration_minutes: number;
    most_active_day: string;
    most_active_hour: number;           // 0-23
    conversation_completion_rate: number; // 0.0-1.0
  };

  // Activity breakdown
  messages_by_day: Record<string, number>;   // "Monday": 45
  messages_by_hour: Record<number, number>;  // "14": 32

  // Engagement metrics
  avg_daily_conversations: number;
  avg_daily_messages: number;
  longest_conversation_messages: number;
  longest_session_hours: number;

  // Comparison to previous period
  conversation_growth: number;  // % change
  message_growth: number;       // % change
}
```

### Use Cases

- **Usage analytics** - Track chat activity over time
- **Peak hours** - Identify when users are most active
- **Engagement trends** - Monitor conversation growth
- **Session insights** - Understand typical session lengths

---

## 3. Conversation Insights

Get AI-driven insights about conversation patterns and quality.

**Endpoint:** `GET /api/v1/chat/my-analytics/insights`

### Response

```typescript
interface ConversationInsightsResponse {
  date_from: string;
  date_to: string;

  // Pattern analysis
  insights: {
    avg_conversation_length_messages: number;
    avg_conversation_duration_minutes: number;
    most_discussed_topics: Array<{
      topic_name: string;
      conversation_count: number;
      percentage: number;           // 0-100
      keywords: string[];
      trend: "rising" | "stable" | "declining";
    }>;
    question_types: Record<string, number>;  // "informational": 45
    avg_time_to_decision_minutes: number | null;
    most_productive_time: string;
  };

  // Topic analysis
  topic_distribution: Array<{
    topic_name: string;
    conversation_count: number;
    percentage: number;
    keywords: string[];
    trend: "rising" | "stable" | "declining";
  }>;

  // Conversation quality metrics
  avg_agent_switches_per_conversation: number;
  successful_conversations_percentage: number; // 0-100

  // Recommendations
  recommended_agents: string[];
  productivity_tips: string[];
}
```

### Use Cases

- **Content insights** - Understand what users talk about
- **Topic trends** - Identify trending discussion areas
- **Agent recommendations** - Suggest relevant agents
- **Productivity tips** - Help users optimize chat experience

---

## 4. Personal Cost Breakdown

Get detailed breakdown of AI costs by agent, model, and time.

**Endpoint:** `GET /api/v1/chat/my-analytics/costs`

### Response

```typescript
interface PersonalCostBreakdownResponse {
  date_from: string;
  date_to: string;

  // Cost summary
  cost_summary: {
    total_cost_usd: number;
    avg_cost_per_conversation: number;
    avg_cost_per_message: number;
    total_tokens_used: number;
    most_expensive_agent: string;
    cost_trend: "increasing" | "stable" | "decreasing";
    projected_monthly_cost_usd: number;
  };

  // Detailed breakdown
  cost_by_agent: Record<string, number>;    // "DEFI_YIELD": 5.20
  cost_by_model: Record<string, number>;    // "gpt-4": 12.50
  cost_by_day: Array<{
    date: string;
    conversations: number;
    messages: number;
    agents_used: number;
    cost_usd: number;
  }>;

  // Token usage
  tokens_by_agent: Record<string, number>;
  avg_tokens_per_conversation: number;

  // Savings recommendations
  cost_saving_tips: string[];
}
```

### Use Cases

- **Cost tracking** - Monitor AI spending by agent
- **Budget management** - Project monthly costs
- **Optimization tips** - Reduce costs without losing quality
- **Agent cost comparison** - Compare agent efficiency

---

## 5. Favorite Agents

Get analysis of agent preferences and performance.

**Endpoint:** `GET /api/v1/chat/my-analytics/agents/favorites`

### Response

```typescript
interface FavoriteAgentsResponse {
  date_from: string;
  date_to: string;

  // Agent preferences (sorted by usage)
  favorite_agents: Array<{
    agent_type: string;
    agent_name: string;
    usage_count: number;
    usage_percentage: number;      // 0-100
    success_rate: number;          // 0.0-1.0
    avg_response_time_ms: number;
    total_cost_usd: number;
    last_used: string | null;
    personal_rating: number | null; // 1.0-5.0
  }>;

  // Usage patterns
  agent_switching_frequency: number;
  preferred_agent_for_task: Record<string, string>; // "yield_query": "DEFI_YIELD"

  // Performance comparison
  best_performing_agent: string;
  fastest_agent: string;
  most_cost_effective_agent: string;

  // Recommendations
  recommended_new_agents: string[];
}
```

### Use Cases

- **Agent analytics** - Track which agents deliver best results
- **Performance comparison** - Compare agent efficiency
- **Agent discovery** - Recommend underutilized agents
- **Personalization** - Customize agent suggestions

---

## 6. Historical Trends

Get time-series data showing trends over time.

**Endpoint:** `GET /api/v1/chat/my-analytics/trends`

### Query Parameters

```typescript
interface TrendsParams {
  date_from?: string;
  date_to?: string;
  granularity?: "hourly" | "daily" | "weekly"; // default: "daily"
}
```

### Response

```typescript
interface HistoricalTrendsResponse {
  date_from: string;
  date_to: string;
  granularity: "hourly" | "daily" | "weekly";

  // Trend data
  conversation_trend: {
    label: string;
    data_points: Array<{
      date: string;
      conversations: number;
      messages: number;
      agents_used: number;
      cost_usd: number;
    }>;
    total: number;
    average: number;
    trend_direction: "up" | "down" | "stable";
    change_percentage: number;
  };

  message_trend: {
    label: string;
    data_points: Array<DailyActivityPoint>;
    total: number;
    average: number;
    trend_direction: "up" | "down" | "stable";
    change_percentage: number;
  };

  cost_trend: {
    label: string;
    data_points: Array<DailyActivityPoint>;
    total: number;
    average: number;
    trend_direction: "up" | "down" | "stable";
    change_percentage: number;
  };

  // Activity patterns
  peak_usage_times: Array<{
    time_period: string;
    activity_level: number;
    typical_actions: string[];
  }>;

  activity_consistency_score: number; // 0.0-1.0

  // Comparative metrics
  percentile_rank: number | null; // 1-100
}
```

### Use Cases

- **Trend visualization** - Show charts of activity over time
- **Pattern identification** - Identify usage patterns
- **Growth tracking** - Monitor engagement growth
- **Benchmarking** - Compare to other users (percentile)

---

## 7. Conversation History

Get detailed conversation history with filtering and analysis.

**Endpoint:** `GET /api/v1/chat/my-analytics/conversations/history`

### Query Parameters

```typescript
interface HistoryParams {
  date_from?: string;
  date_to?: string;
  limit?: number;      // Max conversations to return
  offset?: number;     // Pagination offset
  agent_type?: string; // Filter by agent
  topic?: string;      // Filter by topic
}
```

### Response

```typescript
interface ConversationHistoryResponse {
  date_from: string;
  date_to: string;

  // Recent conversations
  conversations: Array<{
    conversation_id: string;
    title: string | null;
    created_at: string;
    message_count: number;
    duration_seconds: number;
    agents_used: string[];
    primary_topic: string | null;
    cost_usd: number;
    completed: boolean;
  }>;

  total_conversations: number;

  // Historical patterns
  avg_conversation_duration_minutes: number;
  most_common_topics: string[];
  agent_usage_distribution: Record<string, number>;

  // Quality metrics
  completion_rate: number;              // 0.0-1.0
  avg_satisfaction_rating: number | null; // 1.0-5.0

  // Insights
  most_productive_conversations: Array<ConversationSummary>;
}
```

### Use Cases

- **History browsing** - Browse past conversations
- **Search conversations** - Find specific conversations
- **Pattern analysis** - Understand conversation patterns
- **Quality tracking** - Monitor conversation success rates

---

## 8. Export Analytics Data

Export analytics data in JSON or CSV format.

**Endpoint:** `GET /api/v1/chat/my-analytics/export`

### Query Parameters

```typescript
interface ExportParams {
  date_from?: string;
  date_to?: string;
  format?: "json" | "csv";           // default: "json"
  include_conversations?: boolean;    // Include full conversation data
}
```

### Response

```typescript
interface UserExportDataResponse {
  export_format: "json" | "csv";
  date_from: string;
  date_to: string;
  includes_conversations: boolean;

  // Export data (structure varies by format)
  data: Record<string, any>;

  // Metadata
  generated_at: string;
  record_count: number;
  file_size_bytes: number | null;

  // Download info (for large exports)
  download_url: string | null;
  expires_at: string | null;
}
```

### JSON Export Example

```json
{
  "export_format": "json",
  "date_from": "2025-11-17T00:00:00Z",
  "date_to": "2025-12-17T23:59:59Z",
  "includes_conversations": false,
  "data": {
    "summary": {
      "total_conversations": 47,
      "total_messages": 312,
      "total_cost_usd": 15.75
    },
    "agents": [...],
    "costs": {...},
    "trends": [...]
  },
  "generated_at": "2025-12-17T10:30:00Z",
  "record_count": 47,
  "file_size_bytes": 15420
}
```

### CSV Export Example

For CSV format, the response includes a `download_url` pointing to a CSV file:

```csv
conversation_id,created_at,message_count,agents_used,cost_usd,completed
conv_abc123,2025-12-16T14:30:00Z,8,"DEFI_YIELD|RESEARCH",0.45,true
conv_def456,2025-12-15T10:15:00Z,12,"RISK_ANALYZER",0.67,true
```

### Use Cases

- **Data portability** - Export data for external analysis
- **Backup** - Create backups of analytics data
- **Reporting** - Generate reports for teams/stakeholders
- **Integration** - Feed data into external BI tools

---

## Common Response Fields

### Daily Activity Point

Used across multiple endpoints for time-series data:

```typescript
interface DailyActivityPoint {
  date: string;          // ISO date
  conversations: number;
  messages: number;
  agents_used: number;
  cost_usd: number;
}
```

### Agent Preference Entry

Standard agent usage information:

```typescript
interface AgentPreferenceEntry {
  agent_type: string;
  agent_name: string;
  usage_count: number;
  usage_percentage: number;      // 0-100
  success_rate: number;          // 0.0-1.0
  avg_response_time_ms: number;
  total_cost_usd: number;
  last_used: string | null;
  personal_rating: number | null; // 1.0-5.0
}
```

---

## Error Handling

All endpoints use standardized error responses. See [ERROR_CODES_REFERENCE.md](../../ERROR_CODES_REFERENCE.md) for complete error codes.

### Common Errors

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_001` | 401 | Missing or invalid authentication token |
| `AUTH_002` | 401 | Token expired |
| `CHAT_001` | 404 | Conversation not found |
| `CHAT_004` | 400 | Invalid date range |
| `ANALYTICS_001` | 400 | Invalid analytics parameters |
| `RATE_LIMIT_001` | 429 | Too many requests |

### Example Error Response

```json
{
  "error": {
    "code": "CHAT_004",
    "message": "Invalid date range: date_from must be before date_to",
    "i18n_key": "errors.chat.invalid_date_range",
    "details": {
      "date_from": "2025-12-17",
      "date_to": "2025-11-17"
    },
    "http_status": 400
  }
}
```

---

## Rate Limiting

### Intent Detection Endpoints

- **Rate Limit:** 100 requests per minute per user
- **Burst:** 20 requests per second
- **Headers:**
  - `X-RateLimit-Limit: 100`
  - `X-RateLimit-Remaining: 95`
  - `X-RateLimit-Reset: 1702829400`

### Analytics Endpoints

- **Rate Limit:** 60 requests per minute per user
- **Burst:** 10 requests per second
- **Cache:** Results cached for 5 minutes

---

## Performance Considerations

### Intent Detection

- **Average Response Time:** 40-80ms
- **Caching:** Intent results cached for 60 seconds per unique message
- **Optimization:** Use `include_agent_suggestions: false` for faster responses when not needed

### Analytics

- **Average Response Time:** 100-300ms (depends on data volume)
- **Caching:** Analytics results cached for 5 minutes
- **Pagination:** Use pagination for large datasets (conversation history)
- **Date Ranges:** Limit date ranges to 90 days for optimal performance

---

## WebSocket Integration

Intent detection can also be accessed via WebSocket for real-time processing:

```typescript
// Connect to WebSocket
const ws = new WebSocket('wss://api.anvil.defi/ws/chat');

// Send intent detection request
ws.send(JSON.stringify({
  type: 'intent.detect',
  data: {
    message: 'What's the APY on Aave?',
    conversation_id: 'conv_123'
  }
}));

// Receive intent response
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  if (response.type === 'intent.detected') {
    console.log('Intent:', response.data.intent);
    console.log('Suggested Agent:', response.data.suggested_agent);
  }
};
```

See [WEBSOCKET_INTEGRATION_GUIDE.md](../../WEBSOCKET_INTEGRATION_GUIDE.md) for complete WebSocket documentation.

---

## TypeScript SDK

### Intent Detection

```typescript
import { AnvilClient } from '@anvil/sdk';

const client = new AnvilClient({ apiKey: 'your_jwt_token' });

// Detect intent
const intent = await client.chat.intent.detect({
  message: 'What's the best APY on Aave for USDC?',
  include_agent_suggestions: true
});

console.log('Intent type:', intent.intent.type);
console.log('Suggested agent:', intent.suggested_agent?.agent_name);

// Get autocomplete suggestions
const suggestions = await client.chat.intent.autocomplete({
  partial_message: 'What's the APY on Aa',
  max_suggestions: 5
});

// Find similar conversations
const similar = await client.chat.intent.similarConversations({
  message: 'How do I stake ETH on Lido?',
  max_results: 3
});
```

### Analytics

```typescript
// Get dashboard overview
const dashboard = await client.chat.analytics.getDashboard({
  date_from: '2025-11-17',
  date_to: '2025-12-17'
});

console.log('Total conversations:', dashboard.total_conversations);
console.log('Most used agent:', dashboard.most_used_agent);

// Get detailed usage stats
const usage = await client.chat.analytics.getUsageStats({
  date_from: '2025-11-17',
  date_to: '2025-12-17'
});

// Get cost breakdown
const costs = await client.chat.analytics.getCosts({
  date_from: '2025-11-17',
  date_to: '2025-12-17'
});

// Export analytics data
const exportData = await client.chat.analytics.export({
  format: 'json',
  include_conversations: false
});
```

---

## Best Practices

### Intent Detection

1. **Use conversation context** - Include `conversation_id` for better intent detection
2. **Cache results** - Cache intent results to reduce API calls
3. **Batch autocomplete** - Debounce autocomplete requests (300ms minimum)
4. **Handle low confidence** - Show fallback UI when confidence < 0.7

### Analytics

1. **Reasonable date ranges** - Limit to 90 days for best performance
2. **Pagination** - Use pagination for conversation history
3. **Cache dashboard** - Cache dashboard data for 5 minutes
4. **Progressive loading** - Load detailed analytics on demand

### Error Handling

1. **Retry logic** - Implement exponential backoff for 5xx errors
2. **User feedback** - Show user-friendly error messages
3. **Fallback UI** - Provide graceful degradation when analytics unavailable
4. **Logging** - Log errors for debugging but don't expose internals

---

## Migration Guide

### From Legacy Chat API

If migrating from the old chat API, note these changes:

1. **Intent detection is new** - No legacy equivalent
2. **Analytics were scattered** - Now centralized under `/my-analytics`
3. **Response formats standardized** - All use consistent Pydantic schemas
4. **Better caching** - 5-minute cache on analytics, 60-second on intent

### Example Migration

**Old (multiple endpoints):**
```typescript
// Legacy fragmented approach
const stats = await fetch('/api/v1/chat/stats');
const costs = await fetch('/api/v1/chat/costs');
const agents = await fetch('/api/v1/chat/agents/usage');
```

**New (unified dashboard):**
```typescript
// New unified approach
const dashboard = await client.chat.analytics.getDashboard();
// Contains stats, costs, agents, and more in one response
```

---

## Support

For questions or issues:
- **Documentation:** [docs.anvil.defi/chat](https://docs.anvil.defi/chat)
- **API Status:** [status.anvil.defi](https://status.anvil.defi)
- **Support:** [support@anvil.defi](mailto:support@anvil.defi)

---

**Last Updated:** December 17, 2025
**Version:** 1.0
**Status:** ✅ Production Ready

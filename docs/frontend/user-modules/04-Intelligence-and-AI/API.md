# Intelligence & AI Chat API Documentation

> **Complete API and WebSocket Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/user/chat`

---

## 📋 Table of Contents

1. [API Endpoints](#api-endpoints)
2. [WebSocket Connections](#websocket-connections)
3. [Request/Response Schemas](#requestresponse-schemas)
4. [Error Handling](#error-handling)
5. [Message Flow](#message-flow)

---

## 🔌 API Endpoints

### 1. Create Conversation

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/conversations`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Request Body
```typescript
interface CreateConversationRequest {
  title?: string;                // Optional: Conversation title
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | No | Conversation title | Max 200 chars, auto-generated if not provided |

**JSON Example**:
```json
{
  "title": "DeFi Portfolio Strategy"
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface ConversationResponse {
  id: string;                    // UUID
  user_id: number;
  title: string;
  created_at: string;            // ISO 8601
  updated_at: string;            // ISO 8601
}
```

**JSON Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 123,
  "title": "DeFi Portfolio Strategy",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `400` | `ValidationError` | Invalid request | Show inline errors |
| `503` | `ServiceError` | Service unavailable | Show error + Retry |

---

### 2. List Conversations

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/conversations`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `20` |
| `offset` | `number` | No | Pagination offset | `0` |

#### Response

##### Success Response (200 OK)
```typescript
interface ConversationListResponse {
  conversations: ConversationResponse[];
  total: number;
}
```

---

### 3. Get Conversation

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/conversations/{conversation_id}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `conversation_id` | `string` | Yes | Conversation UUID |

#### Response

##### Success Response (200 OK)
Returns `ConversationResponse`

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `404` | `NotFoundError` | Conversation not found | Show error: "Conversation not found" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |

---

### 4. Send Message

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/conversations/{conversation_id}/messages`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SendMessageRequest {
  content: string;                // Required: Message content
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `content` | `string` | **Yes** | Message content | Min 1 char, max 10000 chars |

#### Response

##### Success Response (201 Created)
```typescript
interface SendMessageResponse {
  user_message: Message;
  agent_message: Message;
}

interface Message {
  id: string;                    // UUID
  conversation_id: string;        // UUID
  role: string;                  // "user" | "agent" | "system"
  content: string;
  created_at: string;            // ISO 8601
}
```

**JSON Example**:
```json
{
  "user_message": {
    "id": "msg-123",
    "conversation_id": "conv-456",
    "role": "user",
    "content": "What's the best DeFi strategy?",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "agent_message": {
    "id": "msg-124",
    "conversation_id": "conv-456",
    "role": "agent",
    "content": "Based on your portfolio...",
    "created_at": "2024-01-15T10:30:05Z"
  }
}
```

**Note**: This endpoint returns both the user message and the agent response synchronously. For streaming responses, use WebSocket.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValidationError` | Invalid content | Show inline error |
| `404` | `NotFoundError` | Conversation not found | Show error: "Conversation not found" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `ServiceError` | Service unavailable | Show error + Retry |

---

### 5. Get Messages

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/conversations/{conversation_id}/messages`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |

#### Response

##### Success Response (200 OK)
```typescript
interface MessageListResponse {
  messages: Message[];
  total: number;
}
```

**Note**: Messages are returned in chronological order (oldest first).

---

### 6. Search Protocols (GraphRAG)

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/search-protocols`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ChatProtocolSearchRequest {
  query: string;                  // Required: Search query
  conversation_id?: string;       // Optional: Conversation UUID for context
  user_preferences?: object;      // Optional: User preferences
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ChatProtocolSearchResponse {
  results: ProtocolResult[];
  search_context: string;         // Explanation of search context
  recommendations: string[];      // Recommendations based on search
}

interface ProtocolResult {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;       // 0-1
  risk_score: number;             // 0-1
  risk_level: string;             // "low" | "moderate" | "high" | "critical"
  tvl: number;
  apy: number;
  audit_count: number;
  description: string;
  category: string;
  chain: string;
  why_relevant: string;           // Explanation of relevance
}
```

---

### 7. Analyze Risk

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/analyze-risk`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ChatRiskAnalysisRequest {
  protocol_name: string;          // Required: Protocol name
  conversation_id?: string;       // Optional: Conversation UUID for context
  operation_type?: string;        // Optional: "supply" | "borrow" | "swap"
  amount_usd?: number;            // Optional: Operation amount in USD
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ChatRiskAnalysisResponse {
  risk_analysis: {
    protocol_id: string;
    protocol_name: string;
    risk_score: number;           // 0-1
    risk_level: string;            // "low" | "moderate" | "high" | "critical"
    confidence: number;            // 0-1
    contributing_factors: RiskFactor[];
  };
  recommendations: string[];
  safer_alternatives?: ProtocolAlternative[];
}

interface RiskFactor {
  factor: string;
  impact: number;                 // 0-1
  description: string;
  is_critical: boolean;
}

interface ProtocolAlternative {
  protocol_name: string;
  risk_score: number;
  why_safer: string;
}
```

---

### 8. Get Similar Protocols

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/similar-protocols`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ChatSimilarProtocolsRequest {
  conversation_id: string;        // Required: Conversation UUID
  protocol_name: string;          // Required: Protocol name to find similar ones
  limit?: number;                 // Optional: Max results (default: 5, max: 20)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `conversation_id` | `string` | **Yes** | Conversation UUID | Valid UUID |
| `protocol_name` | `string` | **Yes** | Protocol name | Min 1, max 200 chars |
| `limit` | `number` | No | Max results | 1-20, default 5 |

#### Response

##### Success Response (200 OK)
```typescript
interface ChatSimilarProtocolsResponse {
  base_protocol: {
    protocol_id: string;
    protocol_name: string;
    risk_score: number;
    risk_level: string;
    tvl: number;
    category: string;
  };
  similar_protocols: SimilarProtocolInfo[];
}

interface SimilarProtocolInfo {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;       // 0-1
  risk_score: number;
  risk_level: string;
  tvl: number;
  why_similar: string;            // Explanation of similarity
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `404` | `NotFoundError` | Protocol not found | Show error: "Protocol not found" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |

---

### 9. Agent Squad Message

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/conversations/{conversation_id}/agent-squad/messages`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `conversation_id` | `string` | Yes | Conversation UUID |

##### Request Body
```typescript
interface AgentSquadMessageRequest {
  content: string;                 // Required: User message (1-10000 chars)
  force_agent?: string;           // Optional: Force specific agent
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `content` | `string` | **Yes** | User message | Min 1, max 10000 chars |
| `force_agent` | `string` | No | Force specific agent | Valid agent type |

#### Response

##### Success Response (201 Created)
```typescript
interface AgentSquadMessageResponse {
  user_message_id: string;        // UUID
  agent_message_id: string;        // UUID
  agent_type: string;             // Which agent handled the message
  intent_classification?: string; // Classified intent
  intent_confidence?: number;      // 0.0-1.0
  content: string;                 // Agent response
  tools_used: string[];           // Tools/APIs used
  latency_ms: number;              // Response latency
  tokens_used?: number;            // LLM tokens consumed
}
```

---

### 10. Supervisor Workflow

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/conversations/{conversation_id}/agent-squad/supervisor`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `conversation_id` | `string` | Yes | Conversation UUID |

##### Request Body
```typescript
interface SupervisorWorkflowRequest {
  content: string;                 // Required: Complex task description (1-10000 chars)
  max_agents?: number;            // Optional: Max agents to use (1-10, default: 5)
  timeout_seconds?: number;       // Optional: Workflow timeout (30-300, default: 120)
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface SupervisorWorkflowResponse {
  workflow_id: string;             // UUID
  conversation_id: string;         // UUID
  status: string;                  // "in_progress" | "completed" | "failed"
  tasks: WorkflowTask[];
  final_response?: string;         // Aggregated response (if completed)
  total_latency_ms: number;
  agents_used: string[];
}

interface WorkflowTask {
  agent_type: string;
  task_description: string;
  status: string;                  // "pending" | "in_progress" | "completed" | "failed"
  result?: string;                 // Agent response (if completed)
}
```

---

### 11. List Enabled Agents

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/agent-squad/agents`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `user_subscription_tier` | `string` | No | Subscription tier filter |

#### Response

##### Success Response (200 OK)
```typescript
interface ListEnabledAgentsResponse {
  agents: AgentCapability[];
  total: number;
  core_agents: number;
  enterprise_agents: number;
}

interface AgentCapability {
  agent_type: string;
  name: string;
  description: string;
  model: string;
  temperature: number;
  enabled: boolean;
  is_enterprise: boolean;
}
```

**Note**: Available agents depend on subscription tier:
- **Free**: 5 agents (chat, hunter_ai, research, portfolio, gas_optimizer)
- **Pro**: 10 agents (all core user-facing)
- **Enterprise**: 18 agents (all agents including enterprise/advanced)

---

### 12. Detect Intent

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/intent/detect`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface DetectIntentRequest {
  message: string;                  // Required: User message (1-10000 chars)
  conversation_id?: string;        // Optional: Conversation UUID for context
  include_suggestions?: boolean;   // Optional: Include agent suggestions (default: true)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface DetectIntentResponse {
  intent: IntentPredictionResponse;
  suggested_agents: AgentSuggestionResponse[];
  processing_time_ms: number;
}

interface IntentPredictionResponse {
  intent_type: string;
  confidence: number;              // 0.0-1.0
  confidence_level: string;        // "low" | "medium" | "high"
  suggested_agent?: string;
  extracted_entities: object;
  reasoning?: string;
  alternative_intents: AlternativeIntent[];
  is_high_confidence: boolean;
  is_ambiguous: boolean;
}

interface AlternativeIntent {
  intent_type: string;
  confidence: number;              // 0.0-1.0
}

interface AgentSuggestionResponse {
  agent_name: string;
  confidence: number;              // 0.0-1.0
  reasoning?: string;
  agent_description?: string;
  estimated_response_time_seconds?: number;
  is_high_confidence: boolean;
}
```

---

### 13. Autocomplete

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/intent/autocomplete`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface AutocompleteRequest {
  partial_message: string;         // Required: Partial message (1-1000 chars)
  limit?: number;                  // Optional: Max results (1-50, default: 10)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface AutocompleteResponse {
  suggestions: AutocompleteSuggestionResponse[];
  processing_time_ms: number;
}

interface AutocompleteSuggestionResponse {
  completion_text: string;
  display_text: string;
  confidence: number;              // 0.0-1.0
  suggestion_type: string;        // "protocol" | "token" | "action" | etc.
  icon?: string;
  metadata: object;
}
```

---

### 14. Find Similar Conversations

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/intent/similar-conversations`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SimilarConversationsRequest {
  message: string;                 // Required: Message to match (1-10000 chars)
  limit?: number;                  // Optional: Max results (1-20, default: 5)
  similarity_threshold?: number;   // Optional: Min similarity (0.0-1.0, default: 0.7)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface SimilarConversationsResponse {
  matches: ConversationMatchResponse[];
  processing_time_ms: number;
}

interface ConversationMatchResponse {
  conversation_id: string;         // UUID
  title?: string;
  similarity_score: number;         // 0.0-1.0
  snippet: string;
  created_at: string;               // ISO 8601
  message_count: number;
  was_helpful?: boolean;
}
```

### 15. Get My Analytics Dashboard

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `string` | No | Start date (ISO 8601) | 30 days ago |
| `date_to` | `string` | No | End date (ISO 8601) | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface UserAnalyticsDashboardResponse {
  total_conversations: number;
  total_messages: number;
  most_used_agents: AgentUsage[];
  personal_spending: CostBreakdown;
  conversation_patterns: PatternAnalysis;
  success_rates: SuccessMetrics;
  activity_trends: ActivityTrend[];
}
```

---

### 16. Get My Usage Statistics

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/usage`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface PersonalUsageStatsResponse {
  total_conversations: number;
  total_messages: number;
  average_messages_per_conversation: number;
  most_active_days: DayActivity[];
  conversation_completion_rate: number;
  session_duration_stats: DurationStats;
  engagement_metrics: EngagementMetrics;
}
```

---

### 17. Get Conversation Insights

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/insights`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface ConversationInsightsResponse {
  average_conversation_length: number;
  most_discussed_topics: TopicDistribution[];
  topic_distribution: TopicDistribution[];
  conversation_sentiment: string;
  question_types: QuestionTypeBreakdown;
  engagement_patterns: EngagementPattern[];
  time_to_decision: number;
}
```

---

### 18. Get Personal Cost Breakdown

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/costs`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface PersonalCostBreakdownResponse {
  total_cost_usd: string;
  cost_by_agent: AgentCost[];
  cost_by_conversation: ConversationCost[];
  cost_trends: CostTrend[];
  average_cost_per_message: string;
}
```

---

### 19. Get Favorite Agents

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/favorite-agents`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface FavoriteAgentsResponse {
  favorite_agents: AgentPreferenceEntry[];
  success_rates: AgentSuccessRate[];
  usage_frequency: AgentFrequency[];
}
```

---

### 20. Get Historical Trends

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/trends`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface HistoricalTrendsResponse {
  daily_activity: DailyActivityPoint[];
  conversation_trends: TrendData[];
  message_volume_trends: TrendData[];
  agent_usage_trends: AgentTrendData[];
  cost_trends: TrendData[];
}
```

---

### 21. Get Conversation History Analysis

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/history`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |
| `date_from` | `string` | No | Start date | 30 days ago |
| `date_to` | `string` | No | End date | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface ConversationHistoryResponse {
  conversations: ConversationAnalysis[];
  total: number;
  patterns: ConversationPattern[];
}
```

---

### 22. Export Analytics Data

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/my-analytics/export`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `format` | `string` | No | Export format | `json` |
| `date_from` | `string` | No | Start date | 30 days ago |
| `date_to` | `string` | No | End date | Now |

**Valid Formats**: `json`, `csv`

#### Response

##### Success Response (200 OK)
```typescript
interface UserExportDataResponse {
  export_url: string;
  expires_at: string;             // ISO 8601
  format: string;
  record_count: number;
}
```

---

## 🔌 Hunter AI Endpoints (Advanced AI Features)

### 23. Analyze Token Sentiment

**Method**: `GET`  
**Endpoint**: `/api/v1/user/hunter/sentiment/analyze/{token_symbol}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token_symbol` | `string` | Yes | Token symbol (e.g., "ETH", "BTC") |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `hours` | `number` | No | Hours of historical data | `24` |
| `sources` | `string` | No | Comma-separated sources | All sources |

**Valid Sources**: `twitter`, `reddit`, `discord`, `news`

#### Response

##### Success Response (200 OK)
```typescript
interface SentimentResponse {
  token_symbol: string;
  overall_score: number;           // 0-100
  classification: string;          // "bullish" | "bearish" | "neutral"
  confidence: number;              // 0-1
  signal_strength: string;         // "strong" | "moderate" | "weak"
  timestamp: string;               // ISO 8601
  sources: { [source: string]: SentimentSourceData };
  source_count: number;
  has_divergence: boolean;
  consensus: number;               // 0-1
}
```

---

### 24. Get Trading Signal

**Method**: `GET`  
**Endpoint**: `/api/v1/user/hunter/signals/generate/{token_symbol}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token_symbol` | `string` | Yes | Token symbol |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `timeframe` | `string` | No | Timeframe | `1d` |

**Valid Timeframes**: `1h`, `4h`, `1d`, `1w`, `1M`

#### Response

##### Success Response (200 OK)
```typescript
interface TradingSignalResponse {
  token_symbol: string;
  signal_type: string;             // "BUY" | "SELL" | "HOLD" | "STRONG_BUY" | "STRONG_SELL"
  signal_strength: number;         // 0-100
  confidence: number;              // 0-1
  entry_price?: number;
  stop_loss_price?: number;
  take_profit_price?: number;
  sentiment_score: number;         // 0-100
  prediction_score: number;        // 0-100
  risk_score: number;             // 0-100
  timeframe: string;
  generated_at: string;            // ISO 8601
  recommendation: string;
}
```

---

### 25. Get Multi-Timeframe Analysis

**Method**: `GET`  
**Endpoint**: `/api/v1/user/hunter/signals/multi-timeframe/{token_symbol}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface MultiTimeframeAnalysisResponse {
  token_symbol: string;
  signals: { [timeframe: string]: TradingSignalResponse };
  consensus_signal: string;
  alignment_score: number;         // 0-1
  trend_direction: string;         // "bullish" | "bearish" | "neutral"
  generated_at: string;            // ISO 8601
}
```

---

### 26. Predict Token Price

**Method**: `POST`  
**Endpoint**: `/api/v1/user/hunter/prediction/predict`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface PricePredictionRequest {
  token_symbol: string;            // Required
  timeframe: string;               // Required: "1h" | "4h" | "1d" | "1w" | "1M"
  prediction_horizon: number;      // Required: Hours to predict ahead
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface PricePredictionResponse {
  token_symbol: string;
  current_price: number;
  predicted_price: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  confidence: number;              // 0-1
  timeframe: string;
  prediction_horizon_hours: number;
  factors: PredictionFactor[];
  generated_at: string;            // ISO 8601
}
```

---

### 27. Get Risk Analysis

**Method**: `GET`  
**Endpoint**: `/api/v1/user/hunter/risk/analyze/{token_symbol}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface RiskAnalysisResponse {
  token_symbol: string;
  overall_risk_score: number;      // 0-100
  risk_level: string;              // "low" | "medium" | "high" | "critical"
  volatility_score: number;
  liquidity_score: number;
  market_cap_risk: number;
  technical_risk: number;
  fundamental_risk: number;
  recommendations: string[];
  generated_at: string;            // ISO 8601
}
```

---

### 28. Detect Trading Patterns

**Method**: `GET`  
**Endpoint**: `/api/v1/user/hunter/patterns/detect/{token_symbol}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `pattern_type` | `string` | No | Filter by pattern type | All patterns |
| `timeframe` | `string` | No | Timeframe | `1d` |

#### Response

##### Success Response (200 OK)
```typescript
interface PatternDetectionResponse {
  token_symbol: string;
  patterns: DetectedPattern[];
  confidence: number;              // 0-1
  timeframe: string;
  generated_at: string;             // ISO 8601
}

interface DetectedPattern {
  pattern_type: string;            // "head_and_shoulders" | "double_top" | etc.
  confidence: number;              // 0-1
  description: string;
  implications: string;
}
```

---

## 🔌 ML Prediction Endpoints

### 29. Predict Protocol Risk

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/prediction/{protocol_id}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `protocol_id` | `string` | Yes | Protocol UUID |

#### Response

##### Success Response (200 OK)
```typescript
interface RiskPredictionResponse {
  protocol_id: string;
  protocol_name: string;
  predicted_risk_score: number;    // 0-100
  confidence: number;              // 0-1
  risk_level: string;              // "low" | "medium" | "high" | "critical"
  risk_trend: string;              // "improving" | "stable" | "worsening"
  contributing_factors: string[];
  recommendations: string[];
  prediction_timestamp: string;     // ISO 8601
  model_version: string;
}
```

---

### 30. Batch Predict Protocol Risks

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ml/prediction/batch`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface BatchRiskPredictionRequest {
  protocol_ids: string[];          // Required: Array of protocol UUIDs
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface BatchRiskPredictionResponse {
  predictions: RiskPredictionResponse[];
  total: number;
}
```

---

### 31. Detect Anomalies

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/prediction/{protocol_id}/anomalies`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `lookback_days` | `number` | No | Days to look back | `7` |

#### Response

##### Success Response (200 OK)
```typescript
interface AnomalyDetectionResponse {
  protocol_id: string;
  has_anomalies: boolean;
  anomalies: Anomaly[];
  risk_impact: string;             // "low" | "medium" | "high"
}

interface Anomaly {
  type: string;
  severity: string;
  detected_at: string;             // ISO 8601
  description: string;
}
```

---

### 32. Forecast Risk

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/prediction/{protocol_id}/forecast`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `forecast_days` | `number` | No | Days to forecast | `7` |

#### Response

##### Success Response (200 OK)
```typescript
interface RiskForecastResponse {
  protocol_id: string;
  forecast: RiskForecastPoint[];
  forecast_days: number;
}

interface RiskForecastPoint {
  date: string;                     // ISO 8601
  predicted_risk_score: number;     // 0-100
  confidence: number;               // 0-1
}
```

---

## 🔌 Network Analysis Endpoints

### 33. Calculate PageRank

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/network/pagerank`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `damping_factor` | `number` | No | Damping factor (0-1) | `0.85` |
| `max_iterations` | `number` | No | Max iterations | `100` |

#### Response

##### Success Response (200 OK)
```typescript
interface PageRankListResponse {
  results: PageRankResponse[];
  total: number;
}

interface PageRankResponse {
  protocol_id: string;
  protocol_name: string;
  pagerank_score: number;          // 0-1
  rank: number;
  in_degree: number;
  out_degree: number;
}
```

---

### 34. Detect Communities

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/network/communities`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `algorithm` | `string` | No | Detection algorithm | `label_propagation` |

#### Response

##### Success Response (200 OK)
```typescript
interface CommunityListResponse {
  communities: CommunityResponse[];
  total_communities: number;
}

interface CommunityResponse {
  community_id: number;
  protocols: string[];             // Protocol IDs
  size: number;
  density: number;                 // 0-1
  description: string;
}
```

---

### 35. Calculate Centrality

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/network/centrality`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `protocol_id` | `string` | No | Specific protocol UUID |

#### Response

##### Success Response (200 OK)
```typescript
interface CentralityListResponse {
  results: CentralityResponse[];
  total: number;
}

interface CentralityResponse {
  protocol_id: string;
  protocol_name: string;
  degree_centrality: number;      // 0-1
  betweenness_centrality: number;  // 0-1
  closeness_centrality: number;    // 0-1
  eigenvector_centrality: number;  // 0-1
  importance_score: number;        // Combined score
}
```

---

### 36. Simulate Contagion

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ml/network/contagion/{protocol_id}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `propagation_probability` | `number` | No | Cascade probability (0-1) | `0.8` |
| `max_depth` | `number` | No | Max cascade depth | `5` |

#### Response

##### Success Response (200 OK)
```typescript
interface ContagionSimulationResponse {
  origin_protocol_id: string;
  affected_protocols: AffectedProtocol[];
  total_exposure_at_risk: number;  // USD
  cascade_depth: number;
  propagation_probability: number;
}

interface AffectedProtocol {
  protocol_id: string;
  protocol_name: string;
  cascade_depth: number;
  exposure_at_risk: number;        // USD
  impact_probability: number;       // 0-1
}
```

---

## 🔌 WebSocket Connections

### 1. Chat WebSocket (Real-Time Streaming)

**Endpoint**: `ws://api.example.com/api/v1/ws/chat?token={access_token}&session_id={optional}`  
**Auth Required**: Yes (JWT Token in Query Parameter)  
**Purpose**: Real-time chat with agent streaming and multi-agent orchestration

#### Connection

**URL Format**:
```
ws://api.example.com/api/v1/ws/chat?token={access_token}&session_id={optional_session_id}
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | `string` | **Yes** | JWT access token |
| `session_id` | `string` | No | Optional chat session ID |

#### Connection Flow

1. **Connect**: Client connects to WebSocket endpoint with token
2. **Authentication**: Server validates JWT token
3. **Welcome**: Server sends welcome message with user_id and session_id
4. **Message Exchange**: Client and server exchange messages
5. **Heartbeat**: Client sends "ping", server responds "pong"
6. **Disconnect**: Either side can close connection

#### Message Types

##### Client → Server

**Send Message**:
```json
{
  "type": "message",
  "content": "User message content",
  "conversation_id": "optional-uuid"
}
```

**Ping (Heartbeat)**:
```json
{
  "type": "ping"
}
```

##### Server → Client

**Welcome Message** (on connect):
```json
{
  "type": "system",
  "message": "Connected to Anvil AI Chat",
  "user_id": "user_123",
  "session_id": "session_456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Streaming Token** (token-by-token streaming):
```json
{
  "type": "stream",
  "content": "partial",
  "message_id": "msg-uuid"
}
```

**Progress Event** (agent execution progress):
```json
{
  "type": "progress",
  "status": "thinking|tool_call|processing",
  "message": "Checking swap prices...",
  "tool": "get_swap_quote",
  "data": {}
}
```

**Complete Message**:
```json
{
  "type": "message",
  "content": "Complete agent response",
  "message_id": "msg-uuid",
  "metadata": {}
}
```

**Pong (Heartbeat Response)**:
```json
{
  "type": "pong"
}
```

**Error**:
```json
{
  "type": "error",
  "error": "Error message",
  "code": "error_code"
}
```

#### Connection Lifecycle

**States**:
- `connecting`: Initial connection attempt
- `connected`: Successfully connected and authenticated
- `disconnected`: Connection closed
- `error`: Connection error occurred

**Reconnection**:
- Client should implement exponential backoff
- Reconnect on unexpected disconnect
- Re-authenticate with fresh token if needed

#### Heartbeat

**Purpose**: Keep connection alive, detect dead connections

**Client Behavior**:
- Send "ping" every 30 seconds
- Expect "pong" within 5 seconds
- If no "pong" received, reconnect

**Server Behavior**:
- Respond to "ping" with "pong" immediately
- Close connection if no "ping" received for 60 seconds

#### Progress Events

**Status Types**:
- `thinking`: Agent is analyzing the request
- `tool_call`: Agent is calling an external tool/API
- `processing`: Agent is processing tool results

**Example Progress Flow**:
```json
// 1. Thinking
{"type": "progress", "status": "thinking", "message": "Processing your request..."}

// 2. Tool call
{"type": "progress", "status": "tool_call", "tool": "get_swap_quote", "message": "Checking swap prices..."}

// 3. Processing
{"type": "progress", "status": "processing", "message": "Analyzing results..."}

// 4. Streaming response
{"type": "stream", "content": "Based", "message_id": "msg-123"}
{"type": "stream", "content": " on", "message_id": "msg-123"}
// ... more tokens

// 5. Complete
{"type": "message", "content": "Based on current market data...", "message_id": "msg-123"}
```

#### Error Handling

**Connection Errors**:
- `1011`: Internal server error
- `1008`: Policy violation (invalid token)
- `1006`: Abnormal closure

**Message Errors**:
- Invalid message format → Server sends error message
- Empty message content → Server sends error: "Message content is required"
- Unauthorized → Server closes connection with code 1008

#### WebSocket Best Practices

1. **Connection Management**:
   - Reconnect automatically on disconnect
   - Show connection status in UI
   - Handle connection errors gracefully

2. **Message Handling**:
   - Buffer streaming tokens until complete
   - Show progress events to user
   - Handle errors without breaking UI

3. **Performance**:
   - Throttle UI updates during streaming
   - Debounce progress event displays
   - Clean up on component unmount

---

### 2. Conversation-Specific Chat WebSocket

**Endpoint**: `ws://api.example.com/api/v1/user/chat/ws/{conversation_id}?token={access_token}`  
**Auth Required**: Yes (JWT Token in Query Parameter)  
**Purpose**: Real-time chat updates for a specific conversation with multi-agent orchestration

#### Connection

**URL Format**:
```
ws://api.example.com/api/v1/user/chat/ws/{conversation_id}?token={access_token}
```

**Path Parameters**:
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `conversation_id` | `UUID` | **Yes** | Conversation UUID for this chat session |

**Query Parameters**:
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | `string` | **Yes** | JWT authentication token |

#### Connection Flow

1. **Connect**: Client connects with conversation_id and JWT token
2. **Authentication**: Server validates JWT token and checks conversation access
3. **Welcome**: Server sends welcome system message with session_id
4. **Message Exchange**: Client sends messages, server streams responses
5. **Intent Detection**: Server detects intent and sends suggestions
6. **Agent Streaming**: Server streams agent response with progress updates
7. **Heartbeat**: Client sends "ping", server responds "pong"
8. **Disconnect**: Either side can close connection

#### Client-to-Server Messages

##### Send Chat Message
```typescript
interface ChatMessageRequest {
  type: "message";
  content: string;            // Required: Message content
  conversation_id?: string;   // Optional: Conversation UUID (if not in URL)
}
```

**JSON Example**:
```json
{
  "type": "message",
  "content": "What's the best yield farming strategy?"
}
```

##### Heartbeat (Ping)
```typescript
interface PingMessage {
  type: "ping";
}
```

#### Server-to-Client Messages

##### Welcome System Message (on connect)
```typescript
interface SystemMessage {
  type: "system";
  message: string;
  data: {
    user_id: string;
    session_id: string;
    conversation_id: string;
  };
}
```

**JSON Example**:
```json
{
  "type": "system",
  "message": "Connected to conversation abc-123",
  "data": {
    "user_id": "user_123",
    "session_id": "ws_user_123_abc-123_1234567890",
    "conversation_id": "abc-123"
  }
}
```

##### Intent Suggestions (after message received)
```typescript
interface IntentSuggestionsMessage {
  type: "intent_suggestions";
  suggestions: Array<{
    intent: string;
    confidence: number;        // 0-1
    suggested_agent?: string;
  }>;
}
```

##### Progress Event (agent execution)
```typescript
interface ProgressMessage {
  type: "progress";
  status: "thinking" | "routing" | "tool_call" | "tool_completed" | "processing";
  message: string;
  agent?: string;
  tool?: string;
  confidence?: number;
}
```

**JSON Example**:
```json
{
  "type": "progress",
  "status": "routing",
  "message": "Routing to yield_farming agent (confidence: 95%)",
  "agent": "yield_farming",
  "confidence": 0.95
}
```

##### Streaming Token (token-by-token)
```typescript
interface StreamMessage {
  type: "stream";
  content: string;            // Partial token
  message_id: string;
}
```

##### Complete Message
```typescript
interface MessageCompleteMessage {
  type: "message_complete";
  message_id: string;
  content: string;             // Complete message
  metadata: {
    agent: string;
    confidence: number;
    execution_time_ms?: number;
  };
}
```

##### Error Message
```typescript
interface ErrorMessage {
  type: "error";
  error: string;
  code: string;
}
```

##### Heartbeat Response (Pong)
```typescript
interface PongMessage {
  type: "pong";
}
```

#### Connection Lifecycle

**States**:
- `connecting`: Initial connection attempt
- `authenticating`: Validating JWT token
- `connected`: Successfully connected and authenticated
- `disconnected`: Connection closed
- `error`: Connection error occurred

**Authorization**:
- User must have access to the conversation
- Server checks conversation ownership before accepting connection
- Access denied → Connection closed with code 1008

**Reconnection**:
- Client should implement exponential backoff
- Reconnect on unexpected disconnect
- Re-authenticate with fresh token if needed
- Maintain conversation_id across reconnections

#### Error Handling

**Connection Errors**:
- `1008`: Policy violation (invalid token or no access to conversation)
- `1011`: Internal server error
- `1006`: Abnormal closure

**Message Errors**:
- Invalid message format → Server sends error message
- Empty message content → Server sends error: "Message content is required"
- Unauthorized → Server closes connection with code 1008

#### Differences from Main Chat WebSocket

| Feature | Main WebSocket (`/ws/chat`) | Conversation WebSocket (`/user/chat/ws/{id}`) |
|---------|----------------------------|------------------------------------------------|
| **Conversation Context** | Optional (can create new) | Required (must exist) |
| **Access Control** | Basic (user auth) | Strict (conversation ownership) |
| **Use Case** | General chat, new conversations | Existing conversation updates |
| **Session Management** | Optional session_id | Tied to conversation_id |

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **WebSocket Streaming** | REST polling | Real-time vs. Complexity | Streaming provides better UX, but requires connection management |
| **Token-by-Token Streaming** | Complete messages | Perceived performance vs. Bandwidth | Token streaming feels faster, but uses more bandwidth |
| **Multi-Agent Orchestration** | Single agent | Capability vs. Complexity | Multiple agents provide specialized expertise, but add routing complexity |
| **GraphRAG Hybrid Search** | Keyword-only | Relevance vs. Infrastructure | Hybrid search improves results, but requires vector database |
| **Intent Detection** | Manual routing | Automation vs. Accuracy | Automatic intent detection improves UX, but may misroute queries |
| **Agent Squad Pattern** | Sequential agents | Parallelism vs. Coordination | Parallel agents are faster, but require result aggregation |

### Risk Assessment

**Cognitive Limitations:**
- WebSocket streaming may overwhelm clients with high token rates
- Agent routing may fail for ambiguous queries
- GraphRAG search may return irrelevant results if embeddings are stale

**Technical Debt:**
- Streaming requires careful buffer management
- Multi-agent coordination adds failure points
- GraphRAG requires continuous embedding updates
- Intent detection accuracy depends on training data quality

**Validation Strategy:**
- ✅ Monitor WebSocket streaming latency and error rates
- ✅ Track agent routing accuracy and user satisfaction
- ✅ Measure GraphRAG search relevance (user feedback)
- ✅ Monitor intent detection confidence scores
- ✅ Alert on agent execution failures
- ✅ Track conversation costs and token usage

---

## 📊 Error Handling Summary

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Validation Errors (400)**
   - Invalid request data
   - **Action**: Show inline field errors

3. **Not Found Errors (404)**
   - Conversation or message not found
   - **Action**: Show error message, navigate back

4. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/chat/router.py`
- **WebSocket Handler**: `src/app/presentation/http/websocket/chat_websocket.py`
- **Domain Entities**: `src/app/domain/entities/chat/`
- **Application Interactors**: `src/app/application/chat/`
- **Frontend Implementation**: `04-Intelligence-and-AI/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready

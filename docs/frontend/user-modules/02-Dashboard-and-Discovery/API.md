# Dashboard & Discovery API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/user/portfolio` and `/api/v1/user/markets`

---

## 📋 Table of Contents

1. [Portfolio Endpoints](#portfolio-endpoints)
2. [Dashboard Endpoints](#dashboard-endpoints)
3. [Market Endpoints](#market-endpoints)
4. [Comparison Endpoints](#comparison-endpoints)
5. [Notification Endpoints](#notification-endpoints)
6. [Graph Visualization Endpoints](#graph-visualization-endpoints)
7. [Graph Search Endpoints](#graph-search-endpoints)
8. [Graph Analytics Endpoints](#graph-analytics-endpoints)
9. [Graph Monitoring Endpoints](#graph-monitoring-endpoints)
10. [Search Endpoints](#search-endpoints)
11. [Metrics Endpoints](#metrics-endpoints)
12. [WebSocket Connections](#websocket-connections)
13. [Request/Response Schemas](#requestresponse-schemas)
14. [Error Handling](#error-handling)

---

## 🔌 Portfolio Endpoints

### 1. Get My Portfolio

**Method**: `GET`  
**Endpoint**: `/api/v1/user/portfolio/me`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Chain to calculate for | Wallet's default chain |
| `save_snapshot` | `boolean` | No | Save snapshot for history | `false` |

**Valid Chain Values**: `ethereum`, `base`, `arbitrum`, `polygon`, `optimism`

#### Response

##### Success Response (200 OK)
```typescript
interface PortfolioResponse {
  wallet_address: string;
  chain: string;
  total_usd: number;
  native_balance: string;         // Amount in smallest unit
  native_usd_value: number;
  native_symbol: string;         // "ETH", "MATIC", etc.
  tokens: TokenHolding[];
  captured_at: string;           // ISO 8601
  has_value: boolean;
}

interface TokenHolding {
  token_address: string | null;  // null for native token
  symbol: string;
  name: string;
  decimals: number;
  amount: string;                 // Amount in smallest unit
  usd_value: number | null;
  usd_price: number | null;
  percentage: number;             // Percentage of portfolio (0-100)
}
```

**JSON Example**:
```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain": "base",
  "total_usd": 12500.50,
  "native_balance": "2500000000000000000",
  "native_usd_value": 5000.00,
  "native_symbol": "ETH",
  "tokens": [
    {
      "token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "symbol": "USDC",
      "name": "USD Coin",
      "decimals": 6,
      "amount": "5000000000",
      "usd_value": 5000.00,
      "usd_price": 1.00,
      "percentage": 40.0
    }
  ],
  "captured_at": "2024-01-15T10:30:00Z",
  "has_value": true
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid chain parameter | Show error: "Invalid chain" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `404` | `NotFoundError` | No wallets found | Show error: "No wallets found. Create a wallet first." |
| `500` | `InternalServerError` | Failed to calculate portfolio | Show error: "Failed to calculate portfolio" + Retry |

---

### 2. Get Portfolio by Address

**Method**: `GET`  
**Endpoint**: `/api/v1/user/portfolio/{wallet_address}`  
**Auth Required**: No (Public)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `wallet_address` | `string` | Yes | Wallet address (0x...) |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Chain to calculate for | `base` |
| `save_snapshot` | `boolean` | No | Save snapshot (only if wallet registered) | `false` |

#### Response

##### Success Response (200 OK)
Returns `PortfolioResponse` (same as GET /me)

**Note**: This endpoint is public and doesn't require authentication. It can be used to view any wallet's portfolio.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid address format | Show error: "Invalid wallet address" |
| `400` | `BadRequestError` | Invalid chain | Show error: "Invalid chain" |
| `500` | `InternalServerError` | Failed to calculate portfolio | Show error: "Failed to calculate portfolio" + Retry |

---

### 3. Get Portfolio History

**Method**: `GET`  
**Endpoint**: `/api/v1/user/portfolio/history`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `days` | `number` | No | Number of days to retrieve | `30` |
| `chain` | `string` | No | Chain filter | All chains |

#### Response

##### Success Response (200 OK)
```typescript
interface PortfolioHistoryResponse {
  history: PortfolioHistoryPoint[];
  total_points: number;
}

interface PortfolioHistoryPoint {
  date: string;                   // ISO 8601 date
  total_usd: number;
  chain: string;
  wallet_address: string;
}
```

**JSON Example**:
```json
{
  "history": [
    {
      "date": "2024-01-15",
      "total_usd": 12500.50,
      "chain": "base",
      "wallet_address": "0x123..."
    },
    {
      "date": "2024-01-14",
      "total_usd": 12000.00,
      "chain": "base",
      "wallet_address": "0x123..."
    }
  ],
  "total_points": 30
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `404` | `NotFoundError` | No history found | Show empty state |
| `503` | `ServiceError` | Service unavailable | Show error + Retry |

---

### 4. Get Portfolio Risk Analysis

**Method**: `GET`  
**Endpoint**: `/api/v1/user/portfolio/risk`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Chain filter | All chains |

#### Response

##### Success Response (200 OK)
```typescript
interface PortfolioRiskResponse {
  overall_risk_score: number;     // 0-1
  risk_level: string;               // "low" | "moderate" | "high" | "critical"
  risk_factors: RiskFactor[];
  recommendations: string[];
  diversification_score: number;   // 0-1
  concentration_risks: ConcentrationRisk[];
}

interface RiskFactor {
  factor: string;
  impact: number;                  // 0-1
  description: string;
  is_critical: boolean;
}

interface ConcentrationRisk {
  asset: string;
  percentage: number;              // 0-100
  risk_level: string;
  recommendation: string;
}
```

**JSON Example**:
```json
{
  "overall_risk_score": 0.35,
  "risk_level": "moderate",
  "risk_factors": [
    {
      "factor": "High concentration in single asset",
      "impact": 0.6,
      "description": "60% of portfolio in ETH",
      "is_critical": false
    }
  ],
  "recommendations": [
    "Diversify across multiple assets",
    "Consider stablecoins for lower risk"
  ],
  "diversification_score": 0.4,
  "concentration_risks": [
    {
      "asset": "ETH",
      "percentage": 60.0,
      "risk_level": "moderate",
      "recommendation": "Reduce to < 40%"
    }
  ]
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `404` | `NotFoundError` | No portfolio found | Show error: "No portfolio data" |
| `503` | `ServiceError` | Service unavailable | Show error + Retry |

---

### 5. Simulate Cascade Failure

**Method**: `POST`  
**Endpoint**: `/api/v1/user/portfolio/risk/simulate-cascade`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface CascadeSimulationRequest {
  protocol_name: string;          // Required: Protocol to simulate failure
  impact_percentage?: number;     // Optional: Impact percentage (0-100)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface CascadeSimulationResponse {
  simulated_portfolio_value: number;
  loss_amount: number;
  loss_percentage: number;
  affected_assets: AffectedAsset[];
  recommendations: string[];
}

interface AffectedAsset {
  asset: string;
  current_value: number;
  simulated_value: number;
  loss: number;
}
```

---

## 🔌 Dashboard Endpoints

### 6. Get Dashboard Insights

**Method**: `GET`  
**Endpoint**: `/api/v1/user/dashboard/insights`  
**Auth Required**: Yes (Bearer Token)

#### Request

No query parameters

#### Response

##### Success Response (200 OK)
```typescript
interface DashboardInsightsResponse {
  insights: DashboardInsight[];
  personalized: boolean;
}

interface DashboardInsight {
  id: string;
  type: string;                   // "risk" | "opportunity" | "warning" | "suggestion"
  title: string;
  message: string;
  action_label?: string;
  action_url?: string;
  severity: string;                // "low" | "medium" | "high" | "critical"
  created_at: string;             // ISO 8601
}
```

**JSON Example**:
```json
{
  "insights": [
    {
      "id": "insight-123",
      "type": "risk",
      "title": "High Concentration Risk",
      "message": "60% of your portfolio is in ETH. Consider diversifying.",
      "action_label": "View Portfolio",
      "action_url": "/portfolio",
      "severity": "medium",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "personalized": true
}
```

---

### 7. Get Dashboard Summary

**Method**: `GET`  
**Endpoint**: `/api/v1/user/dashboard/summary`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface DashboardSummaryResponse {
  total_portfolio_value: number;
  change_24h: number;             // Percentage
  risk_score: number;             // 0-1
  chain_breakdown: ChainBreakdown[];
  position_breakdown: PositionBreakdown[];
}

interface ChainBreakdown {
  chain: string;
  value_usd: number;
  percentage: number;
}

interface PositionBreakdown {
  protocol_name: string;
  position_type: string;          // "supplied" | "borrowed" | "staked"
  amount_usd: number;
  percentage: number;
}
```

---

## 🔌 Market Endpoints

### 8. Get Market Overview

**Method**: `GET`  
**Endpoint**: `/api/v1/user/markets/overview`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `chains` | `string` | No | Comma-separated chain names |
| `risk_filter` | `string` | No | Comma-separated risk levels |

#### Response

##### Success Response (200 OK)
```typescript
interface MarketOverviewResponse {
  top_tokens: TokenMarketData[];
  trending_protocols: ProtocolMarketData[];
  market_trends: MarketTrend[];
  recommendations?: ProtocolRecommendation[];
}

interface TokenMarketData {
  symbol: string;
  name: string;
  price_usd: number;
  market_cap: number;
  volume_24h: number;
  change_24h: number;
  risk_score: number;             // ML risk score (0-1)
  risk_level: string;
}

interface ProtocolMarketData {
  protocol_id: string;
  protocol_name: string;
  tvl: number;
  apy: number;
  risk_score: number;
  trend: string;                  // "up" | "down" | "stable"
}

interface MarketTrend {
  metric: string;
  direction: string;              // "up" | "down" | "stable"
  magnitude: number;
  description: string;
}
```

---

### 9. Get Protocol Yields

**Method**: `GET`  
**Endpoint**: `/api/v1/user/markets/yields`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `chains` | `string` | No | Comma-separated chain names |
| `categories` | `string` | No | Comma-separated categories (lending, staking, farming) |
| `min_apy` | `number` | No | Minimum APY threshold |
| `max_risk` | `number` | No | Maximum risk score threshold (0-1) |

#### Response

##### Success Response (200 OK)
```typescript
interface ProtocolYieldsResponse {
  yields: ProtocolYield[];
}

interface ProtocolYield {
  protocol_id: string;
  protocol_name: string;
  chain: string;
  category: string;
  apy: number;
  risk_score: number;
  risk_adjusted_apy: number;
  tvl: number;
}
```

---

### 10. Get Token Details

**Method**: `GET`  
**Endpoint**: `/api/v1/user/markets/tokens/{token_symbol}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token_symbol` | `string` | Yes | Token symbol (e.g., "ETH", "BTC", "USDC") |

#### Response

##### Success Response (200 OK)
```typescript
interface TokenDetailsResponse {
  symbol: string;
  name: string;
  price_usd: number;
  market_cap: number;
  volume_24h: number;
  change_24h: number;
  change_7d: number;
  change_30d: number;
  risk_score: number;
  risk_level: string;
  chains: string[];
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `404` | `NotFoundError` | Token not found | Show error: "Token not found" |

---

### 11. Get Token History

**Method**: `GET`  
**Endpoint**: `/api/v1/user/markets/tokens/{token_symbol}/history`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token_symbol` | `string` | Yes | Token symbol |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `timeframe` | `string` | No | Time range | `7d` |

**Valid Timeframe Values**: `1h`, `24h`, `7d`, `30d`

#### Response

##### Success Response (200 OK)
```typescript
interface TokenHistoryResponse {
  history: PricePoint[];
}

interface PricePoint {
  timestamp: string;               // ISO 8601
  price_usd: number;
  volume_24h: number;
}
```

---

## 🔌 Comparison Endpoints

### 12. Compare Protocols

**Method**: `POST`  
**Endpoint**: `/api/v1/user/comparison/protocols`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface CompareProtocolsRequest {
  protocol_ids: string[];         // Required: 2-5 protocol IDs (UUIDs)
  dimensions?: string[];         // Optional: Comparison dimensions
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `protocol_ids` | `string[]` | **Yes** | Protocol UUIDs | 2-5 items |
| `dimensions` | `string[]` | No | Comparison dimensions | "risk", "yield", "security", "network", "all" |

**JSON Example**:
```json
{
  "protocol_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ],
  "dimensions": ["risk", "yield", "security"]
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ProtocolComparisonResponse {
  protocols: ProtocolComparisonData[];
  comparison_matrix: ComparisonMatrix;
  winners_by_dimension: DimensionWinner[];
  tradeoffs: Tradeoff[];
  recommendation: string;          // AI-powered recommendation
}

interface ProtocolComparisonData {
  protocol_id: string;
  protocol_name: string;
  metrics: {
    risk_score: number;
    yield_apy: number;
    security_score: number;
    network_score: number;
  };
}

interface ComparisonMatrix {
  dimensions: string[];
  scores: DimensionScore[];
}

interface DimensionScore {
  dimension: string;
  protocol_scores: { [protocol_id: string]: number };
}

interface DimensionWinner {
  dimension: string;
  winner_protocol_id: string;
  winner_protocol_name: string;
  score: number;
}

interface Tradeoff {
  dimension: string;
  description: string;
  impact: string;                 // "low" | "medium" | "high"
}
```

---

## 🔌 Notification Endpoints

### 13. Get Notifications

**Method**: `GET`  
**Endpoint**: `/api/v1/notifications`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `page` | `number` | No | Page number | `1` |
| `per_page` | `number` | No | Items per page | `10` |

#### Response

##### Success Response (200 OK)
```typescript
interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  per_page: number;
}

interface Notification {
  id: string;
  type: string;                   // "price_alert" | "risk_warning" | "opportunity" | etc.
  title: string;
  message: string;
  read: boolean;
  created_at: string;              // ISO 8601
  action_url?: string;
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error + Retry |

---

---

## 🔌 Graph Visualization Endpoints

### 14. Get Graph Nodes

**Method**: `GET`  
**Endpoint**: `/api/v1/user/graph/visualization/nodes`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `node_type` | `string` | No | Filter by node type | All types |
| `min_importance` | `number` | No | Minimum importance (0-1) | `0.0` |
| `limit` | `number` | No | Max results | `100` |

**Valid Node Types**: `protocol`, `token`, etc.

#### Response

##### Success Response (200 OK)
```typescript
interface GraphNode {
  id: string;
  label: string;
  type: string;
  importance: number;             // 0-1
  connections: number;
  metadata: object;
}
```

---

### 15. Get Graph Edges

**Method**: `GET`  
**Endpoint**: `/api/v1/user/graph/visualization/edges`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `edge_type` | `string` | No | Filter by edge type | All types |
| `min_weight` | `number` | No | Minimum weight (0-1) | `0.0` |
| `limit` | `number` | No | Max results | `500` |

#### Response

##### Success Response (200 OK)
```typescript
interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;                 // 0-1
  metadata: object;
}
```

---

### 16. Get Subgraph

**Method**: `GET`  
**Endpoint**: `/api/v1/user/graph/visualization/subgraph`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `entity` | `string` | **Yes** | Entity ID (protocol, token, etc.) |
| `depth` | `number` | No | Traversal depth | `2` |

#### Response

##### Success Response (200 OK)
```typescript
interface SubgraphResponse {
  center_node: GraphNode;
  nodes: GraphNode[];
  edges: GraphEdge[];
  depth: number;
}
```

---

## 🔌 Search Endpoints

### 17. Get Search History

**Method**: `GET`  
**Endpoint**: `/api/v1/user/search/history`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `10` |
| `search_type` | `string` | No | Filter by type | All types |

**Valid Search Types**: `graphrag`, `protocol`, `token`, `general`

#### Response

##### Success Response (200 OK)
```typescript
interface SearchHistoryResponse {
  history: SearchHistoryEntry[];
  total: number;
}

interface SearchHistoryEntry {
  id: string;                     // UUID
  query: string;
  type: string;
  results_count: number;
  filters: object;
  created_at: string;             // ISO 8601
}
```

---

### 18. Get Search Suggestions

**Method**: `GET`  
**Endpoint**: `/api/v1/user/search/suggestions`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `prefix` | `string` | **Yes** | Search prefix (min 1 char) |
| `limit` | `number` | No | Max suggestions | `5` |

#### Response

##### Success Response (200 OK)
```typescript
interface SearchSuggestionsResponse {
  suggestions: string[];
  prefix: string;
}
```

---

### 19. Get Popular Queries

**Method**: `GET`  
**Endpoint**: `/api/v1/user/search/popular`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max queries | `5` |
| `days` | `number` | No | Look back period | `30` |

#### Response

##### Success Response (200 OK)
```typescript
interface PopularQueriesResponse {
  popular_queries: PopularQuery[];
  period_days: number;
}

interface PopularQuery {
  query: string;
  count: number;
  last_searched: string;            // ISO 8601
}
```

---

### 20. Delete Search Entry

**Method**: `DELETE`  
**Endpoint**: `/api/v1/user/search/history/{search_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Search deleted"
}
```

---

### 21. Clear Search History

**Method**: `DELETE`  
**Endpoint**: `/api/v1/user/search/history`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `search_type` | `string` | No | Clear only specific type |

#### Response

##### Success Response (200 OK)
```json
{
  "success": true,
  "cleared_count": 42,
  "message": "Cleared 42 searches"
}
```

---

### 22. Get Search Analytics

**Method**: `GET`  
**Endpoint**: `/api/v1/user/search/analytics`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `days` | `number` | No | Look back period | `30` |

#### Response

##### Success Response (200 OK)
```typescript
interface SearchAnalyticsResponse {
  analytics: {
    total_searches: number;
    searches_by_type: { [type: string]: number };
    most_searched_terms: string[];
    average_results_per_search: number;
  };
  period_days: number;
}
```

---

## 🔌 Graph Search Endpoints (GraphRAG)

### 23. Hybrid Search

**Method**: `POST`  
**Endpoint**: `/api/v1/user/graph/search/hybrid`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface HybridSearchRequest {
  query: string;                   // Required: Search query
  limit?: number;                  // Optional: Max results (default: 10)
  include_risks?: boolean;        // Optional: Include risk analysis
  include_dependencies?: boolean;  // Optional: Include dependencies
  similarity_threshold?: number;   // Optional: Min similarity (0-1, default: 0.5)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface HybridSearchResponse {
  query: string;
  results: HybridSearchResult[];
  total: number;
  metadata: object;
}

interface HybridSearchResult {
  protocol_id: string;
  protocol_name: string;
  score: number;                   // Combined score
  vector_similarity: number;       // 0-1
  graph_importance: number;       // 0-1
  context: ProtocolContext;
  risk_info?: RiskInfo;
}

interface ProtocolContext {
  tvl: number;
  category: string;
  dependent_count: number;
  degree: number;
  audit_count: number;
  chain_count: number;
  dependencies?: string[];
}

interface RiskInfo {
  risk_score: number;
  direct_risks: string[];
  systemic_risks: string[];
  top_recommendation?: string;
}
```

---

### 24. Find Similar Protocols

**Method**: `POST`  
**Endpoint**: `/api/v1/user/graph/search/similar`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SimilarProtocolsRequest {
  protocol_id: string;            // Required: Reference protocol UUID
  limit?: number;                  // Optional: Max results (default: 10)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface SimilarProtocolsResponse {
  reference_protocol_id: string;
  results: HybridSearchResult[];
  total: number;
}
```

---

### 25. Contextual Search

**Method**: `POST`  
**Endpoint**: `/api/v1/user/graph/search/contextual`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ContextualSearchRequest {
  query: string;                   // Required: Search query
  user_preferences?: object;       // Optional: User preferences
  limit?: number;                  // Optional: Max results
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ContextualSearchResponse {
  query: string;
  results: HybridSearchResult[];
  personalized: boolean;
  recommendations: string[];
}
```

---

## 🔌 Graph Analytics Endpoints

### 26. Get Graph Analytics Overview

**Method**: `GET`  
**Endpoint**: `/api/v1/user/graph/analytics/overview`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface GraphAnalyticsResponse {
  overview: {
    total_nodes: number;
    total_edges: number;
    protocols_count: number;
    tokens_count: number;
    last_updated: string;
  };
  top_protocols: TopProtocol[];
  category_distribution: { [category: string]: number };
  chain_distribution: { [chain: string]: number };
}

interface TopProtocol {
  name: string;
  slug: string;
  tvl: number;
  category: string;
  change_24h: number;
}
```

---

### 27. Validate Graph

**Method**: `POST`  
**Endpoint**: `/api/v1/user/graph/analytics/validate`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface GraphValidationResponse {
  timestamp: string;               // ISO 8601
  checks: { [check_name: string]: ValidationIssue };
  total_issues: number;
  is_valid: boolean;
}

interface ValidationIssue {
  passed: boolean;
  issues: string[];
  severity: string;
}
```

---

### 28. Generate Embeddings

**Method**: `POST`  
**Endpoint**: `/api/v1/user/graph/analytics/embeddings/generate`  
**Auth Required**: Yes (Bearer Token - Admin only)

#### Request

##### Request Body
```typescript
interface EmbeddingGenerationRequest {
  limit?: number;                  // Optional: Max protocols (default: 100)
  force_regenerate?: boolean;      // Optional: Force regenerate existing
}
```

#### Response

##### Success Response (202 Accepted)
```typescript
interface EmbeddingGenerationResponse {
  processed: number;
  skipped: number;
  errors: number;
  message: string;
}
```

**Note**: This is a long-running operation. Consider running as a background task.

---

## 🔌 Graph Monitoring Endpoints

### 29. Get Cache Statistics

**Method**: `GET`  
**Endpoint**: `/api/v1/user/graph/monitoring/cache-stats`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface PerformanceMetrics {
  cache_stats: {
    graph_cache_keys: number;
    total_keys: number;
    hits: number;
    misses: number;
    hit_rate: number;              // 0-1
  };
  message: string;
}
```

---

### 30. Clear Graph Cache

**Method**: `POST`  
**Endpoint**: `/api/v1/user/graph/monitoring/cache/clear`  
**Auth Required**: Yes (Bearer Token - Admin only)

#### Response

##### Success Response (200 OK)
```json
{
  "message": "Graph cache cleared successfully",
  "status": "ok"
}
```

---

## 🔌 Metrics Endpoints

### 31. Track Event

**Method**: `POST`  
**Endpoint**: `/api/v1/metrics/track`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface TrackEventRequest {
  event_type: string;              // Required: Event type (e.g., "login", "swap_completed")
  event_category?: string;         // Optional: Category (e.g., "auth", "trading")
  properties?: object;             // Optional: Event-specific properties
  device_type?: string;            // Optional: "mobile" | "desktop" | "tablet"
  platform?: string;               // Optional: "ios" | "android" | "web"
  app_version?: string;            // Optional: App version
  session_id?: string;            // Optional: Session identifier
}
```

**Common Event Types**:
- **Authentication**: `login`, `logout`, `signup`, `wallet_connected`
- **Trading**: `swap_initiated`, `swap_completed`, `swap_failed`
- **Earn**: `earn_deposit_initiated`, `earn_deposit_completed`
- **Save/DCA**: `save_schedule_created`, `save_execution`
- **AI**: `ai_chat_started`, `ai_message_sent`
- **Subscription**: `subscription_started`, `subscription_cancelled`

#### Response

##### Success Response (201 Created)
```typescript
interface TrackEventResponse {
  success: boolean;
  event_id: number;
  message: string;                 // "Event tracked successfully"
}
```

---

### 32. Get Available Event Types

**Method**: `GET`  
**Endpoint**: `/api/v1/metrics/event-types`  
**Auth Required**: No (Public)

#### Response

##### Success Response (200 OK)
```typescript
interface EventTypesResponse {
  auth: string[];
  navigation: string[];
  trading: string[];
  earn: string[];
  save: string[];
  perpetuals: string[];
  ai: string[];
  subscription: string[];
  bitcoin: string[];
  error: string[];
}
```

---

### 33. Get My Metrics Summary

**Method**: `GET`  
**Endpoint**: `/api/v1/metrics/me`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface UserMetricsSummaryResponse {
  user_id: number;
  total_events: number;
  first_event_at?: string;         // ISO 8601
  last_event_at?: string;          // ISO 8601
  events_by_category: { [category: string]: number };
  events_by_type: { [type: string]: number };
  devices_used: string[];
  platforms_used: string[];
}
```

---

### 34. Get My Events

**Method**: `GET`  
**Endpoint**: `/api/v1/metrics/me/events`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `event_type` | `string` | No | Filter by event type | All types |
| `event_category` | `string` | No | Filter by category | All categories |
| `limit` | `number` | No | Max results | `50` |
| `offset` | `number` | No | Pagination offset | `0` |

#### Response

##### Success Response (200 OK)
```typescript
interface EventListResponse {
  events: UserEvent[];
  total: number;
  limit: number;
  offset: number;
}

interface UserEvent {
  id: number;
  event_type: string;
  event_category?: string;
  properties: object;
  device_type?: string;
  platform?: string;
  created_at: string;              // ISO 8601
}
```

---

## 🔌 WebSocket Connections

### 1. Graph WebSocket

**Endpoint**: `ws://localhost:8000/api/v1/ws/graph`  
**Auth Required**: Yes (JWT Token in Query Parameter)  
**Purpose**: Real-time updates for graph changes, protocol updates, and risk alerts

#### Connection

**Connection URL**:
```
ws://localhost:8000/api/v1/ws/graph?token={jwt_token}
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | `string` | **Yes** | JWT authentication token |

#### Client-to-Server Messages

##### Subscribe to Channel
```typescript
interface SubscribeMessage {
  action: "subscribe";
  channel: string;  // "protocol:{protocol_id}" | "risk:alerts" | "graph:changes" | "all"
}
```

**Channels**:
- `protocol:{protocol_id}` - Updates for specific protocol (e.g., `protocol:aave-id`)
- `risk:alerts` - Risk alerts for any protocol
- `graph:changes` - Graph structure changes
- `all` - All updates

**JSON Example**:
```json
{
  "action": "subscribe",
  "channel": "protocol:aave-id"
}
```

##### Unsubscribe from Channel
```typescript
interface UnsubscribeMessage {
  action: "unsubscribe";
  channel: string;
}
```

**JSON Example**:
```json
{
  "action": "unsubscribe",
  "channel": "protocol:aave-id"
}
```

##### Heartbeat (Ping)
```typescript
interface PingMessage {
  action: "ping";
}
```

**JSON Example**:
```json
{
  "action": "ping"
}
```

#### Server-to-Client Messages

##### Protocol Update
```typescript
interface ProtocolUpdateMessage {
  type: "protocol:update";
  protocol_id: string;
  protocol_name: string;
  field: string;              // Field that changed (e.g., "tvl", "apy")
  old_value: number | string;
  new_value: number | string;
  timestamp: string;           // ISO 8601
  source: "graph";
}
```

**JSON Example**:
```json
{
  "type": "protocol:update",
  "protocol_id": "aave-id",
  "protocol_name": "Aave",
  "field": "tvl",
  "old_value": 5000000000,
  "new_value": 5500000000,
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "graph"
}
```

##### Risk Alert
```typescript
interface RiskAlertMessage {
  type: "risk:alert";
  protocol_id: string;
  protocol_name: string;
  risk_type: string;          // "liquidation", "slippage", "smart_contract", etc.
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  data: object;
  timestamp: string;           // ISO 8601
  source: "graph";
}
```

**JSON Example**:
```json
{
  "type": "risk:alert",
  "protocol_id": "aave-id",
  "protocol_name": "Aave",
  "risk_type": "liquidation",
  "severity": "high",
  "message": "High liquidation risk detected",
  "data": {
    "health_factor": 1.2,
    "threshold": 1.5
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "graph"
}
```

##### Graph Structure Change
```typescript
interface GraphChangeMessage {
  type: "graph:changes";
  change_type: "node_added" | "node_updated" | "node_removed" | "edge_added" | "edge_removed";
  node_id?: string;
  edge_id?: string;
  data: object;
  timestamp: string;           // ISO 8601
  source: "graph";
}
```

##### Subscription Confirmed
```typescript
interface SubscribedMessage {
  type: "subscribed";
  channel: string;
}
```

##### Unsubscribed Confirmed
```typescript
interface UnsubscribedMessage {
  type: "unsubscribed";
  channel: string;
}
```

##### Heartbeat Response (Pong)
```typescript
interface PongMessage {
  type: "pong";
}
```

##### Error Message
```typescript
interface ErrorMessage {
  type: "error";
  message: string;
}
```

#### Connection Lifecycle

1. **Connect**: Client connects with JWT token
2. **Subscribe**: Client subscribes to desired channels
3. **Receive Updates**: Server broadcasts updates to subscribed channels
4. **Heartbeat**: Client sends ping every 30 seconds
5. **Disconnect**: Client closes connection or server disconnects on error

#### Error Handling

**Connection Errors**:
- Invalid token → Connection rejected (code 1008)
- Network error → Client should reconnect
- Server error → Connection closed (code 1011)

**Message Errors**:
- Unknown action → Server sends error message
- Invalid channel → Server sends error message

---

### 2. Analytics WebSocket

**Endpoint**: `ws://localhost:8000/api/v1/analytics/ws/{user_id}`  
**Auth Required**: Yes (JWT Token in Query Parameter)  
**Purpose**: Real-time analytics streaming for dashboards (metrics, alerts, performance, costs, quality)

#### Connection

**Connection URL**:
```
ws://localhost:8000/api/v1/analytics/ws/{user_id}?token={jwt_token}
```

**Path Parameters**:
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `user_id` | `string` | **Yes** | User identifier |

**Query Parameters**:
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | `string` | **Yes** | JWT authentication token |

#### Client-to-Server Messages

##### Subscribe to Updates
```typescript
interface SubscribeMessage {
  type: "subscribe";
  subscriptions: string[];  // ["metrics", "alerts", "performance", "costs", "quality"]
}
```

**Subscription Types**:
- `metrics` - Real-time metrics updates
- `alerts` - All alert types (cost, performance, quality)
- `performance` - Performance-related alerts only
- `costs` - Cost-related alerts only
- `quality` - Quality-related alerts only

**JSON Example**:
```json
{
  "type": "subscribe",
  "subscriptions": ["metrics", "alerts", "performance"]
}
```

##### Unsubscribe
```typescript
interface UnsubscribeMessage {
  type: "unsubscribe";
  subscriptions: string[];
}
```

**JSON Example**:
```json
{
  "type": "unsubscribe",
  "subscriptions": ["performance"]
}
```

##### Request Snapshot
```typescript
interface RequestSnapshotMessage {
  type: "request_snapshot";
  start_date?: string;        // ISO 8601, optional
  end_date?: string;          // ISO 8601, optional
}
```

**JSON Example**:
```json
{
  "type": "request_snapshot",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-15T23:59:59Z"
}
```

##### Heartbeat (Ping)
```typescript
interface PingMessage {
  type: "ping";
}
```

#### Server-to-Client Messages

##### Metrics Update
```typescript
interface MetricsUpdateMessage {
  type: "metrics_update";
  data: {
    conversation_id: string;
    total_cost_usd: number;
    avg_response_time_ms: number;
    total_messages: number;
    total_tokens: number;
    quality_score?: number;
  };
  timestamp: string;          // ISO 8601
}
```

**JSON Example**:
```json
{
  "type": "metrics_update",
  "data": {
    "conversation_id": "uuid-123",
    "total_cost_usd": 5.23,
    "avg_response_time_ms": 1234.5,
    "total_messages": 42,
    "total_tokens": 15000,
    "quality_score": 0.85
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### Cost Alert
```typescript
interface CostAlertMessage {
  type: "cost_alert";
  severity: "info" | "warning" | "error";
  message: string;
  data: {
    conversation_id?: string;
    cost_usd: number;
    threshold_usd: number;
  };
  timestamp: string;          // ISO 8601
}
```

**JSON Example**:
```json
{
  "type": "cost_alert",
  "severity": "warning",
  "message": "Conversation cost exceeded threshold",
  "data": {
    "conversation_id": "uuid-123",
    "cost_usd": 12.50,
    "threshold_usd": 10.00
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

##### Performance Alert
```typescript
interface PerformanceAlertMessage {
  type: "performance_alert";
  severity: "info" | "warning" | "error";
  message: string;
  data: {
    conversation_id?: string;
    response_time_ms: number;
    threshold_ms: number;
    p95_response_time_ms?: number;
  };
  timestamp: string;          // ISO 8601
}
```

##### Quality Alert
```typescript
interface QualityAlertMessage {
  type: "quality_alert";
  severity: "info" | "warning" | "error";
  message: string;
  data: {
    conversation_id?: string;
    quality_score: number;
    threshold: number;
  };
  timestamp: string;          // ISO 8601
}
```

##### Snapshot Response
```typescript
interface SnapshotMessage {
  type: "snapshot";
  data: {
    aggregate: {
      total_cost_usd: number;
      total_conversations: number;
      avg_response_time_ms: number;
    };
    daily: Array<{
      date: string;
      cost_usd: number;
      conversations: number;
    }>;
    agent_stats: Record<string, {
      cost_usd: number;
      conversations: number;
      avg_response_time_ms: number;
    }>;
    cost_breakdown: {
      model_costs: Record<string, number>;
      api_costs: Record<string, number>;
    };
  };
  timestamp: string;          // ISO 8601
}
```

##### Heartbeat Response (Pong)
```typescript
interface PongMessage {
  type: "pong";
}
```

##### Error Message
```typescript
interface ErrorMessage {
  type: "error";
  message: string;
  code?: string;
}
```

#### Connection Lifecycle

1. **Connect**: Client connects with user_id and JWT token
2. **Subscribe**: Client subscribes to desired analytics types
3. **Receive Updates**: Server streams real-time metrics and alerts
4. **Request Snapshot**: Client can request historical snapshot
5. **Heartbeat**: Client sends ping every 30 seconds
6. **Disconnect**: Client closes connection or server disconnects on error

#### Error Handling

**Connection Errors**:
- Invalid token → Connection rejected (code 1008)
- Invalid user_id → Connection rejected (code 1008)
- Network error → Client should reconnect with exponential backoff

**Message Errors**:
- Invalid subscription type → Server sends error message
- Invalid date range → Server sends error message

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
   - No wallets or portfolio data
   - **Action**: Show empty state or error message

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

- **Backend Controller**: `src/app/presentation/http/controllers/portfolio/router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/markets/router.py`
- **Domain Entities**: `src/app/domain/portfolio/entities/user_portfolio.py`
- **Application Services**: `src/app/application/portfolio/`
- **Frontend Implementation**: `02-Dashboard-and-Discovery/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready

# FRONTEND_ADMIN_LLM_REQUESTS

## Admin LLM Requests Module

**User Type:** Admin  
**Module:** Request Logs & Analysis  
**Route:** `/admin/llm/requests`  
**Access Level:** Read (All) | Export (Admin)

---

## 📋 Module Overview

### Title
**Request Logs** - LLM Request History & Analysis

### Description
Detailed logging interface for all LLM requests across the platform. Enables administrators to inspect individual requests, analyze patterns, debug failures, and export data for compliance and optimization purposes.

### Key Capabilities
- Real-time request feed with filtering
- Detailed request/response inspection
- Error analysis and debugging
- Token usage and cost tracking per request
- Export capabilities for compliance
- Request replay for debugging

---

## 👤 User Stories

### US-ADMIN-REQ-001: View Request Stream
**As a** platform administrator  
**I want to** see a live stream of LLM requests  
**So that** I can monitor system activity in real-time

**Acceptance Criteria:**
- Real-time feed with auto-scroll option
- Pause/resume feed capability
- Color-coded by status (success, error, timeout)
- Basic info visible: timestamp, model, agent, status, latency
- Click to expand for details

### US-ADMIN-REQ-002: Filter and Search Requests
**As a** platform administrator  
**I want to** filter and search requests  
**So that** I can find specific requests quickly

**Acceptance Criteria:**
- Filter by date range, provider, model, agent, status
- Search by request ID, user ID, or content
- Save filter presets
- Combine multiple filters
- Clear all filters with one click

### US-ADMIN-REQ-003: Inspect Request Details
**As a** platform administrator  
**I want to** see full request and response details  
**So that** I can debug issues and understand behavior

**Acceptance Criteria:**
- Full request payload (sanitized)
- Full response content
- Token breakdown (input/output/total)
- Timing breakdown (queue, inference, total)
- Provider routing path
- Associated user/session context

### US-ADMIN-REQ-004: Analyze Errors
**As a** platform administrator  
**I want to** understand why requests failed  
**So that** I can identify and fix issues

**Acceptance Criteria:**
- Error message and stack trace
- Retry attempts shown
- Fallback provider path
- Similar error grouping
- Link to circuit breaker if triggered

### US-ADMIN-REQ-005: Export Request Data
**As a** platform administrator  
**I want to** export request logs  
**So that** I can perform offline analysis or compliance reporting

**Acceptance Criteria:**
- Export as CSV or JSON
- Date range selection
- Field selection
- PII redaction option
- Background export for large datasets
- Download notification when ready

---

## 🖼️ Views & Wireframes

### View 1: Request Log Stream

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📋 LLM Requests                                        [⏸️ Pause] [📥 Export]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Date: [Last 24h ▼]  Provider: [All ▼]  Model: [All ▼]  Status: [All ▼]        ││
│  │ Agent: [All ▼]  [🔍 Search by ID, user, or content...]        [Clear Filters]  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📊 45,230 Requests    ✅ 44,102 Success (97.5%)    ❌ 1,128 Errors (2.5%)     ││
│  │     Last 24 hours          Avg latency: 890ms           Top: Rate limit (42%)  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ TIME        │ ID          │ MODEL              │ AGENT     │ STATUS │ LATENCY  ││
│  ├─────────────┼─────────────┼────────────────────┼───────────┼────────┼──────────┤│
│  │ 14:32:45    │ req_8a7b... │ gemini-1.5-pro     │ SwapAgent │ ✅ 200 │ 823ms    ││
│  │ 14:32:44    │ req_9c2d... │ gemini-1.5-flash   │ Researcher│ ✅ 200 │ 412ms    ││
│  │ 14:32:43    │ req_1e4f... │ llama-3.1-405b     │ Trading   │ ❌ 429 │ 2,100ms  ││
│  │             │             │ ↳ claude-3-sonnet  │           │ ✅ 200 │ +980ms   ││
│  │ 14:32:42    │ req_5g6h... │ gemini-1.5-pro     │ Portfolio │ ✅ 200 │ 756ms    ││
│  │ 14:32:41    │ req_7i8j... │ mixtral-8x22b      │ SwapAgent │ ⏱️ TO  │ 30,000ms ││
│  │             │             │ ↳ gemini-flash     │           │ ✅ 200 │ +380ms   ││
│  │ 14:32:40    │ req_2k3l... │ claude-3-sonnet    │ Researcher│ ✅ 200 │ 1,120ms  ││
│  │ 14:32:39    │ req_4m5n... │ gemini-1.5-pro     │ SwapAgent │ ✅ 200 │ 845ms    ││
│  │ 14:32:38    │ req_6o7p... │ qwen2-72b          │ Trading   │ ❌ 500 │ 450ms    ││
│  │ 14:32:37    │ req_8q9r... │ gemini-1.5-flash   │ Portfolio │ ✅ 200 │ 398ms    ││
│  └─────────────┴─────────────┴────────────────────┴───────────┴────────┴──────────┘│
│                                                                                      │
│  ● Live updating (2.3 req/sec)                        [Load More] [Jump to Time]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Request Detail View

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📋 Request Details: req_8a7b3c2d                       [🔄 Replay] [📋 Copy ID]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Request]  [Response]  [Timing]  [Context]                             │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  OVERVIEW                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐    │  │
│  │  │ Request ID      │ Status          │ Total Latency   │ Cost            │    │  │
│  │  │ req_8a7b3c2d    │ ✅ Success      │ 823ms           │ $0.0082         │    │  │
│  │  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘    │  │
│  │                                                                               │  │
│  │  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐    │  │
│  │  │ Timestamp       │ Provider        │ Model           │ Agent           │    │  │
│  │  │ Dec 1, 14:32:45 │ 🔷 Vertex AI    │ gemini-1.5-pro  │ SwapAgent       │    │  │
│  │  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘    │  │
│  │                                                                               │  │
│  │  ROUTING PATH                                                                │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Request → Vertex AI (gemini-1.5-pro) → ✅ Success                    │    │  │
│  │  │           Ranking: #1 for SwapAgent (Score: 92.5)                     │    │  │
│  │  └───────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                               │  │
│  │  TOKEN USAGE                                                                 │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Input: 1,245 tokens ($0.0019)                                        │    │  │
│  │  │  Output: 420 tokens ($0.0063)                                         │    │  │
│  │  │  ────────────────────────────────────────────                         │    │  │
│  │  │  Total: 1,665 tokens ($0.0082)                                        │    │  │
│  │  └───────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  REQUEST PAYLOAD                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  {                                                                           │  │
│  │    "messages": [                                                             │  │
│  │      {                                                                       │  │
│  │        "role": "system",                                                     │  │
│  │        "content": "You are a DeFi swap assistant..."                        │  │
│  │      },                                                                      │  │
│  │      {                                                                       │  │
│  │        "role": "user",                                                       │  │
│  │        "content": "I want to swap 1 ETH for USDC on Arbitrum"              │  │
│  │      }                                                                       │  │
│  │    ],                                                                        │  │
│  │    "temperature": 0.7,                                                       │  │
│  │    "max_tokens": 2048                                                        │  │
│  │  }                                                         [📋 Copy] [▼]    │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RESPONSE                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  I'll help you swap 1 ETH for USDC on Arbitrum. Let me find the best        │  │
│  │  route for you...                                                            │  │
│  │                                                                               │  │
│  │  Based on current prices and liquidity:                                      │  │
│  │  • 1 ETH = ~2,145 USDC                                                       │  │
│  │  • Best route: 1inch aggregator                                              │  │
│  │  • Estimated gas: ~$0.15                                                     │  │
│  │  • Slippage tolerance: 0.5%                                                  │  │
│  │                                                                               │  │
│  │  Would you like me to execute this swap?                    [📋 Copy] [▼]    │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Error Analysis View

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ❌ Error Details: req_1e4f5g6h                                             [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ERROR SUMMARY                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Error Type: Rate Limit Exceeded (429)                                       │  │
│  │  Provider: 🟣 DeepInfra                                                      │  │
│  │  Model: llama-3.1-405b                                                       │  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Error Message:                                                          │  │  │
│  │  │ "Rate limit exceeded. Please retry after 60 seconds."                   │  │  │
│  │  │                                                                         │  │  │
│  │  │ Provider Response:                                                      │  │  │
│  │  │ { "error": { "code": 429, "message": "Too many requests" } }           │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RETRY & FALLBACK PATH                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Attempt 1: DeepInfra (llama-3.1-405b)                                       │  │
│  │  ├─ Status: ❌ 429 Rate Limit                                                │  │
│  │  ├─ Latency: 2,100ms                                                         │  │
│  │  └─ Action: Fallback to next provider                                        │  │
│  │                                                                               │  │
│  │  Attempt 2: AWS Bedrock (claude-3-sonnet)  [FALLBACK]                        │  │
│  │  ├─ Status: ✅ 200 Success                                                   │  │
│  │  ├─ Latency: 980ms                                                           │  │
│  │  └─ Action: Request completed                                                │  │
│  │                                                                               │  │
│  │  Total Latency: 3,080ms (2,100ms + 980ms)                                    │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SIMILAR ERRORS (Last 24h)                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  42 similar rate limit errors from DeepInfra                                 │  │
│  │  Peak: 14:30-14:35 (28 errors)                                               │  │
│  │  [View All Similar →]                                                        │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Requests

```typescript
// GET /admin/llm/requests
// Get paginated request logs

interface GetRequestsRequest {
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
  provider_id?: string;
  model_id?: string;
  agent_type?: string;
  status?: 'success' | 'error' | 'timeout';
  search?: string;
}

interface GetRequestsResponse {
  success: true;
  data: {
    requests: LLMRequest[];
    pagination: {
      page: number;
      page_size: number;
      total: number;
      total_pages: number;
    };
    summary: {
      total_requests: number;
      success_count: number;
      error_count: number;
      avg_latency_ms: number;
    };
  };
}

interface LLMRequest {
  id: string;
  timestamp: string;
  provider_id: string;
  provider_name: string;
  model_id: string;
  model_name: string;
  agent_type: string;
  status: 'success' | 'error' | 'timeout';
  status_code: number;
  latency_ms: number;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  cost_usd: number;
  error_message?: string;
  had_fallback: boolean;
  fallback_chain?: FallbackAttempt[];
  user_id?: string;
  session_id?: string;
}

interface FallbackAttempt {
  provider_name: string;
  model_name: string;
  status: string;
  status_code: number;
  latency_ms: number;
  error_message?: string;
}
```

### Get Request Detail

```typescript
// GET /admin/llm/requests/{id}
// Get full request details

interface GetRequestDetailResponse {
  success: true;
  data: {
    request: LLMRequest;
    payload: {
      messages: Array<{
        role: string;
        content: string;
      }>;
      temperature?: number;
      max_tokens?: number;
      // ... other params
    };
    response: {
      content: string;
      finish_reason: string;
      usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
      };
    };
    timing: {
      queue_ms: number;
      inference_ms: number;
      network_ms: number;
      total_ms: number;
    };
    context: {
      user_id?: string;
      session_id?: string;
      project_id?: string;
      ip_address?: string;
    };
    routing: {
      selected_model: string;
      ranking_score: number;
      ranking_position: number;
    };
  };
}
```

### Export Requests

```typescript
// POST /admin/llm/requests/export
// Export request logs

interface ExportRequestsRequest {
  start_date: string;
  end_date: string;
  format: 'csv' | 'json';
  fields?: string[];
  redact_pii?: boolean;
  filters?: {
    provider_id?: string;
    status?: string;
  };
}

interface ExportRequestsResponse {
  success: true;
  data: {
    export_id: string;
    estimated_rows: number;
    estimated_size_mb: number;
    status: 'processing';
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface RequestsModuleState {
  requests: LLMRequest[];
  selectedRequest: GetRequestDetailResponse['data'] | null;
  
  loading: {
    list: boolean;
    detail: boolean;
    export: boolean;
  };
  
  streaming: boolean;
  streamPaused: boolean;
  
  filters: {
    dateRange: { start: string; end: string };
    provider: string | null;
    model: string | null;
    agent: string | null;
    status: string | null;
    search: string;
  };
  
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  
  summary: RequestsSummary | null;
  
  detailModalOpen: boolean;
  exportModalOpen: boolean;
}
```

---

## 🎨 Component Specifications

### RequestTable

```typescript
interface RequestTableProps {
  requests: LLMRequest[];
  onSelectRequest: (id: string) => void;
  selectedId?: string;
  streaming?: boolean;
  loading?: boolean;
}
```

### RequestDetailModal

```typescript
interface RequestDetailModalProps {
  request: GetRequestDetailResponse['data'];
  onClose: () => void;
  onReplay: () => void;
}
```

### FallbackChainVisualization

```typescript
interface FallbackChainVisualizationProps {
  attempts: FallbackAttempt[];
  finalStatus: string;
}
```

### RequestStreamIndicator

```typescript
interface RequestStreamIndicatorProps {
  streaming: boolean;
  paused: boolean;
  requestsPerSecond: number;
  onTogglePause: () => void;
}
```

---

## 🎬 Motion Design

```typescript
const requestsAnimations = {
  newRequestSlide: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.2 }
  },
  
  statusPulse: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3 }
  },
  
  fallbackArrow: {
    pathLength: [0, 1],
    transition: { duration: 0.5 }
  },
  
  streamIndicator: {
    opacity: [1, 0.5, 1],
    transition: { duration: 1, repeat: Infinity }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const requestsShortcuts = {
  'space': 'Toggle stream pause',
  'mod+e': 'Export requests',
  'mod+f': 'Focus search',
  'enter': 'View request detail',
  'escape': 'Close detail modal',
  'j/k': 'Navigate requests',
};
```

---

## ⚠️ Error Handling

```typescript
const requestsErrorCodes = {
  REQ_LOAD_001: 'Failed to load requests',
  REQ_DETAIL_001: 'Request not found',
  REQ_EXPORT_001: 'Export failed',
  REQ_EXPORT_002: 'Date range too large',
  REQ_STREAM_001: 'WebSocket connection lost',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Request Logs*

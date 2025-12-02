# FRONTEND_ADMIN_LLM_PROVIDERS

## Admin LLM Providers Management Module

**User Type:** Admin  
**Module:** Providers Management  
**Route:** `/admin/llm/providers`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Providers Management** - LLM Provider Configuration & Health

### Description
Comprehensive management interface for configuring and monitoring LLM providers (Vertex AI, DeepInfra, AWS Bedrock). Enables administrators to configure provider settings, manage priority ordering, monitor health status, and perform diagnostic operations.

### Key Capabilities
- View all configured providers with real-time health status
- Configure provider settings (API keys, endpoints, rate limits)
- Adjust provider priority for failover ordering
- Enable/disable providers without deletion
- Force manual health checks with detailed diagnostics
- View provider-specific performance metrics
- Configure rate limiting and cost thresholds

---

## 👤 User Stories

### US-ADMIN-PROV-001: View All Providers
**As a** platform administrator  
**I want to** see all configured LLM providers in a single view  
**So that** I can understand the current provider landscape

**Acceptance Criteria:**
- All providers displayed in a sortable table
- Each provider shows: name, priority, status, models count, latency, last check
- Status indicators are color-coded (green/yellow/red)
- Clicking a row expands to show detailed configuration
- Search/filter by provider name or status
- Sort by any column

### US-ADMIN-PROV-002: Configure Provider Settings
**As a** platform administrator  
**I want to** modify provider configuration settings  
**So that** I can update API keys and adjust behavior

**Acceptance Criteria:**
- Edit form opens in slide-over panel
- API keys shown as masked with reveal option
- Validation prevents saving invalid configuration
- Changes require confirmation before applying
- Configuration changes logged in audit trail
- Ability to test connection before saving

### US-ADMIN-PROV-003: Adjust Provider Priority
**As a** platform administrator  
**I want to** change the priority order of providers  
**So that** I can control which provider is used first

**Acceptance Criteria:**
- Drag-and-drop reordering of providers
- Priority numbers update automatically
- Visual indicator shows current vs new order
- Save button confirms all priority changes
- Changes take effect immediately after save
- Warning if changing priority of unhealthy provider

### US-ADMIN-PROV-004: Enable/Disable Provider
**As a** platform administrator  
**I want to** temporarily disable a provider  
**So that** I can perform maintenance without affecting the system

**Acceptance Criteria:**
- Toggle switch for enable/disable
- Confirmation dialog when disabling
- Disabled providers shown with muted styling
- System prevents disabling all providers
- Reason field required when disabling
- Audit log records enable/disable actions

### US-ADMIN-PROV-005: Force Health Check
**As a** platform operator  
**I want to** manually trigger a health check  
**So that** I can verify provider status on demand

**Acceptance Criteria:**
- Health check button on each provider card
- Loading state shown during check
- Results displayed immediately after completion
- Detailed diagnostics shown (latency, endpoints checked, errors)
- Batch health check option for all providers
- Health history preserved for troubleshooting

### US-ADMIN-PROV-006: View Provider Performance
**As a** platform administrator  
**I want to** see detailed performance metrics for a provider  
**So that** I can make informed decisions about provider usage

**Acceptance Criteria:**
- Performance tab shows request volume, success rate, latency distribution
- Time period selector (1h, 24h, 7d, 30d)
- Charts for latency over time, error distribution
- Comparison with other providers
- Export metrics as CSV
- Cost breakdown for the period

---

## 🖼️ Views & Wireframes

### View 1: Providers List (Default View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🤖 LLM Providers                                        [+ Add Provider] [⚡ Check All]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ [🔍 Search providers...]              Status: [All ▼]    [↕️ Sort: Priority]    ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ ≡ │ PROVIDER          │ STATUS     │ PRIORITY │ MODELS │ LATENCY │ LAST CHECK  ││
│  ├───┼───────────────────┼────────────┼──────────┼────────┼─────────┼─────────────┤│
│  │ ⋮ │ 🔷 Vertex AI      │ 🟢 Healthy │    1     │  3/3   │  45ms   │ 30s ago     ││
│  │   │ Google Cloud      │            │          │        │         │             ││
│  ├───┼───────────────────┼────────────┼──────────┼────────┼─────────┼─────────────┤│
│  │ ⋮ │ 🟣 DeepInfra      │ 🟢 Healthy │    2     │  3/3   │ 120ms   │ 30s ago     ││
│  │   │ Open Source LLMs  │            │          │        │         │             ││
│  ├───┼───────────────────┼────────────┼──────────┼────────┼─────────┼─────────────┤│
│  │ ⋮ │ 🟠 AWS Bedrock    │ 🟢 Healthy │    3     │  3/3   │  89ms   │ 30s ago     ││
│  │   │ Amazon AI         │            │          │        │         │             ││
│  └───┴───────────────────┴────────────┴──────────┴────────┴─────────┴─────────────┘│
│                                                                                      │
│  Drag rows to reorder priority  │  Showing 3 of 3 providers                         │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Provider Detail (Expanded Row)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔷 Vertex AI                                                    [✏️ Edit] [🔄 Check]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Models]  [Performance]  [Configuration]  [Logs]                       │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  OVERVIEW                                                                           │
│  ┌────────────────────┬────────────────────┬────────────────────┬─────────────────┐ │
│  │ STATUS             │ PRIORITY           │ TOTAL REQUESTS     │ SUCCESS RATE    │ │
│  │ 🟢 Healthy         │ #1 (Primary)       │ 18,500 (24h)       │ 99.2%           │ │
│  └────────────────────┴────────────────────┴────────────────────┴─────────────────┘ │
│                                                                                      │
│  ┌────────────────────┬────────────────────┬────────────────────┬─────────────────┐ │
│  │ AVG LATENCY        │ P95 LATENCY        │ COST (24h)         │ UPTIME (30d)    │ │
│  │ 45ms               │ 78ms               │ $66.50             │ 99.98%          │ │
│  └────────────────────┴────────────────────┴────────────────────┴─────────────────┘ │
│                                                                                      │
│  MODELS                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │ Model               │ Status   │ Requests │ Success │ Avg Latency │ Cost     │   │
│  ├─────────────────────┼──────────┼──────────┼─────────┼─────────────┼──────────┤   │
│  │ gemini-1.5-pro      │ 🟢 Active │ 8,500    │ 98.5%   │ 52ms        │ $45.20   │   │
│  │ gemini-1.5-flash    │ 🟢 Active │ 6,200    │ 97.8%   │ 38ms        │ $12.40   │   │
│  │ gemini-2.0-flash    │ 🟢 Active │ 3,800    │ 96.2%   │ 41ms        │ $8.90    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  HEALTH HISTORY                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │ ████████████████████████████████████████████████████████████ 100% uptime     │   │
│  │ Last 24 hours - 0 incidents                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  [🔴 Disable Provider]                                              Enabled: ✓ ON   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Edit Provider Configuration (Slide-over)

```
┌────────────────────────────────────────────────────────────────┐
│  Edit Provider: Vertex AI                              [✕]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  BASIC SETTINGS                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Display Name                                             │  │
│  │ [Google Vertex AI                                    ]   │  │
│  │                                                          │  │
│  │ Priority                                                 │  │
│  │ [1 ▼] (Lower = Higher Priority)                         │  │
│  │                                                          │  │
│  │ Status                                                   │  │
│  │ [●] Enabled  [ ] Disabled                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  AUTHENTICATION                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Project ID                                               │  │
│  │ [anvil-production-12345                              ]   │  │
│  │                                                          │  │
│  │ Location                                                 │  │
│  │ [us-central1 ▼]                                         │  │
│  │                                                          │  │
│  │ Service Account Key                                      │  │
│  │ [••••••••••••••••••••••••••••••••••] [👁️] [📋]          │  │
│  │ Last updated: 2025-11-15                                │  │
│  │ [Upload New Key]                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  RATE LIMITS                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Requests per Minute                                      │  │
│  │ [1000            ] (Max: 5000)                           │  │
│  │                                                          │  │
│  │ Tokens per Minute                                        │  │
│  │ [100000          ] (Max: 500000)                         │  │
│  │                                                          │  │
│  │ Concurrent Requests                                      │  │
│  │ [50              ] (Max: 200)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  COST CONTROLS                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Daily Cost Limit (USD)                                   │  │
│  │ [500             ] [ ] No limit                          │  │
│  │                                                          │  │
│  │ Alert at % of Limit                                      │  │
│  │ [80              ] %                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  [🔗 Test Connection]                                          │
│  ✅ Connection successful (45ms)                               │
│                                                                │
│  ────────────────────────────────────────────────────────────  │
│                                                                │
│  [Cancel]                              [Save Changes]          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### View 4: Performance Tab

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔷 Vertex AI > Performance                                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Period: [1h] [24h] [7d] [30d]                                     [📥 Export CSV]  │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ LATENCY DISTRIBUTION (24h)                                                       ││
│  │                                                                                  ││
│  │  120ms ┤                                                                        ││
│  │        │    ╭╮                                                                  ││
│  │   80ms ┤   ╭╯╰╮    ╭╮                          ╭╮                              ││
│  │        │  ╭╯  ╰────╯╰──╮    ╭────╮    ╭───────╯╰──╮                            ││
│  │   40ms ┤──╯            ╰────╯    ╰────╯           ╰───                          ││
│  │        └──────────────────────────────────────────────────────────────────────▶ ││
│  │         00:00    04:00    08:00    12:00    16:00    20:00    Now               ││
│  │                                                                                  ││
│  │  ─── P50 (42ms)  ─── P95 (78ms)  ─── P99 (125ms)                               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────┐ ┌─────────────────────────────────────────┐│
│  │ REQUEST VOLUME                      │ │ ERROR BREAKDOWN                         ││
│  │                                     │ │                                         ││
│  │  800 ┤      ╭──╮                    │ │  rate_limit ████████░░░ 42%            ││
│  │      │   ╭──╯  ╰╮  ╭──╮            │ │  timeout    ████░░░░░░░ 23%            ││
│  │  400 ┤  ╭╯      ╰──╯  ╰──          │ │  internal   ███░░░░░░░░ 18%            ││
│  │      │──╯                          │ │  other      ██░░░░░░░░░ 17%            ││
│  │    0 └────────────────────────▶    │ │                                         ││
│  │       00   06   12   18   Now      │ │  Total Errors: 148 (0.8%)               ││
│  └─────────────────────────────────────┘ └─────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ MODEL COMPARISON                                                                 ││
│  │                                                                                  ││
│  │ Model            │ Requests │ Success │ Avg Latency │ P95 Latency │ Cost       ││
│  │ ─────────────────┼──────────┼─────────┼─────────────┼─────────────┼────────────││
│  │ gemini-1.5-pro   │ 8,500    │ 98.5%   │ 52ms        │ 95ms        │ $45.20     ││
│  │ gemini-1.5-flash │ 6,200    │ 97.8%   │ 38ms        │ 72ms        │ $12.40     ││
│  │ gemini-2.0-flash │ 3,800    │ 96.2%   │ 41ms        │ 85ms        │ $8.90      ││
│  │ ─────────────────┼──────────┼─────────┼─────────────┼─────────────┼────────────││
│  │ TOTAL            │ 18,500   │ 97.8%   │ 45ms        │ 84ms        │ $66.50     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Providers

```typescript
// GET /admin/llm/providers
// Get all providers with optional filters

interface GetProvidersRequest {
  status?: 'healthy' | 'degraded' | 'down';
  is_enabled?: boolean;
}

interface GetProvidersResponse {
  success: true;
  data: {
    providers: Provider[];
    total: number;
  };
}

interface Provider {
  id: string;
  name: string;                    // "vertex_ai"
  display_name: string;            // "Google Vertex AI"
  description: string;
  icon_url: string;
  priority: number;
  is_enabled: boolean;
  health_status: 'healthy' | 'degraded' | 'down';
  health_check_latency_ms: number;
  last_health_check: string;
  config: ProviderConfig;
  rate_limits: RateLimits;
  cost_controls: CostControls;
  models: ProviderModel[];
  stats_24h: ProviderStats;
  created_at: string;
  updated_at: string;
}

interface ProviderConfig {
  project_id?: string;           // Vertex AI
  location?: string;             // Vertex AI
  api_key?: string;              // DeepInfra (masked)
  region?: string;               // Bedrock
  endpoint_url?: string;
}

interface RateLimits {
  requests_per_minute: number;
  tokens_per_minute: number;
  concurrent_requests: number;
}

interface CostControls {
  daily_limit_usd: number | null;
  alert_threshold_pct: number;
}

interface ProviderStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_cost_usd: number;
}
```

### Update Provider

```typescript
// PUT /admin/llm/providers/{id}
// Update provider configuration

interface UpdateProviderRequest {
  display_name?: string;
  priority?: number;
  is_enabled?: boolean;
  config?: Partial<ProviderConfig>;
  rate_limits?: Partial<RateLimits>;
  cost_controls?: Partial<CostControls>;
}

// Validation
const updateProviderValidation = {
  display_name: {
    required: false,
    minLength: 2,
    maxLength: 100
  },
  priority: {
    required: false,
    min: 1,
    max: 10
  },
  'rate_limits.requests_per_minute': {
    required: false,
    min: 1,
    max: 10000
  },
  'cost_controls.daily_limit_usd': {
    required: false,
    min: 0,
    max: 10000
  }
};

interface UpdateProviderResponse {
  success: true;
  data: {
    provider: Provider;
    changes: Array<{
      field: string;
      old_value: any;
      new_value: any;
    }>;
  };
}
```

### Force Health Check

```typescript
// POST /admin/llm/providers/{id}/health-check
// Trigger manual health check

interface HealthCheckResponse {
  success: true;
  data: {
    provider_id: string;
    provider_name: string;
    status: 'healthy' | 'degraded' | 'down';
    latency_ms: number;
    endpoints_checked: Array<{
      endpoint: string;
      status: 'ok' | 'error';
      latency_ms: number;
      error?: string;
    }>;
    models_checked: Array<{
      model_id: string;
      status: 'ok' | 'error';
      latency_ms: number;
      error?: string;
    }>;
    checked_at: string;
  };
}
```

### Get Provider Performance

```typescript
// GET /admin/llm/providers/{id}/performance?period=24h
// Get detailed performance metrics

interface GetProviderPerformanceRequest {
  period: '1h' | '24h' | '7d' | '30d';
}

interface GetProviderPerformanceResponse {
  success: true;
  data: {
    provider_id: string;
    period: string;
    summary: ProviderStats;
    latency_percentiles: {
      p50: number;
      p75: number;
      p90: number;
      p95: number;
      p99: number;
    };
    error_breakdown: Record<string, number>;
    model_breakdown: Array<{
      model_id: string;
      model_name: string;
      requests: number;
      success_rate: number;
      avg_latency_ms: number;
      p95_latency_ms: number;
      cost_usd: number;
    }>;
    timeseries: {
      latency: TimeSeriesPoint[];
      requests: TimeSeriesPoint[];
      errors: TimeSeriesPoint[];
    };
  };
}
```

### Reorder Priorities

```typescript
// PUT /admin/llm/providers/priorities
// Batch update provider priorities

interface UpdatePrioritiesRequest {
  priorities: Array<{
    provider_id: string;
    priority: number;
  }>;
}

interface UpdatePrioritiesResponse {
  success: true;
  data: {
    updated: Array<{
      provider_id: string;
      old_priority: number;
      new_priority: number;
    }>;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface ProvidersModuleState {
  // Data
  providers: Provider[];
  selectedProvider: Provider | null;
  
  // UI State
  loading: {
    list: boolean;
    details: boolean;
    healthCheck: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    details: Error | null;
    healthCheck: Error | null;
    save: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    status: 'all' | 'healthy' | 'degraded' | 'down';
  };
  
  // Sorting
  sortBy: 'priority' | 'name' | 'status' | 'latency';
  sortOrder: 'asc' | 'desc';
  
  // Edit State
  editMode: boolean;
  editForm: Partial<UpdateProviderRequest> | null;
  hasUnsavedChanges: boolean;
  
  // Priority Reordering
  isReordering: boolean;
  pendingPriorities: Array<{ provider_id: string; priority: number }>;
  
  // Performance View
  performancePeriod: '1h' | '24h' | '7d' | '30d';
  performanceData: GetProviderPerformanceResponse['data'] | null;
  
  // Health Check
  lastHealthCheckResult: HealthCheckResponse['data'] | null;
  
  // Tab Navigation
  activeTab: 'overview' | 'models' | 'performance' | 'configuration' | 'logs';
}
```

---

## 🎨 Component Specifications

### ProviderTable

```typescript
interface ProviderTableProps {
  providers: Provider[];
  onSelect: (provider: Provider) => void;
  onReorder: (newOrder: string[]) => void;
  selectedId?: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSort: (column: string) => void;
  loading?: boolean;
}

// Usage
<ProviderTable
  providers={providers}
  onSelect={handleSelectProvider}
  onReorder={handleReorderProviders}
  selectedId={selectedProvider?.id}
  sortBy={sortBy}
  sortOrder={sortOrder}
  onSort={handleSort}
  loading={loading.list}
/>
```

### ProviderDetailPanel

```typescript
interface ProviderDetailPanelProps {
  provider: Provider;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onEdit: () => void;
  onHealthCheck: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  performanceData?: GetProviderPerformanceResponse['data'];
  healthCheckResult?: HealthCheckResponse['data'];
  loading?: boolean;
}
```

### ProviderEditForm

```typescript
interface ProviderEditFormProps {
  provider: Provider;
  onSave: (data: UpdateProviderRequest) => void;
  onCancel: () => void;
  onTestConnection: () => Promise<void>;
  loading?: boolean;
  connectionTestResult?: { success: boolean; latency_ms: number };
}
```

### PriorityReorderList

```typescript
interface PriorityReorderListProps {
  items: Array<{ id: string; name: string; priority: number }>;
  onReorder: (newOrder: string[]) => void;
  onSave: () => void;
  onCancel: () => void;
  hasChanges: boolean;
}
```

### HealthCheckResultCard

```typescript
interface HealthCheckResultCardProps {
  result: HealthCheckResponse['data'];
  onRecheck: () => void;
  loading?: boolean;
}
```

---

## 🎬 Motion Design

```typescript
const providersAnimations = {
  // Row reorder
  rowReorder: {
    layout: true,
    transition: { type: 'spring', stiffness: 300, damping: 30 }
  },
  
  // Status change
  statusChange: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3 }
  },
  
  // Detail panel slide
  detailPanelEnter: {
    initial: { opacity: 0, height: 0 },
    animate: { opacity: 1, height: 'auto' },
    exit: { opacity: 0, height: 0 },
    transition: { duration: 0.3 }
  },
  
  // Edit slide-over
  editSlideOver: {
    initial: { x: '100%' },
    animate: { x: 0 },
    exit: { x: '100%' },
    transition: { type: 'spring', stiffness: 300, damping: 30 }
  },
  
  // Health check loading
  healthCheckSpinner: {
    rotate: 360,
    transition: { duration: 1, repeat: Infinity, ease: 'linear' }
  },
  
  // Connection test success
  connectionSuccess: {
    scale: [1, 1.05, 1],
    borderColor: ['#334155', '#10B981', '#334155'],
    transition: { duration: 0.5 }
  },
  
  // Priority drag
  dragActive: {
    scale: 1.02,
    boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
    zIndex: 1000
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const providersShortcuts = {
  'mod+n': 'Add new provider',
  'mod+e': 'Edit selected provider',
  'mod+h': 'Health check selected',
  'mod+shift+h': 'Health check all',
  'up/down': 'Navigate providers',
  'enter': 'Expand/select provider',
  'escape': 'Close edit panel',
  'mod+s': 'Save changes',
  'd': 'Toggle provider enabled/disabled',
};
```

---

## ⚠️ Error Handling

```typescript
const providerErrorCodes = {
  // Validation
  PROV_VAL_001: 'Provider name is required',
  PROV_VAL_002: 'Invalid priority value',
  PROV_VAL_003: 'Invalid rate limit configuration',
  PROV_VAL_004: 'API key format is invalid',
  
  // Business Logic
  PROV_BUS_001: 'Cannot disable all providers',
  PROV_BUS_002: 'Cannot delete provider with active requests',
  PROV_BUS_003: 'Priority conflict detected',
  
  // Connection
  PROV_CON_001: 'Failed to connect to provider',
  PROV_CON_002: 'Authentication failed',
  PROV_CON_003: 'Provider rate limit exceeded',
  PROV_CON_004: 'Health check timed out',
  
  // System
  PROV_SYS_001: 'Failed to save provider configuration',
  PROV_SYS_002: 'Failed to update priorities',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| PUT /providers/{id} | display_name | string | No | 2-100 chars |
| PUT /providers/{id} | priority | number | No | 1-10 |
| PUT /providers/{id} | is_enabled | boolean | No | - |
| PUT /providers/{id} | config.project_id | string | Vertex | Valid GCP project |
| PUT /providers/{id} | config.api_key | string | DeepInfra | Valid API key format |
| PUT /providers/{id} | rate_limits.requests_per_minute | number | No | 1-10000 |
| PUT /providers/{id} | cost_controls.daily_limit_usd | number | No | 0-10000 |

---

## 🔒 Security Considerations

1. **API Key Handling:** Keys displayed masked, revealed only on explicit action, stored encrypted
2. **Connection Testing:** Test uses sandboxed request, doesn't affect production
3. **Audit Trail:** All configuration changes logged with user, timestamp, before/after values
4. **Permission Check:** Edit/disable operations restricted to Admin role only
5. **Confirmation Required:** Destructive actions (disable, delete) require confirmation modal
6. **Concurrent Edit Protection:** Optimistic locking prevents conflicting updates

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Providers Management*  
*User Type: Admin*

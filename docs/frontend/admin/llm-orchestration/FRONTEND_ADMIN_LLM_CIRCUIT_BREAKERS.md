# FRONTEND_ADMIN_LLM_CIRCUIT_BREAKERS

## Admin LLM Circuit Breakers Module

**User Type:** Admin  
**Module:** Circuit Breaker Management  
**Route:** `/admin/llm/circuit-breakers`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Circuit Breakers** - Provider Health Protection

### Description
Management interface for circuit breaker configuration protecting the system from cascading failures when providers experience issues. Monitors breaker states, configures thresholds, and provides manual override capabilities.

### Key Capabilities
- Real-time circuit breaker status monitoring
- Configure trip thresholds per provider
- Manual open/close breakers
- View trip history and patterns
- Alert configuration for state changes
- Half-open testing controls

---

## 👤 User Stories

### US-ADMIN-CB-001: View Circuit Breaker States
**As a** platform administrator  
**I want to** see the current state of all circuit breakers  
**So that** I understand which providers are healthy

**Acceptance Criteria:**
- Dashboard showing all breakers with visual states
- States: Closed (healthy), Open (tripped), Half-Open (testing)
- Time since last state change
- Error count that triggered trip
- Recovery countdown for open breakers

### US-ADMIN-CB-002: Configure Breaker Thresholds
**As a** platform administrator  
**I want to** adjust circuit breaker thresholds  
**So that** I can tune sensitivity per provider

**Acceptance Criteria:**
- Failure threshold (count or percentage)
- Failure window duration
- Recovery timeout duration
- Half-open test request count
- Success threshold to close

### US-ADMIN-CB-003: Manually Control Breakers
**As a** platform administrator  
**I want to** manually open or close breakers  
**So that** I can respond to incidents quickly

**Acceptance Criteria:**
- One-click open breaker (block provider)
- One-click reset breaker (restore traffic)
- Reason field for manual actions
- Audit trail of manual interventions
- Confirmation dialog for actions

### US-ADMIN-CB-004: View Trip History
**As a** platform administrator  
**I want to** see breaker trip history  
**So that** I can identify problematic providers

**Acceptance Criteria:**
- Timeline of state changes
- Trip duration statistics
- Error types that caused trips
- Recovery time metrics
- Correlation with incidents

---

## 🖼️ Views & Wireframes

### View 1: Circuit Breakers Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ Circuit Breakers                                              [⚙️ Configure]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Status Summary ────────────────────────────────────────────────────────────────┐│
│  │  🟢 2 Closed (Healthy)    🟡 1 Half-Open (Testing)    🔴 0 Open (Tripped)      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔷 VERTEX AI                                                                   ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  ┌─────────────────┐                                                      │  ││
│  │  │  │   🟢 CLOSED     │     State: Healthy                                   │  ││
│  │  │  │                 │     Errors: 3/50 (6%) in last 5 min                  │  ││
│  │  │  │   ● ● ● ●       │     Threshold: 10 errors or 20% failure rate        │  ││
│  │  │  │                 │     Last trip: 3 days ago                            │  ││
│  │  │  └─────────────────┘                                                      │  ││
│  │  │                                                                           │  ││
│  │  │  [🔴 Force Open]  [📊 History]  [⚙️ Configure]                           │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟣 DEEPINFRA                                                                   ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  ┌─────────────────┐                                                      │  ││
│  │  │  │   🟡 HALF-OPEN  │     State: Testing recovery                          │  ││
│  │  │  │                 │     Test requests: 2/5 successful                    │  ││
│  │  │  │   ● ● ○ ○ ○     │     Needs: 3 more successes to close                │  ││
│  │  │  │                 │     Tripped: 8 minutes ago                           │  ││
│  │  │  └─────────────────┘     Reason: Rate limit errors (429)                  │  ││
│  │  │                                                                           │  ││
│  │  │  [🟢 Force Close]  [🔴 Force Open]  [📊 History]  [⚙️ Configure]         │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟠 AWS BEDROCK                                                                 ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  ┌─────────────────┐                                                      │  ││
│  │  │  │   🟢 CLOSED     │     State: Healthy                                   │  ││
│  │  │  │                 │     Errors: 1/50 (2%) in last 5 min                  │  ││
│  │  │  │   ● ● ● ●       │     Threshold: 10 errors or 20% failure rate        │  ││
│  │  │  │                 │     Last trip: Never                                 │  ││
│  │  │  └─────────────────┘                                                      │  ││
│  │  │                                                                           │  ││
│  │  │  [🔴 Force Open]  [📊 History]  [⚙️ Configure]                           │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Circuit Breaker Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Configure Circuit Breaker: DeepInfra                                    [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  TRIP CONDITIONS                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Trip when EITHER condition is met:                                          │  │
│  │                                                                               │  │
│  │  Failure Count Threshold                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [10        ] consecutive failures                                       │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  OR                                                                          │  │
│  │                                                                               │  │
│  │  Failure Rate Threshold                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [20        ]% failure rate over [5         ] minutes                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Minimum sample size: [50] requests                                          │  │
│  │                                                                               │  │
│  │  Error Types to Count                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] 5xx Server Errors    [✓] Timeouts    [ ] 429 Rate Limits           │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RECOVERY SETTINGS                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Recovery Timeout                                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [60        ] seconds before attempting recovery                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Time to wait in OPEN state before moving to HALF-OPEN                       │  │
│  │                                                                               │  │
│  │  Half-Open Test Requests                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [5         ] successful requests to close breaker                       │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Max Requests in Half-Open                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [10        ] requests allowed during testing                            │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  NOTIFICATIONS                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  [✓] Alert on trip    [✓] Alert on recovery    [ ] Alert on half-open       │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Reset to Defaults]                               [Cancel]        [Save Changes]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Trip History

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Circuit Breaker History: DeepInfra                          [Last 30 Days ▼]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  SUMMARY                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Total Trips: 12    │  Avg Duration: 4.2 min    │  Availability: 99.2%         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  STATE TIMELINE                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🟢████████████████████🔴██🟡█🟢██████████🔴███🟡██🟢███████████████████████    ││
│  │  |                     |     |            |        |                        |   ││
│  │  Nov 1              Nov 8  Nov 9       Nov 15   Nov 16                   Dec 1   ││
│  │                                                                                  ││
│  │  🟢 Closed (99.2%)    🟡 Half-Open (0.3%)    🔴 Open (0.5%)                     ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TRIP EVENTS                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ TIME              │ DURATION │ TRIGGER REASON           │ RECOVERY             ││
│  ├───────────────────┼──────────┼──────────────────────────┼──────────────────────┤│
│  │ Today, 14:25      │ 8 min    │ 429 Rate limit burst     │ 🟡 In progress       ││
│  │ Nov 15, 10:42     │ 3 min    │ 500 Server errors (12)   │ ✅ Auto-recovered    ││
│  │ Nov 15, 02:15     │ 45 min   │ Provider outage          │ 🔧 Manual reset      ││
│  │ Nov 8, 16:30      │ 2 min    │ Timeout spike            │ ✅ Auto-recovered    ││
│  │ Nov 8, 09:12      │ 5 min    │ 500 Server errors (15)   │ ✅ Auto-recovered    ││
│  └───────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Circuit Breakers

```typescript
// GET /admin/llm/circuit-breakers
// Get all circuit breaker states

interface GetCircuitBreakersResponse {
  success: true;
  data: {
    breakers: CircuitBreaker[];
    summary: {
      closed: number;
      half_open: number;
      open: number;
    };
  };
}

interface CircuitBreaker {
  id: string;
  provider_id: string;
  provider_name: string;
  state: 'closed' | 'half_open' | 'open';
  state_changed_at: string;
  current_failures: number;
  current_successes: number;
  failure_rate: number;
  config: CircuitBreakerConfig;
  last_error?: {
    message: string;
    code: number;
    timestamp: string;
  };
  half_open_progress?: {
    successes: number;
    required: number;
  };
  recovery_at?: string;
}

interface CircuitBreakerConfig {
  failure_count_threshold: number;
  failure_rate_threshold: number;
  failure_rate_window_seconds: number;
  min_sample_size: number;
  recovery_timeout_seconds: number;
  half_open_max_requests: number;
  half_open_success_threshold: number;
  count_rate_limits: boolean;
}
```

### Update Circuit Breaker Config

```typescript
// PUT /admin/llm/circuit-breakers/{id}/config
// Update configuration

interface UpdateCircuitBreakerConfigRequest {
  failure_count_threshold?: number;
  failure_rate_threshold?: number;
  failure_rate_window_seconds?: number;
  recovery_timeout_seconds?: number;
  half_open_success_threshold?: number;
}
```

### Manual Breaker Control

```typescript
// POST /admin/llm/circuit-breakers/{id}/control
// Manual open/close/reset

interface ControlCircuitBreakerRequest {
  action: 'open' | 'close' | 'reset';
  reason: string;
}

interface ControlCircuitBreakerResponse {
  success: true;
  data: {
    breaker: CircuitBreaker;
    previous_state: string;
    new_state: string;
  };
}
```

### Get Trip History

```typescript
// GET /admin/llm/circuit-breakers/{id}/history?days=30
// Get trip history

interface GetTripHistoryResponse {
  success: true;
  data: {
    breaker_id: string;
    period_days: number;
    summary: {
      total_trips: number;
      avg_duration_seconds: number;
      availability_pct: number;
    };
    events: Array<{
      id: string;
      started_at: string;
      ended_at?: string;
      duration_seconds?: number;
      trigger_reason: string;
      error_count: number;
      recovery_type: 'auto' | 'manual';
    }>;
    timeline: Array<{
      timestamp: string;
      state: string;
    }>;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface CircuitBreakersState {
  breakers: CircuitBreaker[];
  summary: BreakersSummary;
  selectedBreaker: CircuitBreaker | null;
  
  loading: {
    list: boolean;
    config: boolean;
    control: boolean;
    history: boolean;
  };
  
  configModalOpen: boolean;
  configForm: Partial<CircuitBreakerConfig>;
  
  historyModalOpen: boolean;
  historyData: GetTripHistoryResponse['data'] | null;
  
  controlModalOpen: boolean;
  controlAction: 'open' | 'close' | 'reset' | null;
}
```

---

## 🎨 Component Specifications

### CircuitBreakerCard

```typescript
interface CircuitBreakerCardProps {
  breaker: CircuitBreaker;
  onForceOpen: () => void;
  onForceClose: () => void;
  onViewHistory: () => void;
  onConfigure: () => void;
}
```

### BreakerStateIndicator

```typescript
interface BreakerStateIndicatorProps {
  state: 'closed' | 'half_open' | 'open';
  progress?: { current: number; total: number };
  animated?: boolean;
}
```

### TripTimeline

```typescript
interface TripTimelineProps {
  events: TripEvent[];
  period: string;
  onEventClick?: (eventId: string) => void;
}
```

---

## 🎬 Motion Design

```typescript
const circuitBreakerAnimations = {
  stateChange: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.3 }
  },
  
  openPulse: {
    boxShadow: ['0 0 0 0 rgba(239, 68, 68, 0.4)', '0 0 0 10px rgba(239, 68, 68, 0)', '0 0 0 0 rgba(239, 68, 68, 0)'],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  halfOpenProgress: {
    width: '100%',
    transition: { duration: 0.3 }
  },
  
  recoveryCountdown: {
    strokeDashoffset: 0,
    transition: { duration: 1, ease: 'linear' }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const circuitBreakerShortcuts = {
  'mod+r': 'Refresh states',
  'o': 'Force open selected',
  'c': 'Force close selected',
  'h': 'View history',
  's': 'Configure settings',
};
```

---

## ⚠️ Error Handling

```typescript
const circuitBreakerErrorCodes = {
  CB_LOAD_001: 'Failed to load circuit breakers',
  CB_CTRL_001: 'Failed to change breaker state',
  CB_CONF_001: 'Invalid configuration values',
  CB_HIST_001: 'Failed to load history',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Circuit Breakers*

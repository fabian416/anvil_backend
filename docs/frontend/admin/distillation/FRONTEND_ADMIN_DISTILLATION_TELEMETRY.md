# FRONTEND_ADMIN_DISTILLATION_TELEMETRY

## Admin Distillation Telemetry Module

**User Type:** Admin  
**Module:** Distillation Telemetry  
**Route:** `/admin/distillation/telemetry`  
**Access Level:** Read (All)

---

## 📋 Module Overview

### Title
**Distillation Telemetry** - Classification & Routing Analytics

### Description
Detailed analytics for the distillation pass system, tracking classification accuracy, routing decisions, latency distribution, and cost savings over time.

---

## 👤 User Stories

### US-ADMIN-DIST-TEL-001: View Classification Metrics
**As a** platform administrator  
**I want to** see intent classification performance  
**So that** I can monitor classification accuracy

### US-ADMIN-DIST-TEL-002: Track Routing Distribution
**As a** platform administrator  
**I want to** see how requests are routed  
**So that** I can optimize routing rules

### US-ADMIN-DIST-TEL-003: Monitor Latency
**As a** platform administrator  
**I want to** track classification latency  
**So that** I ensure <50ms target is met

### US-ADMIN-DIST-TEL-004: Analyze Cost Savings
**As a** platform administrator  
**I want to** see detailed cost savings  
**So that** I can demonstrate distillation value

---

## 🖼️ Views & Wireframes

### View 1: Telemetry Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 Distillation Telemetry                                       [Last 24h ▼]       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Classification]  [Routing]  [Latency]  [Savings]                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  45,230 Classified │ 42ms Avg Latency │ 89% Confidence │ $127.50 Saved         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ROUTING DISTRIBUTION                          CLASSIFICATION LATENCY               │
│  ┌────────────────────────────────────┐       ┌────────────────────────────────────┐│
│  │                                    │       │                                    ││
│  │     ┌──────────┐                   │       │  60ms ┤         ╭──╮              ││
│  │    ╱   FULL    ╲                   │       │       │        ╭╯  ╰╮             ││
│  │   │    LLM     │ 25%               │       │  40ms ┤───────╭╯    ╰──────────── ││
│  │   │            │                   │       │       │      ╭╯       Target: 50ms││
│  │   │ ┌────────┐ │                   │       │  20ms ┤─────╭╯                    ││
│  │   │ │ LIGHT  │ │ 35%               │       │       └────────────────────▶      ││
│  │   │ │  LLM   │ │                   │       │        00   06   12   18   Now    ││
│  │   │ │┌──────┐│ │                   │       │                                    ││
│  │   │ ││STATIC││ │ 20%               │       │  P50: 38ms │ P95: 62ms │ P99: 85ms││
│  │   │ ││┌────┐││ │                   │       └────────────────────────────────────┘│
│  │   │ │││CACH│││ │ 12%               │                                             │
│  │   │ │││E   │││ │                   │       INTENT DISTRIBUTION                   │
│  │   │ │││┌──┐│││ │ 8%                │       ┌────────────────────────────────────┐│
│  │   │ ││││RE│││││REJECT              │       │ price_check      ████████████ 24%  ││
│  │   └─┴┴┴┴──┴┴┴┴─┘                   │       │ balance_check    ██████████   18%  ││
│  │                                    │       │ swap_request     █████████    16%  ││
│  │  🚫 8% │ 💾 12% │ 📝 20%           │       │ greeting         ████████     14%  ││
│  │  🔵 35% │ 🟣 25%                   │       │ explain_concept  ██████       10%  ││
│  └────────────────────────────────────┘       │ other            ████████     18%  ││
│                                               └────────────────────────────────────┘│
│                                                                                      │
│  COST SAVINGS BREAKDOWN                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Route           │ Requests │ Avoided Cost │ Savings                            ││
│  │  ───────────────────────────────────────────────────────────────────────────── ││
│  │  🚫 REJECT       │ 3,618    │ $36.18       │ 100% (no LLM call)                 ││
│  │  💾 CACHE        │ 5,428    │ $48.85       │ 100% (cached response)             ││
│  │  📝 STATIC       │ 9,046    │ $81.41       │ 100% (template response)           ││
│  │  🔵 LIGHT LLM    │ 15,831   │ -$38.94      │ 60% vs full (cheaper model)        ││
│  │  🟣 FULL LLM     │ 11,307   │ $0           │ 0% (full processing)               ││
│  │  ───────────────────────────────────────────────────────────────────────────── ││
│  │  TOTAL           │ 45,230   │ $127.50      │ 45% overall savings                ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Distillation Telemetry

```typescript
// GET /admin/distillation/telemetry?period=24h
interface GetDistillationTelemetryResponse {
  success: true;
  data: {
    summary: {
      total_classified: number;
      avg_latency_ms: number;
      avg_confidence: number;
      total_savings_usd: number;
    };
    routing_distribution: Record<string, {
      count: number;
      percentage: number;
    }>;
    intent_distribution: Record<string, number>;
    latency: {
      timeseries: TimeSeriesPoint[];
      percentiles: { p50: number; p95: number; p99: number };
    };
    savings_breakdown: Array<{
      route: string;
      requests: number;
      avoided_cost_usd: number;
      savings_percentage: number;
    }>;
    low_confidence_samples: Array<{
      query: string;
      intent: string;
      confidence: number;
      routed_to: string;
    }>;
  };
}
```

---

## 🎬 Motion Design

```typescript
const distillationTelemetryAnimations = {
  sankeyFlow: {
    pathLength: [0, 1],
    transition: { duration: 1.5, ease: 'easeOut' }
  },
  
  savingsCounter: {
    opacity: [0, 1],
    y: [20, 0],
    transition: { duration: 0.5 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Distillation Telemetry*

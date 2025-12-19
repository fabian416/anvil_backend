# FRONTEND_ADMIN_PROJECTS_TOOLS

## Admin Project Tools Module

**User Type:** Admin  
**Module:** Project Tools Configuration  
**Route:** `/admin/projects/:id/tools`  
**Access Level:** Full CRUD (Admin)

---

## 📋 Module Overview

### Title
**Project Tools** - DeFi Tool Configuration

### Description
Configuration interface for managing the AI tools available within a project. Enables administrators to enable/disable tools, configure tool parameters, set rate limits, and monitor tool usage.

### Key Capabilities
- Enable/disable tools per project
- Configure tool-specific parameters
- Set rate limits and quotas
- Monitor tool usage statistics
- Test tool functionality
- Configure tool permissions

---

## 👤 User Stories

### US-ADMIN-TOOLS-001: View Available Tools
**As a** platform administrator  
**I want to** see all available tools for a project  
**So that** I understand what capabilities are enabled

### US-ADMIN-TOOLS-002: Enable/Disable Tools
**As a** platform administrator  
**I want to** toggle tool availability  
**So that** users only have access to appropriate functionality

### US-ADMIN-TOOLS-003: Configure Tool Parameters
**As a** platform administrator  
**I want to** adjust tool-specific settings  
**So that** tools work correctly for this project

### US-ADMIN-TOOLS-004: Set Rate Limits
**As a** platform administrator  
**I want to** limit tool invocations  
**So that** costs and risks are controlled

### US-ADMIN-TOOLS-005: Monitor Tool Usage
**As a** platform administrator  
**I want to** see tool usage statistics  
**So that** I understand how tools are being used

---

## 🖼️ Views & Wireframes

### View 1: Tools Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔧 Project Tools: Aave                                              [Save Changes] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  🔧 12 Tools Available    ✅ 8 Enabled    📊 2,450 Invocations (24h)           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  MARKET DATA TOOLS                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] get_token_price                                         [⚙️] [📊]    │ ││
│  │  │     Fetch current price for any token                                     │ ││
│  │  │     📊 1,245 calls (24h) │ ⏱️ 120ms avg │ ✅ 99.8% success               │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] get_gas_prices                                          [⚙️] [📊]    │ ││
│  │  │     Get current gas prices for supported chains                           │ ││
│  │  │     📊 890 calls (24h) │ ⏱️ 85ms avg │ ✅ 99.9% success                  │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] get_protocol_stats                                      [⚙️] [📊]    │ ││
│  │  │     Fetch TVL, APY, and stats for DeFi protocols                          │ ││
│  │  │     📊 312 calls (24h) │ ⏱️ 250ms avg │ ✅ 98.5% success                 │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  WALLET TOOLS                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] get_wallet_balance                                      [⚙️] [📊]    │ ││
│  │  │     Fetch token balances for connected wallet                             │ ││
│  │  │     📊 456 calls (24h) │ ⏱️ 180ms avg │ ✅ 99.2% success                 │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] get_transaction_history                                 [⚙️] [📊]    │ ││
│  │  │     Retrieve recent transactions for wallet                               │ ││
│  │  │     📊 234 calls (24h) │ ⏱️ 320ms avg │ ✅ 97.8% success                 │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  DEFI ACTIONS                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] execute_swap                                            [⚙️] [📊]    │ ││
│  │  │     Execute token swap via 1inch aggregator                               │ ││
│  │  │     📊 89 calls (24h) │ ⏱️ 2.1s avg │ ✅ 94.5% success                   │ ││
│  │  │     ⚠️ Requires: enabled_protocols includes '1inch'                       │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] aave_supply                                             [⚙️] [📊]    │ ││
│  │  │     Supply tokens to Aave lending pool                                    │ ││
│  │  │     📊 45 calls (24h) │ ⏱️ 1.8s avg │ ✅ 96.2% success                   │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [✓] aave_borrow                                             [⚙️] [📊]    │ ││
│  │  │     Borrow tokens from Aave                                               │ ││
│  │  │     📊 23 calls (24h) │ ⏱️ 2.3s avg │ ✅ 91.3% success                   │ ││
│  │  │     ⚠️ Risk: Affects health factor                                        │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ [ ] execute_leverage_loop        🔴 DISABLED                [⚙️] [📊]    │ ││
│  │  │     Execute recursive leverage strategy                                    │ ││
│  │  │     ⚠️ High Risk: Leverage positions can be liquidated                    │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Tool Configuration Modal

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ Configure Tool: execute_swap                                            [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  TOOL INFORMATION                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Name: execute_swap                                                          │  │
│  │  Description: Execute token swap via 1inch aggregator                        │  │
│  │  Category: DeFi Actions                                                       │  │
│  │  Risk Level: 🟡 Medium                                                        │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  PARAMETERS                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Default Slippage (bps)                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [50         ]                           Range: 10-500                   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Swap Aggregator                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [1inch ▼]                                                               │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Gas Price Strategy                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] Standard  [ ] Fast  [ ] Instant                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RATE LIMITS                                                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Per User Limits                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [10        ] calls per [hour ▼]                                        │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Project Limits                                                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [500       ] calls per [day ▼]                                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Maximum Value per Call                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [$] [10,000    ] USD                                                   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  REQUIREMENTS                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  [✓] Require wallet connection                                               │  │
│  │  [✓] Require 2FA for values > $1,000                                        │  │
│  │  [ ] Require admin approval                                                   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Test Tool]                                         [Cancel]        [Save Config]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Project Tools

```typescript
// GET /admin/projects/{id}/tools
interface GetProjectToolsResponse {
  success: true;
  data: {
    tools: ProjectTool[];
    summary: {
      total: number;
      enabled: number;
      invocations_24h: number;
    };
  };
}

interface ProjectTool {
  id: string;
  name: string;
  description: string;
  category: 'market_data' | 'wallet' | 'defi_actions' | 'analytics' | 'utility';
  risk_level: 'low' | 'medium' | 'high';
  is_enabled: boolean;
  config: ToolConfig;
  rate_limits: ToolRateLimits;
  requirements: ToolRequirements;
  stats: {
    calls_24h: number;
    avg_latency_ms: number;
    success_rate: number;
  };
  dependencies?: string[];
}

interface ToolConfig {
  [key: string]: any;
}

interface ToolRateLimits {
  per_user_limit: number;
  per_user_window: 'minute' | 'hour' | 'day';
  project_limit: number;
  project_window: 'hour' | 'day';
  max_value_usd?: number;
}

interface ToolRequirements {
  require_wallet: boolean;
  require_2fa: boolean;
  require_2fa_threshold_usd?: number;
  require_approval: boolean;
}
```

### Update Tool Configuration

```typescript
// PUT /admin/projects/{id}/tools/{tool_id}
interface UpdateToolRequest {
  is_enabled?: boolean;
  config?: ToolConfig;
  rate_limits?: Partial<ToolRateLimits>;
  requirements?: Partial<ToolRequirements>;
}
```

### Test Tool

```typescript
// POST /admin/projects/{id}/tools/{tool_id}/test
interface TestToolRequest {
  params: Record<string, any>;
}

interface TestToolResponse {
  success: boolean;
  result?: any;
  error?: string;
  latency_ms: number;
}
```

---

## 🎬 Motion Design

```typescript
const toolsAnimations = {
  toggleTool: {
    scale: [1, 0.95, 1],
    transition: { duration: 0.2 }
  },
  
  statsUpdate: {
    opacity: [0.5, 1],
    transition: { duration: 0.3 }
  },
  
  categoryExpand: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.3 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Project Tools*

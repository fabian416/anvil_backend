# FRONTEND_ADMIN_PROJECTS_EDITOR

## Admin Project Editor Module

**User Type:** Admin  
**Module:** Project Editor  
**Route:** `/admin/projects/:id/edit`  
**Access Level:** Full CRUD (Admin)

---

## 📋 Module Overview

### Title
**Project Editor** - Complete Project Configuration

### Description
Comprehensive project editing interface allowing administrators to modify all aspects of a project including basic info, system prompts, enabled protocols/chains/tools, risk configuration, and advanced settings.

---

## 👤 User Stories

### US-ADMIN-PROJ-EDIT-001: Edit Basic Information
**As a** platform administrator  
**I want to** edit project name, description, and branding  
**So that** projects are properly identified

### US-ADMIN-PROJ-EDIT-002: Configure System Prompt
**As a** platform administrator  
**I want to** edit the AI system prompt  
**So that** the assistant behaves appropriately

### US-ADMIN-PROJ-EDIT-003: Manage Protocols & Chains
**As a** platform administrator  
**I want to** enable/disable DeFi protocols and chains  
**So that** users can only access approved functionality

### US-ADMIN-PROJ-EDIT-004: Set Risk Limits
**As a** platform administrator  
**I want to** configure risk parameters  
**So that** user operations stay within safe bounds

---

## 🖼️ Views & Wireframes

### View 1: Project Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✏️ Edit Project: Aave                                    [Preview] [Save Changes]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Basic Info]  [System Prompt]  [Protocols]  [Risk Config]  [Advanced]              │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  BASIC INFORMATION                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Project Name *                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Aave                                                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  URL Slug *                               Project Icon                       │  │
│  │  ┌─────────────────────────────┐         ┌─────────────────────────┐         │  │
│  │  │ aave                        │         │  🏦  [Change Icon]      │         │  │
│  │  └─────────────────────────────┘         └─────────────────────────┘         │  │
│  │  anvil.app/projects/aave                                                     │  │
│  │                                                                               │  │
│  │  Description *                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Your intelligent assistant for Aave lending and borrowing. Get help    │  │  │
│  │  │ with health factors, supply/borrow rates, and portfolio optimization.  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Characters: 156/200                                                          │  │
│  │                                                                               │  │
│  │  Brand Color                              Visibility                         │  │
│  │  ┌─────────────────────────────┐         ┌─────────────────────────┐         │  │
│  │  │ [■] #B6509E                 │         │ [Public ▼]              │         │  │
│  │  └─────────────────────────────┘         └─────────────────────────┘         │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SYSTEM PROMPT                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                  Tokens: 485 │  │
│  │  You are an expert Aave assistant helping users with lending and borrowing  │  │
│  │  operations on the Aave protocol.                                            │  │
│  │                                                                               │  │
│  │  ## Your Capabilities                                                        │  │
│  │  - Check supply and borrow APY rates                                         │  │
│  │  - Monitor health factors and liquidation risks                              │  │
│  │  - Execute supply, borrow, repay, and withdraw operations                    │  │
│  │  - Provide yield optimization recommendations                                │  │
│  │                                                                               │  │
│  │  ## Guidelines                                                               │  │
│  │  - Always show health factor impact before transactions                      │  │
│  │  - Warn users when health factor drops below 1.5                            │  │
│  │  - Recommend against high-risk leverage positions                            │  │
│  │                                                                               │  │
│  │  [Markdown supported]                                                        │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  WELCOME MESSAGE                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Welcome! I'm your Aave assistant. I can help you:                           │  │
│  │  • Check current APY rates                                                   │  │
│  │  • Monitor your health factor                                                │  │
│  │  • Supply or borrow assets                                                   │  │
│  │                                                                               │  │
│  │  What would you like to do?                                                  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Protocols & Chains Tab

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✏️ Edit Project: Aave                                    [Preview] [Save Changes]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Basic Info]  [System Prompt]  [Protocols]  [Risk Config]  [Advanced]              │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ENABLED CHAINS                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  [✓] Ethereum Mainnet        [✓] Arbitrum One       [✓] Polygon             │  │
│  │  [✓] Base                    [ ] Optimism           [ ] Avalanche           │  │
│  │  [ ] BSC                     [ ] zkSync Era         [ ] Linea               │  │
│  │                                                                               │  │
│  │  4 chains enabled                                                            │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ENABLED PROTOCOLS                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  LENDING & BORROWING                                                         │  │
│  │  [✓] Aave V3                 [✓] Aave V2            [ ] Compound            │  │
│  │  [ ] Morpho                  [ ] Spark              [ ] Venus               │  │
│  │                                                                               │  │
│  │  DEX & SWAPS                                                                 │  │
│  │  [✓] 1inch                   [ ] Uniswap            [ ] SushiSwap           │  │
│  │  [ ] Curve                   [ ] Balancer           [ ] PancakeSwap         │  │
│  │                                                                               │  │
│  │  STAKING                                                                     │  │
│  │  [ ] Lido                    [ ] Rocket Pool        [ ] Frax                │  │
│  │                                                                               │  │
│  │  BRIDGES                                                                     │  │
│  │  [ ] Across                  [ ] Stargate           [ ] Hop                 │  │
│  │                                                                               │  │
│  │  4 protocols enabled                                                         │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ENABLED OPERATIONS                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  [✓] Supply/Lend             [✓] Borrow             [✓] Repay               │  │
│  │  [✓] Withdraw                [✓] Swap               [ ] Stake               │  │
│  │  [ ] Bridge                  [ ] Provide LP         [✓] View Only           │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Risk Configuration Tab

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✏️ Edit Project: Aave                                    [Preview] [Save Changes]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Basic Info]  [System Prompt]  [Protocols]  [Risk Config]  [Advanced]              │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  TRANSACTION LIMITS                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Maximum Position Size (USD)                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [$] [50,000                                            ]                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Maximum value per transaction                                               │  │
│  │                                                                               │  │
│  │  Maximum Slippage (bps)                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |───────────●────────────────────|           100 bps (1%)           │  │  │
│  │  │     10                              500                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Maximum Leverage                                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │     |───────●────────────────────────|           3x                     │  │  │
│  │  │     1x                               10x                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SECURITY REQUIREMENTS                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  [✓] Require 2FA for transactions over $1,000                               │  │
│  │  [✓] Daily transaction limit per user: [$100,000    ]                       │  │
│  │  [ ] Whitelist-only token swaps                                              │  │
│  │  [✓] Block high-risk tokens                                                 │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  TOKEN RESTRICTIONS                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Allowed Tokens (leave empty for all)                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [ETH ×] [WETH ×] [USDC ×] [USDT ×] [DAI ×] [WBTC ×] [+ Add]           │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Blocked Tokens                                                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [+ Add blocked token]                                                   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Project Details

```typescript
// GET /admin/projects/{id}
interface GetProjectResponse {
  success: true;
  data: {
    project: Project;
  };
}

interface Project {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  visibility: 'public' | 'private' | 'invite_only';
  system_prompt: string;
  welcome_message: string;
  enabled_chains: string[];
  enabled_protocols: string[];
  enabled_tools: string[];
  risk_config: RiskConfig;
  status: 'active' | 'paused' | 'archived';
  created_at: string;
  updated_at: string;
}

interface RiskConfig {
  max_position_usd: number;
  max_slippage_bps: number;
  max_leverage: number;
  require_2fa: boolean;
  require_2fa_threshold_usd: number;
  daily_limit_usd: number;
  allowed_tokens: string[];
  blocked_tokens: string[];
}
```

### Update Project

```typescript
// PUT /admin/projects/{id}
interface UpdateProjectRequest {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  visibility?: string;
  system_prompt?: string;
  welcome_message?: string;
  enabled_chains?: string[];
  enabled_protocols?: string[];
  enabled_tools?: string[];
  risk_config?: Partial<RiskConfig>;
  status?: string;
}
```

---

## 🎬 Motion Design

```typescript
const projectEditorAnimations = {
  tabSwitch: {
    opacity: [0, 1],
    x: [20, 0],
    transition: { duration: 0.2 }
  },
  
  tokenPillAdd: {
    scale: [0, 1],
    transition: { type: 'spring', stiffness: 300 }
  },
  
  sliderThumb: {
    scale: 1.2,
    transition: { duration: 0.15 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Project Editor*

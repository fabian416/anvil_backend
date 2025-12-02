# FRONTEND_ADMIN_PROJECTS_LIST

## Admin Projects Management Module

**User Type:** Admin  
**Module:** Projects List & Dashboard  
**Route:** `/admin/projects`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator/Viewer)

---

## 📋 Module Overview

### Title
**Projects Management** - DeFi Context Configuration Hub

### Description
Central management interface for admin-configured DeFi projects. Enables administrators to create, configure, and manage specialized project contexts (Savings, Earning, Aave, Trading, etc.) that provide users with tailored AI assistance, knowledge bases, and tool configurations.

### Key Capabilities
- View all projects with status, user count, and engagement metrics
- Create new projects with wizard-guided setup
- Clone existing projects for quick configuration
- Toggle project status (Draft, Active, Paused, Archived)
- View real-time project analytics summary
- Manage project visibility and access controls
- Bulk actions for project management

---

## 👤 User Stories

### US-ADMIN-PROJ-001: View All Projects
**As a** platform administrator  
**I want to** see all configured projects in a comprehensive dashboard  
**So that** I can understand the project landscape and identify areas needing attention

**Acceptance Criteria:**
- Projects displayed in card grid with key metrics
- Each card shows: name, icon, status, user count, engagement score
- Filter by status (Active, Draft, Paused, Archived)
- Search by project name or description
- Sort by name, created date, user count, or engagement
- Quick stats summary at top (total projects, active users, total sessions)

### US-ADMIN-PROJ-002: Create New Project
**As a** platform administrator  
**I want to** create a new project with guided setup  
**So that** I can efficiently configure specialized DeFi contexts

**Acceptance Criteria:**
- Multi-step wizard: Basic Info → System Prompt → Tools & Protocols → Risk Config → Review
- Auto-generate slug from name with uniqueness check
- Rich text editor for system prompt with token counter
- Protocol/chain selection with visual checkboxes
- Tool configuration with enable/disable toggles
- Risk parameter sliders with recommended defaults
- Preview mode before final creation
- Save as draft option at any step

### US-ADMIN-PROJ-003: Clone Existing Project
**As a** platform administrator  
**I want to** clone an existing project as a starting point  
**So that** I can quickly create similar projects without starting from scratch

**Acceptance Criteria:**
- Clone button on project card and detail view
- New slug required (auto-suggested with "-copy" suffix)
- All configuration copied except user assignments
- Knowledge base documents optionally cloned
- Clone created as Draft status
- Navigate to editor after cloning

### US-ADMIN-PROJ-004: Change Project Status
**As a** platform administrator  
**I want to** activate, pause, or archive projects  
**So that** I can control project availability

**Acceptance Criteria:**
- Status dropdown on project card
- Confirmation dialog for status changes
- Cannot activate project without system prompt
- Pausing shows warning about affected users
- Archiving moves project to archived section
- Archived projects can be restored
- Status change logged in audit trail

### US-ADMIN-PROJ-005: View Project Quick Stats
**As a** platform administrator  
**I want to** see engagement metrics for each project  
**So that** I can identify successful and underperforming projects

**Acceptance Criteria:**
- User count (total assigned, active in 7 days)
- Session count (total, average per user)
- Satisfaction score (average rating)
- Knowledge base hit rate
- Transaction volume (if applicable)
- Trend indicators (up/down vs previous period)

### US-ADMIN-PROJ-006: Bulk Project Actions
**As a** platform administrator  
**I want to** perform actions on multiple projects at once  
**So that** I can efficiently manage large numbers of projects

**Acceptance Criteria:**
- Multi-select checkboxes on project cards
- Bulk actions: Activate, Pause, Archive, Delete
- Confirmation dialog showing affected projects
- Progress indicator for bulk operations
- Summary of successful/failed operations

### US-ADMIN-PROJ-007: Featured Projects Management
**As a** platform administrator  
**I want to** mark projects as featured  
**So that** users see recommended projects first

**Acceptance Criteria:**
- Toggle featured status on project card
- Featured projects highlighted with badge
- Drag-and-drop reorder for featured projects
- Maximum 5 featured projects at a time
- Featured order affects user project list display

---

## 🖼️ Views & Wireframes

### View 1: Projects Dashboard (Default View)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📁 Projects                                           [+ Create Project] [⋮ More]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📊 10 Projects    👥 3,245 Users    💬 12,850 Sessions (7d)    ⭐ 4.6 Avg     ││
│  │     8 active           2,156 active        +18% vs last week       Rating      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ [🔍 Search projects...]   Status: [All ▼]   [⭐ Featured Only]   Sort: [Users ▼]││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ⭐ FEATURED PROJECTS                                                               │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐            │
│  │ 💰 Smart Savings    │ │ 🏦 Aave Lending     │ │ 📈 DeFi Trading     │            │
│  │                     │ │                     │ │                     │            │
│  │ Low-risk yield      │ │ Lending & borrowing │ │ Spot & perpetuals   │            │
│  │ optimization        │ │ assistance          │ │ trading             │            │
│  │                     │ │                     │ │                     │            │
│  │ 🟢 Active           │ │ 🟢 Active           │ │ 🟢 Active           │            │
│  │ 👥 520 users        │ │ 👥 412 users        │ │ 👥 389 users        │            │
│  │ ⭐ 4.7  📈 +12%     │ │ ⭐ 4.8  📈 +8%      │ │ ⭐ 4.5  📈 +15%     │            │
│  │                     │ │                     │ │                     │            │
│  │ [Edit] [⋮]          │ │ [Edit] [⋮]          │ │ [Edit] [⋮]          │            │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘            │
│                                                                                      │
│  ALL PROJECTS                                                                        │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐            │
│  │ 🌾 Yield Farming    │ │ 🥩 Staking Hub      │ │ 🌉 Cross-Chain      │            │
│  │                     │ │                     │ │    Bridge           │            │
│  │ Active LP strategies│ │ ETH staking & LSTs  │ │ Safe cross-chain    │            │
│  │                     │ │                     │ │ transfers           │            │
│  │ 🟢 Active           │ │ 🟢 Active           │ │ 🟢 Active           │            │
│  │ 👥 298 users        │ │ 👥 245 users        │ │ 👥 198 users        │            │
│  │ ⭐ 4.4  📈 +5%      │ │ ⭐ 4.6  📈 +10%     │ │ ⭐ 4.3  📉 -2%      │            │
│  │                     │ │                     │ │                     │            │
│  │ [Edit] [⋮]          │ │ [Edit] [⋮]          │ │ [Edit] [⋮]          │            │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘            │
│                                                                                      │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐            │
│  │ 📊 Portfolio        │ │ 🗳️ DAO Governance   │ │ 🛡️ Risk Management │            │
│  │    Manager          │ │                     │ │                     │            │
│  │ Portfolio tracking  │ │ DAO participation   │ │ Position protection │            │
│  │                     │ │                     │ │                     │            │
│  │ 🟢 Active           │ │ 🟡 Paused           │ │ 🟢 Active           │            │
│  │ 👥 187 users        │ │ 👥 89 users         │ │ 👥 156 users        │            │
│  │ ⭐ 4.5  → 0%        │ │ ⭐ 4.2  —           │ │ ⭐ 4.7  📈 +22%     │            │
│  │                     │ │                     │ │                     │            │
│  │ [Edit] [⋮]          │ │ [Edit] [⋮]          │ │ [Edit] [⋮]          │            │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘            │
│                                                                                      │
│  ┌─────────────────────┐ ┌─────────────────────┐                                    │
│  │ 🎨 NFT Finance      │ │ ＋                   │                                    │
│  │                     │ │                     │                                    │
│  │ NFT collateral &    │ │ Create New          │                                    │
│  │ lending             │ │ Project             │                                    │
│  │                     │ │                     │                                    │
│  │ 📝 Draft            │ │                     │                                    │
│  │ 👥 0 users          │ │ [+ Create]          │                                    │
│  │ Not published       │ │                     │                                    │
│  │                     │ │                     │                                    │
│  │ [Edit] [⋮]          │ │                     │                                    │
│  └─────────────────────┘ └─────────────────────┘                                    │
│                                                                                      │
│  Showing 10 projects                                                                │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Create Project Wizard - Step 1: Basic Info

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📁 Create New Project                                                      [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Progress ──────────────────────────────────────────────────────────────────────┐│
│  │  [●] Basic Info → [ ] System Prompt → [ ] Tools → [ ] Risk → [ ] Review        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  BASIC INFORMATION                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Project Name *                                                                 ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Leverage Trading Pro                                                       │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │  A descriptive name for the project                                            ││
│  │                                                                                  ││
│  │  Slug *                                                                         ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ leverage-trading-pro                                          ✅ Available │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │  URL-friendly identifier (auto-generated, editable)                            ││
│  │                                                                                  ││
│  │  Description *                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Advanced leverage trading strategies with risk management and position    │││
│  │  │ sizing assistance for experienced DeFi traders.                           │││
│  │  │                                                                            │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │  Brief description shown to users (max 200 chars)              125/200         ││
│  │                                                                                  ││
│  │  Icon                           Color                                           ││
│  │  ┌────────────────────┐        ┌────────────────────────────────────────────┐  ││
│  │  │ 📊 Selected        │        │ [🔴][🟠][🟡][🟢][🔵][🟣][⚫]              │  ││
│  │  │                    │        │  #3B82F6 (Blue) ◀ Selected                 │  ││
│  │  │ [📈][💹][📊][⚡]  │        └────────────────────────────────────────────┘  ││
│  │  │ [🎯][💰][🚀][⭐]  │                                                        ││
│  │  └────────────────────┘                                                        ││
│  │                                                                                  ││
│  │  Visibility                                                                     ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ [●] Public - All users can see and join                                    │││
│  │  │ [ ] Private - Only assigned users can access                               │││
│  │  │ [ ] Invite Only - Requires invitation to join                              │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ────────────────────────────────────────────────────────────────────────────────   │
│  [Cancel]                              [Save as Draft]     [Next: System Prompt →]  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Create Project Wizard - Step 2: System Prompt

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📁 Create New Project                                                      [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Progress ──────────────────────────────────────────────────────────────────────┐│
│  │  [✓] Basic Info → [●] System Prompt → [ ] Tools → [ ] Risk → [ ] Review        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  SYSTEM PROMPT                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  System Prompt *                                          Tokens: 245 / 2000   ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ You are Anvil's Leverage Trading Specialist, helping experienced traders  │││
│  │  │ execute sophisticated trading strategies with proper risk management.      │││
│  │  │                                                                            │││
│  │  │ Your expertise includes:                                                   │││
│  │  │ - Perpetual futures on Hyperliquid, GMX, dYdX                             │││
│  │  │ - Leverage position management (2x-10x)                                    │││
│  │  │ - Risk/reward calculations and position sizing                             │││
│  │  │ - Stop-loss and take-profit strategies                                     │││
│  │  │ - Funding rate analysis and optimization                                   │││
│  │  │                                                                            │││
│  │  │ Guidelines:                                                                │││
│  │  │ - Always calculate and display liquidation price                          │││
│  │  │ - Warn about high leverage risks prominently                              │││
│  │  │ - Never encourage positions beyond user's risk tolerance                  │││
│  │  │ - Require confirmation for leverage above 5x                              │││
│  │  │                                                                            │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  [📋 Load Template ▼]  [✨ AI Assist]  [👁️ Preview]                            ││
│  │                                                                                  ││
│  │  Welcome Message *                                                              ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ Welcome to Leverage Trading Pro! 📊                                        │││
│  │  │                                                                            │││
│  │  │ I'm here to help you execute sophisticated trading strategies safely.     │││
│  │  │                                                                            │││
│  │  │ I can help you with:                                                       │││
│  │  │ • Opening and managing leveraged positions                                 │││
│  │  │ • Calculating optimal position sizes                                       │││
│  │  │ • Setting stop-loss and take-profit levels                                 │││
│  │  │ • Analyzing funding rates                                                  │││
│  │  │                                                                            │││
│  │  │ What trade are you planning today?                                         │││
│  │  │                                                                            │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │  Shown when user first enters the project                                      ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ────────────────────────────────────────────────────────────────────────────────   │
│  [← Back]                              [Save as Draft]     [Next: Tools & Chains →] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 4: Create Project Wizard - Step 3: Tools & Protocols

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📁 Create New Project                                                      [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Progress ──────────────────────────────────────────────────────────────────────┐│
│  │  [✓] Basic Info → [✓] System Prompt → [●] Tools → [ ] Risk → [ ] Review        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  TOOLS & PROTOCOLS                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Enabled Tools                                              Selected: 4/12      ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │                                                                            │││
│  │  │  [✓] 🔄 swap          [✓] 📈 trade_perps    [ ] 💰 lend                   │││
│  │  │      Token swaps          Perpetual trading      Lending deposits         │││
│  │  │                                                                            │││
│  │  │  [ ] 💳 borrow        [ ] 🥩 stake           [ ] 🌉 bridge                │││
│  │  │      Borrowing            Staking                Cross-chain              │││
│  │  │                                                                            │││
│  │  │  [✓] 📊 analyze       [ ] 🏥 check_health    [✓] 🎯 calculate_position   │││
│  │  │      Portfolio analysis   Health factor          Position sizing          │││
│  │  │                                                                            │││
│  │  │  [ ] 🗳️ governance    [ ] 🛡️ hedge          [ ] 💎 nft_lend              │││
│  │  │      DAO voting           Hedging                NFT collateral           │││
│  │  │                                                                            │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  Enabled Protocols                                          Selected: 3/15      ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │                                                                            │││
│  │  │  [ ] 🔷 Aave          [ ] 🟣 Compound       [ ] 🔵 Uniswap                │││
│  │  │  [✓] 🟢 Hyperliquid   [✓] 🔴 GMX           [✓] 🟡 dYdX                   │││
│  │  │  [ ] 🟤 Curve         [ ] ⚪ Lido          [ ] 🟠 Rocket Pool            │││
│  │  │  [ ] 🔷 Morpho        [ ] 🟣 Yearn         [ ] 🔵 Convex                 │││
│  │  │  [ ] 🟢 1inch         [ ] 🔴 Stargate      [ ] 🟡 Across                 │││
│  │  │                                                                            │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  Enabled Chains                                             Selected: 2/6       ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │                                                                            │││
│  │  │  [✓] ◆ Ethereum       [✓] 🔵 Arbitrum      [ ] 🟣 Polygon                │││
│  │  │  [ ] 🔴 Optimism      [ ] 🔵 Base          [ ] 🟢 zkSync                 │││
│  │  │                                                                            │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ────────────────────────────────────────────────────────────────────────────────   │
│  [← Back]                              [Save as Draft]     [Next: Risk Config →]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 5: Create Project Wizard - Step 4: Risk Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📁 Create New Project                                                      [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Progress ──────────────────────────────────────────────────────────────────────┐│
│  │  [✓] Basic Info → [✓] System Prompt → [✓] Tools → [●] Risk → [ ] Review        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  RISK CONFIGURATION                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  POSITION LIMITS                                                                ││
│  │  ─────────────────────────────────────────────────────────────────────────────  ││
│  │                                                                                  ││
│  │  Maximum Position Size (USD)                                                    ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ [$] [25,000                              ]                                 │││
│  │  │     |─────────────────●───────────────────|                                │││
│  │  │     1K                                  100K                               │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  Maximum Leverage                                                               ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ [10x                                    ]                                  │││
│  │  │     |─────────────────────────────●─────|                                  │││
│  │  │     2x                                 20x                                 │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │  ⚠️ Leverage above 5x will show additional risk warnings                       ││
│  │                                                                                  ││
│  │  Maximum Slippage (basis points)                                                ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ [100 bps (1%)                           ]                                  │││
│  │  │     |───────●──────────────────────────|                                   │││
│  │  │     10bps                            500bps                                │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  SAFETY REQUIREMENTS                                                            ││
│  │  ─────────────────────────────────────────────────────────────────────────────  ││
│  │                                                                                  ││
│  │  [✓] Require transaction simulation before execution                           ││
│  │  [✓] Require 2FA for transactions above $5,000                                 ││
│  │  [✓] Show liquidation price warning for leveraged positions                    ││
│  │  [ ] Conservative mode (additional confirmations for all transactions)         ││
│  │                                                                                  ││
│  │  TOKEN RESTRICTIONS                                                             ││
│  │  ─────────────────────────────────────────────────────────────────────────────  ││
│  │                                                                                  ││
│  │  Allowed Tokens (leave empty for all)                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ [ETH ×] [BTC ×] [USDC ×] [+ Add token...]                                 │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  Blocked Tokens                                                                 ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐││
│  │  │ [SHIB ×] [DOGE ×] [+ Add token...]                                        │││
│  │  └────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ────────────────────────────────────────────────────────────────────────────────   │
│  [← Back]                              [Save as Draft]     [Next: Review →]         │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 6: Project Card Actions Menu

```
┌─────────────────────┐
│ 💰 Smart Savings    │
│                     │
│ Low-risk yield      │──────┐
│ optimization        │      │
│                     │      │
│ 🟢 Active           │      ▼
│ 👥 520 users        │  ┌───────────────────────┐
│ ⭐ 4.7  📈 +12%     │  │ ✏️ Edit Project       │
│                     │  │ 📋 Clone Project      │
│ [Edit] [⋮]◀────────────│ 👥 Manage Users       │
└─────────────────────┘  │ 📊 View Analytics     │
                         │ ─────────────────────  │
                         │ ⭐ Set as Featured    │
                         │ ─────────────────────  │
                         │ ⏸️ Pause Project      │
                         │ 🗄️ Archive Project    │
                         │ 🗑️ Delete Project     │
                         └───────────────────────┘
```

---

## 🔌 API Endpoints

### List Projects

```typescript
// GET /admin/projects
// Get all projects with optional filters

interface GetProjectsRequest {
  status?: 'draft' | 'active' | 'paused' | 'archived';
  visibility?: 'public' | 'private' | 'invite_only';
  is_featured?: boolean;
  search?: string;
  sort_by?: 'name' | 'created_at' | 'users' | 'engagement';
  sort_order?: 'asc' | 'desc';
  include_stats?: boolean;
}

interface GetProjectsResponse {
  success: true;
  data: {
    projects: ProjectSummary[];
    summary: {
      total: number;
      active: number;
      draft: number;
      paused: number;
      archived: number;
      total_users: number;
      active_users_7d: number;
      total_sessions_7d: number;
      avg_satisfaction: number;
    };
  };
}

interface ProjectSummary {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  status: 'draft' | 'active' | 'paused' | 'archived';
  visibility: 'public' | 'private' | 'invite_only';
  is_featured: boolean;
  display_order: number;
  stats?: {
    total_users: number;
    active_users_7d: number;
    total_sessions: number;
    sessions_7d: number;
    avg_satisfaction: number;
    engagement_trend: number;    // % change vs previous period
  };
  created_at: string;
  updated_at: string;
}
```

### Create Project

```typescript
// POST /admin/projects
// Create new project

interface CreateProjectRequest {
  slug: string;
  name: string;
  description: string;
  icon?: string;
  color?: string;
  visibility?: 'public' | 'private' | 'invite_only';
  system_prompt: string;
  welcome_message?: string;
  enabled_protocols?: string[];
  enabled_chains?: string[];
  enabled_tools?: string[];
  risk_config?: RiskConfig;
  status?: 'draft' | 'active';
}

interface RiskConfig {
  max_slippage_bps?: number;
  max_position_usd?: number;
  max_leverage?: number;
  max_daily_volume_usd?: number;
  require_2fa_for_transactions?: boolean;
  require_simulation?: boolean;
  allowed_tokens?: string[];
  blocked_tokens?: string[];
  min_health_factor?: number;
  conservative_mode?: boolean;
}

// Validation
const createProjectValidation = {
  slug: {
    required: true,
    pattern: /^[a-z0-9-]+$/,
    minLength: 2,
    maxLength: 50,
    unique: true
  },
  name: {
    required: true,
    minLength: 2,
    maxLength: 100
  },
  description: {
    required: true,
    minLength: 10,
    maxLength: 200
  },
  system_prompt: {
    required: true,
    minLength: 50,
    maxLength: 10000
  },
  'risk_config.max_slippage_bps': {
    min: 1,
    max: 500
  },
  'risk_config.max_position_usd': {
    min: 100,
    max: 1000000
  },
  'risk_config.max_leverage': {
    min: 1,
    max: 100
  }
};

interface CreateProjectResponse {
  success: true;
  data: {
    project_id: string;
    slug: string;
    knowledge_base_id: string;
    status: string;
  };
}
```

### Update Project Status

```typescript
// PATCH /admin/projects/{id}/status
// Update project status

interface UpdateProjectStatusRequest {
  status: 'draft' | 'active' | 'paused' | 'archived';
  reason?: string;
}

interface UpdateProjectStatusResponse {
  success: true;
  data: {
    project_id: string;
    previous_status: string;
    new_status: string;
    affected_users: number;
    updated_at: string;
  };
}
```

### Clone Project

```typescript
// POST /admin/projects/{id}/clone
// Clone existing project

interface CloneProjectRequest {
  new_slug: string;
  new_name: string;
  clone_knowledge_base?: boolean;
}

interface CloneProjectResponse {
  success: true;
  data: {
    original_project_id: string;
    new_project_id: string;
    new_slug: string;
    status: 'draft';
    knowledge_documents_cloned: number;
  };
}
```

### Update Featured Order

```typescript
// PUT /admin/projects/featured
// Update featured projects and order

interface UpdateFeaturedRequest {
  featured_project_ids: string[];  // Ordered list
}

interface UpdateFeaturedResponse {
  success: true;
  data: {
    updated: Array<{
      project_id: string;
      is_featured: boolean;
      display_order: number;
    }>;
  };
}
```

### Check Slug Availability

```typescript
// GET /admin/projects/check-slug?slug=my-project
// Check if slug is available

interface CheckSlugResponse {
  success: true;
  data: {
    slug: string;
    available: boolean;
    suggestion?: string;  // If not available, suggest alternative
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface ProjectsListState {
  // Data
  projects: ProjectSummary[];
  summary: ProjectsSummary | null;
  
  // UI State
  loading: {
    list: boolean;
    create: boolean;
    clone: boolean;
    statusUpdate: boolean;
  };
  
  errors: {
    list: Error | null;
    create: Error | null;
    clone: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    status: 'all' | 'draft' | 'active' | 'paused' | 'archived';
    featured: boolean;
  };
  
  // Sorting
  sortBy: 'name' | 'created_at' | 'users' | 'engagement';
  sortOrder: 'asc' | 'desc';
  
  // Selection
  selectedProjects: string[];
  bulkActionInProgress: boolean;
  
  // Wizard
  wizardOpen: boolean;
  wizardStep: number;
  wizardData: Partial<CreateProjectRequest>;
  
  // Clone
  cloneDialogOpen: boolean;
  projectToClone: ProjectSummary | null;
  
  // Featured Reordering
  isReorderingFeatured: boolean;
  pendingFeaturedOrder: string[];
  
  // Actions Menu
  activeActionMenu: string | null;
}
```

---

## 🎨 Component Specifications

### ProjectCard

```typescript
interface ProjectCardProps {
  project: ProjectSummary;
  onEdit: (id: string) => void;
  onClone: (project: ProjectSummary) => void;
  onStatusChange: (id: string, status: string) => void;
  onToggleFeatured: (id: string) => void;
  onViewAnalytics: (id: string) => void;
  onManageUsers: (id: string) => void;
  onDelete: (id: string) => void;
  selected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  draggable?: boolean;
}

// Usage
<ProjectCard
  project={savingsProject}
  onEdit={handleEdit}
  onClone={handleClone}
  onStatusChange={handleStatusChange}
  onToggleFeatured={handleToggleFeatured}
/>
```

### ProjectWizard

```typescript
interface ProjectWizardProps {
  open: boolean;
  onClose: () => void;
  onComplete: (project: CreateProjectRequest) => void;
  initialData?: Partial<CreateProjectRequest>;
  editMode?: boolean;
}

// Usage
<ProjectWizard
  open={wizardOpen}
  onClose={() => setWizardOpen(false)}
  onComplete={handleCreateProject}
/>
```

### ProjectStatusBadge

```typescript
interface ProjectStatusBadgeProps {
  status: 'draft' | 'active' | 'paused' | 'archived';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

// Usage
<ProjectStatusBadge status="active" size="md" showLabel />
```

### ProjectStatsBar

```typescript
interface ProjectStatsBarProps {
  stats: {
    users: number;
    activeUsers: number;
    satisfaction: number;
    trend: number;
  };
  compact?: boolean;
}
```

### CloneProjectDialog

```typescript
interface CloneProjectDialogProps {
  project: ProjectSummary;
  open: boolean;
  onClose: () => void;
  onClone: (data: CloneProjectRequest) => void;
  loading?: boolean;
}
```

---

## 🎬 Motion Design

```typescript
const projectsAnimations = {
  // Card grid stagger
  gridStagger: {
    container: {
      animate: { transition: { staggerChildren: 0.05 } }
    },
    item: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 }
    }
  },
  
  // Card hover
  cardHover: {
    scale: 1.02,
    boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
    transition: { duration: 0.2 }
  },
  
  // Status change
  statusChange: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.3 }
  },
  
  // Wizard step transition
  wizardStep: {
    initial: { opacity: 0, x: 50 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -50 },
    transition: { duration: 0.3 }
  },
  
  // Featured star
  featuredStar: {
    scale: [1, 1.3, 1],
    rotate: [0, 15, -15, 0],
    transition: { duration: 0.5 }
  },
  
  // Drag reorder
  dragItem: {
    scale: 1.05,
    boxShadow: '0 15px 50px rgba(0,0,0,0.3)',
    zIndex: 1000
  },
  
  // Success creation
  createSuccess: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    transition: { type: 'spring', stiffness: 200 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const projectsShortcuts = {
  'mod+n': 'Create new project',
  'mod+f': 'Focus search',
  '/': 'Focus search (alternative)',
  'mod+a': 'Select all projects',
  'escape': 'Clear selection / Close wizard',
  'enter': 'Edit selected project',
  'del': 'Delete selected projects',
  'f': 'Toggle featured filter',
  's': 'Sort by next column',
};
```

---

## ⚠️ Error Handling

```typescript
const projectErrorCodes = {
  // Validation
  PROJ_VAL_001: 'Project name is required',
  PROJ_VAL_002: 'Slug must be URL-friendly (lowercase, numbers, hyphens)',
  PROJ_VAL_003: 'Slug is already taken',
  PROJ_VAL_004: 'System prompt is required for activation',
  PROJ_VAL_005: 'Description must be between 10-200 characters',
  
  // Business Logic
  PROJ_BUS_001: 'Cannot activate project without system prompt',
  PROJ_BUS_002: 'Cannot delete project with active users',
  PROJ_BUS_003: 'Maximum 5 featured projects allowed',
  PROJ_BUS_004: 'Cannot archive project with pending transactions',
  
  // Clone
  PROJ_CLN_001: 'Failed to clone project',
  PROJ_CLN_002: 'Failed to clone knowledge base',
  
  // System
  PROJ_SYS_001: 'Failed to load projects',
  PROJ_SYS_002: 'Failed to create project',
  PROJ_SYS_003: 'Failed to update project status',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| POST /projects | slug | string | Yes | 2-50 chars, lowercase, no spaces |
| POST /projects | name | string | Yes | 2-100 chars |
| POST /projects | description | string | Yes | 10-200 chars |
| POST /projects | system_prompt | string | Yes | 50-10000 chars |
| POST /projects | icon | string | No | Valid emoji or icon name |
| POST /projects | color | string | No | Valid hex color |
| POST /projects/clone | new_slug | string | Yes | Unique, URL-friendly |

---

## 🔒 Security Considerations

1. **Access Control:** Only Admin users can create/edit/delete projects
2. **System Prompt Injection:** Prompts sanitized to prevent injection attacks
3. **Knowledge Base Privacy:** Documents isolated per project
4. **Audit Trail:** All project changes logged with user and timestamp
5. **Bulk Actions:** Rate limited to prevent abuse
6. **Status Changes:** Require confirmation, notify affected users

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Projects List*  
*User Type: Admin*

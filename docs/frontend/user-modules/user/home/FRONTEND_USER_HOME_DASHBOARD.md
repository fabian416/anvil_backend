# FRONTEND_USER_HOME_DASHBOARD

## User Home Dashboard Module

**User Type:** Authenticated User  
**Module:** Home Dashboard  
**Route:** `/home`, `/` (default)  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Home Dashboard** - Portfolio Overview & Quick Actions

### Description
The main landing screen after authentication, providing a comprehensive view of the user's portfolio, quick access to common actions, and AI-powered insights.

### Key Capabilities
- Total portfolio value display
- Multi-chain asset breakdown
- Quick action buttons
- Recent activity feed
- Market highlights
- AI insights/suggestions

---

## 👤 User Stories

### US-USER-HOME-001: View Portfolio Value
**As a** user  
**I want to** see my total portfolio value  
**So that** I know my overall position at a glance

### US-USER-HOME-002: Access Quick Actions
**As a** user  
**I want to** quickly access common actions  
**So that** I can perform tasks efficiently

### US-USER-HOME-003: View Recent Activity
**As a** user  
**I want to** see my recent transactions  
**So that** I can track my activity

### US-USER-HOME-004: Get AI Insights
**As a** user  
**I want to** receive personalized suggestions  
**So that** I can optimize my DeFi strategy

---

## 🖼️ Views & Wireframes

### View 1: Home Dashboard (Mobile)

```
┌─────────────────────────────────────┐
│ 🔔 3                     ⚙️        │
│                                     │
│  Good morning, Alice 👋             │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  Total Portfolio                ││
│  │                                 ││
│  │  $45,230.42                     ││
│  │  ↑ $1,234.56 (+2.8%) today     ││
│  │                                 ││
│  │  ████████████████░░░░ ETH 56%  ││
│  │  ████████░░░░░░░░░░░░ ARB 28%  ││
│  │  ████░░░░░░░░░░░░░░░░ POLY 12% ││
│  │  ██░░░░░░░░░░░░░░░░░░ BASE 4%  ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Quick Actions                      │
│  ┌───────┐ ┌───────┐ ┌───────┐     │
│  │  🔄   │ │  📤   │ │  💰   │     │
│  │ Swap  │ │ Send  │ │ Earn  │     │
│  └───────┘ └───────┘ └───────┘     │
│  ┌───────┐ ┌───────┐ ┌───────┐     │
│  │  🌉   │ │  📥   │ │  🤖   │     │
│  │Bridge │ │Receive│ │  AI   │     │
│  └───────┘ └───────┘ └───────┘     │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  💡 AI Insight                      │
│  ┌─────────────────────────────────┐│
│  │ ETH staking yields are up 0.3% ││
│  │ this week. You could earn ~$45 ││
│  │ more monthly by staking your   ││
│  │ idle ETH.          [Explore →] ││
│  └─────────────────────────────────┘│
│                                     │
│  Recent Activity                    │
│  ┌─────────────────────────────────┐│
│  │ 🔄 Swap                  2h ago ││
│  │    0.5 ETH → 1,125 USDC        ││
│  │    ✅ Success                   ││
│  ├─────────────────────────────────┤│
│  │ 💰 Supply                5h ago ││
│  │    500 USDC to Aave            ││
│  │    ✅ Success                   ││
│  ├─────────────────────────────────┤│
│  │ 🌉 Bridge              Yesterday││
│  │    0.2 ETH → Arbitrum          ││
│  │    ✅ Success                   ││
│  │                                 ││
│  │         [View All →]            ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
│  Home  Wallet  Chat  Markets Profile│
└─────────────────────────────────────┘
```

### View 2: Home Dashboard (Expanded Portfolio)

```
┌─────────────────────────────────────┐
│ 🔔 3                     ⚙️        │
│                                     │
│  Good morning, Alice 👋             │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Total Portfolio                ││
│  │                                 ││
│  │  $45,230.42                     ││
│  │  ↑ $1,234.56 (+2.8%) today     ││
│  │                                 ││
│  │  [24H] [7D] [30D] [ALL]        ││
│  │                                 ││
│  │  $50K ┤          ╭────         ││
│  │       │    ╭─────╯             ││
│  │  $45K ┤────╯                   ││
│  │       │                        ││
│  │  $40K ┼─────────────────────▶  ││
│  │        Mon  Tue  Wed  Thu  Fri ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Assets by Chain                    │
│  ┌─────────────────────────────────┐│
│  │ ◆ Ethereum            $25,329  ││
│  │   3.2 ETH, 5,000 USDC, ...     ││
│  ├─────────────────────────────────┤│
│  │ ◆ Arbitrum            $12,670  ││
│  │   1.1 ETH, 2,500 USDC, ...     ││
│  ├─────────────────────────────────┤│
│  │ ◆ Polygon              $5,431  ││
│  │   2,000 USDC, 500 MATIC        ││
│  ├─────────────────────────────────┤│
│  │ ◆ Base                 $1,800  ││
│  │   0.3 ETH, 800 USDC            ││
│  └─────────────────────────────────┘│
│                                     │
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

### View 3: Pull to Refresh State

```
┌─────────────────────────────────────┐
│ 🔔 3                     ⚙️        │
│                                     │
│            ↻ Refreshing...          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░  ││
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░  ││
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░  ││
│  └─────────────────────────────────┘│
│                                     │
...
```

---

## 🔌 API Endpoints

### Get Dashboard Data

```typescript
// GET /api/users/me/dashboard
interface GetDashboardResponse {
  success: true;
  data: {
    portfolio: {
      total_value_usd: number;
      change_24h: {
        amount_usd: number;
        percentage: number;
        direction: 'up' | 'down' | 'flat';
      };
      breakdown_by_chain: Array<{
        chain: string;
        value_usd: number;
        percentage: number;
        assets_summary: string;
      }>;
      chart_data: TimeSeriesPoint[];
    };
    ai_insight?: {
      id: string;
      title: string;
      message: string;
      action_type?: string;
      action_url?: string;
    };
    recent_activity: Transaction[];
    pending_actions?: Array<{
      type: string;
      message: string;
      action_url: string;
    }>;
  };
}

interface Transaction {
  id: string;
  type: 'swap' | 'send' | 'receive' | 'supply' | 'borrow' | 'bridge' | 'stake';
  status: 'pending' | 'success' | 'failed';
  description: string;
  amount_display: string;
  timestamp: string;
  chain: string;
}
```

### Dismiss AI Insight

```typescript
// POST /api/users/me/insights/{id}/dismiss
interface DismissInsightResponse {
  success: true;
}
```

---

## 🎬 Motion Design

```typescript
const homeAnimations = {
  portfolioCounter: {
    textContent: { from: 0, to: 'value' },
    transition: { duration: 1.2, ease: 'easeOut' }
  },
  
  chainBar: {
    width: ['0%', 'percentage%'],
    transition: { duration: 0.8, ease: 'easeOut', delay: 'stagger' }
  },
  
  quickActionPress: {
    scale: [1, 0.95, 1],
    transition: { duration: 0.15 }
  },
  
  insightSlide: {
    x: [50, 0],
    opacity: [0, 1],
    transition: { duration: 0.3 }
  },
  
  activityItem: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'stagger' }
  },
  
  pullToRefresh: {
    rotate: [0, 360],
    transition: { duration: 1, repeat: Infinity, ease: 'linear' }
  }
};
```

---

## 🎨 Component Specifications

```typescript
interface PortfolioCardProps {
  totalValue: number;
  change24h: {
    amount: number;
    percentage: number;
    direction: 'up' | 'down' | 'flat';
  };
  breakdown: ChainBreakdown[];
  onPress?: () => void;
}

interface QuickActionButtonProps {
  icon: string;
  label: string;
  onPress: () => void;
  badge?: number;
}

interface AIInsightCardProps {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  onDismiss: () => void;
}

interface ActivityItemProps {
  transaction: Transaction;
  onPress: () => void;
}
```

---

## ⌨️ Gestures & Interactions

```typescript
const homeGestures = {
  pullToRefresh: {
    threshold: 80,
    onRefresh: () => void,
  },
  
  portfolioTap: {
    onPress: () => 'navigate to portfolio detail',
  },
  
  insightSwipe: {
    direction: 'left',
    onSwipe: () => 'dismiss insight',
  },
  
  activityTap: {
    onPress: () => 'navigate to transaction detail',
  }
};
```

---

## ⚠️ Error States

```typescript
const homeErrorStates = {
  portfolioLoadError: {
    icon: '📊',
    title: 'Unable to load portfolio',
    message: 'Pull to refresh or try again later',
    action: 'Retry',
  },
  
  noWalletConnected: {
    icon: '🔗',
    title: 'No wallet connected',
    message: 'Connect a wallet to see your portfolio',
    action: 'Connect Wallet',
  },
  
  emptyPortfolio: {
    icon: '💰',
    title: 'Your portfolio is empty',
    message: 'Deposit funds to get started',
    action: 'Receive Crypto',
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Home Dashboard*

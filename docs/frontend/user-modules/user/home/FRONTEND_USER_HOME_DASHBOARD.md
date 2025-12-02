# FRONTEND_USER_HOME_DASHBOARD

## User Home Dashboard Module

**User Type:** Authenticated User  
**Module:** Home Dashboard  
**Route:** `/home`, `/` (default)  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Home Dashboard** - AI-Powered Portfolio Hub

### Description
The main landing screen after authentication, providing a comprehensive view of the user's portfolio with GraphRAG-powered protocol insights, ML risk indicators, real-time updates via WebSocket, and personalized AI recommendations.

### Key Capabilities
- Total portfolio value display with real-time updates
- Multi-chain asset breakdown
- **GraphRAG protocol intelligence** (NEW)
- **ML risk scoring for positions** (NEW)
- **Real-time WebSocket updates** (NEW)
- Quick action buttons
- Recent activity feed
- **AI-powered insights & recommendations** (ENHANCED)
- Market highlights
- Risk alerts and warnings

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

### US-USER-HOME-005: Monitor Portfolio Risk
**As a** user  
**I want to** see ML-powered risk scores for my positions  
**So that** I can identify and manage risks proactively

**Acceptance Criteria:**
- Risk score (0-10) displayed for each position
- Color-coded risk indicators (🟢🟡🟠🔴)
- Overall portfolio risk summary
- Tap to view detailed risk analysis

---

### US-USER-HOME-006: Receive Real-Time Updates
**As a** user  
**I want to** see real-time price and risk changes  
**So that** I stay informed without manual refreshing

**Acceptance Criteria:**
- WebSocket connection active
- Live price updates
- Real-time risk alerts
- Connection status indicator
- Smooth animations for updates

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

---

### View 1B: Enhanced Dashboard with GraphRAG/ML/WebSocket (NEW)

```
┌─────────────────────────────────────┐
│ 🔔 3  🔴 Live           ⚙️         │
│                                     │
│  Good morning, Alice 👋             │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Total Portfolio   Risk: 3.2🟡 ││
│  │                                 ││
│  │  $45,230.42  🔴 LIVE            ││
│  │  ↑ $1,234.56 (+2.8%) today     ││
│  │                                 ││
│  │  ████████████████░░░░ ETH 56%  ││
│  │  ████████░░░░░░░░░░░░ ARB 28%  ││
│  │  ████░░░░░░░░░░░░░░░░ POLY 12% ││
│  │  ██░░░░░░░░░░░░░░░░░░ BASE 4%  ││
│  │                                 ││
│  │  [View Risk Analysis →]         ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Risk Alert (NEW)                │
│  ┌─────────────────────────────────┐│
│  │ 🟠 Euler Finance                ││
│  │    Risk: 5.2 → 7.8 🔴           ││
│  │    Your exposure: $2,450 (5%)   ││
│  │    [Review Now] [Dismiss]       ││
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
│  💡 AI Insight (GraphRAG-Powered)   │
│  ┌─────────────────────────────────┐│
│  │ Based on your risk profile and  ││
│  │ portfolio, consider diversifying││
│  │ into Lido Finance (Risk: 2.3🟢).││
│  │ Similar to your Rocket Pool     ││
│  │ position but with lower risk.   ││
│  │              [Explore Lido →]   ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Positions                     │
│  ┌─────────────────────────────────┐│
│  │ Aave V3          Risk: 2.1 🟢   ││
│  │ $8,200 (18%)     TVL: $6.2B     ││
│  │ Supplied USDC    [Details →]    ││
│  ├─────────────────────────────────┤│
│  │ Uniswap V3       Risk: 2.8 🟢   ││
│  │ $5,400 (12%)     TVL: $3.8B     ││
│  │ LP: ETH/USDC     [Details →]    ││
│  ├─────────────────────────────────┤│
│  │ Lido Finance     Risk: 2.3 🟢   ││
│  │ $12,000 (27%)    TVL: $28.4B    ││
│  │ stETH            [Details →]    ││
│  ├─────────────────────────────────┤│
│  │ Euler Finance    Risk: 7.8 🔴   ││
│  │ $2,450 (5%) ⚠️   TVL: $450M     ││
│  │ Supplied DAI     [Review Risk]  ││
│  │                                 ││
│  │         [View All →]            ││
│  └─────────────────────────────────┘│
│                                     │
│  Real-Time Updates (2 min ago)      │
│  • ETH $2,475 → $2,480 (+0.2%)      │
│  • Your portfolio +$45.20           │
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
│  Home  Wallet  Chat  Markets Profile│
└─────────────────────────────────────┘
```

**Key Enhancements**:
- 🔴 **Live indicator** - WebSocket connection active
- **Portfolio risk score** - ML-powered aggregate (3.2/10)
- **Risk alerts** - Real-time warnings for high-risk protocols
- **AI Insights** - GraphRAG-powered recommendations
- **Position risk scores** - ML predictions per protocol
- **TVL display** - Protocol size context
- **Real-time updates** - Live price changes

---

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

## 🔌 **NEW: GraphRAG/ML/WebSocket API Integration**

### Get Portfolio Risk Summary (NEW)

```typescript
// GET /api/v1/portfolio/risk
interface PortfolioRiskResponse {
  overall_risk_score: number; // 0-10
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  protocols_at_risk: Array<{
    protocol_id: string;
    protocol_name: string;
    exposure_usd: number;
    risk_score: number;
    risk_level: string;
  }>;
  recommendations: string[];
}
```

### Get AI-Powered Dashboard Insights (NEW)

```typescript
// GET /api/v1/insights/dashboard?user_id={id}
interface DashboardInsightsResponse {
  insights: Array<{
    id: string;
    type: 'optimization' | 'risk_warning' | 'opportunity';
    title: string;
    message: string;
    action_label: string;
    action_url: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
    created_at: string;
  }>;
  personalized: boolean; // Based on user preferences
}
```

### WebSocket Real-Time Updates (NEW)

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function Dashboard() {
  const { isConnected, on } = useWebSocket({
    url: 'ws://api/v1/ws/graph',
    token: authToken,
  });
  
  useEffect(() => {
    // Subscribe to user-specific updates
    const unsubRisk = on('risk:alert', (data) => {
      showRiskAlert(data);
      refreshPortfolioRisk();
    });
    
    const unsubPrice = on('price:update', (data) => {
      updatePriceDisplay(data.token_symbol, data.price_usd);
      recalculatePortfolioValue();
    });
    
    const unsubPortocol = on('protocol:update', (data) => {
      if (userProtocols.includes(data.protocol_id)) {
        showProtocolUpdate(data);
      }
    });
    
    return () => {
      unsubRisk();
      unsubPrice();
      unsubProtocol();
    };
  }, [on]);
  
  return (
    <div>
      <ConnectionIndicator isConnected={isConnected} />
      {/* Dashboard content */}
    </div>
  );
}
```

### GraphRAG Protocol Intelligence (NEW)

```typescript
// GET /api/v1/graph/search/contextual
interface ContextualSearchRequest {
  query: string;
  user_preferences: {
    risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
    preferred_chains: string[];
    min_tvl?: number;
  };
  limit: number;
}

// Used for AI recommendations
const getRecommendations = async () => {
  const prefs = await getUserPreferences();
  const results = await api.post('/graph/search/contextual', {
    query: 'safe staking alternatives',
    user_preferences: prefs,
    limit: 3,
  });
  return results.data;
};
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

# FRONTEND_USER_REALTIME_FEED

## User Real-Time Updates Feed Module

**User Type:** Authenticated User  
**Module:** Live Protocol Updates  
**Route:** `/feed`, `/updates`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0 - WebSocket Powered

---

## 📋 Module Overview

### Title
**Live Feed** - Real-Time Protocol & Risk Updates

### Description
Real-time feed of protocol updates, risk alerts, price changes, and transaction status powered by WebSocket streaming. Users stay informed of important changes affecting their portfolio and watched protocols.

### Key Capabilities
- WebSocket real-time connection
- Protocol update notifications
- Risk alert streaming
- Price change notifications
- Transaction status updates
- Anomaly detection alerts
- Filter by update type
- Subscribe to specific protocols
- Notification preferences
- Update history

---

## 👤 User Stories

### US-USER-FEED-001: View Live Updates
**As a** user  
**I want to** see real-time updates in a feed  
**So that** I'm always informed of important changes

**Acceptance Criteria:**
- Live update stream
- New updates appear automatically
- No manual refresh needed
- Updates sorted by time

---

### US-USER-FEED-002: Subscribe to Protocols
**As a** user  
**I want to** subscribe to specific protocols  
**So that** I only see updates I care about

**Acceptance Criteria:**
- Protocol subscription list
- Easy subscribe/unsubscribe
- Auto-subscribe to portfolio protocols
- Visual subscription indicators

---

### US-USER-FEED-003: Receive Risk Alerts
**As a** user  
**I want to** receive immediate risk alerts  
**So that** I can take quick action

**Acceptance Criteria:**
- Risk alerts appear instantly
- Severity clearly indicated
- Actionable recommendations
- Quick action buttons

---

### US-USER-FEED-004: Filter Update Types
**As a** user  
**I want to** filter updates by type  
**So that** I can focus on what's important

**Acceptance Criteria:**
- Filter by protocol updates
- Filter by risk alerts
- Filter by price changes
- Filter by severity

---

## 🖼️ Views & Wireframes

### View 1: Live Feed (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Live Updates     [🔴Live]  │
│                                     │
│  Filters: [All ▼] [Risk ▼] [...]   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔴 CRITICAL RISK ALERT         ││
│  │                                 ││
│  │  Euler Finance                  ││
│  │  Risk: 5.2 → 7.8 🔴 HIGH        ││
│  │                                 ││
│  │  ⚠️ Anomaly detected in TVL     ││
│  │  patterns. Unusual withdrawal   ││
│  │  activity detected.             ││
│  │                                 ││
│  │  Your Exposure: $2,450 (5%)     ││
│  │                                 ││
│  │  [Review Now] [Dismiss]         ││
│  │                           Just now││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🟢 Protocol Update             ││
│  │                                 ││
│  │  Aave V3                        ││
│  │  New audit completed ✓          ││
│  │                                 ││
│  │  Risk: 2.3 → 2.1 🟢             ││
│  │  Audit by: Trail of Bits        ││
│  │                                 ││
│  │  Your Exposure: $8,200 (16%)    ││
│  │                                 ││
│  │  [View Details]                 ││
│  │                         2 min ago││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💰 Price Alert                 ││
│  │                                 ││
│  │  ETH Price Movement             ││
│  │  $2,510 → $2,475 (-1.4%)        ││
│  │                                 ││
│  │  Your Holdings: 4.52 ETH        ││
│  │  Value Change: -$158.20         ││
│  │                                 ││
│  │  [View Chart]                   ││
│  │                         5 min ago││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⏳ Transaction Status           ││
│  │                                 ││
│  │  Swap: 0.5 ETH → USDC           ││
│  │  Status: ✅ Confirmed           ││
│  │                                 ││
│  │  Received: 1,237.50 USDC        ││
│  │  Gas: $4.32                     ││
│  │                                 ││
│  │  [View Tx] [View Receipt]       ││
│  │                        10 min ago││
│  └─────────────────────────────────┘│
│                                     │
│  [Load Earlier Updates]             │
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Subscription Management

```
┌─────────────────────────────────────┐
│  [←]    Subscriptions       [Edit] │
│                                     │
│  Update Types                       │
│  ┌─────────────────────────────────┐│
│  │ ☑ Protocol Updates              ││
│  │ ☑ Risk Alerts                   ││
│  │ ☑ Price Changes                 ││
│  │ ☐ Transaction Status            ││
│  │ ☑ Anomaly Detection             ││
│  └─────────────────────────────────┘│
│                                     │
│  Alert Severity                     │
│  ┌─────────────────────────────────┐│
│  │ ○ All Alerts                    ││
│  │ ● Medium and above (Default)    ││
│  │ ○ High and Critical only        ││
│  │ ○ Critical only                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Notification Channels              │
│  ┌─────────────────────────────────┐│
│  │ ☑ WebSocket (Real-time)         ││
│  │ ☑ Push Notifications            ││
│  │ ☐ Email Digest (Daily)          ││
│  └─────────────────────────────────┘│
│                                     │
│  Subscribed Protocols (8)           │
│  ┌─────────────────────────────────┐│
│  │ ☑ Aave V3         [Unsubscribe] ││
│  │ ☑ Uniswap V3      [Unsubscribe] ││
│  │ ☑ Lido Finance    [Unsubscribe] ││
│  │ ☑ Curve Finance   [Unsubscribe] ││
│  │ ☑ MakerDAO        [Unsubscribe] ││
│  │ ☑ Compound        [Unsubscribe] ││
│  │ ☑ Balancer        [Unsubscribe] ││
│  │ ☑ Rocket Pool     [Unsubscribe] ││
│  │                                 ││
│  │ [+ Add Protocol]                ││
│  └─────────────────────────────────┘│
│                                     │
│  Rate Limiting                      │
│  Max Alerts: [10 ▼] per hour        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Save Preferences]             ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Update Detail

```
┌─────────────────────────────────────┐
│  [←]    Risk Alert Detail           │
│                                     │
│  🔴 CRITICAL RISK ALERT              │
│                                     │
│  Protocol: Euler Finance            │
│  Time: Just now                     │
│  Severity: CRITICAL                 │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Risk Score Change              ││
│  │                                 ││
│  │  5.2 ────────────→ 7.8          ││
│  │  🟡 MEDIUM      🔴 HIGH          ││
│  │                                 ││
│  │  Change: +2.6 points (+50%)     ││
│  │  Confidence: 87%                ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Contributing Factors            │
│  ┌─────────────────────────────────┐│
│  │  🔴 Unusual withdrawal activity ││
│  │     Impact: +3.2 points         ││
│  │                                 ││
│  │  🟡 TVL volatility increased    ││
│  │     Impact: +1.8 points         ││
│  │                                 ││
│  │  🟡 Low recent audit coverage   ││
│  │     Impact: +1.2 points         ││
│  └─────────────────────────────────┘│
│                                     │
│  💼 Your Exposure                   │
│  ┌─────────────────────────────────┐│
│  │  Amount: $2,450                 ││
│  │  Percentage: 5% of portfolio    ││
│  │  Position: Supplied USDC        ││
│  │  Est. Risk: $490 (20% of pos)   ││
│  └─────────────────────────────────┘│
│                                     │
│  🛡️ Recommendations                 │
│  • Consider reducing exposure       │
│  • Review safer alternatives        │
│  • Monitor closely for 24-48h       │
│  • Set up price alerts              │
│                                     │
│  💡 Safer Alternatives:             │
│  • Aave V3 (Risk: 2.1 🟢)           │
│  • Compound (Risk: 2.5 🟢)          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [View Alternatives]            ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [Reduce Position]              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [Mark as Reviewed]             ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 WebSocket Integration

### Connection Setup

```typescript
import { useEffect, useState, useCallback } from 'react';

const WS_URL = 'ws://api/v1/ws/graph';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
}

export function useRealtimeUpdates(authToken: string) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [updates, setUpdates] = useState<WebSocketMessage[]>([]);
  
  useEffect(() => {
    // Create WebSocket connection
    const websocket = new WebSocket(`${WS_URL}?token=${authToken}`);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Subscribe to all update types
      websocket.send(JSON.stringify({
        action: 'subscribe',
        channels: [
          'graph:updates',
          'graph:risk_alerts',
          'price:updates'
        ]
      }));
    };
    
    websocket.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Add to updates list
      setUpdates(prev => [message, ...prev].slice(0, 100)); // Keep last 100
      
      // Trigger notifications based on type
      if (message.type === 'risk:alert' && message.data.severity === 'CRITICAL') {
        showPushNotification(message.data);
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket closed');
      setIsConnected(false);
      
      // Attempt reconnection
      setTimeout(() => {
        console.log('Reconnecting...');
        // Would recreate connection
      }, 5000);
    };
    
    setWs(websocket);
    
    return () => {
      websocket.close();
    };
  }, [authToken]);
  
  const subscribeToProtocol = useCallback((protocolId: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'subscribe',
        channel: `protocol:${protocolId}`
      }));
    }
  }, [ws]);
  
  const unsubscribeFromProtocol = useCallback((protocolId: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'unsubscribe',
        channel: `protocol:${protocolId}`
      }));
    }
  }, [ws]);
  
  return {
    isConnected,
    updates,
    subscribeToProtocol,
    unsubscribeFromProtocol
  };
}
```

---

### Event Handling

```typescript
interface UpdateHandler {
  onProtocolUpdate: (data: ProtocolUpdateEvent) => void;
  onRiskAlert: (data: RiskAlertEvent) => void;
  onPriceChange: (data: PriceChangeEvent) => void;
  onTransactionStatus: (data: TransactionEvent) => void;
  onAnomalyDetected: (data: AnomalyEvent) => void;
}

const handleWebSocketMessage = (
  message: WebSocketMessage,
  handlers: UpdateHandler
) => {
  switch (message.type) {
    case 'protocol:update':
      handlers.onProtocolUpdate(message.data);
      break;
    case 'risk:alert':
      handlers.onRiskAlert(message.data);
      break;
    case 'price:update':
      handlers.onPriceChange(message.data);
      break;
    case 'transaction:status':
      handlers.onTransactionStatus(message.data);
      break;
    case 'anomaly:detected':
      handlers.onAnomalyDetected(message.data);
      break;
  }
};
```

---

## 🎬 Motion Design

```typescript
const feedAnimations = {
  // New update slide in from top
  updateEnter: {
    initial: { y: -50, opacity: 0, scale: 0.95 },
    animate: { y: 0, opacity: 1, scale: 1 },
    exit: { y: -20, opacity: 0 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 30
    }
  },
  
  // Critical alert pulse
  criticalPulse: {
    animate: {
      scale: [1, 1.02, 1],
      boxShadow: [
        '0 0 0 0 rgba(239, 68, 68, 0)',
        '0 0 0 8px rgba(239, 68, 68, 0.4)',
        '0 0 0 0 rgba(239, 68, 68, 0)'
      ],
      transition: {
        duration: 2,
        repeat: 3
      }
    }
  },
  
  // Connection indicator pulse
  connectionPulse: {
    animate: {
      opacity: [0.5, 1, 0.5],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Dismiss swipe
  dismissSwipe: {
    exit: {
      x: -300,
      opacity: 0,
      transition: { duration: 0.3 }
    }
  },
  
  // Update expansion
  updateExpand: {
    initial: { height: 80 },
    animate: { height: 'auto' },
    transition: { duration: 0.3 }
  }
};
```

---

## 🎨 Component Specifications

```typescript
// Update feed component
interface RealtimeFeedProps {
  authToken: string;
  filters?: UpdateFilters;
  maxUpdates?: number;
  autoScroll?: boolean;
}

interface UpdateFilters {
  types?: string[];
  severities?: string[];
  protocols?: string[];
}

// Update card
interface UpdateCardProps {
  update: WebSocketMessage;
  onAction?: (action: string) => void;
  onDismiss?: () => void;
  isExpanded?: boolean;
}

// Connection status
interface ConnectionStatusProps {
  isConnected: boolean;
  lastUpdate?: Date;
  reconnecting?: boolean;
}

// Subscription manager
interface SubscriptionManagerProps {
  subscribed: string[];
  available: string[];
  onSubscribe: (id: string) => void;
  onUnsubscribe: (id: string) => void;
}
```

---

## ⚠️ Error Handling

```typescript
const feedErrors = {
  WS_001: 'WebSocket connection failed',
  WS_002: 'Connection lost - attempting reconnection',
  WS_003: 'Failed to subscribe to channel',
  WS_004: 'Message parsing failed',
  
  FEED_001: 'Failed to load update history',
  FEED_002: 'Too many updates - please filter',
  
  SUB_001: 'Failed to update subscription',
  SUB_002: 'Invalid protocol ID',
};
```

---

## 🔒 Security & Privacy

- WebSocket authenticated via JWT
- User-specific channels isolated
- No cross-user data leaks
- Encrypted connection (WSS)
- Rate limiting per user
- Subscription validation

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Real-Time Updates Feed*

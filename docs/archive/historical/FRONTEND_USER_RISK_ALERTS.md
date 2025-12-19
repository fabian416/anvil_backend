# FRONTEND_USER_RISK_ALERTS

## User Alerts - Risk Monitoring Module

**User Type:** Authenticated User  
**Module:** Alerts - Real-Time Risk Monitoring & Notifications  
**Route:** `/alerts`, `/alerts/history`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Risk Alerts** - Real-Time Protocol Risk Monitoring and Intelligent Notifications

### Description
Comprehensive risk alert system that monitors user's protocols and positions in real-time, providing instant notifications about risk changes, anomalies, critical events, and dependency risks via WebSocket push notifications.

### Key Capabilities
- ✅ Real-time WebSocket push notifications
- ✅ Protocol risk increase alerts
- ✅ Anomaly detection alerts
- ✅ Critical risk level warnings
- ✅ Dependency risk alerts
- ✅ Alert management (acknowledge, dismiss, act upon)
- ✅ Alert subscription preferences
- ✅ Protocol-specific subscriptions
- ✅ Severity-based filtering
- ✅ Alert history tracking
- ✅ Rate limiting (max alerts per hour)
- ✅ Multi-channel delivery (push, email, WebSocket, in-app)

---

## 👤 User Stories

### US-USER-ALERTS-001: Receive Real-Time Risk Alerts
**As a** user  
**I want to** receive instant notifications when protocol risks change  
**So that** I can take timely action to protect my positions

**Acceptance Criteria:**
- WebSocket connection established on app open
- Alerts appear immediately (< 1 second)
- Clear risk change indication
- Severity-based visual hierarchy
- One-tap to view details

---

### US-USER-ALERTS-002: Manage Alert Notifications
**As a** user  
**I want to** acknowledge, dismiss, or mark alerts as acted upon  
**So that** I can track which alerts I've addressed

**Acceptance Criteria:**
- Acknowledge button (mark as seen)
- Dismiss button (not relevant)
- "I Took Action" button (acted upon)
- Visual state changes
- Persists across devices

---

### US-USER-ALERTS-003: Configure Alert Preferences
**As a** user  
**I want to** control which alerts I receive  
**So that** I only get notifications that matter to me

**Acceptance Criteria:**
- Enable/disable by type (risk, anomaly, updates, price)
- Set minimum severity threshold
- Subscribe to specific protocols
- Exclude unwanted protocols
- Rate limiting configuration

---

### US-USER-ALERTS-004: View Alert History
**As a** user  
**I want to** see my past alerts  
**So that** I can track risk patterns and my responses

**Acceptance Criteria:**
- Chronological alert list
- Filter by severity, type, protocol
- Show acknowledgement status
- Show actions taken
- Export history option

---

### US-USER-ALERTS-005: Subscribe to Protocol Alerts
**As a** user  
**I want to** get alerts for specific protocols I care about  
**So that** I'm notified about protocols in my portfolio or watchlist

**Acceptance Criteria:**
- One-tap subscribe from protocol page
- Manage subscriptions in settings
- Shows subscription count
- Unsubscribe easily

---

### US-USER-ALERTS-006: Receive Actionable Recommendations
**As a** user  
**I want to** get clear recommendations with each alert  
**So that** I know what actions to consider

**Acceptance Criteria:**
- 2-3 specific recommendations per alert
- Actionable steps (not just warnings)
- Quick action buttons
- Learn more links

---

## 🖼️ Wireframes

### View 1: Active Alerts Screen (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Risk Alerts           [⚙️] │
├─────────────────────────────────────┤
│                                     │
│  🔴 Active Alerts (3)               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔴 CRITICAL                    ││
│  │  Aave V3 - Risk Spike           ││
│  │                                 ││
│  │  Risk increased from 2.1 to 4.3 ││
│  │  Multiple security incidents    ││
│  │  detected in last 24h           ││
│  │                                 ││
│  │  Recommendations:               ││
│  │  • Reduce exposure by 50%       ││
│  │  • Monitor closely for 48h      ││
│  │  • Consider alternatives        ││
│  │                                 ││
│  │  [I Took Action] [Dismiss]     ││
│  │                                 ││
│  │  2 minutes ago                  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🟠 HIGH                        ││
│  │  Curve Finance - Anomaly        ││
│  │                                 ││
│  │  Unusual trading volume spike   ││
│  │  Risk: 3.8 (↑0.9 from normal)  ││
│  │                                 ││
│  │  Recommendations:               ││
│  │  • Review your positions        ││
│  │  • Check protocol updates       ││
│  │                                 ││
│  │  [Acknowledge] [Dismiss]       ││
│  │                                 ││
│  │  15 minutes ago                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🟡 MEDIUM                      ││
│  │  Uniswap V3 - Dependency Risk   ││
│  │                                 ││
│  │  Connected protocol (Aave) has  ││
│  │  elevated risk. May impact LP.  ││
│  │                                 ││
│  │  Recommendations:               ││
│  │  • Monitor Aave situation       ││
│  │  • Consider hedging             ││
│  │                                 ││
│  │  [Acknowledge] [Dismiss]       ││
│  │                                 ││
│  │  1 hour ago                     ││
│  └─────────────────────────────────┘│
│                                     │
│  [View History (47 alerts)]         │
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Real-Time Alert Push Notification

```
┌─────────────────────────────────────┐
│  🔴 CRITICAL RISK ALERT             │
├─────────────────────────────────────┤
│                                     │
│  Aave V3 Ethereum                   │
│  Risk jumped from 2.1 → 4.3         │
│                                     │
│  Security incidents detected        │
│                                     │
│  [View Alert]          [Dismiss]    │
│                                     │
│  Just now • Anvil                   │
└─────────────────────────────────────┘
```

---

### View 3: Alert Detail View

```
┌─────────────────────────────────────┐
│  [←]    Alert Details               │
├─────────────────────────────────────┤
│                                     │
│  🔴 CRITICAL ALERT                  │
│                                     │
│  Protocol: Aave V3                  │
│  Chain: Ethereum                    │
│  Type: Risk Increase                │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Risk Score Timeline            ││
│  │                                 ││
│  │   4.3 🔴 ┄┄┄┄┄┄┄┄ Current       ││
│  │   3.5 🟠    ↑                   ││
│  │   2.8 🟡    |                   ││
│  │   2.1 🟢 ┄┄ Previous            ││
│  │                                 ││
│  │   ↑ 2.2 point increase          ││
│  └─────────────────────────────────┘│
│                                     │
│  What Happened:                     │
│  • 3 security incidents in 24h      │
│  • Unusual contract interactions    │
│  • Elevated smart contract risk     │
│  • Community concerns flagged       │
│                                     │
│  Your Exposure:                     │
│  • $12,500 deposited                │
│  • 2 active positions               │
│  • Health factor: 1.8 (was 2.3)    │
│                                     │
│  Recommendations:                   │
│  ┌─────────────────────────────────┐│
│  │  1. Reduce Exposure             ││
│  │     Consider withdrawing 50%    ││
│  │     of your position            ││
│  │                                 ││
│  │     [Withdraw Now]              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  2. Monitor Closely             ││
│  │     Check status every 2-4 hours││
│  │                                 ││
│  │     [Set Reminder]              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  3. Review Alternatives         ││
│  │     Compound, Morpho have lower ││
│  │     risk with similar yields    ││
│  │                                 ││
│  │     [Compare Protocols]         ││
│  └─────────────────────────────────┘│
│                                     │
│  Similar Incidents:                 │
│  Last occurred 3 months ago         │
│  Risk returned to normal in 48h     │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [✓ I Took Action]              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [Acknowledge & Track]          ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [Dismiss (Not Relevant)]       ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Alert Subscription Settings

```
┌─────────────────────────────────────┐
│  [←]    Alert Settings              │
├─────────────────────────────────────┤
│                                     │
│  Alert Types                        │
│  ┌─────────────────────────────────┐│
│  │  [✓] Risk Alerts                ││
│  │      Protocol risk changes      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Anomaly Alerts             ││
│  │      Unusual behavior detected  ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Protocol Updates           ││
│  │      New features, changes      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [ ] Price Alerts               ││
│  │      Token price movements      ││
│  └─────────────────────────────────┘│
│                                     │
│  Severity Threshold                 │
│  ┌─────────────────────────────────┐│
│  │  Only notify for:               ││
│  │                                 ││
│  │  ( ) Low & above                ││
│  │  (•) Medium & above   ✓ Active  ││
│  │  ( ) High & above               ││
│  │  ( ) Critical only              ││
│  └─────────────────────────────────┘│
│                                     │
│  Notification Channels              │
│  ┌─────────────────────────────────┐│
│  │  [✓] Push Notifications         ││
│  │  [ ] Email Notifications        ││
│  │  [✓] In-App WebSocket           ││
│  └─────────────────────────────────┘│
│                                     │
│  Rate Limiting                      │
│  ┌─────────────────────────────────┐│
│  │  Max alerts per hour: 10        ││
│  │  [━━━━━━━━━━━━━━━━━━━━━━━━━] ││
│  │  (Prevents notification spam)   ││
│  └─────────────────────────────────┘│
│                                     │
│  Protocol Subscriptions             │
│  ┌─────────────────────────────────┐│
│  │  Subscribed: 8 protocols        ││
│  │  Excluded: 2 protocols          ││
│  │                                 ││
│  │  [Manage Subscriptions] →       ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 5: Alert History

```
┌─────────────────────────────────────┐
│  [←]    Alert History               │
├─────────────────────────────────────┤
│                                     │
│  [Search alerts...]                 │
│                                     │
│  Filters: [All] [Critical] [High]   │
│           [Protocol ▼] [Type ▼]     │
│                                     │
│  Today (3 alerts)                   │
│  ┌─────────────────────────────────┐│
│  │  🔴 Aave V3 - Risk Spike        ││
│  │     ✓ Acted upon                ││
│  │     2:45 PM                     ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  🟠 Curve - Anomaly             ││
│  │     ✓ Acknowledged              ││
│  │     1:30 PM                     ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  🟡 Uniswap - Dependency Risk   ││
│  │     ✓ Acknowledged              ││
│  │     10:15 AM                    ││
│  └─────────────────────────────────┘│
│                                     │
│  Yesterday (5 alerts)               │
│  ┌─────────────────────────────────┐│
│  │  🟡 GMX - Risk Increase         ││
│  │     ✓ Acted upon                ││
│  │     Yesterday 6:20 PM           ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  🟢 Lido - All Clear            ││
│  │     ✓ Acknowledged              ││
│  │     Yesterday 3:45 PM           ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  Show 3 more...                 ││
│  └─────────────────────────────────┘│
│                                     │
│  This Week (12 alerts)              │
│  [Load More]                        │
│                                     │
│  📊 [View Analytics]                │
│  📥 [Export History]                │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Integration

### Get Risk Alerts

```typescript
// GET /api/v1/alerts/risk?unacknowledged_only=false&severity=MEDIUM&limit=50
interface RiskAlertListResponse {
  alerts: RiskAlert[];
  total: number;
  unacknowledged: number;
}

interface RiskAlert {
  id: string;
  user_id: string;
  protocol_id: string;
  protocol_name: string;
  alert_type: 'risk_increase' | 'anomaly' | 'critical' | 'dependency';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  details: Record<string, any>;
  recommendations: string[];
  current_risk_score: number;
  previous_risk_score: number | null;
  risk_change: number | null;
  acknowledged: boolean;
  dismissed: boolean;
  acted_upon: boolean;
  created_at: string;
  acknowledged_at: string | null;
  expires_at: string | null;
}

const getRiskAlerts = async (
  filters?: {
    unacknowledged_only?: boolean;
    severity?: string;
    limit?: number;
  }
): Promise<RiskAlertListResponse> => {
  const response = await api.get('/api/v1/alerts/risk', { params: filters });
  return response.data;
};
```

### Acknowledge Alert

```typescript
// PUT /api/v1/alerts/risk/:alert_id/acknowledge
interface AcknowledgeAlertRequest {
  acted_upon: boolean;
}

const acknowledgeAlert = async (
  alertId: string,
  actedUpon: boolean = false
): Promise<RiskAlert> => {
  const response = await api.put(
    `/api/v1/alerts/risk/${alertId}/acknowledge`,
    { acted_upon: actedUpon }
  );
  return response.data;
};
```

### Dismiss Alert

```typescript
// DELETE /api/v1/alerts/risk/:alert_id
const dismissAlert = async (alertId: string): Promise<void> => {
  await api.delete(`/api/v1/alerts/risk/${alertId}`);
};
```

### Get Alert Subscription

```typescript
// GET /api/v1/alerts/subscription
interface AlertSubscriptionResponse {
  risk_alerts_enabled: boolean;
  anomaly_alerts_enabled: boolean;
  protocol_update_alerts_enabled: boolean;
  price_alerts_enabled: boolean;
  min_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  subscribed_protocols: string[];
  excluded_protocols: string[];
  push_notifications: boolean;
  email_notifications: boolean;
  websocket_notifications: boolean;
  max_alerts_per_hour: number;
}

const getAlertSubscription = async (): Promise<AlertSubscriptionResponse> => {
  const response = await api.get('/api/v1/alerts/subscription');
  return response.data;
};
```

### Update Alert Subscription

```typescript
// PUT /api/v1/alerts/subscription
interface UpdateSubscriptionRequest {
  risk_alerts_enabled?: boolean;
  anomaly_alerts_enabled?: boolean;
  protocol_update_alerts_enabled?: boolean;
  price_alerts_enabled?: boolean;
  min_severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  subscribed_protocols?: string[];
  excluded_protocols?: string[];
  push_notifications?: boolean;
  email_notifications?: boolean;
  websocket_notifications?: boolean;
  max_alerts_per_hour?: number;
}

const updateAlertSubscription = async (
  updates: UpdateSubscriptionRequest
): Promise<AlertSubscriptionResponse> => {
  const response = await api.put('/api/v1/alerts/subscription', updates);
  return response.data;
};
```

### Subscribe/Unsubscribe to Protocol

```typescript
// POST /api/v1/alerts/subscription/protocols/:protocol_id
const subscribeToProtocol = async (protocolId: string): Promise<void> => {
  await api.post(`/api/v1/alerts/subscription/protocols/${protocolId}`);
};

// DELETE /api/v1/alerts/subscription/protocols/:protocol_id
const unsubscribeFromProtocol = async (protocolId: string): Promise<void> => {
  await api.delete(`/api/v1/alerts/subscription/protocols/${protocolId}`);
};
```

---

## 🔥 WebSocket Integration

### Real-Time Alert Push

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function AlertNotificationSystem() {
  const { socket, isConnected } = useWebSocket();
  const [liveAlerts, setLiveAlerts] = useState<RiskAlert[]>([]);
  
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    // Subscribe to risk alerts channel
    socket.on('risk_alert', (alert: RiskAlert) => {
      // Show push notification
      showPushNotification(alert);
      
      // Add to live alerts
      setLiveAlerts((prev) => [alert, ...prev]);
      
      // Play alert sound based on severity
      if (alert.severity === 'CRITICAL') {
        playAlertSound('critical');
      } else if (alert.severity === 'HIGH') {
        playAlertSound('high');
      }
    });
    
    // Subscribe to protocol updates
    socket.on('protocol_update', (update: ProtocolUpdate) => {
      // Handle protocol updates
      console.log('Protocol update:', update);
    });
    
    return () => {
      socket.off('risk_alert');
      socket.off('protocol_update');
    };
  }, [socket, isConnected]);
  
  return (
    <div>
      {liveAlerts.map((alert) => (
        <AlertToast key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
```

### WebSocket Event Types

```typescript
// WebSocket Events from Server
type WebSocketEvents = {
  'risk_alert': (alert: RiskAlert) => void;
  'protocol_update': (update: ProtocolUpdate) => void;
  'alert_acknowledged': (alertId: string) => void;
  'alert_dismissed': (alertId: string) => void;
};

// Example: Listen for real-time alerts
socket.on('risk_alert', (alert: RiskAlert) => {
  if (alert.severity === 'CRITICAL') {
    // Immediate action required
    showCriticalAlertModal(alert);
  } else {
    // Show toast notification
    showToast({
      type: 'warning',
      title: alert.protocol_name,
      message: alert.message,
      action: () => navigateToAlert(alert.id),
    });
  }
});
```

---

## 🎨 Motion Design

### Alert Toast Animation (Framer Motion)

```typescript
import { motion, AnimatePresence } from 'framer-motion';

function AlertToast({ alert, onDismiss }: AlertToastProps) {
  const severityColors = {
    CRITICAL: '#EF4444',
    HIGH: '#F59E0B',
    MEDIUM: '#F59E0B',
    LOW: '#10B981',
  };
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -50, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, x: 300 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        style={{
          borderLeftColor: severityColors[alert.severity],
        }}
        className="border-l-4 bg-white rounded-lg shadow-lg p-4 max-w-md"
      >
        <div className="flex items-start gap-3">
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 0.5,
              repeat: alert.severity === 'CRITICAL' ? Infinity : 0,
              repeatDelay: 1,
            }}
            className="text-2xl"
          >
            {alert.severity === 'CRITICAL' && '🔴'}
            {alert.severity === 'HIGH' && '🟠'}
            {alert.severity === 'MEDIUM' && '🟡'}
            {alert.severity === 'LOW' && '🟢'}
          </motion.div>
          
          <div className="flex-1">
            <div className="font-bold">{alert.protocol_name}</div>
            <div className="text-sm text-gray-600">{alert.message}</div>
            
            <div className="flex gap-2 mt-3">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => navigateToAlert(alert.id)}
                className="text-sm text-blue-600 font-semibold"
              >
                View Details
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={onDismiss}
                className="text-sm text-gray-500"
              >
                Dismiss
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
```

### Critical Alert Modal Animation

```typescript
function CriticalAlertModal({ alert, onClose }: CriticalAlertModalProps) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.8, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-xl p-6 max-w-lg mx-4 shadow-2xl"
        >
          {/* Pulsing critical indicator */}
          <motion.div
            animate={{
              scale: [1, 1.05, 1],
              opacity: [1, 0.8, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
            }}
            className="flex items-center gap-3 mb-4"
          >
            <div className="text-4xl">🔴</div>
            <div>
              <div className="font-bold text-xl">CRITICAL ALERT</div>
              <div className="text-red-600">{alert.protocol_name}</div>
            </div>
          </motion.div>
          
          <div className="mb-6">{alert.message}</div>
          
          <div className="space-y-3">
            {alert.recommendations.map((rec, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-gray-50 p-3 rounded-lg"
              >
                • {rec}
              </motion.div>
            ))}
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClose}
            className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg font-semibold"
          >
            I Understand
          </motion.button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
```

---

## 🎨 React Native Motion (Reanimated)

### Alert Card Swipe to Dismiss

```typescript
import Animated, {
  useAnimatedGestureHandler,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';

function AlertCard({ alert, onDismiss }: AlertCardProps) {
  const translateX = useSharedValue(0);
  const opacity = useSharedValue(1);
  
  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      translateX.value = event.translationX;
      opacity.value = 1 - Math.abs(event.translationX) / 300;
    },
    onEnd: (event) => {
      if (Math.abs(event.translationX) > 100) {
        // Dismiss
        translateX.value = withTiming(event.translationX > 0 ? 400 : -400);
        opacity.value = withTiming(0, {}, () => {
          runOnJS(onDismiss)();
        });
      } else {
        // Snap back
        translateX.value = withSpring(0);
        opacity.value = withSpring(1);
      }
    },
  });
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
    opacity: opacity.value,
  }));
  
  return (
    <PanGestureHandler onGestureEvent={gestureHandler}>
      <Animated.View style={[styles.card, animatedStyle]}>
        <AlertContent alert={alert} />
      </Animated.View>
    </PanGestureHandler>
  );
}
```

---

## 📱 Component Specifications

### AlertsList Component

```typescript
interface AlertsListProps {
  alerts: RiskAlert[];
  onAcknowledge: (alertId: string, actedUpon: boolean) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onViewDetails: (alert: RiskAlert) => void;
}

function AlertsList({ alerts, onAcknowledge, onDismiss, onViewDetails }: AlertsListProps) {
  const groupedAlerts = groupAlertsByDate(alerts);
  
  return (
    <div className="space-y-6">
      {Object.entries(groupedAlerts).map(([date, dateAlerts]) => (
        <div key={date}>
          <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">
            {date} ({dateAlerts.length} alerts)
          </h3>
          <div className="space-y-3">
            {dateAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={onAcknowledge}
                onDismiss={onDismiss}
                onViewDetails={onViewDetails}
              />
            ))}
          </div>
        </div>
      ))}
      
      {alerts.length === 0 && (
        <EmptyState
          icon="✓"
          title="No active alerts"
          description="All your protocols are looking good!"
        />
      )}
    </div>
  );
}
```

### AlertCard Component

```typescript
interface AlertCardProps {
  alert: RiskAlert;
  onAcknowledge: (alertId: string, actedUpon: boolean) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onViewDetails: (alert: RiskAlert) => void;
}

function AlertCard({ alert, onAcknowledge, onDismiss, onViewDetails }: AlertCardProps) {
  const getSeverityColor = (severity: string) => {
    const colors = {
      CRITICAL: 'border-red-500 bg-red-50',
      HIGH: 'border-orange-500 bg-orange-50',
      MEDIUM: 'border-yellow-500 bg-yellow-50',
      LOW: 'border-green-500 bg-green-50',
    };
    return colors[severity] || colors.MEDIUM;
  };
  
  return (
    <div className={`border-l-4 rounded-lg p-4 ${getSeverityColor(alert.severity)}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <SeverityBadge severity={alert.severity} />
          <span className="font-bold">{alert.protocol_name}</span>
        </div>
        <span className="text-xs text-gray-500">
          {formatRelativeTime(alert.created_at)}
        </span>
      </div>
      
      <p className="text-sm text-gray-700 mb-3">{alert.message}</p>
      
      {alert.risk_change && (
        <div className="text-sm mb-3">
          <span className="text-gray-600">Risk: </span>
          <span className="font-semibold">{alert.current_risk_score.toFixed(1)}</span>
          {' '}
          <RiskChangeIndicator change={alert.risk_change} />
        </div>
      )}
      
      {alert.recommendations.length > 0 && (
        <div className="text-sm mb-3">
          <div className="font-semibold text-gray-700 mb-1">Recommendations:</div>
          <ul className="space-y-1">
            {alert.recommendations.slice(0, 2).map((rec, idx) => (
              <li key={idx} className="text-gray-600">• {rec}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="flex gap-2">
        <button
          onClick={() => onAcknowledge(alert.id, true)}
          className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
        >
          I Took Action
        </button>
        <button
          onClick={() => onDismiss(alert.id)}
          className="px-3 py-2 text-gray-600 text-sm hover:text-gray-800"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
```

---

## 🔗 React Hooks

### useRiskAlerts Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useRiskAlerts() {
  const queryClient = useQueryClient();
  
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['risk-alerts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/alerts/risk');
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
  
  const acknowledgeAlert = useMutation({
    mutationFn: async ({ alertId, actedUpon }: { alertId: string; actedUpon: boolean }) => {
      await api.put(`/api/v1/alerts/risk/${alertId}/acknowledge`, { acted_upon: actedUpon });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-alerts'] });
      toast.success('Alert acknowledged');
    },
  });
  
  const dismissAlert = useMutation({
    mutationFn: async (alertId: string) => {
      await api.delete(`/api/v1/alerts/risk/${alertId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-alerts'] });
      toast.success('Alert dismissed');
    },
  });
  
  return {
    alerts: alerts?.alerts || [],
    total: alerts?.total || 0,
    unacknowledged: alerts?.unacknowledged || 0,
    isLoading,
    acknowledgeAlert: acknowledgeAlert.mutate,
    dismissAlert: dismissAlert.mutate,
  };
}
```

### useAlertSubscription Hook

```typescript
export function useAlertSubscription() {
  const queryClient = useQueryClient();
  
  const { data: subscription } = useQuery({
    queryKey: ['alert-subscription'],
    queryFn: async () => {
      const response = await api.get('/api/v1/alerts/subscription');
      return response.data;
    },
  });
  
  const updateSubscription = useMutation({
    mutationFn: async (updates: UpdateSubscriptionRequest) => {
      const response = await api.put('/api/v1/alerts/subscription', updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-subscription'] });
      toast.success('Alert settings updated');
    },
  });
  
  const subscribeToProtocol = useMutation({
    mutationFn: async (protocolId: string) => {
      await api.post(`/api/v1/alerts/subscription/protocols/${protocolId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-subscription'] });
      toast.success('Subscribed to protocol alerts');
    },
  });
  
  const unsubscribeFromProtocol = useMutation({
    mutationFn: async (protocolId: string) => {
      await api.delete(`/api/v1/alerts/subscription/protocols/${protocolId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-subscription'] });
      toast.success('Unsubscribed from protocol');
    },
  });
  
  return {
    subscription,
    updateSubscription: updateSubscription.mutate,
    subscribeToProtocol: subscribeToProtocol.mutate,
    unsubscribeFromProtocol: unsubscribeFromProtocol.mutate,
  };
}
```

---

## 🎭 User Flows

### Flow 1: Receive and Act on Critical Alert

```
1. User has app open (or background)
   ↓
2. Backend detects critical risk change
   ↓
3. WebSocket pushes alert to user (<1 second)
   ↓
4. Alert toast appears with critical indicator
   ↓
5. User taps "View Details"
   ↓
6. Alert detail screen opens with full context
   ↓
7. User reviews risk timeline and recommendations
   ↓
8. User taps "I Took Action" (or quick action button)
   ↓
9. Alert marked as acted upon
   ↓
10. Confirmation toast: "Thanks for taking action"
```

### Flow 2: Configure Alert Preferences

```
1. User navigates to Settings > Alerts
   ↓
2. Views current subscription settings
   ↓
3. Adjusts severity threshold (e.g., High & above only)
   ↓
4. Disables price alerts (too noisy)
   ↓
5. Increases max alerts per hour to 15
   ↓
6. Taps "Save Changes"
   ↓
7. Settings updated immediately
   ↓
8. Future alerts respect new preferences
```

---

## ⚠️ Error Handling

```typescript
const alertErrors = {
  ALERT_001: 'Failed to load alerts',
  ALERT_002: 'Failed to acknowledge alert',
  ALERT_003: 'Failed to dismiss alert',
  ALERT_004: 'Alert not found',
  ALERT_005: 'Not your alert',
  ALERT_006: 'Failed to update subscription',
  ALERT_007: 'Too many alerts per hour',
};

// Handle acknowledgement error
try {
  await acknowledgeAlert(alertId, true);
} catch (error) {
  if (error.code === 'ALERT_005') {
    toast.error('You can only acknowledge your own alerts');
  } else {
    toast.error('Failed to acknowledge alert. Please try again.');
  }
}
```

---

## ♿ Accessibility

### ARIA Labels

```typescript
<button
  aria-label={`Acknowledge ${alert.severity} risk alert for ${alert.protocol_name}. ${alert.message}`}
  onClick={() => onAcknowledge(alert.id, false)}
>
  Acknowledge
</button>
```

### Screen Reader Support

```typescript
<div role="alert" aria-live="assertive" aria-atomic="true">
  {alert.severity === 'CRITICAL' && (
    <span className="sr-only">
      Critical risk alert for {alert.protocol_name}: {alert.message}
    </span>
  )}
</div>
```

---

## 🔒 Security

### Alert Ownership Validation

```typescript
// Backend validates alert belongs to user
if (alert.user_id !== currentUser.id) {
  throw new UnauthorizedError('Not your alert');
}
```

---

## 🧪 Testing

```typescript
describe('AlertsList', () => {
  it('displays active alerts', () => {
    const { getByText } = render(
      <AlertsList alerts={mockAlerts} onAcknowledge={jest.fn()} onDismiss={jest.fn()} onViewDetails={jest.fn()} />
    );
    
    expect(getByText('Aave V3 - Risk Spike')).toBeInTheDocument();
    expect(getByText('CRITICAL')).toBeInTheDocument();
  });
  
  it('acknowledges alert on button click', async () => {
    const mockAcknowledge = jest.fn();
    const { getByText } = render(
      <AlertCard alert={mockAlert} onAcknowledge={mockAcknowledge} onDismiss={jest.fn()} onViewDetails={jest.fn()} />
    );
    
    fireEvent.click(getByText('I Took Action'));
    
    await waitFor(() => {
      expect(mockAcknowledge).toHaveBeenCalledWith(mockAlert.id, true);
    });
  });
});
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Risk Alerts*  
*Backend Status: ✅ 100% Implemented (7 endpoints + WebSocket)*  
*Frontend Status: ✅ Ready for Implementation*

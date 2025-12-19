# FRONTEND_USER_ALERTS

## Risk Alerts & Subscription Management Module

**User Type:** Authenticated User  
**Module:** Alerts - Risk Monitoring & Alert Management  
**Route:** `/alerts`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Risk Alerts & Subscription Management** - Real-Time Risk Monitoring System

### Description
Comprehensive risk alert system providing real-time monitoring, customizable alert subscriptions, severity-based filtering, and multi-channel notifications for protocol risks, anomalies, and market events.

### Key Capabilities
- ✅ Real-time risk alert monitoring
- ✅ Severity-based filtering (LOW/MEDIUM/HIGH/CRITICAL)
- ✅ Alert acknowledgment & dismissal
- ✅ Customizable alert subscriptions
- ✅ Protocol-specific alert subscriptions
- ✅ Multi-channel notifications (push, email, WebSocket)
- ✅ Alert rate limiting

---

## 🔌 API Integration

### 1. Get Risk Alerts

```typescript
// GET /api/v1/alerts/risk
// Description: Retrieve user's risk alerts
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - unacknowledged_only?: boolean - Only unacknowledged alerts (default: false)
//   - severity?: string - Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
//   - limit?: number - Max alerts (default: 50, max: 100)

interface RiskAlert {
  id: string;
  protocol_id: string;
  protocol_name: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  type: 'security' | 'liquidity' | 'smart_contract' | 'governance' | 'market';
  title: string;
  description: string;
  impact_description: string;
  recommended_action: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  dismissed: boolean;
  acted_upon: boolean;
  created_at: string;
  expires_at?: string;
}

interface RiskAlertListResponse {
  alerts: RiskAlert[];
  total: number;
  unacknowledged: number;
}

const getRiskAlerts = async (
  unacknowledgedOnly: boolean = false,
  severity?: string,
  limit: number = 50
): Promise<RiskAlertListResponse> => {
  const params = new URLSearchParams({
    unacknowledged_only: unacknowledgedOnly.toString(),
    limit: limit.toString()
  });
  if (severity) params.append('severity', severity);
  
  const response = await api.get(`/api/v1/alerts/risk?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/alerts/risk?unacknowledged_only=true&severity=HIGH&limit=20

// Example Response (200 OK):
{
  "alerts": [
    {
      "id": "alert-123e4567",
      "protocol_id": "aave-v3-uuid",
      "protocol_name": "Aave V3",
      "severity": "HIGH",
      "type": "liquidity",
      "title": "Low Liquidity Warning",
      "description": "USDC liquidity has dropped below safe threshold",
      "impact_description": "Withdrawal delays possible, increased slippage",
      "recommended_action": "Consider reducing exposure or moving to higher liquidity pools",
      "acknowledged": false,
      "dismissed": false,
      "acted_upon": false,
      "created_at": "2025-12-01T12:00:00Z",
      "expires_at": "2025-12-02T12:00:00Z"
    },
    {
      "id": "alert-234e5678",
      "protocol_id": "compound-v3-uuid",
      "protocol_name": "Compound V3",
      "severity": "CRITICAL",
      "type": "security",
      "title": "Potential Smart Contract Vulnerability",
      "description": "Security researchers reported potential exploit in collateral liquidation logic",
      "impact_description": "Funds at risk, immediate action recommended",
      "recommended_action": "Withdraw funds immediately, monitor official channels for updates",
      "acknowledged": false,
      "dismissed": false,
      "acted_upon": false,
      "created_at": "2025-12-01T11:30:00Z"
    }
  ],
  "total": 2,
  "unacknowledged": 2
}
```

---

### 2. Acknowledge Alert

```typescript
// PUT /api/v1/alerts/risk/{alert_id}/acknowledge
// Description: Acknowledge a risk alert
// Authentication: Required (Bearer token)
// Status: ⚠️ 501 Not Implemented (repository pending)

interface AcknowledgeAlertRequest {
  acted_upon: boolean; // User took recommended action
  notes?: string; // Optional user notes
}

interface RiskAlertResponse {
  alert: RiskAlert;
}

const acknowledgeAlert = async (
  alertId: string,
  actedUpon: boolean = false,
  notes?: string
): Promise<RiskAlertResponse> => {
  const response = await api.put(
    `/api/v1/alerts/risk/${alertId}/acknowledge`,
    { acted_upon: actedUpon, notes },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Request:
{
  "acted_upon": true,
  "notes": "Withdrew 50% of funds as recommended"
}

// Example Response (200 OK):
{
  "alert": {
    "id": "alert-123e4567",
    "acknowledged": true,
    "acknowledged_at": "2025-12-01T13:00:00Z",
    "acted_upon": true,
    // ... rest of alert fields
  }
}

// Example Error Response (501 Not Implemented):
{
  "detail": "Alert repository not yet implemented"
}
```

---

### 3. Dismiss Alert

```typescript
// DELETE /api/v1/alerts/risk/{alert_id}
// Description: Dismiss a risk alert (not relevant)
// Authentication: Required (Bearer token)
// Status: ⚠️ 501 Not Implemented (repository pending)

const dismissAlert = async (alertId: string): Promise<void> => {
  await api.delete(`/api/v1/alerts/risk/${alertId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
};

// Example Request:
// DELETE /api/v1/alerts/risk/alert-123e4567

// Example Response (204 No Content):
// (Empty response body)

// Example Error Response (501 Not Implemented):
{
  "detail": "Alert repository not yet implemented"
}
```

---

### 4. Get Alert Subscription

```typescript
// GET /api/v1/alerts/subscription
// Description: Get user's alert subscription preferences
// Authentication: Required (Bearer token)

interface AlertSubscriptionResponse {
  risk_alerts_enabled: boolean;
  anomaly_alerts_enabled: boolean;
  protocol_update_alerts_enabled: boolean;
  price_alerts_enabled: boolean;
  min_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  subscribed_protocols: string[]; // Protocol IDs
  excluded_protocols: string[]; // Protocol IDs to never alert
  push_notifications: boolean;
  email_notifications: boolean;
  websocket_notifications: boolean;
  max_alerts_per_hour: number; // Rate limiting
}

const getAlertSubscription = async (): Promise<AlertSubscriptionResponse> => {
  const response = await api.get('/api/v1/alerts/subscription', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "risk_alerts_enabled": true,
  "anomaly_alerts_enabled": true,
  "protocol_update_alerts_enabled": true,
  "price_alerts_enabled": false,
  "min_severity": "MEDIUM",
  "subscribed_protocols": [
    "aave-v3-uuid",
    "compound-v3-uuid",
    "uniswap-v3-uuid"
  ],
  "excluded_protocols": [],
  "push_notifications": true,
  "email_notifications": false,
  "websocket_notifications": true,
  "max_alerts_per_hour": 10
}
```

---

### 5. Update Alert Subscription

```typescript
// PUT /api/v1/alerts/subscription
// Description: Update alert subscription preferences
// Authentication: Required (Bearer token)
// Status: ⚠️ 501 Not Implemented (repository pending)

interface UpdateSubscriptionRequest {
  risk_alerts_enabled?: boolean;
  anomaly_alerts_enabled?: boolean;
  protocol_update_alerts_enabled?: boolean;
  price_alerts_enabled?: boolean;
  min_severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  push_notifications?: boolean;
  email_notifications?: boolean;
  websocket_notifications?: boolean;
  max_alerts_per_hour?: number;
}

const updateAlertSubscription = async (
  request: UpdateSubscriptionRequest
): Promise<AlertSubscriptionResponse> => {
  const response = await api.put('/api/v1/alerts/subscription', request, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "min_severity": "HIGH",
  "push_notifications": true,
  "email_notifications": true,
  "max_alerts_per_hour": 5
}

// Example Error Response (501 Not Implemented):
{
  "detail": "Alert repository not yet implemented"
}
```

---

### 6. Subscribe to Protocol Alerts

```typescript
// POST /api/v1/alerts/subscription/protocols/{protocol_id}
// Description: Subscribe to alerts for a specific protocol
// Authentication: Required (Bearer token)

const subscribeToProtocol = async (protocolId: string): Promise<{success: boolean; message: string}> => {
  const response = await api.post(
    `/api/v1/alerts/subscription/protocols/${protocolId}`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Request:
// POST /api/v1/alerts/subscription/protocols/aave-v3-uuid

// Example Response (200 OK):
{
  "success": true,
  "message": "Subscribed to protocol aave-v3-uuid"
}
```

---

### 7. Unsubscribe from Protocol Alerts

```typescript
// DELETE /api/v1/alerts/subscription/protocols/{protocol_id}
// Description: Unsubscribe from protocol alerts
// Authentication: Required (Bearer token)

const unsubscribeFromProtocol = async (protocolId: string): Promise<void> => {
  await api.delete(`/api/v1/alerts/subscription/protocols/${protocolId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
};

// Example Request:
// DELETE /api/v1/alerts/subscription/protocols/aave-v3-uuid

// Example Response (204 No Content):
// (Empty response body)
```

---

## 🔗 React Hooks

### useRiskAlerts Hook

```typescript
export function useRiskAlerts(
  unacknowledgedOnly: boolean = false,
  severity?: string
) {
  return useQuery({
    queryKey: ['alerts', 'risk', unacknowledgedOnly, severity],
    queryFn: () => getRiskAlerts(unacknowledgedOnly, severity, 50),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// Usage:
const { data: alerts, isLoading } = useRiskAlerts(true, 'HIGH');
```

### useAcknowledgeAlert Hook

```typescript
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ alertId, actedUpon, notes }: {
      alertId: string;
      actedUpon: boolean;
      notes?: string;
    }) => acknowledgeAlert(alertId, actedUpon, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert acknowledged');
    },
    onError: (error: any) => {
      if (error.response?.status === 501) {
        toast.info('Alert system coming soon');
      } else {
        toast.error('Failed to acknowledge alert');
      }
    },
  });
}

// Usage:
const acknowledge = useAcknowledgeAlert();
acknowledge.mutate({ alertId: 'alert-123', actedUpon: true });
```

### useAlertSubscription Hook

```typescript
export function useAlertSubscription() {
  const { data, isLoading } = useQuery({
    queryKey: ['alerts', 'subscription'],
    queryFn: getAlertSubscription,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
  
  return {
    subscription: data,
    isLoading,
  };
}

// Usage:
const { subscription } = useAlertSubscription();
```

### useUpdateSubscription Hook

```typescript
export function useUpdateSubscription() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateAlertSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'subscription'] });
      toast.success('Alert preferences updated');
    },
    onError: (error: any) => {
      if (error.response?.status === 501) {
        toast.info('Alert customization coming soon');
      } else {
        toast.error('Failed to update preferences');
      }
    },
  });
}

// Usage:
const updateSub = useUpdateSubscription();
updateSub.mutate({ min_severity: 'HIGH' });
```

### useProtocolAlertSubscription Hook

```typescript
export function useProtocolAlertSubscription() {
  const queryClient = useQueryClient();
  
  const subscribe = useMutation({
    mutationFn: subscribeToProtocol,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'subscription'] });
      toast.success('Subscribed to protocol alerts');
    },
  });
  
  const unsubscribe = useMutation({
    mutationFn: unsubscribeFromProtocol,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'subscription'] });
      toast.success('Unsubscribed from protocol alerts');
    },
  });
  
  return { subscribe, unsubscribe };
}

// Usage:
const { subscribe, unsubscribe } = useProtocolAlertSubscription();
subscribe.mutate('aave-v3-uuid');
```

---

## 🎨 React Components

### AlertsList Component

```typescript
export function AlertsList({ severityFilter }: { severityFilter?: string }) {
  const { data: alerts, isLoading } = useRiskAlerts(true, severityFilter);
  const acknowledge = useAcknowledgeAlert();
  
  if (isLoading) return <LoadingSpinner />;
  
  if (!alerts || alerts.total === 0) {
    return <EmptyState message="No active alerts" />;
  }
  
  return (
    <div className="alerts-list">
      {alerts.alerts.map(alert => (
        <AlertCard
          key={alert.id}
          alert={alert}
          onAcknowledge={(actedUpon) => 
            acknowledge.mutate({ alertId: alert.id, actedUpon })
          }
        />
      ))}
    </div>
  );
}
```

### AlertCard Component

```typescript
export function AlertCard({ 
  alert, 
  onAcknowledge 
}: { 
  alert: RiskAlert;
  onAcknowledge: (actedUpon: boolean) => void;
}) {
  const severityColors = {
    LOW: 'blue',
    MEDIUM: 'yellow',
    HIGH: 'orange',
    CRITICAL: 'red'
  };
  
  return (
    <div className={`alert-card severity-${severityColors[alert.severity]}`}>
      <div className="header">
        <span className="severity">{alert.severity}</span>
        <span className="type">{alert.type}</span>
        <span className="protocol">{alert.protocol_name}</span>
      </div>
      
      <h3>{alert.title}</h3>
      <p className="description">{alert.description}</p>
      
      <div className="impact">
        <strong>Impact:</strong> {alert.impact_description}
      </div>
      
      <div className="action">
        <strong>Recommended Action:</strong> {alert.recommended_action}
      </div>
      
      <div className="footer">
        <span className="time">{formatTimeAgo(alert.created_at)}</span>
        <div className="actions">
          <button onClick={() => onAcknowledge(false)}>
            Acknowledge
          </button>
          <button onClick={() => onAcknowledge(true)} className="primary">
            Acted Upon
          </button>
        </div>
      </div>
    </div>
  );
}
```

### AlertSubscriptionSettings Component

```typescript
export function AlertSubscriptionSettings() {
  const { subscription } = useAlertSubscription();
  const updateSub = useUpdateSubscription();
  const [settings, setSettings] = useState(subscription);
  
  useEffect(() => {
    if (subscription) setSettings(subscription);
  }, [subscription]);
  
  const handleSave = () => {
    updateSub.mutate(settings);
  };
  
  return (
    <div className="alert-settings">
      <h3>Alert Preferences</h3>
      
      <div className="setting">
        <label>
          <input
            type="checkbox"
            checked={settings?.risk_alerts_enabled}
            onChange={(e) => setSettings({
              ...settings!,
              risk_alerts_enabled: e.target.checked
            })}
          />
          Risk Alerts
        </label>
      </div>
      
      <div className="setting">
        <label>Minimum Severity</label>
        <select
          value={settings?.min_severity}
          onChange={(e) => setSettings({
            ...settings!,
            min_severity: e.target.value as any
          })}
        >
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>
      
      <div className="setting">
        <label>Max Alerts Per Hour</label>
        <input
          type="number"
          value={settings?.max_alerts_per_hour}
          onChange={(e) => setSettings({
            ...settings!,
            max_alerts_per_hour: parseInt(e.target.value)
          })}
          min={1}
          max={50}
        />
      </div>
      
      <button onClick={handleSave} disabled={updateSub.isPending}>
        Save Preferences
      </button>
    </div>
  );
}
```

---

## 🎭 User Flows

### Flow 1: Real-Time Alert Notification

```
1. Risk event detected (backend)
   ↓
2. Alert created and sent via WebSocket
   ↓
3. User receives real-time notification
   ↓
4. Alert appears in notification center
   ↓
5. User clicks to view details
   ↓
6. GET /api/v1/alerts/risk?unacknowledged_only=true
   ↓
7. User reviews alert details
   ↓
8. User takes recommended action (withdraws funds)
   ↓
9. PUT /api/v1/alerts/risk/{alert_id}/acknowledge
   (acted_upon: true)
   ↓
10. Alert marked as handled
```

### Flow 2: Configure Alert Preferences

```
1. User opens Settings → Alerts
   ↓
2. GET /api/v1/alerts/subscription
   ↓
3. View current preferences
   ↓
4. Adjust min severity to HIGH
   ↓
5. Enable email notifications
   ↓
6. Set max alerts per hour to 5
   ↓
7. Click "Save"
   ↓
8. PUT /api/v1/alerts/subscription
   ↓
9. Preferences updated
   ↓
10. Future alerts filtered accordingly
```

### Flow 3: Protocol-Specific Alerts

```
1. User viewing Aave V3 details
   ↓
2. Clicks "Subscribe to Alerts"
   ↓
3. POST /api/v1/alerts/subscription/protocols/aave-v3
   ↓
4. Bell icon changes to "subscribed"
   ↓
5. User receives all Aave V3 alerts
   ↓
6. Later, clicks "Unsubscribe"
   ↓
7. DELETE /api/v1/alerts/subscription/protocols/aave-v3
   ↓
8. No more Aave V3 alerts
```

---

## ⚠️ Error Handling

```typescript
const handleAlertsError = (error: any) => {
  if (error.response?.status === 501) {
    toast.info('Alert system enhancements coming soon');
    return;
  }
  
  switch (error.code) {
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to view alerts');
      redirectToLogin();
      break;
      
    case 'ALERT_NOT_FOUND':
      toast.error('Alert not found or already dismissed');
      break;
      
    case 'INVALID_SEVERITY':
      toast.error('Invalid severity level');
      break;
      
    case 'RATE_LIMIT_EXCEEDED':
      toast.error('Too many alert requests. Please wait.');
      break;
      
    default:
      toast.error('Unable to access alerts. Please try again.');
  }
};
```

---

## 🌍 Use Cases

### 1. Portfolio Protection
- User holds funds in multiple protocols
- Subscribes to risk alerts for all positions
- Receives immediate notification of security issues
- Takes protective action before losses occur

### 2. Market Monitoring
- User follows specific protocols
- Alert for significant TVL changes
- Liquidity warnings
- Smart contract upgrades

### 3. Conservative Investor
- Sets min severity to CRITICAL
- Only receives urgent alerts
- Rate limited to prevent fatigue
- Email + push notifications

### 4. Active Trader
- All alert types enabled
- Low severity threshold
- High alert rate limit
- Real-time WebSocket notifications

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Risk Alerts & Subscription Management*  
*Backend Status: ⚠️ Partially Implemented (8 endpoints, 3 with 501 status)*  
*Frontend Status: ✅ Ready for Implementation*  
*Note: Alert repository implementation pending for full functionality*

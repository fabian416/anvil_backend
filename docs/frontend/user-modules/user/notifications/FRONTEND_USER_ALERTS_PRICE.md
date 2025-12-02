# FRONTEND_USER_ALERTS_PRICE

## User Price Alerts Module

**User Type:** Authenticated User  
**Module:** Price Alerts  
**Route:** `/alerts`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Price Alerts** - Custom Price Notifications

### Description
Set custom price alerts for tokens to get notified when prices hit target levels.

---

## 🖼️ Views & Wireframes

### View 1: Alerts List

```
┌─────────────────────────────────────┐
│  [←]     Price Alerts    [+ Add]   │
│                                     │
│  Active Alerts                      │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ ETH                     ││
│  │ │ Ξ   │ Above $2,600           ││
│  │ └─────┘ Current: $2,510 ↑      ││
│  │                        [Edit]  ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ ETH                     ││
│  │ │ Ξ   │ Below $2,400           ││
│  │ └─────┘ Current: $2,510 ↑      ││
│  │                        [Edit]  ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ ARB                     ││
│  │ │ ◆   │ Above $1.00            ││
│  │ └─────┘ Current: $0.80 ↓       ││
│  │                        [Edit]  ││
│  └─────────────────────────────────┘│
│                                     │
│  Triggered (Last 7 Days)            │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ BTC                     ││
│  │ │ ₿   │ Above $43,000          ││
│  │ └─────┘ ✅ Triggered Nov 30    ││
│  │                      [Reactivate]│
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 2: Create Alert

```
┌─────────────────────────────────────┐
│  [←]    Create Alert               │
│                                     │
│  Token                              │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐                        ││
│  │ │ Ξ   │ ETH              [▼]  ││
│  │ └─────┘ Current: $2,510        ││
│  └─────────────────────────────────┘│
│                                     │
│  Alert When                         │
│  ┌─────────────────────────────────┐│
│  │ [● Above]  [ Below]             ││
│  └─────────────────────────────────┘│
│                                     │
│  Target Price                       │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │     $   2,600                   ││
│  │                                 ││
│  │  +3.6% from current price      ││
│  └─────────────────────────────────┘│
│                                     │
│  Quick Set                          │
│  ┌─────────────────────────────────┐│
│  │ [+5%] [+10%] [+15%] [+20%]     ││
│  └─────────────────────────────────┘│
│                                     │
│  Notify Via                         │
│  ┌─────────────────────────────────┐│
│  │ [✓] Push Notification           ││
│  │ [✓] Email                       ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │         Create Alert            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/alerts
interface GetAlertsResponse {
  success: true;
  data: {
    active: PriceAlert[];
    triggered: PriceAlert[];
  };
}

interface PriceAlert {
  id: string;
  token: TokenInfo;
  condition: 'above' | 'below';
  target_price: number;
  current_price: number;
  status: 'active' | 'triggered' | 'disabled';
  notify_push: boolean;
  notify_email: boolean;
  triggered_at?: string;
  created_at: string;
}

// POST /api/alerts
interface CreateAlertRequest {
  token: string;
  condition: 'above' | 'below';
  target_price: number;
  notify_push?: boolean;
  notify_email?: boolean;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Price Alerts*

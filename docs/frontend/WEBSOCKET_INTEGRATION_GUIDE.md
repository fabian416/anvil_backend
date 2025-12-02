# WebSocket Integration Guide

**Version**: 1.0  
**Last Updated**: December 1, 2025  
**Platform**: Web & Mobile

---

## 🎯 Overview

Complete guide for integrating WebSocket real-time features into the Anvil frontend. Covers connection management, event handling, React integration, and best practices.

---

## 🔌 WebSocket Endpoints

### Graph Updates WebSocket
```
ws://api.anvil.com/api/v1/ws/graph?token={jwt_token}
wss://api.anvil.com/api/v1/ws/graph?token={jwt_token} (production)
```

**Purpose**: Real-time graph updates, risk alerts, protocol changes

---

### Chat WebSocket
```
ws://api.anvil.com/api/v1/ws/chat?token={jwt_token}
```

**Purpose**: Real-time chat streaming, typing indicators, transaction status

---

## 🔐 Authentication

### JWT Token
All WebSocket connections require JWT authentication via query parameter:

```typescript
const token = await getAuthToken(); // From your auth system
const ws = new WebSocket(`${WS_URL}?token=${token}`);
```

**Security Notes**:
- Token validated on connection
- Connection rejected if token invalid
- Token expiration enforced
- Reconnect with fresh token on expiry

---

## 📡 Connection Management

### Basic Connection

```typescript
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // ms
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  constructor(
    private url: string,
    private token: string,
    private onMessage: (data: any) => void
  ) {}
  
  connect() {
    const wsUrl = `${this.url}?token=${this.token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = this.handleOpen.bind(this);
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onerror = this.handleError.bind(this);
    this.ws.onclose = this.handleClose.bind(this);
  }
  
  private handleOpen() {
    console.log('✅ WebSocket connected');
    this.reconnectAttempts = 0;
    this.startHeartbeat();
  }
  
  private handleMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      this.onMessage(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }
  
  private handleError(error: Event) {
    console.error('❌ WebSocket error:', error);
  }
  
  private handleClose(event: CloseEvent) {
    console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
    this.stopHeartbeat();
    this.attemptReconnect();
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }
  
  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ action: 'ping' });
      }
    }, 30000); // 30 seconds
  }
  
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not open, cannot send:', data);
    }
  }
  
  disconnect() {
    this.stopHeartbeat();
    this.ws?.close(1000, 'Client disconnect');
  }
}
```

---

## 📨 Message Protocol

### Client → Server Messages

#### Subscribe to Channel
```json
{
  "action": "subscribe",
  "channel": "graph:updates"
}
```

**Available Channels**:
- `graph:updates` - All protocol updates
- `graph:risk_alerts` - Risk alerts
- `graph:changes` - Graph structure changes
- `graph:anomalies` - Anomaly detection
- `price:updates` - Price changes
- `protocol:{id}` - Specific protocol
- `user:{id}:alerts` - User-specific alerts
- `user:{id}:transactions` - Transaction status

#### Unsubscribe from Channel
```json
{
  "action": "unsubscribe",
  "channel": "graph:updates"
}
```

#### Send Chat Message (Chat WebSocket)
```json
{
  "action": "send_message",
  "conversation_id": "uuid",
  "message": "Find me safe staking protocols",
  "stream_response": true
}
```

#### Heartbeat Ping
```json
{
  "action": "ping"
}
```

---

### Server → Client Messages

#### Protocol Update Event
```json
{
  "type": "protocol:update",
  "protocol_id": "uuid",
  "protocol_name": "Aave V3",
  "change_type": "audit",
  "changes": {
    "audit_added": "Trail of Bits",
    "risk_score": {
      "old": 2.3,
      "new": 2.1
    }
  },
  "timestamp": 1701388800
}
```

#### Risk Alert Event
```json
{
  "type": "risk:alert",
  "protocol_id": "uuid",
  "protocol_name": "Euler Finance",
  "severity": "CRITICAL",
  "message": "Risk score increased significantly",
  "risk_score": 7.8,
  "risk_change": 2.6,
  "timestamp": 1701388800
}
```

#### Graph Change Event
```json
{
  "type": "graph:change",
  "change_type": "edge_added",
  "entity_type": "Protocol",
  "entity_id": "uuid",
  "entity_name": "Aave V3",
  "details": {
    "relationship": "DEPENDS_ON",
    "target": "Chainlink",
    "target_id": "uuid"
  },
  "timestamp": 1701388800
}
```

#### Price Update Event
```json
{
  "type": "price:update",
  "token_symbol": "ETH",
  "price_usd": 2475.50,
  "price_change_24h": -1.4,
  "volume_24h": 15234567890,
  "timestamp": 1701388800
}
```

#### Transaction Status Event
```json
{
  "type": "transaction:status",
  "transaction_id": "tx-123",
  "status": "success",
  "tx_hash": "0xabc...",
  "details": {
    "amount": "0.5 ETH",
    "gas_used": "$4.32"
  },
  "timestamp": 1701388800
}
```

#### Anomaly Detection Event
```json
{
  "type": "anomaly:detected",
  "protocol_id": "uuid",
  "protocol_name": "Euler Finance",
  "anomaly_type": "tvl_volatility",
  "severity": "HIGH",
  "description": "Unusual withdrawal activity",
  "metrics": {
    "z_score": 4.2,
    "deviation": 15
  },
  "timestamp": 1701388800
}
```

#### Heartbeat Pong
```json
{
  "type": "pong",
  "timestamp": 1701388800
}
```

---

## ⚛️ React Integration

### Complete useWebSocket Hook

```typescript
import { useEffect, useState, useRef, useCallback } from 'react';

interface WebSocketConfig {
  url: string;
  token: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export function useWebSocket(config: WebSocketConfig) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  
  // Subscribe to specific message types
  const on = useCallback((messageType: string, handler: (data: any) => void) => {
    if (!messageHandlersRef.current.has(messageType)) {
      messageHandlersRef.current.set(messageType, new Set());
    }
    messageHandlersRef.current.get(messageType)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      messageHandlersRef.current.get(messageType)?.delete(handler);
    };
  }, []);
  
  // Send message
  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);
  
  // Subscribe to channel
  const subscribe = useCallback((channel: string) => {
    send({ action: 'subscribe', channel });
  }, [send]);
  
  // Unsubscribe from channel
  const unsubscribe = useCallback((channel: string) => {
    send({ action: 'unsubscribe', channel });
  }, [send]);
  
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${config.url}?token=${config.token}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        
        // Start heartbeat
        if (config.heartbeatInterval) {
          heartbeatRef.current = setInterval(() => {
            send({ action: 'ping' });
          }, config.heartbeatInterval);
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Call registered handlers for this message type
          const handlers = messageHandlersRef.current.get(message.type);
          if (handlers) {
            handlers.forEach(handler => handler(message));
          }
          
          // Call wildcard handlers
          const wildcardHandlers = messageHandlersRef.current.get('*');
          if (wildcardHandlers) {
            wildcardHandlers.forEach(handler => handler(message));
          }
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };
      
      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError(new Error('WebSocket connection error'));
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code} ${event.reason}`);
        setIsConnected(false);
        
        // Clear heartbeat
        if (heartbeatRef.current) {
          clearInterval(heartbeatRef.current);
          heartbeatRef.current = null;
        }
        
        // Attempt reconnection
        if (config.autoReconnect && 
            reconnectAttemptsRef.current < (config.maxReconnectAttempts || 5)) {
          reconnectAttemptsRef.current++;
          const delay = 1000 * Math.pow(2, reconnectAttemptsRef.current - 1);
          
          console.log(`Reconnecting in ${delay}ms...`);
          setTimeout(connect, delay);
        }
      };
      
      wsRef.current = ws;
    };
    
    connect();
    
    // Cleanup
    return () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
      wsRef.current?.close(1000, 'Component unmount');
    };
  }, [config.url, config.token]);
  
  return {
    isConnected,
    lastMessage,
    error,
    send,
    subscribe,
    unsubscribe,
    on,
  };
}
```

---

### Usage Example

```typescript
function RealtimeDashboard() {
  const { token } = useAuth();
  const [protocolUpdates, setProtocolUpdates] = useState<any[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<any[]>([]);
  
  const { isConnected, subscribe, on } = useWebSocket({
    url: 'ws://api.anvil.com/api/v1/ws/graph',
    token,
    autoReconnect: true,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
  });
  
  useEffect(() => {
    if (isConnected) {
      // Subscribe to channels
      subscribe('graph:updates');
      subscribe('graph:risk_alerts');
      subscribe('price:updates');
    }
  }, [isConnected]);
  
  useEffect(() => {
    // Register event handlers
    const unsubProtocol = on('protocol:update', (data) => {
      setProtocolUpdates(prev => [data, ...prev]);
      showToast(`${data.protocol_name} updated`);
    });
    
    const unsubRisk = on('risk:alert', (data) => {
      setRiskAlerts(prev => [data, ...prev]);
      if (data.severity === 'CRITICAL') {
        showCriticalAlert(data);
      }
    });
    
    const unsubPrice = on('price:update', (data) => {
      updatePriceDisplay(data.token_symbol, data.price_usd);
    });
    
    // Cleanup handlers
    return () => {
      unsubProtocol();
      unsubRisk();
      unsubPrice();
    };
  }, [on]);
  
  return (
    <div>
      <ConnectionStatus isConnected={isConnected} />
      <ProtocolUpdateFeed updates={protocolUpdates} />
      <RiskAlertPanel alerts={riskAlerts} />
    </div>
  );
}
```

---

## 🎨 React Native Integration

### useWebSocket for React Native

```typescript
import { useEffect, useState, useCallback, useRef } from 'react';

export function useWebSocketNative(url: string, token: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const ws = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    // React Native WebSocket
    ws.current = new WebSocket(`${url}?token=${token}`);
    
    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.current.onmessage = (e: any) => {
      const message = JSON.parse(e.data);
      setMessages(prev => [message, ...prev].slice(0, 100)); // Keep last 100
    };
    
    ws.current.onerror = (e: any) => {
      console.error('WebSocket error:', e.message);
    };
    
    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket closed');
    };
    
    return () => {
      ws.current?.close();
    };
  }, [url, token]);
  
  const subscribe = useCallback((channel: string) => {
    ws.current?.send(JSON.stringify({
      action: 'subscribe',
      channel
    }));
  }, []);
  
  return { isConnected, messages, subscribe };
}
```

---

## 📦 State Management Integration

### With Zustand

```typescript
import create from 'zustand';

interface WebSocketStore {
  isConnected: boolean;
  updates: any[];
  alerts: any[];
  prices: Record<string, number>;
  
  setConnected: (connected: boolean) => void;
  addUpdate: (update: any) => void;
  addAlert: (alert: any) => void;
  updatePrice: (symbol: string, price: number) => void;
}

export const useWebSocketStore = create<WebSocketStore>((set) => ({
  isConnected: false,
  updates: [],
  alerts: [],
  prices: {},
  
  setConnected: (connected) => set({ isConnected: connected }),
  
  addUpdate: (update) => set((state) => ({
    updates: [update, ...state.updates].slice(0, 100)
  })),
  
  addAlert: (alert) => set((state) => ({
    alerts: [alert, ...state.alerts]
  })),
  
  updatePrice: (symbol, price) => set((state) => ({
    prices: { ...state.prices, [symbol]: price }
  })),
}));

// Use in component
function Dashboard() {
  const { isConnected, updates, alerts } = useWebSocketStore();
  const { subscribe, on } = useWebSocket({...});
  
  useEffect(() => {
    on('protocol:update', (data) => {
      useWebSocketStore.getState().addUpdate(data);
    });
    
    on('risk:alert', (data) => {
      useWebSocketStore.getState().addAlert(data);
    });
  }, [on]);
  
  return ...;
}
```

---

### With TanStack Query

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useRealtimeSync() {
  const queryClient = useQueryClient();
  const { on } = useWebSocket({...});
  
  useEffect(() => {
    // Invalidate queries on updates
    on('protocol:update', (data) => {
      // Invalidate protocol query
      queryClient.invalidateQueries(['protocol', data.protocol_id]);
      
      // Invalidate search results
      queryClient.invalidateQueries(['search']);
    });
    
    on('risk:alert', (data) => {
      // Invalidate risk queries
      queryClient.invalidateQueries(['risk', data.protocol_id]);
      queryClient.invalidateQueries(['portfolio', 'risk']);
    });
    
    on('price:update', (data) => {
      // Update price data directly
      queryClient.setQueryData(
        ['price', data.token_symbol],
        data.price_usd
      );
    });
  }, [on, queryClient]);
}
```

---

## 🔔 Notification Integration

### Toast Notifications

```typescript
import { toast } from 'sonner'; // or your toast library

export function useWebSocketNotifications() {
  const { on } = useWebSocket({...});
  
  useEffect(() => {
    on('protocol:update', (data) => {
      toast.success(`${data.protocol_name} updated`, {
        description: data.changes.audit_added 
          ? `New audit: ${data.changes.audit_added}`
          : 'Protocol updated',
      });
    });
    
    on('risk:alert', (data) => {
      const toastFn = {
        LOW: toast.info,
        MEDIUM: toast.warning,
        HIGH: toast.warning,
        CRITICAL: toast.error,
      }[data.severity] || toast.info;
      
      toastFn(`Risk Alert: ${data.protocol_name}`, {
        description: data.message,
        action: {
          label: 'View',
          onClick: () => navigate(`/protocols/${data.protocol_id}/risk`),
        },
      });
    });
  }, [on]);
}
```

---

### Push Notifications (React Native)

```typescript
import * as Notifications from 'expo-notifications';

export function useWebSocketPushNotifications() {
  const { on } = useWebSocket({...});
  
  useEffect(() => {
    on('risk:alert', async (data) => {
      if (data.severity === 'CRITICAL' || data.severity === 'HIGH') {
        await Notifications.scheduleNotificationAsync({
          content: {
            title: `⚠️ ${data.severity} Risk Alert`,
            body: `${data.protocol_name}: ${data.message}`,
            data: {
              protocol_id: data.protocol_id,
              type: 'risk_alert',
            },
          },
          trigger: null, // Immediate
        });
      }
    });
  }, [on]);
}
```

---

## 🎯 Best Practices

### Connection Management
✅ **DO**:
- Reconnect with exponential backoff
- Implement heartbeat/ping-pong
- Handle token expiration
- Clean up on component unmount
- Log connection events

❌ **DON'T**:
- Create multiple connections per page
- Forget to unsubscribe
- Ignore close events
- Skip error handling

---

### Message Handling
✅ **DO**:
- Parse JSON safely with try/catch
- Validate message structure
- Type-check event data
- Handle unknown message types
- Log parsing errors

❌ **DON'T**:
- Assume message structure
- Skip validation
- Ignore malformed messages
- Block UI with heavy processing

---

### State Updates
✅ **DO**:
- Batch state updates
- Use functional updates
- Debounce rapid updates
- Limit stored messages (keep last N)
- Clean up old data

❌ **DON'T**:
- Update state in loops
- Store unlimited messages
- Cause unnecessary re-renders
- Block with synchronous operations

---

### Performance
✅ **DO**:
- Throttle UI updates (max 60fps)
- Use React.memo for update components
- Virtualize long lists
- Debounce rapid events
- Use web workers for heavy processing

❌ **DON'T**:
- Update UI for every message
- Render all updates at once
- Block main thread
- Create memory leaks

---

## 🔒 Security Best Practices

1. **Always use WSS** (TLS) in production
2. **Validate JWT tokens** before connecting
3. **Sanitize message data** before rendering
4. **Limit message size** (prevent memory attacks)
5. **Rate limit** subscriptions per connection
6. **Validate channel names** before subscribing
7. **Never expose tokens** in logs or errors
8. **Close connections** on logout

---

## 🐛 Debugging

### Connection Issues

```typescript
// Enable debug logging
const DEBUG = true;

if (DEBUG) {
  ws.onopen = (e) => console.log('OPEN:', e);
  ws.onclose = (e) => console.log('CLOSE:', e.code, e.reason);
  ws.onerror = (e) => console.error('ERROR:', e);
  ws.onmessage = (e) => console.log('MESSAGE:', e.data);
}
```

### Network Tab
- Chrome DevTools → Network → WS
- View WebSocket frames
- Inspect messages
- Monitor connection state

### Common Issues
| Issue | Cause | Solution |
|-------|-------|----------|
| Connection fails immediately | Invalid token | Check JWT validity |
| Frequent disconnects | Network instability | Implement reconnection |
| No messages received | Not subscribed | Check subscription logic |
| Messages delayed | Network latency | Add timestamp checking |

---

## 📊 Performance Monitoring

```typescript
export function useWebSocketMetrics() {
  const [metrics, setMetrics] = useState({
    messagesReceived: 0,
    messageRate: 0, // msg/sec
    averageLatency: 0, // ms
    reconnections: 0,
  });
  
  const { on, isConnected } = useWebSocket({...});
  
  useEffect(() => {
    const startTime = Date.now();
    let messageCount = 0;
    let totalLatency = 0;
    
    const unsub = on('*', (message) => {
      messageCount++;
      
      // Calculate latency if timestamp present
      if (message.timestamp) {
        const latency = Date.now() - (message.timestamp * 1000);
        totalLatency += latency;
      }
      
      // Update metrics every second
      const elapsed = (Date.now() - startTime) / 1000;
      setMetrics({
        messagesReceived: messageCount,
        messageRate: messageCount / elapsed,
        averageLatency: totalLatency / messageCount,
        reconnections: 0, // Would track from ref
      });
    });
    
    return unsub;
  }, [on]);
  
  return metrics;
}
```

---

## ✅ Testing

### Unit Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import WS from 'jest-websocket-mock';

describe('useWebSocket', () => {
  let server: WS;
  
  beforeEach(() => {
    server = new WS('ws://localhost:8000/ws/graph');
  });
  
  afterEach(() => {
    WS.clean();
  });
  
  it('connects and receives messages', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/graph',
        token: 'test-token',
      })
    );
    
    await server.connected;
    expect(result.current.isConnected).toBe(true);
    
    // Send message from server
    server.send(JSON.stringify({
      type: 'protocol:update',
      protocol_name: 'Aave',
    }));
    
    await waitFor(() => {
      expect(result.current.lastMessage?.protocol_name).toBe('Aave');
    });
  });
});
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Complete WebSocket Integration Guide for Anvil Frontend*

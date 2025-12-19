# FRONTEND_USER_WEBSOCKET_REALTIME

## WebSocket Real-Time Communication Module

**User Type:** Authenticated User  
**Module:** WebSocket - Real-Time Streaming & Push Notifications  
**Route:** `/ws/`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**WebSocket Real-Time** - Streaming Chat, Notifications, and Live Updates

### Description
Real-time bidirectional communication system using WebSocket protocol for instant message streaming, AI agent responses, protocol updates, risk alerts, and push notifications.

### Key Capabilities
- ✅ Real-time chat message streaming
- ✅ Token-by-token AI agent responses
- ✅ Live protocol updates
- ✅ Push risk alerts
- ✅ Push notifications
- ✅ Heartbeat/ping-pong for connection health
- ✅ Automatic reconnection handling
- ✅ Connection lifecycle management
- ✅ Authentication via JWT

---

## 🔌 WebSocket Endpoints

### 1. Chat WebSocket - Real-Time Chat Streaming

```typescript
// WS /api/v1/ws/chat?token={jwt}&session_id={optional}
// Description: Real-time chat with streaming agent responses
// Authentication: Required (JWT token in query parameter)
// Protocol: WebSocket

// Connection URL:
const wsUrl = `ws://localhost:8000/api/v1/ws/chat?token=${accessToken}&session_id=${sessionId}`;
const ws = new WebSocket(wsUrl);

// Client → Server Message Format:
interface ClientChatMessage {
  type: 'message' | 'ping';
  content?: string; // Required for 'message' type
  conversation_id?: string; // Optional conversation UUID
}

// Server → Client Message Formats:

// 1. Stream Token (Real-time AI response)
interface StreamTokenMessage {
  type: 'stream';
  content: string; // Single token
  message_id: string; // Message UUID
}

// 2. Complete Message
interface CompleteMessage {
  type: 'message';
  message: {
    id: string;
    role: 'user' | 'agent' | 'system';
    content: string;
    created_at: string;
    conversation_id: string;
  };
}

// 3. Progress Event (Agent activity)
interface ProgressEvent {
  type: 'progress';
  status: 'thinking' | 'tool_call' | 'processing' | 'searching';
  message: string; // Human-readable progress
  tool?: string; // Tool name being executed
  data?: Record<string, any>; // Additional metadata
}

// 4. Error Message
interface ErrorMessage {
  type: 'error';
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

// 5. Heartbeat Response
interface PongMessage {
  type: 'pong';
  timestamp: string;
}

// TypeScript Implementation:
class ChatWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  
  constructor(
    private token: string,
    private sessionId?: string,
    private onMessage?: (message: any) => void,
    private onError?: (error: any) => void,
    private onClose?: () => void,
  ) {}
  
  connect() {
    const baseUrl = process.env.WS_URL || 'ws://localhost:8000';
    const url = `${baseUrl}/api/v1/ws/chat?token=${this.token}${
      this.sessionId ? `&session_id=${this.sessionId}` : ''
    }`;
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.onMessage?.(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.onError?.(error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.onClose?.();
      this.stopHeartbeat();
      this.attemptReconnect();
    };
  }
  
  sendMessage(content: string, conversationId?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message: ClientChatMessage = {
        type: 'message',
        content,
        conversation_id: conversationId,
      };
      this.ws.send(JSON.stringify(message));
    }
  }
  
  private heartbeatInterval: any;
  
  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Every 30 seconds
  }
  
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);
      
      // Exponential backoff
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
  
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage Example:
const chatWs = new ChatWebSocket(
  accessToken,
  sessionId,
  (message) => {
    switch (message.type) {
      case 'stream':
        // Append token to current response
        appendToCurrentResponse(message.content);
        break;
      
      case 'message':
        // Complete message received
        addMessageToConversation(message.message);
        break;
      
      case 'progress':
        // Show progress indicator
        showProgress(message.message);
        break;
      
      case 'error':
        // Handle error
        showError(message.error.message);
        break;
      
      case 'pong':
        // Heartbeat response
        console.log('Connection alive');
        break;
    }
  },
  (error) => {
    console.error('WebSocket error:', error);
  },
  () => {
    console.log('Connection closed');
  }
);

chatWs.connect();

// Send a message
chatWs.sendMessage('What is the best yield farming protocol?', conversationId);

// Disconnect when done
chatWs.disconnect();
```

---

### 2. Conversation-Specific WebSocket

```typescript
// WS /api/v1/chat/ws/{conversation_id}?token={jwt}
// Description: Real-time updates for a specific conversation
// Authentication: Required (JWT token in query parameter)
// Protocol: WebSocket

// Connection URL:
const wsUrl = `ws://localhost:8000/api/v1/chat/ws/${conversationId}?token=${accessToken}`;
const ws = new WebSocket(wsUrl);

// Message Format (Server → Client):
interface ConversationMessage {
  type: 'message';
  message: {
    id: string;
    role: 'agent' | 'user' | 'system';
    content: string;
    created_at: string;
  };
}

// Heartbeat:
// Client sends: "ping"
// Server responds: "pong"

// Usage:
ws.onopen = () => {
  console.log('Connected to conversation');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'message') {
    // New message in conversation
    addMessageToUI(data.message);
  }
};

// Heartbeat
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

---

### 3. Protocol Updates WebSocket

```typescript
// WS /api/v1/ws/protocols?token={jwt}
// Description: Real-time protocol metrics and updates
// Authentication: Required (JWT token)
// Protocol: WebSocket

// Connection URL:
const wsUrl = `ws://localhost:8000/api/v1/ws/protocols?token=${accessToken}`;
const ws = new WebSocket(wsUrl);

// Server → Client Message Format:
interface ProtocolUpdateMessage {
  type: 'protocol_update';
  data: {
    protocol_id: string;
    protocol_name: string;
    metric: 'tvl' | 'apy' | 'price' | 'volume';
    old_value: number;
    new_value: number;
    change_percent: number;
    timestamp: string;
  };
}

// Example Message:
{
  "type": "protocol_update",
  "data": {
    "protocol_id": "aave-v3",
    "protocol_name": "Aave V3",
    "metric": "tvl",
    "old_value": 5200000000,
    "new_value": 5250000000,
    "change_percent": 0.96,
    "timestamp": "2025-12-01T12:00:00Z"
  }
}
```

---

### 4. Risk Alerts WebSocket

```typescript
// WS /api/v1/ws/risk-alerts?token={jwt}
// Description: Real-time risk alert push notifications
// Authentication: Required (JWT token)
// Protocol: WebSocket

// Connection URL:
const wsUrl = `ws://localhost:8000/api/v1/ws/risk-alerts?token=${accessToken}`;
const ws = new WebSocket(wsUrl);

// Server → Client Message Format:
interface RiskAlertMessage {
  type: 'risk_alert';
  alert: {
    id: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    category: 'market' | 'liquidity' | 'smart_contract' | 'governance';
    title: string;
    message: string;
    protocol_id?: string;
    protocol_name?: string;
    recommendation: string;
    created_at: string;
  };
}

// Example Message:
{
  "type": "risk_alert",
  "alert": {
    "id": "alert_123",
    "severity": "HIGH",
    "category": "liquidity",
    "title": "Low Liquidity Warning",
    "message": "Aave V3 USDC pool liquidity dropped below threshold",
    "protocol_id": "aave-v3",
    "protocol_name": "Aave V3",
    "recommendation": "Consider reducing exposure or withdrawing funds",
    "created_at": "2025-12-01T12:05:00Z"
  }
}

// Usage with React:
useEffect(() => {
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'risk_alert') {
      // Show notification
      showNotification({
        title: message.alert.title,
        body: message.alert.message,
        severity: message.alert.severity,
      });
      
      // Update alerts list
      setAlerts(prev => [message.alert, ...prev]);
    }
  };
  
  return () => ws.close();
}, []);
```

---

### 5. General Notifications WebSocket

```typescript
// WS /api/v1/ws/notifications?token={jwt}
// Description: Real-time general push notifications
// Authentication: Required (JWT token)
// Protocol: WebSocket

// Connection URL:
const wsUrl = `ws://localhost:8000/api/v1/ws/notifications?token=${accessToken}`;
const ws = new WebSocket(wsUrl);

// Server → Client Message Format:
interface NotificationMessage {
  type: 'notification';
  notification: {
    id: string;
    title: string;
    body: string;
    category: 'info' | 'warning' | 'success' | 'error';
    action_url?: string; // Optional link
    action_text?: string; // Optional action button text
    created_at: string;
    read: boolean;
  };
}

// Example Message:
{
  "type": "notification",
  "notification": {
    "id": "notif_456",
    "title": "Subscription Renewed",
    "body": "Your PRO subscription has been renewed successfully",
    "category": "success",
    "action_url": "/settings/subscription",
    "action_text": "View Details",
    "created_at": "2025-12-01T08:00:00Z",
    "read": false
  }
}
```

---

## 🔗 React Hooks

### useChatWebSocket Hook

```typescript
export function useChatWebSocket(conversationId?: string) {
  const [messages, setMessages] = useState<any[]>([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const wsRef = useRef<ChatWebSocket | null>(null);
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    const ws = new ChatWebSocket(
      token,
      conversationId,
      (message) => {
        switch (message.type) {
          case 'stream':
            setCurrentResponse(prev => prev + message.content);
            break;
          
          case 'message':
            setMessages(prev => [...prev, message.message]);
            setCurrentResponse('');
            break;
          
          case 'progress':
            setProgress(message.message);
            break;
          
          case 'error':
            toast.error(message.error.message);
            break;
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      },
      () => {
        setIsConnected(false);
      }
    );
    
    ws.connect();
    setIsConnected(true);
    wsRef.current = ws;
    
    return () => {
      ws.disconnect();
    };
  }, [conversationId]);
  
  const sendMessage = useCallback((content: string) => {
    wsRef.current?.sendMessage(content, conversationId);
  }, [conversationId]);
  
  return {
    messages,
    currentResponse,
    isConnected,
    progress,
    sendMessage,
  };
}
```

### useRiskAlertsWebSocket Hook

```typescript
export function useRiskAlertsWebSocket() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    const ws = new WebSocket(
      `ws://localhost:8000/api/v1/ws/risk-alerts?token=${token}`
    );
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'risk_alert') {
        setAlerts(prev => [message.alert, ...prev]);
        
        // Show push notification
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(message.alert.title, {
            body: message.alert.message,
            icon: '/alert-icon.png',
          });
        }
      }
    };
    
    return () => ws.close();
  }, []);
  
  return { alerts, isConnected };
}
```

---

## 🎭 User Flows

### Flow 1: Real-Time Chat with Streaming

```
1. User opens chat interface
   ↓
2. Component establishes WebSocket connection
   WS /api/v1/ws/chat?token={jwt}
   ↓
3. Connection established (onopen)
   ↓
4. User types message and hits send
   ↓
5. Client sends: { type: 'message', content: '...', conversation_id: '...' }
   ↓
6. Server processes request
   ↓
7. Server sends progress events:
   { type: 'progress', status: 'thinking', message: 'Processing...' }
   ↓
8. Server streams AI response token-by-token:
   { type: 'stream', content: 'The', message_id: '...' }
   { type: 'stream', content: ' best', message_id: '...' }
   { type: 'stream', content: ' protocol', message_id: '...' }
   ↓
9. UI appends each token in real-time
   ↓
10. Server sends complete message:
    { type: 'message', message: { ... } }
   ↓
11. UI finalizes response display
```

### Flow 2: Risk Alert Push Notification

```
1. User has app open with active session
   ↓
2. Risk monitoring detects high-risk event
   ↓
3. Backend publishes alert to WebSocket
   ↓
4. Connected client receives:
   { type: 'risk_alert', alert: { severity: 'HIGH', ... } }
   ↓
5. Client shows in-app notification banner
   ↓
6. If user granted browser notifications:
   Browser push notification appears
   ↓
7. Alert added to alerts list
   ↓
8. User can tap to view details
```

---

## ⚠️ Error Handling & Reconnection

```typescript
const handleWebSocketError = (error: any, ws: WebSocket) => {
  console.error('WebSocket error:', error);
  
  // Close and reconnect
  ws.close();
  
  // Exponential backoff reconnection
  let reconnectAttempt = 0;
  const maxAttempts = 5;
  
  const reconnect = () => {
    if (reconnectAttempt >= maxAttempts) {
      toast.error('Unable to connect. Please refresh the page.');
      return;
    }
    
    reconnectAttempt++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
    
    setTimeout(() => {
      console.log(`Reconnecting... Attempt ${reconnectAttempt}`);
      // Reconnect logic
    }, delay);
  };
  
  reconnect();
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: WebSocket Real-Time*  
*Backend Status: ✅ 100% Implemented (5 WebSocket endpoints)*  
*Frontend Status: ✅ Ready for Implementation*

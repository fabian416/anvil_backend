# FRONTEND_CHAT_WEBSOCKET

## Chat WebSocket Module

**User Type:** Authenticated User  
**Module:** Chat - Real-Time WebSocket Communication  
**Route:** `/chat/ws`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Chat WebSocket** - Real-Time Conversation Updates

### Description
WebSocket connection for real-time chat message delivery, agent responses, and typing indicators.

### Key Capabilities
- ✅ Real-time message delivery
- ✅ Bidirectional communication
- ✅ Automatic reconnection
- ✅ Heartbeat/keepalive
- ✅ JWT authentication

---

## 🔌 WebSocket Integration

### Connection

```typescript
// WS /api/v1/chat/ws/{conversation_id}?token={jwt}

interface WebSocketMessage {
  type: 'message' | 'typing' | 'error';
  message?: {
    id: string;
    role: 'user' | 'agent';
    content: string;
    created_at: string;
  };
  typing?: {
    is_typing: boolean;
    agent_type?: string;
  };
  error?: string;
}

class ChatWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(conversationId: string, token: string) {
    const wsUrl = `wss://api.example.com/api/v1/chat/ws/${conversationId}?token=${token}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.attemptReconnect(conversationId, token);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  private handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'message':
        // Handle new message
        this.onMessage?.(message.message!);
        break;
      case 'typing':
        // Handle typing indicator
        this.onTyping?.(message.typing!);
        break;
      case 'error':
        // Handle error
        this.onError?.(message.error!);
        break;
    }
  }
  
  private startHeartbeat() {
    setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // 30 seconds
  }
  
  private attemptReconnect(conversationId: string, token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect(conversationId, token);
      }, Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000));
    }
  }
  
  disconnect() {
    this.ws?.close();
  }
  
  // Callbacks
  onMessage?: (message: any) => void;
  onTyping?: (typing: any) => void;
  onError?: (error: string) => void;
}
```

### React Hook

```typescript
export function useChatWebSocket(conversationId: string) {
  const [messages, setMessages] = useState<any[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef<ChatWebSocket>();
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    const ws = new ChatWebSocket();
    ws.onMessage = (message) => {
      setMessages(prev => [...prev, message]);
    };
    ws.onTyping = (typing) => {
      setIsTyping(typing.is_typing);
    };
    ws.connect(conversationId, token);
    
    wsRef.current = ws;
    
    return () => {
      ws.disconnect();
    };
  }, [conversationId]);
  
  return { messages, isTyping };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Chat WebSocket*  
*Backend Status: ✅ 100% Implemented (1 WebSocket endpoint)*  
*Frontend Status: ✅ Ready for Implementation*

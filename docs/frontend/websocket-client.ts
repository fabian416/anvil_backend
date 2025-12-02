/**
 * Anvil AI Chat WebSocket Client
 * 
 * Real-time chat client with streaming agent responses.
 * 
 * Features:
 * - Automatic reconnection
 * - Message streaming
 * - Progress events
 * - Token-by-token display
 * - Error handling
 * 
 * Usage:
 * ```typescript
 * const client = new AnvilChatClient({
 *   wsUrl: 'ws://localhost:8000/api/v1/ws/chat',
 *   token: 'your-jwt-token',
 *   sessionId: 'optional-session-id',
 *   onMessage: (data) => console.log('Message:', data),
 *   onStream: (token) => console.log('Stream:', token),
 *   onProgress: (event) => console.log('Progress:', event),
 *   onError: (error) => console.error('Error:', error),
 * });
 * 
 * await client.connect();
 * await client.sendMessage('Swap 1 ETH for USDC');
 * ```
 */

export interface AnvilChatConfig {
  /** WebSocket URL (e.g., 'ws://localhost:8000/api/v1/ws/chat') */
  wsUrl: string;
  
  /** JWT authentication token */
  token: string;
  
  /** Optional session ID for conversation continuity */
  sessionId?: string;
  
  /** Callback for complete messages */
  onMessage?: (data: MessageEvent) => void;
  
  /** Callback for streaming tokens */
  onStream?: (token: string, messageId?: string) => void;
  
  /** Callback for progress events */
  onProgress?: (event: ProgressEvent) => void;
  
  /** Callback for errors */
  onError?: (error: ErrorEvent) => void;
  
  /** Callback for connection established */
  onConnect?: () => void;
  
  /** Callback for connection closed */
  onDisconnect?: () => void;
  
  /** Auto-reconnect on disconnect (default: true) */
  autoReconnect?: boolean;
  
  /** Reconnection delay in ms (default: 3000) */
  reconnectDelay?: number;
  
  /** Max reconnection attempts (default: 5) */
  maxReconnectAttempts?: number;
}

export interface MessageEvent {
  type: 'message' | 'message_complete';
  content: string;
  message_id?: string;
  metadata?: Record<string, any>;
}

export interface StreamEvent {
  type: 'stream';
  content: string;
  message_id?: string;
}

export interface ProgressEvent {
  type: 'progress';
  status: 'thinking' | 'routing' | 'tool_call' | 'tool_completed' | 'processing';
  message: string;
  agent?: string;
  tool?: string;
  data?: Record<string, any>;
}

export interface ErrorEvent {
  type: 'error';
  error: string;
  code?: string;
}

export interface SystemEvent {
  type: 'system';
  message: string;
  user_id?: string;
  session_id?: string;
  timestamp?: string;
}

type WSEvent = MessageEvent | StreamEvent | ProgressEvent | ErrorEvent | SystemEvent;


export class AnvilChatClient {
  private ws: WebSocket | null = null;
  private config: Required<AnvilChatConfig>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isManualClose = false;
  private pingInterval: NodeJS.Timeout | null = null;
  
  constructor(config: AnvilChatConfig) {
    this.config = {
      onMessage: () => {},
      onStream: () => {},
      onProgress: () => {},
      onError: () => {},
      onConnect: () => {},
      onDisconnect: () => {},
      autoReconnect: true,
      reconnectDelay: 3000,
      maxReconnectAttempts: 5,
      ...config,
    };
  }
  
  /**
   * Connect to WebSocket server.
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Build URL with query params
        const url = new URL(this.config.wsUrl);
        url.searchParams.set('token', this.config.token);
        if (this.config.sessionId) {
          url.searchParams.set('session_id', this.config.sessionId);
        }
        
        // Create WebSocket
        this.ws = new WebSocket(url.toString());
        
        // Connection opened
        this.ws.onopen = () => {
          console.log('[AnvilChat] Connected');
          this.reconnectAttempts = 0;
          this.startPingInterval();
          this.config.onConnect();
          resolve();
        };
        
        // Listen for messages
        this.ws.onmessage = (event) => {
          try {
            const data: WSEvent = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('[AnvilChat] Failed to parse message:', error);
          }
        };
        
        // Connection closed
        this.ws.onclose = (event) => {
          console.log('[AnvilChat] Disconnected:', event.code, event.reason);
          this.stopPingInterval();
          this.config.onDisconnect();
          
          // Auto-reconnect
          if (
            this.config.autoReconnect &&
            !this.isManualClose &&
            this.reconnectAttempts < this.config.maxReconnectAttempts
          ) {
            this.scheduleReconnect();
          }
        };
        
        // Connection error
        this.ws.onerror = (error) => {
          console.error('[AnvilChat] WebSocket error:', error);
          reject(error);
        };
        
      } catch (error) {
        console.error('[AnvilChat] Failed to connect:', error);
        reject(error);
      }
    });
  }
  
  /**
   * Disconnect from WebSocket server.
   */
  disconnect(): void {
    this.isManualClose = true;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
  
  /**
   * Send a chat message.
   * 
   * @param content - Message content
   * @param conversationId - Optional conversation ID
   */
  async sendMessage(content: string, conversationId?: string): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }
    
    this.ws.send(JSON.stringify({
      type: 'message',
      content,
      conversation_id: conversationId,
    }));
  }
  
  /**
   * Send a ping to keep connection alive.
   */
  private ping(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    
    this.ws.send(JSON.stringify({ type: 'ping' }));
  }
  
  /**
   * Handle incoming WebSocket messages.
   */
  private handleMessage(data: WSEvent): void {
    switch (data.type) {
      case 'message':
      case 'message_complete':
        this.config.onMessage(data);
        break;
      
      case 'stream':
        this.config.onStream(data.content, data.message_id);
        break;
      
      case 'progress':
        this.config.onProgress(data);
        break;
      
      case 'error':
        this.config.onError(data);
        break;
      
      case 'system':
        console.log('[AnvilChat] System:', data.message);
        break;
      
      default:
        console.warn('[AnvilChat] Unknown message type:', data);
    }
  }
  
  /**
   * Schedule reconnection attempt.
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    console.log(
      `[AnvilChat] Reconnecting in ${this.config.reconnectDelay}ms ` +
      `(attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`
    );
    
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[AnvilChat] Reconnection failed:', error);
      });
    }, this.config.reconnectDelay);
  }
  
  /**
   * Start ping interval to keep connection alive.
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      this.ping();
    }, 30000); // Ping every 30 seconds
  }
  
  /**
   * Stop ping interval.
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
  
  /**
   * Check if WebSocket is connected.
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
  
  /**
   * Get current connection state.
   */
  getState(): 'connecting' | 'open' | 'closing' | 'closed' {
    if (!this.ws) return 'closed';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'open';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'closed';
      default: return 'closed';
    }
  }
}


/**
 * React Hook for Anvil Chat WebSocket
 * 
 * Usage:
 * ```tsx
 * const { sendMessage, isConnected, messages, streamingContent } = useAnvilChat({
 *   token: userToken,
 *   onError: (error) => toast.error(error.error),
 * });
 * 
 * return (
 *   <div>
 *     <div>{messages.map(msg => <Message key={msg.id} {...msg} />)}</div>
 *     {streamingContent && <StreamingMessage content={streamingContent} />}
 *     <input onSubmit={(e) => sendMessage(e.target.value)} />
 *   </div>
 * );
 * ```
 */
export function useAnvilChat(config: Partial<AnvilChatConfig> & { token: string }) {
  // This is a TypeScript interface for reference
  // Actual React implementation would use useState, useEffect, useRef, etc.
  return {
    sendMessage: async (content: string) => {},
    isConnected: false,
    messages: [] as Array<{ id: string; content: string; role: 'user' | 'agent'; timestamp: string }>,
    streamingContent: '',
    progress: null as ProgressEvent | null,
    error: null as ErrorEvent | null,
  };
}


/**
 * Example: Complete React Component
 */
export const ExampleReactComponent = `
import React, { useState, useEffect, useRef } from 'react';
import { AnvilChatClient } from './websocket-client';

export function ChatInterface({ token }: { token: string }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [progress, setProgress] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const clientRef = useRef<AnvilChatClient | null>(null);
  
  useEffect(() => {
    // Create WebSocket client
    const client = new AnvilChatClient({
      wsUrl: 'ws://localhost:8000/api/v1/ws/chat',
      token,
      onConnect: () => setIsConnected(true),
      onDisconnect: () => setIsConnected(false),
      onStream: (token) => {
        setStreamingContent((prev) => prev + token);
      },
      onProgress: (event) => {
        setProgress(event.message);
      },
      onMessage: (data) => {
        setMessages((prev) => [...prev, {
          id: data.message_id || Math.random().toString(),
          content: data.content,
          role: 'agent',
          timestamp: new Date().toISOString(),
        }]);
        setStreamingContent('');
        setProgress(null);
      },
      onError: (error) => {
        console.error('Chat error:', error);
        alert(error.error);
      },
    });
    
    clientRef.current = client;
    client.connect();
    
    return () => {
      client.disconnect();
    };
  }, [token]);
  
  const handleSend = async () => {
    if (!input.trim() || !clientRef.current) return;
    
    // Add user message to UI
    setMessages((prev) => [...prev, {
      id: Math.random().toString(),
      content: input,
      role: 'user',
      timestamp: new Date().toISOString(),
    }]);
    
    // Send to server
    await clientRef.current.sendMessage(input);
    setInput('');
  };
  
  return (
    <div className="chat-interface">
      <div className="status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={\`message \${msg.role}\`}>
            <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
        
        {streamingContent && (
          <div className="message agent streaming">
            <strong>AI:</strong>
            <p>{streamingContent}<span className="cursor">▊</span></p>
          </div>
        )}
        
        {progress && (
          <div className="progress">
            <span className="spinner">⏳</span> {progress}
          </div>
        )}
      </div>
      
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <button onClick={handleSend} disabled={!isConnected}>
          Send
        </button>
      </div>
    </div>
  );
}
`;

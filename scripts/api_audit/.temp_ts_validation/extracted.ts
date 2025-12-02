// Auto-generated TypeScript validation file
// Generated: Tue Dec  2 16:59:39 UTC 2025

const token = await getAuthToken(); // From your auth system
const ws = new WebSocket(`${WS_URL}?token=${token}`);

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

// Enable debug logging
const DEBUG = true;

if (DEBUG) {
  ws.onopen = (e) => console.log('OPEN:', e);
  ws.onclose = (e) => console.log('CLOSE:', e.code, e.reason);
  ws.onerror = (e) => console.error('ERROR:', e);
  ws.onmessage = (e) => console.log('MESSAGE:', e.data);
}

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

// POST /api/v1/admin/distillation/static-responses
// Description: Create pre-defined response template for common queries
// Authentication: Required (Admin role)

interface StaticResponseCreate {
  intent: string; // Query intent classification
  variant: string; // Response variation identifier
  response_template: string; // Template with {{variables}}
  template_variables?: Record<string, any>; // Variable definitions
  data_source?: string; // Where to fetch dynamic data
  conditions?: Record<string, any>; // Conditions for activation
  priority?: number; // Priority when multiple match
  is_active?: boolean;
}

const createStaticResponse = async (
  data: StaticResponseCreate
): Promise<StaticResponseResponse> => {
  const response = await api.post(
    '/api/v1/admin/distillation/static-responses',
    data
  );
  return response.data;
};

// Example Request:
{
  "intent": "get_protocol_tvl",
  "variant": "aave_v3",
  "response_template": "Aave V3 currently has {{tvl_formatted}} in total value locked across {{chain_count}} chains.",
  "template_variables": {
    "tvl_formatted": "$.tvl",
    "chain_count": "$.chains.length"
  },
  "data_source": "defi_llama_api",
  "priority": 10,
  "is_active": true
}

// Example Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "get_protocol_tvl",
  "variant": "aave_v3",
  "response_template": "Aave V3 currently has {{tvl_formatted}}...",
  "priority": 10,
  "is_active": true,
  "created_at": "2025-12-01T12:00:00Z",
  "updated_at": "2025-12-01T12:00:00Z"
}

// GET /api/v1/admin/distillation/static-responses?intent=get_protocol_tvl&is_active=true
// Description: List all static response templates
// Authentication: Required (Admin role)

const listStaticResponses = async (filters?: {
  intent?: string;
  is_active?: boolean;
}): Promise<StaticResponseResponse[]> => {
  const response = await api.get('/api/v1/admin/distillation/static-responses', {
    params: filters
  });
  return response.data;
};

// PATCH /api/v1/admin/distillation/static-responses/{response_id}
// Description: Update static response template
// Authentication: Required (Admin role)

const updateStaticResponse = async (
  responseId: string,
  updates: Partial<StaticResponseCreate>
): Promise<StaticResponseResponse> => {
  const response = await api.patch(
    `/api/v1/admin/distillation/static-responses/${responseId}`,
    updates
  );
  return response.data;
};

// DELETE /api/v1/admin/distillation/static-responses/{response_id}
// Description: Delete static response template
// Authentication: Required (Admin role)

const deleteStaticResponse = async (responseId: string): Promise<void> => {
  await api.delete(`/api/v1/admin/distillation/static-responses/${responseId}`);
};

// GET /api/v1/admin/distillation/config
// Description: Get current distillation system configuration
// Authentication: Required (Admin role)

interface DistillationConfigResponse {
  cache_ttl_seconds: number;
  max_cache_size_mb: number;
  enable_static_responses: boolean;
  enable_semantic_cache: boolean;
  similarity_threshold: number;
  enable_telemetry: boolean;
}

const getDistillationConfig = async (): Promise<DistillationConfigResponse> => {
  const response = await api.get('/api/v1/admin/distillation/config');
  return response.data;
};

// Example Response (200 OK):
{
  "cache_ttl_seconds": 3600,
  "max_cache_size_mb": 500,
  "enable_static_responses": true,
  "enable_semantic_cache": true,
  "similarity_threshold": 0.85,
  "enable_telemetry": true
}

// PATCH /api/v1/admin/distillation/config
// Description: Update distillation configuration
// Authentication: Required (Admin role)

interface DistillationConfigUpdate {
  cache_ttl_seconds?: number;
  max_cache_size_mb?: number;
  enable_static_responses?: boolean;
  enable_semantic_cache?: boolean;
  similarity_threshold?: number;
}

const updateDistillationConfig = async (
  updates: DistillationConfigUpdate
): Promise<DistillationConfigResponse> => {
  const response = await api.patch('/api/v1/admin/distillation/config', updates);
  return response.data;
};

// GET /api/v1/admin/distillation/cache/stats
// Description: Get cache performance statistics
// Authentication: Required (Admin role)

interface CacheStatsResponse {
  total_entries: number;
  cache_size_mb: number;
  hit_rate: number; // Percentage
  miss_rate: number; // Percentage
  avg_response_time_ms: number;
  cached_avg_response_time_ms: number;
  uncached_avg_response_time_ms: number;
  oldest_entry_age_seconds: number;
}

const getCacheStats = async (): Promise<CacheStatsResponse> => {
  const response = await api.get('/api/v1/admin/distillation/cache/stats');
  return response.data;
};

// Example Response (200 OK):
{
  "total_entries": 1250,
  "cache_size_mb": 125.5,
  "hit_rate": 78.5,
  "miss_rate": 21.5,
  "avg_response_time_ms": 450,
  "cached_avg_response_time_ms": 85,
  "uncached_avg_response_time_ms": 1200,
  "oldest_entry_age_seconds": 3200
}

// POST /api/v1/admin/distillation/cache/invalidate
// Description: Invalidate cached responses by pattern or all
// Authentication: Required (Admin role)

interface CacheInvalidateRequest {
  pattern?: string; // Regex pattern to match cache keys
  intent?: string; // Invalidate by intent
  invalidate_all?: boolean; // Clear entire cache
}

const invalidateCache = async (
  data: CacheInvalidateRequest
): Promise<{ invalidated_count: number }> => {
  const response = await api.post('/api/v1/admin/distillation/cache/invalidate', data);
  return response.data;
};

// Example Request (invalidate by intent):
{
  "intent": "get_protocol_tvl"
}

// Example Response (200 OK):
{
  "invalidated_count": 45
}

// GET /api/v1/admin/distillation/telemetry?start_date=2025-11-01&end_date=2025-12-01
// Description: Get telemetry data for distillation system
// Authentication: Required (Admin role)

interface DistillationTelemetryResponse {
  total_queries: number;
  static_responses_used: number;
  semantic_cache_hits: number;
  semantic_cache_misses: number;
  avg_response_time_ms: number;
  cost_savings_usd: number; // Estimated savings from caching
  by_intent: Record<string, {
    query_count: number;
    cache_hit_rate: number;
    avg_response_time_ms: number;
  }>;
}

const getDistillationTelemetry = async (
  startDate: string,
  endDate: string
): Promise<DistillationTelemetryResponse> => {
  const response = await api.get('/api/v1/admin/distillation/telemetry', {
    params: { start_date: startDate, end_date: endDate }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "total_queries": 15000,
  "static_responses_used": 3500,
  "semantic_cache_hits": 8200,
  "semantic_cache_misses": 3300,
  "avg_response_time_ms": 385,
  "cost_savings_usd": 127.50,
  "by_intent": {
    "get_protocol_tvl": {
      "query_count": 5200,
      "cache_hit_rate": 85.2,
      "avg_response_time_ms": 120
    },
    "compare_protocols": {
      "query_count": 3800,
      "cache_hit_rate": 72.5,
      "avg_response_time_ms": 450
    }
  }
}

// GET /api/v1/admin/distillation/summary
// Description: Get high-level summary of distillation system
// Authentication: Required (Admin role)

interface DistillationSummaryResponse {
  status: 'healthy' | 'degraded' | 'critical';
  active_static_responses: number;
  cache_hit_rate_7d: number;
  avg_response_time_7d: number;
  cost_savings_30d: number;
  recommendations: string[];
}

const getDistillationSummary = async (): Promise<DistillationSummaryResponse> => {
  const response = await api.get('/api/v1/admin/distillation/summary');
  return response.data;
};

// Example Response (200 OK):
{
  "status": "healthy",
  "active_static_responses": 127,
  "cache_hit_rate_7d": 78.5,
  "avg_response_time_7d": 420,
  "cost_savings_30d": 485.25,
  "recommendations": [
    "Consider adding static response for 'get_swap_quote' intent (high volume)",
    "Cache hit rate below 80% - review similarity threshold",
    "5 static responses have not been used in 30 days - consider archiving"
  ]
}

export function useDistillationManagement() {
  const queryClient = useQueryClient();
  
  const { data: config } = useQuery({
    queryKey: ['distillation-config'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/distillation/config');
      return response.data;
    },
  });
  
  const { data: stats } = useQuery({
    queryKey: ['distillation-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/distillation/cache/stats');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  const updateConfig = useMutation({
    mutationFn: async (updates: DistillationConfigUpdate) => {
      const response = await api.patch('/api/v1/admin/distillation/config', updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['distillation-config'] });
      toast.success('Configuration updated successfully');
    },
  });
  
  const invalidateCache = useMutation({
    mutationFn: async (data: CacheInvalidateRequest) => {
      const response = await api.post('/api/v1/admin/distillation/cache/invalidate', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['distillation-stats'] });
      toast.success(`Invalidated ${data.invalidated_count} cache entries`);
    },
  });
  
  return {
    config,
    stats,
    updateConfig: updateConfig.mutate,
    invalidateCache: invalidateCache.mutate,
  };
}

// POST /api/v1/admin/projects/
// Description: Create a new project with full configuration
// Authentication: Required (Admin role)

interface ProjectCreate {
  slug: string; // URL-friendly identifier
  name: string;
  description?: string;
  icon?: string; // Icon URL or emoji
  color?: string; // Hex color code
  banner_url?: string;
  status?: 'draft' | 'active' | 'archived';
  visibility?: 'public' | 'private' | 'team';
  system_prompt: string; // AI system prompt for the project
  welcome_message?: string;
  enabled_protocols?: string[]; // List of protocol IDs
  enabled_chains?: string[]; // List of chain names
  enabled_tools?: string[]; // List of tool names
  risk_config?: Record<string, any>; // Risk analysis configuration
  max_users?: number;
  display_order?: number;
  is_featured?: boolean;
}

const createProject = async (data: ProjectCreate): Promise<ProjectResponse> => {
  const response = await api.post('/api/v1/admin/projects/', data);
  return response.data;
};

// Example Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "slug": "defi-yield-optimizer",
  "name": "DeFi Yield Optimizer",
  "description": "AI-powered yield optimization across protocols",
  "icon": "🎯",
  "color": "#3B82F6",
  "status": "active",
  "visibility": "public",
  "system_prompt": "You are a DeFi yield optimization specialist...",
  "enabled_protocols": ["aave-v3", "compound", "curve"],
  "enabled_chains": ["ethereum", "arbitrum", "optimism"],
  "enabled_tools": ["swap", "supply", "yield_analysis"],
  "is_featured": true,
  "created_at": "2025-12-01T12:00:00Z",
  "updated_at": "2025-12-01T12:00:00Z"
}

// GET /api/v1/admin/projects/?status=active&limit=50&offset=0
// Description: List all projects with filters
// Authentication: Required (Admin role)

const listProjects = async (filters?: {
  status?: string;
  visibility?: string;
  is_featured?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ProjectResponse[]> => {
  const response = await api.get('/api/v1/admin/projects/', { params: filters });
  return response.data;
};

// GET /api/v1/admin/projects/{project_id}
// Description: Get single project details
// Authentication: Required (Admin role)

const getProject = async (projectId: string): Promise<ProjectResponse> => {
  const response = await api.get(`/api/v1/admin/projects/${projectId}`);
  return response.data;
};

// PATCH /api/v1/admin/projects/{project_id}
// Description: Update project fields
// Authentication: Required (Admin role)

interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: 'draft' | 'active' | 'archived';
  system_prompt?: string;
  enabled_protocols?: string[];
  // ... other optional fields
}

const updateProject = async (
  projectId: string,
  updates: ProjectUpdate
): Promise<ProjectResponse> => {
  const response = await api.patch(`/api/v1/admin/projects/${projectId}`, updates);
  return response.data;
};

// DELETE /api/v1/admin/projects/{project_id}
// Description: Delete a project (soft delete)
// Authentication: Required (Admin role)

const deleteProject = async (projectId: string): Promise<void> => {
  await api.delete(`/api/v1/admin/projects/${projectId}`);
};

// POST /api/v1/admin/projects/{project_id}/knowledge
// Description: Upload knowledge document for project
// Authentication: Required (Admin role)

interface KnowledgeDocumentCreate {
  title: string;
  content: string; // Markdown or plain text
  document_type: 'protocol_guide' | 'faq' | 'strategy' | 'general';
  metadata?: Record<string, any>;
  is_active?: boolean;
}

const createKnowledgeDocument = async (
  projectId: string,
  data: KnowledgeDocumentCreate
): Promise<KnowledgeDocumentResponse> => {
  const response = await api.post(
    `/api/v1/admin/projects/${projectId}/knowledge`,
    data
  );
  return response.data;
};

// GET /api/v1/admin/projects/{project_id}/knowledge
// Description: List all knowledge documents for a project
// Authentication: Required (Admin role)

const listKnowledgeDocuments = async (
  projectId: string
): Promise<KnowledgeDocumentResponse[]> => {
  const response = await api.get(`/api/v1/admin/projects/${projectId}/knowledge`);
  return response.data;
};

// POST /api/v1/admin/projects/assignments/rules
// Description: Create automatic user assignment rule
// Authentication: Required (Admin role)

interface AssignmentRuleCreate {
  project_id: string;
  rule_type: 'user_tier' | 'subscription' | 'manual';
  conditions: Record<string, any>;
  priority: number;
  is_active: boolean;
}

const createAssignmentRule = async (
  data: AssignmentRuleCreate
): Promise<AssignmentRuleResponse> => {
  const response = await api.post('/api/v1/admin/projects/assignments/rules', data);
  return response.data;
};

// Example Request:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "rule_type": "subscription",
  "conditions": {
    "subscription_tier": "PRO",
    "min_tier": "PRO"
  },
  "priority": 10,
  "is_active": true
}

// GET /api/v1/admin/projects/{project_id}/assignments/rules
// Description: Get assignment rules for a project
// Authentication: Required (Admin role)

const listAssignmentRules = async (
  projectId: string
): Promise<AssignmentRuleResponse[]> => {
  const response = await api.get(
    `/api/v1/admin/projects/${projectId}/assignments/rules`
  );
  return response.data;
};

// PATCH /api/v1/admin/projects/assignments/rules/{rule_id}
// Description: Update assignment rule
// Authentication: Required (Admin role)

const updateAssignmentRule = async (
  ruleId: string,
  updates: Partial<AssignmentRuleCreate>
): Promise<AssignmentRuleResponse> => {
  const response = await api.patch(
    `/api/v1/admin/projects/assignments/rules/${ruleId}`,
    updates
  );
  return response.data;
};

// POST /api/v1/admin/projects/{project_id}/users
// Description: Manually assign user to project
// Authentication: Required (Admin role)

interface UserAssignmentCreate {
  user_id: string;
  role?: 'member' | 'contributor' | 'admin';
  expiry_date?: string; // ISO 8601
}

const assignUserToProject = async (
  projectId: string,
  data: UserAssignmentCreate
): Promise<UserAssignmentResponse> => {
  const response = await api.post(
    `/api/v1/admin/projects/${projectId}/users`,
    data
  );
  return response.data;
};

// GET /api/v1/admin/projects/{project_id}/users
// Description: Get all users assigned to project
// Authentication: Required (Admin role)

const listProjectUsers = async (
  projectId: string
): Promise<UserAssignmentResponse[]> => {
  const response = await api.get(`/api/v1/admin/projects/${projectId}/users`);
  return response.data;
};

// GET /api/v1/admin/projects/search?q=yield
// Description: Search projects by name, description, or slug
// Authentication: Required (Admin role)

const searchProjects = async (query: string): Promise<ProjectResponse[]> => {
  const response = await api.get('/api/v1/admin/projects/search', {
    params: { q: query }
  });
  return response.data;
};

export function useAdminProjects(filters?: ProjectFilters) {
  const queryClient = useQueryClient();
  
  const { data: projects, isLoading } = useQuery({
    queryKey: ['admin-projects', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/projects/', {
        params: filters
      });
      return response.data;
    },
  });
  
  const createProject = useMutation({
    mutationFn: async (data: ProjectCreate) => {
      const response = await api.post('/api/v1/admin/projects/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-projects'] });
      toast.success('Project created successfully');
    },
  });
  
  const updateProject = useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: ProjectUpdate }) => {
      const response = await api.patch(`/api/v1/admin/projects/${id}`, updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-projects'] });
      toast.success('Project updated successfully');
    },
  });
  
  const deleteProject = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/admin/projects/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-projects'] });
      toast.success('Project deleted successfully');
    },
  });
  
  return {
    projects: projects || [],
    isLoading,
    createProject: createProject.mutate,
    updateProject: updateProject.mutate,
    deleteProject: deleteProject.mutate,
  };
}

const colors = {
  primary: '#3B82F6',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#06B6D4',
  background: '#0F172A',
  surface: '#1E293B',
  border: '#334155',
};

const motion = {
  duration: { fast: '0.15s', normal: '0.3s', slow: '0.5s' },
  easing: { smooth: [0.4, 0, 0.2, 1], bounce: [0.68, -0.55, 0.265, 1.55] },
};

// GET /admin/blockchain/transactions
interface GetTransactionsResponse {
  success: true;
  data: {
    transactions: BlockchainTransaction[];
    stats: {
      total_24h: number;
      volume_24h_usd: number;
      success_rate: number;
      avg_gas_usd: number;
    };
    pagination: Pagination;
  };
}

interface BlockchainTransaction {
  id: string;
  tx_hash: string;
  type: 'swap' | 'supply' | 'borrow' | 'repay' | 'withdraw' | 'bridge' | 'stake' | 'unstake';
  chain: string;
  protocol: string;
  user_id: string;
  wallet_address: string;
  status: 'pending' | 'success' | 'failed';
  amount_usd: number;
  input: { token: string; amount: string; value_usd: number };
  output?: { token: string; amount: string; value_usd: number };
  gas_used?: number;
  gas_price_gwei?: number;
  gas_cost_usd?: number;
  block_number?: number;
  timestamp: string;
  error_message?: string;
}

// GET /admin/blockchain/wallets/dashboard
interface GetWalletDashboardResponse {
  success: true;
  data: {
    summary: {
      total_wallets: number;
      total_value_usd: number;
      healthy_percentage: number;
      low_gas_count: number;
    };
    mpc_status: {
      status: 'operational' | 'degraded' | 'down';
      last_health_check: string;
      key_shards_available: number;
      key_shards_total: number;
      recovery_status: 'valid' | 'invalid';
    };
    chain_distribution: Record<string, { value_usd: number; percentage: number }>;
    low_gas_wallets: LowGasWallet[];
    recent_activity: {
      today: { created: number; funded: number; issues: number };
      yesterday: { created: number; funded: number; issues: number };
      week: { created: number; funded: number; issues: number };
    };
  };
}

interface LowGasWallet {
  address: string;
  chain: string;
  gas_balance_usd: number;
  threshold_usd: number;
  user_id: string;
  last_transaction?: string;
}

// POST /admin/blockchain/wallets/fund
interface FundWalletsRequest {
  wallet_addresses?: string[];
  fund_all_low_gas?: boolean;
  amount_usd?: number;
}

// GET /admin/blockchain/gas
interface GetGasManagementResponse {
  success: true;
  data: {
    spending_30d: {
      total_usd: number;
      avg_per_tx_usd: number;
      saved_usd: number;
      change_percent: number;
    };
    current_prices: ChainGasPrice[];
    spending_by_chain: Record<string, { amount_usd: number; percentage: number }>;
    strategies: GasStrategy[];
    price_history_24h: Array<{
      chain: string;
      timeseries: TimeSeriesPoint[];
    }>;
  };
}

interface ChainGasPrice {
  chain: string;
  slow: { gwei: number; usd: number };
  standard: { gwei: number; usd: number };
  fast: { gwei: number; usd: number };
  instant: { gwei: number; usd: number };
  trend: 'up' | 'down' | 'stable';
}

interface GasStrategy {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'disabled';
  estimated_savings_percent: number;
}

// GET /admin/blockchain/chains
interface GetChainsStatusResponse {
  success: true;
  data: {
    summary: {
      operational: number;
      total: number;
      avg_latency_ms: number;
      uptime_24h: number;
    };
    chains: ChainStatus[];
  };
}

interface ChainStatus {
  chain_id: number;
  name: string;
  status: 'online' | 'degraded' | 'offline';
  block_height: number;
  last_block_time: string;
  gas_price_gwei: number;
  gas_price_usd: number;
  congestion: 'low' | 'normal' | 'moderate' | 'high' | 'critical';
  endpoints: RPCEndpoint[];
}

interface RPCEndpoint {
  name: string;
  url: string;
  role: 'primary' | 'failover' | 'backup';
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  uptime_percent: number;
  last_check: string;
}

// GET /admin/blockchain/protocols
interface GetProtocolsResponse {
  success: true;
  data: {
    summary: {
      operational: number;
      total: number;
      volume_24h_usd: number;
      avg_latency_ms: number;
    };
    protocols: Protocol[];
  };
}

interface Protocol {
  id: string;
  name: string;
  type: 'dex' | 'lending' | 'bridge' | 'staking' | 'compliance';
  status: 'operational' | 'degraded' | 'down';
  volume_24h_usd: number;
  transaction_count_24h: number;
  avg_latency_ms: number;
  supported_chains: Array<{
    chain: string;
    status: 'active' | 'pending' | 'disabled';
  }>;
  metrics: Record<string, any>;
  api_quota?: {
    used: number;
    limit: number;
  };
  last_sync?: string;
}

// POST /admin/blockchain/protocols/{id}/test
interface TestProtocolResponse {
  success: boolean;
  latency_ms: number;
  error?: string;
}

// GET /admin/distillation/telemetry/overview?period=24h
// Get distillation metrics overview

interface GetDistillationOverviewResponse {
  success: true;
  data: {
    period: string;
    total_requests: number;
    
    route_breakdown: {
      reject: number;
      cache: number;
      static: number;
      light_llm: number;
      full_llm: number;
    };
    
    route_percentages: {
      reject: number;
      cache: number;
      static: number;
      light_llm: number;
      full_llm: number;
    };
    
    cache_metrics: {
      exact_hit_rate: number;
      semantic_hit_rate: number;
      combined_hit_rate: number;
      total_entries: number;
      size_mb: number;
      avg_entry_age_hours: number;
    };
    
    classification_metrics: {
      avg_latency_ms: number;
      p50_latency_ms: number;
      p95_latency_ms: number;
      p99_latency_ms: number;
      avg_confidence: number;
      low_confidence_count: number;
    };
    
    cost_savings: {
      estimated_saved_usd: number;
      requests_avoided: number;
      savings_by_route: Record<string, number>;
      projected_monthly_usd: number;
    };
    
    comparison: {
      requests_change_pct: number;
      cache_hit_change_pct: number;
      savings_change_pct: number;
    };
  };
}

// GET /admin/distillation/telemetry/intents?period=24h
// Get intent classification distribution

interface GetIntentDistributionResponse {
  success: true;
  data: {
    period: string;
    intents: Array<{
      intent: string;
      count: number;
      percentage: number;
      avg_confidence: number;
      route_distribution: Record<string, number>;
    }>;
    confidence_distribution: {
      high: number;      // >90%
      medium: number;    // 70-90%
      low: number;       // <70%
    };
    avg_confidence: number;
    low_confidence_samples: Array<{
      query: string;
      intent: string;
      confidence: number;
      possible_alternatives: string[];
    }>;
  };
}

// GET /admin/distillation/cache/stats
// Get detailed cache statistics

interface GetCacheStatsResponse {
  success: true;
  data: {
    exact_cache: {
      total_entries: number;
      size_mb: number;
      hit_rate_24h: number;
      avg_ttl_seconds: number;
      top_keys: Array<{
        key: string;
        query_preview: string;
        hit_count: number;
        created_at: string;
      }>;
    };
    semantic_cache: {
      total_entries: number;
      size_mb: number;
      hit_rate_24h: number;
      avg_similarity: number;
    };
    combined_hit_rate: number;
    estimated_cost_saved_24h_usd: number;
  };
}

// POST /admin/distillation/test
// Test distillation on a query

interface TestDistillationRequest {
  query: string;
  include_cache_check?: boolean;
  include_static_check?: boolean;
}

interface TestDistillationResponse {
  success: true;
  data: {
    query: string;
    normalized_query: string;
    
    classification: {
      intent: string;
      confidence: number;
      complexity: string;
      latency_ms: number;
    };
    
    entities: {
      tokens: string[];
      protocols: string[];
      chains: string[];
      amounts: string[];
    };
    
    routing_decision: {
      route_type: string;
      reason: string;
      suggested_model_tier: string | null;
    };
    
    cache_check?: {
      exact_hit: boolean;
      semantic_hit: boolean;
      semantic_best_match?: {
        query: string;
        similarity: number;
      };
    };
    
    static_check?: {
      available: boolean;
      template?: string;
      data_source?: string;
    };
    
    expected_response_time_ms: number;
    expected_cost_usd: number;
  };
}

// POST /admin/distillation/cache/invalidate
// Invalidate cache entries

interface InvalidateCacheRequest {
  cache_type: 'exact' | 'semantic' | 'all';
  filter?: {
    intent?: string;
    older_than_hours?: number;
  };
}

interface InvalidateCacheResponse {
  success: true;
  data: {
    invalidated_count: number;
    cache_type: string;
  };
}

interface DistillationDashboardState {
  // Overview Data
  overview: DistillationOverview | null;
  intentDistribution: IntentDistribution | null;
  cacheStats: CacheStats | null;
  staticResponseUsage: StaticResponseUsage[];
  
  // UI State
  loading: {
    overview: boolean;
    intents: boolean;
    cache: boolean;
    static: boolean;
    test: boolean;
  };
  
  errors: {
    overview: Error | null;
    intents: Error | null;
    cache: Error | null;
  };
  
  // Filters
  period: '1h' | '24h' | '7d' | '30d';
  
  // Drill-down
  selectedIntent: string | null;
  intentDetails: IntentDetails | null;
  
  // Test Tool
  testToolOpen: boolean;
  testQuery: string;
  testResult: TestDistillationResponse['data'] | null;
  
  // Cache Actions
  clearingCache: boolean;
  
  // Real-time
  wsConnected: boolean;
  lastUpdate: string | null;
}

interface RouteBreakdownChartProps {
  data: {
    reject: number;
    cache: number;
    static: number;
    light_llm: number;
    full_llm: number;
  };
  onSegmentClick?: (routeType: string) => void;
  showLegend?: boolean;
  animated?: boolean;
}

interface CachePerformanceCardProps {
  stats: CacheStats;
  onClearCache: () => void;
  onConfigure: () => void;
  loading?: boolean;
}

interface CostSavingsCardProps {
  savings: {
    total_usd: number;
    requests_avoided: number;
    by_route: Record<string, number>;
    projected_monthly: number;
  };
  comparison: {
    change_pct: number;
  };
}

interface IntentDistributionChartProps {
  intents: Array<{
    intent: string;
    count: number;
    percentage: number;
  }>;
  onIntentClick: (intent: string) => void;
  maxItems?: number;
}

interface LatencyDistributionChartProps {
  data: TimeSeriesPoint[];
  percentiles: {
    p50: number;
    p95: number;
    p99: number;
  };
  target_ms: number;
}

interface TestQueryPanelProps {
  open: boolean;
  onClose: () => void;
  onTest: (query: string) => void;
  result: TestDistillationResponse['data'] | null;
  loading?: boolean;
}

const distillationAnimations = {
  // Donut chart segments
  chartSegmentEnter: {
    initial: { pathLength: 0 },
    animate: { pathLength: 1 },
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  // Metric counter
  metricCount: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 }
  },
  
  // Cache hit pulse
  cacheHitPulse: {
    scale: [1, 1.1, 1],
    backgroundColor: ['transparent', 'rgba(16, 185, 129, 0.2)', 'transparent'],
    transition: { duration: 0.3 }
  },
  
  // Cost savings counter
  savingsCounter: {
    scale: [1, 1.05, 1],
    color: ['#10B981', '#34D399', '#10B981'],
    transition: { duration: 2, repeat: Infinity }
  },
  
  // Intent bar grow
  intentBarGrow: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  // Test result appear
  testResultAppear: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  },
  
  // Cache clear progress
  cacheClearProgress: {
    width: ['0%', '100%'],
    transition: { duration: 2 }
  }
};

const distillationShortcuts = {
  't': 'Open test query tool',
  'mod+r': 'Refresh data',
  '1': 'Switch to 1h view',
  '2': 'Switch to 24h view',
  '3': 'Switch to 7d view',
  '4': 'Switch to 30d view',
  'c': 'Go to cache management',
  's': 'Go to static responses',
  'escape': 'Close panels',
};

const distillationErrorCodes = {
  // Data Errors
  DISTILL_DATA_001: 'Failed to load distillation overview',
  DISTILL_DATA_002: 'Failed to load intent distribution',
  DISTILL_DATA_003: 'Failed to load cache statistics',
  
  // Cache Errors
  DISTILL_CACHE_001: 'Failed to clear cache',
  DISTILL_CACHE_002: 'Cache operation timed out',
  
  // Test Errors
  DISTILL_TEST_001: 'Failed to analyze query',
  DISTILL_TEST_002: 'Query analysis timed out',
  
  // Config Errors
  DISTILL_CFG_001: 'Failed to update configuration',
};

// GET /admin/distillation/config
// Get current configuration

interface GetDistillationConfigResponse {
  success: true;
  data: {
    thresholds: {
      reject_confidence: number;
      cache_confidence: number;
      static_confidence: number;
      light_llm_confidence: number;
    };
    complexity: {
      light_llm_max_score: number;
      multi_turn_threshold: number;
      context_length_threshold: number;
    };
    rejection: {
      enabled: boolean;
      blocked_keywords: string[];
      blocked_intents: string[];
      custom_message: string;
    };
    classification: {
      model: string;
      max_latency_ms: number;
      fallback_route: string;
    };
    rules: RoutingRule[];
  };
}

interface RoutingRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  conditions: RuleCondition[];
  action: {
    route: 'reject' | 'cache' | 'static' | 'light_llm' | 'full_llm';
    static_template_id?: string;
    rejection_message?: string;
  };
  is_enabled: boolean;
  stats: {
    matches_24h: number;
    last_matched?: string;
  };
}

interface RuleCondition {
  field: 'intent' | 'confidence' | 'complexity' | 'entities' | 'keywords' | 'context_length';
  operator: 'equals' | 'not_equals' | 'contains' | 'gt' | 'gte' | 'lt' | 'lte' | 'in';
  value: any;
}

// PUT /admin/distillation/config/thresholds
// Update confidence thresholds

interface UpdateThresholdsRequest {
  reject_confidence?: number;
  cache_confidence?: number;
  static_confidence?: number;
  light_llm_confidence?: number;
}

// POST /admin/distillation/config/rules
// Create new routing rule

interface CreateRoutingRuleRequest {
  name: string;
  description?: string;
  conditions: RuleCondition[];
  action: {
    route: string;
    static_template_id?: string;
    rejection_message?: string;
  };
}

// POST /admin/distillation/test
// Test routing decision for query

interface TestRoutingRequest {
  query: string;
  context?: {
    user_id?: string;
    project_id?: string;
    is_first_message?: boolean;
  };
}

interface TestRoutingResponse {
  success: true;
  data: {
    query: string;
    classification: {
      intent: string;
      confidence: number;
      complexity_score: number;
      entities: string[];
    };
    matched_rule?: {
      id: string;
      name: string;
    };
    final_route: string;
    route_reason: string;
    latency_ms: number;
  };
}

interface DistillationConfigState {
  config: DistillationConfig | null;
  rules: RoutingRule[];
  
  loading: {
    config: boolean;
    rules: boolean;
    save: boolean;
    test: boolean;
  };
  
  activeTab: 'thresholds' | 'rules' | 'rejection' | 'complexity' | 'advanced';
  
  ruleEditorOpen: boolean;
  editingRule: RoutingRule | null;
  
  testQuery: string;
  testResult: TestRoutingResponse['data'] | null;
  
  unsavedChanges: boolean;
}

interface ThresholdSliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  trafficPercentage?: number;
  description?: string;
}

interface RuleBuilderProps {
  rule?: RoutingRule;
  onSave: (rule: RoutingRule) => void;
  onCancel: () => void;
  onTest: (query: string) => void;
  testResult?: TestRoutingResponse['data'];
  loading?: boolean;
}

interface RoutingTestPanelProps {
  onTest: (query: string, context?: any) => void;
  result?: TestRoutingResponse['data'];
  loading?: boolean;
}

const distillationConfigAnimations = {
  sliderThumb: {
    scale: 1.2,
    transition: { duration: 0.15 }
  },
  
  ruleReorder: {
    y: 0,
    transition: { type: 'spring', stiffness: 300 }
  },
  
  testResultAppear: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.3 }
  },
  
  routeHighlight: {
    backgroundColor: ['transparent', 'rgba(59, 130, 246, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  }
};

const distillationConfigShortcuts = {
  'mod+s': 'Save changes',
  'mod+n': 'Add new rule',
  'mod+t': 'Open test panel',
  'escape': 'Cancel editing',
};

const distillationConfigErrorCodes = {
  DIST_CFG_001: 'Invalid threshold value',
  DIST_CFG_002: 'Rule conditions invalid',
  DIST_CFG_003: 'Static template required for STATIC route',
  DIST_CFG_004: 'Failed to save configuration',
  DIST_CFG_005: 'Test query failed',
};

// GET /admin/distillation/telemetry?period=24h
interface GetDistillationTelemetryResponse {
  success: true;
  data: {
    summary: {
      total_classified: number;
      avg_latency_ms: number;
      avg_confidence: number;
      total_savings_usd: number;
    };
    routing_distribution: Record<string, {
      count: number;
      percentage: number;
    }>;
    intent_distribution: Record<string, number>;
    latency: {
      timeseries: TimeSeriesPoint[];
      percentiles: { p50: number; p95: number; p99: number };
    };
    savings_breakdown: Array<{
      route: string;
      requests: number;
      avoided_cost_usd: number;
      savings_percentage: number;
    }>;
    low_confidence_samples: Array<{
      query: string;
      intent: string;
      confidence: number;
      routed_to: string;
    }>;
  };
}

const distillationTelemetryAnimations = {
  sankeyFlow: {
    pathLength: [0, 1],
    transition: { duration: 1.5, ease: 'easeOut' }
  },
  
  savingsCounter: {
    opacity: [0, 1],
    y: [20, 0],
    transition: { duration: 0.5 }
  }
};

// GET /admin/distillation/cache/stats
interface GetCacheStatsResponse {
  success: true;
  data: {
    total_entries: number;
    exact_entries: number;
    semantic_entries: number;
    size_bytes: number;
    max_size_bytes: number;
    hit_rate_exact: number;
    hit_rate_semantic: number;
    hit_rate_combined: number;
    avg_lookup_ms: number;
    oldest_entry_age_hours: number;
  };
}

// GET /admin/distillation/cache/entries
interface GetCacheEntriesResponse {
  success: true;
  data: {
    entries: CacheEntry[];
    pagination: Pagination;
  };
}

interface CacheEntry {
  id: string;
  query: string;
  cache_type: 'exact' | 'semantic';
  response_preview: string;
  hits: number;
  created_at: string;
  expires_at: string;
  size_bytes: number;
  intent?: string;
  linked_entries?: string[];
}

// DELETE /admin/distillation/cache/entries
interface InvalidateCacheRequest {
  entry_ids?: string[];
  query_pattern?: string;
  intent?: string;
  older_than_hours?: number;
  all?: boolean;
}

// PUT /admin/distillation/cache/config
interface UpdateCacheConfigRequest {
  max_size_mb?: number;
  max_entries?: number;
  eviction_policy?: 'lru' | 'lfu';
  semantic_threshold?: number;
  ttl_by_intent?: Record<string, number>;
}

const cacheAnimations = {
  entrySelect: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    transition: { duration: 0.15 }
  },
  
  invalidateProgress: {
    width: '100%',
    transition: { duration: 0.5 }
  },
  
  hitCountIncrement: {
    scale: [1, 1.1, 1],
    color: ['#fff', '#10B981', '#fff'],
    transition: { duration: 0.3 }
  }
};

// GET /admin/distillation/static-responses
// Get all static response templates

interface GetStaticResponsesResponse {
  success: true;
  data: {
    templates: StaticResponse[];
    categories: Array<{
      name: string;
      count: number;
    }>;
    summary: {
      total: number;
      active: number;
      hits_24h: number;
      cost_saved_24h: number;
    };
  };
}

interface StaticResponse {
  id: string;
  name: string;
  category: string;
  intent: string;
  min_confidence: number;
  template_content: string;
  variables: string[];
  data_source: 'static' | 'api' | 'user_context' | 'blockchain';
  data_config?: {
    api_endpoint?: string;
    cache_ttl_seconds?: number;
  };
  conditions?: ResponseCondition[];
  variants?: ResponseVariant[];
  is_active: boolean;
  stats: {
    hits_24h: number;
    hits_total: number;
    avg_confidence: number;
    follow_up_rate: number;
    cost_saved_24h: number;
  };
  created_at: string;
  updated_at: string;
}

interface ResponseCondition {
  type: 'time' | 'user' | 'context';
  operator: 'equals' | 'contains' | 'between' | 'in';
  field: string;
  value: any;
}

interface ResponseVariant {
  id: string;
  name: string;
  content: string;
  traffic_percentage: number;
  is_active: boolean;
  stats: {
    hits: number;
    follow_up_rate: number;
  };
}

// POST /admin/distillation/static-responses
// Create new static response

interface CreateStaticResponseRequest {
  name: string;
  category: string;
  intent: string;
  min_confidence: number;
  template_content: string;
  data_source: 'static' | 'api' | 'user_context' | 'blockchain';
  data_config?: {
    api_endpoint?: string;
    cache_ttl_seconds?: number;
  };
  conditions?: ResponseCondition[];
  is_active?: boolean;
}

// Validation
const createStaticResponseValidation = {
  name: { required: true, minLength: 2, maxLength: 100 },
  intent: { required: true, enum: VALID_INTENTS },
  min_confidence: { required: true, min: 0.5, max: 1.0 },
  template_content: { required: true, minLength: 10, maxLength: 5000 },
  'data_config.cache_ttl_seconds': { min: 10, max: 86400 }
};

// POST /admin/distillation/static-responses/test
// Test template matching

interface TestTemplateMatchRequest {
  query: string;
}

interface TestTemplateMatchResponse {
  success: true;
  data: {
    query: string;
    matched: boolean;
    template?: {
      id: string;
      name: string;
      intent: string;
    };
    confidence: number;
    threshold: number;
    match_reason?: string;
    variables_extracted?: Record<string, any>;
    rendered_response?: string;
    performance: {
      classification_ms: number;
      data_fetch_ms: number;
      render_ms: number;
      total_ms: number;
    };
    estimated_cost_saved: number;
  };
}

interface StaticResponsesState {
  // Data
  templates: StaticResponse[];
  categories: string[];
  summary: ResponsesSummary;
  selectedTemplate: StaticResponse | null;
  
  // UI State
  loading: {
    list: boolean;
    template: boolean;
    test: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    save: Error | null;
    test: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    category: string | null;
    status: 'all' | 'active' | 'draft' | 'disabled';
  };
  
  // Editor
  editorOpen: boolean;
  editorMode: 'create' | 'edit';
  editorForm: Partial<CreateStaticResponseRequest>;
  previewData: RenderedPreview | null;
  
  // Testing
  testPanelOpen: boolean;
  testQuery: string;
  testResult: TestTemplateMatchResponse['data'] | null;
  testHistory: TestResult[];
  
  // Variants
  variantsOpen: boolean;
  variants: ResponseVariant[];
  
  // Expanded Categories
  expandedCategories: string[];
}

interface TemplateCardProps {
  template: StaticResponse;
  onEdit: (id: string) => void;
  onPreview: (id: string) => void;
  onToggleActive: (id: string, active: boolean) => void;
  onViewVariants: (id: string) => void;
  expanded?: boolean;
}

interface TemplateEditorProps {
  template?: StaticResponse;
  mode: 'create' | 'edit';
  onSave: (data: CreateStaticResponseRequest) => void;
  onCancel: () => void;
  onPreview: (content: string) => void;
  previewData?: RenderedPreview;
  loading?: boolean;
}

interface VariableInserterProps {
  availableVariables: Array<{
    name: string;
    description: string;
    source: string;
    example: any;
  }>;
  onInsert: (variable: string) => void;
}

interface TemplateTestPanelProps {
  open: boolean;
  onClose: () => void;
  onTest: (query: string) => void;
  result: TestTemplateMatchResponse['data'] | null;
  history: TestResult[];
  loading?: boolean;
}

const staticResponseAnimations = {
  // Category expand
  categoryExpand: {
    initial: { height: 0 },
    animate: { height: 'auto' },
    transition: { duration: 0.3 }
  },
  
  // Template card hover
  templateHover: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    transition: { duration: 0.15 }
  },
  
  // Variable chip insert
  variableInsert: {
    initial: { scale: 0, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: { type: 'spring', stiffness: 400 }
  },
  
  // Preview render
  previewRender: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 }
  },
  
  // Test result
  testResult: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  },
  
  // Match success pulse
  matchSuccess: {
    backgroundColor: ['transparent', 'rgba(16, 185, 129, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  },
  
  // Stats counter
  statsCount: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.5 }
  }
};

const staticResponseShortcuts = {
  'mod+n': 'Create new template',
  'mod+e': 'Edit selected template',
  'mod+t': 'Open test panel',
  'mod+p': 'Preview template',
  'mod+s': 'Save template',
  'escape': 'Close editor/panel',
  '{': 'Insert variable',
};

const staticResponseErrorCodes = {
  // Validation
  STATIC_VAL_001: 'Template name is required',
  STATIC_VAL_002: 'Template content is required',
  STATIC_VAL_003: 'Invalid intent mapping',
  STATIC_VAL_004: 'Confidence threshold out of range',
  
  // Variables
  STATIC_VAR_001: 'Unknown variable in template',
  STATIC_VAR_002: 'Variable data source not available',
  STATIC_VAR_003: 'Failed to fetch variable data',
  
  // Testing
  STATIC_TEST_001: 'Template matching failed',
  STATIC_TEST_002: 'Preview render failed',
  
  // System
  STATIC_SYS_001: 'Failed to load templates',
  STATIC_SYS_002: 'Failed to save template',
};

// GET /api/v1/admin/cache/stats
interface CacheStatsResponse {
  global: {
    total_keys: number;
    memory_used_bytes: number;
    memory_limit_bytes: number;
    hit_rate: number;
    miss_rate: number;
    evictions_24h: number;
    avg_response_time_ms: number;
  };
  layers: Array<{
    layer_name: string;
    key_count: number;
    memory_bytes: number;
    hit_rate: number;
    default_ttl_seconds: number;
    top_patterns: string[];
  }>;
}

// DELETE /api/v1/admin/cache/layer/:layer_name
interface InvalidateCacheRequest {
  pattern?: string;  // Optional: invalidate only matching keys
  confirm: boolean;  // Required: must be true
}

interface InvalidateCacheResponse {
  success: boolean;
  keys_deleted: number;
  memory_freed_bytes: number;
}

// POST /api/v1/admin/cache/warm
interface WarmCacheRequest {
  layer: string;
  queries?: string[];  // Specific queries to warm
  top_n?: number;      // Or warm top N popular queries
}

interface WarmCacheResponse {
  success: boolean;
  queries_warmed: number;
  estimated_time_seconds: number;
}

// GET /api/v1/admin/cache/layer/:layer_name/top-queries?limit=100
interface TopQueriesResponse {
  queries: Array<{
    pattern: string;
    hit_count: number;
    hit_rate: number;
    memory_bytes: number;
    avg_response_time_ms: number;
  }>;
  total_queries: number;
}

interface CacheDashboardProps {
  refreshInterval?: number;
}

interface CacheLayerCardProps {
  layer: CacheLayer;
  onViewDetails: () => void;
  onInvalidate: () => void;
  onWarmCache: () => void;
}

interface CacheStatsChartProps {
  stats: CacheStats[];
  metric: 'hit_rate' | 'memory' | 'keys';
  timeRange: '1h' | '24h' | '7d';
}

interface KeyBrowserProps {
  pattern: string;
  onPatternChange: (pattern: string) => void;
  onDeleteKey: (key: string) => void;
}

const cacheErrors = {
  CACHE_001: 'Failed to fetch cache statistics',
  CACHE_002: 'Invalidation requires confirmation',
  CACHE_003: 'Cache warming already in progress',
  CACHE_004: 'Invalid cache layer name',
  CACHE_005: 'Pattern too broad (would delete >10k keys)',
};

// GET /api/v1/admin/data-sources
interface DataSourcesResponse {
  sources: Array<{
    id: string;
    name: string;
    type: 'api' | 'rpc' | 'subgraph' | 'oracle';
    status: 'active' | 'inactive' | 'error' | 'rate_limited';
    health_score: number; // 0-100
    uptime_percentage: number;
    last_sync: string;
    next_sync: string;
    requests_today: number;
    rate_limit: number;
    cost_monthly: number;
  }>;
  total_sources: number;
  healthy_sources: number;
}

// PUT /api/v1/admin/data-sources/:id
interface ConfigureDataSourceRequest {
  api_key?: string;
  sync_interval_minutes?: number;
  enabled?: boolean;
  rate_limit?: number;
  failover_source_id?: string;
}

interface ConfigureDataSourceResponse {
  success: boolean;
  source: DataSource;
}

// POST /api/v1/admin/data-sources/:id/sync
interface ManualSyncResponse {
  job_id: string;
  status: 'queued' | 'running';
  estimated_duration_seconds: number;
}

// GET /api/v1/admin/data-sources/:id/logs?limit=50
interface SyncLogsResponse {
  logs: Array<{
    id: string;
    source_id: string;
    started_at: string;
    completed_at?: string;
    status: 'success' | 'failed' | 'running';
    duration_seconds?: number;
    records_synced?: number;
    error?: string;
  }>;
  total_logs: number;
}

interface DataSourcesDashboardProps {
  refreshInterval?: number;
}

interface DataSourceCardProps {
  source: DataSource;
  onConfigure: () => void;
  onTest: () => void;
  onViewLogs: () => void;
}

interface SyncStatusIndicatorProps {
  lastSync: Date;
  nextSync: Date;
  isRunning: boolean;
}

interface RateLimitGaugeProps {
  current: number;
  limit: number;
  resetTime: Date;
}

// POST /api/v1/admin/ml/network/pagerank
interface PageRankRequest {
  damping_factor?: number; // Default: 0.85
  max_iterations?: number; // Default: 100
}

interface PageRankResponse {
  protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    pagerank_score: number;
    rank: number;
  }>;
  top_10: string[];
  algorithm_params: {
    damping_factor: number;
    iterations: number;
    convergence_threshold: number;
  };
}

// POST /api/v1/admin/ml/network/communities
interface CommunityDetectionRequest {
  algorithm: 'label_propagation' | 'louvain';
}

interface CommunityDetectionResponse {
  communities: Array<{
    community_id: number;
    protocols: Array<{
      protocol_id: string;
      protocol_name: string;
    }>;
    total_protocols: number;
    total_tvl: number;
    average_risk: number;
    interconnections: number;
    label: string;
  }>;
  algorithm: string;
  modularity_score: number;
  total_communities: number;
}

// POST /api/v1/admin/ml/network/contagion/:protocol_id
interface ContagionSimulationRequest {
  failure_probability: number; // 0-1
  transmission_rate: number; // 0-1
  max_hops: number; // 1-10
}

interface ContagionSimulationResponse {
  origin_protocol_id: string;
  cascade_waves: Array<{
    wave_number: number;
    affected_protocols: string[];
    tvl_at_risk: number;
    cascade_probability: number;
  }>;
  total_protocols_affected: number;
  total_tvl_at_risk: number;
  cascade_probability: number;
  max_depth_reached: number;
}

// GET /admin/projects/{id}/rules
interface GetProjectRulesResponse {
  success: true;
  data: {
    rules: AssignmentRule[];
    summary: {
      total_rules: number;
      active_rules: number;
      assignments_24h: number;
      match_rate: number;
    };
  };
}

interface AssignmentRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  conditions: RuleCondition[];
  condition_logic: 'any' | 'all';
  is_enabled: boolean;
  stats: {
    matches_24h: number;
    matches_7d: number;
    last_matched?: string;
  };
  created_at: string;
  updated_at: string;
}

interface RuleCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in';
  value: any;
}

// POST /admin/projects/{id}/rules
interface CreateRuleRequest {
  name: string;
  description?: string;
  conditions: RuleCondition[];
  condition_logic?: 'any' | 'all';
  is_enabled?: boolean;
}

// PUT /admin/projects/{id}/rules/reorder
interface ReorderRulesRequest {
  rule_ids: string[];  // In priority order
}

// POST /admin/projects/{id}/rules/test
interface TestRulesRequest {
  query: string;
  user_context?: {
    user_id?: string;
    wallet_address?: string;
  };
}

interface TestRulesResponse {
  success: true;
  data: {
    query: string;
    classification: {
      intent: string;
      confidence: number;
      entities: string[];
    };
    evaluations: Array<{
      rule_id: string;
      rule_name: string;
      matched: boolean;
      reason: string;
    }>;
    result: {
      assigned: boolean;
      matched_rule_id?: string;
      matched_rule_name?: string;
      evaluation_time_ms: number;
    };
  };
}

const rulesAnimations = {
  ruleDrag: {
    scale: 1.02,
    boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
    transition: { duration: 0.15 }
  },
  
  ruleReorder: {
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 25 }
  },
  
  matchHighlight: {
    backgroundColor: ['transparent', 'rgba(16, 185, 129, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  },
  
  conditionAdd: {
    opacity: [0, 1],
    height: ['0px', 'auto'],
    transition: { duration: 0.2 }
  }
};

// GET /admin/projects
// Get all projects with optional filters

interface GetProjectsRequest {
  status?: 'draft' | 'active' | 'paused' | 'archived';
  visibility?: 'public' | 'private' | 'invite_only';
  is_featured?: boolean;
  search?: string;
  sort_by?: 'name' | 'created_at' | 'users' | 'engagement';
  sort_order?: 'asc' | 'desc';
  include_stats?: boolean;
}

interface GetProjectsResponse {
  success: true;
  data: {
    projects: ProjectSummary[];
    summary: {
      total: number;
      active: number;
      draft: number;
      paused: number;
      archived: number;
      total_users: number;
      active_users_7d: number;
      total_sessions_7d: number;
      avg_satisfaction: number;
    };
  };
}

interface ProjectSummary {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  status: 'draft' | 'active' | 'paused' | 'archived';
  visibility: 'public' | 'private' | 'invite_only';
  is_featured: boolean;
  display_order: number;
  stats?: {
    total_users: number;
    active_users_7d: number;
    total_sessions: number;
    sessions_7d: number;
    avg_satisfaction: number;
    engagement_trend: number;    // % change vs previous period
  };
  created_at: string;
  updated_at: string;
}

// POST /admin/projects
// Create new project

interface CreateProjectRequest {
  slug: string;
  name: string;
  description: string;
  icon?: string;
  color?: string;
  visibility?: 'public' | 'private' | 'invite_only';
  system_prompt: string;
  welcome_message?: string;
  enabled_protocols?: string[];
  enabled_chains?: string[];
  enabled_tools?: string[];
  risk_config?: RiskConfig;
  status?: 'draft' | 'active';
}

interface RiskConfig {
  max_slippage_bps?: number;
  max_position_usd?: number;
  max_leverage?: number;
  max_daily_volume_usd?: number;
  require_2fa_for_transactions?: boolean;
  require_simulation?: boolean;
  allowed_tokens?: string[];
  blocked_tokens?: string[];
  min_health_factor?: number;
  conservative_mode?: boolean;
}

// Validation
const createProjectValidation = {
  slug: {
    required: true,
    pattern: /^[a-z0-9-]+$/,
    minLength: 2,
    maxLength: 50,
    unique: true
  },
  name: {
    required: true,
    minLength: 2,
    maxLength: 100
  },
  description: {
    required: true,
    minLength: 10,
    maxLength: 200
  },
  system_prompt: {
    required: true,
    minLength: 50,
    maxLength: 10000
  },
  'risk_config.max_slippage_bps': {
    min: 1,
    max: 500
  },
  'risk_config.max_position_usd': {
    min: 100,
    max: 1000000
  },
  'risk_config.max_leverage': {
    min: 1,
    max: 100
  }
};

interface CreateProjectResponse {
  success: true;
  data: {
    project_id: string;
    slug: string;
    knowledge_base_id: string;
    status: string;
  };
}

// PATCH /admin/projects/{id}/status
// Update project status

interface UpdateProjectStatusRequest {
  status: 'draft' | 'active' | 'paused' | 'archived';
  reason?: string;
}

interface UpdateProjectStatusResponse {
  success: true;
  data: {
    project_id: string;
    previous_status: string;
    new_status: string;
    affected_users: number;
    updated_at: string;
  };
}

// POST /admin/projects/{id}/clone
// Clone existing project

interface CloneProjectRequest {
  new_slug: string;
  new_name: string;
  clone_knowledge_base?: boolean;
}

interface CloneProjectResponse {
  success: true;
  data: {
    original_project_id: string;
    new_project_id: string;
    new_slug: string;
    status: 'draft';
    knowledge_documents_cloned: number;
  };
}

// PUT /admin/projects/featured
// Update featured projects and order

interface UpdateFeaturedRequest {
  featured_project_ids: string[];  // Ordered list
}

interface UpdateFeaturedResponse {
  success: true;
  data: {
    updated: Array<{
      project_id: string;
      is_featured: boolean;
      display_order: number;
    }>;
  };
}

// GET /admin/projects/check-slug?slug=my-project
// Check if slug is available

interface CheckSlugResponse {
  success: true;
  data: {
    slug: string;
    available: boolean;
    suggestion?: string;  // If not available, suggest alternative
  };
}

interface ProjectsListState {
  // Data
  projects: ProjectSummary[];
  summary: ProjectsSummary | null;
  
  // UI State
  loading: {
    list: boolean;
    create: boolean;
    clone: boolean;
    statusUpdate: boolean;
  };
  
  errors: {
    list: Error | null;
    create: Error | null;
    clone: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    status: 'all' | 'draft' | 'active' | 'paused' | 'archived';
    featured: boolean;
  };
  
  // Sorting
  sortBy: 'name' | 'created_at' | 'users' | 'engagement';
  sortOrder: 'asc' | 'desc';
  
  // Selection
  selectedProjects: string[];
  bulkActionInProgress: boolean;
  
  // Wizard
  wizardOpen: boolean;
  wizardStep: number;
  wizardData: Partial<CreateProjectRequest>;
  
  // Clone
  cloneDialogOpen: boolean;
  projectToClone: ProjectSummary | null;
  
  // Featured Reordering
  isReorderingFeatured: boolean;
  pendingFeaturedOrder: string[];
  
  // Actions Menu
  activeActionMenu: string | null;
}

interface ProjectCardProps {
  project: ProjectSummary;
  onEdit: (id: string) => void;
  onClone: (project: ProjectSummary) => void;
  onStatusChange: (id: string, status: string) => void;
  onToggleFeatured: (id: string) => void;
  onViewAnalytics: (id: string) => void;
  onManageUsers: (id: string) => void;
  onDelete: (id: string) => void;
  selected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  draggable?: boolean;
}

// Usage
<ProjectCard
  project={savingsProject}
  onEdit={handleEdit}
  onClone={handleClone}
  onStatusChange={handleStatusChange}
  onToggleFeatured={handleToggleFeatured}
/>

interface ProjectWizardProps {
  open: boolean;
  onClose: () => void;
  onComplete: (project: CreateProjectRequest) => void;
  initialData?: Partial<CreateProjectRequest>;
  editMode?: boolean;
}

// Usage
<ProjectWizard
  open={wizardOpen}
  onClose={() => setWizardOpen(false)}
  onComplete={handleCreateProject}
/>

interface ProjectStatusBadgeProps {
  status: 'draft' | 'active' | 'paused' | 'archived';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

// Usage
<ProjectStatusBadge status="active" size="md" showLabel />

interface ProjectStatsBarProps {
  stats: {
    users: number;
    activeUsers: number;
    satisfaction: number;
    trend: number;
  };
  compact?: boolean;
}

interface CloneProjectDialogProps {
  project: ProjectSummary;
  open: boolean;
  onClose: () => void;
  onClone: (data: CloneProjectRequest) => void;
  loading?: boolean;
}

const projectsAnimations = {
  // Card grid stagger
  gridStagger: {
    container: {
      animate: { transition: { staggerChildren: 0.05 } }
    },
    item: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 }
    }
  },
  
  // Card hover
  cardHover: {
    scale: 1.02,
    boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
    transition: { duration: 0.2 }
  },
  
  // Status change
  statusChange: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.3 }
  },
  
  // Wizard step transition
  wizardStep: {
    initial: { opacity: 0, x: 50 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -50 },
    transition: { duration: 0.3 }
  },
  
  // Featured star
  featuredStar: {
    scale: [1, 1.3, 1],
    rotate: [0, 15, -15, 0],
    transition: { duration: 0.5 }
  },
  
  // Drag reorder
  dragItem: {
    scale: 1.05,
    boxShadow: '0 15px 50px rgba(0,0,0,0.3)',
    zIndex: 1000
  },
  
  // Success creation
  createSuccess: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    transition: { type: 'spring', stiffness: 200 }
  }
};

const projectsShortcuts = {
  'mod+n': 'Create new project',
  'mod+f': 'Focus search',
  '/': 'Focus search (alternative)',
  'mod+a': 'Select all projects',
  'escape': 'Clear selection / Close wizard',
  'enter': 'Edit selected project',
  'del': 'Delete selected projects',
  'f': 'Toggle featured filter',
  's': 'Sort by next column',
};

const projectErrorCodes = {
  // Validation
  PROJ_VAL_001: 'Project name is required',
  PROJ_VAL_002: 'Slug must be URL-friendly (lowercase, numbers, hyphens)',
  PROJ_VAL_003: 'Slug is already taken',
  PROJ_VAL_004: 'System prompt is required for activation',
  PROJ_VAL_005: 'Description must be between 10-200 characters',
  
  // Business Logic
  PROJ_BUS_001: 'Cannot activate project without system prompt',
  PROJ_BUS_002: 'Cannot delete project with active users',
  PROJ_BUS_003: 'Maximum 5 featured projects allowed',
  PROJ_BUS_004: 'Cannot archive project with pending transactions',
  
  // Clone
  PROJ_CLN_001: 'Failed to clone project',
  PROJ_CLN_002: 'Failed to clone knowledge base',
  
  // System
  PROJ_SYS_001: 'Failed to load projects',
  PROJ_SYS_002: 'Failed to create project',
  PROJ_SYS_003: 'Failed to update project status',
};

// GET /admin/projects/{id}/invitations
interface GetInvitationsResponse {
  success: true;
  data: {
    invitations: Invitation[];
    invite_link: InviteLink | null;
    summary: {
      sent: number;
      pending: number;
      accepted: number;
      expired: number;
      conversion_rate: number;
    };
    pagination: Pagination;
  };
}

interface Invitation {
  id: string;
  email: string;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  role: string;
  sent_at: string;
  expires_at: string;
  accepted_at?: string;
  user_id?: string;
  message?: string;
}

interface InviteLink {
  id: string;
  code: string;
  url: string;
  max_uses: number;
  current_uses: number;
  expires_at: string;
  is_active: boolean;
  default_role: string;
  restrictions: {
    email_domain?: string;
    require_wallet?: boolean;
    min_wallet_balance_usd?: number;
  };
}

// POST /admin/projects/{id}/invitations
interface CreateInvitationRequest {
  email: string;
  message?: string;
  role?: string;
  expires_in_days?: number;
}

// POST /admin/projects/{id}/invitations/bulk
interface BulkCreateInvitationsRequest {
  emails: string[];
  message?: string;
  role?: string;
  expires_in_days?: number;
}

interface BulkCreateInvitationsResponse {
  success: true;
  data: {
    created: number;
    skipped: number;
    errors: Array<{ email: string; reason: string }>;
  };
}

// PUT /admin/projects/{id}/invitations/link
interface UpdateInviteLinkRequest {
  max_uses?: number;
  expires_at?: string;
  default_role?: string;
  is_active?: boolean;
  restrictions?: {
    email_domain?: string;
    require_wallet?: boolean;
    min_wallet_balance_usd?: number;
  };
}

// POST /admin/projects/{id}/invitations/link/regenerate
interface RegenerateInviteLinkResponse {
  success: true;
  data: {
    invite_link: InviteLink;
  };
}

// POST /admin/projects/{id}/invitations/{invitation_id}/resend
interface ResendInvitationResponse {
  success: true;
  data: {
    invitation: Invitation;
  };
}

// DELETE /admin/projects/{id}/invitations/{invitation_id}
interface RevokeInvitationResponse {
  success: true;
  data: {
    revoked: true;
  };
}

const invitationsAnimations = {
  statusBadge: {
    scale: [0.8, 1],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  emailSend: {
    x: [0, 50],
    opacity: [1, 0],
    transition: { duration: 0.3 }
  },
  
  linkCopy: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.2 }
  },
  
  rowSelect: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    transition: { duration: 0.15 }
  }
};

const invitationsShortcuts = {
  'mod+n': 'New invitation',
  'mod+l': 'Copy invite link',
  'mod+a': 'Select all',
  'delete': 'Revoke selected',
  'r': 'Resend selected',
};

const invitationsErrorCodes = {
  INV_VAL_001: 'Invalid email format',
  INV_VAL_002: 'Email already invited',
  INV_VAL_003: 'User already has access',
  INV_LIMIT_001: 'Invitation limit reached',
  INV_LINK_001: 'Invite link expired',
  INV_LINK_002: 'Invite link usage exceeded',
  INV_SEND_001: 'Failed to send invitation email',
};

// GET /admin/projects/{id}/knowledge
// Get knowledge base overview

interface GetKnowledgeBaseResponse {
  success: true;
  data: {
    knowledge_base: {
      id: string;
      project_id: string;
      embedding_model: string;
      chunk_size: number;
      chunk_overlap: number;
      total_documents: number;
      total_chunks: number;
      total_size_bytes: number;
      last_indexed_at: string;
      indexing_status: 'idle' | 'indexing' | 'failed';
    };
    documents: KnowledgeDocument[];
  };
}

interface KnowledgeDocument {
  id: string;
  title: string;
  doc_type: 'guide' | 'faq' | 'reference' | 'data' | 'announcement';
  content_preview: string;
  source_url?: string;
  tags: string[];
  priority: number;                // 1-3
  chunk_count: number;
  token_count: number;
  status: 'draft' | 'indexed' | 'needs_reindex' | 'failed';
  is_live_data: boolean;
  created_at: string;
  updated_at: string;
}

// POST /admin/projects/{id}/knowledge/documents
// Add new document

interface AddDocumentRequest {
  title: string;
  doc_type: 'guide' | 'faq' | 'reference' | 'data' | 'announcement';
  content: string;
  source_url?: string;
  tags?: string[];
  priority?: number;
  auto_index?: boolean;
}

// Validation
const addDocumentValidation = {
  title: { required: true, minLength: 2, maxLength: 200 },
  doc_type: { required: true, enum: ['guide', 'faq', 'reference', 'data', 'announcement'] },
  content: { required: true, minLength: 50, maxLength: 500000 },
  priority: { min: 1, max: 3 }
};

interface AddDocumentResponse {
  success: true;
  data: {
    document: KnowledgeDocument;
    indexing_job_id?: string;
    estimated_chunks: number;
    estimated_processing_seconds: number;
  };
}

// PUT /admin/projects/{id}/knowledge/documents/{doc_id}
// Update document

interface UpdateDocumentRequest {
  title?: string;
  doc_type?: string;
  content?: string;
  source_url?: string;
  tags?: string[];
  priority?: number;
}

interface UpdateDocumentResponse {
  success: true;
  data: {
    document: KnowledgeDocument;
    content_changed: boolean;
    needs_reindex: boolean;
    version: number;
  };
}

// POST /admin/projects/{id}/knowledge/search
// Test semantic search

interface TestSearchRequest {
  query: string;
  top_k?: number;                  // default: 5
  similarity_threshold?: number;   // default: 0.7
}

interface TestSearchResponse {
  success: true;
  data: {
    query: string;
    latency_ms: number;
    results: Array<{
      chunk_id: string;
      document_id: string;
      document_title: string;
      content: string;
      similarity_score: number;
      priority: number;
      chunk_index: number;
    }>;
    documents_matched: number;
    total_chunks_searched: number;
  };
}

// POST /admin/projects/{id}/knowledge/reindex
// Trigger reindexing

interface ReindexRequest {
  document_ids?: string[];         // Empty = all documents
  force?: boolean;                 // Reindex even if up-to-date
}

interface ReindexResponse {
  success: true;
  data: {
    job_id: string;
    documents_to_process: number;
    estimated_duration_seconds: number;
    status: 'queued';
  };
}

// GET /admin/projects/{id}/knowledge/documents/{doc_id}/versions
// Get version history

interface GetVersionsResponse {
  success: true;
  data: {
    document_id: string;
    current_version: number;
    versions: Array<{
      version: number;
      content_hash: string;
      changes_summary: string;
      created_by: string;
      created_at: string;
      chunk_count: number;
    }>;
  };
}

interface KnowledgeBaseState {
  // Data
  knowledgeBase: KnowledgeBase | null;
  documents: KnowledgeDocument[];
  selectedDocument: KnowledgeDocument | null;
  
  // UI State
  loading: {
    list: boolean;
    document: boolean;
    search: boolean;
    reindex: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    document: Error | null;
    search: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    type: 'all' | 'guide' | 'faq' | 'reference' | 'data' | 'announcement';
    status: 'all' | 'indexed' | 'draft' | 'needs_reindex';
    tags: string[];
  };
  
  // Sorting
  sortBy: 'updated_at' | 'priority' | 'title' | 'chunks';
  sortOrder: 'asc' | 'desc';
  
  // Selection
  selectedDocIds: string[];
  
  // Document Editor
  editorOpen: boolean;
  editorMode: 'create' | 'edit';
  editorForm: Partial<AddDocumentRequest>;
  chunkPreview: ChunkPreview | null;
  
  // Search Test
  searchTestOpen: boolean;
  searchQuery: string;
  searchResults: TestSearchResponse['data'] | null;
  
  // Versions
  versionsOpen: boolean;
  versions: GetVersionsResponse['data'] | null;
  
  // Reindex
  reindexJobId: string | null;
  reindexProgress: number;
}

interface DocumentListProps {
  documents: KnowledgeDocument[];
  selectedIds: string[];
  onSelect: (id: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onEdit: (doc: KnowledgeDocument) => void;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
  sortBy: string;
  sortOrder: string;
  onSort: (column: string) => void;
  loading?: boolean;
}

interface DocumentEditorProps {
  document?: KnowledgeDocument;
  mode: 'create' | 'edit';
  onSave: (data: AddDocumentRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}

interface ChunkPreviewProps {
  content: string;
  chunkSize: number;
  overlap: number;
  chunks: Array<{
    index: number;
    content: string;
    tokens: number;
  }>;
}

interface SearchTestPanelProps {
  open: boolean;
  onClose: () => void;
  onSearch: (query: string, topK: number, threshold: number) => void;
  results: TestSearchResponse['data'] | null;
  loading?: boolean;
}

interface DocumentVersionsProps {
  documentId: string;
  versions: GetVersionsResponse['data'];
  onViewVersion: (version: number) => void;
  onRestore: (version: number) => void;
  onCompare: (v1: number, v2: number) => void;
}

const knowledgeAnimations = {
  // Document row expand
  rowExpand: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    transition: { duration: 0.2 }
  },
  
  // Chunk preview appear
  chunkPreview: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: { staggerChildren: 0.05 }
  },
  
  // Search result highlight
  searchHighlight: {
    backgroundColor: ['transparent', 'rgba(59, 130, 246, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  },
  
  // Similarity score bar
  similarityBar: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  // Reindex progress
  reindexProgress: {
    width: '100%',
    transition: { duration: 0.3 }
  },
  
  // Version diff line
  diffLine: {
    initial: { opacity: 0, x: -10 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.2 }
  },
  
  // Tag pill
  tagPill: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    exit: { scale: 0 },
    transition: { type: 'spring', stiffness: 300 }
  }
};

const knowledgeShortcuts = {
  'mod+n': 'Add new document',
  'mod+e': 'Edit selected document',
  'mod+f': 'Open search test',
  'mod+s': 'Save document',
  'mod+shift+r': 'Reindex selected',
  'del': 'Delete selected',
  'escape': 'Close editor/panel',
  't': 'Add tag to selected',
};

const knowledgeErrorCodes = {
  // Validation
  KB_VAL_001: 'Document title is required',
  KB_VAL_002: 'Content is too short (min 50 characters)',
  KB_VAL_003: 'Content exceeds maximum size',
  KB_VAL_004: 'Invalid document type',
  
  // Processing
  KB_PROC_001: 'Failed to generate embeddings',
  KB_PROC_002: 'Chunking failed for document',
  KB_PROC_003: 'Reindex job failed',
  KB_PROC_004: 'Document import failed',
  
  // Search
  KB_SRCH_001: 'Search query failed',
  KB_SRCH_002: 'No results above threshold',
  
  // System
  KB_SYS_001: 'Failed to load knowledge base',
  KB_SYS_002: 'Failed to save document',
  KB_SYS_003: 'Version restore failed',
};

// GET /admin/projects/{id}/tools
interface GetProjectToolsResponse {
  success: true;
  data: {
    tools: ProjectTool[];
    summary: {
      total: number;
      enabled: number;
      invocations_24h: number;
    };
  };
}

interface ProjectTool {
  id: string;
  name: string;
  description: string;
  category: 'market_data' | 'wallet' | 'defi_actions' | 'analytics' | 'utility';
  risk_level: 'low' | 'medium' | 'high';
  is_enabled: boolean;
  config: ToolConfig;
  rate_limits: ToolRateLimits;
  requirements: ToolRequirements;
  stats: {
    calls_24h: number;
    avg_latency_ms: number;
    success_rate: number;
  };
  dependencies?: string[];
}

interface ToolConfig {
  [key: string]: any;
}

interface ToolRateLimits {
  per_user_limit: number;
  per_user_window: 'minute' | 'hour' | 'day';
  project_limit: number;
  project_window: 'hour' | 'day';
  max_value_usd?: number;
}

interface ToolRequirements {
  require_wallet: boolean;
  require_2fa: boolean;
  require_2fa_threshold_usd?: number;
  require_approval: boolean;
}

// PUT /admin/projects/{id}/tools/{tool_id}
interface UpdateToolRequest {
  is_enabled?: boolean;
  config?: ToolConfig;
  rate_limits?: Partial<ToolRateLimits>;
  requirements?: Partial<ToolRequirements>;
}

// POST /admin/projects/{id}/tools/{tool_id}/test
interface TestToolRequest {
  params: Record<string, any>;
}

interface TestToolResponse {
  success: boolean;
  result?: any;
  error?: string;
  latency_ms: number;
}

const toolsAnimations = {
  toggleTool: {
    scale: [1, 0.95, 1],
    transition: { duration: 0.2 }
  },
  
  statsUpdate: {
    opacity: [0.5, 1],
    transition: { duration: 0.3 }
  },
  
  categoryExpand: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

// GET /admin/projects/{id}/users
interface GetProjectUsersResponse {
  success: true;
  data: {
    users: ProjectUser[];
    pagination: Pagination;
    summary: {
      total: number;
      active_24h: number;
      total_conversations: number;
      total_cost_usd: number;
    };
  };
}

interface ProjectUser {
  id: string;
  privy_id: string;
  email?: string;
  wallet_address?: string;
  role: 'user' | 'power_user' | 'vip';
  status: 'active' | 'suspended' | 'pending';
  joined_at: string;
  last_active_at: string;
  stats: {
    conversations: number;
    messages: number;
    transactions: number;
    llm_cost_usd: number;
  };
}

// PUT /admin/projects/{id}/users/{user_id}
interface UpdateProjectUserRequest {
  role?: string;
  status?: string;
  permissions?: UserPermissions;
}

// DELETE /admin/projects/{id}/users/{user_id}

const usersAnimations = {
  rowHover: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    transition: { duration: 0.15 }
  },
  
  onlineIndicator: {
    scale: [1, 1.2, 1],
    transition: { duration: 1, repeat: Infinity }
  },
  
  activityChart: {
    pathLength: [0, 1],
    transition: { duration: 1 }
  }
};

// GET /admin/projects/{id}
interface GetProjectResponse {
  success: true;
  data: {
    project: Project;
  };
}

interface Project {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  visibility: 'public' | 'private' | 'invite_only';
  system_prompt: string;
  welcome_message: string;
  enabled_chains: string[];
  enabled_protocols: string[];
  enabled_tools: string[];
  risk_config: RiskConfig;
  status: 'active' | 'paused' | 'archived';
  created_at: string;
  updated_at: string;
}

interface RiskConfig {
  max_position_usd: number;
  max_slippage_bps: number;
  max_leverage: number;
  require_2fa: boolean;
  require_2fa_threshold_usd: number;
  daily_limit_usd: number;
  allowed_tokens: string[];
  blocked_tokens: string[];
}

// PUT /admin/projects/{id}
interface UpdateProjectRequest {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  visibility?: string;
  system_prompt?: string;
  welcome_message?: string;
  enabled_chains?: string[];
  enabled_protocols?: string[];
  enabled_tools?: string[];
  risk_config?: Partial<RiskConfig>;
  status?: string;
}

const projectEditorAnimations = {
  tabSwitch: {
    opacity: [0, 1],
    x: [20, 0],
    transition: { duration: 0.2 }
  },
  
  tokenPillAdd: {
    scale: [0, 1],
    transition: { type: 'spring', stiffness: 300 }
  },
  
  sliderThumb: {
    scale: 1.2,
    transition: { duration: 0.15 }
  }
};

// GET /admin/projects/{id}/analytics?period=30d
interface GetProjectAnalyticsResponse {
  success: true;
  data: {
    period: string;
    summary: {
      users: MetricWithChange;
      conversations: MetricWithChange;
      transaction_volume_usd: MetricWithChange;
      satisfaction_score: MetricWithChange;
    };
    users: {
      total: number;
      active: number;
      new: number;
      churned: number;
      growth_timeseries: TimeSeriesPoint[];
      segments: Record<string, number>;
      acquisition_sources: Record<string, number>;
      retention_cohorts: RetentionCohort[];
    };
    conversations: {
      total: number;
      avg_daily: number;
      avg_length: number;
      timeseries: TimeSeriesPoint[];
      intent_distribution: Record<string, number>;
      satisfaction_distribution: Record<number, number>;
    };
    transactions: {
      total_count: number;
      total_volume_usd: number;
      avg_daily_volume_usd: number;
      by_type: Record<string, TransactionStats>;
      by_chain: Record<string, TransactionStats>;
      by_token: Record<string, TransactionStats>;
      success_rate: number;
      timeseries: TimeSeriesPoint[];
    };
    agent: {
      success_rate: number;
      task_completion_rate: number;
      avg_response_time_ms: number;
      user_rating: number;
      error_distribution: Record<string, number>;
    };
  };
}

interface MetricWithChange {
  value: number;
  change_pct: number;
  change_direction: 'up' | 'down' | 'flat';
}

interface RetentionCohort {
  week: string;
  d1: number;
  d7: number;
  d14: number;
  d30: number;
}

interface TransactionStats {
  count: number;
  volume_usd: number;
  percentage: number;
}

// POST /admin/projects/{id}/analytics/export
interface ExportAnalyticsRequest {
  period: string;
  sections: string[];  // ['users', 'conversations', 'transactions', 'agent']
  format: 'csv' | 'pdf' | 'json';
}

interface ExportAnalyticsResponse {
  success: true;
  data: {
    export_id: string;
    download_url: string;
    expires_at: string;
  };
}

const analyticsAnimations = {
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1.2, ease: 'easeOut' }
  },
  
  metricCounter: {
    opacity: [0, 1],
    y: [20, 0],
    transition: { duration: 0.5, delay: 0.2 }
  },
  
  barGrow: {
    width: '100%',
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  tabSwitch: {
    opacity: [0, 1],
    x: [10, 0],
    transition: { duration: 0.2 }
  }
};

// POST /api/v1/graph/validate
interface ValidationResponse {
  is_valid: boolean;
  issues: Array<{
    issue_type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    count: number;
    details: string;
    affected_entities: string[];
  }>;
  summary: {
    total_issues: number;
    critical_issues: number;
    warnings: number;
  };
}

// POST /api/v1/graph/generate-embeddings
interface GenerateEmbeddingsRequest {
  protocol_ids?: string[]; // Optional: specific protocols
  force_regenerate?: boolean;
}

interface GenerateEmbeddingsResponse {
  generated: number;
  updated: number;
  failed: number;
  total_processed: number;
  processing_time_seconds: number;
  errors?: Array<{
    protocol_id: string;
    protocol_name: string;
    error: string;
  }>;
}

// GET /api/v1/graph/monitoring/cache-stats
interface CacheStatsResponse {
  hit_rate: number; // 0-1
  miss_rate: number; // 0-1
  total_hits: number;
  total_misses: number;
  avg_latency_cached_ms: number;
  avg_latency_uncached_ms: number;
  cache_size_mb: number;
  cache_max_mb: number;
  evictions: number;
  top_queries: Array<{
    query: string;
    hits: number;
    avg_latency_ms: number;
  }>;
}

// DELETE /api/v1/graph/monitoring/cache
interface ClearCacheRequest {
  clear_all?: boolean;
  clear_expired?: boolean;
  clear_pattern?: string; // e.g., "search:*"
}

interface ClearCacheResponse {
  success: boolean;
  keys_deleted: number;
  message: string;
}

// GET /api/v1/graph/analytics
interface GraphAnalyticsResponse {
  overview: {
    total_protocols: number;
    total_tokens: number;
    total_chains: number;
    total_relationships: number;
    last_updated: string;
  };
  top_protocols_by_tvl: Array<{
    protocol_id: string;
    protocol_name: string;
    tvl: number;
    category: string;
  }>;
  category_distribution: Record<string, number>;
  chain_distribution: Record<string, number>;
  risk_summary: {
    average_risk: number;
    low_risk_count: number;
    medium_risk_count: number;
    high_risk_count: number;
    critical_risk_count: number;
  };
}

interface GraphRAGDashboardProps {
  refreshInterval?: number; // Auto-refresh (ms)
}

interface GraphHealthIndicatorProps {
  healthScore: number; // 0-100
  issues: Issue[];
}

interface EmbeddingProgressProps {
  total: number;
  generated: number;
  failed: number;
  onGenerate: () => void;
}

interface CacheStatsDisplayProps {
  stats: CacheStatsResponse;
  onClear: (options: ClearCacheRequest) => void;
}

interface QueryPerformanceChartProps {
  metrics: Array<{
    timestamp: string;
    latency_ms: number;
    cache_hit: boolean;
  }>;
  timeRange: '1h' | '24h' | '7d' | '30d';
}

const adminErrors = {
  ADMIN_001: 'Insufficient permissions (admin required)',
  ADMIN_002: 'Validation failed',
  ADMIN_003: 'Embedding generation failed',
  ADMIN_004: 'Cache clear failed',
  
  GRAPH_001: 'Graph data corrupted',
  GRAPH_002: 'Unable to connect to graph database',
  
  EMBED_001: 'OpenAI API error',
  EMBED_002: 'Rate limit exceeded',
  EMBED_003: 'Invalid protocol data',
};

// GET /admin/admins
interface GetAdminsResponse {
  success: true;
  data: {
    admins: AdminUser[];
    summary: {
      total: number;
      active: number;
      pending: number;
      suspended: number;
    };
    pagination: Pagination;
  };
}

interface AdminUser {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: AdminRole;
  status: 'active' | 'pending' | 'suspended' | 'deactivated';
  department?: string;
  phone?: string;
  two_factor_enabled: boolean;
  last_login_at?: string;
  last_login_ip?: string;
  created_at: string;
  access_expires_at?: string;
  invited_by?: string;
}

interface AdminRole {
  id: string;
  name: string;
  color: string;
  is_system: boolean;
  permissions: string[];
}

// POST /admin/admins/invite
interface InviteAdminRequest {
  email: string;
  name: string;
  role_id: string;
  department?: string;
  access_expires_at?: string;
  send_email?: boolean;
}

interface InviteAdminResponse {
  success: true;
  data: {
    admin: AdminUser;
    invitation_url?: string;
  };
}

// GET /admin/admins/roles
interface GetRolesResponse {
  success: true;
  data: {
    roles: AdminRole[];
    permissions: Permission[];
  };
}

interface Permission {
  id: string;
  name: string;
  description: string;
  category: string;
}

// POST /admin/admins/roles
// PUT /admin/admins/roles/{id}
interface RoleRequest {
  name: string;
  description: string;
  color: string;
  permissions: string[];
}

// GET /admin/admins/{id}/sessions
interface GetAdminSessionsResponse {
  success: true;
  data: {
    sessions: AdminSession[];
  };
}

interface AdminSession {
  id: string;
  ip_address: string;
  user_agent: string;
  device: string;
  location?: {
    city: string;
    country: string;
  };
  created_at: string;
  last_active_at: string;
  is_current: boolean;
}

// DELETE /admin/admins/{id}/sessions/{session_id}
// DELETE /admin/admins/{id}/sessions (terminate all)

const adminsAnimations = {
  roleColor: {
    backgroundColor: 'var(--role-color)',
    transition: { duration: 0.2 }
  },
  
  permissionToggle: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.15 }
  },
  
  sessionTerminate: {
    opacity: [1, 0],
    x: [0, -20],
    transition: { duration: 0.3 }
  },
  
  inviteSend: {
    scale: [1, 0.95, 1],
    transition: { duration: 0.2 }
  }
};

const adminsShortcuts = {
  'mod+n': 'New admin invitation',
  'mod+r': 'New role',
  '/': 'Focus search',
  'delete': 'Suspend selected admin',
};

// GET /admin/settings
interface GetSettingsResponse {
  success: true;
  data: {
    general: GeneralSettings;
    features: FeatureFlags;
    security: SecuritySettings;
    rate_limits: RateLimitSettings;
    integrations: IntegrationSettings;
    last_modified: {
      at: string;
      by: string;
    };
  };
}

interface GeneralSettings {
  platform_name: string;
  support_email: string;
  support_url: string;
  default_timezone: string;
  default_language: string;
  environment: 'production' | 'staging' | 'development';
  platform_status: 'operational' | 'degraded' | 'outage';
  maintenance_mode: boolean;
  new_registrations_enabled: boolean;
}

interface FeatureFlags {
  [key: string]: {
    enabled: boolean;
    beta_percentage?: number;
    description: string;
    category: string;
    requires_approval?: boolean;
    enabled_at?: string;
    enabled_by?: string;
  };
}

interface SecuritySettings {
  session_timeout_minutes: number;
  max_concurrent_sessions: number;
  require_2fa_admin: boolean;
  require_2fa_transactions: boolean;
  require_2fa_threshold_usd: number;
  require_2fa_all_users: boolean;
  password_min_length: number;
  password_expiry_days: number;
  password_require_uppercase: boolean;
  password_require_lowercase: boolean;
  password_require_numbers: boolean;
  password_require_special: boolean;
  password_block_common: boolean;
  password_history_count: number;
  admin_ip_allowlist: string[];
  geo_restrictions_enabled: boolean;
  blocked_countries: string[];
}

// PUT /admin/settings/{section}
interface UpdateSettingsRequest {
  settings: Partial<GeneralSettings | SecuritySettings | RateLimitSettings>;
}

interface UpdateSettingsResponse {
  success: true;
  data: {
    updated_fields: string[];
    requires_restart: boolean;
  };
}

// PUT /admin/settings/features/{flag_name}
interface ToggleFeatureFlagRequest {
  enabled: boolean;
  beta_percentage?: number;
  scheduled_at?: string;
  reason?: string;
}

// GET /admin/settings/export
interface ExportSettingsResponse {
  success: true;
  data: {
    settings: AllSettings;
    exported_at: string;
    version: string;
  };
}

// POST /admin/settings/import
interface ImportSettingsRequest {
  settings: AllSettings;
  overwrite_existing?: boolean;
}

const settingsAnimations = {
  toggleSwitch: {
    x: [0, 24],
    transition: { type: 'spring', stiffness: 500, damping: 30 }
  },
  
  saveSuccess: {
    scale: [1, 1.05, 1],
    transition: { duration: 0.3 }
  },
  
  flagExpand: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.2 }
  },
  
  warningPulse: {
    boxShadow: ['0 0 0 0 rgba(245, 158, 11, 0.4)', '0 0 0 8px rgba(245, 158, 11, 0)'],
    transition: { duration: 1, repeat: Infinity }
  }
};

const settingsShortcuts = {
  'mod+s': 'Save settings',
  'mod+e': 'Export settings',
  'mod+i': 'Import settings',
  '1-6': 'Switch tabs',
  'mod+z': 'Undo last change',
};

const settingsErrorCodes = {
  SET_VAL_001: 'Invalid setting value',
  SET_VAL_002: 'Setting out of allowed range',
  SET_PERM_001: 'Insufficient permissions to modify',
  SET_IMPORT_001: 'Invalid import file format',
  SET_IMPORT_002: 'Version mismatch in import',
  SET_FLAG_001: 'Feature flag has dependencies',
};

// GET /admin/maintenance
interface GetMaintenanceStatusResponse {
  success: true;
  data: {
    current_status: 'operational' | 'maintenance' | 'admin_only' | 'emergency';
    maintenance_mode: boolean;
    maintenance_details?: {
      reason: string;
      description: string;
      started_at: string;
      estimated_end: string;
      allow_admin: boolean;
    };
    scheduled: ScheduledMaintenance[];
    history: MaintenanceRecord[];
  };
}

interface ScheduledMaintenance {
  id: string;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  estimated_duration_minutes: number;
  impact: 'full_outage' | 'partial' | 'brief_interruption';
  notifications: {
    before_24h: boolean;
    before_1h: boolean;
    at_start: boolean;
  };
  created_by: string;
  created_at: string;
}

interface MaintenanceRecord {
  id: string;
  title: string;
  started_at: string;
  ended_at: string;
  estimated_minutes: number;
  actual_minutes: number;
  status: 'completed' | 'cancelled';
}

// POST /admin/maintenance/enable
interface EnableMaintenanceRequest {
  reason: string;
  description: string;
  estimated_duration_minutes: number;
  allow_admin_access: boolean;
  show_countdown: boolean;
  block_api: boolean;
  pause_jobs: boolean;
  notifications: {
    email: boolean;
    push: boolean;
    status_page: boolean;
    twitter: boolean;
  };
}

// POST /admin/maintenance/disable
interface DisableMaintenanceRequest {
  notes?: string;
}

// POST /admin/maintenance/schedule
interface ScheduleMaintenanceRequest {
  title: string;
  description: string;
  start_time: string;
  estimated_duration_minutes: number;
  impact: 'full_outage' | 'partial' | 'brief_interruption';
  notifications: {
    before_24h: boolean;
    before_1h: boolean;
    at_start: boolean;
  };
}

const maintenanceAnimations = {
  statusPulse: {
    opacity: [1, 0.7, 1],
    transition: { duration: 2, repeat: Infinity }
  },
  
  warningBanner: {
    y: [-50, 0],
    opacity: [0, 1],
    transition: { duration: 0.3 }
  },
  
  countdown: {
    scale: [1, 1.05, 1],
    transition: { duration: 1, repeat: Infinity }
  }
};

const maintenanceShortcuts = {
  'mod+m': 'Toggle maintenance mode',
  'mod+e': 'Emergency mode',
  's': 'Schedule maintenance',
};

// GET /admin/audit
interface GetAuditEventsRequest {
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
  event_types?: string[];
  severity?: string[];
  actor_id?: string;
  resource_type?: string;
  resource_id?: string;
  search?: string;
}

interface GetAuditEventsResponse {
  success: true;
  data: {
    events: AuditEvent[];
    summary: {
      total: number;
      critical: number;
      warning: number;
      info: number;
    };
    pagination: Pagination;
  };
}

interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  event_category: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  actor: {
    id?: string;
    email?: string;
    name?: string;
    role?: string;
    ip_address: string;
    user_agent?: string;
    location?: {
      city: string;
      country: string;
    };
    session_id?: string;
  };
  target?: {
    type: string;
    id: string;
    name?: string;
  };
  changes?: {
    before: Record<string, any>;
    after: Record<string, any>;
  };
  metadata?: Record<string, any>;
}

// GET /admin/audit/{event_id}
interface GetAuditEventResponse {
  success: true;
  data: {
    event: AuditEvent;
    related_events: AuditEvent[];
    actor_session_events?: AuditEvent[];
  };
}

// POST /admin/audit/export
interface ExportAuditRequest {
  start_date: string;
  end_date: string;
  event_types?: string[];
  severity?: string[];
  actor_ids?: string[];
  format: 'csv' | 'json' | 'pdf' | 'siem';
  include_actor_details?: boolean;
  include_ip_addresses?: boolean;
  include_change_diffs?: boolean;
  include_raw_data?: boolean;
}

interface ExportAuditResponse {
  success: true;
  data: {
    export_id: string;
    estimated_events: number;
    estimated_size_mb: number;
    status: 'processing' | 'ready';
    download_url?: string;
  };
}

const auditAnimations = {
  eventAppear: {
    opacity: [0, 1],
    x: [-20, 0],
    transition: { duration: 0.2 }
  },
  
  severityPulse: {
    boxShadow: ['0 0 0 0 var(--severity-color)', '0 0 0 4px transparent'],
    transition: { duration: 0.5 }
  },
  
  expandDetail: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.3 }
  },
  
  liveIndicator: {
    opacity: [1, 0.5, 1],
    transition: { duration: 1.5, repeat: Infinity }
  }
};

const auditShortcuts = {
  'mod+e': 'Export logs',
  'mod+f': 'Focus search',
  'j/k': 'Navigate events',
  'enter': 'View event detail',
  'escape': 'Close detail',
  'r': 'Refresh events',
};

const auditErrorCodes = {
  AUDIT_LOAD_001: 'Failed to load audit events',
  AUDIT_EXPORT_001: 'Export failed',
  AUDIT_EXPORT_002: 'Date range too large for export',
  AUDIT_DETAIL_001: 'Event not found',
};

// GET /admin/system/health
interface GetSystemHealthResponse {
  success: true;
  data: {
    overall_status: 'operational' | 'degraded' | 'partial_outage' | 'major_outage';
    uptime_30d: number;
    services: ServiceHealth[];
    databases: DatabaseHealth[];
    infrastructure: {
      cpu_percent: number;
      memory_percent: number;
      disk_percent: number;
      network_in_mbps: number;
      network_out_mbps: number;
    };
    external_integrations: IntegrationHealth[];
    recent_incidents: Incident[];
  };
}

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  requests_per_second: number;
  error_rate: number;
  last_check: string;
}

interface DatabaseHealth {
  name: string;
  type: 'postgresql' | 'redis' | 'timescaledb';
  status: 'healthy' | 'degraded' | 'down';
  connections_used: number;
  connections_max: number;
  latency_ms?: number;
  replica_lag_seconds?: number;
  cache_hit_rate?: number;
  memory_used_gb?: number;
  memory_max_gb?: number;
}

interface IntegrationHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  last_check: string;
}

interface Incident {
  id: string;
  severity: 'critical' | 'major' | 'minor' | 'maintenance';
  title: string;
  started_at: string;
  resolved_at?: string;
  duration_minutes?: number;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
}

// GET /admin/llm/providers
// Get all providers with health status

interface GetProvidersResponse {
  success: true;
  data: {
    providers: Provider[];
    system_status: 'healthy' | 'degraded' | 'down';
  };
}

interface Provider {
  id: string;                    // UUID
  name: string;                  // "vertex_ai"
  display_name: string;          // "Google Vertex AI"
  priority: number;              // 1-3
  is_enabled: boolean;
  health_status: 'healthy' | 'degraded' | 'down';
  health_check_latency_ms: number;
  last_health_check: string;     // ISO datetime
  config: Record<string, any>;
  models_count: number;
  active_models_count: number;
  created_at: string;
  updated_at: string;
}

// Error Responses
interface ErrorResponse {
  success: false;
  error: {
    code: 'LLM_001' | 'LLM_002' | 'LLM_003';
    message: string;
  };
}

// GET /admin/llm/telemetry/overview?period=24h
// Get dashboard metrics overview

interface GetTelemetryOverviewRequest {
  period: '1h' | '24h' | '7d' | '30d';
}

interface GetTelemetryOverviewResponse {
  success: true;
  data: {
    period: string;
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate: number;
    
    latency: {
      avg_ms: number;
      p50_ms: number;
      p95_ms: number;
      p99_ms: number;
    };
    
    retries: {
      total: number;
      rate: number;
    };
    
    timeouts: {
      total: number;
      rate: number;
    };
    
    active_requests: number;
    
    cost: {
      total_usd: number;
      by_provider: Record<string, number>;
    };
    
    comparison: {
      requests_change_pct: number;
      success_change_pct: number;
      latency_change_ms: number;
    };
  };
}

// GET /admin/llm/budgets
// Get all budgets with current status

interface GetBudgetsResponse {
  success: true;
  data: {
    budgets: Budget[];
    today_spend: number;
    month_spend: number;
    projected_month_spend: number;
  };
}

interface Budget {
  id: string;
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  budget_amount_usd: number;
  current_spend_usd: number;
  utilization_pct: number;
  warning_threshold_pct: number;
  critical_threshold_pct: number;
  is_hard_limit: boolean;
  is_active: boolean;
  period_start: string;
  period_end: string;
}

// GET /admin/llm/circuit-breakers
// Get all circuit breaker states

interface GetCircuitBreakersResponse {
  success: true;
  data: {
    breakers: CircuitBreaker[];
    open_count: number;
    half_open_count: number;
    total_count: number;
  };
}

interface CircuitBreaker {
  id: string;
  entity_type: 'provider' | 'model';
  entity_id: string;
  entity_name: string;
  state: 'closed' | 'open' | 'half_open';
  failure_count: number;
  last_failure_at: string | null;
  opened_at: string | null;
  config: {
    failure_threshold: number;
    recovery_timeout_seconds: number;
    half_open_max_requests: number;
  };
}

// POST /admin/llm/circuit-breakers/{id}/reset
// Reset a circuit breaker

interface ResetCircuitBreakerResponse {
  success: true;
  data: {
    breaker_id: string;
    previous_state: string;
    new_state: 'closed';
    reset_at: string;
  };
}

// GET /admin/llm/telemetry/timeseries?metric=requests&period=24h&group_by=provider
// Get time series data for charts

interface GetTimeSeriesRequest {
  metric: 'requests' | 'latency' | 'cost' | 'errors';
  period: '1h' | '24h' | '7d' | '30d';
  group_by?: 'provider' | 'model' | 'agent';
  interval?: 'minute' | 'hour' | 'day';
}

interface GetTimeSeriesResponse {
  success: true;
  data: {
    metric: string;
    period: string;
    interval: string;
    series: TimeSeriesPoint[];
  };
}

interface TimeSeriesPoint {
  timestamp: string;          // ISO datetime
  value: number;
  breakdown?: Record<string, number>;
}

// POST /admin/llm/providers/{id}/health-check
// Force health check on provider

interface ForceHealthCheckResponse {
  success: true;
  data: {
    provider_id: string;
    status: 'healthy' | 'degraded' | 'down';
    latency_ms: number;
    checked_at: string;
  };
}

// POST /admin/llm/rankings/recalculate
// Trigger ranking recalculation

interface RecalculateRankingsResponse {
  success: true;
  data: {
    job_id: string;
    status: 'queued';
    estimated_duration_seconds: number;
  };
}

interface LLMDashboardState {
  // Provider Data
  providers: Provider[];
  systemStatus: 'healthy' | 'degraded' | 'down';
  
  // Metrics Data
  overview: TelemetryOverview | null;
  timeSeries: TimeSeriesPoint[];
  
  // Budget Data
  budgets: Budget[];
  todaySpend: number;
  monthSpend: number;
  projectedSpend: number;
  
  // Circuit Breakers
  circuitBreakers: CircuitBreaker[];
  openBreakersCount: number;
  
  // Alerts
  alerts: Alert[];
  unacknowledgedCount: number;
  
  // Rankings
  topModelsByAgent: Record<string, RankedModel[]>;
  
  // UI State
  loading: {
    providers: boolean;
    overview: boolean;
    timeSeries: boolean;
    budgets: boolean;
    breakers: boolean;
    alerts: boolean;
  };
  
  errors: {
    providers: Error | null;
    overview: Error | null;
    timeSeries: Error | null;
  };
  
  // Real-time
  wsConnected: boolean;
  lastUpdate: string | null;
  
  // Filters
  timeSeriesPeriod: '1h' | '24h' | '7d' | '30d';
  timeSeriesGroupBy: 'provider' | 'model' | 'agent';
  
  // Actions
  pendingActions: string[];
}

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  source: string;                // Module/component that generated
  resource_type?: string;        // 'provider', 'model', 'budget'
  resource_id?: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
  expires_at?: string;
}

interface RankedModel {
  model_id: string;
  model_name: string;
  provider_name: string;
  provider_icon: string;
  ranking_score: number;
  success_rate: number;
  avg_latency_ms: number;
  total_requests: number;
  trend: 'up' | 'down' | 'stable';
}

interface ProviderHealthCardProps {
  provider: Provider;
  onViewDetails: (id: string) => void;
  onForceHealthCheck: (id: string) => void;
  loading?: boolean;
  expanded?: boolean;
}

// Usage
<ProviderHealthCard
  provider={vertexAI}
  onViewDetails={handleViewDetails}
  onForceHealthCheck={handleHealthCheck}
  expanded={selectedProvider === vertexAI.id}
/>

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    label: string;
  };
  status?: 'success' | 'warning' | 'error' | 'neutral';
  loading?: boolean;
  onClick?: () => void;
}

// Usage
<MetricCard
  title="Success Rate"
  value="98.7%"
  icon={<CheckCircle />}
  trend={{ value: 0.3, direction: 'up', label: 'vs yesterday' }}
  status="success"
/>

interface BudgetProgressCardProps {
  title: string;
  current: number;
  limit: number;
  projected?: number;
  variant: 'daily' | 'monthly';
  onManage?: () => void;
}

// Usage
<BudgetProgressCard
  title="Today's Spend"
  current={127.45}
  limit={500}
  variant="daily"
  onManage={handleManageBudget}
/>

interface TimeSeriesChartProps {
  data: TimeSeriesPoint[];
  metric: string;
  period: string;
  groupBy?: string;
  height?: number;
  showLegend?: boolean;
  interactive?: boolean;
  onPointClick?: (point: TimeSeriesPoint) => void;
}

// Usage
<TimeSeriesChart
  data={requestTimeSeries}
  metric="requests"
  period="24h"
  groupBy="provider"
  height={250}
  showLegend
  interactive
/>

interface CircuitBreakerStatusProps {
  breakers: CircuitBreaker[];
  openCount: number;
  onReset: (id: string) => void;
  onViewAll: () => void;
  loading?: boolean;
}

// Usage
<CircuitBreakerStatus
  breakers={circuitBreakers}
  openCount={openBreakersCount}
  onReset={handleResetBreaker}
  onViewAll={navigateToBreakers}
/>

interface AlertTimelineProps {
  alerts: Alert[];
  maxItems?: number;
  onAcknowledge: (id: string) => void;
  onViewAlert: (alert: Alert) => void;
  onViewAll: () => void;
}

// Usage
<AlertTimeline
  alerts={recentAlerts}
  maxItems={5}
  onAcknowledge={handleAcknowledge}
  onViewAlert={handleViewAlert}
  onViewAll={navigateToAlerts}
/>

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
  permission?: string;
}

interface QuickActionPanelProps {
  actions: QuickAction[];
  columns?: 2 | 3 | 4;
}

// Usage
<QuickActionPanel
  actions={[
    { id: 'health', label: 'Force Health Check', icon: <RefreshCw />, onClick: handleHealthCheck },
    { id: 'rankings', label: 'Recalculate Rankings', icon: <BarChart />, onClick: handleRecalculate },
    { id: 'export', label: 'Export Report', icon: <Download />, onClick: handleExport },
  ]}
  columns={3}
/>

const llmDashboardAnimations = {
  // Page entry
  pageEnter: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 }
  },
  
  // Staggered card entry
  staggerContainer: {
    animate: {
      transition: {
        staggerChildren: 0.05
      }
    }
  },
  
  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3 }
  },
  
  // Provider card hover
  providerCardHover: {
    scale: 1.02,
    boxShadow: '0 8px 30px rgba(59, 130, 246, 0.15)',
    transition: { duration: 0.2 }
  },
  
  // Metric value update
  metricUpdate: {
    scale: [1, 1.05, 1],
    color: ['inherit', '#10B981', 'inherit'],
    transition: { duration: 0.3 }
  },
  
  // Status indicator pulse
  statusPulse: {
    scale: [1, 1.2, 1],
    opacity: [1, 0.8, 1],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  // Alert slide in
  alertEnter: {
    initial: { opacity: 0, x: 50, height: 0 },
    animate: { opacity: 1, x: 0, height: 'auto' },
    exit: { opacity: 0, x: -50, height: 0 },
    transition: { duration: 0.3 }
  },
  
  // Progress bar fill
  progressFill: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  // Chart line draw
  chartLineDraw: {
    initial: { pathLength: 0 },
    animate: { pathLength: 1 },
    transition: { duration: 1, ease: 'easeInOut' }
  },
  
  // Button click feedback
  buttonTap: {
    scale: 0.95,
    transition: { duration: 0.1 }
  },
  
  // Loading skeleton
  skeleton: {
    opacity: [0.5, 1, 0.5],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  // WebSocket connected indicator
  wsConnected: {
    scale: [1, 1.2, 1],
    backgroundColor: ['#10B981', '#34D399', '#10B981'],
    transition: { duration: 2, repeat: Infinity }
  }
};

const llmDashboardShortcuts = {
  'mod+r': 'Refresh all data',
  'mod+h': 'Force health check',
  'mod+e': 'Export report',
  '1': 'Focus Vertex AI card',
  '2': 'Focus DeepInfra card',
  '3': 'Focus Bedrock card',
  'a': 'View all alerts',
  'b': 'View all breakers',
  't': 'Toggle time period (1h/24h/7d)',
  '?': 'Show keyboard shortcuts',
};

const errorCodes = {
  // API Errors
  LLM_DASH_001: 'Failed to fetch provider health data',
  LLM_DASH_002: 'Failed to fetch telemetry overview',
  LLM_DASH_003: 'Failed to fetch budget information',
  LLM_DASH_004: 'Failed to fetch circuit breaker status',
  LLM_DASH_005: 'Failed to fetch alerts',
  LLM_DASH_006: 'Failed to fetch time series data',
  
  // WebSocket Errors
  LLM_DASH_WS_001: 'WebSocket connection failed',
  LLM_DASH_WS_002: 'WebSocket disconnected unexpectedly',
  
  // Action Errors
  LLM_DASH_ACT_001: 'Failed to force health check',
  LLM_DASH_ACT_002: 'Failed to reset circuit breaker',
  LLM_DASH_ACT_003: 'Failed to acknowledge alert',
  LLM_DASH_ACT_004: 'Failed to trigger ranking recalculation',
  
  // Permission Errors
  LLM_DASH_PERM_001: 'Insufficient permissions for this action',
};

// Error display component
interface DashboardErrorProps {
  error: Error;
  section: string;
  onRetry: () => void;
}

// GET /admin/llm/budgets
// Get all budgets with current status

interface GetBudgetsResponse {
  success: true;
  data: {
    budgets: Budget[];
    summary: {
      today_spend: number;
      month_spend: number;
      projected_month_spend: number;
      active_alerts_count: number;
    };
  };
}

interface Budget {
  id: string;
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  scope_type: 'global' | 'provider' | 'model' | 'tier';
  scope_id?: string;
  scope_name?: string;
  budget_amount_usd: number;
  current_spend_usd: number;
  utilization_pct: number;
  warning_threshold_pct: number;
  critical_threshold_pct: number;
  action_on_critical: 'alert' | 'throttle' | 'stop';
  is_hard_limit: boolean;
  is_active: boolean;
  period_start: string;
  period_end: string;
  time_remaining_seconds: number;
  projected_spend_usd: number;
  spend_rate_per_hour: number;
  notifications: {
    email: boolean;
    slack: boolean;
    in_app: boolean;
  };
  created_at: string;
  updated_at: string;
}

// POST /admin/llm/budgets
// Create new budget

interface CreateBudgetRequest {
  name: string;
  budget_type: 'daily' | 'weekly' | 'monthly';
  scope_type: 'global' | 'provider' | 'model' | 'tier';
  scope_id?: string;
  budget_amount_usd: number;
  warning_threshold_pct: number;
  critical_threshold_pct: number;
  action_on_critical: 'alert' | 'throttle' | 'stop';
  is_hard_limit?: boolean;
  notifications: {
    email?: boolean;
    slack?: boolean;
    in_app?: boolean;
  };
}

// Validation
const createBudgetValidation = {
  name: { required: true, minLength: 2, maxLength: 100 },
  budget_amount_usd: { required: true, min: 1, max: 1000000 },
  warning_threshold_pct: { required: true, min: 1, max: 100 },
  critical_threshold_pct: { required: true, min: 1, max: 100 }
};

interface CreateBudgetResponse {
  success: true;
  data: {
    budget: Budget;
  };
}

// GET /admin/llm/budgets/{id}
// Get detailed budget information

interface GetBudgetDetailsResponse {
  success: true;
  data: {
    budget: Budget;
    spend_breakdown: {
      by_provider: Record<string, number>;
      by_model: Record<string, number>;
      by_tier: Record<string, number>;
      by_agent: Record<string, number>;
    };
    hourly_spend: TimeSeriesPoint[];
    alerts_history: BudgetAlert[];
  };
}

interface BudgetAlert {
  id: string;
  threshold_type: 'warning' | 'critical';
  threshold_pct: number;
  amount_at_trigger: number;
  triggered_at: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
}

// GET /admin/llm/budgets/{id}/history?period=7d
// Get historical spend data

interface GetSpendHistoryResponse {
  success: true;
  data: {
    budget_id: string;
    period: string;
    daily_spend: Array<{
      date: string;
      spend_usd: number;
      limit_usd: number;
      utilization_pct: number;
    }>;
    total_spend: number;
    average_daily_spend: number;
    peak_day: {
      date: string;
      spend: number;
    };
    trend: {
      direction: 'up' | 'down' | 'stable';
      change_pct: number;
    };
  };
}

interface BudgetsModuleState {
  // Data
  budgets: Budget[];
  summary: BudgetsSummary | null;
  selectedBudget: Budget | null;
  budgetDetails: GetBudgetDetailsResponse['data'] | null;
  
  // UI State
  loading: {
    list: boolean;
    details: boolean;
    create: boolean;
    update: boolean;
  };
  
  errors: {
    list: Error | null;
    create: Error | null;
    update: Error | null;
  };
  
  // Filters
  filters: {
    type: 'all' | 'daily' | 'weekly' | 'monthly';
    scope: 'all' | 'global' | 'provider' | 'model' | 'tier';
    status: 'all' | 'active' | 'paused';
  };
  
  // Create/Edit Modal
  modalOpen: boolean;
  modalMode: 'create' | 'edit';
  formData: Partial<CreateBudgetRequest>;
  
  // Spend History
  historyPeriod: '7d' | '30d' | '90d';
  historyData: GetSpendHistoryResponse['data'] | null;
  
  // Real-time
  wsConnected: boolean;
  lastUpdate: string | null;
}

interface BudgetCardProps {
  budget: Budget;
  onEdit: (id: string) => void;
  onViewDetails: (id: string) => void;
  onPause: (id: string) => void;
  onDelete: (id: string) => void;
  animated?: boolean;
}

interface BudgetProgressBarProps {
  current: number;
  limit: number;
  warningThreshold: number;
  criticalThreshold: number;
  showMarkers?: boolean;
  animated?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

interface SpendBreakdownChartProps {
  data: Record<string, number>;
  type: 'pie' | 'bar';
  title: string;
  showPercentages?: boolean;
  showValues?: boolean;
  onSegmentClick?: (key: string) => void;
}

interface BudgetFormProps {
  initialData?: Partial<CreateBudgetRequest>;
  mode: 'create' | 'edit';
  onSubmit: (data: CreateBudgetRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}

interface ImpactPreviewProps {
  budgetAmount: number;
  budgetType: 'daily' | 'weekly' | 'monthly';
  scope: string;
  historicalAverage: number;
}

const budgetsAnimations = {
  // Progress bar fill
  progressFill: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 1, ease: 'easeOut' }
  },
  
  // Threshold marker pulse
  thresholdPulse: {
    scale: [1, 1.3, 1],
    opacity: [1, 0.7, 1],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  // Spend counter increment
  spendIncrement: {
    scale: [1, 1.1, 1],
    color: ['#fff', '#F59E0B', '#fff'],
    transition: { duration: 0.3 }
  },
  
  // Alert badge bounce
  alertBounce: {
    y: [0, -5, 0],
    transition: { duration: 0.5, repeat: Infinity }
  },
  
  // Chart segment hover
  chartSegmentHover: {
    scale: 1.05,
    opacity: 1,
    transition: { duration: 0.2 }
  },
  
  // Card expand
  cardExpand: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.3 }
  },
  
  // Warning state
  warningState: {
    borderColor: ['#334155', '#F59E0B', '#334155'],
    transition: { duration: 1, repeat: Infinity }
  },
  
  // Critical state
  criticalState: {
    borderColor: ['#334155', '#EF4444', '#334155'],
    boxShadow: ['none', '0 0 20px rgba(239, 68, 68, 0.3)', 'none'],
    transition: { duration: 0.5, repeat: Infinity }
  }
};

const budgetsShortcuts = {
  'mod+n': 'Create new budget',
  'mod+e': 'Edit selected budget',
  'mod+r': 'Refresh data',
  'd': 'View details',
  'h': 'View history',
  'escape': 'Close modal',
  '1/2/3': 'Filter by type (daily/weekly/monthly)',
};

const budgetErrorCodes = {
  // Validation
  BUD_VAL_001: 'Budget name is required',
  BUD_VAL_002: 'Budget amount must be positive',
  BUD_VAL_003: 'Warning threshold must be less than critical',
  BUD_VAL_004: 'Invalid scope configuration',
  
  // Business Logic
  BUD_BUS_001: 'Cannot reduce budget below current spend',
  BUD_BUS_002: 'Duplicate budget scope exists',
  BUD_BUS_003: 'Cannot delete budget with active alerts',
  
  // System
  BUD_SYS_001: 'Failed to load budgets',
  BUD_SYS_002: 'Failed to create budget',
  BUD_SYS_003: 'Failed to update budget',
  BUD_SYS_004: 'Real-time updates unavailable',
};

// GET /admin/llm/models
// Get all models with optional filters

interface GetModelsRequest {
  provider_id?: string;
  tier?: 'premium' | 'standard' | 'economy';
  is_enabled?: boolean;
}

interface GetModelsResponse {
  success: true;
  data: {
    models: Model[];
    total: number;
    by_provider: Record<string, number>;
    by_tier: Record<string, number>;
  };
}

interface Model {
  id: string;
  provider_id: string;
  provider_name: string;
  name: string;                     // "gemini-1.5-pro"
  display_name: string;             // "Gemini 1.5 Pro"
  tier: 'premium' | 'standard' | 'economy';
  is_enabled: boolean;
  
  capabilities: {
    text_generation: boolean;
    code_generation: boolean;
    function_calling: boolean;
    vision: boolean;
    long_context: boolean;
    json_mode: boolean;
  };
  
  limits: {
    context_window: number;
    max_output_tokens: number;
  };
  
  pricing: {
    input_per_1k_tokens: number;
    output_per_1k_tokens: number;
    cached_input_per_1k_tokens?: number;
  };
  
  config: ModelConfig;
  
  stats_24h: {
    requests: number;
    success_rate: number;
    avg_latency_ms: number;
    p95_latency_ms: number;
    total_cost_usd: number;
  };
  
  agent_usage: Array<{
    agent_type: string;
    requests: number;
    success_rate: number;
    ranking_position: number;
    ranking_score: number;
  }>;
  
  created_at: string;
  updated_at: string;
}

interface ModelConfig {
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  system_prompt_prefix?: string;
}

// PUT /admin/llm/models/{id}
// Update model configuration

interface UpdateModelRequest {
  is_enabled?: boolean;
  tier?: 'premium' | 'standard' | 'economy';
  config?: Partial<ModelConfig>;
  cost_limits?: {
    daily_limit_usd?: number;
    action_on_limit?: 'alert' | 'throttle' | 'disable';
  };
  enabled_for_agents?: string[];
}

// Validation
const updateModelValidation = {
  'config.temperature': { min: 0, max: 2 },
  'config.max_tokens': { min: 1, max: 128000 },
  'config.top_p': { min: 0, max: 1 },
  'config.frequency_penalty': { min: -2, max: 2 },
  'cost_limits.daily_limit_usd': { min: 0, max: 10000 }
};

interface UpdateModelResponse {
  success: true;
  data: {
    model: Model;
    changes: Array<{
      field: string;
      old_value: any;
      new_value: any;
    }>;
  };
}

// GET /admin/llm/models/{id}/performance?period=24h
// Get detailed model performance

interface GetModelPerformanceResponse {
  success: true;
  data: {
    model_id: string;
    period: string;
    summary: {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      success_rate: number;
      total_input_tokens: number;
      total_output_tokens: number;
      total_cost_usd: number;
      avg_latency_ms: number;
    };
    latency_percentiles: {
      p50: number;
      p75: number;
      p90: number;
      p95: number;
      p99: number;
    };
    error_breakdown: Record<string, number>;
    agent_breakdown: Array<{
      agent_type: string;
      requests: number;
      success_rate: number;
      avg_latency_ms: number;
      total_cost_usd: number;
      ranking_score: number;
    }>;
    timeseries: {
      requests: TimeSeriesPoint[];
      latency: TimeSeriesPoint[];
      cost: TimeSeriesPoint[];
    };
  };
}

// POST /admin/llm/models/compare
// Compare multiple models

interface CompareModelsRequest {
  model_ids: string[];           // 2-4 models
  period?: '1h' | '24h' | '7d' | '30d';
  agent_type?: string;
}

interface CompareModelsResponse {
  success: true;
  data: {
    models: Array<{
      model_id: string;
      model_name: string;
      provider_name: string;
      tier: string;
      metrics: {
        requests: number;
        success_rate: number;
        avg_latency_ms: number;
        p95_latency_ms: number;
        cost_per_1k: number;
        total_cost: number;
        context_window: number;
      };
      agent_performance: Record<string, {
        success_rate: number;
        avg_latency_ms: number;
        ranking_score: number;
      }>;
    }>;
    recommendation: {
      best_quality: string;
      best_value: string;
      best_speed: string;
      summary: string;
    };
  };
}

interface ModelsModuleState {
  // Data
  models: Model[];
  modelsByProvider: Record<string, Model[]>;
  selectedModel: Model | null;
  
  // UI State
  loading: {
    list: boolean;
    details: boolean;
    performance: boolean;
    comparison: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    save: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    provider: string | null;
    tier: 'all' | 'premium' | 'standard' | 'economy';
    status: 'all' | 'enabled' | 'disabled';
  };
  
  // Sorting
  sortBy: 'name' | 'success_rate' | 'latency' | 'cost' | 'requests';
  sortOrder: 'asc' | 'desc';
  
  // Edit Mode
  editMode: boolean;
  editForm: Partial<UpdateModelRequest> | null;
  
  // Performance View
  performancePeriod: '1h' | '24h' | '7d' | '30d';
  performanceData: GetModelPerformanceResponse['data'] | null;
  
  // Comparison
  comparisonMode: boolean;
  selectedForComparison: string[];
  comparisonResult: CompareModelsResponse['data'] | null;
  
  // Expanded Providers
  expandedProviders: string[];
}

interface ModelTableProps {
  models: Model[];
  groupBy: 'provider' | 'tier' | 'none';
  expandedGroups: string[];
  onToggleGroup: (group: string) => void;
  onSelectModel: (model: Model) => void;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  selectedId?: string;
  comparisonMode?: boolean;
  selectedForComparison?: string[];
  onToggleComparison?: (id: string) => void;
  loading?: boolean;
}

interface ModelDetailPanelProps {
  model: Model;
  activeTab: 'overview' | 'configuration' | 'agents' | 'performance' | 'costs';
  onTabChange: (tab: string) => void;
  onEdit: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  performanceData?: GetModelPerformanceResponse['data'];
  loading?: boolean;
}

interface ModelConfigEditorProps {
  model: Model;
  onSave: (data: UpdateModelRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}

interface ModelComparisonPanelProps {
  modelIds: string[];
  data: CompareModelsResponse['data'] | null;
  onRemoveModel: (id: string) => void;
  onClearAll: () => void;
  onExport: () => void;
  loading?: boolean;
}

interface TierBadgeProps {
  tier: 'premium' | 'standard' | 'economy';
  size?: 'sm' | 'md' | 'lg';
}

// Renders:
// ⭐ Premium (gold)
// 📊 Standard (blue)
// 💰 Economy (green)

const modelsAnimations = {
  // Provider group expand
  groupExpand: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    exit: { height: 0, opacity: 0 },
    transition: { duration: 0.3 }
  },
  
  // Model row hover
  rowHover: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    transition: { duration: 0.15 }
  },
  
  // Status toggle
  statusToggle: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3 }
  },
  
  // Comparison select
  comparisonSelect: {
    scale: [1, 1.05, 1],
    borderColor: ['#334155', '#3B82F6', '#3B82F6'],
    transition: { duration: 0.2 }
  },
  
  // Slider thumb
  sliderThumb: {
    scale: 1.2,
    boxShadow: '0 0 0 4px rgba(59, 130, 246, 0.2)',
    transition: { duration: 0.15 }
  },
  
  // Comparison panel
  comparisonPanel: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: { duration: 0.3 }
  },
  
  // Winner badge
  winnerBadge: {
    scale: [0, 1.2, 1],
    rotate: [0, 10, 0],
    transition: { duration: 0.5, type: 'spring' }
  }
};

const modelsShortcuts = {
  'mod+f': 'Focus search',
  'mod+n': 'Add new model',
  'mod+e': 'Edit selected model',
  'c': 'Toggle comparison mode',
  'space': 'Toggle model in comparison',
  'up/down': 'Navigate models',
  'enter': 'Expand/select model',
  'escape': 'Exit comparison/close panel',
  '1/2/3': 'Switch tabs (overview/config/performance)',
};

const modelErrorCodes = {
  // Validation
  MODEL_VAL_001: 'Temperature must be between 0 and 2',
  MODEL_VAL_002: 'Max tokens exceeds model limit',
  MODEL_VAL_003: 'Invalid top-p value',
  MODEL_VAL_004: 'Cost limit must be positive',
  
  // Business Logic
  MODEL_BUS_001: 'Cannot disable last enabled model for agent',
  MODEL_BUS_002: 'Model not available for this provider',
  MODEL_BUS_003: 'Cost limit exceeded',
  
  // System
  MODEL_SYS_001: 'Failed to load models',
  MODEL_SYS_002: 'Failed to update model configuration',
  MODEL_SYS_003: 'Failed to load performance data',
};

// GET /admin/llm/rankings?agent_type=swap_agent
// Get current rankings

interface GetRankingsResponse {
  success: true;
  data: {
    rankings: AgentRanking[];
    config: RankingConfig;
    last_calculated_at: string;
    next_calculation_at: string;
  };
}

interface AgentRanking {
  agent_type: string;
  agent_display_name: string;
  models: RankedModel[];
  override_active: boolean;
  override_expires_at?: string;
}

interface RankedModel {
  model_id: string;
  model_name: string;
  provider_name: string;
  rank: number;
  score: number;
  factors: {
    success_rate: number;
    success_score: number;
    latency_ms: number;
    latency_score: number;
    cost_efficiency: number;
    cost_score: number;
  };
  is_pinned: boolean;
  pin_reason?: string;
  pin_expires_at?: string;
  request_count: number;
}

interface RankingConfig {
  weights: {
    success: number;
    latency: number;
    cost: number;
  };
  lookback_hours: number;
  min_requests: number;
  recalculation_interval_minutes: number;
  smoothing_factor: number;
}

// PUT /admin/llm/rankings/config
// Update ranking configuration

interface UpdateRankingConfigRequest {
  weights?: {
    success?: number;
    latency?: number;
    cost?: number;
  };
  lookback_hours?: number;
  min_requests?: number;
  recalculation_interval_minutes?: number;
  smoothing_factor?: number;
}

// POST /admin/llm/rankings/override
// Create ranking override

interface CreateOverrideRequest {
  agent_type: string;
  model_id: string;
  pin_position: number;
  duration_hours: number | null;  // null = permanent
  reason: string;
}

interface CreateOverrideResponse {
  success: true;
  data: {
    override_id: string;
    expires_at: string | null;
    previous_ranking: RankedModel[];
    new_ranking: RankedModel[];
  };
}

// POST /admin/llm/rankings/recalculate
// Trigger ranking recalculation

interface RecalculateRequest {
  agent_types?: string[];  // Empty = all
}

interface RecalculateResponse {
  success: true;
  data: {
    job_id: string;
    agents_to_process: number;
    estimated_seconds: number;
  };
}

interface RankingsModuleState {
  rankings: AgentRanking[];
  config: RankingConfig | null;
  selectedAgent: string | null;
  
  loading: {
    rankings: boolean;
    config: boolean;
    recalculate: boolean;
    override: boolean;
  };
  
  configModalOpen: boolean;
  overrideModalOpen: boolean;
  overrideForm: Partial<CreateOverrideRequest>;
  
  historyModalOpen: boolean;
  historyData: RankingHistory | null;
  
  filters: {
    agentType: string | null;
  };
}

interface RankingTableProps {
  ranking: AgentRanking;
  onViewHistory: () => void;
  onRecalculate: () => void;
  onOverride: (modelId: string) => void;
  onRemoveOverride: (modelId: string) => void;
}

interface RankingBarProps {
  score: number;
  maxScore: number;
  color?: string;
  showLabel?: boolean;
}

interface OverrideModalProps {
  agentType: string;
  currentRankings: RankedModel[];
  onSubmit: (data: CreateOverrideRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}

const rankingsAnimations = {
  rankChange: {
    y: [0, -10, 0],
    transition: { duration: 0.3 }
  },
  
  pinIndicator: {
    scale: [1, 1.2, 1],
    rotate: [0, 10, 0],
    transition: { duration: 0.5 }
  },
  
  scoreBarFill: {
    width: '100%',
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  recalculateSpinner: {
    rotate: 360,
    transition: { duration: 1, repeat: Infinity, ease: 'linear' }
  }
};

const rankingsShortcuts = {
  'mod+r': 'Recalculate all rankings',
  'mod+o': 'Create override',
  'mod+c': 'Open configuration',
  'h': 'View history',
  '1-6': 'Filter by agent type',
};

const rankingsErrorCodes = {
  RANK_VAL_001: 'Weights must sum to 100%',
  RANK_VAL_002: 'Override reason is required',
  RANK_VAL_003: 'Invalid pin position',
  RANK_BUS_001: 'Model has insufficient data for ranking',
  RANK_BUS_002: 'Override conflicts with existing override',
  RANK_SYS_001: 'Recalculation job failed',
};

// GET /admin/llm/telemetry/overview?period=24h
// Get telemetry overview

interface GetTelemetryOverviewResponse {
  success: true;
  data: {
    period: string;
    summary: {
      total_requests: number;
      success_rate: number;
      error_count: number;
      avg_latency_ms: number;
      total_cost_usd: number;
      total_tokens: number;
    };
    timeseries: {
      requests: TimeSeriesPoint[];
      success_rate: TimeSeriesPoint[];
      latency_p50: TimeSeriesPoint[];
      latency_p95: TimeSeriesPoint[];
      cost: TimeSeriesPoint[];
    };
    by_provider: Record<string, ProviderMetrics>;
    by_model: Record<string, ModelMetrics>;
    by_agent: Record<string, AgentMetrics>;
  };
}

// GET /admin/llm/telemetry/latency?period=7d
// Get latency analysis

interface GetLatencyAnalysisResponse {
  success: true;
  data: {
    percentiles: {
      p50: number;
      p75: number;
      p90: number;
      p95: number;
      p99: number;
    };
    distribution: Array<{
      bucket_ms: number;
      count: number;
    }>;
    by_provider: Record<string, LatencyBreakdown>;
    by_model: Record<string, LatencyBreakdown>;
    heatmap: Array<{
      day: string;
      hour: number;
      avg_latency_ms: number;
    }>;
    timeseries: {
      p50: TimeSeriesPoint[];
      p95: TimeSeriesPoint[];
      p99: TimeSeriesPoint[];
    };
  };
}

// GET /admin/llm/telemetry/errors?period=24h
// Get error analysis

interface GetErrorAnalysisResponse {
  success: true;
  data: {
    summary: {
      total_errors: number;
      error_rate: number;
      most_common: string;
    };
    timeseries: TimeSeriesPoint[];
    by_type: Record<string, number>;
    by_provider: Record<string, number>;
    by_model: Record<string, number>;
    error_groups: Array<{
      group_id: string;
      description: string;
      count: number;
      first_seen: string;
      last_seen: string;
      status: 'ongoing' | 'resolved' | 'recurring';
      affected_providers: string[];
    }>;
    spikes: Array<{
      timestamp: string;
      error_rate: number;
      duration_minutes: number;
      root_cause?: string;
    }>;
  };
}

interface TelemetryModuleState {
  overview: TelemetryOverview | null;
  latencyAnalysis: LatencyAnalysis | null;
  errorAnalysis: ErrorAnalysis | null;
  costAnalysis: CostAnalysis | null;
  
  loading: {
    overview: boolean;
    latency: boolean;
    errors: boolean;
    cost: boolean;
  };
  
  activeTab: 'overview' | 'performance' | 'costs' | 'errors' | 'custom';
  
  timeRange: {
    preset: '1h' | '24h' | '7d' | '30d' | 'custom';
    start?: string;
    end?: string;
  };
  
  autoRefresh: boolean;
  refreshInterval: number;
  
  fullscreenMode: boolean;
  
  customDashboard: {
    widgets: Widget[];
    layout: LayoutConfig;
  };
}

interface TimeSeriesChartProps {
  data: TimeSeriesPoint[];
  type: 'line' | 'area' | 'bar';
  color?: string;
  yAxisLabel?: string;
  showTooltip?: boolean;
  showGrid?: boolean;
  height?: number;
}

interface LatencyHeatmapProps {
  data: HeatmapPoint[];
  colorScale: 'sequential' | 'diverging';
  onCellClick?: (day: string, hour: number) => void;
}

interface ErrorGroupTableProps {
  groups: ErrorGroup[];
  onViewDetails: (groupId: string) => void;
  onAcknowledge: (groupId: string) => void;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    direction: 'up' | 'down';
    isPositive: boolean;
  };
  sparkline?: number[];
  icon?: React.ReactNode;
}

const telemetryAnimations = {
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1, ease: 'easeOut' }
  },
  
  metricCount: {
    opacity: [0, 1],
    y: [20, 0],
    transition: { duration: 0.5 }
  },
  
  heatmapCell: {
    opacity: [0, 1],
    scale: [0.8, 1],
    transition: { duration: 0.2 }
  },
  
  refreshPulse: {
    opacity: [1, 0.5, 1],
    transition: { duration: 1, repeat: Infinity }
  }
};

const telemetryShortcuts = {
  'mod+r': 'Refresh data',
  'f': 'Toggle fullscreen',
  '1-5': 'Switch tabs',
  '[/]': 'Previous/Next time range',
  'mod+e': 'Export data',
};

const telemetryErrorCodes = {
  TELEM_LOAD_001: 'Failed to load telemetry data',
  TELEM_RANGE_001: 'Invalid time range',
  TELEM_EXPORT_001: 'Export failed',
  TELEM_WS_001: 'Real-time connection lost',
};

// GET /admin/llm/circuit-breakers
// Get all circuit breaker states

interface GetCircuitBreakersResponse {
  success: true;
  data: {
    breakers: CircuitBreaker[];
    summary: {
      closed: number;
      half_open: number;
      open: number;
    };
  };
}

interface CircuitBreaker {
  id: string;
  provider_id: string;
  provider_name: string;
  state: 'closed' | 'half_open' | 'open';
  state_changed_at: string;
  current_failures: number;
  current_successes: number;
  failure_rate: number;
  config: CircuitBreakerConfig;
  last_error?: {
    message: string;
    code: number;
    timestamp: string;
  };
  half_open_progress?: {
    successes: number;
    required: number;
  };
  recovery_at?: string;
}

interface CircuitBreakerConfig {
  failure_count_threshold: number;
  failure_rate_threshold: number;
  failure_rate_window_seconds: number;
  min_sample_size: number;
  recovery_timeout_seconds: number;
  half_open_max_requests: number;
  half_open_success_threshold: number;
  count_rate_limits: boolean;
}

// PUT /admin/llm/circuit-breakers/{id}/config
// Update configuration

interface UpdateCircuitBreakerConfigRequest {
  failure_count_threshold?: number;
  failure_rate_threshold?: number;
  failure_rate_window_seconds?: number;
  recovery_timeout_seconds?: number;
  half_open_success_threshold?: number;
}

// POST /admin/llm/circuit-breakers/{id}/control
// Manual open/close/reset

interface ControlCircuitBreakerRequest {
  action: 'open' | 'close' | 'reset';
  reason: string;
}

interface ControlCircuitBreakerResponse {
  success: true;
  data: {
    breaker: CircuitBreaker;
    previous_state: string;
    new_state: string;
  };
}

// GET /admin/llm/circuit-breakers/{id}/history?days=30
// Get trip history

interface GetTripHistoryResponse {
  success: true;
  data: {
    breaker_id: string;
    period_days: number;
    summary: {
      total_trips: number;
      avg_duration_seconds: number;
      availability_pct: number;
    };
    events: Array<{
      id: string;
      started_at: string;
      ended_at?: string;
      duration_seconds?: number;
      trigger_reason: string;
      error_count: number;
      recovery_type: 'auto' | 'manual';
    }>;
    timeline: Array<{
      timestamp: string;
      state: string;
    }>;
  };
}

interface CircuitBreakersState {
  breakers: CircuitBreaker[];
  summary: BreakersSummary;
  selectedBreaker: CircuitBreaker | null;
  
  loading: {
    list: boolean;
    config: boolean;
    control: boolean;
    history: boolean;
  };
  
  configModalOpen: boolean;
  configForm: Partial<CircuitBreakerConfig>;
  
  historyModalOpen: boolean;
  historyData: GetTripHistoryResponse['data'] | null;
  
  controlModalOpen: boolean;
  controlAction: 'open' | 'close' | 'reset' | null;
}

interface CircuitBreakerCardProps {
  breaker: CircuitBreaker;
  onForceOpen: () => void;
  onForceClose: () => void;
  onViewHistory: () => void;
  onConfigure: () => void;
}

interface BreakerStateIndicatorProps {
  state: 'closed' | 'half_open' | 'open';
  progress?: { current: number; total: number };
  animated?: boolean;
}

interface TripTimelineProps {
  events: TripEvent[];
  period: string;
  onEventClick?: (eventId: string) => void;
}

const circuitBreakerAnimations = {
  stateChange: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.3 }
  },
  
  openPulse: {
    boxShadow: ['0 0 0 0 rgba(239, 68, 68, 0.4)', '0 0 0 10px rgba(239, 68, 68, 0)', '0 0 0 0 rgba(239, 68, 68, 0)'],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  halfOpenProgress: {
    width: '100%',
    transition: { duration: 0.3 }
  },
  
  recoveryCountdown: {
    strokeDashoffset: 0,
    transition: { duration: 1, ease: 'linear' }
  }
};

const circuitBreakerShortcuts = {
  'mod+r': 'Refresh states',
  'o': 'Force open selected',
  'c': 'Force close selected',
  'h': 'View history',
  's': 'Configure settings',
};

const circuitBreakerErrorCodes = {
  CB_LOAD_001: 'Failed to load circuit breakers',
  CB_CTRL_001: 'Failed to change breaker state',
  CB_CONF_001: 'Invalid configuration values',
  CB_HIST_001: 'Failed to load history',
};

// GET /admin/llm/requests
// Get paginated request logs

interface GetRequestsRequest {
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
  provider_id?: string;
  model_id?: string;
  agent_type?: string;
  status?: 'success' | 'error' | 'timeout';
  search?: string;
}

interface GetRequestsResponse {
  success: true;
  data: {
    requests: LLMRequest[];
    pagination: {
      page: number;
      page_size: number;
      total: number;
      total_pages: number;
    };
    summary: {
      total_requests: number;
      success_count: number;
      error_count: number;
      avg_latency_ms: number;
    };
  };
}

interface LLMRequest {
  id: string;
  timestamp: string;
  provider_id: string;
  provider_name: string;
  model_id: string;
  model_name: string;
  agent_type: string;
  status: 'success' | 'error' | 'timeout';
  status_code: number;
  latency_ms: number;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  cost_usd: number;
  error_message?: string;
  had_fallback: boolean;
  fallback_chain?: FallbackAttempt[];
  user_id?: string;
  session_id?: string;
}

interface FallbackAttempt {
  provider_name: string;
  model_name: string;
  status: string;
  status_code: number;
  latency_ms: number;
  error_message?: string;
}

// GET /admin/llm/requests/{id}
// Get full request details

interface GetRequestDetailResponse {
  success: true;
  data: {
    request: LLMRequest;
    payload: {
      messages: Array<{
        role: string;
        content: string;
      }>;
      temperature?: number;
      max_tokens?: number;
      // ... other params
    };
    response: {
      content: string;
      finish_reason: string;
      usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
      };
    };
    timing: {
      queue_ms: number;
      inference_ms: number;
      network_ms: number;
      total_ms: number;
    };
    context: {
      user_id?: string;
      session_id?: string;
      project_id?: string;
      ip_address?: string;
    };
    routing: {
      selected_model: string;
      ranking_score: number;
      ranking_position: number;
    };
  };
}

// POST /admin/llm/requests/export
// Export request logs

interface ExportRequestsRequest {
  start_date: string;
  end_date: string;
  format: 'csv' | 'json';
  fields?: string[];
  redact_pii?: boolean;
  filters?: {
    provider_id?: string;
    status?: string;
  };
}

interface ExportRequestsResponse {
  success: true;
  data: {
    export_id: string;
    estimated_rows: number;
    estimated_size_mb: number;
    status: 'processing';
  };
}

interface RequestsModuleState {
  requests: LLMRequest[];
  selectedRequest: GetRequestDetailResponse['data'] | null;
  
  loading: {
    list: boolean;
    detail: boolean;
    export: boolean;
  };
  
  streaming: boolean;
  streamPaused: boolean;
  
  filters: {
    dateRange: { start: string; end: string };
    provider: string | null;
    model: string | null;
    agent: string | null;
    status: string | null;
    search: string;
  };
  
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  
  summary: RequestsSummary | null;
  
  detailModalOpen: boolean;
  exportModalOpen: boolean;
}

interface RequestTableProps {
  requests: LLMRequest[];
  onSelectRequest: (id: string) => void;
  selectedId?: string;
  streaming?: boolean;
  loading?: boolean;
}

interface RequestDetailModalProps {
  request: GetRequestDetailResponse['data'];
  onClose: () => void;
  onReplay: () => void;
}

interface FallbackChainVisualizationProps {
  attempts: FallbackAttempt[];
  finalStatus: string;
}

interface RequestStreamIndicatorProps {
  streaming: boolean;
  paused: boolean;
  requestsPerSecond: number;
  onTogglePause: () => void;
}

const requestsAnimations = {
  newRequestSlide: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.2 }
  },
  
  statusPulse: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3 }
  },
  
  fallbackArrow: {
    pathLength: [0, 1],
    transition: { duration: 0.5 }
  },
  
  streamIndicator: {
    opacity: [1, 0.5, 1],
    transition: { duration: 1, repeat: Infinity }
  }
};

const requestsShortcuts = {
  'space': 'Toggle stream pause',
  'mod+e': 'Export requests',
  'mod+f': 'Focus search',
  'enter': 'View request detail',
  'escape': 'Close detail modal',
  'j/k': 'Navigate requests',
};

const requestsErrorCodes = {
  REQ_LOAD_001: 'Failed to load requests',
  REQ_DETAIL_001: 'Request not found',
  REQ_EXPORT_001: 'Export failed',
  REQ_EXPORT_002: 'Date range too large',
  REQ_STREAM_001: 'WebSocket connection lost',
};

// GET /admin/llm/providers
// Get all providers with optional filters

interface GetProvidersRequest {
  status?: 'healthy' | 'degraded' | 'down';
  is_enabled?: boolean;
}

interface GetProvidersResponse {
  success: true;
  data: {
    providers: Provider[];
    total: number;
  };
}

interface Provider {
  id: string;
  name: string;                    // "vertex_ai"
  display_name: string;            // "Google Vertex AI"
  description: string;
  icon_url: string;
  priority: number;
  is_enabled: boolean;
  health_status: 'healthy' | 'degraded' | 'down';
  health_check_latency_ms: number;
  last_health_check: string;
  config: ProviderConfig;
  rate_limits: RateLimits;
  cost_controls: CostControls;
  models: ProviderModel[];
  stats_24h: ProviderStats;
  created_at: string;
  updated_at: string;
}

interface ProviderConfig {
  project_id?: string;           // Vertex AI
  location?: string;             // Vertex AI
  api_key?: string;              // DeepInfra (masked)
  region?: string;               // Bedrock
  endpoint_url?: string;
}

interface RateLimits {
  requests_per_minute: number;
  tokens_per_minute: number;
  concurrent_requests: number;
}

interface CostControls {
  daily_limit_usd: number | null;
  alert_threshold_pct: number;
}

interface ProviderStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_cost_usd: number;
}

// PUT /admin/llm/providers/{id}
// Update provider configuration

interface UpdateProviderRequest {
  display_name?: string;
  priority?: number;
  is_enabled?: boolean;
  config?: Partial<ProviderConfig>;
  rate_limits?: Partial<RateLimits>;
  cost_controls?: Partial<CostControls>;
}

// Validation
const updateProviderValidation = {
  display_name: {
    required: false,
    minLength: 2,
    maxLength: 100
  },
  priority: {
    required: false,
    min: 1,
    max: 10
  },
  'rate_limits.requests_per_minute': {
    required: false,
    min: 1,
    max: 10000
  },
  'cost_controls.daily_limit_usd': {
    required: false,
    min: 0,
    max: 10000
  }
};

interface UpdateProviderResponse {
  success: true;
  data: {
    provider: Provider;
    changes: Array<{
      field: string;
      old_value: any;
      new_value: any;
    }>;
  };
}

// POST /admin/llm/providers/{id}/health-check
// Trigger manual health check

interface HealthCheckResponse {
  success: true;
  data: {
    provider_id: string;
    provider_name: string;
    status: 'healthy' | 'degraded' | 'down';
    latency_ms: number;
    endpoints_checked: Array<{
      endpoint: string;
      status: 'ok' | 'error';
      latency_ms: number;
      error?: string;
    }>;
    models_checked: Array<{
      model_id: string;
      status: 'ok' | 'error';
      latency_ms: number;
      error?: string;
    }>;
    checked_at: string;
  };
}

// GET /admin/llm/providers/{id}/performance?period=24h
// Get detailed performance metrics

interface GetProviderPerformanceRequest {
  period: '1h' | '24h' | '7d' | '30d';
}

interface GetProviderPerformanceResponse {
  success: true;
  data: {
    provider_id: string;
    period: string;
    summary: ProviderStats;
    latency_percentiles: {
      p50: number;
      p75: number;
      p90: number;
      p95: number;
      p99: number;
    };
    error_breakdown: Record<string, number>;
    model_breakdown: Array<{
      model_id: string;
      model_name: string;
      requests: number;
      success_rate: number;
      avg_latency_ms: number;
      p95_latency_ms: number;
      cost_usd: number;
    }>;
    timeseries: {
      latency: TimeSeriesPoint[];
      requests: TimeSeriesPoint[];
      errors: TimeSeriesPoint[];
    };
  };
}

// PUT /admin/llm/providers/priorities
// Batch update provider priorities

interface UpdatePrioritiesRequest {
  priorities: Array<{
    provider_id: string;
    priority: number;
  }>;
}

interface UpdatePrioritiesResponse {
  success: true;
  data: {
    updated: Array<{
      provider_id: string;
      old_priority: number;
      new_priority: number;
    }>;
  };
}

interface ProvidersModuleState {
  // Data
  providers: Provider[];
  selectedProvider: Provider | null;
  
  // UI State
  loading: {
    list: boolean;
    details: boolean;
    healthCheck: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    details: Error | null;
    healthCheck: Error | null;
    save: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    status: 'all' | 'healthy' | 'degraded' | 'down';
  };
  
  // Sorting
  sortBy: 'priority' | 'name' | 'status' | 'latency';
  sortOrder: 'asc' | 'desc';
  
  // Edit State
  editMode: boolean;
  editForm: Partial<UpdateProviderRequest> | null;
  hasUnsavedChanges: boolean;
  
  // Priority Reordering
  isReordering: boolean;
  pendingPriorities: Array<{ provider_id: string; priority: number }>;
  
  // Performance View
  performancePeriod: '1h' | '24h' | '7d' | '30d';
  performanceData: GetProviderPerformanceResponse['data'] | null;
  
  // Health Check
  lastHealthCheckResult: HealthCheckResponse['data'] | null;
  
  // Tab Navigation
  activeTab: 'overview' | 'models' | 'performance' | 'configuration' | 'logs';
}

interface ProviderTableProps {
  providers: Provider[];
  onSelect: (provider: Provider) => void;
  onReorder: (newOrder: string[]) => void;
  selectedId?: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSort: (column: string) => void;
  loading?: boolean;
}

// Usage
<ProviderTable
  providers={providers}
  onSelect={handleSelectProvider}
  onReorder={handleReorderProviders}
  selectedId={selectedProvider?.id}
  sortBy={sortBy}
  sortOrder={sortOrder}
  onSort={handleSort}
  loading={loading.list}
/>

interface ProviderDetailPanelProps {
  provider: Provider;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onEdit: () => void;
  onHealthCheck: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  performanceData?: GetProviderPerformanceResponse['data'];
  healthCheckResult?: HealthCheckResponse['data'];
  loading?: boolean;
}

interface ProviderEditFormProps {
  provider: Provider;
  onSave: (data: UpdateProviderRequest) => void;
  onCancel: () => void;
  onTestConnection: () => Promise<void>;
  loading?: boolean;
  connectionTestResult?: { success: boolean; latency_ms: number };
}

interface PriorityReorderListProps {
  items: Array<{ id: string; name: string; priority: number }>;
  onReorder: (newOrder: string[]) => void;
  onSave: () => void;
  onCancel: () => void;
  hasChanges: boolean;
}

interface HealthCheckResultCardProps {
  result: HealthCheckResponse['data'];
  onRecheck: () => void;
  loading?: boolean;
}

const providersAnimations = {
  // Row reorder
  rowReorder: {
    layout: true,
    transition: { type: 'spring', stiffness: 300, damping: 30 }
  },
  
  // Status change
  statusChange: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3 }
  },
  
  // Detail panel slide
  detailPanelEnter: {
    initial: { opacity: 0, height: 0 },
    animate: { opacity: 1, height: 'auto' },
    exit: { opacity: 0, height: 0 },
    transition: { duration: 0.3 }
  },
  
  // Edit slide-over
  editSlideOver: {
    initial: { x: '100%' },
    animate: { x: 0 },
    exit: { x: '100%' },
    transition: { type: 'spring', stiffness: 300, damping: 30 }
  },
  
  // Health check loading
  healthCheckSpinner: {
    rotate: 360,
    transition: { duration: 1, repeat: Infinity, ease: 'linear' }
  },
  
  // Connection test success
  connectionSuccess: {
    scale: [1, 1.05, 1],
    borderColor: ['#334155', '#10B981', '#334155'],
    transition: { duration: 0.5 }
  },
  
  // Priority drag
  dragActive: {
    scale: 1.02,
    boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
    zIndex: 1000
  }
};

const providersShortcuts = {
  'mod+n': 'Add new provider',
  'mod+e': 'Edit selected provider',
  'mod+h': 'Health check selected',
  'mod+shift+h': 'Health check all',
  'up/down': 'Navigate providers',
  'enter': 'Expand/select provider',
  'escape': 'Close edit panel',
  'mod+s': 'Save changes',
  'd': 'Toggle provider enabled/disabled',
};

const providerErrorCodes = {
  // Validation
  PROV_VAL_001: 'Provider name is required',
  PROV_VAL_002: 'Invalid priority value',
  PROV_VAL_003: 'Invalid rate limit configuration',
  PROV_VAL_004: 'API key format is invalid',
  
  // Business Logic
  PROV_BUS_001: 'Cannot disable all providers',
  PROV_BUS_002: 'Cannot delete provider with active requests',
  PROV_BUS_003: 'Priority conflict detected',
  
  // Connection
  PROV_CON_001: 'Failed to connect to provider',
  PROV_CON_002: 'Authentication failed',
  PROV_CON_003: 'Provider rate limit exceeded',
  PROV_CON_004: 'Health check timed out',
  
  // System
  PROV_SYS_001: 'Failed to save provider configuration',
  PROV_SYS_002: 'Failed to update priorities',
};

// GET /admin/security/fraud
interface GetFraudDashboardResponse {
  success: true;
  data: {
    metrics_24h: {
      flagged: number;
      blocked: number;
      prevented_usd: number;
      fraud_rate: number;
    };
    active_cases: FraudCase[];
    patterns_30d: Record<string, number>;
    detection_by_rule: Record<string, number>;
  };
}

interface FraudCase {
  id: string;
  user_id: string;
  wallet_address?: string;
  email?: string;
  fraud_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  pattern: string;
  amount_at_risk_usd: number;
  transaction_count: number;
  status: 'pending' | 'investigating' | 'confirmed_fraud' | 'false_positive';
  auto_blocked: boolean;
  risk_factors: Array<{ severity: string; description: string }>;
  transactions: FraudTransaction[];
  created_at: string;
}

// GET /admin/security/dashboard
interface GetSecurityDashboardResponse {
  success: true;
  data: {
    threat_level: 'low' | 'elevated' | 'high' | 'critical';
    alerts_by_severity: {
      critical: { total: number; new: number };
      high: { total: number; new: number };
      medium: { total: number; new: number };
      low: { total: number; new: number };
    };
    live_alerts: SecurityAlert[];
    attack_vectors_24h: Record<string, number>;
    blocked_ips_24h: {
      total: number;
      by_country: Record<string, number>;
    };
  };
}

interface SecurityAlert {
  id: string;
  type: 'brute_force' | 'api_abuse' | 'suspicious_login' | 'failed_login' | 'sql_injection' | 'fraud';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  ip_address?: string;
  user_id?: string;
  location?: string;
  auto_action_taken?: string;
  status: 'open' | 'investigating' | 'resolved';
  created_at: string;
}

// POST /admin/security/alerts/{id}/action
interface SecurityAlertActionRequest {
  action: 'investigate' | 'block_ip' | 'block_ip_range' | 'throttle' | 'force_logout' | 'mark_safe' | 'resolve';
  notes?: string;
  duration_hours?: number;
}

// GET /admin/compliance/sanctions
interface GetSanctionsDashboardResponse {
  success: true;
  data: {
    summary: {
      screened_this_month: number;
      confirmed_matches: number;
      pending_review: number;
      clear_rate: number;
    };
    active_matches: SanctionsMatch[];
    lists_status: Array<{
      name: string;
      updated_at: string;
      enabled: boolean;
    }>;
    coverage: {
      wallets: { screened: number; total: number };
      users: { screened: number; total: number };
      last_batch: string;
    };
  };
}

interface SanctionsMatch {
  id: string;
  type: 'wallet' | 'user';
  wallet_address?: string;
  user_id?: string;
  email?: string;
  matched_list: string;
  matched_entity: string;
  match_type: string;
  confidence: number;
  status: 'pending' | 'confirmed' | 'false_positive';
  user_action: 'blocked' | 'pending' | 'none';
  detected_at: string;
}

// POST /admin/compliance/sanctions/{id}/resolve
interface ResolveSanctionsMatchRequest {
  resolution: 'confirmed_match' | 'false_positive';
  notes: string;
  report_to_fincen?: boolean;
}

// GET /admin/compliance/dashboard
interface GetComplianceDashboardResponse {
  success: true;
  data: {
    status: 'healthy' | 'warning' | 'critical';
    alerts: {
      total: number;
      critical: number;
      pending_review: number;
    };
    kyc_rate: number;
    risk_distribution: {
      low: number;
      medium: number;
      high: number;
      critical: number;
    };
    alerts_by_type: Record<string, number>;
    recent_screenings: {
      total: number;
      clear: number;
      review_required: number;
      blocked: number;
      avg_response_ms: number;
    };
    chainalysis_status: {
      connected: boolean;
      last_sync: string;
      api_usage: number;
      api_limit: number;
    };
    critical_alerts: ComplianceAlert[];
  };
}

interface ComplianceAlert {
  id: string;
  type: 'sanctions_match' | 'high_risk' | 'unusual_activity' | 'kyc_expired' | 'large_transaction';
  severity: 'low' | 'medium' | 'high' | 'critical';
  user_id?: string;
  wallet_address?: string;
  description: string;
  confidence_score?: number;
  source: string;
  status: 'pending' | 'investigating' | 'resolved' | 'escalated';
  created_at: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_action?: string;
  resolution_notes?: string;
}

// POST /admin/compliance/alerts/{id}/resolve
interface ResolveAlertRequest {
  action: 'block' | 'suspend' | 'clear' | 'escalate';
  notes: string;
  report_to_fincen?: boolean;
}

// GET /admin/compliance/reports/risk?period=30d
interface GetRiskReportResponse {
  success: true;
  data: {
    period: string;
    summary: {
      total_users_screened: number;
      high_risk_identified: number;
      sanctions_matches: number;
      sars_filed: number;
    };
    trends: {
      risk_scores: TimeSeriesPoint[];
      alerts: TimeSeriesPoint[];
    };
    top_risks: Array<{
      category: string;
      count: number;
      change_pct: number;
    }>;
  };
}

const complianceAnimations = {
  alertPulse: {
    boxShadow: ['0 0 0 0 rgba(239, 68, 68, 0.4)', '0 0 0 10px rgba(239, 68, 68, 0)'],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  riskBar: {
    width: '100%',
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  statusIndicator: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.5 }
  }
};

// GET /admin/billing/invoices
interface GetInvoicesRequest {
  page?: number;
  page_size?: number;
  status?: 'paid' | 'pending' | 'failed' | 'refunded' | 'void';
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  search?: string;
}

interface GetInvoicesResponse {
  success: true;
  data: {
    invoices: Invoice[];
    summary: {
      total_invoices: number;
      total_revenue: number;
      paid_rate: number;
      outstanding: number;
    };
    pagination: Pagination;
  };
}

interface Invoice {
  id: string;
  invoice_number: string;
  user_id: string;
  email: string;
  name?: string;
  status: 'paid' | 'pending' | 'failed' | 'refunded' | 'void';
  amount: number;
  currency: string;
  tax: number;
  total: number;
  line_items: Array<{
    description: string;
    amount: number;
    period_start?: string;
    period_end?: string;
  }>;
  billing_address?: {
    line1: string;
    line2?: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  payment?: {
    method: string;
    last4?: string;
    transaction_id: string;
    paid_at: string;
  };
  created_at: string;
  due_at: string;
  paid_at?: string;
}

// POST /admin/billing/invoices/{id}/refund
interface RefundInvoiceRequest {
  amount?: number; // partial refund, full if not specified
  reason: string;
}

// POST /admin/billing/invoices/{id}/void
interface VoidInvoiceRequest {
  reason: string;
}

// POST /admin/billing/invoices/{id}/send
interface SendInvoiceRequest {
  email?: string; // override default email
}

const invoiceShortcuts = {
  'n': 'New invoice',
  'e': 'Export invoices',
  'd': 'Download PDF',
  '/': 'Search invoices',
};

// GET /admin/billing/dashboard
interface GetBillingDashboardResponse {
  success: true;
  data: {
    metrics: {
      mrr: MetricWithChange;
      arr: MetricWithChange;
      paid_users: MetricWithChange;
      churn_rate: MetricWithChange;
    };
    revenue_trend: TimeSeriesPoint[];
    revenue_by_plan: Array<{
      plan: string;
      amount: number;
      users: number;
      percentage: number;
    }>;
    payment_status: {
      successful: { count: number; percentage: number };
      pending: { count: number; percentage: number };
      failed: { count: number; percentage: number };
    };
    recent_transactions: BillingTransaction[];
  };
}

interface BillingTransaction {
  id: string;
  user_id: string;
  email: string;
  type: 'subscription' | 'upgrade' | 'downgrade' | 'refund';
  amount_usd: number;
  status: 'success' | 'pending' | 'failed';
  payment_method: string;
  created_at: string;
}

interface MetricWithChange {
  value: number;
  change_percent: number;
  change_direction: 'up' | 'down' | 'flat';
}

// GET /admin/billing/payments
interface GetPaymentMethodsResponse {
  success: true;
  data: {
    volume_30d: {
      card: number;
      crypto: number;
      success_rate: number;
      total_fees: number;
    };
    processors: PaymentProcessor[];
    method_breakdown: Record<string, number>;
    failed_recovery: {
      failed_count: number;
      recovery_attempts: number;
      recovered_count: number;
      recovered_amount: number;
      dunning_sent: number;
    };
  };
}

interface PaymentProcessor {
  id: string;
  name: string;
  type: 'card' | 'crypto' | 'bank';
  status: 'connected' | 'disconnected' | 'error';
  volume_30d: number;
  transaction_count: number;
  success_rate: number;
  fee_structure: string;
  total_fees: number;
  supported_methods: string[];
  last_payout?: {
    date: string;
    amount: number;
  };
  next_payout?: {
    date: string;
    estimated_amount: number;
  };
}

// POST /admin/billing/payments/processors/{id}/configure
interface ConfigureProcessorRequest {
  enabled: boolean;
  test_mode?: boolean;
  api_key?: string;
  webhook_secret?: string;
}

// GET /admin/billing/subscriptions
interface GetSubscriptionsResponse {
  success: true;
  data: {
    subscriptions: Subscription[];
    summary: {
      active: number;
      new_30d: number;
      canceled_30d: number;
      renewals_upcoming: number;
    };
    pagination: Pagination;
  };
}

interface Subscription {
  id: string;
  user_id: string;
  email: string;
  plan: 'free' | 'pro' | 'elite';
  status: 'active' | 'trial' | 'canceled' | 'past_due' | 'paused';
  billing_period: 'monthly' | 'annual';
  mrr_contribution: number;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  trial_end?: string;
  created_at: string;
}

// GET /admin/analytics/revenue
interface GetRevenueAnalyticsRequest {
  period?: '30d' | '90d' | '12m' | 'ytd' | 'all';
  compare?: 'previous_period' | 'previous_year' | 'none';
}

interface GetRevenueAnalyticsResponse {
  success: true;
  data: {
    key_metrics: {
      arr: MetricWithChange;
      mrr: MetricWithChange;
      arpu: MetricWithChange;
      ltv: MetricWithChange;
      churn_rate: MetricWithChange;
      churned_mrr: MetricWithChange;
      ltv_cac_ratio: MetricWithChange;
      payback_months: MetricWithChange;
    };
    mrr_trend: TimeSeriesPoint[];
    mrr_breakdown: {
      new: number;
      expansion: number;
      contraction: number;
      churned: number;
      net_new: number;
      total: number;
    };
    revenue_by_plan: Array<{
      plan: string;
      amount: number;
      percentage: number;
      user_count: number;
    }>;
    cohort_retention: Array<{
      cohort: string;
      months: Record<string, number>;
    }>;
    forecast: {
      projected_mrr: TimeSeriesPoint[];
      confidence_low: TimeSeriesPoint[];
      confidence_high: TimeSeriesPoint[];
      projected_arr_12m: number;
      projected_growth_percent: number;
    };
  };
}

interface MetricWithChange {
  value: number;
  change_percent: number;
  change_direction: 'up' | 'down' | 'flat';
  period_comparison: string;
}

const revenueAnimations = {
  metricCounter: {
    textContent: { from: 0, to: 'value' },
    transition: { duration: 1, ease: 'easeOut' }
  },
  
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1.5, ease: 'easeInOut' }
  },
  
  cohortCell: {
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'stagger' }
  }
};

const revenueShortcuts = {
  'r': 'Refresh data',
  'e': 'Export report',
  '1': 'View 30 days',
  '2': 'View 90 days',
  '3': 'View 12 months',
};

// GET /admin/analytics?period=30d
interface GetPlatformAnalyticsResponse {
  success: true;
  data: {
    period: string;
    key_metrics: {
      total_users: MetricWithChange;
      conversations: MetricWithChange;
      transaction_volume_usd: MetricWithChange;
      revenue_usd: MetricWithChange;
    };
    user_growth: {
      timeseries: TimeSeriesPoint[];
      new_users: number;
      churned_users: number;
      net_growth: number;
      growth_rate: number;
    };
    engagement: {
      dau_mau_ratio: number;
      avg_session_minutes: number;
      messages_per_session: number;
      transactions_per_active_user: number;
    };
    transaction_volume: {
      timeseries: TimeSeriesPoint[];
      by_type: Record<string, number>;
    };
    top_projects: {
      by_users: Array<{ name: string; count: number; percentage: number }>;
      by_volume: Array<{ name: string; volume_usd: number; percentage: number }>;
    };
    ai_performance: {
      total_requests: number;
      avg_latency_ms: number;
      success_rate: number;
      cost_breakdown: Record<string, number>;
      distillation_savings_usd: number;
    };
    retention_cohorts: RetentionCohort[];
  };
}

interface MetricWithChange {
  value: number;
  change_pct: number;
  change_direction: 'up' | 'down' | 'flat';
}

interface RetentionCohort {
  cohort: string;
  d1: number;
  d7: number;
  d14: number;
  d30: number;
}

// GET /admin/users/{id}
interface GetUserDetailResponse {
  success: true;
  data: {
    user: UserDetail;
    wallets: WalletInfo[];
    risk_assessment: RiskAssessment;
    stats: UserStats;
    recent_activity: ActivityEvent[];
  };
}

interface UserDetail {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  status: 'active' | 'inactive' | 'suspended' | 'banned';
  suspension_reason?: string;
  suspended_at?: string;
  suspended_by?: string;
  tier: 'free' | 'pro' | 'elite';
  kyc_status: 'verified' | 'pending' | 'not_started' | 'failed';
  kyc_verified_at?: string;
  two_factor_enabled: boolean;
  last_login_at?: string;
  last_login_ip?: string;
  created_at: string;
  signup_source?: string;
}

interface WalletInfo {
  address: string;
  chain: string;
  is_primary: boolean;
  balance_usd: number;
  transaction_count: number;
  first_seen_at: string;
  risk_score?: number;
}

interface RiskAssessment {
  overall_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  factors: Array<{
    name: string;
    status: 'pass' | 'warning' | 'fail';
    detail: string;
  }>;
  chainalysis_score?: string;
  last_checked_at: string;
}

interface UserStats {
  portfolio_value_usd: number;
  transaction_count_30d: number;
  conversation_count_30d: number;
  project_count: number;
  total_volume_usd: number;
}

// GET /admin/users/{id}/transactions
interface GetUserTransactionsResponse {
  success: true;
  data: {
    transactions: UserTransaction[];
    summary: {
      total_count: number;
      total_volume_usd: number;
      by_type: Record<string, number>;
    };
    pagination: Pagination;
  };
}

interface UserTransaction {
  id: string;
  type: 'swap' | 'supply' | 'borrow' | 'repay' | 'withdraw' | 'bridge' | 'stake';
  chain: string;
  timestamp: string;
  amount_usd: number;
  details: string;
  status: 'success' | 'failed' | 'pending';
  tx_hash: string;
  gas_usd?: number;
}

// POST /admin/users/{id}/suspend
interface SuspendUserRequest {
  reason: string;
  notes?: string;
  duration_days?: number;  // null = indefinite
  send_notification?: boolean;
}

// POST /admin/users/{id}/activate
interface ActivateUserRequest {
  notes?: string;
}

const userDetailAnimations = {
  tabSwitch: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.2 }
  },
  
  riskIndicator: {
    scale: [0.8, 1],
    transition: { type: 'spring', stiffness: 300 }
  },
  
  actionConfirm: {
    scale: [1, 0.98, 1],
    transition: { duration: 0.15 }
  }
};

// GET /admin/users
interface GetUsersRequest {
  page?: number;
  page_size?: number;
  status?: 'active' | 'inactive' | 'suspended';
  tier?: 'free' | 'pro' | 'elite';
  project_id?: string;
  chain?: string;
  kyc_status?: 'verified' | 'pending' | 'not_started';
  joined_after?: string;
  joined_before?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

interface GetUsersResponse {
  success: true;
  data: {
    users: PlatformUser[];
    summary: {
      total: number;
      active: number;
      inactive: number;
      suspended: number;
      new_this_week: number;
    };
    pagination: Pagination;
  };
}

interface PlatformUser {
  id: string;
  email: string;
  name?: string;
  status: 'active' | 'inactive' | 'suspended';
  suspension_reason?: string;
  tier: 'free' | 'pro' | 'elite';
  kyc_status: 'verified' | 'pending' | 'not_started';
  wallets: Array<{
    address: string;
    chain: string;
    is_primary: boolean;
  }>;
  projects: string[];
  project_count: number;
  transaction_count: number;
  total_volume_usd: number;
  last_active_at?: string;
  created_at: string;
  signup_source?: string;
}

// GET /admin/users/segments
interface GetUserSegmentsResponse {
  success: true;
  data: {
    by_tier: Record<string, number>;
    by_activity: Record<string, number>;
    by_chain: Record<string, number>;
    by_kyc: Record<string, number>;
    by_source: Record<string, number>;
    growth_timeseries: TimeSeriesPoint[];
  };
}

// POST /admin/users/bulk
interface BulkUserActionRequest {
  user_ids: string[];
  action: 'suspend' | 'activate' | 'send_email' | 'export';
  reason?: string;
  email_template_id?: string;
}

const usersAnimations = {
  rowSelect: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    transition: { duration: 0.15 }
  },
  
  bulkActionBar: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  segmentHover: {
    scale: 1.02,
    transition: { duration: 0.2 }
  }
};

// GET /admin/users/bans
interface GetBansRequest {
  page?: number;
  page_size?: number;
  status?: 'suspended' | 'banned' | 'reinstated';
  reason?: string;
  has_appeal?: boolean;
  appeal_status?: 'pending' | 'approved' | 'denied';
  search?: string;
}

interface GetBansResponse {
  success: true;
  data: {
    bans: UserBan[];
    summary: {
      suspended: number;
      banned: number;
      appeals_pending: number;
      reinstated_today: number;
    };
    pagination: Pagination;
  };
}

interface UserBan {
  id: string;
  user_id: string;
  email: string;
  wallet_address?: string;
  status: 'suspended' | 'banned' | 'reinstated';
  reason: string;
  reason_category: string;
  notes?: string;
  duration_days?: number;
  expires_at?: string;
  created_at: string;
  created_by: string;
  reinstated_at?: string;
  reinstated_by?: string;
  appeal?: BanAppeal;
}

interface BanAppeal {
  id: string;
  status: 'pending' | 'approved' | 'denied';
  message: string;
  submitted_at: string;
  decided_at?: string;
  decided_by?: string;
  decision_notes?: string;
}

// GET /admin/users/bans/appeals
interface GetAppealsResponse {
  success: true;
  data: {
    appeals: AppealWithContext[];
    total_pending: number;
    pagination: Pagination;
  };
}

interface AppealWithContext {
  appeal: BanAppeal;
  ban: UserBan;
  user: {
    id: string;
    email: string;
    account_age_days: number;
    total_volume_usd: number;
    prior_suspensions: number;
    prior_warnings: number;
  };
}

// POST /admin/users/bans/appeals/{id}/decide
interface DecideAppealRequest {
  decision: 'approve' | 'deny';
  reinstatement_type?: 'full' | 'conditional' | 'probationary';
  conditions?: string[];
  probation_days?: number;
  notes: string;
  send_notification?: boolean;
}

// POST /admin/users/bans/{id}/reinstate
interface ReinstateRequest {
  notes: string;
  reinstatement_type: 'full' | 'conditional' | 'probationary';
  conditions?: string[];
}

const bansAnimations = {
  appealCard: {
    y: [10, 0],
    opacity: [0, 1],
    transition: { duration: 0.3 }
  },
  
  statusChange: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.3 }
  },
  
  approveButton: {
    backgroundColor: ['#10B981', '#059669'],
    transition: { duration: 0.2 }
  }
};

const bansShortcuts = {
  'a': 'View appeals',
  'r': 'Reinstate selected',
  '/': 'Focus search',
  'j/k': 'Navigate list',
};

// GET /admin/users/kyc
interface GetKYCDashboardResponse {
  success: true;
  data: {
    summary: {
      verified: number;
      pending: number;
      failed: number;
      expiring_soon: number;
      verification_rate: number;
    };
    pending_review: KYCSubmission[];
    funnel: {
      started: number;
      submitted: number;
      auto_passed: number;
      manual_review: number;
      approved: number;
      failed: number;
    };
    by_tier: Record<string, { count: number; percentage: number }>;
  };
}

interface KYCSubmission {
  id: string;
  user_id: string;
  email: string;
  tier: 'tier_1' | 'tier_2' | 'tier_3';
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  auto_check_result: 'passed' | 'review' | 'failed';
  auto_check_reason?: string;
  documents: KYCDocument[];
  submitted_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
}

interface KYCDocument {
  id: string;
  type: 'passport' | 'drivers_license' | 'id_card' | 'proof_of_address' | 'selfie';
  url: string;
  extracted_data?: Record<string, string>;
  verification_status: 'pending' | 'verified' | 'rejected';
}

// POST /admin/users/kyc/{id}/review
interface ReviewKYCRequest {
  decision: 'approve' | 'reject' | 'request_reupload';
  notes: string;
  rejection_reason?: string;
  documents_to_reupload?: string[];
}

// GET /api/v1/admin/ml/models/performance
interface ModelPerformanceResponse {
  models: Array<{
    name: string;
    version: string;
    status: 'active' | 'training' | 'retired';
    accuracy: number; // 0-1
    predictions_today: number;
    avg_confidence: number; // 0-1
    last_updated: string;
  }>;
  alerts: Array<{
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
    message: string;
    model_name: string;
  }>;
}

// GET /api/v1/admin/ml/models/:name/features
interface FeatureImportanceResponse {
  model_name: string;
  model_version: string;
  features: Array<{
    rank: number;
    name: string;
    weight: number; // 0-1
    change_from_previous: number;
    description: string;
  }>;
  total_features: number;
}

// POST /api/v1/admin/ml/models/:name/retrain
interface RetrainRequest {
  hyperparameters?: Record<string, any>;
  training_data_filter?: {
    start_date?: string;
    end_date?: string;
    min_protocols?: number;
  };
}

interface RetrainResponse {
  job_id: string;
  status: 'queued' | 'running';
  estimated_duration_minutes: number;
  started_at: string;
}

// GET /api/v1/admin/ml/predictions/audit?limit=100
interface PredictionAuditResponse {
  predictions: Array<{
    id: string;
    protocol_id: string;
    protocol_name: string;
    predicted_risk: number;
    confidence: number;
    actual_risk?: number; // If available
    prediction_error?: number;
    predicted_at: string;
    model_version: string;
  }>;
  statistics: {
    total_predictions: number;
    avg_error: number;
    accuracy: number;
  };
}

interface MLDashboardProps {
  refreshInterval?: number;
}

interface ModelPerformanceChartProps {
  modelName: string;
  timeRange: '7d' | '30d' | '90d' | '1y';
  metrics: Array<{
    timestamp: string;
    accuracy: number;
    confidence: number;
  }>;
}

interface FeatureImportanceTableProps {
  features: FeatureImportance[];
  onExport: () => void;
}

interface AnomalyThresholdControlsProps {
  thresholds: Record<string, number>;
  recommended: Record<string, number>;
  onApply: (metric: string, value: number) => void;
}

interface ModelRetrainingDialogProps {
  modelName: string;
  currentVersion: string;
  estimatedDuration: number;
  onTrigger: (params: RetrainRequest) => void;
}

const mlAdminErrors = {
  ML_ADMIN_001: 'Model not found',
  ML_ADMIN_002: 'Retraining already in progress',
  ML_ADMIN_003: 'Invalid hyperparameters',
  ML_ADMIN_004: 'Insufficient training data',
  ML_ADMIN_005: 'Model performance degraded below threshold',
};

// GET /admin/notifications
interface GetNotificationsResponse {
  success: true;
  data: {
    stats_24h: {
      sent: number;
      delivery_rate: number;
      open_rate: number;
      click_rate: number;
    };
    recent: NotificationCampaign[];
    scheduled: NotificationCampaign[];
    channels: NotificationChannel[];
  };
}

interface NotificationCampaign {
  id: string;
  type: 'email' | 'push' | 'in_app';
  subject: string;
  message: string;
  cta_text?: string;
  cta_url?: string;
  audience: {
    type: 'all' | 'segment' | 'specific';
    segment_id?: string;
    user_ids?: string[];
  };
  status: 'draft' | 'scheduled' | 'sending' | 'sent';
  scheduled_at?: string;
  sent_at?: string;
  stats?: {
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    unsubscribed?: number;
  };
}

// POST /admin/notifications
interface CreateNotificationRequest {
  type: 'email' | 'push' | 'in_app';
  subject: string;
  message: string;
  cta_text?: string;
  cta_url?: string;
  audience: {
    type: 'all' | 'segment' | 'specific';
    segment_id?: string;
    user_ids?: string[];
  };
  send_immediately?: boolean;
  scheduled_at?: string;
}

// GET /admin/announcements
interface GetAnnouncementsResponse {
  success: true;
  data: {
    active: Announcement[];
    scheduled: Announcement[];
    expired: Announcement[];
    drafts: Announcement[];
  };
}

interface Announcement {
  id: string;
  type: 'banner' | 'modal' | 'toast' | 'in_feed';
  style: 'info' | 'success' | 'warning' | 'error' | 'promo';
  title: string;
  message: string;
  button_text?: string;
  button_url?: string;
  audience: {
    type: 'all' | 'segment' | 'specific';
    segment_id?: string;
    user_ids?: string[];
  };
  dismissible: boolean;
  show_once: boolean;
  status: 'draft' | 'active' | 'scheduled' | 'expired';
  start_at: string;
  end_at?: string;
  stats?: {
    views: number;
    clicks: number;
    dismissals: number;
  };
  created_at: string;
  created_by: string;
}

// POST /admin/announcements
interface CreateAnnouncementRequest {
  type: 'banner' | 'modal' | 'toast' | 'in_feed';
  style: 'info' | 'success' | 'warning' | 'error' | 'promo';
  title: string;
  message: string;
  button_text?: string;
  button_url?: string;
  audience: {
    type: 'all' | 'segment' | 'specific';
    segment_id?: string;
    user_ids?: string[];
  };
  dismissible?: boolean;
  show_once?: boolean;
  start_at?: string;
  end_at?: string;
  publish_now?: boolean;
}

// POST /admin/announcements/{id}/end
interface EndAnnouncementRequest {
  notes?: string;
}

// GET /admin/notifications/templates
interface GetTemplatesResponse {
  success: true;
  data: {
    templates: EmailTemplate[];
    categories: string[];
  };
}

interface EmailTemplate {
  id: string;
  name: string;
  slug: string;
  category: 'transactional' | 'billing' | 'security' | 'marketing';
  trigger: string;
  status: 'active' | 'draft' | 'disabled';
  subject: string;
  from_name: string;
  from_email: string;
  body_html: string;
  body_text?: string;
  variables: Array<{
    name: string;
    description: string;
    example: string;
  }>;
  stats_30d?: {
    sent: number;
    open_rate: number;
    click_rate: number;
  };
  updated_at: string;
  updated_by: string;
}

// PUT /admin/notifications/templates/{id}
interface UpdateTemplateRequest {
  subject?: string;
  from_name?: string;
  from_email?: string;
  body_html?: string;
  body_text?: string;
  status?: 'active' | 'draft' | 'disabled';
}

// POST /admin/notifications/templates/{id}/test
interface SendTestEmailRequest {
  email: string;
  variables?: Record<string, any>;
}

import React, { useState, useEffect } from 'react';
import { Search, Loader2, AlertCircle } from 'lucide-react';

interface SearchResult {
  protocol_id: string;
  protocol_name: string;
  score: number;
  vector_similarity: float;
  graph_importance: number;
  context: {
    tvl: number;
    category: string;
    dependent_count: number;
  };
  risk_info?: {
    risk_score: number;
    top_recommendation: string;
  };
}

export const GraphSearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/graph/search/hybrid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          query,
          limit: 10,
          include_risks: true,
          include_dependencies: true,
          similarity_threshold: 0.5,
        }),
      });

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      {/* Search Input */}
      <div className="relative mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search DeFi protocols... (e.g., 'decentralized lending')"
          className="w-full px-4 py-3 pl-12 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <Search className="absolute left-4 top-3.5 text-gray-400" size={20} />
        {loading && <Loader2 className="absolute right-4 top-3.5 animate-spin" size={20} />}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-700">
          <AlertCircle className="mr-2" size={20} />
          {error}
        </div>
      )}

      {/* Search Results */}
      <div className="space-y-4">
        {results.map((result) => (
          <div
            key={result.protocol_id}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            {/* Protocol Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {result.protocol_name}
                </h3>
                <span className="text-sm text-gray-500">{result.context.category}</span>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {(result.score * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">Match Score</div>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-500">TVL</div>
                <div className="text-lg font-semibold">
                  ${(result.context.tvl / 1e9).toFixed(2)}B
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Dependencies</div>
                <div className="text-lg font-semibold">{result.context.dependent_count}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Vector Similarity</div>
                <div className="text-lg font-semibold">
                  {(result.vector_similarity * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            {/* Risk Info */}
            {result.risk_info && (
              <div className={`p-3 rounded-lg ${
                result.risk_info.risk_score < 4 ? 'bg-green-50' :
                result.risk_info.risk_score < 7 ? 'bg-yellow-50' : 'bg-red-50'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    Risk Score: {result.risk_info.risk_score}/10
                  </span>
                  <span className="text-xs">{result.risk_info.top_recommendation}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface Node {
  id: string;
  name: string;
  type: string;
  tvl?: number;
}

interface Link {
  source: string;
  target: string;
  type: string;
}

interface GraphVisualizationProps {
  protocolId: string;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({ protocolId }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    // Fetch graph data
    const fetchGraphData = async () => {
      const response = await fetch(
        `/api/v1/graph/protocols/${protocolId}/ecosystem`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      
      const data = await response.json();
      renderGraph(data);
    };

    const renderGraph = (data: { nodes: Node[]; links: Link[] }) => {
      const width = 800;
      const height = 600;

      // Clear existing
      d3.select(svgRef.current).selectAll('*').remove();

      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      // Create force simulation
      const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id((d: any) => d.id))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

      // Draw links
      const link = svg.append('g')
        .selectAll('line')
        .data(data.links)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 2);

      // Draw nodes
      const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter().append('circle')
        .attr('r', (d) => Math.sqrt((d.tvl || 0) / 1e8) + 5)
        .attr('fill', (d) => {
          if (d.type === 'Protocol') return '#3b82f6';
          if (d.type === 'Token') return '#10b981';
          return '#6b7280';
        })
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended));

      // Add labels
      const label = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .enter().append('text')
        .text((d) => d.name)
        .attr('font-size', 10)
        .attr('dx', 12)
        .attr('dy', 4);

      // Update positions
      simulation.on('tick', () => {
        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y);

        node
          .attr('cx', (d: any) => d.x)
          .attr('cy', (d: any) => d.y);

        label
          .attr('x', (d: any) => d.x)
          .attr('y', (d: any) => d.y);
      });

      // Drag functions
      function dragstarted(event: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event: any) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragended(event: any) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }
    };

    fetchGraphData();
  }, [protocolId]);

  return (
    <div className="w-full bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-semibold mb-4">Protocol Ecosystem</h3>
      <svg ref={svgRef} className="w-full h-auto border border-gray-200 rounded"></svg>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Bell, TrendingUp, AlertTriangle } from 'lucide-react';

interface GraphEvent {
  type: string;
  protocol_id?: string;
  protocol_name?: string;
  message: string;
  timestamp: number;
}

export const RealtimeUpdates: React.FC = () => {
  const [events, setEvents] = useState<GraphEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/graph?token=${token}`);

    ws.onopen = () => {
      setConnected(true);
      
      // Subscribe to all updates
      ws.send(JSON.stringify({
        action: 'subscribe',
        channel: 'all',
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      setEvents((prev) => [
        {
          type: data.type,
          protocol_id: data.protocol_id,
          protocol_name: data.protocol_name,
          message: data.message || JSON.stringify(data),
          timestamp: data.timestamp || Date.now(),
        },
        ...prev.slice(0, 49), // Keep last 50 events
      ]);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="w-full max-w-md bg-white rounded-lg shadow-md p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center">
          <Bell className="mr-2" size={20} />
          Live Updates
        </h3>
        <div className={`px-2 py-1 rounded-full text-xs ${
          connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {/* Events Feed */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            Waiting for updates...
          </div>
        )}
        
        {events.map((event, idx) => (
          <div
            key={idx}
            className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {event.protocol_name && (
                  <div className="font-medium text-sm mb-1">{event.protocol_name}</div>
                )}
                <div className="text-sm text-gray-600">{event.message}</div>
              </div>
              {event.type === 'risk:alert' && (
                <AlertTriangle className="text-red-500 ml-2" size={16} />
              )}
              {event.type === 'protocol:update' && (
                <TrendingUp className="text-blue-500 ml-2" size={16} />
              )}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {new Date(event.timestamp * 1000).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

import React from 'react';
import { GraphSearchInterface } from './GraphSearchInterface';
import { GraphVisualization } from './GraphVisualization';
import { RealtimeUpdates } from './RealtimeUpdates';

export const GraphDashboard: React.FC = () => {
  const [selectedProtocol, setSelectedProtocol] = React.useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">GraphRAG Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Intelligent DeFi protocol discovery powered by hybrid retrieval
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search - Takes 2 columns */}
          <div className="lg:col-span-2">
            <GraphSearchInterface />
            
            {selectedProtocol && (
              <div className="mt-6">
                <GraphVisualization protocolId={selectedProtocol} />
              </div>
            )}
          </div>

          {/* Real-time Updates - Takes 1 column */}
          <div className="lg:col-span-1">
            <RealtimeUpdates />
          </div>
        </div>
      </div>
    </div>
  );
};

import { GraphDashboard } from './components/GraphDashboard';

function App() {
  return <GraphDashboard />;
}

localStorage.setItem('token', 'your-jwt-token');

headers: {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
}

const colors = {
  // Primary
  primary: '#3B82F6',
  primaryLight: '#60A5FA',
  primaryDark: '#2563EB',
  
  // Status
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#06B6D4',
  
  // Background (Dark Theme)
  background: '#0F172A',
  surface: '#1E293B',
  surfaceElevated: '#334155',
  
  // Text
  textPrimary: '#F8FAFC',
  textSecondary: '#94A3B8',
  textTertiary: '#64748B',
  
  // Border
  border: '#334155',
  borderLight: '#475569',
};

const typography = {
  // Display
  displayLarge: { size: 32, weight: '700', lineHeight: 40 },
  displayMedium: { size: 28, weight: '700', lineHeight: 36 },
  
  // Headlines
  headlineLarge: { size: 24, weight: '600', lineHeight: 32 },
  headlineMedium: { size: 20, weight: '600', lineHeight: 28 },
  headlineSmall: { size: 18, weight: '600', lineHeight: 24 },
  
  // Body
  bodyLarge: { size: 16, weight: '400', lineHeight: 24 },
  bodyMedium: { size: 14, weight: '400', lineHeight: 20 },
  bodySmall: { size: 12, weight: '400', lineHeight: 16 },
  
  // Labels
  labelLarge: { size: 14, weight: '500', lineHeight: 20 },
  labelMedium: { size: 12, weight: '500', lineHeight: 16 },
  labelSmall: { size: 10, weight: '500', lineHeight: 14 },
};

const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

const motion = {
  duration: {
    instant: 100,
    fast: 150,
    normal: 300,
    slow: 500,
  },
  easing: {
    smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    snappy: 'cubic-bezier(0.2, 0, 0, 1)',
  },
};

// GET /api/v1/search/history?limit=10&search_type=graphrag
interface SearchHistoryResponse {
  history: SearchHistoryEntry[];
  total: number;
}

interface SearchHistoryEntry {
  id: string;
  query: string;
  type: 'graphrag' | 'protocol' | 'token' | 'general';
  results_count: number;
  filters: Record<string, any>;
  created_at: string;
}

const getSearchHistory = async (
  filters?: {
    limit?: number;
    search_type?: string;
  }
): Promise<SearchHistoryResponse> => {
  const response = await api.get('/api/v1/search/history', { 
    params: filters 
  });
  return response.data;
};

// GET /api/v1/search/suggestions?prefix=aave&limit=5
interface SearchSuggestionsResponse {
  suggestions: string[];
  prefix: string;
}

const getSearchSuggestions = async (
  prefix: string,
  limit: number = 5
): Promise<string[]> => {
  const response = await api.get('/api/v1/search/suggestions', {
    params: { prefix, limit },
  });
  return response.data.suggestions;
};

// GET /api/v1/search/popular?limit=5&days=30
interface PopularQuery {
  query: string;
  count: number;
}

interface PopularQueriesResponse {
  popular_queries: PopularQuery[];
  period_days: number;
}

const getPopularQueries = async (
  limit: number = 5,
  days: number = 30
): Promise<PopularQuery[]> => {
  const response = await api.get('/api/v1/search/popular', {
    params: { limit, days },
  });
  return response.data.popular_queries;
};

// DELETE /api/v1/search/history/:search_id
const deleteSearchEntry = async (searchId: string): Promise<void> => {
  await api.delete(`/api/v1/search/history/${searchId}`);
};

// DELETE /api/v1/search/history/clear?search_type=graphrag
interface ClearHistoryResponse {
  cleared: number;
  message: string;
}

const clearSearchHistory = async (
  searchType?: string
): Promise<ClearHistoryResponse> => {
  const response = await api.delete('/api/v1/search/history/clear', {
    params: searchType ? { search_type: searchType } : undefined,
  });
  return response.data;
};

// GET /api/v1/search/analytics?days=30
interface SearchAnalytics {
  total_searches: number;
  by_type: Record<string, number>;
  average_results: number;
  most_common_filters: Array<{
    filter: string;
    count: number;
  }>;
}

const getSearchAnalytics = async (
  days: number = 30
): Promise<SearchAnalytics> => {
  const response = await api.get('/api/v1/search/analytics', {
    params: { days },
  });
  return response.data;
};

import { motion, AnimatePresence } from 'framer-motion';

function SearchHistoryList({ entries, onReRun, onDelete }: SearchHistoryListProps) {
  return (
    <div className="space-y-2">
      <AnimatePresence mode="popLayout">
        {entries.map((entry, index) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20, height: 0 }}
            transition={{ delay: index * 0.05 }}
            layout
          >
            <SearchHistoryCard
              entry={entry}
              onReRun={onReRun}
              onDelete={onDelete}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

function AutocompleteDropdown({ suggestions, onSelect }: AutocompleteProps) {
  return (
    <AnimatePresence>
      {suggestions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          className="absolute top-full left-0 right-0 bg-white rounded-lg shadow-xl mt-2 overflow-hidden z-50"
        >
          {suggestions.map((suggestion, idx) => (
            <motion.div
              key={idx}
              whileHover={{ backgroundColor: '#F3F4F6' }}
              onClick={() => onSelect(suggestion)}
              className="px-4 py-3 cursor-pointer border-b last:border-b-0"
            >
              <div className="flex items-center gap-2">
                <span className="text-gray-400">🔍</span>
                <span className="text-gray-900">{suggestion}</span>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ClearHistoryModal({ isOpen, onClose, onConfirm }: ClearModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-xl p-6 max-w-sm mx-4 shadow-2xl"
          >
            <div className="text-center mb-4">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-6xl mb-3"
              >
                ⚠️
              </motion.div>
              <h3 className="text-xl font-bold">Clear History?</h3>
              <p className="text-gray-600 mt-2">
                This will permanently delete your search history.
              </p>
            </div>
            
            <div className="space-y-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onConfirm}
                className="w-full bg-red-600 text-white py-3 rounded-lg font-semibold"
              >
                Clear All History
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onClose}
                className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-semibold"
              >
                Cancel
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

import Animated, {
  useAnimatedGestureHandler,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';

function SearchHistoryCard({ entry, onDelete }: SearchCardProps) {
  const translateX = useSharedValue(0);
  const opacity = useSharedValue(1);
  const deleteThreshold = -100;
  
  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      // Only allow left swipe (negative translateX)
      if (event.translationX < 0) {
        translateX.value = event.translationX;
        
        // Fade out as approaching delete threshold
        const progress = Math.abs(event.translationX) / Math.abs(deleteThreshold);
        opacity.value = Math.max(0.3, 1 - progress * 0.7);
      }
    },
    onEnd: (event) => {
      if (event.translationX < deleteThreshold) {
        // Delete
        translateX.value = withTiming(-400, {}, () => {
          runOnJS(onDelete)(entry.id);
        });
        opacity.value = withTiming(0);
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
  
  const deleteIndicatorStyle = useAnimatedStyle(() => ({
    opacity: translateX.value < -20 ? 1 : 0,
  }));
  
  return (
    <View style={styles.cardContainer}>
      <Animated.View style={[styles.deleteIndicator, deleteIndicatorStyle]}>
        <Text style={styles.deleteText}>🗑️ Delete</Text>
      </Animated.View>
      
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={[styles.card, animatedStyle]}>
          <SearchEntryContent entry={entry} />
        </Animated.View>
      </PanGestureHandler>
    </View>
  );
}

interface SearchHistoryScreenProps {
  navigation: any;
}

function SearchHistoryScreen({ navigation }: SearchHistoryScreenProps) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const { history, deleteEntry, clearHistory } = useSearchHistory();
  
  const filteredHistory = selectedType
    ? history.filter((entry) => entry.type === selectedType)
    : history;
  
  return (
    <div className="p-4">
      {/* Filter chips */}
      <div className="flex gap-2 mb-4 overflow-x-auto">
        <FilterChip
          label="All"
          count={history.length}
          active={!selectedType}
          onPress={() => setSelectedType(null)}
        />
        <FilterChip
          label="GraphRAG"
          count={history.filter((e) => e.type === 'graphrag').length}
          active={selectedType === 'graphrag'}
          onPress={() => setSelectedType('graphrag')}
        />
        <FilterChip
          label="Protocol"
          count={history.filter((e) => e.type === 'protocol').length}
          active={selectedType === 'protocol'}
          onPress={() => setSelectedType('protocol')}
        />
        {/* More filter chips */}
      </div>
      
      {/* History list */}
      <SearchHistoryList
        entries={filteredHistory}
        onReRun={(entry) => navigation.navigate('Search', { query: entry.query })}
        onDelete={deleteEntry}
      />
      
      {/* Clear all button */}
      {history.length > 0 && (
        <button
          onClick={() => clearHistory()}
          className="mt-6 w-full py-3 text-red-600 font-semibold"
        >
          Clear All History
        </button>
      )}
    </div>
  );
}

interface SearchAutocompleteProps {
  query: string;
  onSelect: (suggestion: string) => void;
}

function SearchAutocomplete({ query, onSelect }: SearchAutocompleteProps) {
  const { suggestions, isLoading } = useSearchSuggestions(query);
  
  if (!query || query.length < 1 || suggestions.length === 0) {
    return null;
  }
  
  return (
    <AutocompleteDropdown
      suggestions={suggestions}
      onSelect={onSelect}
      isLoading={isLoading}
    />
  );
}

function PopularQueriesWidget() {
  const { popularQueries } = usePopularQueries(5, 30);
  
  if (popularQueries.length === 0) return null;
  
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm">
      <h3 className="font-bold text-lg mb-3">Your Popular Searches</h3>
      <div className="space-y-2">
        {popularQueries.map((query, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔥</span>
              <div>
                <div className="font-medium">{query.query}</div>
                <div className="text-xs text-gray-500">
                  Searched {query.count} times
                </div>
              </div>
            </div>
            <button className="text-blue-600">↻</button>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useSearchHistory(filters?: { type?: string; limit?: number }) {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['search-history', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/search/history', {
        params: filters,
      });
      return response.data;
    },
  });
  
  const deleteEntry = useMutation({
    mutationFn: async (searchId: string) => {
      await api.delete(`/api/v1/search/history/${searchId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search-history'] });
      toast.success('Search deleted');
    },
  });
  
  const clearHistory = useMutation({
    mutationFn: async (searchType?: string) => {
      const response = await api.delete('/api/v1/search/history/clear', {
        params: searchType ? { search_type: searchType } : undefined,
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['search-history'] });
      toast.success(`Cleared ${data.cleared} search entries`);
    },
  });
  
  return {
    history: data?.history || [],
    total: data?.total || 0,
    isLoading,
    deleteEntry: deleteEntry.mutate,
    clearHistory: clearHistory.mutate,
  };
}

export function useSearchSuggestions(prefix: string, limit: number = 5) {
  const { data, isLoading } = useQuery({
    queryKey: ['search-suggestions', prefix, limit],
    queryFn: async () => {
      if (!prefix || prefix.length < 1) return { suggestions: [], prefix };
      
      const response = await api.get('/api/v1/search/suggestions', {
        params: { prefix, limit },
      });
      return response.data;
    },
    enabled: prefix.length >= 1,
    staleTime: 30000, // 30 seconds
  });
  
  return {
    suggestions: data?.suggestions || [],
    isLoading,
  };
}

export function usePopularQueries(limit: number = 5, days: number = 30) {
  const { data, isLoading } = useQuery({
    queryKey: ['popular-queries', limit, days],
    queryFn: async () => {
      const response = await api.get('/api/v1/search/popular', {
        params: { limit, days },
      });
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
  
  return {
    popularQueries: data?.popular_queries || [],
    periodDays: data?.period_days || days,
    isLoading,
  };
}

export function useSearchAnalytics(days: number = 30) {
  const { data, isLoading } = useQuery({
    queryKey: ['search-analytics', days],
    queryFn: async () => {
      const response = await api.get('/api/v1/search/analytics', {
        params: { days },
      });
      return response.data;
    },
    staleTime: 600000, // 10 minutes
  });
  
  return {
    analytics: data,
    isLoading,
  };
}

const searchHistoryErrors = {
  SEARCH_001: 'Failed to load search history',
  SEARCH_002: 'Failed to delete search entry',
  SEARCH_003: 'Failed to clear history',
  SEARCH_004: 'Search entry not found',
  SEARCH_005: 'Not your search entry',
  SEARCH_006: 'Invalid search type filter',
};

// Handle delete error
try {
  await deleteSearchEntry(searchId);
} catch (error) {
  if (error.code === 'SEARCH_005') {
    toast.error('You can only delete your own searches');
  } else if (error.code === 'SEARCH_004') {
    toast.error('Search entry not found');
  } else {
    toast.error('Failed to delete search. Please try again.');
  }
}

<button
  aria-label={`Re-run search: ${entry.query}. This search returned ${entry.results_count} results ${formatRelativeTime(entry.created_at)}`}
  onClick={() => onReRun(entry)}
>
  ↻
</button>

<div role="list" aria-label="Search history">
  {history.map((entry) => (
    <div
      key={entry.id}
      role="listitem"
      aria-label={`${entry.query}, ${entry.type} search, ${entry.results_count} results, ${formatRelativeTime(entry.created_at)}`}
    >
      <SearchHistoryCard entry={entry} />
    </div>
  ))}
</div>

// Backend validates history entry belongs to user
if (search_entry.user_id !== currentUser.id) {
  throw new UnauthorizedError('Not your search entry');
}

// Sanitize search queries before storing
const sanitizeQuery = (query: string): string => {
  return query
    .trim()
    .replace(/[<>]/g, '') // Remove angle brackets
    .substring(0, 500); // Limit length
};

describe('SearchHistory', () => {
  it('displays recent searches', () => {
    const { getByText } = render(
      <SearchHistoryScreen history={mockHistory} />
    );
    
    expect(getByText('Aave V3 security analysis')).toBeInTheDocument();
    expect(getByText('12 results')).toBeInTheDocument();
  });
  
  it('filters by search type', async () => {
    const { getByText, queryByText } = render(
      <SearchHistoryScreen history={mockHistory} />
    );
    
    fireEvent.click(getByText('GraphRAG'));
    
    await waitFor(() => {
      expect(getByText('Aave V3 security analysis')).toBeInTheDocument();
      expect(queryByText('ETH')).not.toBeInTheDocument(); // Token search hidden
    });
  });
  
  it('provides autocomplete suggestions', async () => {
    const { getByPlaceholderText, getByText } = render(
      <SearchWithAutocomplete />
    );
    
    const input = getByPlaceholderText('Search...');
    fireEvent.change(input, { target: { value: 'aav' } });
    
    await waitFor(() => {
      expect(getByText('Aave V3 security analysis')).toBeInTheDocument();
    });
  });
});

// Track when user re-runs a search
analytics.track('search_history_rerun', {
  original_query: entry.query,
  search_type: entry.type,
  time_since_original: Date.now() - new Date(entry.created_at).getTime(),
});

// Track autocomplete usage
analytics.track('search_autocomplete_used', {
  prefix: prefix,
  selected_suggestion: suggestion,
  suggestion_rank: suggestions.indexOf(suggestion) + 1,
});

// Track history clearing
analytics.track('search_history_cleared', {
  entries_cleared: response.cleared,
  filter_type: searchType || 'all',
});

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

// POST /api/v1/graph/search/hybrid
interface HybridSearchRequest {
  query: string;
  limit?: number; // Default: 10
  similarity_threshold?: number; // Default: 0.7
  filters?: {
    risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    chains?: string[];
    categories?: string[];
    min_tvl?: number;
    min_audits?: number;
    max_age_days?: number;
  };
  user_preferences?: {
    risk_tolerance?: 'conservative' | 'moderate' | 'aggressive';
    preferred_chains?: string[];
    excluded_protocols?: string[];
  };
}

interface HybridSearchResponse {
  results: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number; // 0-1
    combined_score: number; // 0-1 (semantic + graph)
    risk_score: number; // 0-10
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    tvl: number;
    apy?: number;
    category: string;
    chain: string;
    audit_count: number;
    description: string;
    why_relevant: string;
    tags: string[];
  }>;
  total_results: number;
  search_time_ms: number;
}

// POST /api/v1/graph/search/similar-protocols
interface SimilarProtocolsRequest {
  protocol_id: string;
  limit?: number; // Default: 10
  similarity_threshold?: number; // Default: 0.6
}

interface SimilarProtocolsResponse {
  base_protocol: {
    protocol_id: string;
    protocol_name: string;
    category: string;
    risk_level: string;
  };
  similar_protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    similarity_reasons: string[];
    shared_features: string[];
    key_differences: string[];
    risk_score: number;
    tvl: number;
  }>;
  community_cluster?: string;
}

// POST /api/v1/graph/search/contextual
interface ContextualSearchRequest {
  query: string;
  user_preferences: {
    risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
    preferred_chains?: string[];
    preferred_categories?: string[];
    min_tvl?: number;
  };
  limit?: number;
}

interface ContextualSearchResponse {
  results: Array<{
    protocol_id: string;
    protocol_name: string;
    relevance_score: number;
    matches_preferences: boolean;
    preference_match_reasons: string[];
    // ... other fields
  }>;
  personalization_applied: boolean;
  filters_applied: string[];
}

// POST /api/v1/search/saved
interface SaveSearchRequest {
  name: string;
  query: string;
  filters: {
    risk_level?: string;
    chains?: string[];
    categories?: string[];
    min_tvl?: number;
  };
}

interface SaveSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: any;
  created_at: string;
}

// GET /api/v1/search/history?limit=50
interface SearchHistoryResponse {
  searches: Array<{
    id: string;
    query: string;
    filters: any;
    results_count: number;
    created_at: string;
  }>;
  total: number;
}

// POST /api/v1/protocols/compare
interface CompareProtocolsRequest {
  protocol_ids: string[]; // Max 5
}

interface CompareProtocolsResponse {
  protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    metrics: {
      risk_score: number;
      tvl: number;
      apy?: number;
      audit_count: number;
      age_days: number;
      // ... more metrics
    };
  }>;
  comparison_matrix: {
    [metric: string]: {
      values: number[];
      winner_index: number;
      normalized_values: number[]; // 0-1
    };
  };
  overall_winner?: {
    protocol_id: string;
    protocol_name: string;
    wins_count: number;
  };
}

const searchAnimations = {
  // Search input focus
  searchInputFocus: {
    scale: [1, 1.02, 1],
    boxShadow: [
      '0 0 0 0 rgba(59, 130, 246, 0)',
      '0 0 0 4px rgba(59, 130, 246, 0.2)',
    ],
    transition: { duration: 0.3 }
  },
  
  // Result cards stagger
  resultCardEnter: {
    initial: { y: 20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    transition: {
      duration: 0.3,
      delay: 'stagger', // 0.05s per card
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Risk badge pulse (high risk)
  highRiskBadge: {
    animate: {
      scale: [1, 1.1, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Filter panel slide
  filterPanel: {
    initial: { x: -300, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -300, opacity: 0 },
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30
    }
  },
  
  // Similarity score meter
  similarityMeter: {
    initial: { width: 0 },
    animate: { width: 'percentage%' },
    transition: {
      duration: 1,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Comparison table reveal
  comparisonRow: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    transition: {
      duration: 0.4,
      delay: 'stagger'
    }
  },
  
  // Winner badge
  winnerBadge: {
    initial: { scale: 0, rotate: -180 },
    animate: { scale: 1, rotate: 0 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 20
    }
  },
  
  // Search result highlight
  resultHighlight: {
    whileHover: {
      scale: 1.02,
      boxShadow: "0 8px 16px rgba(0,0,0,0.1)",
      transition: { duration: 0.2 }
    },
    whileTap: {
      scale: 0.98
    }
  }
};

// Search input component
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  placeholder?: string;
  suggestions?: string[];
  recentSearches?: string[];
}

// Search result card
interface SearchResultCardProps {
  protocol: {
    id: string;
    name: string;
    similarity_score: number;
    risk_score: number;
    risk_level: string;
    tvl: number;
    apy?: number;
    category: string;
    chain: string;
    audit_count: number;
    why_relevant: string;
  };
  onViewDetails: () => void;
  onMoreLikeThis: () => void;
  onAddToCompare: () => void;
  onAction?: (action: string) => void;
}

// Filter panel
interface FilterPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onApply: () => void;
  onReset: () => void;
}

interface SearchFilters {
  risk_levels: string[];
  chains: string[];
  categories: string[];
  tvl_range: [number, number];
  min_audits: number;
  age: string[];
}

// Similarity indicator
interface SimilarityIndicatorProps {
  score: number; // 0-1
  showPercentage?: boolean;
  showBar?: boolean;
  color?: string;
}

// Protocol comparison table
interface ComparisonTableProps {
  protocols: Protocol[];
  metrics: string[];
  onRemoveProtocol: (id: string) => void;
  onAddProtocol: () => void;
}

// Search history item
interface SearchHistoryItemProps {
  search: {
    id: string;
    query: string;
    results_count: number;
    created_at: string;
  };
  onRepeat: () => void;
  onDelete?: () => void;
}

const searchErrors = {
  SEARCH_001: 'Search query too short (minimum 2 characters)',
  SEARCH_002: 'No protocols found matching your criteria',
  SEARCH_003: 'Search service temporarily unavailable',
  SEARCH_004: 'Too many search results - please refine your query',
  SEARCH_005: 'Invalid search filters',
  
  SIMILAR_001: 'Protocol not found',
  SIMILAR_002: 'No similar protocols found',
  
  COMPARE_001: 'Maximum 5 protocols can be compared',
  COMPARE_002: 'At least 2 protocols required for comparison',
  
  HISTORY_001: 'Failed to load search history',
  HISTORY_002: 'Failed to save search',
};

// GET /api/v1/graph/protocols/:id/dependencies
interface ProtocolDependenciesResponse {
  protocol_id: string;
  protocol_name: string;
  dependencies: Array<{
    protocol_id: string;
    protocol_name: string;
    relationship_type: string; // DEPENDS_ON, USES_TOKEN, etc.
    criticality: 'LOW' | 'MEDIUM' | 'HIGH';
    distance: number; // Hops from origin
  }>;
  dependents: Array<{
    protocol_id: string;
    protocol_name: string;
    relationship_type: string;
    impact_if_failure: string;
  }>;
  total_dependencies: number;
  total_dependents: number;
  importance_score: number; // PageRank score
}

// GET /api/v1/graph/protocols/:id/ecosystem?depth=2
interface ProtocolEcosystemResponse {
  center_protocol: {
    id: string;
    name: string;
    tvl: number;
    risk_score: number;
  };
  nodes: Array<{
    id: string;
    name: string;
    type: 'Protocol' | 'Token' | 'Chain';
    tvl?: number;
    risk_score?: number;
    category?: string;
    distance: number; // Hops from center
  }>;
  edges: Array<{
    source_id: string;
    target_id: string;
    relationship_type: string;
    properties?: Record<string, any>;
  }>;
  communities?: Array<{
    community_id: number;
    protocol_ids: string[];
    label: string;
  }>;
  statistics: {
    total_nodes: number;
    total_edges: number;
    max_depth: number;
    avg_risk: number;
  };
}

// GET /api/v1/ml/network/communities
interface CommunitiesResponse {
  communities: Array<{
    community_id: number;
    protocols: Array<{
      protocol_id: string;
      protocol_name: string;
      tvl: number;
      risk_score: number;
    }>;
    total_protocols: number;
    total_tvl: number;
    average_risk: number;
    interconnections: number;
    label: string;
  }>;
  algorithm: string; // "label_propagation" | "louvain"
  modularity_score: number;
  total_communities: number;
}

// GET /api/v1/ml/network/pagerank
interface PageRankResponse {
  protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    pagerank_score: number; // 0-10
    rank: number; // 1, 2, 3, ...
    interpretation: string;
  }>;
  top_10: string[]; // Protocol names
}

// GET /api/v1/graph/path/:source_id/:target_id
interface ShortestPathResponse {
  source: {
    protocol_id: string;
    protocol_name: string;
  };
  target: {
    protocol_id: string;
    protocol_name: string;
  };
  path: Array<{
    node_id: string;
    node_name: string;
    node_type: string;
    position: number; // 0, 1, 2, ...
  }>;
  relationships: Array<{
    from: string;
    to: string;
    type: string;
  }>;
  path_length: number; // Number of hops
  cascade_risk: 'LOW' | 'MEDIUM' | 'HIGH';
}

import * as d3 from 'd3';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: 'Protocol' | 'Token' | 'Chain';
  tvl?: number;
  risk_score?: number;
  category?: string;
  community_id?: number;
}

interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  relationship_type: string;
}

const createForceSimulation = (
  nodes: GraphNode[],
  edges: GraphEdge[]
) => {
  const simulation = d3.forceSimulation(nodes)
    .force(
      'link',
      d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance(100)
        .strength(0.5)
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => getNodeRadius(d)))
    .force('x', d3.forceX(width / 2).strength(0.1))
    .force('y', d3.forceY(height / 2).strength(0.1));
  
  return simulation;
};

const getNodeRadius = (node: GraphNode): number => {
  if (!node.tvl) return 8; // Default size
  
  // Logarithmic scale for TVL
  const minRadius = 8;
  const maxRadius = 40;
  const minTVL = 1_000_000; // $1M
  const maxTVL = 50_000_000_000; // $50B
  
  const logScale = d3.scaleLog()
    .domain([minTVL, maxTVL])
    .range([minRadius, maxRadius])
    .clamp(true);
  
  return logScale(node.tvl);
};

const getNodeColor = (node: GraphNode): string => {
  if (!node.risk_score) return '#94A3B8'; // Default gray
  
  // Color scale from green (low risk) to red (high risk)
  const colorScale = d3.scaleLinear<string>()
    .domain([0, 3, 5, 7, 10])
    .range([
      '#10B981', // Green (LOW)
      '#84CC16', // Lime (LOW-MED)
      '#F59E0B', // Orange (MED-HIGH)
      '#EF4444', // Red (HIGH)
      '#DC2626', // Dark Red (CRITICAL)
    ])
    .clamp(true);
  
  return colorScale(node.risk_score);
};

const getEdgeStyle = (edge: GraphEdge): {
  stroke: string;
  strokeWidth: number;
  strokeDasharray?: string;
} => {
  const styles: Record<string, any> = {
    DEPENDS_ON: {
      stroke: '#3B82F6',
      strokeWidth: 2,
    },
    USES_TOKEN: {
      stroke: '#10B981',
      strokeWidth: 1,
      strokeDasharray: '4 2',
    },
    COMPETES_WITH: {
      stroke: '#EF4444',
      strokeWidth: 1,
      strokeDasharray: '2 2',
    },
    INTEGRATED_BY: {
      stroke: '#8B5CF6',
      strokeWidth: 1.5,
    },
  };
  
  return styles[edge.relationship_type] || {
    stroke: '#64748B',
    strokeWidth: 1,
  };
};

// Zoom behavior
const zoom = d3.zoom()
  .scaleExtent([0.1, 4])
  .on('zoom', (event) => {
    svg.attr('transform', event.transform);
  });

svg.call(zoom);

// Node click handler
const handleNodeClick = (event: any, node: GraphNode) => {
  // Highlight node and connections
  highlightNode(node.id);
  
  // Show details panel
  showNodeDetails(node);
  
  // Focus on node
  focusOnNode(node);
};

// Node drag behavior
const drag = d3.drag<SVGCircleElement, GraphNode>()
  .on('start', dragStarted)
  .on('drag', dragged)
  .on('end', dragEnded);

nodeElements.call(drag);

// Search and highlight
const searchAndHighlight = (query: string) => {
  const matchedNodes = nodes.filter(n => 
    n.name.toLowerCase().includes(query.toLowerCase())
  );
  
  // Fade non-matching nodes
  nodeElements
    .style('opacity', d => matchedNodes.includes(d) ? 1 : 0.2);
};

const graphAnimations = {
  // Initial graph load
  graphEnter: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 1 }
  },
  
  // Node enter animation
  nodeEnter: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 30,
      delay: 'stagger' // Stagger by force simulation
    }
  },
  
  // Edge draw animation
  edgeDraw: {
    initial: { pathLength: 0, opacity: 0 },
    animate: { pathLength: 1, opacity: 1 },
    transition: {
      duration: 0.8,
      ease: "easeInOut"
    }
  },
  
  // Node focus (click)
  nodeFocus: {
    scale: [1, 1.3, 1.2],
    transition: {
      type: "spring",
      stiffness: 500
    }
  },
  
  // Highlight connections
  connectionHighlight: {
    strokeWidth: [1, 3, 2],
    opacity: [0.3, 1, 0.8],
    transition: { duration: 0.4 }
  },
  
  // Community pulse
  communityPulse: {
    animate: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Risk indicator throb
  riskIndicator: {
    animate: {
      boxShadow: [
        '0 0 0 0 rgba(239, 68, 68, 0)',
        '0 0 0 8px rgba(239, 68, 68, 0.3)',
        '0 0 0 0 rgba(239, 68, 68, 0)'
      ],
      transition: {
        duration: 2,
        repeat: Infinity
      }
    }
  }
};

// Main graph component
interface ProtocolGraphProps {
  protocolId?: string; // Center on specific protocol
  depth?: number; // Graph depth (default: 2)
  width: number;
  height: number;
  showCommunities?: boolean;
  showRiskIndicators?: boolean;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
}

// Graph controls
interface GraphControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  onCenter: () => void;
  onExport: () => void;
  zoomLevel: number;
}

// Node detail panel
interface NodeDetailPanelProps {
  node: GraphNode | null;
  dependencies: Dependency[];
  dependents: Dependent[];
  onClose: () => void;
  onViewFull: () => void;
  onCompare: () => void;
  onSimulateCascade: () => void;
}

// Community legend
interface CommunityLegendProps {
  communities: Community[];
  onSelectCommunity: (id: number) => void;
  selectedCommunityId?: number;
}

// Risk legend
interface RiskLegendProps {
  show: boolean;
}

// Path finder
interface PathFinderProps {
  sourceId: string;
  targetId: string;
  onPathFound: (path: PathNode[]) => void;
}

const graphErrors = {
  GRAPH_001: 'Failed to load graph data',
  GRAPH_002: 'Protocol not found in graph',
  GRAPH_003: 'Too many nodes (>1000) - please filter',
  GRAPH_004: 'Graph rendering failed',
  
  PATH_001: 'No path found between protocols',
  PATH_002: 'Path calculation failed',
  
  COMMUNITY_001: 'Community detection failed',
  COMMUNITY_002: 'No communities detected',
  
  EXPORT_001: 'Graph export failed',
};

// Handled by Privy SDK
// POST /auth/login (Privy endpoint)

interface PrivyAuthResult {
  user: {
    id: string;
    email?: string;
    wallet?: {
      address: string;
      chain_id: number;
    };
  };
  access_token: string;
}

// POST /api/users/onboarding
interface CompleteOnboardingRequest {
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  interests?: ('trading' | 'lending' | 'staking' | 'yield')[];
  notifications_enabled?: boolean;
}

interface CompleteOnboardingResponse {
  success: true;
  data: {
    user_id: string;
    onboarding_complete: true;
    recommended_actions: string[];
  };
}

// GET /api/users/me/onboarding
interface OnboardingStatusResponse {
  success: true;
  data: {
    onboarding_complete: boolean;
    steps_completed: string[];
    current_step?: string;
  };
}

const onboardingAnimations = {
  slideTransition: {
    x: ['100%', '0%'],
    opacity: [0, 1],
    transition: { duration: 0.3, ease: 'easeOut' }
  },
  
  illustrationEntrance: {
    scale: [0.8, 1],
    opacity: [0, 1],
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  buttonPulse: {
    scale: [1, 1.02, 1],
    transition: { duration: 2, repeat: Infinity }
  },
  
  walletCreated: {
    scale: [0.5, 1.1, 1],
    opacity: [0, 1],
    transition: { duration: 0.5, ease: 'backOut' }
  },
  
  codeInput: {
    scale: [1, 1.05, 1],
    transition: { duration: 0.15 }
  }
};

interface WelcomeSlideProps {
  illustration: React.ReactNode;
  title: string;
  description: string;
  currentIndex: number;
  totalSlides: number;
  onNext: () => void;
  onSkip: () => void;
}

interface AuthButtonProps {
  provider: 'email' | 'google' | 'apple' | 'wallet';
  onPress: () => void;
  loading?: boolean;
}

interface CodeInputProps {
  length: number;
  value: string;
  onChange: (code: string) => void;
  error?: string;
  autoFocus?: boolean;
}

interface ExperienceLevelCardProps {
  level: 'beginner' | 'intermediate' | 'advanced';
  icon: string;
  title: string;
  description: string;
  selected: boolean;
  onSelect: () => void;
}

const onboardingErrors = {
  AUTH_001: 'Invalid email format',
  AUTH_002: 'Email already registered',
  AUTH_003: 'Invalid verification code',
  AUTH_004: 'Code expired, please request a new one',
  AUTH_005: 'Too many attempts, please try again later',
  WALLET_001: 'Failed to create wallet',
  WALLET_002: 'Wallet connection failed',
  NETWORK_001: 'Network error, please check connection',
};

// Privy SDK handles authentication
// POST /auth/login via Privy

interface LoginResult {
  success: boolean;
  user?: {
    id: string;
    email?: string;
    wallet_address?: string;
  };
  access_token?: string;
  error?: string;
}

const loginAnimations = {
  logoEntrance: {
    y: [-20, 0],
    opacity: [0, 1],
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  buttonStagger: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'index * 0.1' }
  },
  
  biometricPulse: {
    scale: [1, 1.1, 1],
    opacity: [0.8, 1, 0.8],
    transition: { duration: 2, repeat: Infinity }
  }
};

// GET /api/users/me/kyc
interface GetKYCStatusResponse {
  success: true;
  data: {
    status: 'not_started' | 'pending' | 'approved' | 'rejected';
    tier?: 'tier_1' | 'tier_2';
    submitted_at?: string;
    reviewed_at?: string;
    rejection_reason?: string;
  };
}

// POST /api/users/me/kyc/start
interface StartKYCResponse {
  success: true;
  data: {
    session_id: string;
    provider_url?: string;
  };
}

// POST /api/users/me/kyc/documents
interface UploadDocumentRequest {
  session_id: string;
  document_type: 'passport' | 'drivers_license' | 'national_id';
  front_image: string; // base64
  back_image?: string; // base64
  selfie_image: string; // base64
  country: string;
}

// GET /api/transactions
interface GetTransactionsRequest {
  page?: number;
  page_size?: number;
  type?: 'swap' | 'send' | 'receive' | 'supply' | 'borrow' | 'bridge' | 'stake';
  chain?: string;
  status?: 'pending' | 'success' | 'failed';
  search?: string;
}

interface GetTransactionsResponse {
  success: true;
  data: {
    transactions: Transaction[];
    pagination: Pagination;
  };
}

interface Transaction {
  id: string;
  type: string;
  status: 'pending' | 'success' | 'failed';
  chain: string;
  protocol?: string;
  tx_hash?: string;
  from?: { token: string; amount: string; value_usd: number };
  to?: { token: string; amount: string; value_usd?: number; address?: string };
  gas_fee_usd?: number;
  created_at: string;
  completed_at?: string;
}

// GET /api/v1/dashboard/insights
interface DashboardInsightsResponse {
  insights: AIInsight[];
  personalized: boolean;
}

interface AIInsight {
  id: string;
  type: 'risk_warning' | 'optimization' | 'diversification' | 'opportunity';
  title: string;
  message: string;
  action_label: string | null;
  action_url: string | null;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
}

const getDashboardInsights = async (): Promise<AIInsight[]> => {
  const response = await api.get('/api/v1/dashboard/insights');
  return response.data.insights;
};

// GET /api/v1/dashboard/summary
interface DashboardSummaryResponse {
  total_value_usd: number;
  change_24h_usd: number;
  change_24h_percent: number;
  overall_risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  chains: ChainBreakdown[];
  positions: PositionBreakdown[];
}

interface ChainBreakdown {
  chain: string;
  value_usd: number;
  percentage: number;
  protocol_count: number;
}

interface PositionBreakdown {
  protocol_name: string;
  chain: string;
  position_type: 'supplied' | 'borrowed' | 'staked' | 'lp';
  amount_usd: number;
  percentage: number;
}

const getDashboardSummary = async (): Promise<DashboardSummaryResponse> => {
  const response = await api.get('/api/v1/dashboard/summary');
  return response.data;
};

export function useDashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const response = await api.get('/api/v1/dashboard/summary');
      return response.data;
    },
    refetchInterval: 60000, // Refetch every 60 seconds
  });
  
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['dashboard-insights'],
    queryFn: async () => {
      const response = await api.get('/api/v1/dashboard/insights');
      return response.data.insights;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });
  
  return {
    summary,
    insights: insights || [],
    isLoading: summaryLoading || insightsLoading,
  };
}

// GET /api/v1/ml/prediction/:protocol_id
interface RiskPredictionResponse {
  protocol_id: string;
  protocol_name: string;
  risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number; // 0-1
  risk_trend: 'DECREASING' | 'STABLE' | 'INCREASING' | 'VOLATILE';
  contributing_factors: Array<{
    feature: string;
    impact: number; // -1 to +1
    explanation: string;
  }>;
  recommendations: string[];
  model_version: string;
  predicted_at: string;
}

// GET /api/v1/ml/prediction/:protocol_id/anomalies
interface AnomalyDetectionResponse {
  protocol_id: string;
  protocol_name: string;
  is_anomalous: boolean;
  confidence: number;
  anomalies: Array<{
    feature: string;
    current_value: number;
    expected_value: number;
    deviation: number;
    z_score: number; // Standard deviations
    is_anomalous: boolean;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
  }>;
  overall_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendations: string[];
  detected_at: string;
}

// GET /api/v1/ml/prediction/:protocol_id/forecast?days=30
interface RiskForecastResponse {
  protocol_id: string;
  protocol_name: string;
  current_risk: number;
  forecasts: Array<{
    days_ahead: number;
    predicted_risk: number;
    confidence_lower: number;
    confidence_upper: number;
    trend: 'DECREASING' | 'STABLE' | 'INCREASING';
  }>;
  overall_trend: 'DECREASING' | 'STABLE' | 'INCREASING' | 'VOLATILE';
  driving_factors: string[];
  recommendations: string[];
  forecast_generated_at: string;
}

// POST /api/v1/ml/prediction/batch
interface BatchRiskRequest {
  protocol_ids: string[];
}

interface BatchRiskResponse {
  predictions: Array<RiskPredictionResponse>;
  summary: {
    average_risk: number;
    highest_risk: {
      protocol_id: string;
      protocol_name: string;
      risk_score: number;
    };
    lowest_risk: {
      protocol_id: string;
      protocol_name: string;
      risk_score: number;
    };
  };
}

const riskAnimations = {
  // Risk meter fill
  riskMeterFill: {
    initial: { width: 0 },
    animate: { width: 'percentage%' },
    transition: {
      duration: 1.2,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Risk score count up
  riskScoreCounter: {
    initial: { value: 0 },
    animate: { value: 'targetValue' },
    transition: {
      duration: 1,
      ease: "easeOut"
    }
  },
  
  // Anomaly shake
  anomalyShake: {
    animate: {
      x: [0, -5, 5, -5, 5, 0],
      transition: {
        duration: 0.5,
        repeat: 2
      }
    }
  },
  
  // Factor card reveal
  factorReveal: {
    initial: { x: -20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    transition: {
      duration: 0.3,
      delay: 'stagger' // 0.1s per card
    }
  },
  
  // Trend arrow animation
  trendArrow: {
    animate: {
      y: 'direction === "up" ? [-3, 0] : [3, 0]',
      transition: {
        duration: 1,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Confidence bar
  confidenceBar: {
    initial: { scaleX: 0 },
    animate: { scaleX: 1 },
    transition: { duration: 0.8 }
  },
  
  // Forecast line draw
  forecastLineDraw: {
    initial: { pathLength: 0 },
    animate: { pathLength: 1 },
    transition: {
      duration: 1.5,
      ease: "easeInOut"
    }
  }
};

// Risk meter gauge
interface RiskMeterProps {
  riskScore: number; // 0-10
  riskLevel: string;
  confidence: number;
  showLabel?: boolean;
  size?: 'small' | 'medium' | 'large';
}

// Factor card
interface FactorCardProps {
  factor: {
    feature: string;
    impact: number;
    explanation: string;
  };
  isExpanded?: boolean;
  onToggle?: () => void;
}

// Anomaly indicator
interface AnomalyIndicatorProps {
  anomaly: {
    feature: string;
    current_value: number;
    expected_value: number;
    z_score: number;
    severity: string;
  };
}

// Forecast chart
interface ForecastChartProps {
  forecasts: Array<{
    days_ahead: number;
    predicted_risk: number;
    confidence_lower: number;
    confidence_upper: number;
  }>;
  currentRisk: number;
  width: number;
  height: number;
}

// Risk comparison
interface RiskComparisonProps {
  protocols: Array<{
    id: string;
    name: string;
    risk_score: number;
  }>;
  highlightProtocolId?: string;
}

const riskErrors = {
  RISK_001: 'Risk prediction failed',
  RISK_002: 'Insufficient data for prediction',
  RISK_003: 'ML service unavailable',
  RISK_004: 'Protocol not found',
  
  ANOMALY_001: 'Anomaly detection failed',
  ANOMALY_002: 'No anomalies detected',
  
  FORECAST_001: 'Forecast generation failed',
  FORECAST_002: 'Insufficient historical data',
};

// GET /api/v1/portfolio/risk
interface PortfolioRiskResponse {
  user_id: string;
  overall_risk_score: number; // 0-10, weighted by exposure
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
    exposure_percentage: number;
    risk_score: number;
    risk_level: string;
    risk_trend: string;
    contributing_factors: string[];
    value_at_risk_usd: number;
  }>;
  dependency_risks: Array<{
    dependency_protocol_id: string;
    dependency_protocol_name: string;
    dependent_protocols: string[];
    impact_if_failure: string;
    total_exposure_usd: number;
    risk_score: number;
  }>;
  systemic_risk_score: number;
  concentration_risk: number;
  chain_risk_distribution: Record<string, number>;
  recommendations: string[];
  total_value_at_risk_usd: number;
  last_updated: string;
}

// POST /api/v1/portfolio/risk/simulate-cascade
interface CascadeSimulationRequest {
  origin_protocol_id: string;
}

interface CascadeSimulationResponse {
  user_id: string;
  cascade_impacts: Array<{
    origin_protocol_id: string;
    origin_protocol_name: string;
    directly_affected: string[];
    indirectly_affected: string[];
    total_exposure_at_risk_usd: number;
    cascade_probability: number;
    time_to_impact: string; // "immediate" | "hours" | "days"
  }>;
  worst_case_loss_usd: number;
  worst_case_loss_percentage: number;
  protocols_to_exit: string[];
  protocols_to_reduce: string[];
  safe_protocols: string[];
}

const portfolioRiskAnimations = {
  // Risk score reveal
  riskScoreReveal: {
    initial: { scale: 0, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20
    }
  },
  
  // Distribution bars
  distributionBars: {
    initial: { scaleX: 0 },
    animate: { scaleX: 1 },
    transition: {
      duration: 0.8,
      delay: 'stagger',
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Cascade animation
  cascadeFlow: {
    animate: {
      pathLength: [0, 1],
      opacity: [0, 1, 0.5],
      transition: {
        duration: 2,
        ease: "easeInOut"
      }
    }
  },
  
  // Warning pulse
  warningPulse: {
    animate: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 1.5,
        repeat: Infinity
      }
    }
  }
};

interface PortfolioRiskDashboardProps {
  userId: string;
  refreshInterval?: number; // Auto-refresh in ms
}

interface RiskDistributionChartProps {
  distribution: Record<string, number>;
  totalValue: number;
}

interface ProtocolRiskCardProps {
  protocol: {
    id: string;
    name: string;
    exposure_usd: number;
    exposure_percentage: number;
    risk_score: number;
    risk_level: string;
  };
  onReview: () => void;
  onReduce: () => void;
}

interface DependencyRiskMapProps {
  dependencies: Array<{
    id: string;
    name: string;
    dependents: string[];
    impact: string;
    exposure: number;
  }>;
  onSimulate: (id: string) => void;
}

interface CascadeSimulatorProps {
  protocolId: string;
  onComplete: (result: CascadeSimulationResponse) => void;
}

// GET /api/v1/portfolio/
interface PortfolioResponse {
  user_id: string;
  total_value_usd: number;
  protocols: ProtocolExposure[];
  overall_risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  last_updated: string;
}

interface ProtocolExposure {
  protocol_id: string;
  protocol_name: string;
  chain: string;
  position_type: 'supplied' | 'borrowed' | 'staked' | 'lp';
  amount_usd: number;
  percentage_of_portfolio: number;
  risk_score: number; // ML-powered
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

const getPortfolio = async (): Promise<PortfolioResponse> => {
  const response = await api.get('/api/v1/portfolio/');
  return response.data;
};

// GET /api/v1/portfolio/risk
interface PortfolioRiskResponse {
  overall_risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_factors: RiskFactor[];
  concentration_risk: number; // 0-10
  protocol_risks: ProtocolRisk[];
  recommendations: string[];
}

interface RiskFactor {
  factor: string;
  impact: 'low' | 'medium' | 'high';
  description: string;
}

interface ProtocolRisk {
  protocol_name: string;
  risk_score: number;
  exposure_usd: number;
  contribution_to_portfolio_risk: number; // 0-100%
}

const getPortfolioRisk = async (): Promise<PortfolioRiskResponse> => {
  const response = await api.get('/api/v1/portfolio/risk');
  return response.data;
};

export function usePortfolio() {
  const { data: portfolio, isLoading } = useQuery({
    queryKey: ['user-portfolio'],
    queryFn: async () => {
      const response = await api.get('/api/v1/portfolio/');
      return response.data;
    },
    refetchInterval: 60000, // Refetch every 60 seconds
  });
  
  const { data: risk } = useQuery({
    queryKey: ['portfolio-risk'],
    queryFn: async () => {
      const response = await api.get('/api/v1/portfolio/risk');
      return response.data;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });
  
  return {
    portfolio,
    risk,
    isLoading,
    totalValue: portfolio?.total_value_usd || 0,
    overallRisk: portfolio?.overall_risk_score || 0,
  };
}

// GET /api/v1/subscription/
// Description: Get all available subscription plans
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface Subscription {
  id: number;
  name: string; // "PRO" | "CORPORATE"
  price_monthly: number; // USD
  price_yearly: number; // USD
  features: string[];
  stripe_price_id_monthly: string;
  stripe_price_id_yearly: string;
  is_active: boolean;
}

const getSubscriptions = async (): Promise<Subscription[]> => {
  const response = await api.get('/api/v1/subscription/', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
[
  {
    "id": 1,
    "name": "PRO",
    "price_monthly": 29.99,
    "price_yearly": 299.99,
    "features": [
      "Advanced AI Chat",
      "Portfolio Analytics",
      "Risk Alerts",
      "GraphRAG Search",
      "Priority Support"
    ],
    "stripe_price_id_monthly": "price_1234567890",
    "stripe_price_id_yearly": "price_0987654321",
    "is_active": true
  },
  {
    "id": 2,
    "name": "CORPORATE",
    "price_monthly": 99.99,
    "price_yearly": 999.99,
    "features": [
      "Everything in PRO",
      "Team Management (up to 10 users)",
      "API Access",
      "Custom Projects",
      "Dedicated Support"
    ],
    "stripe_price_id_monthly": "price_1111111111",
    "stripe_price_id_yearly": "price_2222222222",
    "is_active": true
  }
]

// POST /api/v1/subscription/{subscription_id}/subscribe
// Description: Create a new subscription for current user via Stripe Checkout
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - subscription_id: number - ID of the subscription plan (1=PRO, 2=CORPORATE)
//
// Query Parameters: None
//
// Request Body: None (subscription_id in path)

// Response:
interface CreateSubscriptionResponse {
  checkout_url: string; // Stripe Checkout URL to redirect user
  subscription_id: number;
  plan_name: string;
}

const createSubscription = async (
  subscriptionId: number
): Promise<CreateSubscriptionResponse> => {
  const response = await api.post(
    `/api/v1/subscription/${subscriptionId}/subscribe`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Usage:
const handleSubscribe = async (planId: number) => {
  const result = await createSubscription(planId);
  // Redirect to Stripe Checkout
  window.location.href = result.checkout_url;
};

// Example Response (200 OK):
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_abc123...",
  "subscription_id": 1,
  "plan_name": "PRO"
}

// Example Error Response (404 Not Found - Invalid plan):
{
  "error": {
    "code": "SUBSCRIPTION_NOT_FOUND",
    "message": "Subscription plan with ID 99 not found",
    "details": {
      "subscription_id": 99
    }
  }
}

// POST /api/v1/subscription/cancel
// Description: Cancel current user's active subscription
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface CancelSubscriptionRequest {
  reason?: string; // Optional cancellation reason
  feedback?: string; // Optional user feedback
}

// Response:
interface CancelSubscriptionResponse {
  success: boolean;
  message: string;
  cancelled_at: string;
  active_until: string; // End of current billing period
}

const cancelSubscription = async (
  reason?: string
): Promise<CancelSubscriptionResponse> => {
  const response = await api.post('/api/v1/subscription/cancel', {
    reason,
  }, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "reason": "switching_to_competitor",
  "feedback": "Need more features for team management"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "Subscription cancelled successfully",
  "cancelled_at": "2025-12-01T11:00:00Z",
  "active_until": "2025-12-31T23:59:59Z"
}

// Example Error Response (400 Bad Request - No active subscription):
{
  "error": {
    "code": "NO_ACTIVE_SUBSCRIPTION",
    "message": "You don't have an active subscription to cancel",
    "details": {}
  }
}

// POST /api/v1/subscription/success
// Description: Handle successful subscription payment from Stripe
// Authentication: Required (Bearer token)
// Note: Typically called by Stripe redirect after successful payment
//
// Path Parameters: None
//
// Query Parameters:
//   - session_id: string - Stripe Checkout session ID
//
// Request Body: None

// Response:
interface SubscriptionSuccessResponse {
  success: boolean;
  subscription_active: boolean;
  plan_name: string;
  next_billing_date: string;
}

const handleSubscriptionSuccess = async (
  sessionId: string
): Promise<SubscriptionSuccessResponse> => {
  const response = await api.post(
    `/api/v1/subscription/success?session_id=${sessionId}`,
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
// POST /api/v1/subscription/success?session_id=cs_test_abc123...

// Example Response (200 OK):
{
  "success": true,
  "subscription_active": true,
  "plan_name": "PRO",
  "next_billing_date": "2026-01-01T00:00:00Z"
}

// POST /api/v1/subscription/init
// Description: Initialize default subscription plans (PRO, CORPORATE)
// Authentication: Required (Bearer token + Admin role)
// Note: Internal/admin endpoint for setup
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface InitSubscriptionsResponse {
  plans_created: number;
  plans: Subscription[];
}

const initializeSubscriptions = async (): Promise<InitSubscriptionsResponse> => {
  const response = await api.post('/api/v1/subscription/init', {}, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "plans_created": 2,
  "plans": [
    {
      "id": 1,
      "name": "PRO",
      "price_monthly": 29.99,
      "price_yearly": 299.99
    },
    {
      "id": 2,
      "name": "CORPORATE",
      "price_monthly": 99.99,
      "price_yearly": 999.99
    }
  ]
}

// GET /api/v1/payments/user?page=1&per_page=10
// Description: Get paginated list of user's payment transactions
// Authentication: Required (Bearer token)
//
// Path Parameters: None
//
// Query Parameters:
//   - page: number - Page number (default: 1, min: 1)
//   - per_page: number - Items per page (default: 10, max: 100)

// Response:
interface PaymentHistoryResponse {
  items: Payment[];
  page: number;
  per_page: number;
  total: number;
}

interface Payment {
  id: number;
  user_id: number;
  subscription_id: number;
  subscription_name: string;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  stripe_payment_id: string;
  created_at: string;
  paid_at: string | null;
}

const getUserPayments = async (
  page: number = 1,
  perPage: number = 10
): Promise<PaymentHistoryResponse> => {
  const response = await api.get('/api/v1/payments/user', {
    params: { page, per_page: perPage },
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/payments/user?page=1&per_page=5

// Example Response (200 OK):
{
  "items": [
    {
      "id": 501,
      "user_id": 12345,
      "subscription_id": 1,
      "subscription_name": "PRO",
      "amount": 29.99,
      "currency": "USD",
      "status": "completed",
      "stripe_payment_id": "pi_1234567890",
      "created_at": "2025-12-01T10:00:00Z",
      "paid_at": "2025-12-01T10:00:15Z"
    },
    {
      "id": 450,
      "user_id": 12345,
      "subscription_id": 1,
      "subscription_name": "PRO",
      "amount": 29.99,
      "currency": "USD",
      "status": "completed",
      "stripe_payment_id": "pi_0987654321",
      "created_at": "2025-11-01T10:00:00Z",
      "paid_at": "2025-11-01T10:00:12Z"
    }
  ],
  "page": 1,
  "per_page": 5,
  "total": 12
}

// POST /api/v1/payments/transaction
// Description: Create a new payment transaction
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface CreatePaymentRequest {
  amount: number; // Payment amount in specified currency
  currency: string; // "USD", "EUR", etc.
  description: string; // Payment description/memo
}

// Response:
interface CreatePaymentResponse {
  status: string;
  payment: {
    id: number;
    amount: number;
    currency: string;
    status: string;
  };
}

const createPayment = async (
  payment: CreatePaymentRequest
): Promise<CreatePaymentResponse> => {
  const response = await api.post('/api/v1/payments/transaction', payment, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "amount": 29.99,
  "currency": "USD",
  "description": "PRO Plan - Monthly subscription"
}

// Example Response (200 OK):
{
  "status": "success",
  "payment": {
    "id": 502,
    "amount": 29.99,
    "currency": "USD",
    "status": "pending"
  }
}

export function useSubscription() {
  const queryClient = useQueryClient();
  
  const { data: plans, isLoading } = useQuery({
    queryKey: ['subscription-plans'],
    queryFn: async () => {
      const response = await api.get('/api/v1/subscription/');
      return response.data;
    },
  });
  
  const subscribe = useMutation({
    mutationFn: async (planId: number) => {
      const response = await api.post(`/api/v1/subscription/${planId}/subscribe`);
      return response.data;
    },
    onSuccess: (data) => {
      // Redirect to Stripe Checkout
      window.location.href = data.checkout_url;
    },
  });
  
  const cancelSubscription = useMutation({
    mutationFn: async (reason?: string) => {
      const response = await api.post('/api/v1/subscription/cancel', { reason });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Subscription cancelled successfully');
    },
  });
  
  return {
    plans: plans || [],
    isLoading,
    subscribe: subscribe.mutate,
    cancelSubscription: cancelSubscription.mutate,
  };
}

export function usePaymentHistory(page: number = 1, perPage: number = 10) {
  const { data, isLoading } = useQuery({
    queryKey: ['payment-history', page, perPage],
    queryFn: async () => {
      const response = await api.get('/api/v1/payments/user', {
        params: { page, per_page: perPage }
      });
      return response.data;
    },
  });
  
  return {
    payments: data?.items || [],
    page: data?.page || 1,
    perPage: data?.per_page || 10,
    total: data?.total || 0,
    isLoading,
  };
}

const subscriptionErrors = {
  SUB_001: 'Subscription plan not found',
  SUB_002: 'Already subscribed to this plan',
  SUB_003: 'No active subscription to cancel',
  SUB_004: 'Payment processing failed',
  SUB_005: 'Stripe checkout session expired',
};

// Handle subscription error
try {
  await createSubscription(planId);
} catch (error) {
  if (error.code === 'SUB_002') {
    toast.error('You are already subscribed to this plan');
  } else if (error.code === 'SUB_004') {
    toast.error('Payment failed. Please try again or contact support.');
  } else {
    toast.error('Subscription failed. Please try again.');
  }
}

// POST /api/v1/chat/messages
interface SendMessageRequest {
  conversation_id?: string;
  message: string;
  context?: {
    selected_chain?: string;
    selected_token?: string;
    user_preferences?: UserPreferences;
  };
  enable_graphrag?: boolean; // NEW: Enable GraphRAG search
  enable_risk_analysis?: boolean; // NEW: Enable ML risk analysis
}

interface SendMessageResponse {
  success: true;
  data: {
    conversation_id: string;
    message_id: string;
    response: EnhancedChatResponse;
  };
}

interface EnhancedChatResponse {
  type: 'text' | 'transaction_preview' | 'transaction_status' | 
        'protocol_search' | 'risk_warning' | 'protocol_insight' | 
        'dependency_info' | 'live_update';
  content: string;
  
  // For transaction_preview
  transaction?: TransactionPreview;
  
  // NEW: For protocol_search
  protocol_results?: ProtocolSearchResult[];
  
  // NEW: For risk_warning
  risk_analysis?: RiskAnalysis;
  alternatives?: AlternativeProtocol[];
  
  // NEW: For protocol_insight
  protocol_details?: ProtocolDetails;
  dependencies?: DependencyInfo[];
  similar_protocols?: SimilarProtocol[];
  
  // For suggestions
  suggestions?: string[];
  
  // For quick actions
  actions?: Array<{
    label: string;
    action: string;
    params?: Record<string, any>;
  }>;
  
  // NEW: Streaming support
  is_streaming?: boolean;
  stream_id?: string;
}

// NEW: Protocol search result
interface ProtocolSearchResult {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number; // 0-1
  risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  tvl: number;
  apy?: number;
  audit_count: number;
  description: string;
  category: string;
  chain: string;
  why_relevant: string; // Why this was suggested
}

// NEW: Risk analysis
interface RiskAnalysis {
  protocol_id: string;
  protocol_name: string;
  risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number; // 0-1
  contributing_factors: Factor[];
  recommendations: string[];
  historical_incidents: Incident[];
}

interface Factor {
  factor: string;
  impact: number; // -10 to +10
  description: string;
}

// NEW: Alternative protocol
interface AlternativeProtocol {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  tvl: number;
  apy?: number;
  why_better: string;
}

// NEW: Dependency info
interface DependencyInfo {
  dependency_type: 'direct' | 'indirect';
  protocol_id: string;
  protocol_name: string;
  relationship: string; // 'DEPENDS_ON' | 'USES_TOKEN' | etc.
  criticality: 'LOW' | 'MEDIUM' | 'HIGH';
}

// NEW: Similar protocol
interface SimilarProtocol {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number; // 0-1
  reason: string;
  shared_features: string[];
}

// POST /api/v1/chat/search-protocols
interface ChatProtocolSearchRequest {
  conversation_id: string;
  query: string;
  filters?: {
    risk_level?: 'LOW' | 'MEDIUM' | 'HIGH';
    min_tvl?: number;
    category?: string;
    chain?: string;
  };
  limit?: number;
}

interface ChatProtocolSearchResponse {
  success: true;
  data: {
    results: ProtocolSearchResult[];
    search_context: string; // Natural language explanation
    recommendations: string[];
  };
}

// POST /api/v1/chat/analyze-risk
interface ChatRiskAnalysisRequest {
  conversation_id: string;
  protocol_name: string;
  operation_type?: 'supply' | 'borrow' | 'swap' | 'stake';
  amount_usd?: number;
}

interface ChatRiskAnalysisResponse {
  success: true;
  data: {
    risk_analysis: RiskAnalysis;
    alternatives: AlternativeProtocol[];
    should_warn: boolean;
    warning_message?: string;
  };
}

// POST /api/v1/chat/similar-protocols
interface ChatSimilarProtocolsRequest {
  conversation_id: string;
  protocol_name: string;
  limit?: number;
}

interface ChatSimilarProtocolsResponse {
  success: true;
  data: {
    base_protocol: ProtocolSearchResult;
    similar_protocols: SimilarProtocol[];
    community_cluster?: string;
  };
}

// GET /api/v1/projects/ - Get user's assigned projects
interface UserProjectsResponse {
  assigned_projects: ProjectSummary[];
  active_project_id: string | null;
}

interface ProjectSummary {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  welcome_message: string;
  is_featured: boolean;
}

// POST /api/v1/projects/:project_id/activate - Activate a project
const activateProject = async (projectId: string): Promise<void> => {
  await api.post(`/api/v1/projects/${projectId}/activate`);
  // After activation, the AI chat will use this project's context
};

// Client example - Projects integration
const useProjects = () => {
  const { data: projects } = useQuery({
    queryKey: ['user-projects'],
    queryFn: async () => {
      const response = await api.get('/api/v1/projects/');
      return response.data;
    },
  });
  
  const activateProject = useMutation({
    mutationFn: async (projectId: string) => {
      await api.post(`/api/v1/projects/${projectId}/activate`);
    },
    onSuccess: () => {
      // Refresh chat context
      queryClient.invalidateQueries(['chat-context']);
    },
  });
  
  return {
    projects: projects?.assigned_projects || [],
    activeProjectId: projects?.active_project_id,
    activateProject: activateProject.mutate,
  };
};

// Integration in Chat: Show active project context
function ChatHeader() {
  const { projects, activeProjectId } = useProjects();
  const activeProject = projects.find(p => p.id === activeProjectId);
  
  return (
    <header>
      {activeProject && (
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-50">
          <span style={{ color: activeProject.color }}>
            {activeProject.icon}
          </span>
          <span className="font-semibold">{activeProject.name}</span>
          <button onClick={() => showProjectSwitcher()}>Switch</button>
        </div>
      )}
    </header>
  );
}

// WebSocket: ws://api/v1/ws/chat?token={jwt_token}

// Connection
const ws = new WebSocket('ws://api/v1/ws/chat?token=' + authToken);

// Subscribe to conversation updates
ws.send(JSON.stringify({
  action: 'subscribe',
  conversation_id: 'conv-uuid-123'
}));

// Message types received
interface WebSocketChatMessage {
  type: 'message_chunk' | 'typing_indicator' | 'protocol_update' | 
        'risk_alert' | 'connection_status';
  
  // For message_chunk (streaming response)
  chunk?: {
    message_id: string;
    content: string;
    is_final: boolean;
  };
  
  // For typing_indicator
  is_typing?: boolean;
  
  // For protocol_update
  protocol_update?: {
    protocol_id: string;
    protocol_name: string;
    change_type: 'risk_change' | 'tvl_change' | 'audit_added' | 'incident';
    old_value?: any;
    new_value?: any;
    message: string;
  };
  
  // For risk_alert
  risk_alert?: {
    protocol_id: string;
    protocol_name: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    message: string;
    recommended_action?: string;
  };
  
  timestamp: number;
}

// Send message with streaming
ws.send(JSON.stringify({
  action: 'send_message',
  conversation_id: 'conv-uuid-123',
  message: 'Find me safe staking protocols',
  stream_response: true
}));

// Receive streaming chunks
ws.onmessage = (event) => {
  const data: WebSocketChatMessage = JSON.parse(event.data);
  
  if (data.type === 'message_chunk') {
    appendToMessage(data.chunk.content);
    if (data.chunk.is_final) {
      markMessageComplete();
    }
  }
};

// GET /api/v1/chat/conversations/{id}/messages?include_graph_context=true

interface GetMessagesResponse {
  success: true;
  data: {
    conversation_id: string;
    messages: EnhancedMessage[];
    graph_context?: ConversationGraphContext; // NEW
  };
}

interface EnhancedMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: EnhancedChatResponse;
  created_at: string;
  
  // NEW: Graph context
  mentioned_protocols?: string[];
  risk_warnings_shown?: string[];
  searches_performed?: string[];
}

// NEW: Graph context for conversation
interface ConversationGraphContext {
  protocols_discussed: Array<{
    protocol_id: string;
    protocol_name: string;
    mention_count: number;
    last_mentioned: string;
  }>;
  searches_performed: Array<{
    query: string;
    timestamp: string;
    results_count: number;
  }>;
  risk_warnings_shown: number;
  alternatives_suggested: number;
}

const chatAnimationsV2 = {
  // Message animations
  messageSend: {
    initial: { y: 20, opacity: 0, scale: 0.95 },
    animate: { y: 0, opacity: 1, scale: 1 },
    transition: { 
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  messageReceive: {
    initial: { y: 20, opacity: 0, scale: 0.95 },
    animate: { y: 0, opacity: 1, scale: 1 },
    transition: { 
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
      delay: 0.1
    }
  },
  
  // NEW: Streaming text animation
  streamingText: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.15 }
  },
  
  // NEW: Typing indicator with bounce
  typingIndicator: {
    animate: {
      y: [0, -8, 0],
      transition: {
        duration: 0.6,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // NEW: Protocol card slide-in
  protocolCard: {
    initial: { x: -20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    transition: { 
      duration: 0.3,
      delay: 'stagger', // Use staggerChildren for list
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // NEW: Risk warning pulse
  riskWarning: {
    animate: {
      scale: [1, 1.05, 1],
      boxShadow: [
        '0 0 0 0 rgba(239, 68, 68, 0)',
        '0 0 0 8px rgba(239, 68, 68, 0.2)',
        '0 0 0 0 rgba(239, 68, 68, 0)'
      ],
      transition: {
        duration: 2,
        repeat: 3,
        ease: "easeInOut"
      }
    }
  },
  
  // NEW: Live update notification
  liveUpdate: {
    initial: { y: -50, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: -50, opacity: 0 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 30
    }
  },
  
  // Transaction card
  transactionCard: {
    initial: { scale: 0.9, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: { 
      duration: 0.4,
      ease: [0.68, -0.55, 0.265, 1.55] // Bounce easing
    }
  },
  
  // Confirm button interaction
  confirmButton: {
    whileTap: { scale: 0.95 },
    whileHover: { scale: 1.05 },
    transition: { duration: 0.15 }
  },
  
  // Success animation
  successCheck: {
    initial: { scale: 0, rotate: -180 },
    animate: { scale: 1, rotate: 0 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 20
    }
  },
  
  // NEW: Risk meter animation
  riskMeter: {
    initial: { width: 0 },
    animate: { width: 'percentage%' },
    transition: {
      duration: 1.2,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // NEW: Dependency tree expand
  dependencyTree: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    exit: { height: 0, opacity: 0 },
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Suggestion chips
  suggestionChip: {
    initial: { x: -10, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    transition: {
      duration: 0.2,
      delay: 'index * 0.05' // Stagger based on index
    }
  }
};

// Enhanced message component
interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  response?: EnhancedChatResponse;
  timestamp: string;
  isStreaming?: boolean; // NEW
  streamProgress?: number; // NEW: 0-1
}

// NEW: Protocol search results component
interface ProtocolSearchResultsProps {
  results: ProtocolSearchResult[];
  onSelectProtocol: (protocolId: string) => void;
  onCompare: (protocolIds: string[]) => void;
  onViewDetails: (protocolId: string) => void;
}

// NEW: Risk warning card component
interface RiskWarningCardProps {
  riskAnalysis: RiskAnalysis;
  alternatives: AlternativeProtocol[];
  onProceedAnyway: () => void;
  onSelectAlternative: (protocolId: string) => void;
  onLearnMore: () => void;
}

// NEW: Protocol insight card
interface ProtocolInsightCardProps {
  protocolDetails: ProtocolDetails;
  dependencies?: DependencyInfo[];
  similarProtocols?: SimilarProtocol[];
  onViewGraph: () => void;
  onCompare: (otherProtocolId: string) => void;
}

// NEW: Live update notification
interface LiveUpdateNotificationProps {
  update: ProtocolUpdate | RiskAlert;
  onDismiss: () => void;
  onViewDetails: () => void;
}

// Transaction preview card (enhanced)
interface TransactionPreviewCardProps {
  preview: TransactionPreview;
  riskAnalysis?: RiskAnalysis; // NEW
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

// Transaction status card
interface TransactionStatusCardProps {
  status: 'pending' | 'success' | 'failed';
  type: string;
  summary: string;
  txHash?: string;
  details?: Record<string, string>;
  onViewDetails?: () => void;
}

// Data card
interface DataCardProps {
  card: DataCard;
  onAction?: (action: string) => void;
}

// Quick action chip
interface QuickActionChipProps {
  icon: string;
  label: string;
  onPress: () => void;
}

// Chat input (enhanced)
interface ChatInputProps {
  value: string;
  onChange: (text: string) => void;
  onSend: () => void;
  onVoice?: () => void;
  onAttach?: () => void;
  disabled?: boolean;
  placeholder?: string;
  isTyping?: boolean; // NEW: Show assistant typing
  enableGraphRAG?: boolean; // NEW: Toggle GraphRAG
}

// NEW: Streaming message indicator
interface StreamingIndicatorProps {
  isStreaming: boolean;
  progress?: number; // 0-1
}

// NEW: WebSocket connection status
interface ConnectionStatusProps {
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  lastUpdate?: Date;
}

class ChatWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  
  constructor(
    private authToken: string,
    private conversationId: string
  ) {}
  
  connect() {
    const wsUrl = `${WS_BASE_URL}/chat?token=${this.authToken}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Subscribe to conversation
      this.subscribe(this.conversationId);
    };
    
    this.ws.onmessage = (event) => {
      const message: WebSocketChatMessage = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.attemptReconnect();
    };
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`Reconnecting (attempt ${this.reconnectAttempts})...`);
        this.connect();
      }, delay);
    }
  }
  
  subscribe(conversationId: string) {
    this.send({
      action: 'subscribe',
      conversation_id: conversationId
    });
  }
  
  sendMessage(message: string, streamResponse: boolean = true) {
    this.send({
      action: 'send_message',
      conversation_id: this.conversationId,
      message,
      stream_response: streamResponse
    });
  }
  
  private send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  private handleMessage(message: WebSocketChatMessage) {
    switch (message.type) {
      case 'message_chunk':
        this.onMessageChunk(message.chunk!);
        break;
      case 'typing_indicator':
        this.onTypingIndicator(message.is_typing!);
        break;
      case 'protocol_update':
        this.onProtocolUpdate(message.protocol_update!);
        break;
      case 'risk_alert':
        this.onRiskAlert(message.risk_alert!);
        break;
    }
  }
  
  // Event handlers (to be overridden)
  onMessageChunk(chunk: any) {}
  onTypingIndicator(isTyping: boolean) {}
  onProtocolUpdate(update: any) {}
  onRiskAlert(alert: any) {}
  
  disconnect() {
    this.ws?.close();
  }
}

import { useState, useEffect, useRef } from 'react';

interface UseChatWebSocketOptions {
  authToken: string;
  conversationId: string;
  onMessageChunk?: (chunk: string, isFinal: boolean) => void;
  onProtocolUpdate?: (update: any) => void;
  onRiskAlert?: (alert: any) => void;
}

export function useChatWebSocket(options: UseChatWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const wsClientRef = useRef<ChatWebSocketClient | null>(null);
  
  useEffect(() => {
    const client = new ChatWebSocketClient(
      options.authToken,
      options.conversationId
    );
    
    client.onMessageChunk = (chunk) => {
      setStreamingMessage(prev => prev + chunk.content);
      if (chunk.is_final) {
        options.onMessageChunk?.(streamingMessage + chunk.content, true);
        setStreamingMessage('');
      }
    };
    
    client.onTypingIndicator = (isTyping) => {
      setIsTyping(isTyping);
    };
    
    client.onProtocolUpdate = (update) => {
      options.onProtocolUpdate?.(update);
    };
    
    client.onRiskAlert = (alert) => {
      options.onRiskAlert?.(alert);
    };
    
    client.connect();
    wsClientRef.current = client;
    
    return () => {
      client.disconnect();
    };
  }, [options.conversationId]);
  
  const sendMessage = (message: string) => {
    wsClientRef.current?.sendMessage(message);
  };
  
  return {
    isConnected,
    isTyping,
    streamingMessage,
    sendMessage
  };
}

const chatErrorsV2 = {
  // Existing errors
  CHAT_001: 'Failed to send message',
  CHAT_002: 'Conversation not found',
  TX_001: 'Transaction preview expired',
  TX_002: 'Insufficient balance',
  TX_003: 'Transaction failed',
  TX_004: 'Gas estimation failed',
  VOICE_001: 'Microphone access denied',
  VOICE_002: 'Speech recognition unavailable',
  
  // NEW: GraphRAG errors
  GRAPH_001: 'Protocol search failed',
  GRAPH_002: 'No protocols found matching criteria',
  GRAPH_003: 'GraphRAG service unavailable',
  GRAPH_004: 'Invalid search query',
  
  // NEW: ML errors
  ML_001: 'Risk analysis failed',
  ML_002: 'ML service unavailable',
  ML_003: 'Insufficient data for risk prediction',
  ML_004: 'Anomaly detection failed',
  
  // NEW: WebSocket errors
  WS_001: 'WebSocket connection failed',
  WS_002: 'WebSocket disconnected unexpectedly',
  WS_003: 'Failed to subscribe to conversation',
  WS_004: 'Message streaming interrupted',
  WS_005: 'WebSocket authentication failed',
  
  // NEW: Real-time errors
  RT_001: 'Failed to receive protocol update',
  RT_002: 'Risk alert delivery failed',
  RT_003: 'Real-time sync interrupted',
};

// POST /api/chat/messages
interface SendMessageRequest {
  conversation_id?: string;
  message: string;
  context?: {
    selected_chain?: string;
    selected_token?: string;
  };
}

interface SendMessageResponse {
  success: true;
  data: {
    conversation_id: string;
    message_id: string;
    response: ChatResponse;
  };
}

interface ChatResponse {
  type: 'text' | 'transaction_preview' | 'transaction_status' | 'data_card' | 'error';
  content: string;
  
  // For transaction_preview
  transaction?: TransactionPreview;
  
  // For data_card
  card?: DataCard;
  
  // For suggestions
  suggestions?: string[];
  
  // For quick actions
  actions?: Array<{
    label: string;
    action: string;
    params?: Record<string, any>;
  }>;
}

interface TransactionPreview {
  id: string;
  type: 'swap' | 'bridge' | 'supply' | 'borrow' | 'stake' | 'send';
  summary: string;
  details: {
    from?: { token: string; amount: string; value_usd: number };
    to?: { token: string; amount: string; value_usd?: number };
    chain: string;
    protocol?: string;
    gas_estimate_usd: number;
    rate?: string;
    slippage?: number;
  };
  warnings?: string[];
  expires_at: string;
}

interface DataCard {
  type: 'yields' | 'prices' | 'portfolio' | 'gas';
  title: string;
  items: Array<{
    label: string;
    value: string;
    subtext?: string;
    icon?: string;
  }>;
}

// POST /api/chat/transactions/{preview_id}/confirm
interface ConfirmTransactionResponse {
  success: true;
  data: {
    transaction_id: string;
    status: 'pending' | 'submitted';
    tx_hash?: string;
  };
}

// GET /api/chat/conversations
interface GetConversationsResponse {
  success: true;
  data: {
    conversations: Array<{
      id: string;
      title: string;
      preview: string;
      last_message_at: string;
      message_count: number;
    }>;
  };
}

// GET /api/chat/conversations/{id}/messages
interface GetMessagesResponse {
  success: true;
  data: {
    conversation_id: string;
    messages: Array<{
      id: string;
      role: 'user' | 'assistant';
      content: string;
      response?: ChatResponse;
      created_at: string;
    }>;
  };
}

const chatAnimations = {
  messageSend: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  messageReceive: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.3 }
  },
  
  typingIndicator: {
    opacity: [0.3, 1, 0.3],
    transition: { duration: 1, repeat: Infinity }
  },
  
  transactionCard: {
    scale: [0.95, 1],
    opacity: [0, 1],
    transition: { duration: 0.3, ease: 'backOut' }
  },
  
  confirmButton: {
    scale: [1, 0.95, 1],
    transition: { duration: 0.15 }
  },
  
  successCheck: {
    scale: [0, 1.2, 1],
    opacity: [0, 1],
    transition: { duration: 0.4, ease: 'backOut' }
  },
  
  suggestionChip: {
    x: [-10, 0],
    opacity: [0, 1],
    transition: { duration: 0.2, delay: 'index * 0.05' }
  }
};

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  response?: ChatResponse;
  timestamp: string;
}

interface TransactionPreviewCardProps {
  preview: TransactionPreview;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

interface TransactionStatusCardProps {
  status: 'pending' | 'success' | 'failed';
  type: string;
  summary: string;
  txHash?: string;
  details?: Record<string, string>;
  onViewDetails?: () => void;
}

interface DataCardProps {
  card: DataCard;
  onAction?: (action: string) => void;
}

interface QuickActionChipProps {
  icon: string;
  label: string;
  onPress: () => void;
}

interface ChatInputProps {
  value: string;
  onChange: (text: string) => void;
  onSend: () => void;
  onVoice?: () => void;
  onAttach?: () => void;
  disabled?: boolean;
  placeholder?: string;
}

interface VoiceInputConfig {
  language: 'en-US';
  continuous: false;
  interimResults: true;
  maxAlternatives: 1;
}

const voiceInputStates = {
  idle: { icon: '🎤', color: 'default' },
  listening: { icon: '🔴', color: 'red', pulse: true },
  processing: { icon: '⏳', color: 'blue' },
  error: { icon: '❌', color: 'red' },
};

const chatErrors = {
  CHAT_001: 'Failed to send message',
  CHAT_002: 'Conversation not found',
  TX_001: 'Transaction preview expired',
  TX_002: 'Insufficient balance',
  TX_003: 'Transaction failed',
  TX_004: 'Gas estimation failed',
  VOICE_001: 'Microphone access denied',
  VOICE_002: 'Speech recognition unavailable',
};

// GET /api/v1/projects/
interface UserProjectsResponse {
  assigned_projects: ProjectSummary[];
  active_project_id: string | null;
}

interface ProjectSummary {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  welcome_message: string;
  is_featured: boolean;
}

// POST /api/v1/projects/:project_id/activate
const activateProject = async (projectId: string) => {
  const response = await api.post(
    `/api/v1/projects/${projectId}/activate`
  );
  return response.data;
};

// GET /api/v1/projects/available
const getAvailableProjects = async (): Promise<ProjectSummary[]> => {
  const response = await api.get('/api/v1/projects/available');
  return response.data;
};

import { motion } from 'framer-motion';

function ProjectCard({ project, onSelect }: ProjectCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ borderColor: project.color }}
      className="border-2 rounded-xl p-4 cursor-pointer"
      onClick={() => onSelect(project)}
    >
      <div className="text-4xl mb-2">{project.icon}</div>
      <h3 className="font-bold text-lg">{project.name}</h3>
      <p className="text-sm text-gray-600">{project.description}</p>
      
      <motion.button
        whileHover={{ x: 4 }}
        className="mt-3 text-blue-600 flex items-center gap-1"
      >
        Select Project →
      </motion.button>
    </motion.div>
  );
}

function ChatWithProject({ activeProject }: ChatProps) {
  return (
    <div>
      {/* Project header with color transition */}
      <motion.div
        animate={{
          backgroundColor: activeProject.color,
        }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
        className="p-4 text-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{activeProject.icon}</span>
            <span className="font-bold">{activeProject.name}</span>
          </div>
          <button onClick={openProjectSwitcher}>Switch</button>
        </div>
      </motion.div>
      
      {/* Chat messages with context indicator */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeProject.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: 0.3 }}
        >
          <ChatMessages />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function ProjectContextLoader({ project }: { project: Project }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        className="text-2xl"
      >
        {project.icon}
      </motion.div>
      <div>
        <p className="font-semibold">Loading {project.name} context...</p>
        <p className="text-sm text-gray-600">
          Preparing specialized assistance
        </p>
      </div>
    </motion.div>
  );
}

import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

function ProjectCardNative({ project, onSelect }: ProjectCardProps) {
  const scale = useSharedValue(1);
  const pressed = useSharedValue(0);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value },
      { translateY: withSpring(pressed.value ? -8 : 0) },
    ],
  }));
  
  const handlePressIn = () => {
    scale.value = withSpring(0.95);
    pressed.value = 1;
  };
  
  const handlePressOut = () => {
    scale.value = withSpring(1);
    pressed.value = 0;
  };
  
  return (
    <Animated.View style={[styles.card, animatedStyle]}>
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => onSelect(project)}
      >
        <Text style={styles.icon}>{project.icon}</Text>
        <Text style={styles.name}>{project.name}</Text>
        <Text style={styles.description}>{project.description}</Text>
      </Pressable>
    </Animated.View>
  );
}

interface ProjectSelectorProps {
  projects: ProjectSummary[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string) => Promise<void>;
  recommendedProjects?: string[];
}

function ProjectSelector({
  projects,
  activeProjectId,
  onSelectProject,
  recommendedProjects = [],
}: ProjectSelectorProps) {
  const recommended = projects.filter(p => 
    recommendedProjects.includes(p.id)
  );
  const other = projects.filter(p => 
    !recommendedProjects.includes(p.id)
  );
  
  return (
    <div className="space-y-6">
      {recommended.length > 0 && (
        <section>
          <h2 className="text-lg font-bold mb-3">Recommended for You</h2>
          <div className="space-y-3">
            {recommended.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                isActive={project.id === activeProjectId}
                onSelect={onSelectProject}
              />
            ))}
          </div>
        </section>
      )}
      
      <section>
        <h2 className="text-lg font-bold mb-3">All Projects</h2>
        <div className="grid grid-cols-2 gap-3">
          {other.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              isActive={project.id === activeProjectId}
              onSelect={onSelectProject}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

interface ProjectHeaderProps {
  project: ProjectSummary;
  onOpenSwitcher: () => void;
}

function ProjectHeader({ project, onOpenSwitcher }: ProjectHeaderProps) {
  return (
    <div
      style={{ backgroundColor: project.color }}
      className="p-4 text-white flex items-center justify-between"
    >
      <div className="flex items-center gap-2">
        <span className="text-2xl">{project.icon}</span>
        <span className="font-bold">{project.name}</span>
      </div>
      <button
        onClick={onOpenSwitcher}
        className="bg-white/20 px-3 py-1 rounded-full text-sm"
      >
        Switch
      </button>
    </div>
  );
}

interface ProjectContextBadgeProps {
  project: ProjectSummary;
  size?: 'sm' | 'md' | 'lg';
}

function ProjectContextBadge({ project, size = 'md' }: ProjectContextBadgeProps) {
  const sizes = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };
  
  return (
    <div
      style={{
        backgroundColor: `${project.color}20`,
        borderColor: project.color,
      }}
      className={`border-2 rounded-full inline-flex items-center gap-1 ${sizes[size]}`}
    >
      <span>{project.icon}</span>
      <span style={{ color: project.color }} className="font-semibold">
        {project.name}
      </span>
    </div>
  );
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useProjects() {
  const queryClient = useQueryClient();
  
  const { data: projects, isLoading } = useQuery({
    queryKey: ['user-projects'],
    queryFn: async () => {
      const response = await api.get('/api/v1/projects/');
      return response.data;
    },
  });
  
  const activateProject = useMutation({
    mutationFn: async (projectId: string) => {
      await api.post(`/api/v1/projects/${projectId}/activate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-projects'] });
      queryClient.invalidateQueries({ queryKey: ['chat-context'] });
    },
  });
  
  return {
    projects: projects?.assigned_projects ?? [],
    activeProjectId: projects?.active_project_id,
    isLoading,
    activateProject: activateProject.mutate,
  };
}

export function useActiveProject() {
  const { projects, activeProjectId } = useProjects();
  
  const activeProject = projects.find(p => p.id === activeProjectId);
  
  return {
    activeProject,
    isProjectActive: !!activeProject,
  };
}

export const PROJECT_COLORS = {
  savings: '#10B981',      // Green
  earning: '#F59E0B',      // Amber
  aave: '#B6509E',         // Aave Purple
  trading: '#3B82F6',      // Blue
  staking: '#8B5CF6',      // Purple
  bridge: '#EC4899',       // Pink
  portfolio: '#06B6D4',    // Cyan
  governance: '#F97316',   // Orange
  risk: '#EF4444',         // Red
  nft_finance: '#A855F7',  // Purple
};

export const PROJECT_ICONS = {
  savings: '💰',
  earning: '🌾',
  aave: '🏦',
  trading: '📈',
  staking: '🥩',
  bridge: '🌉',
  portfolio: '📊',
  governance: '🗳️',
  risk: '🛡️',
  nft_finance: '🎨',
};

interface ProjectStore {
  activeProject: ProjectSummary | null;
  assignedProjects: ProjectSummary[];
  isLoading: boolean;
  
  setActiveProject: (project: ProjectSummary) => void;
  loadProjects: () => Promise<void>;
  activateProject: (projectId: string) => Promise<void>;
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  activeProject: null,
  assignedProjects: [],
  isLoading: false,
  
  setActiveProject: (project) => set({ activeProject: project }),
  
  loadProjects: async () => {
    set({ isLoading: true });
    const response = await api.get('/api/v1/projects/');
    const activeProj = response.data.assigned_projects.find(
      (p: ProjectSummary) => p.id === response.data.active_project_id
    );
    set({
      assignedProjects: response.data.assigned_projects,
      activeProject: activeProj || null,
      isLoading: false,
    });
  },
  
  activateProject: async (projectId) => {
    await api.post(`/api/v1/projects/${projectId}/activate`);
    await get().loadProjects();
  },
}));

function ChatScreen() {
  const { activeProject } = useActiveProject();
  const [projectSwitcherOpen, setProjectSwitcherOpen] = useState(false);
  
  // Show project selection if no active project
  if (!activeProject) {
    return <ProjectSelector />;
  }
  
  return (
    <div>
      <ProjectHeader
        project={activeProject}
        onOpenSwitcher={() => setProjectSwitcherOpen(true)}
      />
      
      {/* Chat interface with project context */}
      <ChatInterface projectContext={activeProject} />
      
      {/* Project switcher modal */}
      <ProjectSwitcherModal
        open={projectSwitcherOpen}
        onClose={() => setProjectSwitcherOpen(false)}
      />
    </div>
  );
}

function AIMessage({ message, project }: MessageProps) {
  return (
    <div className="flex gap-3">
      <div
        style={{ backgroundColor: project.color }}
        className="w-8 h-8 rounded-full flex items-center justify-center text-white"
      >
        {project.icon}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold">AI Assistant</span>
          <ProjectContextBadge project={project} size="sm" />
        </div>
        <div className="prose">{message.content}</div>
      </div>
    </div>
  );
}

const projectErrors = {
  PROJ_001: 'Failed to load projects',
  PROJ_002: 'Project not found',
  PROJ_003: 'You do not have access to this project',
  PROJ_004: 'Project is currently inactive',
  PROJ_005: 'Failed to switch projects',
  PROJ_006: 'Project is at capacity',
};

// Handle project selection error
try {
  await activateProject(projectId);
} catch (error) {
  if (error.status === 403) {
    toast.error('You do not have access to this project');
  } else if (error.status === 404) {
    toast.error('Project not found');
  } else {
    toast.error('Failed to activate project. Please try again.');
  }
}

<button
  aria-label={`Select ${project.name} project for ${project.description}`}
  role="button"
  onClick={() => onSelect(project)}
>
  <span aria-hidden="true">{project.icon}</span>
  <span>{project.name}</span>
</button>

function ProjectGrid({ projects, onSelect }: ProjectGridProps) {
  const handleKeyPress = (e: KeyboardEvent, project: Project) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(project);
    }
  };
  
  return (
    <div role="grid">
      {projects.map((project, idx) => (
        <div
          key={project.id}
          role="gridcell"
          tabIndex={0}
          onKeyPress={(e) => handleKeyPress(e, project)}
        >
          <ProjectCard project={project} onSelect={onSelect} />
        </div>
      ))}
    </div>
  );
}

// Verify user has access before activating
const verifyProjectAccess = async (userId: string, projectId: string) => {
  const { assigned_projects } = await api.get(`/api/v1/projects/`);
  const hasAccess = assigned_projects.some(p => p.id === projectId);
  
  if (!hasAccess) {
    throw new Error('Unauthorized: Project access denied');
  }
};

// Ensure project context is valid before sending messages
const validateProjectContext = (project: ProjectSummary) => {
  if (!project.id) throw new Error('Invalid project: missing ID');
  if (!project.slug) throw new Error('Invalid project: missing slug');
  
  return true;
};

describe('ProjectSelector', () => {
  it('displays recommended projects first', () => {
    const { getByText } = render(
      <ProjectSelector 
        projects={mockProjects}
        recommendedProjects={['savings-id']}
      />
    );
    
    expect(getByText('Recommended for You')).toBeInTheDocument();
    expect(getByText('Smart Savings')).toBeInTheDocument();
  });
  
  it('activates project on selection', async () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <ProjectSelector projects={mockProjects} onSelectProject={onSelect} />
    );
    
    fireEvent.click(getByText('Smart Savings'));
    
    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith('savings-id');
    });
  });
});

// POST /api/v1/account/signup
// Description: Register a new user account
// Authentication: None (Public endpoint)
// Rate Limit: 5 requests per hour per IP
//
// Path Parameters: None
//
// Query Parameters: None
//
// Request Body:
interface SignUpRequest {
  email: string; // Valid email address
  first_name: string; // 1-50 characters
  last_name: string; // 1-50 characters
  password: string; // Min 8 characters, must include uppercase, lowercase, number
  country_id?: number; // Optional country ID
  city_id?: number; // Optional city ID  
  language?: string; // Optional preferred language (en, es, fr, etc.)
}

// Response:
interface SignUpResponse {
  id: number;
  session_id: string;
  user_id: number;
  expires_at: string; // ISO 8601 timestamp
  access_token: string; // JWT access token
  refresh_token: string; // JWT refresh token
  token_type: string; // "Bearer"
  is_active: boolean;
}

// TypeScript Implementation:
const signup = async (data: SignUpRequest): Promise<SignUpResponse> => {
  const response = await api.post('/api/v1/account/signup', data);
  return response.data;
};

// Example Request:
{
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Johnson",
  "password": "SecurePass123!",
  "country_id": 1,
  "city_id": 100,
  "language": "en"
}

// Example Response (201 Created):
{
  "id": 12345,
  "session_id": "sess_550e8400e29b41d4a716446655440000",
  "user_id": 12345,
  "expires_at": "2025-12-02T10:30:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "is_active": true
}

// Example Error Response (409 Conflict - Email exists):
{
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "An account with this email already exists",
    "details": {
      "email": "alice@example.com"
    }
  }
}

// Example Error Response (400 Bad Request - Invalid password):
{
  "error": {
    "code": "INVALID_PASSWORD",
    "message": "Password must be at least 8 characters and include uppercase, lowercase, and number",
    "details": {
      "field": "password",
      "requirements": ["min_length_8", "uppercase", "lowercase", "number"]
    }
  }
}

// POST /api/v1/account/login
// Description: Authenticate user with email and password
// Authentication: None (Public endpoint)
// Rate Limit: 10 requests per 15 minutes per IP
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface LogInRequest {
  email: string;
  password: string;
}

// Response:
interface LogInResponse {
  session_id: string;
  user_id: number;
  expires_at: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

const login = async (credentials: LogInRequest): Promise<LogInResponse> => {
  const response = await api.post('/api/v1/account/login', credentials);
  
  // Store tokens
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Example Request:
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}

// Example Response (200 OK):
{
  "session_id": "sess_660e8400e29b41d4a716446655440000",
  "user_id": 12345,
  "expires_at": "2025-12-02T10:30:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}

// Example Error Response (401 Unauthorized - Invalid credentials):
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": {}
  }
}

// Example Error Response (404 Not Found - User not found):
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "No account found with this email",
    "details": {
      "email": "notfound@example.com"
    }
  }
}

// GET /api/v1/account/me
// Description: Get current authenticated user's profile information
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface MeResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_admin: boolean;
  is_super_admin: boolean;
  email_verified: boolean;
  country_id: number | null;
  city_id: number | null;
  language: string;
  created_at: string;
  updated_at: string;
}

const getCurrentUser = async (): Promise<MeResponse> => {
  const response = await api.get('/api/v1/account/me', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "id": 12345,
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Johnson",
  "is_active": true,
  "is_admin": false,
  "is_super_admin": false,
  "email_verified": true,
  "country_id": 1,
  "city_id": 100,
  "language": "en",
  "created_at": "2025-11-01T08:00:00Z",
  "updated_at": "2025-12-01T10:30:00Z"
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}

// PUT /api/v1/account/me
// Description: Update current user's profile information
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface UpdateMeRequest {
  first_name?: string; // 1-50 characters
  last_name?: string; // 1-50 characters
  country_id?: number;
  city_id?: number;
  language?: string;
}

// Response:
interface MeResponse {
  // Same as GET /api/v1/account/me
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  // ... other fields
}

const updateProfile = async (updates: UpdateMeRequest): Promise<MeResponse> => {
  const response = await api.put('/api/v1/account/me', updates, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "first_name": "Alicia",
  "language": "es"
}

// Example Response (200 OK):
{
  "id": 12345,
  "email": "alice@example.com",
  "first_name": "Alicia",
  "last_name": "Johnson",
  "language": "es",
  "updated_at": "2025-12-01T11:00:00Z"
}

// DELETE /api/v1/account/logout
// Description: Terminate current user session and invalidate tokens
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface LogoutResponse {
  success: boolean;
  message: string;
}

const logout = async (): Promise<void> => {
  await api.delete('/api/v1/account/logout', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  
  // Clear local tokens
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// Example Response (200 OK):
{
  "success": true,
  "message": "Logged out successfully"
}

// POST /api/v1/account/refresh-token
// Description: Refresh expired access token using refresh token
// Authentication: Required (Refresh token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface RefreshTokenRequest {
  refresh_token: string;
}

// Response:
interface RefreshTokenResponse {
  access_token: string;
  expires_at: string;
  token_type: string;
}

const refreshAccessToken = async (): Promise<RefreshTokenResponse> => {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await api.post('/api/v1/account/refresh-token', {
    refresh_token: refreshToken
  });
  
  // Update stored access token
  localStorage.setItem('access_token', response.data.access_token);
  
  return response.data;
};

// Example Request:
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Example Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-12-02T12:00:00Z",
  "token_type": "Bearer"
}

// Example Error Response (401 Unauthorized - Invalid refresh token):
{
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Refresh token is invalid or expired",
    "details": {}
  }
}

// PUT /api/v1/account/password
// Description: Change current user's password
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface ChangePasswordRequest {
  current_password: string;
  new_password: string; // Min 8 chars, uppercase, lowercase, number
}

// Response:
interface ChangePasswordResponse {
  success: boolean;
  message: string;
}

const changePassword = async (
  passwords: ChangePasswordRequest
): Promise<ChangePasswordResponse> => {
  const response = await api.put('/api/v1/account/password', passwords, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "Password changed successfully"
}

// Example Error Response (401 Unauthorized - Wrong current password):
{
  "error": {
    "code": "INVALID_CURRENT_PASSWORD",
    "message": "Current password is incorrect",
    "details": {}
  }
}

// POST /api/v1/account/password-reset/request
// Description: Request password reset email with reset token
// Authentication: None (Public endpoint)
// Rate Limit: 3 requests per hour per email
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface PasswordResetRequest {
  email: string;
}

// Response:
interface PasswordResetResponse {
  success: boolean;
  message: string;
  email_sent: boolean;
}

const requestPasswordReset = async (
  email: string
): Promise<PasswordResetResponse> => {
  const response = await api.post('/api/v1/account/password-reset/request', {
    email
  });
  return response.data;
};

// Example Request:
{
  "email": "alice@example.com"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "If an account with this email exists, a password reset link has been sent",
  "email_sent": true
}

// Note: Always returns success to prevent email enumeration attacks

// POST /api/v1/account/password-reset/confirm
// Description: Reset password using token from email
// Authentication: None (Token-based)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface PasswordResetConfirmRequest {
  token: string; // Reset token from email
  new_password: string; // Min 8 chars, uppercase, lowercase, number
}

// Response:
interface PasswordResetConfirmResponse {
  success: boolean;
  message: string;
}

const confirmPasswordReset = async (
  token: string,
  newPassword: string
): Promise<PasswordResetConfirmResponse> => {
  const response = await api.post('/api/v1/account/password-reset/confirm', {
    token,
    new_password: newPassword
  });
  return response.data;
};

// Example Request:
{
  "token": "reset_tok_550e8400e29b41d4a716446655440000",
  "new_password": "NewSecurePass456!"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "Password reset successfully"
}

// Example Error Response (400 Bad Request - Expired token):
{
  "error": {
    "code": "RESET_TOKEN_EXPIRED",
    "message": "Password reset token has expired. Please request a new one.",
    "details": {
      "token_expires_at": "2025-12-01T10:00:00Z"
    }
  }
}

// POST /api/v1/account/email-verification/send
// Description: Send email verification link to user's email
// Authentication: Required (Bearer token)
// Rate Limit: 3 requests per hour
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface EmailVerificationSendResponse {
  success: boolean;
  message: string;
  email: string;
  expires_at: string;
}

const sendEmailVerification = async (): Promise<EmailVerificationSendResponse> => {
  const response = await api.post('/api/v1/account/email-verification/send', {}, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "message": "Verification email sent successfully",
  "email": "alice@example.com",
  "expires_at": "2025-12-01T11:30:00Z"
}

// PUT /api/v1/account/email-verification
// Description: Verify user's email using token from email link
// Authentication: Required (Bearer token) OR Token parameter
//
// Path Parameters: None
//
// Query Parameters:
//   - token: string - Verification token from email link
//
// Request Body: None (token in query param)

// Response:
interface EmailVerificationResponse {
  success: boolean;
  message: string;
  email_verified: boolean;
}

const verifyEmail = async (token: string): Promise<EmailVerificationResponse> => {
  const response = await api.put(`/api/v1/account/email-verification?token=${token}`);
  return response.data;
};

// Example Request:
// GET /api/v1/account/email-verification?token=verify_tok_550e8400e29b41d4a716

// Example Response (200 OK):
{
  "success": true,
  "message": "Email verified successfully",
  "email_verified": true
}

// Example Error Response (400 Bad Request - Invalid token):
{
  "error": {
    "code": "INVALID_VERIFICATION_TOKEN",
    "message": "Email verification token is invalid or expired",
    "details": {}
  }
}

// POST /api/v1/account/privy-login
// Description: Authenticate user via Privy (Web3 wallet, social, etc.)
// Authentication: None (Privy token-based)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface PrivyLoginRequest {
  privy_token: string; // Token from Privy SDK
  wallet_address?: string; // Optional wallet address
}

// Response:
interface PrivyLoginResponse {
  session_id: string;
  user_id: number;
  access_token: string;
  refresh_token: string;
  is_new_user: boolean; // True if user was created during login
}

const loginWithPrivy = async (
  privyToken: string,
  walletAddress?: string
): Promise<PrivyLoginResponse> => {
  const response = await api.post('/api/v1/account/privy-login', {
    privy_token: privyToken,
    wallet_address: walletAddress
  });
  
  // Store tokens
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Example Request:
{
  "privy_token": "privy_tok_abc123def456...",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}

// Example Response (200 OK - Existing user):
{
  "session_id": "sess_770e8400e29b41d4a716446655440000",
  "user_id": 12345,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "is_new_user": false
}

// Example Response (201 Created - New user):
{
  "session_id": "sess_880e8400e29b41d4a716446655440000",
  "user_id": 67890,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "is_new_user": true
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useAuth() {
  const queryClient = useQueryClient();
  
  const { data: user, isLoading } = useQuery({
    queryKey: ['current-user'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return null;
      
      const response = await api.get('/api/v1/account/me');
      return response.data;
    },
    retry: false,
  });
  
  const signup = useMutation({
    mutationFn: async (data: SignUpRequest) => {
      const response = await api.post('/api/v1/account/signup', data);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      queryClient.setQueryData(['current-user'], data);
      toast.success('Account created successfully!');
    },
  });
  
  const login = useMutation({
    mutationFn: async (credentials: LogInRequest) => {
      const response = await api.post('/api/v1/account/login', credentials);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Logged in successfully!');
    },
  });
  
  const logout = useMutation({
    mutationFn: async () => {
      await api.delete('/api/v1/account/logout');
    },
    onSuccess: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      queryClient.setQueryData(['current-user'], null);
      toast.success('Logged out successfully');
    },
  });
  
  const updateProfile = useMutation({
    mutationFn: async (updates: UpdateMeRequest) => {
      const response = await api.put('/api/v1/account/me', updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Profile updated successfully');
    },
  });
  
  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    signup: signup.mutate,
    login: login.mutate,
    logout: logout.mutate,
    updateProfile: updateProfile.mutate,
  };
}

// POST /api/wallet/send
interface SendRequest {
  to_address: string;
  token: string;
  amount: string;
  chain: string;
}

interface SendResponse {
  success: true;
  data: {
    transaction_id: string;
    tx_hash: string;
    status: 'pending' | 'submitted';
  };
}

// GET /api/wallet/send/estimate
interface EstimateSendRequest {
  to_address: string;
  token: string;
  amount: string;
  chain: string;
}

interface EstimateSendResponse {
  success: true;
  data: {
    gas_estimate_usd: number;
    gas_estimate_native: string;
  };
}

// GET /api/wallets
interface GetWalletsResponse {
  success: true;
  data: {
    total_balance_usd: number;
    wallets: Wallet[];
    assets: Asset[];
  };
}

interface Wallet {
  id: string;
  address: string;
  type: 'privy_mpc' | 'external';
  name?: string;
  is_primary: boolean;
  balance_usd: number;
  created_at: string;
  provider?: string;
}

interface Asset {
  token_address: string;
  symbol: string;
  name: string;
  logo_url?: string;
  chain: string;
  balance: string;
  balance_usd: number;
  price_usd: number;
  change_24h_percent: number;
  wallet_address: string;
}

// GET /api/wallets/assets?chain={chain}
interface GetAssetsByChainResponse {
  success: true;
  data: {
    chain: string;
    total_balance_usd: number;
    assets: Asset[];
  };
}

const walletAnimations = {
  balanceReveal: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.5 }
  },
  
  assetItem: {
    x: [-20, 0],
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'index * 0.05' }
  },
  
  chainFilterExpand: {
    height: ['0', 'auto'],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  priceChange: {
    color: 'direction === "up" ? "#10B981" : "#EF4444"',
    transition: { duration: 0.3 }
  }
};

interface AssetRowProps {
  asset: Asset;
  onPress: () => void;
  showChainBadge?: boolean;
}

interface ChainFilterProps {
  chains: Array<{ id: string; name: string; balance: number }>;
  selected: string;
  onSelect: (chainId: string) => void;
}

interface WalletCardProps {
  wallet: Wallet;
  onCopyAddress: () => void;
  onDisconnect?: () => void;
}

// GET /api/wallets/tokens/:symbol
interface GetTokenDetailResponse {
  success: true;
  data: {
    token: {
      symbol: string;
      name: string;
      logo_url?: string;
      description?: string;
      website?: string;
      contract_addresses: Record<string, string>;
    };
    balance: {
      total: string;
      total_usd: number;
      by_chain: Array<{
        chain: string;
        balance: string;
        balance_usd: number;
      }>;
    };
    price: {
      current_usd: number;
      change_24h: number;
      change_24h_percent: number;
      high_24h: number;
      low_24h: number;
    };
    chart_data: {
      period: string;
      points: TimeSeriesPoint[];
    };
    recent_transactions: Transaction[];
  };
}

const tokenAnimations = {
  priceUpdate: {
    scale: [1, 1.05, 1],
    color: ['current', 'highlight', 'current'],
    transition: { duration: 0.3 }
  },
  
  chartDraw: {
    pathLength: [0, 1],
    transition: { duration: 1, ease: 'easeInOut' }
  },
  
  holdingBar: {
    width: ['0%', 'percentage%'],
    transition: { duration: 0.5 }
  }
};

// GET /api/wallet/address
interface GetWalletAddressResponse {
  success: true;
  data: {
    address: string;
    supported_chains: Array<{
      chain_id: number;
      name: string;
      supported_tokens: string[];
    }>;
  };
}

// POST /api/v1/comparison/protocols
interface CompareProtocolsRequest {
  protocol_ids: string[]; // 2-5 protocol UUIDs
  dimensions?: string[]; // Optional: ['risk', 'yield', 'security', 'network']
}

interface ComparisonResponse {
  protocols: ProtocolDetail[];
  comparison_matrix: ComparisonMatrix;
  winner_by_dimension: Winners;
  trade_offs: TradeOff[];
  recommendation: AIRecommendation;
}

interface ProtocolDetail {
  protocol_id: string;
  name: string;
  chain: string;
  category: string;
  logo_url: string | null;
  risk: {
    score: number; // 0-10
    level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    confidence: number; // 0-1
    trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  };
  tvl: {
    current_usd: number;
    change_24h_percent: number;
    change_7d_percent: number;
  };
  yield: {
    supply_apy: number | null;
    borrow_apy: number | null;
    stake_apy: number | null;
  };
  security: {
    audit_count: number;
    auditors: string[];
    last_audit: string | null;
    vulnerabilities: number;
  };
  network: {
    users_24h: number | null;
    transactions_24h: number | null;
    centrality: number | null;
  };
  historical: {
    age_days: number;
    incidents: number;
  };
}

interface ComparisonMatrix {
  risk?: DimensionComparison;
  yield?: DimensionComparison;
  security?: DimensionComparison;
  network?: DimensionComparison;
}

interface DimensionComparison {
  metric: string;
  lower_is_better: boolean;
  values: ComparisonValue[];
  best: string; // Protocol name
  worst?: string;
}

interface ComparisonValue {
  protocol: string;
  value: number;
  label?: string;
  trend?: string;
  [key: string]: any; // Additional dimension-specific fields
}

interface Winners {
  safest?: string;
  highest_yield?: string;
  most_secure?: string;
  most_active?: string;
  balanced: string; // Overall best
}

interface TradeOff {
  dimension: string; // e.g., "Risk vs Yield"
  description: string;
}

interface AIRecommendation {
  recommended_protocol: string;
  reason: string;
  confidence: number; // 0-1
  alternatives: string[];
}

const compareProtocols = async (
  protocolIds: string[],
  dimensions?: string[]
): Promise<ComparisonResponse> => {
  const response = await api.post('/api/v1/comparison/protocols', {
    protocol_ids: protocolIds,
    dimensions,
  });
  return response.data;
};

import { motion } from 'framer-motion';

function ComparisonMatrix({ matrix, dimension }: ComparisonMatrixProps) {
  const comparison = matrix[dimension];
  
  return (
    <div className="space-y-3">
      <h3 className="font-bold text-lg uppercase">{dimension} Comparison</h3>
      
      {comparison.values.map((value, idx) => {
        const isWinner = value.protocol === comparison.best;
        
        return (
          <motion.div
            key={value.protocol}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className={`p-4 rounded-lg ${
              isWinner ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xl font-bold text-gray-400">
                  {idx + 1}.
                </span>
                <div>
                  <div className="font-semibold">{value.protocol}</div>
                  <div className="text-sm text-gray-600">
                    {value.label || value.trend}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: idx * 0.1 + 0.2, type: 'spring' }}
                  className="text-2xl font-bold"
                >
                  {value.value}
                </motion.span>
                {isWinner && (
                  <motion.span
                    initial={{ rotate: -180, scale: 0 }}
                    animate={{ rotate: 0, scale: 1 }}
                    transition={{ delay: idx * 0.1 + 0.3, type: 'spring' }}
                    className="text-2xl"
                  >
                    ★
                  </motion.span>
                )}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

function AIRecommendationCard({ recommendation }: AIRecommendationProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.8, type: 'spring', stiffness: 100 }}
      className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 border-2 border-blue-200 shadow-lg"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 1, type: 'spring', stiffness: 200 }}
        className="flex items-center gap-3 mb-4"
      >
        <span className="text-4xl">🤖</span>
        <div>
          <h3 className="font-bold text-xl">AI Recommendation</h3>
          <div className="text-sm text-gray-600">
            Confidence: {Math.round(recommendation.confidence * 100)}%
          </div>
        </div>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
      >
        <div className="text-2xl font-bold mb-2">
          {recommendation.recommended_protocol}
        </div>
        <p className="text-gray-700 mb-4">{recommendation.reason}</p>
        
        {recommendation.alternatives.length > 0 && (
          <div className="text-sm text-gray-600">
            <div className="font-semibold mb-1">Alternatives:</div>
            <div className="space-y-1">
              {recommendation.alternatives.map((alt) => (
                <div key={alt}>• {alt}</div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}

interface ComparisonScreenProps {
  selectedProtocols: string[];
  onBack: () => void;
}

function ComparisonScreen({ selectedProtocols, onBack }: ComparisonScreenProps) {
  const [dimensions, setDimensions] = useState(['risk', 'yield', 'security']);
  const { comparison, isLoading } = useProtocolComparison(
    selectedProtocols,
    dimensions
  );
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  return (
    <div className="p-4">
      <header className="flex items-center justify-between mb-6">
        <button onClick={onBack}>←</button>
        <h1 className="text-2xl font-bold">Comparison Results</h1>
        <button onClick={() => exportComparison(comparison)}>
          Export PDF
        </button>
      </header>
      
      {/* AI Recommendation */}
      <AIRecommendationCard recommendation={comparison.recommendation} />
      
      {/* Winners Summary */}
      <WinnersSummary winners={comparison.winner_by_dimension} />
      
      {/* Comparison Matrices */}
      {dimensions.map((dimension) => (
        <ComparisonMatrix
          key={dimension}
          matrix={comparison.comparison_matrix}
          dimension={dimension}
        />
      ))}
      
      {/* Tradeoffs */}
      <TradeoffsList tradeoffs={comparison.trade_offs} />
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';

export function useProtocolComparison(
  protocolIds: string[],
  dimensions?: string[]
) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['protocol-comparison', protocolIds, dimensions],
    queryFn: async () => {
      const response = await api.post('/api/v1/comparison/protocols', {
        protocol_ids: protocolIds,
        dimensions,
      });
      return response.data;
    },
    enabled: protocolIds.length >= 2 && protocolIds.length <= 5,
    staleTime: 300000, // 5 minutes
  });
  
  return {
    comparison: data,
    isLoading,
    error,
  };
}

const comparisonErrors = {
  COMPARE_001: 'Must compare 2-5 protocols',
  COMPARE_002: 'Protocol not found',
  COMPARE_003: 'Failed to fetch comparison data',
  COMPARE_004: 'Invalid comparison dimension',
};

try {
  const comparison = await compareProtocols(protocolIds);
} catch (error) {
  if (error.code === 'COMPARE_001') {
    toast.error('Please select 2-5 protocols to compare');
  } else {
    toast.error('Comparison failed. Please try again.');
  }
}

<table role="table" aria-label="Protocol comparison matrix">
  <thead>
    <tr role="row">
      <th role="columnheader">Metric</th>
      {protocols.map((p) => (
        <th key={p.id} role="columnheader">{p.name}</th>
      ))}
    </tr>
  </thead>
  <tbody>
    {/* Comparison rows */}
  </tbody>
</table>

describe('ProtocolComparison', () => {
  it('compares multiple protocols', async () => {
    const { getByText } = render(
      <ComparisonScreen selectedProtocols={['aave', 'compound']} onBack={jest.fn()} />
    );
    
    await waitFor(() => {
      expect(getByText('AI Recommendation')).toBeInTheDocument();
      expect(getByText('Aave V3')).toBeInTheDocument();
      expect(getByText('Compound V3')).toBeInTheDocument();
    });
  });
});

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

// POST /api/users/me/insights/{id}/dismiss
interface DismissInsightResponse {
  success: true;
}

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

// GET /api/v1/markets?risk_filter=LOW,MEDIUM&chain=Ethereum
interface GetMarketsResponse {
  success: true;
  data: {
    trending: EnhancedTokenPrice[];
    top_gainers: EnhancedTokenPrice[];
    top_losers: EnhancedTokenPrice[];
    safest: EnhancedTokenPrice[];  // NEW: Lowest risk
    defi_yields: DeFiYield[];
    personalized_recommendations?: EnhancedTokenPrice[];  // NEW
  };
}

interface EnhancedTokenPrice {
  // Original fields
  symbol: string;
  name: string;
  logo_url?: string;
  price_usd: number;
  change_24h_percent: number;
  volume_24h_usd: number;
  market_cap_usd: number;
  
  // NEW: ML Risk fields
  risk_score: number;  // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;  // 0-1
  risk_trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  
  // NEW: Protocol info
  protocol_id?: string;
  protocol_name?: string;
  chains: string[];
  categories: string[];
  
  // NEW: DeFi metrics
  tvl_usd?: number;
  tvl_change_24h_percent?: number;
}

interface DeFiYield {
  protocol: string;
  protocol_id: string;
  asset: string;
  apy: number;
  tvl_usd: number;
  risk_score: number;  // NEW
  risk_level: string;  // NEW
  chain: string;
}

// GET /api/v1/markets/:symbol/details
interface TokenDetailResponse {
  token: EnhancedTokenPrice;
  
  // ML Risk Analysis
  risk_analysis: {
    overall_risk: number;
    confidence: number;
    breakdown: {
      tvl_stability: { score: number; label: string };
      audit_history: { score: number; label: string };
      network_position: { score: number; label: string };
      historical_track: { score: number; label: string };
    };
    forecast_7d: 'INCREASING' | 'DECREASING' | 'STABLE';
    contributing_factors: Array<{
      feature: string;
      impact: number;
      explanation: string;
    }>;
  };
  
  // GraphRAG Similar Protocols
  similar_protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    risk_score: number;
    tvl_usd: number;
  }>;
  
  // Historical data
  price_history_7d: Array<{ timestamp: number; price: number }>;
  risk_history_7d: Array<{ timestamp: number; risk_score: number }>;
}

// POST /api/v1/markets/search
interface MarketSearchRequest {
  query: string;  // Natural language: "safe staking on Ethereum"
  filters?: {
    risk_levels?: string[];
    chains?: string[];
    categories?: string[];
    min_apy?: number;
    min_tvl?: number;
  };
  user_preferences?: boolean;  // Apply user risk tolerance
}

interface MarketSearchResponse {
  results: EnhancedTokenPrice[];
  filters_applied: {
    risk_tolerance: string;
    chains: string[];
    categories: string[];
  };
}

// Connect to markets WebSocket
const ws = new WebSocket(`wss://api.anvil.com/ws/markets`);

// Subscribe to price updates
ws.send(JSON.stringify({
  type: 'subscribe:markets',
  symbols: ['ETH', 'BTC', 'AAVE'],
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'price:update') {
    // { symbol, price_usd, change_24h_percent }
    updateTokenPrice(data);
  }
  
  if (data.type === 'risk:update') {
    // { protocol_id, risk_score, risk_level }
    updateRiskIndicator(data);
  }
};

// React Hook Example
function useMarketsPrices(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, number>>({});
  
  useEffect(() => {
    const ws = connectMarketsWebSocket();
    
    ws.send(JSON.stringify({
      type: 'subscribe:markets',
      symbols,
    }));
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'price:update') {
        setPrices(prev => ({
          ...prev,
          [data.symbol]: data.price_usd,
        }));
      }
    };
    
    return () => ws.close();
  }, [symbols]);
  
  return prices;
}

// Framer Motion: Risk badge entrance
<motion.div
  initial={{ scale: 0, opacity: 0 }}
  animate={{ scale: 1, opacity: 1 }}
  transition={{ type: 'spring', stiffness: 260, damping: 20 }}
>
  <RiskBadge score={2.1} />
</motion.div>

// React Native Reanimated: Risk color pulse
const riskPulse = useSharedValue(1);

useEffect(() => {
  if (riskLevel === 'HIGH' || riskLevel === 'CRITICAL') {
    riskPulse.value = withRepeat(
      withTiming(1.1, { duration: 1000 }),
      -1,
      true
    );
  }
}, [riskLevel]);

const animatedStyle = useAnimatedStyle(() => ({
  transform: [{ scale: riskPulse.value }],
}));

// Price change flash
const [priceFlash, setPriceFlash] = useState('none');

useEffect(() => {
  if (price > previousPrice) {
    setPriceFlash('green');
  } else if (price < previousPrice) {
    setPriceFlash('red');
  }
  
  const timer = setTimeout(() => setPriceFlash('none'), 300);
  return () => clearTimeout(timer);
}, [price]);

<motion.div
  animate={{
    backgroundColor: 
      priceFlash === 'green' ? '#10b98120' :
      priceFlash === 'red' ? '#ef444420' :
      'transparent'
  }}
  transition={{ duration: 0.3 }}
>
  ${price.toFixed(2)}
</motion.div>

interface MarketsScreenProps {
  initialTab?: 'trending' | 'gainers' | 'losers' | 'safest';
  riskFilter?: RiskLevel[];
}

interface TokenListItemProps {
  token: EnhancedTokenPrice;
  showRisk?: boolean;
  showSimilar?: boolean;
  onPress: (token: EnhancedTokenPrice) => void;
}

interface RiskBadgeProps {
  score: number;
  level: RiskLevel;
  confidence?: number;
  size?: 'sm' | 'md' | 'lg';
  animate?: boolean;
}

interface TokenDetailModalProps {
  symbol: string;
  onClose: () => void;
  onSupply?: () => void;
  onBorrow?: () => void;
}

interface MarketSearchBarProps {
  onSearch: (query: string) => void;
  onFilterPress: () => void;
  placeholder?: string;
}

const marketsErrors = {
  MARKETS_001: 'Failed to load market data',
  MARKETS_002: 'Risk data unavailable',
  MARKETS_003: 'WebSocket connection lost',
  MARKETS_004: 'Invalid risk filter',
  MARKETS_005: 'Search failed',
};

// Error recovery
try {
  const markets = await fetchMarkets();
} catch (error) {
  // Fallback to cached data
  const cached = await getCachedMarkets();
  if (cached) {
    showNotification('Using cached data', 'warning');
    return cached;
  }
  // Show error state
  showError(marketsErrors.MARKETS_001);
}

// GET /api/users/me/settings
interface GetUserSettingsResponse {
  success: true;
  data: {
    profile: {
      email: string;
      name?: string;
      kyc_status: string;
      subscription_plan: string;
    };
    security: {
      two_factor_enabled: boolean;
      biometric_enabled: boolean;
      auto_lock_minutes: number;
      transaction_confirm_threshold: number;
    };
    notifications: {
      push_enabled: boolean;
      transaction_completed: boolean;
      transaction_failed: boolean;
      large_transactions: boolean;
      position_alerts: boolean;
      price_alerts: boolean;
      marketing: boolean;
    };
    preferences: {
      theme: 'light' | 'dark' | 'system';
      default_chain: string;
      currency: string;
    };
  };
}

// PUT /api/users/me/settings
interface UpdateSettingsRequest {
  security?: Partial<SecuritySettings>;
  notifications?: Partial<NotificationSettings>;
  preferences?: Partial<PreferenceSettings>;
}

// GET /api/users/me
interface GetProfileResponse {
  success: true;
  data: {
    id: string;
    email: string;
    name?: string;
    phone?: string;
    avatar_url?: string;
    kyc_status: 'not_started' | 'pending' | 'verified' | 'rejected';
    subscription: {
      plan: string;
      status: string;
      price: number;
      next_billing_date?: string;
    };
    created_at: string;
  };
}

// PUT /api/users/me
interface UpdateProfileRequest {
  name?: string;
  phone?: string;
  avatar_url?: string;
}

// GET /api/v1/users/me/preferences
// Description: Get all user preferences including risk tolerance, chains, notifications
// Authentication: Required (Bearer token)
// Query Parameters: None
// Path Parameters: None

interface UserPreferencesResponse {
  user_id: string;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  preferred_chains: string[];
  preferred_chains: string[];
  preferred_categories: string[];
  excluded_protocols: string[];
  favorite_protocols: string[];
  search_settings: {
    default_similarity_threshold: number;
    default_risk_filter: string | null;
    search_history_enabled: boolean;
  };
  notification_settings: {
    risk_alerts_enabled: boolean;
    push_enabled: boolean;
    min_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  };
  default_currency: string;
  theme: 'dark' | 'light';
}

const getPreferences = async (): Promise<UserPreferencesResponse> => {
  const response = await api.get('/api/v1/users/me/preferences');
  return response.data;
};

// Example Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_tolerance": "moderate",
  "preferred_chains": ["ethereum", "arbitrum", "optimism"],
  "preferred_categories": ["lending", "dex", "liquid-staking"],
  "excluded_protocols": ["risky-protocol-id"],
  "favorite_protocols": ["aave-v3", "compound-v3", "uniswap-v3"],
  "search_settings": {
    "default_similarity_threshold": 0.7,
    "default_risk_filter": "MEDIUM",
    "search_history_enabled": true
  },
  "notification_settings": {
    "risk_alerts_enabled": true,
    "push_enabled": true,
    "min_severity": "MEDIUM"
  },
  "default_currency": "USD",
  "theme": "dark"
}

// PUT /api/v1/users/me/preferences/risk-tolerance
interface UpdateRiskToleranceRequest {
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
}

const updateRiskTolerance = async (
  riskTolerance: string
): Promise<UserPreferencesResponse> => {
  const response = await api.put(
    '/api/v1/users/me/preferences/risk-tolerance',
    { risk_tolerance: riskTolerance }
  );
  return response.data;
};

// PUT /api/v1/users/me/preferences/chains
interface UpdateChainPreferencesRequest {
  preferred_chains: string[];
}

const updateChainPreferences = async (
  chains: string[]
): Promise<UserPreferencesResponse> => {
  const response = await api.put('/api/v1/users/me/preferences/chains', {
    preferred_chains: chains,
  });
  return response.data;
};

// POST /api/v1/users/me/preferences/search/saved
interface SaveSearchRequest {
  name: string;
  query: string;
  filters: Record<string, any>;
}

interface SavedSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: Record<string, any>;
  created_at: string;
}

const saveSearch = async (
  search: SaveSearchRequest
): Promise<SavedSearchResponse> => {
  const response = await api.post(
    '/api/v1/users/me/preferences/search/saved',
    search
  );
  return response.data;
};

// DELETE /api/v1/users/me/preferences/search/saved/:search_id
const deleteSavedSearch = async (searchId: string): Promise<void> => {
  await api.delete(`/api/v1/users/me/preferences/search/saved/${searchId}`);
};

// POST /api/v1/users/me/preferences/favorites/protocols/:protocol_id
const addFavoriteProtocol = async (protocolId: string): Promise<void> => {
  await api.post(
    `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
  );
};

// DELETE /api/v1/users/me/preferences/favorites/protocols/:protocol_id
const removeFavoriteProtocol = async (protocolId: string): Promise<void> => {
  await api.delete(
    `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
  );
};

import { motion } from 'framer-motion';

function PreferenceCard({ title, value, onChange }: PreferenceCardProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  
  const handleChange = async (newValue: any) => {
    setIsUpdating(true);
    await onChange(newValue);
    setIsUpdating(false);
  };
  
  return (
    <motion.div
      animate={{
        scale: isUpdating ? 0.98 : 1,
        opacity: isUpdating ? 0.6 : 1,
      }}
      transition={{ duration: 0.2 }}
      className="bg-white rounded-lg p-4 border border-gray-200"
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold">{title}</span>
        {isUpdating && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            ⟳
          </motion.div>
        )}
      </div>
      <div className="mt-2">{value}</div>
    </motion.div>
  );
}

function RiskToleranceSelector({ value, onChange }: RiskToleranceSelectorProps) {
  const options = [
    {
      value: 'conservative',
      label: 'Conservative',
      icon: '🛡️',
      color: '#10B981',
    },
    { value: 'moderate', label: 'Moderate', icon: '⚖️', color: '#3B82F6' },
    { value: 'aggressive', label: 'Aggressive', icon: '⚡', color: '#EF4444' },
  ];
  
  return (
    <div className="space-y-3">
      {options.map((option) => (
        <motion.button
          key={option.value}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          animate={{
            borderColor: value === option.value ? option.color : '#E5E7EB',
            backgroundColor:
              value === option.value ? `${option.color}10` : 'white',
          }}
          onClick={() => onChange(option.value)}
          className="w-full p-4 border-2 rounded-xl text-left"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{option.icon}</span>
              <div>
                <div className="font-bold">{option.label}</div>
                <div className="text-sm text-gray-600">
                  {option.value === 'conservative' && 'Maximum safety'}
                  {option.value === 'moderate' && 'Balanced approach'}
                  {option.value === 'aggressive' && 'Higher risk tolerance'}
                </div>
              </div>
            </div>
            {value === option.value && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                style={{ color: option.color }}
              >
                ✓
              </motion.div>
            )}
          </div>
        </motion.button>
      ))}
    </div>
  );
}

function SaveSearchButton({ onSave }: SaveSearchButtonProps) {
  const [saved, setSaved] = useState(false);
  
  const handleSave = async () => {
    await onSave();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };
  
  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={handleSave}
      className="px-4 py-2 rounded-lg"
      animate={{
        backgroundColor: saved ? '#10B981' : '#3B82F6',
      }}
    >
      <motion.div
        animate={{
          x: saved ? [0, 10, 0] : 0,
        }}
        transition={{ duration: 0.5 }}
        className="flex items-center gap-2 text-white"
      >
        {saved ? '✓ Saved!' : '💾 Save Search'}
      </motion.div>
    </motion.button>
  );
}

import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

function PreferenceToggle({ value, onToggle, label }: ToggleProps) {
  const offset = useSharedValue(value ? 1 : 0);
  const backgroundColor = useSharedValue(value ? '#10B981' : '#D1D5DB');
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: withSpring(offset.value * 24) }],
  }));
  
  const containerStyle = useAnimatedStyle(() => ({
    backgroundColor: withTiming(backgroundColor.value),
  }));
  
  const handleToggle = () => {
    const newValue = !value;
    offset.value = newValue ? 1 : 0;
    backgroundColor.value = newValue ? '#10B981' : '#D1D5DB';
    onToggle(newValue);
  };
  
  return (
    <View style={styles.toggleContainer}>
      <Text style={styles.label}>{label}</Text>
      <Pressable onPress={handleToggle}>
        <Animated.View style={[styles.track, containerStyle]}>
          <Animated.View style={[styles.thumb, animatedStyle]} />
        </Animated.View>
      </Pressable>
    </View>
  );
}

interface PreferencesScreenProps {
  userId: string;
}

function PreferencesScreen({ userId }: PreferencesScreenProps) {
  const { preferences, isLoading, updatePreference } = usePreferences();
  
  const sections = [
    {
      title: 'Risk & Safety',
      items: [
        {
          id: 'risk-tolerance',
          icon: '🎯',
          label: 'Risk Tolerance',
          value: preferences?.risk_tolerance || 'moderate',
          route: '/settings/preferences/risk-tolerance',
        },
        {
          id: 'excluded-protocols',
          icon: '⛔',
          label: 'Excluded Protocols',
          value: `${preferences?.excluded_protocols.length || 0} blocked`,
          route: '/settings/preferences/excluded-protocols',
        },
      ],
    },
    {
      title: 'DeFi Preferences',
      items: [
        {
          id: 'chains',
          icon: '⛓️',
          label: 'Preferred Chains',
          value: preferences?.preferred_chains.slice(0, 2).join(', ') || '',
          route: '/settings/preferences/chains',
        },
        {
          id: 'favorites',
          icon: '⭐',
          label: 'Favorite Protocols',
          value: `${preferences?.favorite_protocols.length || 0} favorites`,
          route: '/settings/preferences/favorites',
        },
      ],
    },
    // ... more sections
  ];
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  return (
    <ScrollView style={styles.container}>
      {sections.map((section) => (
        <PreferenceSection key={section.title} section={section} />
      ))}
    </ScrollView>
  );
}

interface RiskToleranceSelectorProps {
  value: 'conservative' | 'moderate' | 'aggressive';
  onChange: (value: string) => Promise<void>;
}

function RiskToleranceSelector({ value, onChange }: RiskToleranceSelectorProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  
  const handleSelect = async (newValue: string) => {
    setIsUpdating(true);
    try {
      await onChange(newValue);
      toast.success('Risk tolerance updated');
    } catch (error) {
      toast.error('Failed to update risk tolerance');
    } finally {
      setIsUpdating(false);
    }
  };
  
  return (
    <div className="space-y-4">
      <p className="text-gray-600">
        Choose your risk comfort level. This affects protocol recommendations
        and risk warnings.
      </p>
      <RiskOptions
        value={value}
        onChange={handleSelect}
        disabled={isUpdating}
      />
    </div>
  );
}

interface SavedSearchesListProps {
  searches: SavedSearch[];
  onRun: (search: SavedSearch) => void;
  onDelete: (searchId: string) => Promise<void>;
}

function SavedSearchesList({ searches, onRun, onDelete }: SavedSearchesListProps) {
  return (
    <div className="space-y-3">
      {searches.map((search) => (
        <SavedSearchCard
          key={search.id}
          search={search}
          onRun={() => onRun(search)}
          onDelete={() => onDelete(search.id)}
        />
      ))}
      
      {searches.length === 0 && (
        <EmptyState
          icon="💾"
          title="No saved searches"
          description="Save your frequent search configurations for quick access"
        />
      )}
      
      {searches.length < 10 && (
        <Link to="/settings/preferences/saved-searches/new">
          <button className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600">
            + Create New Saved Search
          </button>
        </Link>
      )}
    </div>
  );
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function usePreferences() {
  const queryClient = useQueryClient();
  
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user-preferences'],
    queryFn: async () => {
      const response = await api.get('/api/v1/users/me/preferences');
      return response.data;
    },
  });
  
  const updateRiskTolerance = useMutation({
    mutationFn: async (riskTolerance: string) => {
      await api.put('/api/v1/users/me/preferences/risk-tolerance', {
        risk_tolerance: riskTolerance,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  const updateChainPreferences = useMutation({
    mutationFn: async (chains: string[]) => {
      await api.put('/api/v1/users/me/preferences/chains', {
        preferred_chains: chains,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  const addFavoriteProtocol = useMutation({
    mutationFn: async (protocolId: string) => {
      await api.post(
        `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  const removeFavoriteProtocol = useMutation({
    mutationFn: async (protocolId: string) => {
      await api.delete(
        `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  return {
    preferences,
    isLoading,
    updateRiskTolerance: updateRiskTolerance.mutate,
    updateChainPreferences: updateChainPreferences.mutate,
    addFavoriteProtocol: addFavoriteProtocol.mutate,
    removeFavoriteProtocol: removeFavoriteProtocol.mutate,
  };
}

export function useSavedSearches() {
  const queryClient = useQueryClient();
  
  const saveSearch = useMutation({
    mutationFn: async (search: SaveSearchRequest) => {
      const response = await api.post(
        '/api/v1/users/me/preferences/search/saved',
        search
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
      toast.success('Search saved successfully');
    },
  });
  
  const deleteSavedSearch = useMutation({
    mutationFn: async (searchId: string) => {
      await api.delete(
        `/api/v1/users/me/preferences/search/saved/${searchId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
      toast.success('Search deleted');
    },
  });
  
  return {
    saveSearch: saveSearch.mutate,
    deleteSavedSearch: deleteSavedSearch.mutate,
    isSaving: saveSearch.isPending,
  };
}

const preferenceErrors = {
  PREF_001: 'Failed to load preferences',
  PREF_002: 'Invalid risk tolerance value',
  PREF_003: 'Too many preferred chains (max 10)',
  PREF_004: 'Too many favorite protocols (max 20)',
  PREF_005: 'Too many saved searches (max 10)',
  PREF_006: 'Failed to save preference',
  PREF_007: 'Search name already exists',
};

// Handle preference update error
try {
  await updateRiskTolerance('conservative');
} catch (error) {
  if (error.code === 'PREF_002') {
    toast.error('Invalid risk tolerance selected');
  } else {
    toast.error('Failed to update preference. Please try again.');
  }
}

<button
  aria-label={`Set risk tolerance to ${option.label}. ${option.description}`}
  role="radio"
  aria-checked={value === option.value}
  onClick={() => onChange(option.value)}
>
  {option.label}
</button>

function PreferencesList({ sections }: PreferencesListProps) {
  const handleKeyPress = (e: KeyboardEvent, route: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      navigate(route);
    }
  };
  
  return (
    <div role="list">
      {sections.map((section) => (
        <div key={section.title} role="listitem">
          {section.items.map((item, idx) => (
            <div
              key={item.id}
              role="button"
              tabIndex={0}
              onKeyPress={(e) => handleKeyPress(e, item.route)}
            >
              {item.label}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// Validate before sending to backend
const validatePreferences = (prefs: Partial<UserPreferences>) => {
  if (prefs.risk_tolerance) {
    if (!['conservative', 'moderate', 'aggressive'].includes(prefs.risk_tolerance)) {
      throw new Error('Invalid risk tolerance');
    }
  }
  
  if (prefs.preferred_chains) {
    if (prefs.preferred_chains.length > 10) {
      throw new Error('Too many chains selected');
    }
  }
  
  if (prefs.favorite_protocols) {
    if (prefs.favorite_protocols.length > 20) {
      throw new Error('Too many favorite protocols');
    }
  }
  
  return true;
};

describe('PreferencesScreen', () => {
  it('loads and displays user preferences', async () => {
    const { getByText } = render(<PreferencesScreen userId="123" />);
    
    await waitFor(() => {
      expect(getByText('Risk Tolerance')).toBeInTheDocument();
      expect(getByText('Moderate')).toBeInTheDocument();
    });
  });
  
  it('updates risk tolerance', async () => {
    const { getByText } = render(<RiskToleranceSelector value="moderate" onChange={mockOnChange} />);
    
    fireEvent.click(getByText('Conservative'));
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith('conservative');
    });
  });
  
  it('manages favorite protocols', async () => {
    const { getByTestId } = render(<FavoritesList favorites={mockFavorites} />);
    
    fireEvent.click(getByTestId('remove-favorite-aave'));
    
    await waitFor(() => {
      expect(mockRemoveFavorite).toHaveBeenCalledWith('aave-id');
    });
  });
});

// GET /api/referrals
interface GetReferralsResponse {
  success: true;
  data: {
    referral_code: string;
    referral_link: string;
    reward_amount: number;
    stats: {
      invited_count: number;
      completed_count: number;
      total_earned_usd: number;
    };
    referrals: Array<{
      id: string;
      email_masked: string;
      status: 'pending' | 'complete';
      joined_at: string;
      completed_at?: string;
      reward_earned?: number;
    }>;
  };
}

// GET /api/users/me/subscription
interface GetSubscriptionResponse {
  success: true;
  data: {
    plan: 'free' | 'pro' | 'elite';
    status: 'active' | 'canceled' | 'past_due';
    price: number;
    billing_period: 'monthly' | 'annual';
    next_billing_date?: string;
    cancel_at_period_end?: boolean;
    features: string[];
    payment_method?: {
      type: string;
      last4: string;
    };
  };
}

// POST /api/users/me/subscription/change
interface ChangeSubscriptionRequest {
  plan: 'free' | 'pro' | 'elite';
  billing_period?: 'monthly' | 'annual';
}

// POST /api/users/me/subscription/cancel
interface CancelSubscriptionResponse {
  success: true;
  data: {
    cancel_at_period_end: true;
    end_date: string;
  };
}

// GET /api/support/articles
interface GetHelpArticlesResponse {
  success: true;
  data: {
    popular: HelpArticle[];
    categories: Array<{
      id: string;
      name: string;
      icon: string;
      description: string;
      article_count: number;
    }>;
  };
}

interface HelpArticle {
  id: string;
  title: string;
  category: string;
  excerpt: string;
  content?: string;
  video_url?: string;
  related_articles?: string[];
}

// POST /api/support/tickets
interface CreateSupportTicketRequest {
  topic: string;
  subject: string;
  description: string;
  attachments?: string[];
}

interface CreateSupportTicketResponse {
  success: true;
  data: {
    ticket_id: string;
    status: 'open';
    estimated_response_hours: number;
  };
}

// POST /api/v1/markets/advanced-search
interface AdvancedMarketsSearchRequest {
  query?: string; // Natural language or protocol name
  chains?: string[];
  categories?: string[];
  min_tvl?: number;
  max_tvl?: number;
  min_risk_score?: number;
  max_risk_score?: number;
  sort_by?: 'tvl' | 'apy' | 'risk' | 'volume';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  enable_graphrag?: boolean;
}

interface AdvancedMarketsSearchResponse {
  protocols: ProtocolResult[];
  total: number;
  filters_applied: Record<string, any>;
  search_metadata?: {
    search_type: 'semantic' | 'graph' | 'hybrid';
    query_expanded: boolean;
  };
}

interface ProtocolResult {
  protocol_id: string;
  protocol_name: string;
  chain: string;
  category: string;
  tvl_usd: number;
  apy_supply: number | null;
  risk_score: number; // 0-10 (ML-powered)
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  audit_count: number;
  logo_url: string | null;
  similarity_score?: number; // If GraphRAG search
}

const advancedSearch = async (
  filters: AdvancedMarketsSearchRequest
): Promise<AdvancedMarketsSearchResponse> => {
  const response = await api.post('/api/v1/markets/advanced-search', filters);
  return response.data;
};

// POST /api/v1/comparison/protocols
// See FRONTEND_USER_PROTOCOL_COMPARISON.md for full details

const compareProtocols = async (
  protocolIds: string[],
  dimensions?: string[]
): Promise<ComparisonResponse> => {
  const response = await api.post('/api/v1/comparison/protocols', {
    protocol_ids: protocolIds,
    dimensions,
  });
  return response.data;
};

export function useAdvancedMarkets(filters: AdvancedMarketsSearchRequest) {
  const { data, isLoading } = useQuery({
    queryKey: ['advanced-markets', filters],
    queryFn: async () => {
      const response = await api.post('/api/v1/markets/advanced-search', filters);
      return response.data;
    },
    enabled: Object.keys(filters).length > 0,
  });
  
  return {
    protocols: data?.protocols || [],
    total: data?.total || 0,
    metadata: data?.search_metadata,
    isLoading,
  };
}

// GET /api/v1/defi/supply/markets
interface GetSupplyMarketsResponse {
  success: true;
  data: {
    user_summary: {
      total_supplied_usd: number;
      avg_apy: number;
      total_earned_usd: number;
      portfolio_risk_score: number;  // NEW
      portfolio_risk_level: string;  // NEW
    };
    positions: EnhancedSupplyPosition[];
    available_markets: EnhancedSupplyMarket[];
  };
}

interface EnhancedSupplyPosition {
  id: string;
  token: TokenInfo;
  protocol: string;
  protocol_id: string;  // NEW
  chain: string;
  supplied_amount: string;
  supplied_usd: number;
  apy: number;
  earned_usd: number;
  is_collateral: boolean;
  
  // NEW: ML Risk fields
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  risk_trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  
  // NEW: Alerts
  has_alerts: boolean;
  alert_count: number;
}

interface EnhancedSupplyMarket {
  token: TokenInfo;
  protocol: string;
  protocol_id: string;  // NEW
  chain: string;
  apy: number;
  total_supplied_usd: number;
  available_balance: string;
  available_balance_usd: number;
  
  // NEW: ML Risk fields
  risk_score: number;
  risk_level: string;
  confidence: number;
  tvl_usd: number;
  tvl_change_7d_percent: number;
}

// POST /api/v1/defi/supply
interface SupplyRequest {
  token: string;
  amount: string;
  protocol_id: string;  // Changed from protocol name to ID
  chain: string;
  use_as_collateral: boolean;
  risk_acknowledged?: boolean;  // NEW: Required if risk > 5.0
}

interface SupplyResponse {
  success: boolean;
  transaction_hash?: string;
  
  // NEW: Risk check
  risk_check: {
    risk_score: number;
    risk_level: string;
    requires_acknowledgment: boolean;
    warnings: string[];
    alternatives?: Array<{
      protocol_id: string;
      protocol_name: string;
      apy: number;
      risk_score: number;
      similarity_score: number;
    }>;
  };
}

// POST /api/v1/defi/supply/compare
interface CompareSupplyProtocolsRequest {
  token: string;
  amount: string;
  protocol_ids: string[];  // 2-5 protocols
}

interface CompareSupplyProtocolsResponse {
  comparisons: Array<{
    protocol_id: string;
    protocol_name: string;
    apy: number;
    risk_score: number;
    risk_level: string;
    tvl_usd: number;
    estimated_yearly_earnings: number;
    pros: string[];
    cons: string[];
  }>;
  recommendation: {
    protocol_id: string;
    reason: string;
    confidence: number;
  };
}

// Subscribe to supply APY updates
ws.send(JSON.stringify({
  type: 'subscribe:supply',
  protocols: ['aave-v3', 'compound'],
  tokens: ['USDC', 'ETH'],
}));

// Receive APY updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'apy:update') {
    // { protocol_id, token, apy_supply, apy_borrow }
    updateAPY(data);
  }
  
  if (data.type === 'risk:update') {
    // { protocol_id, risk_score, risk_level }
    updateRiskIndicator(data);
  }
};

// High risk warning shake
<motion.div
  initial={{ x: 0 }}
  animate={{ 
    x: isHighRisk ? [-10, 10, -10, 10, 0] : 0 
  }}
  transition={{ 
    duration: 0.4,
    times: [0, 0.25, 0.5, 0.75, 1]
  }}
>
  <RiskWarning />
</motion.div>

// Risk badge pulse for critical
const riskPulse = useSharedValue(1);

useEffect(() => {
  if (riskLevel === 'CRITICAL') {
    riskPulse.value = withRepeat(
      withSequence(
        withTiming(1.2, { duration: 500 }),
        withTiming(1, { duration: 500 })
      ),
      -1
    );
  }
}, [riskLevel]);

interface SupplyMarketsProps {
  sortBy?: 'safety' | 'apy' | 'tvl';
  riskFilter?: RiskLevel[];
}

interface SupplyFormProps {
  token: string;
  protocol: Protocol;
  onSubmit: (data: SupplyRequest) => void;
  showRiskAnalysis?: boolean;
}

interface RiskWarningModalProps {
  protocol: Protocol;
  amount: string;
  alternatives: Protocol[];
  onProceed: () => void;
  onSelectAlternative: (protocolId: string) => void;
  onCancel: () => void;
}

interface ProtocolComparisonProps {
  protocols: Protocol[];
  token: string;
  amount: string;
  onSelect: (protocolId: string) => void;
}

const supplyErrors = {
  SUPPLY_001: 'Insufficient balance',
  SUPPLY_002: 'Amount below minimum',
  SUPPLY_003: 'Protocol risk too high',
  SUPPLY_004: 'Risk acknowledgment required',
  SUPPLY_005: 'Transaction failed',
};

// Risk threshold checks
if (riskScore > 7.0 && !risk_acknowledged) {
  throw new Error(supplyErrors.SUPPLY_004);
}

// Show alternatives for high risk
if (riskScore > 5.0) {
  const alternatives = await getAlternativeProtocols(protocol_id);
  showRiskWarningModal({ protocol, alternatives });
}

// GET /api/defi/earn/overview
interface GetEarnOverviewResponse {
  success: true;
  data: {
    summary: {
      total_value_usd: number;
      avg_apy: number;
      total_earned_usd: number;
    };
    positions: Array<{
      id: string;
      type: 'stake' | 'supply' | 'liquidity';
      protocol: string;
      token: TokenInfo;
      amount: string;
      value_usd: number;
      apy: number;
      earned_usd: number;
    }>;
    opportunities: Array<{
      token: TokenInfo;
      type: 'stake' | 'supply' | 'liquidity';
      protocol: string;
      apy: number;
      tvl_usd: number;
    }>;
  };
}

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

// DELETE /api/v1/alerts/risk/:alert_id
const dismissAlert = async (alertId: string): Promise<void> => {
  await api.delete(`/api/v1/alerts/risk/${alertId}`);
};

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

// POST /api/v1/alerts/subscription/protocols/:protocol_id
const subscribeToProtocol = async (protocolId: string): Promise<void> => {
  await api.post(`/api/v1/alerts/subscription/protocols/${protocolId}`);
};

// DELETE /api/v1/alerts/subscription/protocols/:protocol_id
const unsubscribeFromProtocol = async (protocolId: string): Promise<void> => {
  await api.delete(`/api/v1/alerts/subscription/protocols/${protocolId}`);
};

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

<button
  aria-label={`Acknowledge ${alert.severity} risk alert for ${alert.protocol_name}. ${alert.message}`}
  onClick={() => onAcknowledge(alert.id, false)}
>
  Acknowledge
</button>

<div role="alert" aria-live="assertive" aria-atomic="true">
  {alert.severity === 'CRITICAL' && (
    <span className="sr-only">
      Critical risk alert for {alert.protocol_name}: {alert.message}
    </span>
  )}
</div>

// Backend validates alert belongs to user
if (alert.user_id !== currentUser.id) {
  throw new UnauthorizedError('Not your alert');
}

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

// GET /api/v1/notifications/?page=1&per_page=10
// Description: Get paginated list of user's notifications
// Authentication: Required (Bearer token)
//
// Path Parameters: None
//
// Query Parameters:
//   - page: number - Page number (default: 1, min: 1)
//   - per_page: number - Items per page (default: 10, max: 100)

// Response:
interface NotificationListResponse {
  items: Notification[];
  page: number;
  per_page: number;
  total: number;
  unread_count: number;
}

interface Notification {
  id: string;
  user_id: number;
  title: string;
  body: string;
  category: 'info' | 'warning' | 'success' | 'error';
  action_url?: string; // Optional deep link
  action_text?: string; // Optional action button text
  read: boolean;
  created_at: string;
  read_at?: string;
}

const getNotifications = async (
  page: number = 1,
  perPage: number = 10
): Promise<NotificationListResponse> => {
  const response = await api.get('/api/v1/notifications/', {
    params: { page, per_page: perPage },
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/notifications/?page=1&per_page=20

// Example Response (200 OK):
{
  "items": [
    {
      "id": "notif_123",
      "user_id": 12345,
      "title": "Subscription Renewed",
      "body": "Your PRO subscription has been renewed successfully for another month",
      "category": "success",
      "action_url": "/settings/subscription",
      "action_text": "View Details",
      "read": false,
      "created_at": "2025-12-01T08:00:00Z",
      "read_at": null
    },
    {
      "id": "notif_122",
      "user_id": 12345,
      "title": "Risk Alert: High Volatility",
      "body": "AAVE protocol detected high volatility. Review your positions.",
      "category": "warning",
      "action_url": "/alerts/notif_122",
      "action_text": "View Alert",
      "read": true,
      "created_at": "2025-11-30T14:30:00Z",
      "read_at": "2025-11-30T15:00:00Z"
    },
    {
      "id": "notif_121",
      "user_id": 12345,
      "title": "New Feature Available",
      "body": "GraphRAG search is now available! Try semantic search across protocols.",
      "category": "info",
      "action_url": "/search",
      "action_text": "Try It Now",
      "read": true,
      "created_at": "2025-11-29T10:00:00Z",
      "read_at": "2025-11-29T12:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 45,
  "unread_count": 8
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}

// PUT /api/v1/notifications/{notification_id}/read
// Description: Mark a specific notification as read
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - notification_id: string - ID of the notification to mark as read
//
// Query Parameters: None
// Request Body: None

// Response:
interface MarkReadResponse {
  success: boolean;
  notification_id: string;
  read_at: string;
}

const markNotificationAsRead = async (
  notificationId: string
): Promise<MarkReadResponse> => {
  const response = await api.put(
    `/api/v1/notifications/${notificationId}/read`,
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
// PUT /api/v1/notifications/notif_123/read

// Example Response (200 OK):
{
  "success": true,
  "notification_id": "notif_123",
  "read_at": "2025-12-01T12:00:00Z"
}

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "Notification with ID 'notif_999' not found",
    "details": {
      "notification_id": "notif_999"
    }
  }
}

// PUT /api/v1/notifications/read-all
// Description: Mark all user's notifications as read
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface MarkAllReadResponse {
  success: boolean;
  count: number; // Number of notifications marked as read
}

const markAllNotificationsAsRead = async (): Promise<MarkAllReadResponse> => {
  const response = await api.put(
    '/api/v1/notifications/read-all',
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "count": 8
}

// DELETE /api/v1/notifications/{notification_id}
// Description: Delete a specific notification
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - notification_id: string - ID of the notification to delete
//
// Query Parameters: None
// Request Body: None

// Response:
interface DeleteNotificationResponse {
  success: boolean;
  notification_id: string;
}

const deleteNotification = async (
  notificationId: string
): Promise<DeleteNotificationResponse> => {
  const response = await api.delete(
    `/api/v1/notifications/${notificationId}`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "notification_id": "notif_123"
}

// GET /api/v1/notifications/unread-count
// Description: Get count of unread notifications (for badge display)
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface UnreadCountResponse {
  unread_count: number;
}

const getUnreadCount = async (): Promise<UnreadCountResponse> => {
  const response = await api.get('/api/v1/notifications/unread-count', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "unread_count": 8
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useNotifications(page: number = 1, perPage: number = 10) {
  const queryClient = useQueryClient();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', page, perPage],
    queryFn: async () => {
      const response = await api.get('/api/v1/notifications/', {
        params: { page, per_page: perPage }
      });
      return response.data;
    },
  });
  
  const markAsRead = useMutation({
    mutationFn: async (notificationId: string) => {
      const response = await api.put(
        `/api/v1/notifications/${notificationId}/read`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });
  
  const markAllAsRead = useMutation({
    mutationFn: async () => {
      const response = await api.put('/api/v1/notifications/read-all');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
      toast.success('All notifications marked as read');
    },
  });
  
  const deleteNotification = useMutation({
    mutationFn: async (notificationId: string) => {
      await api.delete(`/api/v1/notifications/${notificationId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast.success('Notification deleted');
    },
  });
  
  return {
    notifications: data?.items || [],
    page: data?.page || 1,
    perPage: data?.per_page || 10,
    total: data?.total || 0,
    unreadCount: data?.unread_count || 0,
    isLoading,
    error,
    markAsRead: markAsRead.mutate,
    markAllAsRead: markAllAsRead.mutate,
    deleteNotification: deleteNotification.mutate,
  };
}

export function useUnreadCount() {
  const { data, isLoading } = useQuery({
    queryKey: ['unread-count'],
    queryFn: async () => {
      const response = await api.get('/api/v1/notifications/unread-count');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
  
  return {
    unreadCount: data?.unread_count || 0,
    isLoading,
  };
}

export function NotificationBadge() {
  const { unreadCount } = useUnreadCount();
  
  if (unreadCount === 0) return null;
  
  return (
    <span className="notification-badge">
      {unreadCount > 99 ? '99+' : unreadCount}
    </span>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onRead: (id: string) => void;
  onDelete: (id: string) => void;
}

export function NotificationItem({ 
  notification, 
  onRead, 
  onDelete 
}: NotificationItemProps) {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  };
  
  return (
    <div className={`notification-item ${notification.read ? 'read' : 'unread'}`}>
      <div className="notification-icon">
        {getCategoryIcon(notification.category)}
      </div>
      
      <div className="notification-content">
        <h4>{notification.title}</h4>
        <p>{notification.body}</p>
        <span className="notification-time">
          {formatDistanceToNow(new Date(notification.created_at))} ago
        </span>
      </div>
      
      <div className="notification-actions">
        {!notification.read && (
          <button onClick={() => onRead(notification.id)}>
            Mark as read
          </button>
        )}
        
        {notification.action_url && (
          <Link to={notification.action_url}>
            {notification.action_text || 'View'}
          </Link>
        )}
        
        <button onClick={() => onDelete(notification.id)}>
          Delete
        </button>
      </div>
    </div>
  );
}

const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.log('Browser does not support notifications');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  
  return false;
};

// Usage in app initialization
useEffect(() => {
  requestNotificationPermission();
}, []);

const showBrowserNotification = (notification: Notification) => {
  if (Notification.permission === 'granted') {
    const notif = new Notification(notification.title, {
      body: notification.body,
      icon: '/notification-icon.png',
      badge: '/badge-icon.png',
      tag: notification.id,
      requireInteraction: notification.category === 'error',
    });
    
    notif.onclick = () => {
      window.focus();
      if (notification.action_url) {
        window.location.href = notification.action_url;
      }
      notif.close();
    };
  }
};

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

// GET /api/v1/atlas/countries/search
// Description: Search and filter countries with pagination
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - name?: string - Country name (partial match)
//   - iso2?: string - ISO 3166-1 alpha-2 code (e.g., "US", "GB")
//   - iso3?: string - ISO 3166-1 alpha-3 code (e.g., "USA", "GBR")
//   - region?: string - Geographic region (e.g., "Americas", "Europe", "Asia")
//   - subregion?: string - Geographic subregion (e.g., "Northern America", "Western Europe")
//   - currency?: string - Currency code (e.g., "USD", "EUR", "GBP")
//   - limit?: number - Results per page (default: 10, max: 100)
//   - offset?: number - Pagination offset (default: 0)

interface SearchCountriesRequest {
  name?: string;
  iso2?: string;
  iso3?: string;
  region?: string;
  subregion?: string;
  currency?: string;
  limit?: number;
  offset?: number;
}

interface Country {
  id: number;
  name: string;
  iso2: string; // "US"
  iso3: string; // "USA"
  numeric_code: string; // "840"
  phone_code: string; // "+1"
  capital: string;
  currency: string; // "USD"
  currency_name: string; // "United States dollar"
  currency_symbol: string; // "$"
  tld: string; // ".us"
  native: string; // Native name
  region: string; // "Americas"
  subregion: string; // "Northern America"
  nationality: string; // "American"
  timezones: Timezone[];
  latitude: number;
  longitude: number;
  emoji: string; // "🇺🇸"
  emojiU: string; // Unicode
}

interface Timezone {
  zoneName: string; // "America/New_York"
  gmtOffset: number; // -18000
  gmtOffsetName: string; // "UTC-05:00"
  abbreviation: string; // "EST"
  tzName: string; // "Eastern Standard Time"
}

interface SearchCountriesResponse {
  countries: Country[];
  total: number;
  limit: number;
  offset: number;
}

const searchCountries = async (
  filters: SearchCountriesRequest
): Promise<SearchCountriesResponse> => {
  const response = await api.get('/api/v1/atlas/countries/search', {
    params: filters,
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/atlas/countries/search?region=Americas&currency=USD&limit=5

// Example Response (200 OK):
{
  "countries": [
    {
      "id": 1,
      "name": "United States",
      "iso2": "US",
      "iso3": "USA",
      "numeric_code": "840",
      "phone_code": "+1",
      "capital": "Washington",
      "currency": "USD",
      "currency_name": "United States dollar",
      "currency_symbol": "$",
      "tld": ".us",
      "native": "United States",
      "region": "Americas",
      "subregion": "Northern America",
      "nationality": "American",
      "timezones": [
        {
          "zoneName": "America/New_York",
          "gmtOffset": -18000,
          "gmtOffsetName": "UTC-05:00",
          "abbreviation": "EST",
          "tzName": "Eastern Standard Time"
        },
        {
          "zoneName": "America/Chicago",
          "gmtOffset": -21600,
          "gmtOffsetName": "UTC-06:00",
          "abbreviation": "CST",
          "tzName": "Central Standard Time"
        }
      ],
      "latitude": 38.0,
      "longitude": -97.0,
      "emoji": "🇺🇸",
      "emojiU": "U+1F1FA U+1F1F8"
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}

// GET /api/v1/atlas/cities/search
// Description: Search cities with multiple filter options
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - name?: string - City name (partial match)
//   - country_id?: number - Country ID
//   - state_id?: string - State/province ID
//   - state_code?: string - State code (e.g., "CA", "TX")
//   - state_name?: string - State name (e.g., "California")
//   - country_code?: string - Country ISO2 code (e.g., "US")
//   - wikiDataId?: string - WikiData identifier
//   - limit?: number - Results per page (default: 10, max: 100)
//   - offset?: number - Pagination offset (default: 0)

interface SearchCitiesRequest {
  name?: string;
  country_id?: number;
  state_id?: string;
  state_code?: string;
  state_name?: string;
  country_code?: string;
  wikiDataId?: string;
  limit?: number;
  offset?: number;
}

interface City {
  id: number;
  name: string;
  state_id: string;
  state_code: string;
  state_name: string;
  country_id: number;
  country_code: string;
  country_name: string;
  latitude: number;
  longitude: number;
  wikiDataId: string;
}

interface SearchCitiesResponse {
  cities: City[];
  total: number;
  limit: number;
  offset: number;
}

const searchCities = async (
  filters: SearchCitiesRequest
): Promise<SearchCitiesResponse> => {
  const response = await api.get('/api/v1/atlas/cities/search', {
    params: filters,
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/atlas/cities/search?country_code=US&state_code=CA&name=San&limit=5

// Example Response (200 OK):
{
  "cities": [
    {
      "id": 111968,
      "name": "San Francisco",
      "state_id": "1416",
      "state_code": "CA",
      "state_name": "California",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "wikiDataId": "Q62"
    },
    {
      "id": 111969,
      "name": "San Diego",
      "state_id": "1416",
      "state_code": "CA",
      "state_name": "California",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "latitude": 32.7157,
      "longitude": -117.1611,
      "wikiDataId": "Q16552"
    },
    {
      "id": 111970,
      "name": "San Jose",
      "state_id": "1416",
      "state_code": "CA",
      "state_name": "California",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "latitude": 37.3382,
      "longitude": -121.8863,
      "wikiDataId": "Q16553"
    }
  ],
  "total": 15,
  "limit": 5,
  "offset": 0
}

// GET /api/v1/atlas/states/{country_id}
// Description: Get all states/provinces for a specific country
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - country_id: number - Country ID (e.g., 233 for USA)

interface State {
  id: number;
  name: string;
  country_id: number;
  country_code: string;
  country_name: string;
  state_code: string;
  type: string; // "state", "province", "territory", etc.
  latitude: number;
  longitude: number;
}

const listStatesByCountry = async (
  countryId: number
): Promise<State[]> => {
  const response = await api.get(`/api/v1/atlas/states/${countryId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/atlas/states/233

// Example Response (200 OK):
[
  {
    "id": 1416,
    "name": "California",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States",
    "state_code": "CA",
    "type": "state",
    "latitude": 36.7783,
    "longitude": -119.4179
  },
  {
    "id": 1417,
    "name": "Texas",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States",
    "state_code": "TX",
    "type": "state",
    "latitude": 31.9686,
    "longitude": -99.9018
  }
]

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "COUNTRY_NOT_FOUND",
    "message": "Country with ID 9999 not found",
    "details": {
      "country_id": 9999
    }
  }
}

export function useCountries(filters?: SearchCountriesRequest) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['countries', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/atlas/countries/search', {
        params: filters
      });
      return response.data;
    },
  });
  
  return {
    countries: data?.countries || [],
    total: data?.total || 0,
    isLoading,
    error,
  };
}

// Usage:
const { countries, isLoading } = useCountries({ region: 'Americas' });

export function useCities(filters?: SearchCitiesRequest) {
  const { data, isLoading } = useQuery({
    queryKey: ['cities', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/atlas/cities/search', {
        params: filters
      });
      return response.data;
    },
    enabled: !!filters?.country_id || !!filters?.country_code,
  });
  
  return {
    cities: data?.cities || [],
    total: data?.total || 0,
    isLoading,
  };
}

// Usage:
const { cities } = useCities({ country_code: 'US', state_code: 'CA' });

export function useStates(countryId?: number) {
  const { data, isLoading } = useQuery({
    queryKey: ['states', countryId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/atlas/states/${countryId}`);
      return response.data;
    },
    enabled: !!countryId,
  });
  
  return {
    states: data || [],
    isLoading,
  };
}

// Usage:
const { states } = useStates(233); // USA

export function CountrySelector({ 
  value, 
  onChange 
}: { 
  value?: number; 
  onChange: (countryId: number) => void;
}) {
  const { countries, isLoading } = useCountries({ limit: 250 });
  
  return (
    <select 
      value={value} 
      onChange={(e) => onChange(Number(e.target.value))}
      disabled={isLoading}
    >
      <option value="">Select Country</option>
      {countries.map(country => (
        <option key={country.id} value={country.id}>
          {country.emoji} {country.name}
        </option>
      ))}
    </select>
  );
}

export function CityAutocomplete({ 
  countryId,
  onSelect 
}: { 
  countryId: number;
  onSelect: (city: City) => void;
}) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  
  const { cities, isLoading } = useCities({
    country_id: countryId,
    name: debouncedSearch,
    limit: 10,
  });
  
  return (
    <div className="autocomplete">
      <input 
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search city..."
      />
      
      {isLoading && <div>Loading...</div>}
      
      <ul>
        {cities.map(city => (
          <li 
            key={city.id}
            onClick={() => onSelect(city)}
          >
            {city.name}, {city.state_code}
          </li>
        ))}
      </ul>
    </div>
  );
}

const handleLocationError = (error: any) => {
  switch (error.code) {
    case 'COUNTRY_NOT_FOUND':
      toast.error('Country not found. Please select from the list.');
      break;
      
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to access location services.');
      redirectToLogin();
      break;
      
    default:
      toast.error('Unable to load location data. Please try again.');
  }
};

// GET /api/v1/health
// Description: Check API health status
// Authentication: None (Public)

interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    database: 'up' | 'down';
    redis: 'up' | 'down';
    celery: 'up' | 'down';
  };
}

const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await api.get('/api/v1/health');
  return response.data;
};

// Example Response (200 OK):
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-01T12:00:00Z",
  "services": {
    "database": "up",
    "redis": "up",
    "celery": "up"
  }
}

// WebSocket Connection
ws://api/v1/ws/graph?token={token}

// Events
interface GraphUpdateEvent {
  type: 'protocol:update' | 'risk:alert' | 'graph:change';
  protocol_id?: string;
  protocol_name?: string;
  message: string;
  timestamp: number;
}

// Subscribe to updates
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'risk:alerts'
}));

interface GraphRAGInsightCard {
  insight_type: 'recommendation' | 'risk_warning' | 'optimization';
  title: string;
  message: string;
  affected_protocols: string[];
  action_url?: string;
  severity?: 'low' | 'medium' | 'high';
}

interface RiskAlertBanner {
  risk_level: RiskLevel;
  message: string;
  protocols: string[];
  recommendations: string[];
}

// Hybrid Search
POST /api/v1/graph/search/hybrid
{
  query: string;
  limit?: number;
  similarity_threshold?: number;
  include_risks?: boolean;
}

// Real-time prices (WebSocket)
ws://api/v1/ws/graph
// Subscribe to 'protocol:update' channel

interface ProtocolRiskWarning {
  protocol_id: string;
  protocol_name: string;
  risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  contributing_factors: Factor[];
  recommendations: string[];
  confidence: number; // 0-1
}

interface AlternativeProtocolSuggestion {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;
  risk_score: number;
  tvl: number;
  why_suggested: string;
}

// Get notifications
GET /api/v1/notifications?types=risk_alert,protocol_update

// Mark as read (bulk)
POST /api/v1/notifications/read
{
  notification_ids: string[];
}

// WebSocket subscription
ws.send({
  action: 'subscribe',
  channel: 'risk:alerts'
});

// lib/graphrag-client.ts
import axios from 'axios';

const graphragClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
graphragClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default graphragClient;

// services/graphrag.ts
export interface HybridSearchRequest {
  query: string;  // Natural language: "safe staking on Ethereum"
  filters?: {
    risk_levels?: ('LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL')[];
    chains?: string[];
    categories?: string[];
    min_tvl?: number;
  };
  limit?: number;  // Default: 10
}

export interface SearchResult {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;  // 0-1
  risk_score: number;        // 0-10
  risk_level: string;
  tvl_usd: number;
  chain: string;
  category: string;
  why_relevant: string;
}

export const searchProtocols = async (
  request: HybridSearchRequest
): Promise<SearchResult[]> => {
  const response = await graphragClient.post(
    '/api/v1/graph/search/hybrid',
    request
  );
  return response.data.results;
};

// hooks/useGraphRAGSearch.ts
import { useQuery } from '@tanstack/react-query';

export function useGraphRAGSearch(
  query: string,
  filters?: HybridSearchRequest['filters']
) {
  return useQuery({
    queryKey: ['graphrag-search', query, filters],
    queryFn: () => searchProtocols({ query, filters }),
    enabled: query.length >= 3,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Usage
function SearchComponent() {
  const [query, setQuery] = useState('');
  const { data, isLoading } = useGraphRAGSearch(query);
  
  return (
    <div>
      <input 
        value={query} 
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search protocols..."
      />
      {isLoading && <Spinner />}
      {data?.map(result => (
        <ProtocolCard key={result.protocol_id} protocol={result} />
      ))}
    </div>
  );
}

export const findSimilarProtocols = async (
  protocol_id: string,
  limit: number = 5
): Promise<SearchResult[]> => {
  const response = await graphragClient.post(
    '/api/v1/graph/search/similar-protocols',
    { protocol_id, limit }
  );
  return response.data.similar_protocols;
};

// Hook
export function useSimilarProtocols(protocol_id: string) {
  return useQuery({
    queryKey: ['similar-protocols', protocol_id],
    queryFn: () => findSimilarProtocols(protocol_id),
  });
}

export const compareProtocols = async (
  protocol_ids: string[]
): Promise<ComparisonResult> => {
  const response = await graphragClient.post(
    '/api/v1/comparison/protocols',
    { protocol_ids }
  );
  return response.data;
};

// Hook
export function useProtocolComparison(protocol_ids: string[]) {
  return useQuery({
    queryKey: ['comparison', protocol_ids.sort().join(',')],
    queryFn: () => compareProtocols(protocol_ids),
    enabled: protocol_ids.length >= 2,
  });
}

import { useDebouncedValue } from '@/hooks/useDebounce';

function SearchInput() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebouncedValue(query, 300);
  const { data } = useGraphRAGSearch(debouncedQuery);
  
  // Search triggers after 300ms of no typing
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      cacheTime: 10 * 60 * 1000,     // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
});

const { data, error, isError } = useGraphRAGSearch(query);

if (isError) {
  return (
    <ErrorState 
      message="Search failed. Please try again."
      retry={() => refetch()}
    />
  );
}

interface RiskBadgeProps {
  score: number;  // 0-10
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence?: number;  // 0-1
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

function RiskBadge({ score, level, confidence, size = 'md', showLabel = true }: RiskBadgeProps) {
  const colors = {
    LOW: 'bg-green-500',
    MEDIUM: 'bg-yellow-500',
    HIGH: 'bg-orange-500',
    CRITICAL: 'bg-red-500',
  };
  
  return (
    <div className={`flex items-center gap-2 ${colors[level]} px-2 py-1 rounded`}>
      <span className="text-white font-bold">{score.toFixed(1)}</span>
      {showLabel && <span className="text-white text-sm">{level}</span>}
      {confidence && (
        <span className="text-white/70 text-xs">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </div>
  );
}

interface ProtocolCardProps {
  protocol: {
    protocol_id: string;
    protocol_name: string;
    logo_url?: string;
    chain: string;
    category: string;
    tvl_usd: number;
    risk_score: number;
    risk_level: string;
  };
  onPress?: () => void;
  showRisk?: boolean;
}

function ProtocolCard({ protocol, onPress, showRisk = true }: ProtocolCardProps) {
  return (
    <div 
      className="border rounded-lg p-4 hover:shadow-lg cursor-pointer"
      onClick={onPress}
    >
      <div className="flex items-center gap-3">
        {protocol.logo_url && (
          <img 
            src={protocol.logo_url} 
            alt={protocol.protocol_name}
            className="w-12 h-12 rounded-full"
          />
        )}
        <div className="flex-1">
          <h3 className="font-bold">{protocol.protocol_name}</h3>
          <p className="text-sm text-gray-500">
            {protocol.category} • {protocol.chain}
          </p>
        </div>
        {showRisk && (
          <RiskBadge 
            score={protocol.risk_score} 
            level={protocol.risk_level}
          />
        )}
      </div>
      <div className="mt-3 flex justify-between">
        <span className="text-sm">TVL: ${formatLargeNumber(protocol.tvl_usd)}</span>
      </div>
    </div>
  );
}

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
}

function SearchBar({ 
  value, 
  onChange, 
  placeholder = 'Search...', 
  suggestions = [],
  onSuggestionClick 
}: SearchBarProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2 border rounded-lg"
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
      />
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute w-full mt-1 bg-white border rounded-lg shadow-lg z-10">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              className="w-full px-4 py-2 text-left hover:bg-gray-100"
              onClick={() => onSuggestionClick?.(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

import { motion } from 'framer-motion';

function RiskWarning({ message }: { message: string }) {
  return (
    <motion.div
      initial={{ x: 0 }}
      animate={{ x: [-10, 10, -10, 10, 0] }}
      transition={{ duration: 0.4 }}
      className="bg-red-50 border-l-4 border-red-500 p-4"
    >
      <p className="text-red-800 font-semibold">{message}</p>
    </motion.div>
  );
}

function ProtocolCardSkeleton() {
  return (
    <div className="border rounded-lg p-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-gray-200 rounded-full" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-1/2" />
        </div>
      </div>
    </div>
  );
}

<RiskBadge 
  score={7.8}
  level="HIGH"
  aria-label="High risk: 7.8 out of 10"
  role="status"
/>

function ProtocolList({ protocols }: { protocols: Protocol[] }) {
  return (
    <div role="list">
      {protocols.map((protocol, idx) => (
        <div
          key={protocol.protocol_id}
          role="listitem"
          tabIndex={0}
          onKeyPress={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              selectProtocol(protocol);
            }
          }}
        >
          <ProtocolCard protocol={protocol} />
        </div>
      ))}
    </div>
  );
}

// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        risk: {
          low: '#10b981',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#ef4444',
        },
      },
    },
  },
};

// Mobile Risk Badge
import { View, Text } from 'react-native';
import Animated, { useAnimatedStyle, withRepeat, withTiming } from 'react-native-reanimated';

function RiskBadgeNative({ score, level }: RiskBadgeProps) {
  const pulse = useSharedValue(1);
  
  React.useEffect(() => {
    if (level === 'CRITICAL') {
      pulse.value = withRepeat(
        withTiming(1.1, { duration: 500 }),
        -1,
        true
      );
    }
  }, [level]);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
  }));
  
  return (
    <Animated.View style={[styles.badge, animatedStyle]}>
      <Text style={styles.badgeText}>{score.toFixed(1)}</Text>
    </Animated.View>
  );
}

// Format large numbers
export function formatLargeNumber(num: number): string {
  if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
  return num.toFixed(0);
}

// Format percentage
export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

// Get risk color
export function getRiskColor(level: string): string {
  const colors = {
    LOW: '#10b981',
    MEDIUM: '#f59e0b',
    HIGH: '#f97316',
    CRITICAL: '#ef4444',
  };
  return colors[level as keyof typeof colors] || colors.MEDIUM;
}

import { render, screen, fireEvent } from '@testing-library/react';

describe('RiskBadge', () => {
  it('displays correct risk level', () => {
    render(<RiskBadge score={7.8} level="HIGH" />);
    expect(screen.getByText('7.8')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });
  
  it('shows confidence when provided', () => {
    render(<RiskBadge score={2.1} level="LOW" confidence={0.94} />);
    expect(screen.getByText('94%')).toBeInTheDocument();
  });
});


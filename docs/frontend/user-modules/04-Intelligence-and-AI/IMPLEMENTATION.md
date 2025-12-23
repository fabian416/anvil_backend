# Chat Module Implementation Files

> **Complete TypeScript/React Implementation for AI Chat Module**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **AI Chat Module** is the central intelligence hub of Anvil. It's not just a text interface but a multi-agent orchestration platform integrating GraphRAG (Graph Retrieval-Augmented Generation), ML Risk Analysis, and Agent Squad routing.

### Key Capabilities
1. **Multi-Agent Routing**: Automatically routes queries to the best agent (Chat, Hunter AI, Risk, etc.)
2. **GraphRAG Search**: Hybrid semantic + graph search for protocols
3. **Real-Time Risk**: ML-powered risk analysis for any protocol mentioned
4. **Intent Awareness**: Real-time intent detection while typing
5. **WebSocket Streaming**: Real-time message streaming with progress updates

### Business Value
- **Differentiation**: AI-powered DeFi assistance is the core value proposition
- **User Engagement**: Chat interface drives daily active usage
- **Monetization**: Gateway to premium AI features
- **Data Collection**: User queries inform product development

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Users need intelligent, conversational access to DeFi information and operations.

**Root Cause Analysis**:
- **Complexity Barrier**: DeFi is too complex for most users
- **Solution**: Natural language interface with intelligent routing
- **Friction Points**: Slow responses, unclear agent selection, no progress feedback
- **Solution**: Real-time streaming, clear agent indicators, progress updates

**Design Decisions**:
1. **Conversation-First**: Chat interface is primary, not secondary
2. **Progressive Disclosure**: Show agent thinking process
3. **Real-Time Feedback**: WebSocket streaming for immediate responses
4. **Context Preservation**: Maintain conversation history and context

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Conversation-First UI** | Feature-First | Simplicity vs. Feature Discovery | Chat is core value prop; features should emerge from conversation |
| **Progressive Disclosure of Agent Thinking** | Hide Thinking | Transparency vs. Clutter | Users want to understand AI reasoning, but too much detail is overwhelming |
| **WebSocket Streaming** | Polling | Real-Time vs. Complexity | Real-time responses critical for chat UX; WebSocket more efficient than polling |
| **Multi-Agent Routing** | Single Agent | Specialization vs. Complexity | Different agents excel at different tasks; routing improves quality |
| **GraphRAG Integration** | Simple RAG | Accuracy vs. Complexity | GraphRAG provides better context, but adds implementation complexity |
| **Intent Detection While Typing** | Post-Submit | UX Speed vs. API Calls | Real-time intent improves UX, but increases API load |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────┐
│ Header: Chat Title + Agent Selector     │
├─────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────────────┐   │
│ │Conversation│  │  Main Chat Area  │   │
│ │  Sidebar  │  │                   │   │
│ │           │  │  [Message List]   │   │
│ │ [Conv 1]  │  │                   │   │
│ │ [Conv 2]  │  │  [User Message]   │   │
│ │ [+ New]   │  │  [Agent Response] │   │
│ └──────────┘  │  [Typing...]       │   │
│                │                   │   │
│                │  [Message Input]  │   │
│                └──────────────────┘   │
└─────────────────────────────────────────┘
```

#### Color Palette
- **Primary**: `#3B82F6` (Blue) - Trust, AI
- **User Message**: `#E5E7EB` (Gray-200) - User content
- **Agent Message**: `#DBEAFE` (Blue-100) - AI content
- **System Message**: `#F3F4F6` (Gray-100) - System info
- **Agent Indicator**: `#10B981` (Green) - Active agent
- **Error**: `#FEE2E2` (Red-100) - Error messages

#### Typography
- **Chat Title**: Inter, 700 weight, 24px
- **Message Text**: Inter, 400 weight, 16px
- **Agent Name**: Inter, 600 weight, 14px
- **Timestamp**: Inter, 400 weight, 12px
- **Input Text**: Inter, 400 weight, 16px

#### Component Specifications

##### Message Bubble
```typescript
interface MessageBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  agentType?: string;
  timestamp: string;
  isStreaming?: boolean;
}
```

**Visual Design**:
- **User**: Right-aligned, gray background, rounded corners
- **Agent**: Left-aligned, blue background, agent badge
- **System**: Centered, subtle background, info icon
- **Streaming**: Animated typing indicator

##### Message Input
```typescript
interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Visual Design**:
- Multi-line textarea
- Send button (disabled when empty)
- Character counter (if max length)
- Auto-resize based on content

##### Agent Selector
```typescript
interface AgentSelectorProps {
  selectedAgent?: string;
  availableAgents: Agent[];
  onAgentChange: (agent: string) => void;
}
```

**Visual Design**:
- Dropdown or segmented control
- Agent icons/avatars
- Agent descriptions
- "Auto" option for intelligent routing

### Responsive Breakpoints

**Mobile** (< 640px):
- Full-screen chat
- Conversation sidebar as drawer
- Bottom input bar
- Swipe gestures

**Tablet** (640px - 1024px):
- Side-by-side: sidebar + chat
- Collapsible sidebar
- Optimized input area

**Desktop** (> 1024px):
- Three-panel layout
- Persistent sidebar
- Full chat area
- Keyboard shortcuts

### Accessibility Requirements

1. **Screen Readers**:
   - Announce new messages
   - Describe agent responses
   - Announce typing indicators
   - Describe agent selection

2. **Keyboard Navigation**:
   - Tab through messages
   - Enter to send
   - Escape to close modals
   - Arrow keys for message navigation

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Message bubbles: 3:1 minimum
   - Agent indicators: 4.5:1

### Loading States

**Initial Load**:
- Skeleton loaders for conversation list
- Skeleton for message area

**Sending Message**:
- Input disabled
- "Sending..." indicator
- Message appears in list (pending state)

**Receiving Response**:
- Typing indicator
- Progress updates (if available)
- Streaming content (token-by-token)

### Empty States

**No Conversations**:
- Illustration: Empty chat
- Message: "Start a conversation with your AI assistant"
- CTA: "New Conversation"

**No Messages in Conversation**:
- Welcome message
- Suggested prompts
- Agent capabilities overview

### Error States

**Message Send Failed**:
- Error message below input
- Retry button
- Error details in toast

**WebSocket Disconnected**:
- Connection indicator
- Auto-reconnect attempt
- Manual reconnect button

---

## 🔌 API Endpoints

### 1. Create Conversation

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/conversations`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Request Body
```typescript
interface CreateConversationRequest {
  title?: string;  // Optional: Max 200 chars. Generated from first message if omitted
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `title` | `string` | No | Conversation title | Max 200 chars |

**JSON Example**:
```json
{
  "title": "DeFi Strategy Discussion"
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface ConversationResponse {
  id: string;  // UUID
  user_id: number;
  title: string | null;
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
}
```

**JSON Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 42,
  "title": "DeFi Strategy Discussion",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `422` | `ValidationError` | Invalid title length | Show inline error |
| `503` | `DataMapperError` | Database unavailable | Show error toast + Retry |

### 2. List Conversations

**Method**: `GET`  
**Endpoint**: `/api/v1/user/chat/conversations`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Number of conversations | 20 |
| `offset` | `number` | No | Pagination offset | 0 |

#### Response

##### Success Response (200 OK)
```typescript
interface ConversationListResponse {
  conversations: ConversationResponse[];
  total: number;
}
```

### 3. Send Message (Basic)

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/conversations/{conversation_id}/messages`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `conversation_id` | `UUID` | Yes | Conversation identifier |

##### Request Body
```typescript
interface SendMessageRequest {
  content: string;  // Required: Max 10,000 chars
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `content` | `string` | **Yes** | Message content | Min: 1, Max: 10,000 chars |

#### Response

##### Success Response (201 Created)
```typescript
interface SendMessageResponse {
  user_message: MessageResponse;
  agent_message: MessageResponse;
}

interface MessageResponse {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent_type?: string;
  created_at: string;
}
```

### 4. Send Agent Squad Message (Advanced Routing)

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/agent-squad/messages`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface AgentSquadMessageRequest {
  content: string;  // Required: User message
  force_agent?: string;  // Optional: Force specific agent (e.g., "hunter_ai")
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface AgentSquadMessageResponse {
  user_message_id: string;
  agent_message_id: string;
  agent_type: string;  // e.g., "hunter_ai", "risk_agent"
  intent_classification: string;
  intent_confidence: number;  // 0-1
  content: string;
  tools_used: string[];
  latency_ms: number;
}
```

### 5. Search Protocols (GraphRAG)

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/search-protocols`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ChatProtocolSearchRequest {
  conversation_id: string;  // Required: UUID
  query: string;  // Required: Search query (max 500 chars)
  user_preferences?: Record<string, any>;  // Optional: Filters
  limit?: number;  // Optional: Default 5, max 20
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ChatProtocolSearchResponse {
  results: ProtocolSearchResult[];
  search_context: string;
  recommendations: string[];
}

interface ProtocolSearchResult {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;  // 0-1
  risk_score: number;  // 0-10
  risk_level: string;  // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  tvl: number;
  apy?: number;
  audit_count: number;
  description: string;
  category: string;
  chain: string;
  why_relevant: string;
}
```

### 6. Analyze Risk (ML)

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/analyze-risk`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ChatRiskAnalysisRequest {
  conversation_id: string;  // Required: UUID
  protocol_name: string;  // Required: Protocol to analyze
  operation_type?: string;  // Optional: "supply" | "borrow" | "swap" | "stake" | "bridge"
  amount_usd?: number;  // Optional: Transaction amount for risk scaling
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ChatRiskAnalysisResponse {
  risk_analysis: {
    protocol_id: string;
    protocol_name: string;
    risk_score: number;  // 0-10
    risk_level: string;
    confidence: number;  // 0-1
    contributing_factors: Array<{
      factor: string;
      impact: number;  // 0-10
      description: string;
      is_critical: boolean;
    }>;
    should_warn: boolean;
    warning_message?: string;
  };
  alternatives: Array<{
    protocol_name: string;
    risk_score: number;
    why_better: string;
  }>;
  contextual_message: string;
}
```

### 7. Detect Intent

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/intent/detect`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface DetectIntentRequest {
  message: string;  // Required: Partial or full message
  include_suggestions?: boolean;  // Optional: Default true
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface DetectIntentResponse {
  intent: {
    intent_type: string;
    confidence: number;  // 0-1
    confidence_level: string;  // "low" | "medium" | "high"
    suggested_agent: string;
  };
  suggested_agents: Array<{
    agent_name: string;
    confidence: number;
    reasoning: string;
  }>;
}
```

### 8. Autocomplete

**Method**: `POST`  
**Endpoint**: `/api/v1/user/chat/intent/autocomplete`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface AutocompleteRequest {
  partial_message: string;  // Required: Text so far
  limit?: number;  // Optional: Default 10
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface AutocompleteResponse {
  suggestions: Array<{
    completion_text: string;
    display_text: string;
    suggestion_type: string;  // "action" | "protocol" | "token"
    confidence: number;  // 0-1
  }>;
}
```

---

## 🔄 User Flows & Use Cases

### Use Case 1: Start New Conversation

**Actor**: Authenticated User  
**Goal**: Ask AI assistant a question about DeFi  
**Preconditions**: User is authenticated

#### Flow Steps

1. **Entry Point**: User navigates to `/chat` or taps "Chat" tab
2. **Initial State**: 
   - Chat interface loads
   - Show conversation sidebar
   - Show empty chat area (or last conversation)
3. **User Action**: User taps "New Conversation" or starts typing
4. **System Response**:
   - Create new conversation (if needed)
   - Focus message input
   - Show intent detection (if typing)
5. **User Action**: User types message and sends
6. **System Response**:
   - Show user message in chat
   - Show "Thinking..." indicator
   - Call `POST /api/v1/user/chat/agent-squad/messages`
   - Route to appropriate agent
   - Stream response via WebSocket
7. **Success Path**:
   - Agent response streams in
   - Message completes
   - Conversation saved
8. **Error Path**:
   - If send fails: Show error, allow retry
   - If WebSocket fails: Fallback to polling

#### Flow Diagram
```
[User] → [Chat Interface]
         ↓
    [Type Message]
         ↓
    [Detect Intent] (optional)
         ↓
    [Send Message]
         ↓
    [Route to Agent]
         ↓
    [Stream Response]
         ↓
    [Display Complete]
```

#### Success Criteria
- [ ] Message sends in < 500ms
- [ ] Response starts streaming in < 2 seconds
- [ ] User sees progress updates
- [ ] Conversation persists

### Use Case 2: Search Protocols via GraphRAG

**Actor**: Authenticated User  
**Goal**: Find DeFi protocols matching criteria  
**Preconditions**: User is in active conversation

#### Flow Steps

1. **Entry Point**: User asks "Find high yield stablecoin pools"
2. **User Action**: System detects protocol search intent
3. **System Response**:
   - Call `POST /api/v1/user/chat/search-protocols`
   - Show "Searching protocols..." indicator
4. **Success Path**:
   - Display protocol results
   - Show risk scores
   - Show recommendations
   - User can ask follow-up questions

---

## 📁 File Structure

```
src/modules/chat/
├── main/
│   ├── ChatInterface.tsx
│   ├── ChatInterface.types.ts
│   ├── ChatInterface.hooks.ts
│   ├── ChatInterface.service.ts
│   ├── components/
│   │   ├── MessageList.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── MessageInput.tsx
│   │   ├── AgentSelector.tsx
│   │   ├── ConversationSidebar.tsx
│   │   └── TypingIndicator.tsx
│   └── __tests__/
├── websocket/
│   ├── ChatWebSocketClient.ts
│   ├── useChatWebSocket.ts
│   └── types.ts
├── analytics/
│   ├── ChatAnalytics.tsx
│   ├── ChatAnalytics.types.ts
│   ├── ChatAnalytics.hooks.ts
│   └── ChatAnalytics.service.ts
└── shared/
    ├── chatStore.ts
    └── chatUtils.ts
```

## 🔑 Key Implementation Files

### 1. Chat Interface Module

#### `ChatInterface.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type {
  CreateConversationRequest,
  ConversationResponse,
  SendMessageRequest,
  SendMessageResponse,
  ConversationListResponse,
  AgentSquadMessageRequest,
  AgentSquadMessageResponse,
} from './ChatInterface.types';

export const chatService = {
  async createConversation(
    request: CreateConversationRequest
  ): Promise<ConversationResponse> {
    const response = await apiClient.post<ConversationResponse>(
      '/api/v1/user/chat/conversations',
      request
    );
    return response.data;
  },

  async listConversations(
    limit = 20,
    offset = 0
  ): Promise<ConversationListResponse> {
    const response = await apiClient.get<ConversationListResponse>(
      '/api/v1/user/chat/conversations',
      { params: { limit, offset } }
    );
    return response.data;
  },

  async sendMessage(
    conversationId: string,
    request: SendMessageRequest
  ): Promise<SendMessageResponse> {
    const response = await apiClient.post<SendMessageResponse>(
      `/api/v1/user/chat/conversations/${conversationId}/messages`,
      request
    );
    return response.data;
  },

  async sendAgentSquadMessage(
    request: AgentSquadMessageRequest
  ): Promise<AgentSquadMessageResponse> {
    const response = await apiClient.post<AgentSquadMessageResponse>(
      '/api/v1/user/chat/agent-squad/messages',
      request
    );
    return response.data;
  },

  async searchProtocols(
    request: ChatProtocolSearchRequest
  ): Promise<ChatProtocolSearchResponse> {
    const response = await apiClient.post<ChatProtocolSearchResponse>(
      '/api/v1/user/chat/search-protocols',
      request
    );
    return response.data;
  },

  async analyzeRisk(
    request: ChatRiskAnalysisRequest
  ): Promise<ChatRiskAnalysisResponse> {
    const response = await apiClient.post<ChatRiskAnalysisResponse>(
      '/api/v1/user/chat/analyze-risk',
      request
    );
    return response.data;
  },
};
```

#### `ChatInterface.types.ts`
```typescript
export interface CreateConversationRequest {
  title?: string;
}

export interface ConversationResponse {
  id: string;
  user_id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent_type?: string;
  created_at: string;
}

export interface SendMessageResponse {
  user_message: MessageResponse;
  agent_message: MessageResponse;
}

export interface ConversationListResponse {
  conversations: ConversationResponse[];
  total: number;
}

export interface AgentSquadMessageRequest {
  content: string;
  force_agent?: string;
}

export interface AgentSquadMessageResponse {
  user_message_id: string;
  agent_message_id: string;
  agent_type: string;
  intent_classification: string;
  intent_confidence: number;
  content: string;
  tools_used: string[];
  latency_ms: number;
}

export interface ChatProtocolSearchRequest {
  conversation_id: string;
  query: string;
  user_preferences?: Record<string, any>;
  limit?: number;
}

export interface ProtocolSearchResult {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;
  risk_score: number;
  risk_level: string;
  tvl: number;
  apy?: number;
  audit_count: number;
  description: string;
  category: string;
  chain: string;
  why_relevant: string;
}

export interface ChatProtocolSearchResponse {
  results: ProtocolSearchResult[];
  search_context: string;
  recommendations: string[];
}

export interface ChatRiskAnalysisRequest {
  conversation_id: string;
  protocol_name: string;
  operation_type?: string;
  amount_usd?: number;
}

export interface ChatRiskAnalysisResponse {
  risk_analysis: {
    protocol_id: string;
    protocol_name: string;
    risk_score: number;
    risk_level: string;
    confidence: number;
    contributing_factors: Array<{
      factor: string;
      impact: number;
      description: string;
      is_critical: boolean;
    }>;
    should_warn: boolean;
    warning_message?: string;
  };
  alternatives: Array<{
    protocol_name: string;
    risk_score: number;
    why_better: string;
  }>;
  contextual_message: string;
}
```

#### `ChatInterface.hooks.ts`
```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chatService } from './ChatInterface.service';
import { useChatWebSocket } from '../websocket/useChatWebSocket';
import type {
  CreateConversationRequest,
  SendMessageRequest,
  AgentSquadMessageRequest,
} from './ChatInterface.types';

export function useConversations(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['conversations', limit, offset],
    queryFn: () => chatService.listConversations(limit, offset),
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (request: CreateConversationRequest) =>
      chatService.createConversation(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (request: SendMessageRequest) =>
      chatService.sendMessage(conversationId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', conversationId] });
    },
  });
}

export function useAgentSquadMessage() {
  return useMutation({
    mutationFn: (request: AgentSquadMessageRequest) =>
      chatService.sendAgentSquadMessage(request),
  });
}

export function useChatWebSocketIntegration(conversationId: string) {
  const queryClient = useQueryClient();
  
  useChatWebSocket({
    conversationId,
    onMessage: (message) => {
      // Update messages in cache
      queryClient.setQueryData(
        ['messages', conversationId],
        (old: any) => {
          return {
            ...old,
            messages: [...(old?.messages || []), message],
          };
        }
      );
    },
    onProgress: (progress) => {
      // Handle progress updates
      console.log('Progress:', progress);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });
}
```

#### `ChatInterface.tsx`
```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { useConversations, useCreateConversation, useAgentSquadMessage } from './ChatInterface.hooks';
import { useChatWebSocketIntegration } from './ChatInterface.hooks';
import { MessageList } from './components/MessageList';
import { MessageInput } from './components/MessageInput';
import { ConversationSidebar } from './components/ConversationSidebar';
import { AgentSelector } from './components/AgentSelector';
import { LoadingSpinner } from '@/design-system/components/LoadingSpinner';

export const ChatInterface: React.FC = () => {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [forceAgent, setForceAgent] = useState<string | undefined>();
  
  const { data: conversations, isLoading: conversationsLoading } = useConversations();
  const createConversation = useCreateConversation();
  const sendMessage = useAgentSquadMessage();
  
  // WebSocket integration
  useChatWebSocketIntegration(selectedConversationId || '');

  const handleSendMessage = async (content: string) => {
    if (!selectedConversationId) {
      // Create new conversation
      const newConv = await createConversation.mutateAsync({});
      setSelectedConversationId(newConv.id);
    }

    await sendMessage.mutateAsync({
      content,
      force_agent: forceAgent,
    });
  };

  if (conversationsLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="chat-interface-container">
      <ConversationSidebar
        conversations={conversations?.conversations || []}
        selectedId={selectedConversationId}
        onSelectConversation={setSelectedConversationId}
        onCreateConversation={() => createConversation.mutate({})}
      />
      
      <div className="chat-main">
        <AgentSelector
          selectedAgent={forceAgent}
          onAgentChange={setForceAgent}
        />
        
        <MessageList conversationId={selectedConversationId} />
        
        <MessageInput
          onSend={handleSendMessage}
          disabled={sendMessage.isPending}
        />
      </div>
    </div>
  );
};
```

### 2. WebSocket Integration

#### `ChatWebSocketClient.ts`
```typescript
import { getAccessToken } from '@/store/authStore';

export class ChatWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(
    private conversationId: string,
    private callbacks: {
      onMessage: (message: any) => void;
      onProgress: (progress: any) => void;
      onError: (error: any) => void;
    }
  ) {}

  connect(): void {
    const token = getAccessToken();
    const url = `ws://localhost:8000/api/v1/ws/chat?token=${token}&conversation_id=${this.conversationId}`;
    
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.callbacks.onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.stopHeartbeat();
      this.attemptReconnect();
    };
  }

  private handleMessage(message: any): void {
    switch (message.type) {
      case 'system':
        console.log('System message:', message.message);
        break;
      case 'progress':
        this.callbacks.onProgress(message);
        break;
      case 'stream':
        // Handle streaming content
        this.callbacks.onMessage({
          type: 'stream',
          content: message.content,
          message_id: message.message_id,
        });
        break;
      case 'message_complete':
        this.callbacks.onMessage({
          type: 'complete',
          ...message,
        });
        break;
      case 'error':
        this.callbacks.onError(message);
        break;
      case 'pong':
        // Heartbeat acknowledged
        break;
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  sendMessage(content: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'message',
        content,
        conversation_id: this.conversationId,
      }));
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

#### `useChatWebSocket.ts`
```typescript
import { useEffect, useRef } from 'react';
import { ChatWebSocketClient } from './ChatWebSocketClient';

interface UseChatWebSocketOptions {
  conversationId: string;
  onMessage: (message: any) => void;
  onProgress: (progress: any) => void;
  onError: (error: any) => void;
}

export function useChatWebSocket(options: UseChatWebSocketOptions) {
  const clientRef = useRef<ChatWebSocketClient | null>(null);

  useEffect(() => {
    if (!options.conversationId) return;

    const client = new ChatWebSocketClient(options.conversationId, {
      onMessage: options.onMessage,
      onProgress: options.onProgress,
      onError: options.onError,
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
    };
  }, [options.conversationId]);

  return {
    sendMessage: (content: string) => {
      clientRef.current?.sendMessage(content);
    },
  };
}
```

## 📝 Complete File List

### Chat Interface
- [x] `ChatInterface.tsx` - Main component
- [x] `ChatInterface.types.ts` - Types
- [x] `ChatInterface.hooks.ts` - Hooks
- [x] `ChatInterface.service.ts` - Service
- [ ] `components/MessageList.tsx`
- [ ] `components/MessageBubble.tsx`
- [ ] `components/MessageInput.tsx`
- [ ] `components/AgentSelector.tsx`
- [ ] `components/ConversationSidebar.tsx`
- [ ] `components/TypingIndicator.tsx`
- [ ] `__tests__/ChatInterface.test.tsx`

### WebSocket
- [x] `ChatWebSocketClient.ts` - Client implementation
- [x] `useChatWebSocket.ts` - React hook
- [ ] `types.ts` - WebSocket message types

### Analytics
- [ ] `ChatAnalytics.tsx`
- [ ] `ChatAnalytics.types.ts`
- [ ] `ChatAnalytics.hooks.ts`
- [ ] `ChatAnalytics.service.ts`

---

## 🧪 Testing Requirements

### Unit Tests

**Chat Interface Component**:
- [ ] Renders message list correctly
- [ ] Handles message sending
- [ ] Displays streaming messages
- [ ] Shows agent indicators
- [ ] Handles errors gracefully

**Chat Service**:
- [ ] All API endpoints called correctly
- [ ] Request formatting
- [ ] Response parsing
- [ ] Error handling

**WebSocket Client**:
- [ ] Connection lifecycle
- [ ] Message handling
- [ ] Reconnection logic
- [ ] Heartbeat mechanism

### Integration Tests

**Chat Flow**:
- [ ] Create conversation
- [ ] Send message
- [ ] Receive response
- [ ] WebSocket streaming
- [ ] Protocol search
- [ ] Risk analysis

### E2E Tests

**Complete Chat Journey**:
- [ ] Login → Chat → Send Message → Receive Response
- [ ] Protocol search flow
- [ ] Risk analysis flow
- [ ] Multi-turn conversation

### Performance Tests

- [ ] Message sends in < 500ms
- [ ] Response starts in < 2 seconds
- [ ] Streaming is smooth (no lag)
- [ ] Large conversations render efficiently

### Accessibility Tests

- [ ] Screen reader announces messages
- [ ] Keyboard navigation works
- [ ] Focus management in chat
- [ ] Color contrast meets WCAG 2.1 AA

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **WebSocket Reliability**
   - **Risk**: Connection drops during critical responses
   - **Mitigation**: Auto-reconnect, message queuing
   - **Validation**: Test connection resilience

2. **Agent Routing Accuracy**
   - **Risk**: Wrong agent selected, poor responses
   - **Mitigation**: Confidence thresholds, fallback agents
   - **Validation**: Monitor routing accuracy metrics

3. **Streaming Performance**
   - **Risk**: Slow streaming degrades UX
   - **Mitigation**: Optimize token rendering, chunking
   - **Validation**: Performance testing with long responses

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Message Caching**
   - **Debt**: Reload all messages on mount
   - **Cost**: Slow initial load, poor UX
   - **Prevention**: Implement message caching with React Query

2. **Hardcoded Agent List**
   - **Debt**: New agents require code changes
   - **Cost**: Maintenance burden
   - **Prevention**: Dynamic agent configuration

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ Message send success rate > 99% (messages delivered to backend)
- ✅ Average response time < 3 seconds (p95, from send to first token)
- ✅ WebSocket uptime > 99.9% (connection reliability)
- ✅ User satisfaction > 4.5/5 (user ratings)
- ✅ Agent routing accuracy > 95% (correct agent selected)
- ✅ Intent detection accuracy > 90% (intent matches user query)
- ✅ GraphRAG search relevance > 85% (relevant protocols returned)
- ✅ Streaming latency < 100ms (time between tokens)

**Module-Specific Test Requirements**:
- **Unit Tests**: Message parsing, agent routing logic, intent detection algorithms
- **Integration Tests**: WebSocket connection, message streaming, GraphRAG search, agent squad routing
- **E2E Tests**: Complete chat flow (create → send → receive → stream), multi-turn conversations
- **Performance Tests**: Long conversations (100+ messages), large context windows, concurrent users
- **Accessibility Tests**: Chat interface navigation, message reading, input accessibility
- **AI Quality Tests**: Response relevance, agent routing accuracy, intent detection accuracy

**Failure Detection & Monitoring**:
- Monitor WebSocket connection health (alert if uptime < 99%)
- Track agent routing accuracy (alert if < 90%)
- Alert on high error rates (alert if > 1%)
- Log all chat interactions (for quality improvement)
- Monitor response quality metrics (user ratings, relevance scores)
- Track intent detection accuracy (alert if < 85%)
- Monitor GraphRAG search performance (alert if relevance < 80%)

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/chat/router.py`
- **Backend Schemas**: `src/app/presentation/http/schemas/chat.py`
- **WebSocket Handler**: `src/app/presentation/http/websocket/chat_websocket.py`
- **Domain Entity**: `src/app/domain/chat/entities/conversation.py`
- **Application Interactor**: `src/app/application/agent_squad/commands/send_agent_squad_message.py`
- **Related Modules**: 
  - Dashboard (entry point to chat)
  - DeFi Operations (actions from chat)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.

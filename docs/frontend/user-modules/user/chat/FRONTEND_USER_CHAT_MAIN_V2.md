# FRONTEND_USER_CHAT_MAIN (v2.0 - Enterprise Edition)

## User AI Chat Module

**User Type:** Authenticated User  
**Module:** AI Chat (Copilot) with GraphRAG & Real-Time Intelligence  
**Route:** `/chat`, `/chat/:conversationId`  
**Platform:** Mobile (React Native) & Web  
**Version:** 2.0 - GraphRAG Enhanced

---

## 📋 Module Overview

### Title
**AI Chat** - Your DeFi Intelligence Copilot with Graph-Powered Insights

### Description
Enterprise-grade AI-powered chat interface with real-time WebSocket streaming, GraphRAG hybrid search, ML risk prediction, and protocol intelligence. Enables natural language interactions for all DeFi operations with context-aware, graph-powered recommendations.

### Key Capabilities
- ✅ Natural language DeFi commands
- ✅ Transaction previews & confirmations
- ✅ Multi-turn conversations with context
- ✅ **NEW: Real-time WebSocket streaming**
- ✅ **NEW: GraphRAG protocol search**
- ✅ **NEW: ML risk predictions**
- ✅ **NEW: Similar protocol suggestions**
- ✅ **NEW: Dependency warnings**
- ✅ **NEW: Live protocol updates**
- ✅ Transaction status tracking
- ✅ Conversation history with graph context
- ✅ Voice input support

### New Enterprise Features

#### **GraphRAG Integration**
- Hybrid semantic + graph search
- Protocol relationship discovery
- Community-based recommendations
- Risk-aware suggestions

#### **ML Risk Intelligence**
- Real-time risk scoring
- Anomaly detection alerts
- Predictive risk warnings
- Contributing factor analysis

#### **WebSocket Real-Time**
- Live message streaming
- Typing indicators
- Protocol update notifications
- Risk alert push notifications

---

## 👤 User Stories

### US-USER-CHAT-001: Execute DeFi via Chat
**As a** user  
**I want to** chat naturally to execute DeFi operations  
**So that** I don't need to navigate complex interfaces

**Acceptance Criteria:**
- Natural language parsing
- Intent recognition
- Transaction preview
- Confirmation flow

---

### US-USER-CHAT-002: Preview Transactions with Risk Warnings
**As a** user  
**I want to** see transaction details AND risk warnings before confirming  
**So that** I understand risks and can make informed decisions

**Acceptance Criteria:**
- ML risk score displayed
- Contributing factors shown
- Alternative protocols suggested (if high risk)
- Clear risk level indicator

---

### US-USER-CHAT-003: Get GraphRAG-Powered Market Insights
**As a** user  
**I want to** ask about protocols and get graph-powered insights  
**So that** I can discover related protocols and understand ecosystems

**Acceptance Criteria:**
- Hybrid search results
- Similar protocol suggestions
- Dependency chain information
- Community cluster insights

---

### US-USER-CHAT-004: Receive Real-Time Updates
**As a** user  
**I want to** receive live updates about protocols I'm interacting with  
**So that** I'm always informed of important changes

**Acceptance Criteria:**
- WebSocket connection established
- Protocol updates shown in chat
- Risk alerts displayed immediately
- Price changes notified

---

### US-USER-CHAT-005: Search Protocols via Chat
**As a** user  
**I want to** search for protocols by asking natural questions  
**So that** I can discover protocols based on intent, not exact names

**Acceptance Criteria:**
- Semantic search understanding
- Results ranked by relevance + risk
- Similar protocols suggested
- Category-based filtering

---

## 🖼️ Views & Wireframes

### View 1: Chat Interface with Real-Time Streaming (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot    [🔴Live] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Hi Alice! I'm your DeFi    ││
│  │     assistant with graph-powered││
│  │     intelligence. How can I     ││
│  │     help you today?             ││
│  │                                 ││
│  │     Quick Actions:              ││
│  │     • Search protocols 🔍       ││
│  │     • Check portfolio risk ⚠️   ││
│  │     • Swap tokens 🔄            ││
│  │     • Get recommendations 💡    ││
│  │                          10:30 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 Find me low-risk staking   ││
│  │     protocols on Ethereum      ││
│  │                          10:31 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Searching protocols...     ││
│  │     [████████░░] 80%            ││
│  │                          10:31 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Found 3 low-risk staking   ││
│  │     protocols:                  ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  📊 PROTOCOL RESULTS      │  ││
│  │  │                           │  ││
│  │  │  🥇 Lido (stETH)          │  ││
│  │  │     Risk: 2.3/10 🟢 LOW   │  ││
│  │  │     APY: 3.8%             │  ││
│  │  │     TVL: $28.4B           │  ││
│  │  │     ✓ 15 audits           │  ││
│  │  │     → [View Details]      │  ││
│  │  │                           │  ││
│  │  │  🥈 Rocket Pool (rETH)    │  ││
│  │  │     Risk: 2.8/10 🟢 LOW   │  ││
│  │  │     APY: 3.6%             │  ││
│  │  │     TVL: $4.2B            │  ││
│  │  │     ✓ 12 audits           │  ││
│  │  │     → [View Details]      │  ││
│  │  │                           │  ││
│  │  │  🥉 Frax (sfrxETH)        │  ││
│  │  │     Risk: 3.1/10 🟡 LOW-MED│ ││
│  │  │     APY: 4.2%             │  ││
│  │  │     TVL: $1.8B            │  ││
│  │  │     ✓ 8 audits            │  ││
│  │  │     → [View Details]      │  ││
│  │  │                           │  ││
│  │  │  [See More] [Compare]     │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  Based on your 4.52 ETH, Lido  ││
│  │  would earn ~$172/year. Want   ││
│  │  to stake now?                 ││
│  │                                 ││
│  │  [Stake with Lido] [Learn More]││
│  │                          10:32 ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🎤]  Ask anything...     [📎] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Risk Warning with Alternative Suggestions

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot    [🔴Live] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 I want to supply 10k USDC  ││
│  │     to Euler Finance           ││
│  │                          14:15 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 ⚠️ Important Risk Warning  ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  🔴 HIGH RISK DETECTED    │  ││
│  │  │                           │  ││
│  │  │  Protocol: Euler Finance  │  ││
│  │  │  Risk Score: 7.8/10       │  ││
│  │  │  Level: 🔴 HIGH           │  ││
│  │  │  Confidence: 87%          │  ││
│  │  │                           │  ││
│  │  │  ⚠️ Risk Factors:         │  ││
│  │  │  • Previous hack ($197M)  │  ││
│  │  │  • High systemic risk     │  ││
│  │  │  • Low audit score        │  ││
│  │  │  • Volatile TVL           │  ││
│  │  │                           │  ││
│  │  │  Recommendation:          │  ││
│  │  │  Consider lower-risk      │  ││
│  │  │  alternatives below       │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  💡 Safer Alternatives:        ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  Aave V3                  │  ││
│  │  │  Risk: 2.1/10 🟢          │  ││
│  │  │  APY: 4.2% (similar)      │  ││
│  │  │  TVL: $6.2B (stable)      │  ││
│  │  │  → [Use Aave Instead]     │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  Compound V3              │  ││
│  │  │  Risk: 2.5/10 🟢          │  ││
│  │  │  APY: 3.9% (similar)      │  ││
│  │  │  TVL: $3.8B (stable)      │  ││
│  │  │  → [Use Compound Instead] │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  Still want to proceed with    ││
│  │  Euler? I'll need explicit     ││
│  │  confirmation.                 ││
│  │                                 ││
│  │  [⚠️ Proceed Anyway] [Use Safe]││
│  │                          14:16 ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Real-Time Protocol Update Alert

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot    [🔴Live] │
│                                     │
│  ... (previous messages) ...        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔔 LIVE UPDATE                ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  ⚡ Protocol Update        │  ││
│  │  │                           │  ││
│  │  │  Lido Finance             │  ││
│  │  │  Risk: 2.3 → 2.1 🟢       │  ││
│  │  │                           │  ││
│  │  │  Change: Risk decreased   │  ││
│  │  │  Reason: New audit passed │  ││
│  │  │                           │  ││
│  │  │  This affects your        │  ││
│  │  │  4.52 stETH position      │  ││
│  │  │                           │  ││
│  │  │  [View Details] [Dismiss] │  ││
│  │  └───────────────────────────┘  ││
│  │                          15:42 ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🎤]  Ask anything...     [📎] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Protocol Dependency Visualization

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot    [🔴Live] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 Show me Aave's dependencies││
│  │                          16:20 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Here's Aave's protocol     ││
│  │     ecosystem:                  ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  🕸️ DEPENDENCY MAP       │  ││
│  │  │                           │  ││
│  │  │        Chainlink          │  ││
│  │  │           ↓               │  ││
│  │  │      [AAVE V3]            │  ││
│  │  │      /    |    \          │  ││
│  │  │   USDC  ETH  WBTC         │  ││
│  │  │                           │  ││
│  │  │  Dependencies: 4          │  ││
│  │  │  Dependents: 127          │  ││
│  │  │  Importance: 9.2/10       │  ││
│  │  │                           │  ││
│  │  │  Key Dependencies:        │  ││
│  │  │  • Chainlink (oracles) ✓  │  ││
│  │  │  • Circle (USDC) ✓        │  ││
│  │  │  • Ethereum (base) ✓      │  ││
│  │  │                           │  ││
│  │  │  [View Full Graph →]      │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  Risk Analysis:                 ││
│  │  • Systemic Risk: LOW 🟢       ││
│  │  • Cascade Risk: MEDIUM 🟡     ││
│  │                                 ││
│  │  If Chainlink fails, Aave      ││
│  │  would be affected. Want to    ││
│  │  see cascade simulation?       ││
│  │                                 ││
│  │  [Run Simulation] [Learn More] ││
│  │                          16:21 ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 5: Similar Protocols Discovery

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot    [🔴Live] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 What's similar to Uniswap? ││
│  │                          17:05 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Found 5 similar DEXs:      ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  🔄 SIMILAR PROTOCOLS     │  ││
│  │  │                           │  ││
│  │  │  🥇 SushiSwap             │  ││
│  │  │     Similarity: 94%       │  ││
│  │  │     Risk: 3.2/10 🟢       │  ││
│  │  │     TVL: $421M            │  ││
│  │  │     Why: Fork of Uniswap  │  ││
│  │  │     → [Compare]           │  ││
│  │  │                           │  ││
│  │  │  🥈 PancakeSwap V3        │  ││
│  │  │     Similarity: 89%       │  ││
│  │  │     Risk: 3.5/10 🟡       │  ││
│  │  │     TVL: $1.8B            │  ││
│  │  │     Why: V3 AMM model     │  ││
│  │  │     → [Compare]           │  ││
│  │  │                           │  ││
│  │  │  🥉 Curve Finance         │  ││
│  │  │     Similarity: 72%       │  ││
│  │  │     Risk: 2.8/10 🟢       │  ││
│  │  │     TVL: $3.2B            │  ││
│  │  │     Why: AMM for stable   │  ││
│  │  │     → [Compare]           │  ││
│  │  │                           │  ││
│  │  │  [See All 5] [Compare]    │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  💡 Community Insight:         ││
│  │  These protocols are in the    ││
│  │  same "DEX AMM" cluster with   ││
│  │  shared liquidity patterns.    ││
│  │                                 ││
│  │  [View Community] [Graph View] ││
│  │                          17:06 ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### **ENHANCED: Send Chat Message with GraphRAG**

```typescript
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
```

---

### **NEW: GraphRAG Protocol Search from Chat**

```typescript
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
```

---

### **NEW: Get Risk Analysis from Chat**

```typescript
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
```

---

### **NEW: Get Similar Protocols from Chat**

```typescript
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
```

---

### **NEW: WebSocket Connection for Real-Time Chat**

```typescript
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
```

---

### **Enhanced: Get Conversation History with Graph Context**

```typescript
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
```

---

## 🎬 Motion Design (Enterprise Grade)

```typescript
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
```

---

## 🎨 Component Specifications

```typescript
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
```

---

## 🔌 WebSocket Integration Patterns

### **Connection Management**

```typescript
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
```

---

### **React Hook for Chat WebSocket**

```typescript
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
```

---

## ⚠️ Error Handling

```typescript
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
```

---

## 🔒 Security Considerations

### **Existing Security**:
- All transaction previews expire after 2 minutes
- User must explicitly confirm transactions
- Transaction details shown before confirmation
- Wallet signing required for all transactions
- Rate limiting on chat messages
- Content filtering for prompt injection

### **NEW Security for GraphRAG/ML**:
- **Query Sanitization**: All GraphRAG searches sanitized
- **Risk Warning Enforcement**: High-risk operations require explicit confirmation
- **WebSocket Auth**: JWT validation on WebSocket connection
- **Rate Limiting**: WebSocket message rate limiting
- **Data Privacy**: User conversations not used for training
- **Protocol Data Validation**: All protocol data validated before display
- **ML Model Security**: Prediction requests rate-limited
- **Context Isolation**: Conversations isolated by user

---

## 🚀 Performance Optimization

### **Caching Strategy**:
- Protocol search results cached (5 minutes)
- Risk analysis cached (15 minutes)
- Similar protocols cached (30 minutes)
- Dependencies cached (1 hour)

### **WebSocket Optimization**:
- Message batching for efficiency
- Automatic reconnection with exponential backoff
- Connection pooling for multiple conversations
- Ping/pong for keepalive

### **Streaming Response**:
- Chunked message delivery
- Progressive rendering
- Cancel streaming on user navigation

---

## 📊 Analytics & Monitoring

### **Track User Interactions**:
- GraphRAG search queries
- Risk warnings shown
- Alternatives suggested
- Protocol comparisons
- WebSocket connection quality
- Streaming response latency
- Error rates by type

---

## ♿ Accessibility

### **WCAG 2.1 AA Compliance**:
- Keyboard navigation for all actions
- Screen reader announcements for streaming messages
- ARIA labels for protocol cards
- Color contrast for risk indicators
- Focus management in modals
- Skip to content links

### **NEW Accessibility for Real-Time**:
- Announce protocol updates to screen readers
- Optional sound alerts for risk warnings
- Reduce motion support for animations
- High contrast mode for risk meters

---

*Document Version: 2.0 (Enterprise Edition)*  
*Last Updated: December 1, 2025*  
*Module: AI Chat with GraphRAG & ML Intelligence*  
*Changes: Added WebSocket streaming, GraphRAG search, ML risk analysis, protocol insights, real-time updates*

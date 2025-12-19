# FRONTEND_USER_CHAT_MAIN

## User AI Chat Module

**User Type:** Authenticated User  
**Module:** AI Chat (Copilot)  
**Route:** `/chat`, `/chat/:conversationId`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**AI Chat** - Your DeFi Intelligence Copilot

### Description
The core AI-powered chat interface that enables natural language interactions for all DeFi operations. Users can chat to swap tokens, check balances, get market insights, execute strategies, and learn about DeFi.

### Key Capabilities
- Natural language DeFi commands
- Transaction previews & confirmations
- Multi-turn conversations
- Context-aware suggestions
- Transaction status tracking
- Conversation history
- Voice input support

---

## 👤 User Stories

### US-USER-CHAT-001: Execute DeFi via Chat
**As a** user  
**I want to** chat naturally to execute DeFi operations  
**So that** I don't need to navigate complex interfaces

### US-USER-CHAT-002: Preview Transactions
**As a** user  
**I want to** see transaction details before confirming  
**So that** I understand exactly what will happen

### US-USER-CHAT-003: Get Market Insights
**As a** user  
**I want to** ask about market conditions  
**So that** I can make informed decisions

### US-USER-CHAT-004: Learn About DeFi
**As a** user  
**I want to** ask questions about DeFi concepts  
**So that** I can understand what I'm doing

---

## 🖼️ Views & Wireframes

### View 1: Chat Interface (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot       [...]  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Hi Alice! I'm your DeFi    ││
│  │     assistant. How can I help  ││
│  │     you today?                 ││
│  │                                 ││
│  │     Here are some things I     ││
│  │     can help with:             ││
│  │     • Swap tokens              ││
│  │     • Check your portfolio     ││
│  │     • Stake ETH for rewards    ││
│  │     • Bridge to other chains   ││
│  │                          10:30 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 Swap 0.5 ETH to USDC       ││
│  │                          10:31 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 I'll help you swap 0.5 ETH ││
│  │     to USDC. Let me find the   ││
│  │     best rate for you...       ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  🔄 SWAP PREVIEW          │  ││
│  │  │                           │  ││
│  │  │  You Send                 │  ││
│  │  │  0.5 ETH ($1,255.00)      │  ││
│  │  │                           │  ││
│  │  │         ↓                 │  ││
│  │  │                           │  ││
│  │  │  You Receive              │  ││
│  │  │  1,248.50 USDC            │  ││
│  │  │                           │  ││
│  │  │  ─────────────────────    │  ││
│  │  │  Rate: 1 ETH = 2,497 USDC │  ││
│  │  │  Slippage: 0.5%           │  ││
│  │  │  Network: Ethereum        │  ││
│  │  │  Est. Gas: $4.50          │  ││
│  │  │  Via: 1inch               │  ││
│  │  │                           │  ││
│  │  │  [Cancel]  [✓ Confirm]    │  ││
│  │  │                           │  ││
│  │  └───────────────────────────┘  ││
│  │                          10:31 ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🎤]  Type a message...   [📎] ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

### View 2: Transaction Confirmed

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot       [...]  │
│                                     │
│  ... (previous messages) ...        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 Yes, confirm the swap      ││
│  │                          10:32 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Executing your swap...     ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  ⏳ TRANSACTION PENDING   │  ││
│  │  │                           │  ││
│  │  │       [Spinner]           │  ││
│  │  │                           │  ││
│  │  │  Swapping 0.5 ETH → USDC  │  ││
│  │  │                           │  ││
│  │  │  Waiting for confirmation │  ││
│  │  │  on Ethereum network...   │  ││
│  │  │                           │  ││
│  │  │  [View on Etherscan ↗]    │  ││
│  │  │                           │  ││
│  │  └───────────────────────────┘  ││
│  │                          10:32 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 ✅ Swap completed!         ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  ✅ TRANSACTION SUCCESS   │  ││
│  │  │                           │  ││
│  │  │  You received             │  ││
│  │  │  1,248.50 USDC            │  ││
│  │  │                           │  ││
│  │  │  Gas used: $4.32          │  ││
│  │  │  Time: 15 seconds         │  ││
│  │  │                           │  ││
│  │  │  [View Details]           │  ││
│  │  │                           │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  Anything else I can help      ││
│  │  with?                         ││
│  │                          10:33 ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🎤]  Type a message...   [📎] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 3: Market Insights Conversation

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot       [...]  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  👤 What's the best staking    ││
│  │     yield right now?           ││
│  │                          11:15 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Here are the current top   ││
│  │     staking yields:            ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  📊 STAKING YIELDS        │  ││
│  │  │                           │  ││
│  │  │  🥇 stETH (Lido)          │  ││
│  │  │     3.8% APY              │  ││
│  │  │     $28B TVL              │  ││
│  │  │                           │  ││
│  │  │  🥈 rETH (Rocket Pool)    │  ││
│  │  │     3.6% APY              │  ││
│  │  │     $4.2B TVL             │  ││
│  │  │                           │  ││
│  │  │  🥉 cbETH (Coinbase)      │  ││
│  │  │     3.4% APY              │  ││
│  │  │     $2.8B TVL             │  ││
│  │  │                           │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  Based on your 4.52 ETH, you   ││
│  │  could earn ~$45/month with    ││
│  │  Lido. Want me to help you     ││
│  │  stake?                        ││
│  │                                 ││
│  │  [Stake with Lido]             ││
│  │                          11:15 ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 4: Quick Suggestions

```
┌─────────────────────────────────────┐
│  [←]    Anvil Copilot       [...]  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 How can I help you today?  ││
│  │                          14:00 ││
│  └─────────────────────────────────┘│
│                                     │
│  Quick Actions                      │
│  ┌─────────────┐ ┌─────────────┐   │
│  │ 🔄 Swap     │ │ 💰 Stake    │   │
│  │    tokens   │ │    ETH      │   │
│  └─────────────┘ └─────────────┘   │
│  ┌─────────────┐ ┌─────────────┐   │
│  │ 📊 Check    │ │ 🌉 Bridge   │   │
│  │   portfolio │ │   tokens    │   │
│  └─────────────┘ └─────────────┘   │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🎤]  Type a message...   [📎] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 5: Conversation History

```
┌─────────────────────────────────────┐
│  [←]    Conversations       [New]  │
│                                     │
│  [🔍 Search conversations...]       │
│                                     │
│  Today                              │
│  ┌─────────────────────────────────┐│
│  │ 🔄 Swap ETH to USDC            ││
│  │    "Swap 0.5 ETH to USDC"      ││
│  │                        10:33 AM ││
│  ├─────────────────────────────────┤│
│  │ 📊 Staking yields question      ││
│  │    "What's the best staking..." ││
│  │                        11:15 AM ││
│  └─────────────────────────────────┘│
│                                     │
│  Yesterday                          │
│  ┌─────────────────────────────────┐│
│  │ 🌉 Bridge to Arbitrum          ││
│  │    "Bridge 1 ETH to Arbitrum"  ││
│  │                         3:45 PM ││
│  ├─────────────────────────────────┤│
│  │ 💰 Supply USDC to Aave         ││
│  │    "I want to earn yield..."   ││
│  │                        11:20 AM ││
│  └─────────────────────────────────┘│
│                                     │
│  This Week                          │
│  ┌─────────────────────────────────┐│
│  │ ❓ What is impermanent loss?   ││
│  │    "Can you explain what..."   ││
│  │                       Nov 28   ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Send Chat Message

```typescript
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
```

### Confirm Transaction

```typescript
// POST /api/chat/transactions/{preview_id}/confirm
interface ConfirmTransactionResponse {
  success: true;
  data: {
    transaction_id: string;
    status: 'pending' | 'submitted';
    tx_hash?: string;
  };
}
```

### Get Conversation History

```typescript
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
```

### Get Conversation Messages

```typescript
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
```

---

## 🎬 Motion Design

```typescript
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
```

---

## 🎨 Component Specifications

```typescript
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
```

---

## 🎤 Voice Input

```typescript
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
```

---

## ⚠️ Error Handling

```typescript
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
```

---

## 🔒 Security Considerations

- All transaction previews expire after 2 minutes
- User must explicitly confirm transactions
- Transaction details shown before confirmation
- Wallet signing required for all transactions
- Rate limiting on chat messages
- Content filtering for prompt injection

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: AI Chat*

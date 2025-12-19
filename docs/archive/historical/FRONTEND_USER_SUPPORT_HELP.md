# FRONTEND_USER_SUPPORT_HELP

## User Help & Support Module

**User Type:** Authenticated User  
**Module:** Help & Support  
**Route:** `/support`, `/help`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Help & Support** - User Assistance Center

### Description
Help center with FAQs, guides, and support contact options for users needing assistance.

---

## 🖼️ Views & Wireframes

### View 1: Help Center

```
┌─────────────────────────────────────┐
│  [←]     Help Center               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [🔍 Search for help...]         ││
│  └─────────────────────────────────┘│
│                                     │
│  Popular Topics                     │
│  ┌─────────────────────────────────┐│
│  │ 🔄 How to swap tokens       [>] ││
│  ├─────────────────────────────────┤│
│  │ 💰 Understanding staking    [>] ││
│  ├─────────────────────────────────┤│
│  │ 🌉 Bridging between chains  [>] ││
│  ├─────────────────────────────────┤│
│  │ 🔐 Security best practices  [>] ││
│  └─────────────────────────────────┘│
│                                     │
│  Categories                         │
│  ┌─────────────────────────────────┐│
│  │ 📱 Getting Started          [>] ││
│  │    Account setup, first steps   ││
│  ├─────────────────────────────────┤│
│  │ 💼 Wallet & Assets          [>] ││
│  │    Deposits, withdrawals, tokens││
│  ├─────────────────────────────────┤│
│  │ 🔄 Trading & DeFi           [>] ││
│  │    Swaps, staking, lending      ││
│  ├─────────────────────────────────┤│
│  │ 🔒 Security & Privacy       [>] ││
│  │    2FA, account protection      ││
│  ├─────────────────────────────────┤│
│  │ 💳 Billing & Subscription   [>] ││
│  │    Plans, payments, invoices    ││
│  └─────────────────────────────────┘│
│                                     │
│  Need More Help?                    │
│  ┌─────────────────────────────────┐│
│  │ 💬 Contact Support          [>] ││
│  │    Chat with our team           ││
│  ├─────────────────────────────────┤│
│  │ 📧 Email Us                 [>] ││
│  │    support@anvil.app            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 2: Article View

```
┌─────────────────────────────────────┐
│  [←]   How to Swap Tokens          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  How to Swap Tokens             ││
│  │                                 ││
│  │  Swapping tokens on Anvil is    ││
│  │  easy. You can do it via the    ││
│  │  Swap screen or simply chat     ││
│  │  with our AI assistant.         ││
│  │                                 ││
│  │  Via Chat:                      ││
│  │  1. Open the Chat tab           ││
│  │  2. Type "Swap 0.5 ETH to USDC" ││
│  │  3. Review the preview          ││
│  │  4. Confirm the transaction     ││
│  │                                 ││
│  │  Via Swap Screen:               ││
│  │  1. Tap Swap in Quick Actions   ││
│  │  2. Select tokens to swap       ││
│  │  3. Enter amount                ││
│  │  4. Review and confirm          ││
│  │                                 ││
│  │  [📹 Watch Tutorial Video]      ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Was this helpful?                  │
│  [👍 Yes]    [👎 No]               │
│                                     │
│  Related Articles                   │
│  ┌─────────────────────────────────┐│
│  │ Understanding slippage      [>] ││
│  │ Gas fees explained          [>] ││
│  │ Best times to trade         [>] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 3: Contact Support

```
┌─────────────────────────────────────┐
│  [←]   Contact Support             │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │  How can we help?               ││
│  │                                 ││
│  │  Our support team typically     ││
│  │  responds within 2-4 hours.     ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Topic                              │
│  ┌─────────────────────────────────┐│
│  │ Select a topic...           [▼] ││
│  └─────────────────────────────────┘│
│                                     │
│  Subject                            │
│  ┌─────────────────────────────────┐│
│  │ Brief description of issue      ││
│  └─────────────────────────────────┘│
│                                     │
│  Description                        │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │ Please describe your issue in   ││
│  │ detail...                       ││
│  │                                 ││
│  │                                 ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Attachments (optional)             │
│  ┌─────────────────────────────────┐│
│  │ [+ Add Screenshots]             ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │       Submit Request            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
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
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Help & Support*

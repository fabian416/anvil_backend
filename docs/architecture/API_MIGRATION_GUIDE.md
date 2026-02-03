# API MIGRATION GUIDE
**Migrating from Legacy Chat to New Conversations System**

**Deadline:** 2026-06-01 (Sunset Date)  
**Status:** ⚠️ URGENT - Legacy system will be removed  
**Impact:** HIGH - All clients using `/user/chat/*` will break

---

## OVERVIEW

The legacy chat system (`/api/v1/user/chat/*`) is being replaced by a new unified system (`/api/v1/conversations/*`) with the following improvements:

**What's New:**
- ✅ Guest support (no authentication required)
- ✅ Multi-language support (en, es, pt, zh)
- ✅ Enhanced intent detection
- ✅ Flow cancellation detection
- ✅ Multi-step conversational flows
- ✅ Better rate limiting
- ✅ Improved error handling

**What's Deprecated:**
- ❌ `/api/v1/user/chat/*` endpoints (removal: 2026-06-01)
- ❌ Legacy tables (`conversations`, `messages` with INTEGER user_id)
- ❌ Old interactors (`CreateConversation`, `SendMessage`)

---

## MIGRATION CHECKLIST

### Phase 1: Preparation (Week 1)
- [ ] Audit all API calls to `/user/chat/*` in your codebase
- [ ] Review new endpoint documentation
- [ ] Set up test environment with new endpoints
- [ ] Create migration plan with timeline

### Phase 2: Development (Week 2-3)
- [ ] Update API client library to support new endpoints
- [ ] Implement new request/response schemas
- [ ] Update error handling for new error codes
- [ ] Add support for guest mode (optional JWT)
- [ ] Update rate limit handling

### Phase 3: Testing (Week 4)
- [ ] Test all chat functionality with new endpoints
- [ ] Verify guest mode works correctly
- [ ] Test rate limiting behavior
- [ ] Validate multi-language support
- [ ] Performance testing (compare old vs new)

### Phase 4: Deployment (Week 5)
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Deploy to production (canary/blue-green)
- [ ] Monitor error rates and latency
- [ ] Rollback plan ready

### Phase 5: Cleanup (Week 6+)
- [ ] Remove legacy code references
- [ ] Update documentation
- [ ] Archive old API client versions
- [ ] Celebrate! 🎉

---

## CODE EXAMPLES

### 1. Create Conversation

#### Before (DEPRECATED):
```javascript
// Legacy endpoint - DO NOT USE
const response = await fetch('/api/v1/user/chat/conversations', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`, // REQUIRED
  },
  body: JSON.stringify({
    title: 'My Conversation'
  })
});

const data = await response.json();
// Response: { id, title, created_at, updated_at }
```

#### After (NEW):
```javascript
// New endpoint - USE THIS
const response = await fetch('/api/v1/conversations', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`, // OPTIONAL for guests
  },
  body: JSON.stringify({
    title: 'My Conversation',
    language: 'en' // NEW: language support
  })
});

const data = await response.json();
// Response: { id, title, status, created_at, updated_at, message_count, language }
```

**Key Changes:**
- Base path: `/user/chat/conversations` → `/conversations`
- Authentication now optional (supports guests)
- Added `language` field (default: "en")
- Response includes `status`, `message_count`, `language`

---

### 2. Send Message

#### Before (DEPRECATED):
```javascript
// Legacy endpoint - DO NOT USE
const response = await fetch(`/api/v1/user/chat/conversations/${conversationId}/messages`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`, // REQUIRED
  },
  body: JSON.stringify({
    content: 'What is Bitcoin?'
  })
});

const data = await response.json();
// Old response format
```

#### After (NEW):
```javascript
// New endpoint - USE THIS
const response = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`, // OPTIONAL for guests
  },
  body: JSON.stringify({
    content: 'What is Bitcoin?',
    language: 'en' // NEW: language support
  })
});

const data = await response.json();
/*
New response format:
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message_id": "456e7890-e89b-12d3-a456-426614174001",
  "user_message": {
    "id": "456e7890...",
    "role": "user",
    "content": "What is Bitcoin?",
    "created_at": "2026-01-22T00:00:00Z"
  },
  "agent_message": {
    "id": "789e0123...",
    "role": "assistant",
    "content": "Bitcoin is a decentralized digital currency...",
    "created_at": "2026-01-22T00:00:01Z"
  },
  "routing": {
    "intent": "GENERAL_CONVERSATION",
    "confidence": 0.95,
    "handler": "llm_handler",
    "language": "en",
    "user_type": "authenticated"
  },
  "enrichment": null, // Intent-specific data (swap, lending, etc.)
  "registration_required": null, // For guest users only
  "rate_limit_status": {
    "user_type": "authenticated",
    "remaining_hourly": 987,
    "remaining_daily": 9843
  },
  "execute": null // For executable actions (swap, deposit, etc.)
}
*/
```

**Key Changes:**
- Base path: `/user/chat/conversations/{id}/messages` → `/conversations/{id}/messages`
- Added `language` field to request
- Response now includes:
  - Both user and agent messages
  - Routing metadata (intent, confidence, handler)
  - Rate limit status
  - Execute data (for swaps, deposits, etc.)
  - Enrichment data (intent-specific)

---

### 3. List Conversations

#### Before (DEPRECATED):
```javascript
// Legacy endpoint - DO NOT USE
const response = await fetch('/api/v1/user/chat/conversations?limit=20&offset=0', {
  headers: {
    'Authorization': `Bearer ${accessToken}`, // REQUIRED
  }
});

const data = await response.json();
// Response: { conversations: [...], total: 42 }
```

#### After (NEW):
```javascript
// New endpoint - USE THIS
const response = await fetch('/api/v1/conversations?status=active&limit=20&offset=0', {
  headers: {
    'Authorization': `Bearer ${accessToken}`, // OPTIONAL for guests
  }
});

const data = await response.json();
// Response: Array of conversations
/*
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "My Conversation",
    "status": "active", // NEW: status field
    "created_at": "2026-01-22T00:00:00Z",
    "updated_at": "2026-01-22T00:05:00Z",
    "last_message_at": "2026-01-22T00:05:00Z", // NEW
    "message_count": 12, // NEW
    "language": "en" // NEW
  },
  ...
]
*/
```

**Key Changes:**
- Added `status` filter query parameter (active, archived)
- Response is now array (not object with `conversations` key)
- Each conversation includes:
  - `status` - active, archived
  - `last_message_at` - timestamp of last message
  - `message_count` - number of messages
  - `language` - conversation language

---

### 4. Get Conversation with Messages

#### Before (DEPRECATED):
```javascript
// Legacy endpoint - DO NOT USE
// Required TWO API calls:
// 1. Get conversation
const conv = await fetch(`/api/v1/user/chat/conversations/${id}`, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});

// 2. Get messages
const msgs = await fetch(`/api/v1/user/chat/conversations/${id}/messages?limit=50`, {
  headers: { 'Authorization': `Bearer ${accessToken}` }
});
```

#### After (NEW):
```javascript
// New endpoint - USE THIS (single API call)
const response = await fetch(`/api/v1/conversations/${id}?limit=50`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`, // OPTIONAL for guests
  }
});

const data = await response.json();
/*
{
  "conversation": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "My Conversation",
    "status": "active",
    "created_at": "2026-01-22T00:00:00Z",
    "updated_at": "2026-01-22T00:05:00Z",
    "last_message_at": "2026-01-22T00:05:00Z",
    "message_count": 12,
    "language": "en"
  },
  "messages": [
    {
      "id": "456e7890...",
      "role": "user",
      "content": "What is Bitcoin?",
      "intent": null,
      "is_restricted_action": false,
      "created_at": "2026-01-22T00:00:00Z",
      "metadata": null
    },
    {
      "id": "789e0123...",
      "role": "assistant",
      "content": "Bitcoin is a decentralized digital currency...",
      "intent": "GENERAL_CONVERSATION",
      "is_restricted_action": false,
      "created_at": "2026-01-22T00:00:01Z",
      "metadata": {
        "handler": "llm_handler",
        "confidence": 0.95
      }
    },
    ...
  ]
}
*/
```

**Key Changes:**
- Single API call (vs 2 in legacy)
- GET endpoint includes messages (via `limit` query param)
- Messages include `intent`, `metadata`, `is_restricted_action`
- Messages ordered chronologically (oldest first)

---

### 5. Update Conversation

#### Before (DEPRECATED):
```javascript
// Legacy endpoint - DO NOT USE
const response = await fetch(`/api/v1/user/chat/conversations/${id}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
  },
  body: JSON.stringify({
    title: 'Updated Title'
  })
});
```

#### After (NEW):
```javascript
// New endpoint - USE THIS
const response = await fetch(`/api/v1/conversations/${id}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`, // OPTIONAL for guests
  },
  body: JSON.stringify({
    title: 'Updated Title'
  })
});

const data = await response.json();
// Same response as GET conversation
```

**Key Changes:**
- Base path: `/user/chat/conversations/{id}` → `/conversations/{id}`
- Response includes full conversation object (not just updated fields)

---

### 6. Delete Conversation

#### Before (DEPRECATED):
```javascript
// Legacy endpoint - DO NOT USE (HARD DELETE)
const response = await fetch(`/api/v1/user/chat/conversations/${id}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  }
});

const data = await response.json();
// Response: { deleted: true, id: "..." }
```

#### After (NEW):
```javascript
// New endpoint - USE THIS (SOFT DELETE / ARCHIVE)
const response = await fetch(`/api/v1/conversations/${id}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`, // OPTIONAL for guests
  }
});

const data = await response.json();
/*
Response: Full conversation object with status="archived"
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "My Conversation",
  "status": "archived", // Changed from "active"
  "created_at": "2026-01-22T00:00:00Z",
  "updated_at": "2026-01-22T00:10:00Z",
  "last_message_at": "2026-01-22T00:05:00Z",
  "message_count": 12,
  "language": "en"
}
*/

// Alternative: Explicit archive endpoint
const response2 = await fetch(`/api/v1/conversations/${id}/archive`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  }
});
// Same response as DELETE
```

**Key Changes:**
- DELETE now performs SOFT DELETE (archives conversation)
- Conversation is not deleted, just marked `status="archived"`
- Can be unarchived later if needed
- Alternative explicit `/archive` endpoint available

---

### 7. Guest Chat (No Authentication)

#### Before (DEPRECATED):
```javascript
// Legacy system did NOT support guests
// Required authentication for all chat operations
```

#### After (NEW):
```javascript
// Option 1: Guest-specific endpoint
const response = await fetch('/api/v1/guest/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    // NO Authorization header
  },
  body: JSON.stringify({
    content: 'What is Ethereum?',
    language: 'en'
  })
});

const data = await response.json();
/*
{
  "conversation_id": "guest-123e4567...",
  "message_id": "456e7890...",
  "user_message": { ... },
  "agent_message": { ... },
  "routing": { ... },
  "enrichment": null,
  "registration_required": { // For restricted features
    "required": true,
    "reason": "action_required",
    "message": {
      "en": "Sign up to execute swaps and manage your portfolio.",
      "es": "Regístrate para ejecutar swaps y gestionar tu cartera."
    },
    "cta": {
      "en": "Sign Up",
      "es": "Registrarse"
    },
    "signup_url": "/signup"
  },
  "guest_info": {
    "messages_remaining": 19, // Out of 20/hr
    "session_active": true
  },
  "rate_limited": false
}
*/

// Option 2: Universal endpoint (auto-detects guest)
const response2 = await fetch('/api/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    // NO Authorization header = guest user
  },
  body: JSON.stringify({
    content: 'What is Ethereum?',
    language: 'en'
  })
});
// Same response as Option 1
```

**Key Features:**
- No authentication required
- IP-based user tracking
- Rate limiting (20 msg/hr for guests)
- Restricted actions show signup CTA
- Multi-language support

---

## ERROR HANDLING

### Legacy Errors (OLD):
```javascript
// Legacy error format
{
  "detail": "Conversation not found"
}
```

### New Errors (NEW):
```javascript
// Standard FastAPI error format
{
  "detail": {
    "error": "not_found",
    "message": "Conversation not found",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}

// Rate limit error (429)
{
  "detail": {
    "error": "rate_limit_exceeded",
    "reason": "Hourly limit exceeded",
    "limit": 1000,
    "current": 1000,
    "reset_in": 3420, // seconds
    "message": {
      "en": "Rate limit exceeded. Try again in 57 minutes.",
      "es": "Límite de tasa excedido. Intenta de nuevo en 57 minutos.",
      "pt": "Limite de taxa excedido. Tente novamente em 57 minutos."
    }
  }
}

// Authentication error (401)
{
  "detail": "Could not validate credentials"
}

// Authorization error (403)
{
  "detail": "Not authorized to access this conversation"
}
```

**Error Codes:**
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid JWT)
- `403` - Forbidden (not authorized)
- `404` - Not Found (conversation/message not found)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

---

## RATE LIMITING

### Legacy System:
```javascript
// No explicit rate limit headers
// Limit: 1000 msg/hr (authenticated only)
```

### New System:
```javascript
// Rate limit headers in EVERY response
response.headers = {
  'X-RateLimit-Limit': '1000',      // Total allowed per hour
  'X-RateLimit-Remaining': '847',   // Remaining this hour
  'X-RateLimit-Reset': '1737504000', // Unix timestamp of reset
  'Retry-After': '3600'             // Seconds until reset (if 429)
};

// Rate limit in response body (send message)
data.rate_limit_status = {
  "user_type": "authenticated", // or "guest"
  "remaining_hourly": 847,
  "remaining_daily": 9843
};

// Handle rate limit
if (response.status === 429) {
  const resetTime = response.headers.get('X-RateLimit-Reset');
  const retryAfter = response.headers.get('Retry-After');
  
  console.log(`Rate limited. Retry after ${retryAfter} seconds`);
  console.log(`Limit resets at ${new Date(resetTime * 1000)}`);
}
```

**Rate Limits:**
- **Guest**: 20 msg/hr (guest endpoint), 800 msg/hr (universal endpoint)
- **Authenticated**: 1000 msg/hr
- **Premium**: 10,000 msg/hr

---

## MULTI-LANGUAGE SUPPORT

### Legacy System:
```javascript
// No language support
// All responses in English
```

### New System:
```javascript
// Specify language in request
const response = await fetch('/api/v1/conversations/123.../messages', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
  },
  body: JSON.stringify({
    content: '¿Qué es Bitcoin?',
    language: 'es' // Spanish
  })
});

// Response in Spanish
data.agent_message.content = "Bitcoin es una moneda digital descentralizada...";

// Supported languages:
// - "en" - English (default)
// - "es" - Spanish
// - "pt" - Portuguese
// - "zh" - Mandarin Chinese
```

---

## INTENT DETECTION

### Legacy System:
```javascript
// No explicit intent detection
// All messages handled the same way
```

### New System:
```javascript
// Automatic intent detection in every message
data.routing = {
  "intent": "SWAP", // Detected intent
  "confidence": 0.92, // Confidence score (0-1)
  "handler": "swap_handler_v2", // Handler used
  "language": "en",
  "user_type": "authenticated"
};

// Intent-specific enrichment
data.enrichment = {
  // For SWAP intent:
  "from_token": "USDC",
  "to_token": "ETH",
  "amount": "100",
  "chain": "base",
  "estimated_output": "0.0222 ETH",
  "exchange_rate": "1 USDC = 0.000222 ETH",
  "network_fee_usd": "0.25"
};

// Execute data (for actionable intents)
data.execute = {
  "action_type": "swap",
  "provider": "privy_0x",
  "chain": "base",
  "from_token": "USDC",
  "to_token": "ETH",
  "amount": "100",
  // ... execution parameters
};

// Supported intents:
// - GENERAL_CONVERSATION
// - SWAP, SWAP_CONTINUE
// - MOONPAY_SWAP, MOONPAY_SWAP_CONTINUE
// - LENDING, LENDING_CONTINUE
// - MONEY_MARKET
// - BUY, BUY_CONTINUE
// - PORTFOLIO, BALANCE, ACTIVITY, RECEIVE (restricted)
// - PROTOCOL_SEARCH, RISK_ASSESSMENT, SIMILAR_PROTOCOLS
// - And more...
```

---

## TESTING YOUR MIGRATION

### 1. Unit Tests

```javascript
// Test: Create conversation
describe('Conversations API', () => {
  it('should create conversation with new endpoint', async () => {
    const response = await fetch('/api/v1/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${testToken}`,
      },
      body: JSON.stringify({
        title: 'Test Conversation',
        language: 'en'
      })
    });
    
    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('status', 'active');
    expect(data).toHaveProperty('language', 'en');
  });
  
  it('should support guest users (no auth)', async () => {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // No Authorization header
      },
      body: JSON.stringify({
        content: 'What is Bitcoin?',
        language: 'en'
      })
    });
    
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('routing');
    expect(data.routing.user_type).toBe('guest');
  });
});
```

### 2. Integration Tests

```javascript
// Test: Complete conversation flow
describe('Conversation Flow', () => {
  let conversationId;
  
  it('should create conversation', async () => {
    const response = await fetch('/api/v1/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${testToken}`,
      },
      body: JSON.stringify({
        title: 'Integration Test',
        language: 'en'
      })
    });
    
    const data = await response.json();
    conversationId = data.id;
    expect(conversationId).toBeTruthy();
  });
  
  it('should send message', async () => {
    const response = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${testToken}`,
      },
      body: JSON.stringify({
        content: 'What is Bitcoin?',
        language: 'en'
      })
    });
    
    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('user_message');
    expect(data).toHaveProperty('agent_message');
    expect(data.routing.intent).toBeTruthy();
  });
  
  it('should get conversation with messages', async () => {
    const response = await fetch(`/api/v1/conversations/${conversationId}?limit=10`, {
      headers: {
        'Authorization': `Bearer ${testToken}`,
      }
    });
    
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('conversation');
    expect(data).toHaveProperty('messages');
    expect(data.messages.length).toBeGreaterThan(0);
  });
  
  it('should archive conversation', async () => {
    const response = await fetch(`/api/v1/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${testToken}`,
      }
    });
    
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('archived');
  });
});
```

### 3. Performance Tests

```javascript
// Test: Rate limiting
describe('Rate Limiting', () => {
  it('should enforce rate limits for guests', async () => {
    const requests = [];
    
    // Send 21 messages (limit is 20/hr for guests)
    for (let i = 0; i < 21; i++) {
      requests.push(
        fetch('/api/v1/guest/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: `Message ${i}`,
            language: 'en'
          })
        })
      );
    }
    
    const responses = await Promise.all(requests);
    const rateLimited = responses.filter(r => r.status === 429);
    
    expect(rateLimited.length).toBeGreaterThan(0);
    
    // Check rate limit headers
    const headers = rateLimited[0].headers;
    expect(headers.get('X-RateLimit-Limit')).toBe('20');
    expect(headers.get('Retry-After')).toBeTruthy();
  });
});
```

---

## ROLLBACK PLAN

If you encounter critical issues after migration:

### Step 1: Identify the Issue
- Check error logs
- Monitor error rates
- Review performance metrics
- Gather user reports

### Step 2: Quick Rollback (< 1 hour)
```javascript
// Revert to legacy endpoints in your client code
const BASE_URL = process.env.USE_LEGACY_CHAT 
  ? '/api/v1/user/chat'  // Legacy
  : '/api/v1/conversations'; // New

// Update environment variable and redeploy
```

### Step 3: Contact Support
- Email: api-support@anvil.finance
- Slack: #api-migration
- Include: Error logs, affected endpoints, timeline

### Step 4: Extended Support (2026-06-01 - 2026-07-01)
- Legacy endpoints available for 30 days post-sunset as READ-ONLY
- No new conversations or messages
- Only GET requests allowed
- Use this time to complete migration

---

## FAQ

**Q: Can I use both legacy and new endpoints during migration?**  
A: Yes, but we recommend migrating all endpoints at once for consistency. Both systems work in parallel until 2026-06-01.

**Q: Will my conversation history be lost?**  
A: No, all conversation data has been migrated from legacy tables to new tables. Both systems can access the same conversations.

**Q: Do I need to update my authentication logic?**  
A: No, authentication (JWT) works the same way. The only difference is that new endpoints support optional authentication for guests.

**Q: What happens to my legacy API calls after 2026-06-01?**  
A: They will return `410 Gone` status. You MUST migrate before this date.

**Q: Can I test the new endpoints without affecting production?**  
A: Yes, use a separate environment or create test conversations. Both systems use the same database, so test data will be visible in both.

**Q: How do I handle rate limiting?**  
A: Check `X-RateLimit-Remaining` header and `rate_limit_status` in response body. If you hit the limit (429 status), wait for `Retry-After` seconds.

**Q: What if I need help with migration?**  
A: Contact us via:
- Email: api-support@anvil.finance
- Slack: #api-migration
- Office Hours: Tue/Thu 2-4pm UTC

---

## TIMELINE

| Date | Milestone |
|------|-----------|
| **2026-01-22** | Migration guide published |
| **2026-02-01** | Email notification to all API consumers |
| **2026-03-01** | Legacy endpoints show deprecation warnings |
| **2026-04-01** | Final reminder emails sent |
| **2026-05-01** | Legacy endpoints log warnings for every call |
| **2026-06-01** | ⚠️ SUNSET DATE - Legacy endpoints removed |
| **2026-07-01** | Read-only legacy access removed |

---

**Last Updated:** 2026-01-22  
**Maintained By:** @system-architect  
**Need Help?** Contact api-support@anvil.finance

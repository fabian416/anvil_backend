# Frontend Integration - Request Distillation

## Overview

Guide for frontend developers integrating with the Request Distillation System.

**Audience**: Frontend/UI Developers  
**Framework Agnostic**: Works with React, Vue, Angular, etc.  
**Last Updated**: 2025-12-01

---

## Quick Start

### 1. Understanding Distillation Responses

When you send a chat message, it may be blocked by distillation before reaching the main LLM:

```typescript
// Success Response (request allowed)
{
  "success": true,
  "message": "...",  // Your chat response
  "metadata": {
    "distillation": {
      "validated": true,
      "provider": "vertex_ai",
      "latency_ms": 287.5
    }
  }
}

// Error Response (request blocked)
{
  "success": false,
  "message": "I can only help with DeFi trading and analytics. Please ask about cryptocurrency or DeFi topics.",
  "metadata": {
    "reason": "out_of_scope",
    "confidence": 0.95
  }
}
```

### 2. Handle Blocked Requests

```typescript
async function sendMessage(content: string) {
  try {
    const response = await fetch('/api/v1/chat/conversations/{id}/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      // Request was blocked by distillation
      showUserFriendlyError(data.message, data.metadata.reason);
      return null;
    }
    
    // Request was allowed, process normally
    return data.message;
  } catch (error) {
    handleNetworkError(error);
  }
}

function showUserFriendlyError(message: string, reason: string) {
  // Show the message from distillation (already in user's language)
  toast.error(message, {
    duration: 5000,
    icon: reason === 'malicious' ? '🚫' : 'ℹ️'
  });
  
  // Optional: Track analytics
  analytics.track('MessageBlocked', { reason });
}
```

---

## Error Handling

### Error Types

**Out of Scope** (`out_of_scope`):
- User asked about non-DeFi topics
- Show friendly redirect message
- Suggest valid topics

**Malicious** (`malicious`):
- Prompt injection attempt detected
- Show security message
- Log security event

**Rate Limit** (`rate_limit`):
- User exceeded request quota
- Show rate limit message with retry time
- Implement exponential backoff

**System Error** (`system_error`):
- Distillation system unavailable
- Request was allowed (fail-open)
- No user action needed

### Example Error Handler

```typescript
interface DistillationError {
  reason: 'out_of_scope' | 'malicious' | 'rate_limit' | 'system_error';
  message: string;
  confidence?: number;
}

function handleDistillationError(error: DistillationError) {
  switch (error.reason) {
    case 'out_of_scope':
      return {
        title: 'Out of Scope',
        message: error.message,
        action: 'Try asking about DeFi, trading, or portfolio management',
        severity: 'info'
      };
    
    case 'malicious':
      return {
        title: 'Invalid Request',
        message: 'This request cannot be processed for security reasons.',
        action: 'Please rephrase your question',
        severity: 'error'
      };
    
    case 'rate_limit':
      return {
        title: 'Rate Limit Exceeded',
        message: error.message,
        action: 'Please wait a moment before trying again',
        severity: 'warning'
      };
    
    case 'system_error':
      // Request was allowed, no error to show
      return null;
  }
}
```

---

## UI/UX Recommendations

### 1. Message Input Validation

```typescript
// Validate before sending
function validateMessage(content: string): { valid: boolean; error?: string } {
  if (content.length < 1) {
    return { valid: false, error: 'Message cannot be empty' };
  }
  
  if (content.length > 10000) {
    return { valid: false, error: 'Message too long (max 10,000 characters)' };
  }
  
  return { valid: true };
}
```

### 2. Loading States

```tsx
// React example
function ChatInput() {
  const [message, setMessage] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  
  async function handleSend() {
    setIsValidating(true);
    
    try {
      const result = await sendMessage(message);
      if (result) {
        // Success
        addMessageToChat(result);
        setMessage('');
      }
    } finally {
      setIsValidating(false);
    }
  }
  
  return (
    <div>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isValidating}
        placeholder={isValidating ? 'Validating...' : 'Ask about DeFi...'}
      />
      <button
        onClick={handleSend}
        disabled={isValidating}
      >
        {isValidating ? 'Validating...' : 'Send'}
      </button>
    </div>
  );
}
```

### 3. Error Display

```tsx
// User-friendly error component
function DistillationError({ error }: { error: DistillationError }) {
  const config = handleDistillationError(error);
  
  if (!config) return null;
  
  return (
    <div className={`alert alert-${config.severity}`}>
      <h4>{config.title}</h4>
      <p>{config.message}</p>
      <small>{config.action}</small>
    </div>
  );
}
```

### 4. Suggested Topics

```tsx
// Show suggested topics when out-of-scope
function SuggestedTopics() {
  const topics = [
    'What is the TVL of Aave?',
    'Show me trending tokens',
    'Analyze my portfolio risk',
    'Compare Uniswap and Curve yields'
  ];
  
  return (
    <div className="suggested-topics">
      <p>Try asking about:</p>
      {topics.map(topic => (
        <button
          key={topic}
          onClick={() => sendMessage(topic)}
        >
          {topic}
        </button>
      ))}
    </div>
  );
}
```

---

## Rate Limiting

### Client-Side Rate Limiting

```typescript
class RateLimiter {
  private requests: number[] = [];
  private limit: number;
  private window: number;
  
  constructor(limit: number = 100, windowMs: number = 3600000) {
    this.limit = limit;
    this.window = windowMs;
  }
  
  canSend(): boolean {
    const now = Date.now();
    this.requests = this.requests.filter(t => t > now - this.window);
    return this.requests.length < this.limit;
  }
  
  recordRequest() {
    this.requests.push(Date.now());
  }
  
  getRemaining(): number {
    const now = Date.now();
    this.requests = this.requests.filter(t => t > now - this.window);
    return Math.max(0, this.limit - this.requests.length);
  }
}

// Usage
const rateLimiter = new RateLimiter(100, 3600000); // 100/hour

async function sendMessageWithRateLimit(content: string) {
  if (!rateLimiter.canSend()) {
    toast.error(
      `Rate limit exceeded. ${rateLimiter.getRemaining()} requests remaining.`
    );
    return null;
  }
  
  rateLimiter.recordRequest();
  return await sendMessage(content);
}
```

### Display Rate Limit Info

```tsx
function RateLimitInfo() {
  const remaining = rateLimiter.getRemaining();
  const percentage = (remaining / 100) * 100;
  
  return (
    <div className="rate-limit-info">
      <progress value={remaining} max={100} />
      <span>{remaining} requests remaining this hour</span>
    </div>
  );
}
```

---

## Analytics & Monitoring

### Track Blocked Requests

```typescript
// Track when requests are blocked
analytics.track('MessageBlocked', {
  reason: error.reason,
  confidence: error.confidence,
  messageLength: content.length,
  timestamp: Date.now()
});

// Track successful validations
analytics.track('MessageValidated', {
  provider: metadata.distillation.provider,
  latency: metadata.distillation.latency_ms,
  timestamp: Date.now()
});
```

### User Feedback

```tsx
// Collect feedback on blocked requests
function FeedbackPrompt({ error }: { error: DistillationError }) {
  const [feedback, setFeedback] = useState<'helpful' | 'not_helpful' | null>(null);
  
  function submitFeedback(helpful: boolean) {
    analytics.track('DistillationFeedback', {
      reason: error.reason,
      helpful,
      message: error.message
    });
    setFeedback(helpful ? 'helpful' : 'not_helpful');
  }
  
  if (feedback) {
    return <p>Thank you for your feedback!</p>;
  }
  
  return (
    <div>
      <p>Was this helpful?</p>
      <button onClick={() => submitFeedback(true)}>Yes</button>
      <button onClick={() => submitFeedback(false)}>No</button>
    </div>
  );
}
```

---

## Testing

### Mock Responses

```typescript
// Mock for testing
export const mockDistillationResponses = {
  success: {
    success: true,
    message: 'Aave has a TVL of $5.2B...',
    metadata: {
      distillation: {
        validated: true,
        provider: 'vertex_ai',
        latency_ms: 287.5
      }
    }
  },
  
  outOfScope: {
    success: false,
    message: 'I can only help with DeFi topics. Please ask about cryptocurrency or DeFi.',
    metadata: {
      reason: 'out_of_scope',
      confidence: 0.95
    }
  },
  
  malicious: {
    success: false,
    message: 'This request cannot be processed for security reasons.',
    metadata: {
      reason: 'malicious',
      confidence: 0.99
    }
  },
  
  rateLimit: {
    success: false,
    message: 'Rate limit exceeded. Please try again in 30 minutes.',
    metadata: {
      reason: 'rate_limit',
      retryAfter: 1800
    }
  }
};
```

### Unit Tests

```typescript
// Jest/Vitest example
describe('Message Validation', () => {
  it('handles successful validation', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockDistillationResponses.success
    });
    
    const result = await sendMessage('What is Aave TVL?');
    expect(result).toBeTruthy();
  });
  
  it('handles out-of-scope rejection', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => mockDistillationResponses.outOfScope
    });
    
    const result = await sendMessage('Tell me a joke');
    expect(result).toBeNull();
    expect(toast.error).toHaveBeenCalledWith(
      expect.stringContaining('DeFi'),
      expect.any(Object)
    );
  });
});
```

---

## Best Practices

### DO

- ✅ Show distillation messages directly (already localized)
- ✅ Implement client-side rate limiting
- ✅ Track blocked requests for analytics
- ✅ Provide suggested topics for guidance
- ✅ Handle errors gracefully with fallbacks
- ✅ Display loading states during validation

### DON'T

- ❌ Hide distillation errors from users
- ❌ Retry blocked requests automatically
- ❌ Modify distillation messages
- ❌ Bypass validation on frontend
- ❌ Show technical error details
- ❌ Ignore rate limit responses

---

## Example: Complete Integration

```typescript
// Complete example with all best practices
class ChatService {
  private rateLimiter = new RateLimiter(100, 3600000);
  private analytics = new Analytics();
  
  async sendMessage(content: string): Promise<ChatMessage | null> {
    // 1. Validate input
    const validation = validateMessage(content);
    if (!validation.valid) {
      toast.error(validation.error);
      return null;
    }
    
    // 2. Check rate limit
    if (!this.rateLimiter.canSend()) {
      toast.warning(
        `Rate limit exceeded. ${this.rateLimiter.getRemaining()} requests remaining.`
      );
      return null;
    }
    
    // 3. Send request
    try {
      const response = await fetch('/api/v1/chat/conversations/{id}/messages', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
      });
      
      const data = await response.json();
      
      // 4. Handle distillation response
      if (!data.success) {
        const error = handleDistillationError({
          reason: data.metadata.reason,
          message: data.message,
          confidence: data.metadata.confidence
        });
        
        if (error) {
          toast.error(error.message, {
            duration: 5000,
            action: error.action
          });
        }
        
        // Track blocked request
        this.analytics.track('MessageBlocked', {
          reason: data.metadata.reason,
          confidence: data.metadata.confidence
        });
        
        return null;
      }
      
      // 5. Success
      this.rateLimiter.recordRequest();
      this.analytics.track('MessageValidated', {
        provider: data.metadata.distillation.provider,
        latency: data.metadata.distillation.latency_ms
      });
      
      return data.message;
      
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message. Please try again.');
      return null;
    }
  }
}
```

---

## References

- Integration Guide: `docs/DISTILLATION_INTEGRATION_GUIDE.md`
- API Spec: `docs/specs/REQUEST_DISTILLATION_SPEC.md`

---

**Document Status**: ✅ Complete

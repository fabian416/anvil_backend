# 🚦 Anvil Platform - API Rate Limiting & Throttling Guide

## Complete Rate Limiting Strategy

**Version:** 1.0  
**Date:** November 2025  
**Purpose:** Protect API from abuse and ensure fair usage

---

## 🎯 Objectives

```yaml
Primary Goals:
  - Prevent API abuse and DoS attacks
  - Ensure fair resource allocation
  - Protect backend services
  - Maintain service quality for all users

Secondary Goals:
  - Encourage Pro subscription upgrades
  - Provide predictable performance
  - Enable usage analytics
  - Support burst traffic patterns
```

---

## 📊 Rate Limit Tiers

### User Tiers

**Free Tier:**
```yaml
API Requests:
  - 60 requests per minute
  - 1,000 requests per hour
  - 10,000 requests per day

Transaction Limits:
  - $100 per transaction
  - $1,000 per day total volume

Features:
  - Basic swap
  - Basic earn
  - Limited AI chat (10 messages/day)
```

**Pro Tier ($9.99/month):**
```yaml
API Requests:
  - 120 requests per minute
  - 5,000 requests per hour
  - 100,000 requests per day

Transaction Limits:
  - $10,000 per transaction
  - $100,000 per day total volume

Features:
  - All features unlocked
  - Unlimited AI chat
  - Priority support
  - Advanced analytics
```

**Enterprise Tier (Custom):**
```yaml
API Requests:
  - Custom limits
  - Dedicated rate limit pool
  - No daily caps

Transaction Limits:
  - Custom limits
  - White-glove service

Features:
  - API access
  - Dedicated support
  - Custom integrations
```

---

## 🔧 Implementation

### Redis-Based Rate Limiter

**Core Implementation:**
```python
# app/core/rate_limiter.py
import redis
from fastapi import HTTPException, Request
from functools import wraps
from typing import Tuple
import time

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, dict]:
        """
        Check if rate limit is exceeded.
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            limit: Max requests allowed
            window: Time window in seconds
        
        Returns:
            (allowed, info) tuple
        """
        current_time = int(time.time())
        window_key = f"rate_limit:{key}:{current_time // window}"
        
        # Get current count
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window * 2)  # Keep for 2 windows
        results = pipe.execute()
        
        current_count = results[0]
        
        # Calculate remaining and reset time
        remaining = max(0, limit - current_count)
        reset_time = ((current_time // window) + 1) * window
        
        info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "current": current_count
        }
        
        allowed = current_count <= limit
        
        return allowed, info
    
    def get_user_tier_limits(self, user) -> dict:
        """Get rate limits based on user subscription tier."""
        if user.subscription_tier == "pro":
            return {
                "requests_per_minute": 120,
                "requests_per_hour": 5000,
                "requests_per_day": 100000
            }
        else:  # free tier
            return {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000
            }


# Global rate limiter instance
rate_limiter = RateLimiter(redis_client)
```

### Middleware Implementation

```python
# app/api/middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import rate_limiter
from app.core.security import get_user_from_token

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get user from token
        user = await get_user_from_token(request)
        
        if user:
            # Authenticated user - use user_id
            identifier = f"user:{user.id}"
            limits = rate_limiter.get_user_tier_limits(user)
        else:
            # Anonymous - use IP address
            identifier = f"ip:{request.client.host}"
            limits = {
                "requests_per_minute": 30,
                "requests_per_hour": 100,
                "requests_per_day": 1000
            }
        
        # Check all time windows
        checks = [
            (identifier, limits["requests_per_minute"], 60, "minute"),
            (identifier, limits["requests_per_hour"], 3600, "hour"),
            (identifier, limits["requests_per_day"], 86400, "day"),
        ]
        
        for key, limit, window, window_name in checks:
            allowed, info = rate_limiter.check_rate_limit(key, limit, window)
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded for {window_name}",
                        "limit": info["limit"],
                        "window": window_name,
                        "retry_after": info["reset"] - int(time.time())
                    },
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset"]),
                        "Retry-After": str(info["reset"] - int(time.time()))
                    }
                )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add headers for the minute window
        allowed, info = rate_limiter.check_rate_limit(
            identifier, 
            limits["requests_per_minute"], 
            60
        )
        
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response
```

---

## 🎯 Endpoint-Specific Limits

### Custom Rate Limits by Endpoint

```python
# app/core/rate_limiter.py (extended)

ENDPOINT_LIMITS = {
    # Authentication - strict limits to prevent brute force
    "/api/v1/user/auth/login": {
        "free": (5, 60),      # 5 per minute
        "pro": (10, 60)
    },
    
    # Trading - moderate limits
    "/api/v1/user/trade/quote": {
        "free": (20, 60),     # 20 per minute
        "pro": (60, 60)
    },
    "/api/v1/user/trade/swap": {
        "free": (10, 60),     # 10 per minute
        "pro": (30, 60)
    },
    
    # AI Chat - tier-based daily limits
    "/api/v1/user/chat/message": {
        "free": (10, 86400),  # 10 per day
        "pro": (1000, 86400)  # 1000 per day
    },
    
    # Wallet - high limits (read-only)
    "/api/v1/user/wallet": {
        "free": (60, 60),
        "pro": (120, 60)
    },
    
    # Admin endpoints - lower limits
    "/api/v1/admin/*": {
        "admin": (30, 60),
        "auditor": (30, 60)
    }
}

def rate_limit(limit: int = None, window: int = 60):
    """
    Decorator for endpoint-specific rate limiting.
    
    Usage:
        @router.post("/swap")
        @rate_limit(limit=10, window=60)
        async def execute_swap(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            user = kwargs.get("current_user")
            
            # Get endpoint-specific limits or use decorator params
            endpoint_key = request.url.path
            if endpoint_key in ENDPOINT_LIMITS:
                tier = user.subscription_tier if user else "free"
                endpoint_limit, endpoint_window = ENDPOINT_LIMITS[endpoint_key].get(
                    tier, (limit, window)
                )
            else:
                endpoint_limit, endpoint_window = limit, window
            
            # Check rate limit
            identifier = f"user:{user.id}:{endpoint_key}" if user else f"ip:{request.client.host}:{endpoint_key}"
            
            allowed, info = rate_limiter.check_rate_limit(
                identifier,
                endpoint_limit,
                endpoint_window
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for this endpoint"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

**Example Usage:**
```python
# app/api/v1/routes/trading.py
from app.core.rate_limiter import rate_limit

@router.post("/swap")
@rate_limit(limit=10, window=60)
async def execute_swap(
    swap_data: SwapRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Execute token swap with rate limiting."""
    # Implementation
    pass
```

---

## 📈 Burst Handling

### Token Bucket Algorithm

```python
# app/core/token_bucket.py
import time
from typing import Tuple

class TokenBucket:
    def __init__(
        self,
        redis_client,
        capacity: int,
        refill_rate: float
    ):
        """
        Token bucket rate limiter.
        
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
    
    def consume(self, key: str, tokens: int = 1) -> Tuple[bool, dict]:
        """
        Try to consume tokens from bucket.
        
        Returns:
            (allowed, info) tuple
        """
        now = time.time()
        bucket_key = f"bucket:{key}"
        
        # Get current bucket state
        bucket_data = self.redis.hgetall(bucket_key)
        
        if bucket_data:
            last_refill = float(bucket_data.get(b"last_refill", now))
            current_tokens = float(bucket_data.get(b"tokens", self.capacity))
        else:
            last_refill = now
            current_tokens = self.capacity
        
        # Calculate token refill
        time_passed = now - last_refill
        refill_amount = time_passed * self.refill_rate
        current_tokens = min(self.capacity, current_tokens + refill_amount)
        
        # Try to consume tokens
        if current_tokens >= tokens:
            # Consume successful
            new_tokens = current_tokens - tokens
            
            self.redis.hmset(bucket_key, {
                "tokens": new_tokens,
                "last_refill": now
            })
            self.redis.expire(bucket_key, 3600)  # 1 hour
            
            return True, {
                "allowed": True,
                "remaining": int(new_tokens),
                "capacity": self.capacity
            }
        else:
            # Not enough tokens
            return False, {
                "allowed": False,
                "remaining": int(current_tokens),
                "capacity": self.capacity,
                "retry_after": int((tokens - current_tokens) / self.refill_rate)
            }


# Usage for bursty endpoints
token_bucket = TokenBucket(
    redis_client,
    capacity=100,      # Allow burst of 100 requests
    refill_rate=1.0    # Refill at 1 token/second (60/min sustained)
)
```

---

## 🚨 Rate Limit Response Handling

### Client-Side Handling

**Mobile App (React Native):**
```typescript
// services/api/client.ts
class ApiClient {
  private async handleRateLimitError(error: any) {
    if (error.response?.status === 429) {
      const retryAfter = parseInt(
        error.response.headers['retry-after'] || '60'
      )
      
      // Show user-friendly message
      Alert.alert(
        'Rate Limit Exceeded',
        `Please wait ${retryAfter} seconds before trying again.`,
        [
          {
            text: 'Upgrade to Pro',
            onPress: () => navigation.navigate('Subscription')
          },
          { text: 'OK' }
        ]
      )
      
      // Schedule retry
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000))
      
      // Retry request
      return this.client.request(error.config)
    }
    
    throw error
  }
}
```

### Server-Side Error Response

```python
# Standardized rate limit error response
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded for minute window",
  "limit": 60,
  "window": "minute",
  "retry_after": 45,
  "upgrade_info": {
    "current_tier": "free",
    "next_tier": "pro",
    "next_tier_limit": 120,
    "upgrade_url": "https://anvil.com/upgrade"
  }
}
```

---

## 📊 Monitoring & Analytics

### Rate Limit Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Rate limit metrics
rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['tier', 'endpoint', 'window']
)

rate_limit_usage = Histogram(
    'rate_limit_usage_percentage',
    'Rate limit usage as percentage',
    ['tier', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0]
)

# Track in rate limiter
def check_rate_limit_with_metrics(key, limit, window, tier, endpoint):
    allowed, info = rate_limiter.check_rate_limit(key, limit, window)
    
    # Record metrics
    usage_pct = info["current"] / info["limit"]
    rate_limit_usage.labels(tier=tier, endpoint=endpoint).observe(usage_pct)
    
    if not allowed:
        rate_limit_exceeded.labels(
            tier=tier,
            endpoint=endpoint,
            window=window
        ).inc()
    
    return allowed, info
```

### CloudWatch Dashboard

```yaml
Rate Limit Dashboard:
  Widgets:
    - Title: "Rate Limit Exceeded by Tier"
      Query: |
        SELECT COUNT(*) as count
        FROM rate_limit_events
        WHERE exceeded = true
        GROUP BY tier, endpoint
      
    - Title: "Average Usage by Tier"
      Query: |
        SELECT AVG(usage_percentage) as avg_usage
        FROM rate_limit_metrics
        GROUP BY tier
      
    - Title: "Top Rate-Limited Users"
      Query: |
        SELECT user_id, COUNT(*) as exceeded_count
        FROM rate_limit_events
        WHERE exceeded = true
        GROUP BY user_id
        ORDER BY exceeded_count DESC
        LIMIT 10
```

---

## 🎓 Best Practices

### For Developers

```yaml
DO:
  - Use appropriate rate limits per endpoint
  - Implement exponential backoff on client
  - Cache responses when possible
  - Batch requests when API supports it
  - Show user-friendly error messages
  - Track rate limit headers

DON'T:
  - Retry immediately after 429
  - Ignore rate limit headers
  - Make unnecessary API calls
  - Implement aggressive polling
  - Cache auth tokens indefinitely
```

### For API Design

```yaml
DO:
  - Use consistent rate limit headers
  - Provide clear error messages
  - Document rate limits in API docs
  - Allow burst traffic with token bucket
  - Differentiate by user tier
  - Monitor and adjust limits

DON'T:
  - Apply one-size-fits-all limits
  - Block users permanently
  - Return generic errors
  - Set limits too low for normal use
  - Ignore business metrics
```

---

## 🔄 Dynamic Rate Limiting

### Adaptive Limits Based on Load

```python
# app/core/adaptive_rate_limiter.py
class AdaptiveRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.base_limits = {
            "free": 60,
            "pro": 120
        }
    
    def get_dynamic_limit(self, tier: str) -> int:
        """Adjust limits based on system load."""
        base_limit = self.base_limits[tier]
        
        # Get current system metrics
        cpu_usage = self.get_cpu_usage()
        db_connections = self.get_db_connection_count()
        
        # Reduce limits if system under stress
        if cpu_usage > 80 or db_connections > 80:
            multiplier = 0.5  # 50% reduction
        elif cpu_usage > 60 or db_connections > 60:
            multiplier = 0.75  # 25% reduction
        else:
            multiplier = 1.0  # Normal limits
        
        adjusted_limit = int(base_limit * multiplier)
        
        # Store in Redis for monitoring
        self.redis.setex(
            f"dynamic_limit:{tier}",
            60,
            adjusted_limit
        )
        
        return adjusted_limit
```

---

## 💰 Cost-Based Rate Limiting

### Weighted Requests

```python
# Different endpoints have different "costs"
ENDPOINT_COSTS = {
    "/api/v1/user/wallet": 1,              # Cheap (cached)
    "/api/v1/user/trade/quote": 5,         # Moderate (external API)
    "/api/v1/user/trade/swap": 10,         # Expensive (blockchain tx)
    "/api/v1/user/chat/message": 20,       # Very expensive (AI inference)
}

class CostBasedRateLimiter:
    def consume_credits(
        self,
        user_id: int,
        endpoint: str,
        credits_per_hour: int
    ) -> bool:
        """Consume credits based on endpoint cost."""
        cost = ENDPOINT_COSTS.get(endpoint, 1)
        
        key = f"credits:{user_id}:hour"
        current = int(self.redis.get(key) or 0)
        
        if current + cost > credits_per_hour:
            return False
        
        self.redis.incrby(key, cost)
        self.redis.expire(key, 3600)
        
        return True
```

---

## 🎯 A/B Testing Rate Limits

```python
# Test different limits for optimization
def get_ab_test_limit(user_id: int, base_limit: int) -> int:
    """A/B test different rate limits."""
    # Hash user_id to assign to test group
    group = hash(str(user_id)) % 100
    
    if group < 25:  # Group A: 25% - Control
        return base_limit
    elif group < 50:  # Group B: 25% - +20%
        return int(base_limit * 1.2)
    elif group < 75:  # Group C: 25% - +50%
        return int(base_limit * 1.5)
    else:  # Group D: 25% - +100%
        return int(base_limit * 2.0)
```

---

## ✅ Testing Rate Limits

```python
# tests/test_rate_limiter.py
import pytest
import time

def test_rate_limit_enforced():
    """Test that rate limit is enforced."""
    client = TestClient(app)
    
    # Make requests up to limit
    for i in range(60):
        response = client.get("/api/v1/user/wallet")
        assert response.status_code == 200
    
    # 61st request should be blocked
    response = client.get("/api/v1/user/wallet")
    assert response.status_code == 429

def test_rate_limit_resets():
    """Test that rate limit resets after window."""
    client = TestClient(app)
    
    # Exceed limit
    for i in range(61):
        client.get("/api/v1/user/wallet")
    
    # Wait for window to pass
    time.sleep(61)
    
    # Should work again
    response = client.get("/api/v1/user/wallet")
    assert response.status_code == 200

def test_rate_limit_headers():
    """Test that rate limit headers are present."""
    client = TestClient(app)
    response = client.get("/api/v1/user/wallet")
    
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Backend Team  
**Review:** Quarterly based on usage patterns

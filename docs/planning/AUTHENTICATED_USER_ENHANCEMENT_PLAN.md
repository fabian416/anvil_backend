# Authenticated User Enhancement Plan
## Extending Guest Chat for Authenticated Users

**Date:** 2026-01-11
**Methodology:** CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)
**Status:** Draft - Strategic Analysis

---

## 🎯 Executive Summary

**Core Insight:** Instead of building a separate system, extend the proven guest chat infrastructure to support authenticated users with the same endpoints and UX, unlocking premium features through authentication context.

**Key Principle:** Maximum code reuse, minimal architectural changes, enhanced features through feature flags.

---

## 📚 Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Assumption Questioning

**What is the actual requirement?**
- ✅ Authenticated users need access to chat functionality
- ✅ Same UX as guest chat (proven, tested, production-ready)
- ✅ Enhanced features for authenticated users (unlimited messages, history, premium tools)
- ✅ Reuse existing Hunter AI handlers and caching infrastructure

**What unverified assumptions exist?**
- ❌ WRONG: "We need separate endpoints for authenticated users"
- ❌ WRONG: "We need to duplicate the handler logic"
- ❌ WRONG: "We need a complex migration strategy"
- ✅ RIGHT: "We can extend existing endpoints to support both user types"
- ✅ RIGHT: "We can use feature flags to unlock premium features"
- ✅ RIGHT: "We can use different database tables with same domain logic"

**Which constraints are pseudo-constraints?**
- 🔓 Separate API endpoints (can use same endpoint with optional auth)
- 🔓 Different handler services (can use same service with feature flags)
- 🔓 Complex migration (can deprecate legacy without building new system)
- 🔒 Different data retention (real constraint - guests: 90 days, auth: permanent)
- 🔒 Different rate limits (real constraint - guests: 20/hour, auth: unlimited)

### 1.2 Root Cause Identification

**Problem Essence:**
```
Guest Chat (Complete) ──────┐
                             ├──> Same UX, Same Handlers, Same Cache
Authenticated Users (Need) ──┘

Difference = Context (user type) + Features (premium) + Storage (separate tables)
```

**Current State Analysis:**
```python
# What we have (WORKING):
POST /api/v1/guest/chat
- IP-based identification
- guest_users, guest_conversations, guest_messages tables
- 6 Hunter AI handlers with Redis caching
- 20 msg/hour rate limit
- 90-day retention

# What we need (EXTENSION):
POST /api/v1/guest/chat  # SAME ENDPOINT
- Optional JWT authentication
- chat_users, chat_conversations, chat_messages tables (separate storage)
- SAME 6 Hunter AI handlers + premium features
- No rate limit (or 1000 msg/hour)
- Permanent retention
```

**Mathematical Truth:**
```
AuthenticatedChat = GuestChat + Authentication + PremiumFeatures + PersistentStorage

NOT:
AuthenticatedChat = NewSystem + Migration + DuplicatedCode
```

### 1.3 Solution Space Mapping

**System Invariants (Must Preserve):**
- Hunter AI handler logic (works perfectly)
- Redis caching strategy (96.1% hit rate)
- API response format (proven UX)
- Intent routing mechanism
- Multi-language support

**Design Degrees of Freedom:**
- User identification method (IP vs JWT)
- Database tables (guest_* vs chat_*)
- Rate limiting policy
- Feature availability
- Data retention policy

**Hard Constraints:**
- Must maintain backward compatibility with guest chat
- Must support both user types simultaneously
- Must preserve existing test coverage
- Must not break production guest chat

**Soft Constraints:**
- Endpoint naming (can use same endpoint)
- Code organization (can use feature flags vs separate services)
- Migration timeline (can deprecate legacy independently)

---

## 🔬 Phase 2: Solution Generation & Trade-off Analysis

### 2.1 Solution Divergence (3 Approaches)

#### **Approach A: Unified Endpoint with Context Detection** ⭐ RECOMMENDED

**Architecture:**
```python
# Single endpoint handles both user types
@router.post("/api/v1/chat")  # Or keep as /guest/chat
async def chat(
    request: ChatRequest,
    user: Optional[User] = Depends(get_optional_user),  # JWT if present
    ip_address: str = Depends(get_client_ip),
):
    """Universal chat endpoint for guest and authenticated users."""

    if user:
        # Authenticated path
        context = AuthenticatedContext(user_id=user.id)
        features = PremiumFeatures(enabled=True)
        storage = ChatStorage(tables=['chat_users', 'chat_conversations', 'chat_messages'])
        rate_limit = RateLimit(limit=1000, window=3600)
    else:
        # Guest path
        context = GuestContext(ip_address=ip_address)
        features = BasicFeatures(enabled=True)
        storage = GuestStorage(tables=['guest_users', 'guest_conversations', 'guest_messages'])
        rate_limit = RateLimit(limit=20, window=3600)

    # SAME handler for both
    return await unified_chat_handler(
        request=request,
        context=context,
        features=features,
        storage=storage,
        rate_limit=rate_limit,
    )
```

**Benefits:**
- ✅ Maximum code reuse (single handler, single endpoint)
- ✅ Consistent UX across user types
- ✅ No API version fragmentation
- ✅ Easy to test (same test suite, different contexts)
- ✅ Zero migration needed (legacy system deprecated separately)

**Costs:**
- ⚠️ Slightly more complex handler (context branching)
- ⚠️ Need to maintain two database schemas
- ⚠️ Optional authentication adds middleware complexity

**Risks:**
- 🔴 LOW: Handler complexity manageable with feature flags
- 🟡 MEDIUM: Need careful testing of both paths
- 🟢 LOW: Performance impact negligible (context check is fast)

---

#### **Approach B: Separate Endpoint with Shared Handlers**

**Architecture:**
```python
# Two endpoints, shared handler core
@router.post("/api/v1/guest/chat")
async def guest_chat(...):
    return await chat_handler(context=GuestContext(...))

@router.post("/api/v1/chat")  # Authenticated only
async def authenticated_chat(...):
    return await chat_handler(context=AuthContext(...))
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Easier to apply different middleware
- ✅ Independent rate limiting

**Costs:**
- ⚠️ API fragmentation (two endpoints for same feature)
- ⚠️ Potential code duplication (request validation, etc.)
- ⚠️ User confusion (which endpoint to use?)

**Risks:**
- 🟡 MEDIUM: Divergent implementations over time
- 🟡 MEDIUM: Maintenance burden (two endpoints to update)

---

#### **Approach C: No Change (Guest Only)**

**Architecture:**
```
Keep guest chat as-is.
Authenticated users must use guest flow.
Premium features unavailable.
```

**Benefits:**
- ✅ Zero implementation cost
- ✅ Zero risk

**Costs:**
- ❌ No value for authenticated users
- ❌ No premium features
- ❌ No competitive advantage
- ❌ Doesn't solve the problem

**Verdict:** ❌ NOT VIABLE

---

### 2.2 Multi-dimensional Trade-off Matrix

| Dimension | Approach A (Unified) | Approach B (Separate) | Approach C (No Change) |
|-----------|---------------------|----------------------|------------------------|
| **Code Reuse** | ⭐⭐⭐⭐⭐ (95%) | ⭐⭐⭐⭐ (80%) | ⭐⭐⭐⭐⭐ (100%) |
| **UX Consistency** | ⭐⭐⭐⭐⭐ (Identical) | ⭐⭐⭐⭐ (Similar) | ⭐⭐⭐⭐⭐ (N/A) |
| **Implementation Cost** | ⭐⭐⭐⭐ (1 week) | ⭐⭐⭐ (2 weeks) | ⭐⭐⭐⭐⭐ (0 days) |
| **Maintenance Burden** | ⭐⭐⭐⭐⭐ (Low) | ⭐⭐⭐ (Medium) | ⭐⭐⭐⭐⭐ (None) |
| **Scalability** | ⭐⭐⭐⭐⭐ (Excellent) | ⭐⭐⭐⭐ (Good) | ⭐⭐⭐ (Limited) |
| **Risk Level** | ⭐⭐⭐⭐ (Low) | ⭐⭐⭐ (Medium) | ⭐⭐⭐⭐⭐ (Zero) |
| **Business Value** | ⭐⭐⭐⭐⭐ (High) | ⭐⭐⭐⭐ (High) | ⭐ (None) |

**Decision Matrix Score:**
- Approach A: 34/35 (⭐⭐⭐⭐⭐)
- Approach B: 28/35 (⭐⭐⭐⭐)
- Approach C: 28/35 (Not viable)

**RECOMMENDATION: Approach A - Unified Endpoint with Context Detection**

---

### 2.3 Constraint Priority Framework

**Our Priorities:**
1. 🔴 **CRITICAL:** Code maintainability (maximize reuse, minimize duplication)
2. 🔴 **CRITICAL:** UX consistency (same proven experience)
3. 🟡 **HIGH:** Development speed (1 week vs 2 weeks matters)
4. 🟡 **HIGH:** Feature completeness (premium features for auth users)
5. 🟢 **MEDIUM:** Architecture purity (pragmatism over perfection)

**Approach A Alignment:**
- ✅ Code maintainability: EXCELLENT (95% reuse)
- ✅ UX consistency: PERFECT (identical flow)
- ✅ Development speed: FAST (1 week)
- ✅ Feature completeness: FULL (feature flags)
- ✅ Architecture: CLEAN (context pattern)

---

## 🎯 Phase 3: Risk Assessment & Validation Design

### 3.1 Cognitive Limitation Analysis

**This analysis may overlook:**
- Long-term implications of mixing guest and authenticated logic in same endpoint
- Edge cases in context switching between user types
- Performance impact of additional database tables
- Monitoring complexity for unified metrics

**The solution assumes:**
- Feature flag patterns are maintainable long-term
- Context abstraction handles all use cases
- Database table separation is sufficient isolation
- Rate limiting can handle both user types

**Areas requiring validation:**
- Load testing with mixed guest/authenticated traffic
- Error handling when authentication is optional
- Cache key collision prevention between user types
- Monitoring dashboard clarity (guest vs auth metrics)

### 3.2 Technical Debt Assessment

**Short-term Compromises:**
- ✅ ACCEPTABLE: Single endpoint handles two user types
  - *Rationale:* Common pattern in modern APIs (e.g., Stripe, Twilio)
  - *Mitigation:* Clear context abstraction, comprehensive tests

- ✅ ACCEPTABLE: Feature flags for premium features
  - *Rationale:* Industry standard pattern
  - *Mitigation:* Feature flag management system (LaunchDarkly, etc.)

**Long-term Maintenance:**
- ⚠️ WATCH: Context branching complexity could grow
  - *Mitigation:* Strategy pattern, quarterly refactoring reviews
  - *Estimated cost:* 2-4 hours/quarter

**Architecture Evolution:**
- ✅ GOOD: Easy to split later if needed (context already abstracted)
- ✅ GOOD: Can add more user types (enterprise, trial, etc.)
- ✅ GOOD: Feature flags make A/B testing easy

### 3.3 Validation & Testing Strategy

**Success Criteria (Measurable):**
```python
# Performance
assert p95_response_time < 500  # Same as guest
assert cache_hit_rate > 80      # Same as guest
assert error_rate < 1           # Same as guest

# Functionality
assert authenticated_user_can_chat == True
assert premium_features_enabled_for_auth == True
assert guest_features_still_work == True

# Data Isolation
assert guest_data_retention == 90_days
assert auth_data_retention == PERMANENT
assert no_data_leakage_between_user_types == True
```

**Validation Experiments:**

1. **Load Test: Mixed Traffic** (1 hour)
   ```python
   # 50% guest users, 50% authenticated users
   # Target: Same performance as guest-only
   concurrent_users = 1000
   guest_ratio = 0.5
   auth_ratio = 0.5

   results = await load_test(
       duration=300,  # 5 minutes
       users=concurrent_users,
       guest_ratio=guest_ratio,
       auth_ratio=auth_ratio,
   )

   assert results.p95 < 500
   assert results.error_rate < 0.01
   ```

2. **Feature Flag Test: Progressive Rollout** (1 day)
   ```python
   # Day 1: 10% of authenticated users
   # Day 2: 50% of authenticated users
   # Day 3: 100% of authenticated users

   rollout_schedule = [0.1, 0.5, 1.0]
   for percentage in rollout_schedule:
       enable_feature("authenticated_chat", percentage)
       await monitor_metrics(duration=hours(24))
       if metrics.error_rate > 0.01:
           rollback()
           break
   ```

3. **Data Isolation Test** (30 minutes)
   ```python
   # Verify guest and authenticated data never mix
   guest_user = create_guest_user()
   auth_user = create_authenticated_user()

   guest_conv = await guest_user.create_conversation()
   auth_conv = await auth_user.create_conversation()

   # Should use different tables
   assert guest_conv.table_name == "guest_conversations"
   assert auth_conv.table_name == "chat_conversations"

   # Should not be cross-accessible
   with pytest.raises(UnauthorizedError):
       await auth_user.get_conversation(guest_conv.id)
   ```

**Error Detection & Rollback:**
```python
# Canary deployment with automatic rollback
if error_rate > 1% or p95_latency > 1000:
    logger.critical("Metrics exceeded threshold, rolling back")
    disable_feature("authenticated_chat")
    alert_oncall("Authenticated chat rollback triggered")

# Gradual rollout with kill switch
KILL_SWITCH = redis.get("feature:authenticated_chat:kill_switch")
if KILL_SWITCH:
    return legacy_response()
```

---

## 🚀 Implementation Plan (1 Week)

### Time Allocation (Following CTO Methodology)

- **Analysis:** 25% (1.25 days) ✅ COMPLETE (this document)
- **Design:** 35% (1.75 days) → Detailed design specs
- **Risk Assessment:** 15% (0.75 days) → Test planning
- **Implementation:** 25% (1.25 days) → Code + tests

**Total: 5 working days (1 week)**

---

### Day 1-2: Design Phase (35% of time)

**1.1 Context Abstraction Design** (4 hours)

```python
# src/app/domain/chat/value_objects.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class UserContext(ABC):
    """Abstract user context."""

    @abstractmethod
    def get_user_id(self) -> str:
        """Get unique user identifier."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        pass

    @abstractmethod
    def get_rate_limit(self) -> tuple[int, int]:
        """Get rate limit (messages, window_seconds)."""
        pass

    @abstractmethod
    def get_retention_days(self) -> Optional[int]:
        """Get data retention in days (None = permanent)."""
        pass


@dataclass(frozen=True)
class GuestContext(UserContext):
    """Guest user context."""
    ip_address: str

    def get_user_id(self) -> str:
        return f"guest:{self.ip_address}"

    def is_authenticated(self) -> bool:
        return False

    def get_rate_limit(self) -> tuple[int, int]:
        return (20, 3600)  # 20 messages per hour

    def get_retention_days(self) -> Optional[int]:
        return 90  # 90 days retention


@dataclass(frozen=True)
class AuthenticatedContext(UserContext):
    """Authenticated user context."""
    user_id: UUID
    email: str
    subscription_tier: str = "free"

    def get_user_id(self) -> str:
        return f"auth:{self.user_id}"

    def is_authenticated(self) -> bool:
        return True

    def get_rate_limit(self) -> tuple[int, int]:
        if self.subscription_tier == "premium":
            return (10000, 3600)  # 10k/hour
        return (1000, 3600)  # 1k/hour for free tier

    def get_retention_days(self) -> Optional[int]:
        return None  # Permanent retention


@dataclass(frozen=True)
class FeatureFlags:
    """Feature availability based on user context."""

    # Basic features (available to all)
    hunter_sentiment: bool = True
    hunter_trading_signals: bool = True
    hunter_price_prediction: bool = True

    # Premium features (authenticated only)
    hunter_patterns: bool = False
    hunter_portfolio: bool = False
    hunter_risk_signals: bool = False

    # Advanced features (premium tier)
    export_conversations: bool = False
    unlimited_history: bool = False
    advanced_analytics: bool = False
    priority_support: bool = False

    @classmethod
    def from_context(cls, context: UserContext) -> 'FeatureFlags':
        """Create feature flags from user context."""
        if isinstance(context, GuestContext):
            return cls(
                # Basic features only
                hunter_patterns=False,
                hunter_portfolio=False,
                hunter_risk_signals=False,
            )

        elif isinstance(context, AuthenticatedContext):
            if context.subscription_tier == "premium":
                # All features
                return cls(
                    hunter_patterns=True,
                    hunter_portfolio=True,
                    hunter_risk_signals=True,
                    export_conversations=True,
                    unlimited_history=True,
                    advanced_analytics=True,
                    priority_support=True,
                )
            else:
                # Standard authenticated features
                return cls(
                    hunter_patterns=True,
                    hunter_portfolio=True,
                    hunter_risk_signals=True,
                )

        # Default: basic only
        return cls()
```

**1.2 Unified Handler Design** (4 hours)

```python
# src/app/application/chat/handlers/unified_chat_handler.py

class UnifiedChatHandler:
    """
    Universal chat handler for guest and authenticated users.

    Architecture:
    - Single handler for both user types
    - Context determines behavior (storage, features, limits)
    - Feature flags control premium access
    - Same Hunter AI core for all users
    """

    def __init__(
        self,
        # Gateways for both storage types
        guest_gateway: GuestConversationCommandGateway,
        auth_gateway: ChatConversationCommandGateway,

        # Shared infrastructure
        cache: GuestCache,
        hunter_service: HunterAIService,
        rate_limiter: RateLimiter,
    ):
        self._guest_gateway = guest_gateway
        self._auth_gateway = auth_gateway
        self._cache = cache
        self._hunter_service = hunter_service
        self._rate_limiter = rate_limiter

    async def handle_message(
        self,
        content: str,
        language: str,
        context: UserContext,
    ) -> dict:
        """
        Handle chat message for any user type.

        Flow:
        1. Check rate limit (context-specific)
        2. Get or create user/conversation (context-specific storage)
        3. Classify intent
        4. Check cache (shared)
        5. Process with Hunter AI (feature-flag-gated)
        6. Save message (context-specific storage)
        7. Return response
        """

        # 1. Rate limiting (context-aware)
        limit, window = context.get_rate_limit()
        await self._rate_limiter.check_limit(
            key=context.get_user_id(),
            limit=limit,
            window=window,
        )

        # 2. Get storage gateway (polymorphic)
        gateway = self._get_gateway(context)

        # 3. Get or create conversation
        conversation = await gateway.get_or_create_active_conversation(
            user_identifier=context.get_user_id(),
            language=language,
        )

        # 4. Classify intent
        intent = await self._classify_intent(content)

        # 5. Get feature flags
        features = FeatureFlags.from_context(context)

        # 6. Check if intent is allowed
        if not self._is_intent_allowed(intent, features):
            return {
                "content": "This feature requires authentication. Please sign up for free access!",
                "requires_registration": True,
            }

        # 7. Check cache (shared across all users)
        token = self._extract_token(content) or "BTC"
        cached = await self._cache.get_hunter_response(
            intent, token, language
        )

        if cached:
            # Save message from cache
            await gateway.create_message(
                conversation_id=conversation.id,
                role="user",
                content=content,
                intent=intent,
                enrichment=cached.get("enrichment"),
            )
            return cached

        # 8. Process with Hunter AI
        response = await self._hunter_service.process(
            intent=intent,
            token=token,
            language=language,
            is_authenticated=context.is_authenticated(),
            features=features,
        )

        # 9. Cache response (shared)
        await self._cache.set_hunter_response(
            intent, token, language, response
        )

        # 10. Save message
        await gateway.create_message(
            conversation_id=conversation.id,
            role="user",
            content=content,
            intent=intent,
            enrichment=response.get("enrichment"),
        )

        return response

    def _get_gateway(self, context: UserContext):
        """Get appropriate storage gateway based on context."""
        if isinstance(context, GuestContext):
            return self._guest_gateway
        elif isinstance(context, AuthenticatedContext):
            return self._auth_gateway
        else:
            raise ValueError(f"Unknown context type: {type(context)}")

    def _is_intent_allowed(self, intent: str, features: FeatureFlags) -> bool:
        """Check if intent is allowed for user's feature flags."""
        intent_feature_map = {
            "hunter_sentiment": features.hunter_sentiment,
            "hunter_trading_signals": features.hunter_trading_signals,
            "hunter_price_prediction": features.hunter_price_prediction,
            "hunter_patterns": features.hunter_patterns,
            "hunter_portfolio": features.hunter_portfolio,
            "hunter_risk_signals": features.hunter_risk_signals,
        }

        return intent_feature_map.get(intent, False)
```

**1.3 API Endpoint Design** (2 hours)

```python
# src/app/presentation/http/controllers/chat/universal_chat_router.py

from fastapi import APIRouter, Depends, Request
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["Universal Chat"])


async def get_optional_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    """
    Get authenticated user if JWT token provided.
    Returns None if no token (guest user).
    """
    if not authorization:
        return None

    try:
        token = authorization.replace("Bearer ", "")
        user = await verify_jwt(token)
        return user
    except Exception:
        # Invalid token = treat as guest
        return None


async def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    return request.client.host


@router.post("/chat")  # Universal endpoint
async def universal_chat(
    request: ChatRequest,
    user: Optional[User] = Depends(get_optional_user),
    ip_address: str = Depends(get_client_ip),
    handler: UnifiedChatHandler = Depends(get_unified_chat_handler),
):
    """
    Universal chat endpoint for guest and authenticated users.

    Authentication:
    - Optional: Provide JWT in Authorization header for authenticated features
    - No token: Treated as guest user (basic features only)

    Rate Limits:
    - Guest: 20 messages/hour
    - Authenticated (free): 1000 messages/hour
    - Authenticated (premium): 10000 messages/hour

    Features:
    - Guest: Sentiment, Trading Signals, Price Prediction
    - Authenticated: + Patterns, Portfolio, Risk Signals
    - Premium: + Export, Advanced Analytics, Priority Support
    """

    # Create context based on authentication
    if user:
        context = AuthenticatedContext(
            user_id=user.id,
            email=user.email,
            subscription_tier=user.subscription_tier,
        )
    else:
        context = GuestContext(ip_address=ip_address)

    # Handle message (unified handler)
    response = await handler.handle_message(
        content=request.content,
        language=request.language,
        context=context,
    )

    return ChatResponse(
        message_id=response.get("message_id"),
        content=response.get("content"),
        intent=response.get("intent"),
        enrichment=response.get("enrichment"),
        requires_registration=response.get("requires_registration", False),
        user_type="authenticated" if user else "guest",
        features_available=FeatureFlags.from_context(context),
    )


# Backward compatibility alias
@router.post("/guest/chat")
async def guest_chat_alias(
    request: ChatRequest,
    ip_address: str = Depends(get_client_ip),
    handler: UnifiedChatHandler = Depends(get_unified_chat_handler),
):
    """
    Legacy guest chat endpoint.
    Redirects to universal endpoint with guest context.
    """
    context = GuestContext(ip_address=ip_address)

    response = await handler.handle_message(
        content=request.content,
        language=request.language,
        context=context,
    )

    return ChatResponse(**response)
```

**Deliverables:**
- [ ] Context abstraction complete
- [ ] Unified handler design reviewed
- [ ] API endpoint specification finalized
- [ ] Feature flag matrix documented

---

### Day 2-3: Implementation Phase (25% of time)

**2.1 Database Schema** (2 hours)

```sql
-- Authenticated user tables (similar to guest but different retention)

CREATE TABLE chat_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,  -- References auth.users
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chat_users_user FOREIGN KEY (user_id)
        REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_user_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chat_conversations_user FOREIGN KEY (chat_user_id)
        REFERENCES chat_users(id) ON DELETE CASCADE
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(100),
    enrichment JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chat_messages_conversation FOREIGN KEY (conversation_id)
        REFERENCES chat_conversations(id) ON DELETE CASCADE
);

-- Performance indexes (same as guest)
CREATE INDEX idx_chat_users_user_id ON chat_users(user_id);
CREATE INDEX idx_chat_conversations_user_status ON chat_conversations(chat_user_id, status, created_at DESC);
CREATE INDEX idx_chat_messages_conversation_created ON chat_messages(conversation_id, created_at ASC);
```

**2.2 Implementation** (6 hours)

1. Create domain entities (ChatUser, ChatConversation, ChatMessage)
2. Implement repositories (ChatUserRepository, ChatConversationRepository, ChatMessageRepository)
3. Implement UnifiedChatHandler
4. Update API endpoint
5. Add authentication dependency
6. Implement feature flags

**2.3 Testing** (Rest of Day 3)

```python
# tests/integration/chat/test_unified_chat.py

async def test_guest_user_chat():
    """Test guest user can chat with basic features."""
    response = await client.post(
        "/api/v1/chat",
        json={"content": "What is the sentiment for BTC?", "language": "en"},
    )

    assert response.status_code == 200
    assert response.json()["user_type"] == "guest"
    assert response.json()["intent"] == "hunter_sentiment"


async def test_authenticated_user_chat():
    """Test authenticated user can chat with premium features."""
    token = await create_test_user_token()

    response = await client.post(
        "/api/v1/chat",
        json={"content": "What patterns do you see in BTC?", "language": "en"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["user_type"] == "authenticated"
    assert response.json()["intent"] == "hunter_patterns"


async def test_guest_cannot_access_premium_features():
    """Test guest users get upgrade prompt for premium features."""
    response = await client.post(
        "/api/v1/chat",
        json={"content": "Analyze patterns for BTC", "language": "en"},
    )

    assert response.status_code == 200
    assert response.json()["requires_registration"] == True
    assert "authentication" in response.json()["content"].lower()


async def test_rate_limiting_different_for_users():
    """Test rate limits differ for guest vs authenticated."""
    # Guest: 20 messages/hour
    for i in range(25):
        response = await client.post("/api/v1/chat", json={"content": f"test {i}"})
        if i < 20:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Rate limited

    # Authenticated: 1000 messages/hour
    token = await create_test_user_token()
    for i in range(50):
        response = await client.post(
            "/api/v1/chat",
            json={"content": f"test {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200  # No rate limiting


async def test_data_isolation():
    """Test guest and authenticated data is isolated."""
    # Guest conversation
    guest_response = await client.post(
        "/api/v1/chat",
        json={"content": "Hello", "language": "en"},
    )

    # Authenticated conversation
    token = await create_test_user_token()
    auth_response = await client.post(
        "/api/v1/chat",
        json={"content": "Hello", "language": "en"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Verify different tables
    guest_conv = await db.execute("SELECT * FROM guest_conversations")
    auth_conv = await db.execute("SELECT * FROM chat_conversations")

    assert len(guest_conv) == 1
    assert len(auth_conv) == 1
    assert guest_conv[0].id != auth_conv[0].id


async def test_cache_shared_across_user_types():
    """Test cache is shared between guest and authenticated users."""
    # Guest request (populates cache)
    response1 = await client.post(
        "/api/v1/chat",
        json={"content": "What is the sentiment for BTC?", "language": "en"},
    )

    # Authenticated request (should hit cache)
    token = await create_test_user_token()
    start = time.time()
    response2 = await client.post(
        "/api/v1/chat",
        json={"content": "What is the sentiment for BTC?", "language": "en"},
        headers={"Authorization": f"Bearer {token}"},
    )
    duration = time.time() - start

    # Should be fast (cached)
    assert duration < 0.1  # <100ms
    assert response2.json()["enrichment"] == response1.json()["enrichment"]
```

---

### Day 4: Risk Assessment & Validation (15% of time)

**3.1 Load Testing** (3 hours)

```python
# tests/load/unified_chat_load_test.py

async def test_mixed_user_load():
    """Load test with 50% guest, 50% authenticated users."""

    results = await load_test(
        url="http://localhost:8080/api/v1/chat",
        duration=300,  # 5 minutes
        concurrent_users=1000,
        guest_ratio=0.5,
        auth_ratio=0.5,

        # Success criteria (same as guest-only)
        max_error_rate=0.01,  # <1%
        max_p95_latency=500,  # <500ms
        min_cache_hit_rate=0.8,  # >80%
    )

    assert results.error_rate < 0.01
    assert results.p95_latency < 500
    assert results.cache_hit_rate > 0.8
```

**3.2 Security Testing** (2 hours)

```python
# tests/security/test_authenticated_chat_security.py

async def test_jwt_validation():
    """Test JWT token validation."""
    # Invalid token
    response = await client.post(
        "/api/v1/chat",
        json={"content": "test"},
        headers={"Authorization": "Bearer invalid_token"},
    )

    # Should treat as guest (graceful degradation)
    assert response.status_code == 200
    assert response.json()["user_type"] == "guest"


async def test_no_cross_user_access():
    """Test users cannot access each other's data."""
    user1_token = await create_test_user_token(user_id="user1")
    user2_token = await create_test_user_token(user_id="user2")

    # User 1 creates conversation
    response1 = await client.post(
        "/api/v1/chat",
        json={"content": "Hello"},
        headers={"Authorization": f"Bearer {user1_token}"},
    )

    # User 2 cannot access User 1's data
    conv_id = response1.json()["conversation_id"]
    response2 = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {user2_token}"},
    )

    assert response2.status_code == 403  # Forbidden
```

**3.3 Monitoring Setup** (2 hours)

```python
# Add unified metrics

cloudwatch.track_chat_message(
    user_type="guest" if isinstance(context, GuestContext) else "authenticated",
    intent=intent,
    cache_hit=cached is not None,
    response_time_ms=duration,
)

# Sentry context
sentry_sdk.set_tag("user_type", context.get_user_id().split(":")[0])
sentry_sdk.set_tag("subscription_tier",
    context.subscription_tier if isinstance(context, AuthenticatedContext) else "guest"
)
```

---

### Day 5: Documentation & Deployment (Remaining time)

**4.1 Documentation** (3 hours)

- API documentation with authentication examples
- Migration guide from legacy system
- Feature comparison table (guest vs auth vs premium)
- Developer guide for adding new features

**4.2 Deployment Preparation** (2 hours)

- Create Alembic migration for chat_* tables
- Update environment variables
- Create deployment checklist
- Write rollback procedure

**4.3 Stakeholder Demo** (1 hour)

- Demo guest flow (unchanged)
- Demo authenticated flow (new features)
- Show premium tier benefits
- Performance metrics comparison

---

## 📊 Success Metrics

### Functional Success
- ✅ Guest users can still chat (no regression)
- ✅ Authenticated users can chat with same UX
- ✅ Premium features work for authenticated users
- ✅ Rate limiting works for both user types
- ✅ Data isolation maintained

### Performance Success
- ✅ P95 response time <500ms (both user types)
- ✅ Cache hit rate >80% (shared cache)
- ✅ Error rate <1%
- ✅ Load test passes (1000 concurrent users, mixed traffic)

### Quality Success
- ✅ Unit test coverage >90%
- ✅ Integration test coverage >85%
- ✅ Security tests pass
- ✅ Load tests pass

### Business Success
- ✅ Zero regression for existing guest users
- ✅ Clear upgrade path (guest → auth → premium)
- ✅ Same proven UX across all tiers
- ✅ Easy to add more tiers in future

---

## 🎯 Key Decisions

**Decision 1: Single Endpoint vs Separate Endpoints**
- ✅ CHOSEN: Single endpoint (`/api/v1/chat`) with optional authentication
- RATIONALE: Maximum code reuse, consistent UX, simpler maintenance
- REJECTED: Separate endpoints (code duplication, API fragmentation)

**Decision 2: Feature Flags vs Separate Handlers**
- ✅ CHOSEN: Feature flags based on user context
- RATIONALE: Clean abstraction, easy to test, flexible for A/B testing
- REJECTED: Separate handlers (code duplication, hard to keep in sync)

**Decision 3: Database Tables - Shared vs Separate**
- ✅ CHOSEN: Separate tables (guest_* vs chat_*)
- RATIONALE: Different retention policies, different business logic, data isolation
- REJECTED: Shared tables (complex retention logic, no clear separation)

**Decision 4: Cache Strategy - Shared vs Isolated**
- ✅ CHOSEN: Shared cache across all user types
- RATIONALE: Maximum cache hit rate, proven to work (96.1%), cost efficient
- REJECTED: Isolated caches (lower hit rates, more complex, higher cost)

---

## 📈 Future Enhancements (Post-Launch)

### Phase 2: Advanced Features (Week 2-3)
- Conversation export (JSON, CSV, PDF)
- Conversation search and filtering
- User preferences management
- Conversation sharing

### Phase 3: Premium Tier (Week 4-5)
- Advanced analytics dashboard
- Custom alert notifications
- Priority support
- API access for integrations

### Phase 4: Enterprise (Month 2-3)
- Team collaboration features
- Admin dashboard
- Usage analytics
- SSO integration

---

## 🔐 Security Considerations

**Authentication:**
- ✅ Optional JWT (graceful degradation to guest)
- ✅ Token validation with expiry
- ✅ No authentication bypass vectors

**Authorization:**
- ✅ Feature flags enforce premium access
- ✅ Rate limiting per user type
- ✅ Data isolation (separate tables)

**Data Privacy:**
- ✅ Guest: IP anonymization (same as current)
- ✅ Auth: Standard PII protection
- ✅ Compliance: GDPR, CCPA ready

---

## 📋 Dependencies

**Existing (No Changes Needed):**
- ✅ Guest chat system (production-ready)
- ✅ Hunter AI handlers (working perfectly)
- ✅ Redis caching (96.1% hit rate)
- ✅ Authentication system (JWT)

**New (Need to Create):**
- Database tables (chat_users, chat_conversations, chat_messages)
- Context abstraction (UserContext, GuestContext, AuthenticatedContext)
- Feature flags (FeatureFlags class)
- Unified handler (UnifiedChatHandler)

---

## 🚨 Rollback Plan

**If issues detected after deployment:**

1. **Immediate Rollback** (<5 minutes)
   ```python
   # Disable authenticated chat via feature flag
   redis.set("feature:authenticated_chat:enabled", "false")

   # All requests treated as guest
   # Zero downtime
   ```

2. **Partial Rollback** (<15 minutes)
   ```python
   # Gradual rollback (reduce authenticated user percentage)
   redis.set("feature:authenticated_chat:rollout_percentage", "50")
   redis.set("feature:authenticated_chat:rollout_percentage", "10")
   redis.set("feature:authenticated_chat:rollout_percentage", "0")
   ```

3. **Database Rollback** (if needed)
   ```bash
   # Drop new tables (no data loss - auth users weren't using it yet)
   alembic downgrade -1
   ```

---

## 🎓 Lessons from CTO Methodology

**First Principles Analysis:**
- Problem essence: Extend proven system, don't build new one
- Core truth: Guest chat works, reuse it

**Design Thinking:**
- Diverged into 3 approaches
- Converged on unified endpoint (best trade-offs)
- User-centered: Same UX is best UX

**Systems Thinking:**
- Identified invariants (Hunter AI, cache, UX)
- Leveraged design freedom (context, feature flags)
- Managed constraints (retention, rate limits)

**Risk Management:**
- Cognitive limitations acknowledged
- Validation experiments defined
- Rollback mechanisms ready

---

**Plan Status:** Draft - Ready for Review
**Estimated Effort:** 1 week (5 days)
**Risk Level:** Low (extending proven system)
**Business Value:** High (enables monetization)

**Next Step:** Team review and approval to proceed with implementation

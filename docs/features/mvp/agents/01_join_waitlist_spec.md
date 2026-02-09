# Join Waitlist — Chat Agent CTA Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Context**: Chat Response Enrichment (conversations/messages)  
**Related**: Guest Chat Spec, Gamification AARRR, Unified Chat Routing

---

## Overview

Periodic promotional CTA injected into chat agent responses that encourages unauthenticated or waitlisted users to join the Anvil waitlist. Shown **once every 10–20 minutes per user** — not on every response. The CTA is embedded as structured data in the `enrichment` field of the `UnifiedChatResponse`, allowing the frontend to render it as a dismissible card/banner within the chat flow.

---

## Trigger Rules

### When to Show

| Condition | Rule |
|-----------|------|
| **Frequency** | Maximum once per 10–20 min per user (randomized to feel organic) |
| **User type** | Guest users (unauthenticated) OR authenticated users not yet on waitlist |
| **Cooldown** | After user dismisses → 30 min cooldown before next eligible show |
| **Session limit** | Max 3 per session (to avoid annoyance) |
| **First message** | Never on the first message of a conversation (let user engage first) |
| **After value** | Prefer showing after high-value responses (sentiment analysis, balance info, swap quote) |

### When NOT to Show

- User is already registered AND has wallet connected
- User is already on the waitlist (show different CTA: "You're on the list! #{{position}}")
- User has explicitly dismissed 3+ times in current session
- Error responses or empty responses
- Rate-limited responses

---

## Architecture

### Tracking State

```python
# Redis key pattern for cooldown tracking
WAITLIST_CTA_KEY = "waitlist_cta:{user_id_or_ip}"
# Value: JSON { "last_shown_at": "ISO8601", "shown_count_session": int, "dismissed_count": int }
# TTL: 24 hours (resets daily)

# For guest users, use IP + fingerprint hash as identifier
# For authenticated users, use user_id
```

### Decision Logic (CTA Eligibility Service)

```python
class WaitlistCTAService:
    """Determines if a join_waitlist CTA should be injected into the response."""

    COOLDOWN_MIN_SECONDS = 600   # 10 minutes
    COOLDOWN_MAX_SECONDS = 1200  # 20 minutes
    DISMISS_COOLDOWN_SECONDS = 1800  # 30 minutes after dismiss
    MAX_PER_SESSION = 3

    async def should_show_cta(
        self,
        user_id: str | None,
        guest_id: str | None,
        is_first_message: bool,
        conversation_message_count: int,
        response_intent: str,
    ) -> bool:
        """Check if CTA should be shown in this response."""
        
        identifier = user_id or guest_id
        if not identifier:
            return False

        # Rule 1: Never on first message
        if is_first_message or conversation_message_count < 2:
            return False

        # Rule 2: Check if user already registered + wallet
        if user_id:
            user = await self._user_repo.get(user_id)
            if user and user.has_wallet and not user.is_waitlisted:
                return False  # Full user, no CTA needed

        # Rule 3: Check cooldown from Redis
        state = await self._cache.get(f"waitlist_cta:{identifier}")
        if state:
            elapsed = (now() - state["last_shown_at"]).total_seconds()
            cooldown = state.get("cooldown_seconds", self.COOLDOWN_MIN_SECONDS)
            if elapsed < cooldown:
                return False
            if state["shown_count_session"] >= self.MAX_PER_SESSION:
                return False

        # Rule 4: Randomize within 10-20 min window (organic feel)
        next_cooldown = random.randint(
            self.COOLDOWN_MIN_SECONDS,
            self.COOLDOWN_MAX_SECONDS
        )

        return True

    async def record_shown(self, identifier: str) -> None:
        """Record that CTA was shown."""
        state = await self._cache.get(f"waitlist_cta:{identifier}") or {
            "shown_count_session": 0,
            "dismissed_count": 0,
        }
        state["last_shown_at"] = now().isoformat()
        state["shown_count_session"] += 1
        state["cooldown_seconds"] = random.randint(
            self.COOLDOWN_MIN_SECONDS, self.COOLDOWN_MAX_SECONDS
        )
        await self._cache.set(
            f"waitlist_cta:{identifier}", state, ttl=86400
        )

    async def record_dismissed(self, identifier: str) -> None:
        """User dismissed CTA — apply extended cooldown."""
        state = await self._cache.get(f"waitlist_cta:{identifier}") or {}
        state["dismissed_count"] = state.get("dismissed_count", 0) + 1
        state["last_shown_at"] = now().isoformat()
        state["cooldown_seconds"] = self.DISMISS_COOLDOWN_SECONDS
        await self._cache.set(
            f"waitlist_cta:{identifier}", state, ttl=86400
        )
```

---

## Response Schema

### Enrichment Field (injected into UnifiedChatResponse)

```python
class WaitlistCTA(BaseModel):
    type: Literal["join_waitlist"] = "join_waitlist"
    title: str                      # "Join the Anvil Waitlist"
    message: str                    # Context-aware message
    cta_text: str                   # Button label: "Join Waitlist"
    cta_url: str                    # Deep link or action URL
    variant: str                    # A/B test variant: "value_prop" | "social_proof" | "urgency"
    dismissible: bool = True        # User can dismiss
    position: str = "after_response"  # Where to render: "after_response" | "inline"
    xp_bonus: int | None = None     # "Sign up and earn 100 XP" (gamification tie-in)
```

### Example Response

```json
{
  "user_message": { "content": "what's the sentiment on ETH?", ... },
  "agent_message": { "content": "ETH is showing bullish momentum...", ... },
  "routing": { "intent": "HUNTER_SENTIMENT", "confidence": 0.92, ... },
  "enrichment": {
    "sentiment_data": { ... },
    "join_waitlist": {
      "type": "join_waitlist",
      "title": "🚀 Get Full Access to Anvil",
      "message": "Love the sentiment insights? Join the waitlist to unlock real-time alerts, portfolio tracking, and one-tap swaps.",
      "cta_text": "Join Waitlist — It's Free",
      "cta_url": "https://anvil.finance/waitlist?ref=chat&intent=sentiment",
      "variant": "value_prop",
      "dismissible": true,
      "position": "after_response",
      "xp_bonus": 100
    }
  }
}
```

---

## CTA Variants (A/B Testing)

### Variant 1: Value Proposition

```json
{
  "variant": "value_prop",
  "title": "🚀 Get Full Access to Anvil",
  "message": "Unlock real-time alerts, portfolio tracking, and one-tap DeFi operations.",
  "cta_text": "Join Waitlist — It's Free"
}
```

### Variant 2: Social Proof

```json
{
  "variant": "social_proof",
  "title": "Join 12,847 Users on Anvil",
  "message": "Thousands of DeFi users are already chatting with Anvil. Don't miss out.",
  "cta_text": "Get Early Access"
}
```

### Variant 3: Urgency

```json
{
  "variant": "urgency",
  "title": "⏰ Limited Early Access Spots",
  "message": "Early access users get lifetime benefits. Spots are filling fast.",
  "cta_text": "Claim Your Spot"
}
```

### Variant Selection Logic

```python
def select_variant(intent: str, message_count: int) -> str:
    """Select variant based on context."""
    if message_count <= 3:
        return "value_prop"       # First few messages: explain value
    elif message_count <= 8:
        return "social_proof"     # Mid-session: social pressure
    else:
        return "urgency"          # Deep session: urgency
```

---

## Dismiss Endpoint

```
POST /api/v1/chat/waitlist-cta/dismiss
```

**Auth**: Optional (works for guest + authenticated)

### Request Body

```json
{
  "conversation_id": "uuid",
  "variant": "value_prop"
}
```

### Response 200

```json
{
  "acknowledged": true,
  "next_eligible_minutes": 30
}
```

---

## Waitlist Submit Endpoint

```
POST /api/v1/waitlist/join
```

**Auth**: Optional

### Request Body

```json
{
  "email": "user@example.com",
  "referral_code": "abc123",
  "source": "chat_cta",
  "intent_context": "sentiment_analysis"
}
```

### Response 201

```json
{
  "success": true,
  "position": 1284,
  "message": "You're #1,284 on the list! We'll notify you when it's your turn.",
  "xp_earned": 100,
  "referral_code": "usr_def789"
}
```

---

## Database

### Table: `waitlist_entries`

```sql
CREATE TABLE waitlist_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    referred_by VARCHAR(50) REFERENCES waitlist_entries(referral_code),
    source VARCHAR(50) DEFAULT 'chat_cta',       -- chat_cta, landing_page, social
    intent_context VARCHAR(100),                  -- which intent triggered the CTA
    variant_shown VARCHAR(50),                    -- which A/B variant converted
    position INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting',         -- waiting, invited, registered
    invited_at TIMESTAMPTZ,
    registered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_waitlist_email ON waitlist_entries(email);
CREATE INDEX idx_waitlist_status ON waitlist_entries(status);
CREATE INDEX idx_waitlist_position ON waitlist_entries(position);
CREATE INDEX idx_waitlist_referral ON waitlist_entries(referral_code);
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/chat/waitlist_cta.py` | Dismiss + Join endpoints |
| **Application** | `services/waitlist_cta_service.py` | Eligibility logic + variant selection |
| **Application** | `commands/waitlist/join_waitlist.py` | Join handler |
| **Domain** | `entities/waitlist.py` | WaitlistEntry entity |
| **Domain** | `ports/waitlist_repository.py` | WaitlistRepository protocol |
| **Infrastructure** | `adapters/waitlist/pg_waitlist_repo.py` | PostgreSQL adapter |
| **Infrastructure** | `adapters/cache/redis_cta_state.py` | Redis cooldown state |

---

## Integration Point

The CTA injection happens **after** the main handler returns its response, inside the `UnifiedChatOrchestrator`:

```python
# In UnifiedChatOrchestrator.execute()
response = await handler.handle(message, context)

# Post-processing: inject waitlist CTA if eligible
if await self._waitlist_cta_service.should_show_cta(
    user_id=context.user_id,
    guest_id=context.guest_id,
    is_first_message=context.message_index == 0,
    conversation_message_count=context.message_count,
    response_intent=routing.intent,
):
    response.enrichment["join_waitlist"] = self._waitlist_cta_service.build_cta(
        intent=routing.intent,
        message_count=context.message_count,
    )
    await self._waitlist_cta_service.record_shown(identifier)

return response
```

---

## Metrics

| Metric | Target |
|--------|--------|
| CTA impression rate | 1 per 15 min average |
| CTA click-through rate | > 5% |
| Dismiss rate | < 40% |
| Waitlist conversion (impression → join) | > 3% |
| Session engagement after CTA | No drop in message count |

---

## Frontend Rendering

```
┌─────────────────────────────────────────┐
│  🤖 ETH is showing bullish momentum    │
│  with a sentiment score of 0.78...      │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  🚀 Get Full Access to Anvil       ││
│  │                                     ││
│  │  Love the sentiment insights? Join  ││
│  │  the waitlist to unlock real-time   ││
│  │  alerts and one-tap swaps.          ││
│  │                                     ││
│  │  [Join Waitlist — It's Free]    [✕] ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Open Items

- [ ] A/B test variant weighting via admin config
- [ ] Waitlist position counter: sequential vs batch invites
- [ ] Email verification flow after join
- [ ] Integration with gamification XP system (UC-A1 Onboarding Quest)
- [ ] i18n for CTA messages (en, es, pt, zh)

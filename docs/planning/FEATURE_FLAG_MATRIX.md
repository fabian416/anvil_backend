# Feature Flag Matrix

**Date:** 2026-01-12
**Status:** Design Complete
**Implementation:** Day 1-2 of Authenticated User Enhancement Plan

---

## Overview

This document defines the complete feature availability matrix for the unified chat system, showing which features are available to each user type and subscription tier.

The feature flag system enables:
- **Progressive enhancement**: Guest → Free → Premium → Enterprise
- **Feature gating**: Premium features locked behind authentication
- **Flexible tier management**: Easy to add/modify tiers without code changes
- **Clear upgrade paths**: Users see exactly what they gain by upgrading

---

## User Types and Contexts

### Guest Users (GuestContext)

**Identification**: IP address
**Authentication**: None required
**Rate Limit**: 20 messages/hour
**Data Retention**: 90 days
**Storage Tables**: `guest_*` (guest_users, guest_conversations, guest_messages)

**Use Cases**:
- First-time visitors exploring Hunter AI
- Users testing the platform before registering
- Quick crypto sentiment checks without commitment

### Authenticated Users (AuthenticatedContext)

**Identification**: UUID
**Authentication**: JWT token required
**Rate Limit**: 1,000 - 10,000 messages/hour (tier-dependent)
**Data Retention**: Permanent
**Storage Tables**: `chat_*` (chat_users, chat_conversations, chat_messages)

**Subscription Tiers**:
- **Free**: Basic + Premium hunter features
- **Premium**: Free tier + Advanced features
- **Enterprise**: All features including team collaboration

---

## Complete Feature Matrix

| Feature Category | Feature Name | Guest | Free Auth | Premium | Enterprise | Description |
|-----------------|--------------|-------|-----------|---------|------------|-------------|
| **Basic Hunter AI** | | | | | | |
| | `hunter_sentiment` | ✅ | ✅ | ✅ | ✅ | Crypto sentiment analysis |
| | `hunter_trading_signals` | ✅ | ✅ | ✅ | ✅ | Buy/sell/hold signals |
| | `hunter_price_prediction` | ✅ | ✅ | ✅ | ✅ | Price forecasting |
| **Premium Hunter AI** | | | | | | |
| | `hunter_patterns` | ❌ | ✅ | ✅ | ✅ | Technical pattern detection |
| | `hunter_portfolio` | ❌ | ✅ | ✅ | ✅ | Portfolio optimization |
| | `hunter_risk_signals` | ❌ | ✅ | ✅ | ✅ | Risk analysis and warnings |
| **Advanced Features** | | | | | | |
| | `export_conversations` | ❌ | ❌ | ✅ | ✅ | Export chat history (JSON/CSV) |
| | `unlimited_history` | ❌ | ❌ | ✅ | ✅ | Permanent conversation storage |
| | `advanced_analytics` | ❌ | ❌ | ✅ | ✅ | Deep analytics dashboards |
| | `priority_support` | ❌ | ❌ | ✅ | ✅ | Priority customer support |
| | `custom_alerts` | ❌ | ❌ | ✅ | ✅ | Custom price/signal alerts |
| | `api_access` | ❌ | ❌ | ✅ | ✅ | Programmatic API access |
| **Enterprise Features** | | | | | | |
| | `team_collaboration` | ❌ | ❌ | ❌ | ✅ | Shared workspaces and chat |
| | `sso_integration` | ❌ | ❌ | ❌ | ✅ | Single Sign-On (SAML/OAuth) |
| | `admin_dashboard` | ❌ | ❌ | ❌ | ✅ | Team admin controls |
| | `dedicated_support` | ❌ | ❌ | ❌ | ✅ | Dedicated account manager |

**Legend**:
- ✅ = Feature available
- ❌ = Feature locked (upgrade required)

---

## Feature Flag Implementation

### Code Structure

```python
# src/app/domain/chat/value_objects.py

@dataclass(frozen=True)
class FeatureFlags:
    """Feature availability flags based on user context."""

    # Basic features (all users)
    hunter_sentiment: bool = True
    hunter_trading_signals: bool = True
    hunter_price_prediction: bool = True

    # Premium features (authenticated users only)
    hunter_patterns: bool = False
    hunter_portfolio: bool = False
    hunter_risk_signals: bool = False

    # Advanced features (premium tier only)
    export_conversations: bool = False
    unlimited_history: bool = False
    advanced_analytics: bool = False
    priority_support: bool = False
    custom_alerts: bool = False
    api_access: bool = False

    # Enterprise features
    team_collaboration: bool = False
    sso_integration: bool = False
    admin_dashboard: bool = False
    dedicated_support: bool = False
```

### Factory Method

```python
@classmethod
def from_context(cls, context: UserContext) -> 'FeatureFlags':
    """Create feature flags from user context."""

    if isinstance(context, GuestContext):
        # Guest users: Basic features only
        return cls(
            hunter_sentiment=True,
            hunter_trading_signals=True,
            hunter_price_prediction=True,
            # All premium/advanced/enterprise features = False
        )

    elif isinstance(context, AuthenticatedContext):
        if context.subscription_tier == "enterprise":
            # Enterprise: All features enabled
            return cls(
                hunter_sentiment=True,
                hunter_trading_signals=True,
                hunter_price_prediction=True,
                hunter_patterns=True,
                hunter_portfolio=True,
                hunter_risk_signals=True,
                export_conversations=True,
                unlimited_history=True,
                advanced_analytics=True,
                priority_support=True,
                custom_alerts=True,
                api_access=True,
                team_collaboration=True,
                sso_integration=True,
                admin_dashboard=True,
                dedicated_support=True,
            )

        elif context.subscription_tier == "premium":
            # Premium: All features except enterprise
            return cls(
                hunter_sentiment=True,
                hunter_trading_signals=True,
                hunter_price_prediction=True,
                hunter_patterns=True,
                hunter_portfolio=True,
                hunter_risk_signals=True,
                export_conversations=True,
                unlimited_history=True,
                advanced_analytics=True,
                priority_support=True,
                custom_alerts=True,
                api_access=True,
                # Enterprise features disabled
                team_collaboration=False,
                sso_integration=False,
                admin_dashboard=False,
                dedicated_support=False,
            )

        else:  # free tier
            # Free authenticated: Basic + standard premium features
            return cls(
                hunter_sentiment=True,
                hunter_trading_signals=True,
                hunter_price_prediction=True,
                hunter_patterns=True,
                hunter_portfolio=True,
                hunter_risk_signals=True,
                # Advanced/enterprise features disabled
                export_conversations=False,
                unlimited_history=False,
                advanced_analytics=False,
                priority_support=False,
                custom_alerts=False,
                api_access=False,
                team_collaboration=False,
                sso_integration=False,
                admin_dashboard=False,
                dedicated_support=False,
            )

    # Default: Basic features only
    return cls()
```

### Intent Validation

```python
def is_intent_allowed(self, intent: str) -> bool:
    """Check if specific intent is allowed for this user."""

    intent_feature_map = {
        "hunter_sentiment": self.hunter_sentiment,
        "hunter_trading_signals": self.hunter_trading_signals,
        "hunter_price_prediction": self.hunter_price_prediction,
        "hunter_patterns": self.hunter_patterns,
        "hunter_portfolio": self.hunter_portfolio,
        "hunter_risk_signals": self.hunter_risk_signals,
    }

    return intent_feature_map.get(intent, False)
```

---

## Upgrade Prompts

When a user attempts to access a locked feature, the system returns a structured upgrade prompt:

### Guest User Accessing Premium Feature

**Request**:
```json
POST /api/v1/chat
{
  "content": "Show me portfolio optimization for my holdings",
  "language": "en"
}
```

**Response** (requires_registration=true):
```json
{
  "message_id": "temp-uuid",
  "content": "🔒 **Portfolio Optimization** is a premium feature.\n\nSign up for free to unlock:\n✨ Pattern Detection\n✨ Portfolio Optimization\n✨ Risk Analysis\n✨ Unlimited messages\n✨ Permanent conversation history\n\n[Sign Up Free](https://anvil.fi/signup)",
  "intent": "hunter_portfolio",
  "enrichment": null,
  "requires_registration": true,
  "user_type": "guest",
  "features_available": {
    "basic": {
      "sentiment": true,
      "trading_signals": true,
      "price_prediction": true
    },
    "premium": {
      "patterns": false,
      "portfolio": false,
      "risk_signals": false
    },
    "advanced": {
      "export": false,
      "unlimited_history": false,
      "analytics": false,
      "priority_support": false,
      "custom_alerts": false,
      "api_access": false
    },
    "enterprise": {
      "team_collaboration": false,
      "sso": false,
      "admin_dashboard": false,
      "dedicated_support": false
    }
  }
}
```

### Free User Accessing Premium Feature

**Request** (with JWT):
```json
POST /api/v1/chat
Authorization: Bearer eyJhbGc...
{
  "content": "I want to export my conversation history",
  "language": "en"
}
```

**Response** (requires_registration=false but feature locked):
```json
{
  "message_id": "uuid",
  "content": "🔒 **Export Conversations** is available on Premium and Enterprise plans.\n\nUpgrade to Premium ($19/month) to unlock:\n✨ Export conversations (JSON/CSV)\n✨ Unlimited conversation history\n✨ Advanced analytics dashboards\n✨ Priority support\n✨ Custom alerts\n✨ API access\n\n[Upgrade to Premium](https://anvil.fi/upgrade)",
  "intent": "export_request",
  "enrichment": null,
  "requires_registration": false,
  "user_type": "authenticated",
  "features_available": {
    "basic": { "sentiment": true, "trading_signals": true, "price_prediction": true },
    "premium": { "patterns": true, "portfolio": true, "risk_signals": true },
    "advanced": { "export": false, "unlimited_history": false, "analytics": false, ... },
    "enterprise": { ... }
  }
}
```

---

## Rate Limiting by Tier

| User Type | Tier | Messages/Hour | Window | Enforcement |
|-----------|------|---------------|--------|-------------|
| Guest | - | 20 | 3600s | IP-based |
| Authenticated | Free | 1,000 | 3600s | User ID-based |
| Authenticated | Premium | 10,000 | 3600s | User ID-based |
| Authenticated | Enterprise | 10,000 | 3600s | User ID-based |

**Implementation**:
```python
# Context-based rate limiting
def get_rate_limit(self) -> tuple[int, int]:
    """Get rate limit configuration.

    Returns:
        Tuple of (messages_limit, window_seconds)
    """
    if isinstance(self, GuestContext):
        return (20, 3600)
    elif isinstance(self, AuthenticatedContext):
        if self.subscription_tier in ("premium", "enterprise"):
            return (10000, 3600)
        return (1000, 3600)
```

---

## Data Retention by Tier

| User Type | Tier | Retention | Storage Tables | Cleanup |
|-----------|------|-----------|----------------|---------|
| Guest | - | 90 days | `guest_*` | Automated (daily job) |
| Authenticated | Free | Permanent | `chat_*` | Never deleted |
| Authenticated | Premium | Permanent | `chat_*` | Never deleted |
| Authenticated | Enterprise | Permanent | `chat_*` | Never deleted |

**Implementation**:
```python
def get_retention_days(self) -> Optional[int]:
    """Get data retention period in days.

    Returns:
        Number of days to retain data, or None for permanent retention
    """
    if isinstance(self, GuestContext):
        return 90  # 90-day retention for guests
    elif isinstance(self, AuthenticatedContext):
        return None  # Permanent retention for authenticated users
```

---

## Feature Comparison for Marketing

### Guest vs Authenticated (Free)

**What Guest Users Get**:
- ✅ 3 basic Hunter AI tools (sentiment, signals, predictions)
- ✅ 20 messages/hour
- ✅ 90-day conversation history
- ✅ Multi-language support (en, es, pt, zh)
- ✅ Real-time crypto data

**What Free Authenticated Users Get** (in addition):
- ✨ **3 premium Hunter AI tools** (patterns, portfolio, risk analysis)
- ✨ **1,000 messages/hour** (50x increase)
- ✨ **Permanent conversation history** (no expiration)
- ✨ Cross-device sync
- ✨ Personalized dashboard

**Upgrade Path**: Guest → Free Auth → Premium → Enterprise

---

## Testing Feature Flags

### Unit Tests

```python
# tests/unit/domain/chat/test_feature_flags.py

def test_guest_context_features():
    """Guest users only get basic features."""
    context = GuestContext(ip_address="1.2.3.4")
    flags = FeatureFlags.from_context(context)

    # Basic features enabled
    assert flags.hunter_sentiment is True
    assert flags.hunter_trading_signals is True
    assert flags.hunter_price_prediction is True

    # Premium features disabled
    assert flags.hunter_patterns is False
    assert flags.hunter_portfolio is False
    assert flags.hunter_risk_signals is False

    # Advanced features disabled
    assert flags.export_conversations is False
    assert flags.api_access is False


def test_authenticated_free_features():
    """Free authenticated users get basic + premium hunter features."""
    context = AuthenticatedContext(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        email="user@example.com",
        subscription_tier="free",
    )
    flags = FeatureFlags.from_context(context)

    # Basic features enabled
    assert flags.hunter_sentiment is True

    # Premium hunter features enabled
    assert flags.hunter_patterns is True
    assert flags.hunter_portfolio is True
    assert flags.hunter_risk_signals is True

    # Advanced features disabled
    assert flags.export_conversations is False
    assert flags.api_access is False


def test_authenticated_premium_features():
    """Premium users get basic + premium + advanced features."""
    context = AuthenticatedContext(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        email="user@example.com",
        subscription_tier="premium",
    )
    flags = FeatureFlags.from_context(context)

    # All basic and premium features
    assert flags.hunter_sentiment is True
    assert flags.hunter_patterns is True

    # Advanced features enabled
    assert flags.export_conversations is True
    assert flags.unlimited_history is True
    assert flags.advanced_analytics is True
    assert flags.api_access is True

    # Enterprise features disabled
    assert flags.team_collaboration is False
    assert flags.sso_integration is False


def test_authenticated_enterprise_features():
    """Enterprise users get all features."""
    context = AuthenticatedContext(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        email="user@example.com",
        subscription_tier="enterprise",
    )
    flags = FeatureFlags.from_context(context)

    # All features enabled
    assert flags.hunter_sentiment is True
    assert flags.hunter_patterns is True
    assert flags.export_conversations is True
    assert flags.team_collaboration is True
    assert flags.sso_integration is True
    assert flags.admin_dashboard is True


def test_intent_allowed():
    """Test intent validation."""
    guest_flags = FeatureFlags.from_context(
        GuestContext(ip_address="1.2.3.4")
    )

    # Basic intents allowed for guests
    assert guest_flags.is_intent_allowed("hunter_sentiment") is True
    assert guest_flags.is_intent_allowed("hunter_trading_signals") is True

    # Premium intents not allowed for guests
    assert guest_flags.is_intent_allowed("hunter_patterns") is False
    assert guest_flags.is_intent_allowed("hunter_portfolio") is False
```

### Integration Tests

```python
# tests/integration/application/chat/test_feature_gating.py

async def test_guest_blocked_from_premium_feature(client, guest_ip):
    """Guest users receive upgrade prompt for premium features."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "content": "Optimize my portfolio with 50% BTC, 30% ETH, 20% SOL",
            "language": "en",
        },
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "hunter_portfolio"
    assert data["requires_registration"] is True
    assert data["user_type"] == "guest"
    assert "premium feature" in data["content"].lower()
    assert "sign up" in data["content"].lower()


async def test_authenticated_free_access_premium_feature(client, auth_token):
    """Free authenticated users can access premium hunter features."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "content": "Show me BTC chart patterns",
            "language": "en",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "hunter_patterns"
    assert data["requires_registration"] is False
    assert data["user_type"] == "authenticated"
    assert data["features_available"]["premium"]["patterns"] is True
```

---

## Future Feature Additions

### How to Add New Features

1. **Add feature flag to FeatureFlags dataclass**:
   ```python
   # src/app/domain/chat/value_objects.py
   hunter_new_feature: bool = False
   ```

2. **Update from_context() factory method**:
   ```python
   # Decide which tier gets the feature
   if context.subscription_tier == "premium":
       return cls(
           hunter_new_feature=True,  # Add here
           ...
       )
   ```

3. **Update is_intent_allowed() if it's a Hunter AI intent**:
   ```python
   intent_feature_map = {
       "hunter_new_feature": self.hunter_new_feature,
       ...
   }
   ```

4. **Update to_dict() for API responses**:
   ```python
   return {
       "premium": {
           "new_feature": self.hunter_new_feature,
           ...
       }
   }
   ```

5. **Add tests**:
   - Unit tests for feature flag creation
   - Integration tests for feature gating
   - E2E tests for upgrade prompts

### Planned Features (Roadmap)

**Q2 2026**:
- `hunter_whale_tracking`: Track large wallet movements
- `hunter_social_sentiment`: Social media sentiment aggregation
- `custom_watchlists`: Personalized token watchlists

**Q3 2026**:
- `hunter_dex_analytics`: DEX trading analysis
- `hunter_nft_signals`: NFT market signals
- `multichain_support`: Support for Solana, Polygon, etc.

**Q4 2026**:
- `hunter_derivatives`: Futures and options analysis
- `ml_personalization`: ML-based response personalization
- `voice_interface`: Voice chat support

---

## Summary

**Total Features**: 20 (4 basic, 6 premium, 6 advanced, 4 enterprise)

**User Types**: 4 (guest, free auth, premium auth, enterprise auth)

**Implementation Status**:
- ✅ Feature flag dataclass complete
- ✅ Context abstraction complete
- ✅ Factory method complete
- ✅ Intent validation complete
- ⏳ API endpoint integration (Day 2-3)
- ⏳ Testing suite (Day 2-3)

**Design Principles**:
- **Immutability**: FeatureFlags is frozen dataclass (thread-safe)
- **Factory pattern**: from_context() creates appropriate flags
- **Open/Closed**: Easy to add features without modifying existing code
- **Single Responsibility**: Each feature is independent boolean flag
- **DRY**: Single source of truth for feature availability

---

**Last Updated**: 2026-01-12
**Next Review**: After Day 2-3 implementation completion

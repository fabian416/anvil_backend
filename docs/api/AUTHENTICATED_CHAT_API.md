# Authenticated Chat API Documentation

## Overview

The Authenticated Chat API provides unified chat functionality for both guest and authenticated users through a single endpoint. The system intelligently routes requests based on authentication state and manages feature access through subscription tiers.

**Base URL**: `/api/v1/chat`

**Authentication**: Optional JWT Bearer token (graceful degradation to guest mode)

**Rate Limits**:
- **Guest Users**: 800 messages per hour per IP address
- **Free Tier**: 1,000 messages per hour
- **Premium Tier**: 10,000 messages per hour
- **Enterprise Tier**: 10,000 messages per hour

---

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoint Reference](#endpoint-reference)
3. [Request/Response Models](#requestresponse-models)
4. [Feature Access Matrix](#feature-access-matrix)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)
7. [WebSocket Subscriptions](#websocket-subscriptions)

---

## Authentication

### JWT Bearer Token (Authenticated Users)

```http
POST /api/v1/chat
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "content": "What's the current price of BTC?",
  "language": "en"
}
```

**Token Claims**:
```json
{
  "sub": "123",  // Legacy user ID (INTEGER)
  "email": "user@example.com",
  "exp": 1735689600,
  "iat": 1735686000
}
```

### Guest Mode (No Authentication)

```http
POST /api/v1/chat
Content-Type: application/json
X-Forwarded-For: 203.0.113.42  // IP address for rate limiting

{
  "content": "What's the current price of BTC?",
  "language": "en"
}
```

**IP-Based Tracking**: Guest sessions are tracked by IP address for rate limiting and conversation continuity.

### Graceful Degradation

Invalid or expired JWT tokens result in **graceful degradation to guest mode** (not 401 Unauthorized):

```http
POST /api/v1/chat
Authorization: Bearer invalid_token_xyz123
Content-Type: application/json

{
  "content": "Show me swap rates",
  "language": "en"
}
```

**Response** (200 OK):
```json
{
  "content": "I can show you current swap rates! To access advanced features like historical patterns and alerts, please sign up for a free account.",
  "requires_registration": true,
  "user_type": "guest",
  "conversation_id": null
}
```

---

## Endpoint Reference

### Universal Chat Endpoint

**POST** `/api/v1/chat`

Unified endpoint for both guest and authenticated users. Automatically routes to appropriate handler based on authentication state.

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Optional | `Bearer {jwt_token}` for authenticated requests |
| `Content-Type` | Required | `application/json` |
| `Accept-Language` | Optional | Preferred language (overrides `language` in body) |

#### Request Body

```json
{
  "content": "string (required, max 2000 chars)",
  "language": "string (optional, default: 'en', enum: ['en', 'es', 'pt', 'zh'])",
  "conversation_id": "string (optional, UUID for authenticated users only)",
  "metadata": {
    "source": "string (optional, e.g., 'web', 'mobile')",
    "user_agent": "string (optional)"
  }
}
```

#### Response (200 OK)

**Authenticated User Response**:
```json
{
  "content": "Based on current data, BTC is trading at $42,350 with a 24h volume of $28.5B...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "user_type": "authenticated",
  "subscription_tier": "premium",
  "requires_registration": false,
  "enrichment": {
    "intent": "crypto_price_query",
    "entities": [
      {"type": "cryptocurrency", "value": "BTC", "confidence": 0.98}
    ],
    "suggested_actions": [
      {"action": "set_price_alert", "params": {"symbol": "BTC"}},
      {"action": "view_chart", "params": {"symbol": "BTC", "interval": "1h"}}
    ],
    "data_sources": ["coingecko", "binance_api"],
    "hunter_confidence": 0.95
  },
  "feature_flags": {
    "hunter_patterns": true,
    "price_alerts": true,
    "advanced_charts": true,
    "export_conversations": true,
    "api_access": true,
    "priority_support": true
  },
  "metadata": {
    "processing_time_ms": 245,
    "model_version": "hunter-ai-v2.1",
    "tokens_used": 850
  }
}
```

**Guest User Response**:
```json
{
  "content": "Based on current data, BTC is trading at $42,350. Sign up for a free account to access historical patterns and price alerts!",
  "conversation_id": null,
  "message_id": null,
  "user_type": "guest",
  "subscription_tier": "guest",
  "requires_registration": false,
  "enrichment": {
    "intent": "crypto_price_query",
    "entities": [
      {"type": "cryptocurrency", "value": "BTC", "confidence": 0.98}
    ],
    "suggested_actions": [
      {"action": "sign_up", "params": {"reason": "price_alerts"}}
    ],
    "data_sources": ["coingecko"],
    "hunter_confidence": 0.92
  },
  "feature_flags": {
    "hunter_patterns": false,
    "price_alerts": false,
    "advanced_charts": false,
    "export_conversations": false,
    "api_access": false,
    "priority_support": false
  },
  "metadata": {
    "rate_limit_remaining": 18,
    "rate_limit_reset_at": "2026-01-12T03:05:40Z"
  }
}
```

**Premium Feature Blocked (Free Tier)**:
```json
{
  "content": "I can show you basic swap rates! To access advanced features like multi-step swaps and best route optimization, upgrade to Premium.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_type": "authenticated",
  "subscription_tier": "free",
  "requires_registration": false,
  "pending_action": {
    "action_type": "upgrade_required",
    "feature": "multi_step_swaps",
    "required_tier": "premium",
    "upgrade_url": "/api/v1/billing/upgrade"
  },
  "feature_flags": {
    "hunter_patterns": true,
    "price_alerts": false,
    "advanced_charts": false,
    "export_conversations": false,
    "api_access": false,
    "priority_support": false
  }
}
```

#### Response Status Codes

| Status | Description |
|--------|-------------|
| `200 OK` | Request successful (both guest and authenticated) |
| `400 Bad Request` | Invalid request body or parameters |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Server error (check logs) |

**Note**: Authentication errors (401) are NOT returned. Invalid tokens gracefully degrade to guest mode.

---

## Request/Response Models

### ChatRequest

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ChatRequest(BaseModel):
    """Universal chat request model."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User message content"
    )

    language: str = Field(
        default="en",
        pattern="^(en|es|pt|zh)$",
        description="Response language (en, es, pt, zh)"
    )

    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Conversation ID for authenticated users (auto-created if null)"
    )

    metadata: Optional[dict] = Field(
        default=None,
        description="Optional client metadata (source, user_agent, etc.)"
    )
```

### ChatResponse

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID

class EnrichmentData(BaseModel):
    """Hunter AI enrichment data."""

    intent: Optional[str] = Field(
        default=None,
        description="Detected user intent (e.g., 'crypto_price_query', 'swap_request')"
    )

    entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted entities (cryptocurrencies, amounts, addresses)"
    )

    suggested_actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Suggested actions with parameters"
    )

    data_sources: List[str] = Field(
        default_factory=list,
        description="Data sources used (coingecko, binance_api, etc.)"
    )

    hunter_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Hunter AI confidence score (0.0 - 1.0)"
    )

class FeatureFlagsResponse(BaseModel):
    """Feature access flags based on subscription tier."""

    hunter_patterns: bool = Field(description="Access to Hunter AI pattern analysis")
    price_alerts: bool = Field(description="Access to price alert creation")
    advanced_charts: bool = Field(description="Access to advanced charting tools")
    export_conversations: bool = Field(description="Export conversation history")
    api_access: bool = Field(description="Programmatic API access")
    priority_support: bool = Field(description="Priority customer support")

class PendingAction(BaseModel):
    """Action pending user decision (e.g., upgrade, registration)."""

    action_type: str = Field(
        description="Type of action (upgrade_required, registration_required)"
    )

    feature: str = Field(
        description="Feature requiring action"
    )

    required_tier: Optional[str] = Field(
        default=None,
        description="Required subscription tier (for upgrades)"
    )

    upgrade_url: Optional[str] = Field(
        default=None,
        description="URL for upgrade flow"
    )

class ChatResponse(BaseModel):
    """Universal chat response model."""

    content: str = Field(
        description="Assistant response content"
    )

    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Conversation ID (null for guests)"
    )

    message_id: Optional[UUID] = Field(
        default=None,
        description="Message ID (null for guests)"
    )

    user_type: str = Field(
        description="User type: 'guest' or 'authenticated'"
    )

    subscription_tier: str = Field(
        description="Subscription tier: 'guest', 'free', 'premium', 'enterprise'"
    )

    requires_registration: bool = Field(
        default=False,
        description="True if feature requires user registration"
    )

    enrichment: Optional[EnrichmentData] = Field(
        default=None,
        description="Hunter AI enrichment data"
    )

    feature_flags: FeatureFlagsResponse = Field(
        description="Available features for current tier"
    )

    pending_action: Optional[PendingAction] = Field(
        default=None,
        description="Action pending user decision"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata (processing time, rate limits, etc.)"
    )
```

---

## Feature Access Matrix

### Subscription Tiers

| Feature | Guest | Free | Premium | Enterprise |
|---------|-------|------|---------|------------|
| **Basic Chat** | ✅ | ✅ | ✅ | ✅ |
| **Hunter AI Patterns** | ❌ | ✅ | ✅ | ✅ |
| **Price Alerts** | ❌ | ❌ | ✅ | ✅ |
| **Advanced Charts** | ❌ | ❌ | ✅ | ✅ |
| **Multi-Step Swaps** | ❌ | ❌ | ✅ | ✅ |
| **Export Conversations** | ❌ | ❌ | ❌ | ✅ |
| **API Access** | ❌ | ❌ | ❌ | ✅ |
| **Priority Support** | ❌ | ❌ | ❌ | ✅ |
| **Message Limit** | 800/hour | 1,000/hour | 10,000/hour | 10,000/hour |
| **Conversation History** | ❌ | ✅ (30 days) | ✅ (1 year) | ✅ (Forever) |

### Feature Flags Implementation

```python
from app.domain.chat.value_objects.context import FeatureFlags, AuthenticatedContext

# Authenticated user with premium tier
context = AuthenticatedContext(
    user_id=123,
    email="user@example.com",
    subscription_tier="premium"
)

features = FeatureFlags.from_context(context)
# FeatureFlags(
#     hunter_patterns=True,
#     price_alerts=True,
#     advanced_charts=True,
#     export_conversations=False,  # Enterprise only
#     api_access=False,  # Enterprise only
#     priority_support=False  # Enterprise only
# )

# Check specific feature
if features.price_alerts:
    # Create price alert
    pass
else:
    # Show upgrade prompt
    pass
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again in 45 minutes.",
    "context": {
      "limit": 20,
      "reset_at": "2026-01-12T03:45:00Z",
      "current_tier": "guest"
    },
    "suggestion": "Sign up for a free account to get 100 messages per day!"
  }
}
```

### Common Error Codes

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `INVALID_REQUEST` | 400 | Malformed request body | Check request format |
| `CONTENT_TOO_LONG` | 400 | Message exceeds 2000 chars | Shorten message |
| `INVALID_LANGUAGE` | 400 | Unsupported language code | Use en, es, pt, or zh |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait for reset or upgrade |
| `CONVERSATION_NOT_FOUND` | 404 | Invalid conversation_id | Check conversation ID |
| `UNAUTHORIZED_ACCESS` | 403 | Accessing other user's conversation | Use your own conversations |
| `INTERNAL_ERROR` | 500 | Server error | Retry or contact support |

### Error Handling Best Practices

```python
import httpx
from typing import Optional

async def send_chat_message(
    content: str,
    jwt_token: Optional[str] = None,
    language: str = "en"
) -> dict:
    """Send chat message with proper error handling."""

    headers = {"Content-Type": "application/json"}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"

    payload = {
        "content": content,
        "language": language
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.anvil.com/api/v1/chat",
                headers=headers,
                json=payload,
                timeout=30.0
            )

            # Check for rate limiting
            if response.status_code == 429:
                error_data = response.json()
                reset_at = error_data["detail"]["context"]["reset_at"]
                raise RateLimitError(f"Rate limit exceeded. Reset at {reset_at}")

            # Check for other errors
            response.raise_for_status()

            data = response.json()

            # Handle upgrade prompts
            if data.get("pending_action"):
                action = data["pending_action"]
                if action["action_type"] == "upgrade_required":
                    print(f"Feature '{action['feature']}' requires {action['required_tier']} tier")
                    print(f"Upgrade at: {action['upgrade_url']}")

            return data

        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code}")
            print(f"Details: {e.response.json()}")
            raise

        except httpx.TimeoutException:
            print("Request timeout - retry with exponential backoff")
            raise
```

---

## Code Examples

### Example 1: Guest Chat (No Authentication)

```python
import httpx

async def guest_chat_example():
    """Simple guest chat without authentication."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={"Content-Type": "application/json"},
            json={
                "content": "What's the current price of Ethereum?",
                "language": "en"
            }
        )

        data = response.json()

        print(f"Assistant: {data['content']}")
        print(f"User Type: {data['user_type']}")
        print(f"Rate Limit Remaining: {data['metadata']['rate_limit_remaining']}")

        # Check if feature requires registration
        if data.get("requires_registration"):
            print("⚠️  Some features require registration!")

# Output:
# Assistant: Ethereum is currently trading at $2,245.80...
# User Type: guest
# Rate Limit Remaining: 19
```

### Example 2: Authenticated Chat (Free Tier)

```python
import httpx

async def authenticated_chat_example(jwt_token: str):
    """Authenticated chat with JWT token."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            json={
                "content": "Show me the Hunter AI pattern for BTC",
                "language": "en"
            }
        )

        data = response.json()

        print(f"Assistant: {data['content']}")
        print(f"Subscription: {data['subscription_tier']}")
        print(f"Conversation ID: {data['conversation_id']}")

        # Access Hunter AI enrichment
        if data.get("enrichment"):
            enrichment = data["enrichment"]
            print(f"\nIntent: {enrichment['intent']}")
            print(f"Confidence: {enrichment['hunter_confidence']:.2%}")
            print(f"Data Sources: {', '.join(enrichment['data_sources'])}")

            # Execute suggested actions
            for action in enrichment.get("suggested_actions", []):
                print(f"Suggested: {action['action']} with {action['params']}")

# Output:
# Assistant: Based on Hunter AI analysis, BTC shows a bullish pattern...
# Subscription: free
# Conversation ID: 550e8400-e29b-41d4-a716-446655440000
#
# Intent: pattern_analysis
# Confidence: 95.00%
# Data Sources: coingecko, binance_api, hunter_ai
# Suggested: set_price_alert with {'symbol': 'BTC', 'threshold': 43000}
```

### Example 3: Premium Feature (Multi-Step Swap)

```python
import httpx

async def premium_swap_example(jwt_token: str):
    """Request premium feature (multi-step swap)."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            json={
                "content": "Find best route to swap 1000 USDC to WBTC with intermediate steps",
                "language": "en"
            }
        )

        data = response.json()

        # Check if feature is blocked by tier
        if data.get("pending_action"):
            action = data["pending_action"]
            if action["action_type"] == "upgrade_required":
                print(f"❌ Feature '{action['feature']}' requires {action['required_tier']} tier")
                print(f"Upgrade at: {action['upgrade_url']}")
                return

        # Feature available - process swap route
        enrichment = data["enrichment"]
        swap_route = enrichment.get("swap_route", {})

        print(f"Optimal Route:")
        for step in swap_route.get("steps", []):
            print(f"  {step['from']} → {step['to']} via {step['dex']}")

        print(f"\nTotal Gas Cost: {swap_route.get('total_gas_cost')}")
        print(f"Expected Output: {swap_route.get('expected_output')}")

# Output (Free Tier):
# ❌ Feature 'multi_step_swaps' requires premium tier
# Upgrade at: /api/v1/billing/upgrade

# Output (Premium Tier):
# Optimal Route:
#   USDC → WETH via Uniswap V3
#   WETH → WBTC via Sushiswap
#
# Total Gas Cost: 0.0045 ETH
# Expected Output: 0.0234 WBTC
```

### Example 4: Conversation Continuity

```python
import httpx
from uuid import UUID

async def conversation_continuity_example(jwt_token: str):
    """Maintain conversation context across messages."""

    async with httpx.AsyncClient() as client:
        # First message - creates new conversation
        response1 = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            json={
                "content": "What's the price of BTC?",
                "language": "en"
            }
        )

        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        print(f"Message 1: {data1['content']}")
        print(f"Conversation ID: {conversation_id}")

        # Follow-up message - uses same conversation
        response2 = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            json={
                "content": "What about ETH?",  # Context maintained
                "language": "en",
                "conversation_id": str(conversation_id)
            }
        )

        data2 = response2.json()
        print(f"\nMessage 2: {data2['content']}")
        print(f"Same Conversation: {data2['conversation_id'] == conversation_id}")

# Output:
# Message 1: BTC is currently trading at $42,350...
# Conversation ID: 550e8400-e29b-41d4-a716-446655440000
#
# Message 2: Ethereum (ETH) is trading at $2,245.80...
# Same Conversation: True
```

### Example 5: Multi-Language Support

```python
import httpx

async def multilingual_chat_example():
    """Chat in different languages."""

    async with httpx.AsyncClient() as client:
        # Spanish
        response_es = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={"Content-Type": "application/json"},
            json={
                "content": "¿Cuál es el precio de Bitcoin?",
                "language": "es"
            }
        )

        print(f"ES: {response_es.json()['content']}")

        # Portuguese
        response_pt = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={"Content-Type": "application/json"},
            json={
                "content": "Qual é o preço do Bitcoin?",
                "language": "pt"
            }
        )

        print(f"PT: {response_pt.json()['content']}")

        # Chinese
        response_zh = await client.post(
            "https://api.anvil.com/api/v1/chat",
            headers={"Content-Type": "application/json"},
            json={
                "content": "比特币的价格是多少？",
                "language": "zh"
            }
        )

        print(f"ZH: {response_zh.json()['content']}")

# Output:
# ES: Bitcoin se cotiza actualmente a $42,350...
# PT: Bitcoin está sendo negociado a $42.350...
# ZH: 比特币目前的交易价格为 $42,350...
```

### Example 6: Rate Limit Handling with Retry

```python
import httpx
import asyncio
from datetime import datetime

async def rate_limit_retry_example():
    """Handle rate limits with exponential backoff."""

    async with httpx.AsyncClient() as client:
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = await client.post(
                    "https://api.anvil.com/api/v1/chat",
                    headers={"Content-Type": "application/json"},
                    json={
                        "content": "What's BTC price?",
                        "language": "en"
                    }
                )

                if response.status_code == 429:
                    error_data = response.json()
                    reset_at_str = error_data["detail"]["context"]["reset_at"]
                    reset_at = datetime.fromisoformat(reset_at_str.replace("Z", "+00:00"))

                    wait_seconds = (reset_at - datetime.now()).total_seconds()

                    print(f"⚠️  Rate limited. Waiting {wait_seconds:.0f} seconds...")
                    await asyncio.sleep(wait_seconds + 1)

                    retry_count += 1
                    continue

                response.raise_for_status()
                data = response.json()

                print(f"✅ Success: {data['content']}")
                break

            except httpx.HTTPStatusError as e:
                print(f"❌ Error: {e.response.status_code}")
                break

        if retry_count >= max_retries:
            print("❌ Max retries exceeded")
```

---

## WebSocket Subscriptions

### Real-Time Conversation Updates

For enterprise clients requiring real-time updates on conversation changes (e.g., multi-user collaboration):

```python
import websockets
import json

async def subscribe_to_conversation(jwt_token: str, conversation_id: str):
    """Subscribe to real-time conversation updates."""

    uri = f"wss://api.anvil.com/ws/conversations/{conversation_id}"

    async with websockets.connect(
        uri,
        extra_headers={"Authorization": f"Bearer {jwt_token}"}
    ) as websocket:
        # Send subscription message
        await websocket.send(json.dumps({
            "action": "subscribe",
            "conversation_id": conversation_id
        }))

        # Receive updates
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "new_message":
                print(f"New message from {data['role']}: {data['content']}")

            elif data["type"] == "conversation_archived":
                print(f"Conversation archived at {data['archived_at']}")
                break

            elif data["type"] == "title_updated":
                print(f"Conversation title changed to: {data['new_title']}")

# Note: WebSocket subscriptions are Enterprise tier only
```

---

## OpenAPI Specification

Full OpenAPI 3.1 specification available at:

```
GET /openapi.json
```

Interactive documentation:

```
GET /docs
```

---

## Best Practices

### 1. **Always Include Language Parameter**

Even if using English, explicitly specify language for consistent responses:

```json
{
  "content": "What's BTC price?",
  "language": "en"  // Always specify
}
```

### 2. **Handle Graceful Degradation**

Never assume authentication will work. Always handle guest fallback:

```python
response = await send_message(content, jwt_token)

if response["user_type"] == "guest":
    # Authentication failed - show login prompt
    show_login_ui()
else:
    # Authenticated - full features available
    show_full_ui()
```

### 3. **Respect Rate Limits**

Check rate limit headers and implement exponential backoff:

```python
if "rate_limit_remaining" in response["metadata"]:
    remaining = response["metadata"]["rate_limit_remaining"]
    if remaining < 5:
        show_warning(f"Only {remaining} messages remaining this hour")
```

### 4. **Use Conversation Continuity**

For authenticated users, always pass `conversation_id` for context:

```python
# First message
response1 = await send_message("What's BTC price?")
conv_id = response1["conversation_id"]

# Follow-up (context maintained)
response2 = await send_message(
    "What about yesterday?",
    conversation_id=conv_id
)
```

### 5. **Check Feature Flags Before UI**

Only show UI elements if user has access:

```python
response = await send_message("Hello")
features = response["feature_flags"]

if features["price_alerts"]:
    show_alert_button()  # Show button
else:
    show_upgrade_prompt()  # Suggest upgrade
```

---

## Migration from Legacy API

If migrating from the deprecated `/api/v1/user/chat/*` endpoints:

### Legacy (Deprecated)
```http
POST /api/v1/user/chat/conversations/550e8400-e29b-41d4-a716-446655440000/messages
```

### New (Universal)
```http
POST /api/v1/chat
{
  "content": "message",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

See **Migration Guide** for complete transition instructions.

---

## Support

**Documentation**: https://docs.anvil.com/chat-api
**API Status**: https://status.anvil.com
**Support Email**: api-support@anvilcrypto.com

**Rate Limit Increases**: Contact sales@anvilcrypto.com for enterprise tier.

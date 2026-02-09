# Chat Mode Endpoint — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Intent**: CHAT / PROFILE  
**Related**: Conversations Router (#1002), Chat Agent (#1212), Authenticated Supervisor

---

## Overview

Endpoint to retrieve and configure the user's Anvil chat mode. Chat modes define the **personality, depth, and vocabulary** of Anvil's AI responses. This enables a personalized experience ranging from casual newcomers to advanced DeFi power users.

---

## Endpoint

```
GET /api/v1/chat/mode
```

**Auth**: Required (JWT Bearer Token)  
**Rate Limit**: Standard authenticated (200/hr)  
**Purpose**: Returns the user's current chat mode with all available profiles.

---

## Chat Mode Profiles

### 1. Casual 🌱

| Attribute | Value |
|-----------|-------|
| `slug` | `casual` |
| `name` | Casual |
| `icon` | `seedling` |
| `description` | Friendly and simple. Explains everything in plain language. Perfect for beginners exploring DeFi for the first time. |
| `tone` | Warm, encouraging, avoids jargon |
| `detail_level` | Low — summarizes key info, hides technical details |
| `vocabulary` | Plain English, analogies to traditional finance |
| `example_response` | "You swapped $100 of USDC and got some PURR tokens! 🎉 Your balance is now $1,234." |
| `target_user` | New to crypto, exploring casually |

### 2. Power User ⚡

| Attribute | Value |
|-----------|-------|
| `slug` | `power_user` |
| `name` | Power User |
| `icon` | `zap` |
| `description` | Balanced and informative. Shows market data, fees, and key metrics without overwhelming detail. Ideal for experienced users who want efficiency. |
| `tone` | Direct, data-driven, efficient |
| `detail_level` | Medium — includes fees, slippage, gas, APYs |
| `vocabulary` | Standard DeFi terminology (APY, TVL, slippage, gas) |
| `example_response` | "Swapped 100 USDC → 4,264 PURR on HL Spot. Fee: 0.02% ($0.02). Gas: $0.00. PURR is +12.5% 24h." |
| `target_user` | Active DeFi user, trades regularly |

### 3. Degen 🔥

| Attribute | Value |
|-----------|-------|
| `slug` | `degen` |
| `name` | Degen |
| `icon` | `flame` |
| `description` | Full degen mode. Raw data, advanced metrics, meme energy. Shows everything — spread, depth, order book stats, PnL tracking. No hand-holding. |
| `tone` | Fast, raw, meme-aware, no filter |
| `detail_level` | High — spread bps, order book depth, funding rates, PnL |
| `vocabulary` | Native crypto slang (ape, rekt, rug, moon, gwei, chad) |
| `example_response` | "Filled 100 USDC → 4,264 PURR. Spread 3.2bps, depth $45k. PURR pumping +12.5%. You're up $84.56 (+56%) on this bag. LFG 🚀" |
| `target_user` | Advanced trader, degen culture enthusiast |

---

## Response Schema

```python
class ChatModeProfile(BaseModel):
    slug: str                           # "casual" | "power_user" | "degen"
    name: str                           # "Casual" | "Power User" | "Degen"
    icon: str                           # "seedling" | "zap" | "flame"
    description: str                    # Human-readable description
    is_active: bool                     # True if this is user's current mode
    is_default: bool                    # True for "casual" (default for new users)

class ChatModeResponse(BaseModel):
    current_mode: str                   # "casual" | "power_user" | "degen"
    modes: list[ChatModeProfile]        # All 3 profiles
```

### Example Response

```json
{
  "current_mode": "power_user",
  "modes": [
    {
      "slug": "casual",
      "name": "Casual",
      "icon": "seedling",
      "description": "Friendly and simple. Explains everything in plain language. Perfect for beginners exploring DeFi for the first time.",
      "is_active": false,
      "is_default": true
    },
    {
      "slug": "power_user",
      "name": "Power User",
      "icon": "zap",
      "description": "Balanced and informative. Shows market data, fees, and key metrics without overwhelming detail.",
      "is_active": true,
      "is_default": false
    },
    {
      "slug": "degen",
      "name": "Degen",
      "icon": "flame",
      "description": "Full degen mode. Raw data, advanced metrics, meme energy. No hand-holding.",
      "is_active": false,
      "is_default": false
    }
  ]
}
```

---

## Set Chat Mode

```
PUT /api/v1/chat/mode
```

**Auth**: Required (JWT Bearer Token)

### Request Body

```python
class SetChatModeRequest(BaseModel):
    mode: Literal["casual", "power_user", "degen"]
```

### Response

```json
{
  "current_mode": "degen",
  "message": "Chat mode updated to Degen 🔥"
}
```

---

## Integration with Agent System

The selected chat mode is injected into the **system prompt** of all agents via the Supervisor:

```python
# In authenticated_supervisor.py
async def _get_mode_instruction(self, user_id: UUID) -> str:
    mode = await self._user_prefs_repo.get_chat_mode(user_id)
    
    MODE_INSTRUCTIONS = {
        "casual": """
            Respond in friendly, simple language. Avoid jargon.
            Use analogies. Add encouraging emojis. Explain concepts
            as if the user is new to crypto. Keep responses concise.
        """,
        "power_user": """
            Include key metrics: fees, gas, APY, 24h change.
            Use standard DeFi terminology. Be efficient and direct.
            Show data inline. Skip basic explanations.
        """,
        "degen": """
            Full raw data: spread bps, depth, funding, PnL.
            Use crypto slang freely. Fast-paced, no hand-holding.
            Include order book stats when relevant. Meme energy welcome.
        """,
    }
    return MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["casual"])
```

---

## Database

```sql
-- Stored in chat_users table
ALTER TABLE chat_users ADD COLUMN chat_mode VARCHAR(20) DEFAULT 'casual';

-- Valid values: 'casual', 'power_user', 'degen'
-- Default: 'casual' for new users
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/chat/chat_mode.py` | GET + PUT endpoints |
| **Application** | `queries/chat/get_chat_mode.py` | Query handler |
| **Application** | `commands/chat/set_chat_mode.py` | Command handler |
| **Domain** | `entities/chat_mode.py` | ChatModeProfile value object |
| **Domain** | `ports/user/user_preferences_repository.py` | Port for mode storage |
| **Infrastructure** | `adapters/user/user_preferences_adapter.py` | PostgreSQL adapter |

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 400 | INVALID_MODE | Mode not in ["casual", "power_user", "degen"] |

---

## Performance Targets

| Endpoint | Target |
|----------|--------|
| GET /chat/mode | < 100ms (single DB query) |
| PUT /chat/mode | < 200ms (single DB update) |

---

## Open Items

- [ ] Onboarding: should new users pick a mode during signup?
- [ ] Mode-specific UI themes (colors, icons per mode)?
- [ ] Per-conversation mode override vs global setting?
- [ ] Analytics: track mode usage distribution

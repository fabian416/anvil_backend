# Activities Endpoint — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Intent**: ACTIVITY  
**Related**: Transaction History Agent (#1151), Balance Dashboard (#1706), Send Endpoint (#1699)

---

## Overview

REST API for the Activity feed — the user's transaction history shown in the shortcut/tab UI. Two endpoints: a **list** (paginated feed) and a **detail** view (full transaction breakdown). This replaces the agent-based activity rendering with structured API responses suitable for native UI cards.

---

## Endpoint 1: Activity Feed (List)

```
GET /api/v1/activities?page=1&limit=20&action={action}&chain_id={chain_id}
```

**Auth**: Required (JWT Bearer Token)  
**Rate Limit**: Standard authenticated (200/hr)  
**Purpose**: Paginated list of user's recent transactions for the Activity tab.

### Query Parameters

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| page | int | No | 1 | Page number (1-indexed) |
| limit | int | No | 20 | Items per page (max 50) |
| action | str | No | null | Filter: "swap", "buy", "send", "receive", "lend", "borrow", "cashout" |
| chain_id | int | No | null | Filter by chain |
| status | str | No | null | Filter: "completed", "pending", "failed" |

### Response Schema

```python
class ActivityItem(BaseModel):
    id: str                              # UUID
    tx_hash: str | None                  # "0xabc123..." (null if pending/internal)

    # Token In (source)
    token_in: str                        # "USDC"
    token_in_icon: str | None            # Icon URL
    amount_in: str                       # "1500.00"
    amount_in_usd: str                   # "1,500.00"

    # Token Out (destination)
    token_out: str                       # "ETH"
    token_out_icon: str | None           # Icon URL
    amount_out: str                      # "0.75"
    amount_out_usd: str                  # "1,500.00"

    # Transaction metadata
    action: str                          # "swap" | "buy" | "send" | "receive" | "lend" | "borrow" | "cashout"
    summary: str                         # "Swapped 1,500 USDC for 0.75 ETH on Uniswap"
    status: str                          # "completed" | "pending" | "failed"
    chain_id: int                        # 8453
    chain_name: str                      # "Base"
    timestamp: str                       # ISO 8601: "2026-02-08T14:30:00Z"
    time_ago: str                        # "2h ago" | "Yesterday" | "Feb 7"

class ActivityListResponse(BaseModel):
    activities: list[ActivityItem]
    total_count: int                     # Total matching activities
    page: int                            # Current page
    limit: int                           # Items per page
    has_next: bool                       # More pages available
    filters_applied: dict                # Active filters for UI state
```

### Example Response

```json
{
  "activities": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "tx_hash": "0xabc123def456789...",
      "token_in": "USDC",
      "token_in_icon": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
      "amount_in": "1500.00",
      "amount_in_usd": "1,500.00",
      "token_out": "ETH",
      "token_out_icon": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
      "amount_out": "0.75",
      "amount_out_usd": "1,500.00",
      "action": "swap",
      "summary": "Swapped 1,500 USDC for 0.75 ETH",
      "status": "completed",
      "chain_id": 8453,
      "chain_name": "Base",
      "timestamp": "2026-02-08T14:30:00Z",
      "time_ago": "2h ago"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "tx_hash": "0xdef789abc123456...",
      "token_in": "USDC",
      "token_in_icon": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
      "amount_in": "2000.00",
      "amount_in_usd": "2,000.00",
      "token_out": "USDC (Morpho)",
      "token_out_icon": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
      "amount_out": "2000.00",
      "amount_out_usd": "2,000.00",
      "action": "lend",
      "summary": "Deposited 2,000 USDC to Morpho at 6.5% APY",
      "status": "completed",
      "chain_id": 8453,
      "chain_name": "Base",
      "timestamp": "2026-02-07T10:15:00Z",
      "time_ago": "Yesterday"
    },
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "tx_hash": null,
      "token_in": "USD",
      "token_in_icon": null,
      "amount_in": "500.00",
      "amount_in_usd": "500.00",
      "token_out": "USDC",
      "token_out_icon": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
      "amount_out": "500.00",
      "amount_out_usd": "500.00",
      "action": "buy",
      "summary": "Bought 500 USDC with Apple Pay",
      "status": "completed",
      "chain_id": 8453,
      "chain_name": "Base",
      "timestamp": "2026-02-06T08:00:00Z",
      "time_ago": "Feb 6"
    }
  ],
  "total_count": 47,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "filters_applied": {}
}
```

---

## Endpoint 2: Activity Detail (Single Transaction)

```
GET /api/v1/activities/{tx_hash}
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: Full transaction detail view when user taps an activity card.

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| tx_hash | str | Transaction hash or internal activity ID |

### Response Schema

```python
class ActivityDetailResponse(BaseModel):
    id: str                              # Internal UUID

    # Token In (full detail)
    token_in_symbol: str                 # "USDC"
    token_in_name: str                   # "USD Coin"
    token_in_address: str                # "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    token_in_icon: str | None
    amount_in: str                       # "1500.00"
    amount_in_usd: str                   # "1,500.00"

    # Token Out (full detail)
    token_out_symbol: str                # "ETH"
    token_out_name: str                  # "Ethereum"
    token_out_address: str               # "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    token_out_icon: str | None
    amount_out: str                      # "0.75"
    amount_out_usd: str                  # "1,500.00"

    # Transaction details
    action: str                          # "swap" | "buy" | "send" | "receive" | "lend" | "borrow" | "cashout"
    summary: str                         # "Swapped 1,500 USDC for 0.75 ETH on Uniswap"
    tx_hash: str | None                  # "0xabc123..."
    chain_id: int                        # 1
    chain_name: str                      # "Ethereum"
    status: str                          # "completed" | "pending" | "failed"
    timestamp: str                       # "2026-02-08T14:30:00Z"

    # Execution details
    gas_used: str | None                 # "65000"
    gas_cost_usd: str | None             # "0.01"
    fee_usd: str | None                  # "0.30" (trading fee)
    provider: str | None                 # "Hyperliquid Spot" | "Morpho" | "MoonPay"
    explorer_url: str | None             # "https://basescan.org/tx/0xabc..."

    # P&L (for swaps — if user still holds the output token)
    pnl_usd: str | None                  # "+45.00" | null if sold
    pnl_pct: float | None               # 3.0 | null
```

### Example Response

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",

  "token_in_symbol": "USDC",
  "token_in_name": "USD Coin",
  "token_in_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "token_in_icon": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
  "amount_in": "1500.00",
  "amount_in_usd": "1,500.00",

  "token_out_symbol": "ETH",
  "token_out_name": "Ethereum",
  "token_out_address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
  "token_out_icon": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
  "amount_out": "0.75",
  "amount_out_usd": "1,500.00",

  "action": "swap",
  "summary": "Swapped 1,500 USDC for 0.75 ETH on Uniswap",
  "tx_hash": "0xabc123def456789012345678901234567890abcdef",
  "chain_id": 1,
  "chain_name": "Ethereum",
  "status": "completed",
  "timestamp": "2026-02-08T14:30:00Z",

  "gas_used": "152345",
  "gas_cost_usd": "3.45",
  "fee_usd": "0.30",
  "provider": "Uniswap V3",
  "explorer_url": "https://etherscan.io/tx/0xabc123def456789012345678901234567890abcdef",

  "pnl_usd": "+45.00",
  "pnl_pct": 3.0
}
```

---

## Action Types

| Action | token_in | token_out | Description |
|--------|----------|-----------|-------------|
| `swap` | Source token | Destination token | Token exchange (HL Spot, Uniswap) |
| `buy` | Fiat (USD, EUR) | Crypto (USDC) | Fiat on-ramp via MoonPay |
| `send` | Sent token | — (same token) | Transfer to external address |
| `receive` | — | Received token | Transfer from external address |
| `lend` | Token | Token (Protocol) | Deposit to lending protocol |
| `borrow` | — | Borrowed token | Borrow from lending protocol |
| `cashout` | USDC | Fiat (USD) | Off-ramp to bank |

---

## Data Sources

```
┌──────────────────────────────────────────────────┐
│              GET /api/v1/activities               │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ transactions  │  │ CoinGecko    │              │
│  │ table (DB)    │  │ (icons, USD) │              │
│  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                      │
│         ▼                  ▼                      │
│  ┌──────────────────────────────────────────┐    │
│  │     Activity Aggregation Service         │    │
│  │                                          │    │
│  │  1. Query transactions table             │    │
│  │  2. Resolve token icons (CoinGecko)      │    │
│  │  3. Calculate time_ago                   │    │
│  │  4. Build explorer URLs                  │    │
│  │  5. Calculate PnL for swaps (optional)   │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### Database Table

```sql
-- Primary source: transactions table
SELECT 
    id, tx_hash, type AS action, status,
    from_token AS token_in, from_amount AS amount_in,
    to_token AS token_out, to_amount AS amount_out,
    chain_id, gas_used, gas_price,
    created_at AS timestamp
FROM transactions
WHERE user_id = :user_id
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/activity/activities.py` | GET list + GET detail endpoints |
| **Application** | `queries/activity/get_activities.py` | List query handler (CQRS) |
| **Application** | `queries/activity/get_activity_detail.py` | Detail query handler |
| **Domain** | `entities/activity.py` | ActivityItem, ActivityDetail value objects |
| **Domain** | `ports/transaction/transaction_repository.py` | Existing port (reused) |
| **Infrastructure** | `adapters/transaction/transaction_adapter.py` | PostgreSQL adapter (reused) |
| **Infrastructure** | `adapters/external/coingecko_client.py` | Token icons + USD prices (reused) |

---

## Caching Strategy

| Data | Cache TTL | Source |
|------|-----------|--------|
| Transaction list | No cache (fresh DB) | transactions table |
| Token icons | 24h | CoinGecko / static CDN |
| USD prices (for PnL) | 30s | CoinGecko API |
| Explorer URLs | Static | Chain registry |

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 404 | TX_NOT_FOUND | Transaction hash not found for this user |
| 400 | INVALID_FILTER | Invalid action or status filter |

---

## Performance Targets

| Endpoint | Target |
|----------|--------|
| GET /activities (list) | < 500ms (indexed DB query) |
| GET /activities/{tx} (detail) | < 300ms (single row + joins) |

---

## Agent Integration

The Activity shortcut button triggers the activity screen, NOT the chat agent:

```
Shortcut: "Activity" → Opens /activities screen → GET /api/v1/activities
```

If user types "show my activity" in chat → existing `transaction_history` agent responds with natural language summary, but the structured data comes from this API.

---

## Open Items

- [ ] Pagination strategy: offset vs cursor-based?
- [ ] Real-time updates: WebSocket push for pending → completed transitions?
- [ ] Export to CSV for tax reporting (future)
- [ ] Group activities by date for UI sections
- [ ] Activity notifications (push when tx completes)

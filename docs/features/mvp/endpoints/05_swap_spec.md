# Swap Flow Endpoints — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-08  
**Status**: Specification  
**Intent**: SWAP  
**Recallium**: Memory #1702, #1703, #1704, #1705  
**Related**: Send Endpoint (#1698), Swap System Spec (#1166), Swap Workflow (#1679), Hyperliquid Client (#1690)

---

## Overview

Three-endpoint swap UI flow for the frontend swap screen:

1. **`GET /swap/defaults`** → Initial swap screen state: pre-selects FROM (highest balance token) and TO (most traded Hyperliquid Spot token)
2. **`GET /swap/from-tokens`** → User taps FROM field: shows their holdings with amounts, USD values, per chain
3. **`GET /swap/to-tokens`** → User taps TO field: shows all available Hyperliquid Spot tokens with 24h volume and price

All swaps route through **Hyperliquid Spot** (50+ meme tokens paired with USDC). Major tokens (ETH, BTC, SOL) are NOT supported on HL Spot.

---

## Endpoint 1: Swap Defaults (Initial Screen)

```
GET /api/v1/swap/defaults
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: Pre-populate the swap screen with smart defaults.

### Default Selection Logic

| User State | FROM | TO |
|-----------|------|-----|
| Has balance | Highest USD balance token | Most traded HL Spot token by 24h volume (excluding FROM) |
| $0 balance | USDC (empty) + "Buy crypto" CTA | Top meme token |
| Only USDC | USDC | Top meme (e.g., PURR) |
| Has meme tokens | Highest meme token | USDC (sell flow) |

### Response Schema

```python
class SwapDefaultsResponse(BaseModel):
    from_token: SwapFromToken         # Pre-selected FROM
    to_token: SwapToToken             # Pre-selected TO
    has_balance: bool                 # False if $0 portfolio
    cta: str | None = None            # "Buy crypto to start swapping" if no balance
    fee_info: FeeInfo

class FeeInfo(BaseModel):
    trading_fee_pct: str              # "0.02"
    gas_fee: str                      # "0.00" (Hyperliquid = zero gas)
    provider: str                     # "Hyperliquid Spot"
```

---

## Endpoint 2: FROM Token Picker (User Holdings)

```
GET /api/v1/swap/from-tokens?chain_id={chain_id}
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: User taps FROM field — shows actual holdings with balances.

### Response

```python
class SwapFromTokensResponse(BaseModel):
    total_balance_usd: str
    tokens: list[SwapFromToken]       # Sorted by amount_usd DESC
    chains: list[ChainSummary]

class SwapFromToken(BaseModel):
    symbol: str                       # "USDC"
    name: str                         # "USD Coin"
    address: str
    decimals: int
    chain_id: int
    chain_name: str
    icon_url: str | None
    amount: str                       # "500.00"
    amount_usd: str                   # "500.00"
    price_usd: str                    # "1.00"
    change_24h: float | None
    is_native: bool
    is_swappable: bool                # True if token exists on HL Spot or is USDC
    swap_note: str | None             # "Major tokens not available on Hyperliquid Spot"
```

**`is_swappable` Logic**: Token is swappable if it exists on Hyperliquid Spot. Non-swappable tokens show `swap_note` and are dimmed in UI but still visible.

Reuses `RPCBalanceProvider` + `CoinGeckoClient` from send endpoint.

---

## Endpoint 3: TO Token Picker (Hyperliquid Spot Tokens)

```
GET /api/v1/swap/to-tokens?search={query}&sort_by=volume_24h
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: User taps TO field — shows all available Hyperliquid Spot tokens.

### Query Parameters

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| search | str | No | null | Filter by symbol or name (fuzzy) |
| sort_by | str | No | "volume_24h" | Sort: "volume_24h", "change_24h", "price", "name" |
| sort_order | str | No | "desc" | "asc" or "desc" |

### Response

```python
class SwapToTokensResponse(BaseModel):
    tokens: list[SpotToken]           # All HL Spot tokens
    total_count: int                  # 50+
    quote_currency: str               # Always "USDC"

class SpotToken(BaseModel):
    symbol: str                       # "PURR"
    name: str                         # "Purr"
    icon_url: str | None
    price_usd: str                    # "0.023456"
    change_24h: float | None          # 12.5
    volume_24h_usd: str               # "2,345,678.00"
    market_cap_usd: str | None
    spread_bps: float | None          # 3.2
    is_trending: bool                 # True for top 5 by volume
    rank: int                         # 1 = highest volume
```

---

## UI Flow Diagram

```
[Initial Load] → GET /swap/defaults
                      ↓
    ┌─────────────────────────────────┐
    │  FROM [USDC ▼]    500.00       │ ← tap → GET /swap/from-tokens
    │  Amount: [____]    ~$500       │
    │            ⇅                   │
    │  TO   [PURR ▼]                 │ ← tap → GET /swap/to-tokens
    │  Fee: 0.02% · Gas: $0.00      │
    │  [      Get Quote       ]      │ ← triggers swap_workflow agent
    └─────────────────────────────────┘
```

**Get Quote** → `POST /conversations/{id}/messages` ("swap 100 USDC to PURR") → existing `swap_workflow` agent handles quote + confirm + execute.

---

## Shared Components with Send Endpoint

```
Send Endpoint (#1698)          Swap Endpoints
    │                              │
    ├── RPCBalanceProvider ◄───────┤  (reused for from-tokens)
    ├── CoinGeckoClient    ◄───────┤  (reused for prices)
    ├── ChainRegistry      ◄───────┤  (reused for chain info)
    └── WalletRepository   ◄───────┘  (reused for user address)
```

---

## Caching Strategy

| Data | Cache TTL | Source |
|------|-----------|--------|
| User balances | No cache (fresh RPC) | On-chain RPC |
| CoinGecko prices | 30s | CoinGecko API |
| HL Spot token list | 5 min | `get_spot_meta()` |
| HL Spot order books | 5s | `get_spot_order_book()` |
| HL 24h volume | 30s | Hyperliquid API |

---

## Performance Targets

| Endpoint | Target |
|----------|--------|
| GET /swap/defaults | < 2s (balances + HL meta parallel) |
| GET /swap/from-tokens | < 2s (same as send/tokens) |
| GET /swap/to-tokens | < 500ms (cached HL meta) |

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 404 | NO_WALLET | User has no Privy wallet |
| 503 | HL_UNAVAILABLE | Hyperliquid API down |
| 400 | UNSUPPORTED_CHAIN | Invalid chain_id filter |

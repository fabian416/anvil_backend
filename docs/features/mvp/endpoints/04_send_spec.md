# Wallet Send Endpoint — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-08  
**Status**: Specification  
**Intent**: TRANSFER / SEND  
**Recallium**: Memory #1699, #1700, #1701  
**Related**: Receive Endpoint (#1695), Portfolio Agent (#1565), Execution Shortcuts (#1325)

---

## Overview

Three-phase send flow:
1. **Phase 1** — `GET /api/v1/wallet/send/tokens` → List user's available tokens with balances (token picker)
2. **Phase 2** — `POST /api/v1/wallet/send/preview` → Preview transfer with gas estimation (5 min expiry)
3. **Phase 3** — `POST /api/v1/wallet/send/execute` → Execute signed transfer via Privy

Data sources: On-Chain RPC (balances, always fresh) → CoinGecko (USD prices, 30s cache) → Gas estimation via RPC.

---

## Endpoint 1: List Sendable Tokens

```
GET /api/v1/wallet/send/tokens?chain_id={chain_id}&min_balance_usd=0.01
```

**Auth**: Required (JWT Bearer Token)  
**Rate Limit**: Standard authenticated (200/hr)

### Query Parameters

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| chain_id | int | No | null | Filter by chain |
| min_balance_usd | float | No | 0.01 | Hide dust tokens |

### Response Schema

```python
class SendableToken(BaseModel):
    symbol: str                          # "USDC"
    name: str                            # "USD Coin"
    address: str                         # Contract address or "native"
    decimals: int                        # 6
    chain_id: int                        # 8453
    chain_name: str                      # "Base"
    icon_url: str | None
    amount: str                          # "500.00"
    amount_usd: str                      # "500.00"
    price_usd: str                       # "1.00"
    change_24h: float | None             # 0.01
    is_native: bool                      # False

class SendTokensResponse(BaseModel):
    total_balance_usd: str               # "1234.56"
    tokens: list[SendableToken]          # Sorted by amount_usd DESC
    chains: list[ChainSummary]
    updated_at: str
```

### Example Response

```json
{
  "total_balance_usd": "1234.56",
  "tokens": [
    {
      "symbol": "USDC",
      "name": "USD Coin",
      "address": "0x833589f...",
      "chain_id": 8453,
      "chain_name": "Base",
      "amount": "500.00",
      "amount_usd": "500.00",
      "price_usd": "1.00",
      "change_24h": 0.01,
      "icon_url": "https://...",
      "is_native": false
    }
  ]
}
```

---

## Endpoint 2: Preview Send

```
POST /api/v1/wallet/send/preview
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: Gas estimation + validation + warnings (5 min expiry)

### Request Body

```python
class SendPreviewRequest(BaseModel):
    token_address: str                    # Contract address or "native"
    chain_id: int
    amount: str                           # "100"
    to_address: str                       # Destination wallet
```

### Response

```json
{
  "token_symbol": "USDC",
  "amount": "100",
  "amount_usd": "100.00",
  "gas_cost_usd": "0.01",
  "has_sufficient_balance": true,
  "has_sufficient_gas": true,
  "remaining_balance": "400.00",
  "remaining_balance_usd": "400.00",
  "warnings": [],
  "preview_id": "prev_abc123",
  "expires_at": "2026-02-08T14:35:00Z"
}
```

---

## Endpoint 3: Execute Send

```
POST /api/v1/wallet/send/execute
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: Execute the transfer. Frontend uses Privy SDK to sign.

### Request

```python
class SendExecuteRequest(BaseModel):
    preview_id: str                       # From preview response
```

### Response

```python
class SendExecuteResponse(BaseModel):
    action_type: Literal["transfer"] = "transfer"
    provider: str                         # "privy"
    chain: str                            # "base"
    chain_id: int                         # 8453
    token_address: str
    token_symbol: str                     # "USDC"
    amount: str                           # "100.00"
    to_address: str
    tx_data: dict                         # Raw transaction data for Privy signing
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/wallet/send.py` | 3 endpoints (tokens, preview, execute) |
| **Application** | `queries/wallet/get_sendable_tokens.py` | Token list query handler |
| **Application** | `commands/wallet/preview_send.py` | Preview command handler |
| **Application** | `commands/wallet/execute_send.py` | Execute command handler |
| **Domain** | `entities/send_preview.py` | SendPreview value object |
| **Domain** | `ports/wallet/balance_provider.py` | Reused for balances |
| **Infrastructure** | `adapters/wallet/rpc_balance_provider.py` | On-chain RPC |
| **Infrastructure** | `adapters/external/coingecko_client.py` | USD prices |

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 404 | NO_WALLET | User has no Privy wallet |
| 400 | INSUFFICIENT_BALANCE | Can't afford amount + gas |
| 400 | INVALID_ADDRESS | Bad recipient address format |
| 410 | PREVIEW_EXPIRED | Preview older than 5 minutes |

---

## Performance Targets

| Endpoint | Target |
|----------|--------|
| GET /send/tokens | < 2s (RPC + prices parallel) |
| POST /send/preview | < 2s (gas estimation) |
| POST /send/execute | < 500ms (return tx_data) |

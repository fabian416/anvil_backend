# Cash Out Endpoint — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Intent**: CASHOUT / OFF-RAMP  
**Related**: Balance Dashboard (#1706), Buy Workflow (#1150), Send Endpoint (#1699)

---

## Overview

Cash Out enables users to convert crypto (USDC) to fiat and withdraw to a bank account or card. The flow uses the user's USDC balance (from the Balance Dashboard) as the available amount and integrates with **MoonPay Off-Ramp** via Privy SDK for the actual conversion and payout.

---

## Endpoint 1: Cash Out Availability

```
GET /api/v1/wallet/cashout
```

**Auth**: Required (JWT Bearer Token)  
**Rate Limit**: Standard authenticated (200/hr)  
**Purpose**: Returns the user's available USDC balance for cash out plus provider configuration.

### Response Schema

```python
class CashOutAvailabilityResponse(BaseModel):
    # Available balance
    available_usdc: str                       # "1,500.00" — user's total USDC across chains
    available_usd: str                        # "1,500.00" — equivalent USD value
    has_sufficient_balance: bool              # True if USDC > minimum ($10)

    # Provider info
    provider: str                             # "moonpay"
    provider_display: str                     # "MoonPay"
    supported_fiat: list[FiatCurrency]        # Supported payout currencies
    supported_methods: list[PayoutMethod]     # Bank, card, etc.

    # Limits
    min_amount_usd: str                       # "10.00"
    max_amount_usd: str                       # "10,000.00" (daily limit)
    daily_remaining_usd: str                  # "10,000.00" (remaining today)

    # Fees
    estimated_fee_pct: float                  # 1.5 (percentage)
    estimated_fee_usd: str                    # "22.50" (based on full balance)
    net_payout_usd: str                       # "1,477.50" (after fees)

    # USDC breakdown by chain (for user info)
    usdc_by_chain: list[ChainBalance]

    # CTA
    cta: str | None                           # "You need USDC to cash out" if $0

class FiatCurrency(BaseModel):
    code: str                                 # "USD", "EUR", "GBP"
    name: str                                 # "US Dollar"
    symbol: str                               # "$"
    is_default: bool                          # True for USD

class PayoutMethod(BaseModel):
    method: str                               # "bank_transfer" | "card" | "apple_pay"
    name: str                                 # "Bank Transfer" | "Debit Card"
    icon: str                                 # "bank" | "card" | "apple"
    is_available: bool                        # True if user has this method set up
    estimated_arrival: str                    # "1-3 business days" | "Instant"

class ChainBalance(BaseModel):
    chain_id: int                             # 8453
    chain_name: str                           # "Base"
    usdc_amount: str                          # "1,500.00"
    usdc_address: str                         # Contract address
```

### Example Response

```json
{
  "available_usdc": "1,500.00",
  "available_usd": "1,500.00",
  "has_sufficient_balance": true,

  "provider": "moonpay",
  "provider_display": "MoonPay",

  "supported_fiat": [
    {"code": "USD", "name": "US Dollar", "symbol": "$", "is_default": true},
    {"code": "EUR", "name": "Euro", "symbol": "€", "is_default": false},
    {"code": "GBP", "name": "British Pound", "symbol": "£", "is_default": false}
  ],

  "supported_methods": [
    {
      "method": "bank_transfer",
      "name": "Bank Transfer",
      "icon": "bank",
      "is_available": true,
      "estimated_arrival": "1-3 business days"
    },
    {
      "method": "card",
      "name": "Debit Card",
      "icon": "card",
      "is_available": false,
      "estimated_arrival": "Instant"
    }
  ],

  "min_amount_usd": "10.00",
  "max_amount_usd": "10,000.00",
  "daily_remaining_usd": "10,000.00",

  "estimated_fee_pct": 1.5,
  "estimated_fee_usd": "22.50",
  "net_payout_usd": "1,477.50",

  "usdc_by_chain": [
    {"chain_id": 8453, "chain_name": "Base", "usdc_amount": "1,500.00", "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}
  ],

  "cta": null
}
```

### Empty Balance Response

```json
{
  "available_usdc": "0.00",
  "available_usd": "0.00",
  "has_sufficient_balance": false,
  "cta": "You need USDC to cash out. Buy crypto or swap tokens to USDC first.",
  "estimated_fee_pct": 1.5,
  "estimated_fee_usd": "0.00",
  "net_payout_usd": "0.00"
}
```

---

## Endpoint 2: Cash Out Preview

```
POST /api/v1/wallet/cashout/preview
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: Calculate exact fees and payout for a specific amount.

### Request Body

```python
class CashOutPreviewRequest(BaseModel):
    amount_usdc: str                          # "500.00"
    fiat_currency: str = "USD"                # "USD", "EUR", "GBP"
    payout_method: str = "bank_transfer"      # "bank_transfer" | "card"
```

### Response

```python
class CashOutPreviewResponse(BaseModel):
    amount_usdc: str                          # "500.00"
    amount_fiat: str                          # "500.00" (pre-fee in fiat)
    fiat_currency: str                        # "USD"
    exchange_rate: str                        # "1.00" (USDC/USD)

    # Fees breakdown
    provider_fee_usd: str                     # "7.50" (MoonPay fee)
    network_fee_usd: str                      # "0.01" (gas for USDC transfer)
    total_fee_usd: str                        # "7.51"

    # Payout
    net_payout: str                           # "492.49"
    payout_method: str                        # "bank_transfer"
    estimated_arrival: str                    # "1-3 business days"

    # Validation
    has_sufficient_balance: bool
    warnings: list[str]                       # ["Large withdrawal: $5,000+"]
    preview_id: str                           # UUID
    expires_at: str                           # 5 min expiry
```

---

## Endpoint 3: Execute Cash Out

```
POST /api/v1/wallet/cashout/execute
```

**Auth**: Required (JWT Bearer Token)  
**Purpose**: Initiate the off-ramp via MoonPay. Returns Privy widget URL or execute_data.

### Request

```python
class CashOutExecuteRequest(BaseModel):
    preview_id: str                           # From preview response
```

### Response

```python
class CashOutExecuteResponse(BaseModel):
    action_type: str                          # "cashout"
    provider: str                             # "moonpay"
    widget_url: str | None                    # MoonPay off-ramp widget URL
    execute_data: dict | None                 # For Privy SDK integration
    status: str                               # "initiated" | "pending_kyc"
    message: str                              # "Cash out initiated. Check your email for confirmation."
```

---

## Flow Diagram

```
┌──────────────────────────────────────────────┐
│  CASH OUT SCREEN                             │
│                                              │
│  Available USDC: $1,500.00                   │ ← GET /cashout
│                                              │
│  Amount: [____$500____]   [MAX]              │
│                                              │
│  To: 🏦 Bank Transfer (1-3 days)            │
│  Currency: USD ($)                           │
│                                              │
│  ┌──────────────────────────────────┐        │
│  │  You send:     500.00 USDC      │        │
│  │  Fee:          -$7.51           │        │
│  │  You receive:  $492.49          │        │ ← POST /cashout/preview
│  └──────────────────────────────────┘        │
│                                              │
│  [        Cash Out $492.49        ]          │ ← POST /cashout/execute
│                                              │
└──────────────────────────────────────────────┘
```

---

## Data Sources

| Data | Source | Cache |
|------|--------|-------|
| USDC balance | On-chain RPC (reused from balance) | No cache |
| USDC price | CoinGecko (always ~$1.00) | 30s |
| MoonPay fees | MoonPay API | 5 min |
| Exchange rates | MoonPay API | 5 min |
| Daily limits | Anvil DB (user limits tracking) | No cache |

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/wallet/cashout.py` | 3 endpoints (availability, preview, execute) |
| **Application** | `queries/wallet/get_cashout_availability.py` | Availability query handler |
| **Application** | `commands/wallet/preview_cashout.py` | Preview command handler |
| **Application** | `commands/wallet/execute_cashout.py` | Execute command handler |
| **Domain** | `entities/cashout.py` | CashOut value objects |
| **Domain** | `ports/offramp/offramp_provider.py` | Port for MoonPay off-ramp |
| **Infrastructure** | `adapters/offramp/moonpay_offramp_adapter.py` | MoonPay API adapter |
| **Infrastructure** | `adapters/wallet/rpc_balance_provider.py` | Reused for USDC balance |

---

## KYC Requirements

MoonPay off-ramp requires KYC verification. If user hasn't completed KYC:

```json
{
  "status": "pending_kyc",
  "message": "Identity verification required for cash out. This is a one-time process.",
  "kyc_url": "https://moonpay.com/kyc/..."
}
```

---

## Non-USDC Assets

If user wants to cash out non-USDC assets, the flow is:
1. **Swap** to USDC first (via swap endpoints)
2. Then **Cash Out** USDC

The UI should suggest: "Swap your ETH to USDC first, then cash out."

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 404 | NO_WALLET | User has no Privy wallet |
| 400 | INSUFFICIENT_BALANCE | USDC balance below minimum |
| 400 | BELOW_MINIMUM | Amount < $10 |
| 400 | ABOVE_DAILY_LIMIT | Exceeds daily withdrawal limit |
| 410 | PREVIEW_EXPIRED | Preview older than 5 minutes |
| 503 | PROVIDER_UNAVAILABLE | MoonPay API unavailable |

---

## Performance Targets

| Endpoint | Target |
|----------|--------|
| GET /cashout | < 2s (balance + MoonPay rates parallel) |
| POST /cashout/preview | < 3s (MoonPay quote) |
| POST /cashout/execute | < 2s (initiate off-ramp) |

---

## Open Items

- [ ] MoonPay off-ramp API integration (widget vs API mode)
- [ ] KYC flow integration with Privy
- [ ] Daily/monthly limits configuration (per user tier?)
- [ ] Transaction tracking: webhook for payout completion
- [ ] Support for non-USDC off-ramp (auto-swap + cashout?)
- [ ] Compliance: OFAC screening before off-ramp

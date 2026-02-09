# Balance Dashboard Endpoint — Backend Specification

**Version**: 1.0  
**Date**: 2026-02-08  
**Status**: Specification  
**Intent**: BALANCE / PORTFOLIO  
**Recallium**: Memory #1706, #1707, #1708, #1709, #1710  
**Related**: Send Endpoint (#1698), Swap Flow (#1702), Portfolio Agent (#1565), Lending Schema (#1405)

---

## Overview

Consolidated balance endpoint that aggregates the user's complete financial picture across **wallet holdings**, **lending positions**, and **swap/transaction history** into a single dashboard response. Calculates overall **P&L (profit/loss)** based on cost basis tracking.

---

## Endpoint

```
GET /api/v1/wallet/balance?period={period}
```

**Auth**: Required (JWT Bearer Token)  
**Rate Limit**: Standard authenticated (200/hr)

### Query Parameters

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| period | str | No | "all" | P&L period: "24h", "7d", "30d", "90d", "all" |
| chain_id | int | No | null | Filter by chain |

---

## Response Schema

```python
class BalanceDashboardResponse(BaseModel):
    # Consolidated Totals
    total_balance_usd: str                    # "5,234.56" (wallet + lending)
    total_pnl_usd: str                        # "+534.56" or "-120.00"
    total_pnl_pct: float                      # 12.3 or -2.1
    pnl_period: str                           # "all", "24h", "7d", "30d", "90d"
    is_profitable: bool                       # True if pnl > 0

    # Breakdown
    wallet: WalletBalance                     # On-chain holdings
    lending: LendingBalance                   # Active lending positions
    activity_summary: ActivitySummary         # Swap/tx history stats

    # Portfolio Allocation (for chart)
    allocation: list[AllocationItem]          # % breakdown with colors

    # Recommendations
    recommendations: list[Recommendation]     # Max 3 smart CTAs

    updated_at: str                           # ISO timestamp
```

### Key Sub-Models

```python
class WalletBalance(BaseModel):
    total_usd: str
    pnl_usd: str
    pnl_pct: float
    holdings: list[TokenHolding]              # Each with cost_basis, pnl, acquired_via

class LendingBalance(BaseModel):
    total_supplied_usd: str
    total_debt_usd: str
    net_value_usd: str
    total_yield_earned_usd: str
    positions: list[LendingPosition]          # Each with APY, health_factor, yield

class ActivitySummary(BaseModel):
    total_transactions: int
    total_volume_usd: str
    swaps: ActivityBreakdown
    transfers: ActivityBreakdown
    best_swap: SwapPnL | None
    worst_swap: SwapPnL | None

class AllocationItem(BaseModel):
    category: str                             # "stablecoins" | "meme_tokens" | "lending" | "native"
    label: str
    amount_usd: str
    pct: float
    color: str                                # Hex color for chart
    tokens: list[str]

class Recommendation(BaseModel):
    action: str                               # "buy" | "swap" | "earn_yield" | "receive"
    icon: str
    label: str
    summary: str
    cta: str                                  # Pre-filled chat message
    intent_trigger: str
```

---

## P&L Calculation

```
Total P&L = Wallet Holdings P&L + Lending Yield Earned

Wallet: For each token → (current_amount × current_price) - cost_basis (FIFO)
Lending: For each position → current_supply_value - net_deposited_amount
Total Balance: wallet.total_usd + lending.net_value_usd
```

### Cost Basis Sources
1. **BUY** transactions → fiat amount spent = cost basis
2. **SWAP** transactions → USD value of from_token at swap time
3. **RECEIVE/TRANSFER_IN** → USD value at time of receipt

---

## Recommendation Logic

| User State | Recommendations |
|-----------|----------------|
| $0 portfolio | Buy Crypto, Receive Crypto |
| Has idle stablecoins > $100 | Earn Yield (deposit to Morpho ~6.5% APY) |
| Has balance | Swap Tokens, Send Crypto |

---

## Data Sources & Parallel Fetching

```python
async def get_balance_dashboard(self, query):
    # All fetches run in parallel
    wallet, lending, transactions, prices = await asyncio.gather(
        self._balance_provider.get_all_balances(address, chains),
        self._lending_provider.get_positions(user_id),
        self._tx_repo.get_user_transactions(user_id, period=query.period),
        self._price_provider.get_all_tracked_prices(),
    )
    # Sequential calculations
    pnl = self._pnl_calculator.calculate(wallet, transactions, prices)
    yield_data = self._yield_calculator.calculate(lending)
    allocation = self._build_allocation(wallet, lending)
    recommendations = self._build_recommendations(wallet, lending)
```

---

## Caching & Performance

| Data | Cache | Source | Target |
|------|-------|--------|--------|
| On-chain balances | No cache | RPC | < 1s |
| CoinGecko prices | 30s TTL | CoinGecko | < 200ms |
| Lending positions | 60s TTL | lending_* tables | < 300ms |
| Cost basis calc | 5 min TTL | Computed | < 200ms |
| **Total endpoint** | — | — | **< 3s** |

---

## Error Responses

| Status | Error Code | Scenario |
|--------|-----------|----------|
| 401 | UNAUTHORIZED | No JWT / expired token |
| 404 | NO_WALLET | User has no Privy wallet |
| 400 | INVALID_PERIOD | Invalid period parameter |

# Balance Overview — Chat Agent Response Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Context**: Chat Response Enrichment (conversations/messages)  
**Intent**: `BALANCE_CHECK` / `PORTFOLIO_OVERVIEW`  
**Related**: Balance Dashboard Endpoint (GET /api/v1/wallet/balance), Hunter AI, CoinGecko API

---

## Overview

When a user asks about their portfolio balance (e.g., "what's my balance?", "show my portfolio", "how's my wallet doing?"), the unified chat router produces a structured `balance_overview` enrichment block with per-token holdings, P&L calculations, per-token `chart_url`, and AI-driven portfolio recommendations. This is the **chat response** equivalent of the wallet balance dashboard, optimized for the conversational interface.

---

## Intent Detection

### Trigger Phrases

```
"what's my balance?"
"show my portfolio"
"how much do I have?"
"my wallet"
"portfolio overview"
"how's my crypto doing?"
"am I up or down?"
"show me my holdings"
"what's my net worth?"
```

### Intent Classification

```python
intent = "BALANCE_CHECK"  # or "PORTFOLIO_OVERVIEW" 
confidence >= 0.90
entities = []  # No specific token — full portfolio
```

---

## Response Schema

### Enrichment Block: `balance_overview`

```python
class BalanceOverviewEnrichment(BaseModel):
    type: Literal["balance_overview"] = "balance_overview"
    total_usd: float                        # 12500.00
    total_change_24h_usd: float             # +650.00
    total_change_24h_pct: float             # +5.2
    total_change_period: str                # "24h"
    portfolio_chart_url: str                # Aggregate portfolio value chart
    holdings: list[HoldingItem]             # Per-token breakdown
    lending_positions: list[LendingItem] | None  # Active lending/staking
    total_lending_usd: float | None         # Total in lending protocols
    recommendations: list[Recommendation]   # AI-driven suggestions
    last_updated: str                       # ISO8601

class HoldingItem(BaseModel):
    symbol: str                             # "BTC"
    name: str                               # "Bitcoin"
    address: str                            # Contract address or "native"
    chain_id: int                           # 1, 8453, 998
    chain_name: str                         # "Ethereum", "Base"
    icon_url: str | None                    # Token icon
    amount_token: str                       # "0.05" (human readable)
    amount_usd: float                       # 4875.00
    price_usd: str                          # "97,500.00"
    pnl_usd: float                          # +535.00
    pnl_pct: float                          # +12.3
    acquired_via: str                       # "buy" | "swap" | "receive" | "airdrop"
    chart_url: str                          # Per-token chart URL
    allocation_pct: float                   # 39.0 — % of total portfolio

class LendingItem(BaseModel):
    protocol: str                           # "Morpho", "Aave"
    token: str                              # "USDC"
    supplied_amount: str                    # "1,000.00"
    supplied_usd: float                     # 1000.00
    current_apy: float                      # 4.5
    earned_usd: float                       # +12.50
    chain_name: str                         # "Base"

class Recommendation(BaseModel):
    action: str                             # "buy" | "swap" | "earn_yield" | "diversify" | "take_profit" | "rebalance"
    priority: int                           # 1 = highest
    summary: str                            # Human-readable suggestion
    reasoning: str                          # Why this recommendation
    cta: str                                # Actionable prompt for user
    potential_impact: str | None            # "$45/month in yield" or "+5% diversification"
```

### Example Response

```json
{
  "user_message": { "content": "what's my balance?", ... },
  "agent_message": {
    "content": "Your portfolio is worth $12,500 — up 5.2% ($650) in the last 24 hours! 🚀\n\nYour biggest winner is BTC at +12.3%. You have $5,000 in idle USDC that could be earning ~4.5% APY on Morpho. Want me to set that up?",
    "agent_type": "balance_handler"
  },
  "routing": {
    "intent": "BALANCE_CHECK",
    "confidence": 0.95,
    "handler": "balance_overview_handler"
  },
  "enrichment": {
    "balance_overview": {
      "type": "balance_overview",
      "total_usd": 12500.00,
      "total_change_24h_usd": 650.00,
      "total_change_24h_pct": 5.2,
      "total_change_period": "24h",
      "portfolio_chart_url": "https://api.anvil.finance/api/v1/charts/portfolio?user_id=uuid&range=7d&theme=dark",
      "holdings": [
        {
          "symbol": "USDC",
          "name": "USD Coin",
          "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
          "chain_id": 8453,
          "chain_name": "Base",
          "icon_url": "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
          "amount_token": "5,000.00",
          "amount_usd": 5000.00,
          "price_usd": "1.00",
          "pnl_usd": 0.00,
          "pnl_pct": 0.0,
          "acquired_via": "buy",
          "chart_url": "https://api.anvil.finance/api/v1/charts/USDC?range=7d&theme=dark&w=400&h=200",
          "allocation_pct": 40.0
        },
        {
          "symbol": "BTC",
          "name": "Bitcoin",
          "address": "native",
          "chain_id": 1,
          "chain_name": "Ethereum",
          "icon_url": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png",
          "amount_token": "0.05",
          "amount_usd": 4875.00,
          "price_usd": "97,500.00",
          "pnl_usd": 535.00,
          "pnl_pct": 12.3,
          "acquired_via": "buy",
          "chart_url": "https://api.anvil.finance/api/v1/charts/BTC?range=7d&theme=dark&w=400&h=200",
          "allocation_pct": 39.0
        },
        {
          "symbol": "ETH",
          "name": "Ethereum",
          "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
          "chain_id": 8453,
          "chain_name": "Base",
          "icon_url": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
          "amount_token": "0.85",
          "amount_usd": 2625.00,
          "price_usd": "3,088.24",
          "pnl_usd": -243.00,
          "pnl_pct": -3.1,
          "acquired_via": "swap",
          "chart_url": "https://api.anvil.finance/api/v1/charts/ETH?range=7d&theme=dark&w=400&h=200",
          "allocation_pct": 21.0
        }
      ],
      "lending_positions": [
        {
          "protocol": "Morpho",
          "token": "USDC",
          "supplied_amount": "1,000.00",
          "supplied_usd": 1000.00,
          "current_apy": 4.5,
          "earned_usd": 12.50,
          "chain_name": "Base"
        }
      ],
      "total_lending_usd": 1000.00,
      "recommendations": [
        {
          "action": "earn_yield",
          "priority": 1,
          "summary": "You have $5,000 USDC sitting idle",
          "reasoning": "Idle stablecoins can earn 4-6% APY on lending protocols like Morpho on Base with minimal risk.",
          "cta": "Would you like to earn ~$225/year by lending your USDC on Morpho?",
          "potential_impact": "$225/year in yield"
        },
        {
          "action": "take_profit",
          "priority": 2,
          "summary": "BTC is up 12.3% — consider taking some profit",
          "reasoning": "Your BTC position has appreciated significantly. Taking partial profit locks in gains while maintaining exposure.",
          "cta": "Want to swap 20% of your BTC to USDC to lock in gains?",
          "potential_impact": "Lock in ~$107 profit"
        },
        {
          "action": "diversify",
          "priority": 3,
          "summary": "40% in USDC and 39% in BTC — consider diversifying",
          "reasoning": "Portfolio is concentrated in 2 assets. Adding exposure to other assets reduces risk.",
          "cta": "Would you like to explore other tokens for diversification?",
          "potential_impact": "Reduced concentration risk"
        }
      ],
      "last_updated": "2026-02-09T14:30:00Z"
    }
  }
}
```

---

## P&L Calculation Logic

### Cost Basis (FIFO Method)

```python
class PnLCalculator:
    """Calculate P&L per holding using FIFO cost basis from transaction history."""

    async def calculate_holding_pnl(
        self, user_id: str, token: str, chain_id: int
    ) -> tuple[float, float, str]:
        """
        Returns: (pnl_usd, pnl_pct, acquired_via)
        """
        # 1. Get all acquisition transactions for this token
        txns = await self._tx_repo.get_user_transactions(
            user_id=user_id,
            token=token,
            chain_id=chain_id,
            types=["buy", "swap_to", "receive"]
        )

        if not txns:
            return 0.0, 0.0, "unknown"

        # 2. Calculate FIFO cost basis
        total_cost_usd = sum(tx.cost_basis_usd for tx in txns)
        total_amount = sum(tx.amount for tx in txns)

        # 3. Get current value
        current_price = await self._price_provider.get_price(token)
        current_value = total_amount * current_price

        # 4. Calculate P&L
        pnl_usd = current_value - total_cost_usd
        pnl_pct = ((current_value - total_cost_usd) / total_cost_usd * 100) if total_cost_usd > 0 else 0.0

        # 5. Determine primary acquisition method
        acquired_via = self._dominant_acquisition(txns)

        return round(pnl_usd, 2), round(pnl_pct, 1), acquired_via

    def _dominant_acquisition(self, txns: list) -> str:
        """Return most common acquisition method."""
        from collections import Counter
        methods = Counter(tx.transaction_type for tx in txns)
        return methods.most_common(1)[0][0]  # "buy", "swap", "receive"
```

### Cost Basis Sources

| Transaction Type | Cost Basis |
|-----------------|------------|
| **Buy** (fiat on-ramp) | Fiat amount spent (USD) |
| **Swap** (received token) | USD value of `from_token` at swap time |
| **Receive** (deposit) | Market price at time of receipt |
| **Airdrop** | Market price at time of claim (or $0 if free) |

---

## Recommendation Engine

### Decision Rules

```python
class RecommendationEngine:
    """Generate portfolio recommendations based on holdings analysis."""

    def generate(
        self,
        holdings: list[HoldingItem],
        lending_positions: list[LendingItem],
        total_usd: float,
    ) -> list[Recommendation]:
        recommendations = []

        # Rule 1: Idle stablecoins > $100
        idle_stables = sum(
            h.amount_usd for h in holdings
            if h.symbol in ("USDC", "USDT", "DAI") 
            and not self._is_in_lending(h.symbol, lending_positions)
        )
        if idle_stables > 100:
            annual_yield = idle_stables * 0.045  # Estimate 4.5% APY
            recommendations.append(Recommendation(
                action="earn_yield",
                priority=1,
                summary=f"You have ${idle_stables:,.0f} in idle stablecoins",
                reasoning="Idle stablecoins can earn 4-6% APY on lending protocols.",
                cta=f"Would you like to earn ~${annual_yield:,.0f}/year by lending?",
                potential_impact=f"${annual_yield:,.0f}/year in yield",
            ))

        # Rule 2: Significant profit (>10% on any holding)
        for h in holdings:
            if h.pnl_pct > 10 and h.amount_usd > 50:
                profit = h.pnl_usd * 0.2  # 20% take-profit suggestion
                recommendations.append(Recommendation(
                    action="take_profit",
                    priority=2,
                    summary=f"{h.symbol} is up {h.pnl_pct:.1f}%",
                    reasoning="Consider taking partial profits to lock in gains.",
                    cta=f"Want to swap 20% of your {h.symbol} to USDC?",
                    potential_impact=f"Lock in ~${profit:,.0f} profit",
                ))

        # Rule 3: Concentration risk (any single asset > 50%)
        for h in holdings:
            if h.allocation_pct > 50:
                recommendations.append(Recommendation(
                    action="diversify",
                    priority=3,
                    summary=f"{h.symbol} is {h.allocation_pct:.0f}% of portfolio",
                    reasoning="High concentration in a single asset increases risk.",
                    cta="Would you like to explore other tokens?",
                    potential_impact="Reduced concentration risk",
                ))

        # Rule 4: Empty portfolio
        if total_usd == 0:
            recommendations.append(Recommendation(
                action="buy",
                priority=1,
                summary="Your portfolio is empty",
                reasoning="Start building your portfolio with a small purchase.",
                cta="Would you like to buy some crypto? Try 'buy $50 of USDC'",
                potential_impact="Start earning and trading",
            ))

        # Rule 5: Loss > 10% — suggest DCA
        for h in holdings:
            if h.pnl_pct < -10 and h.amount_usd > 50:
                recommendations.append(Recommendation(
                    action="buy",
                    priority=3,
                    summary=f"{h.symbol} is down {abs(h.pnl_pct):.1f}%",
                    reasoning="Dollar-cost averaging can reduce your average entry price.",
                    cta=f"Want to buy more {h.symbol} to average down?",
                    potential_impact="Lower average entry price",
                ))

        return sorted(recommendations, key=lambda r: r.priority)[:3]  # Max 3
```

---

## Data Flow

```
User: "what's my balance?"
│
├── Intent Detection → BALANCE_CHECK
│
├── BalanceOverviewHandler.handle()
│   │
│   ├── Parallel fetch (asyncio.gather):
│   │   ├── BalanceProvider.get_all_balances(address, chains)    # On-chain RPC
│   │   ├── PriceProvider.get_prices(tokens)                     # CoinGecko
│   │   ├── LendingProvider.get_positions(user_id)               # DB + Morpho API
│   │   └── TransactionRepository.get_user_transactions(user_id) # PostgreSQL
│   │
│   ├── Calculate per-token P&L (FIFO cost basis)
│   ├── Build chart_url per token
│   ├── Calculate allocation percentages
│   ├── Generate recommendations
│   │
│   └── Return BalanceOverviewEnrichment
│
└── UnifiedChatResponse with enrichment.balance_overview
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Application** | `queries/balance/balance_overview_chat.py` | BalanceOverviewChatHandler |
| **Application** | `services/pnl_calculator.py` | PnLCalculator (FIFO) |
| **Application** | `services/recommendation_engine.py` | RecommendationEngine |
| **Application** | `services/chart_url_builder.py` | ChartURLBuilder (shared with sentiment) |
| **Domain** | `entities/balance.py` | HoldingItem, LendingItem, Recommendation |
| **Domain** | `ports/balance_provider.py` | BalanceProvider protocol |
| **Domain** | `ports/lending_provider.py` | LendingProvider protocol |
| **Infrastructure** | `adapters/wallet/rpc_balance_provider.py` | On-chain RPC |
| **Infrastructure** | `adapters/external/coingecko_client.py` | Price data |
| **Infrastructure** | `adapters/lending/morpho_adapter.py` | Morpho positions |

---

## Caching Strategy

| Data | TTL | Reason |
|------|-----|--------|
| Token balances | No cache | Fresh RPC read for accuracy |
| Token prices | 30s | CoinGecko rate limits |
| Lending positions | 60s | Positions don't change every second |
| Transaction history | 5 min | For P&L cost basis |
| Chart URLs | Static | URLs are deterministic, images cached separately |

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Total response time | < 3s |
| RPC balance fetch | < 1.5s (parallel across chains) |
| Price enrichment | < 300ms (cached) |
| P&L calculation | < 500ms |
| Recommendation gen | < 100ms (rule-based) |

---

## Frontend Rendering

```
┌─────────────────────────────────────────┐
│  💰 Portfolio Overview                  │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  $12,500.00      ↑ $650 (+5.2%)    ││
│  │  ┌─────────────────────────────┐    ││
│  │  │ [Portfolio 7D Chart]        │    ││
│  │  └─────────────────────────────┘    ││
│  └─────────────────────────────────────┘│
│                                         │
│  Holdings                               │
│  ┌─────────────────────────────────────┐│
│  │  USDC    $5,000   40%    ── 0.0%   ││
│  │  [mini chart]                       ││
│  │                                     ││
│  │  BTC     $4,875   39%  ↑ +12.3%    ││
│  │  [mini chart]                       ││
│  │                                     ││
│  │  ETH     $2,625   21%  ↓ -3.1%     ││
│  │  [mini chart]                       ││
│  └─────────────────────────────────────┘│
│                                         │
│  💡 Recommendations                     │
│  ┌─────────────────────────────────────┐│
│  │ 1. Earn ~$225/yr lending USDC      ││
│  │    [Set up Morpho lending →]        ││
│  │                                     ││
│  │ 2. BTC up 12.3% — take profit?     ││
│  │    [Swap 20% BTC → USDC →]         ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Open Items

- [ ] Portfolio chart endpoint (aggregate value over time, requires TimescaleDB snapshots)
- [ ] Multi-chain aggregation: same token across chains = single row or separate?
- [ ] Lending yield calculation: real-time APY vs historical earned
- [ ] Recommendation personalization based on chat mode (casual vs degen)
- [ ] Tax reporting tie-in: cost basis export
- [ ] Real-time price updates via WebSocket for live portfolio tracking

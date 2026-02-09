# Swap Workflow — Multi-Provider `available_swaps` Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Context**: Chat Response Enrichment (conversations/messages) — CONFIRM Step  
**Intent**: `SWAP` / `TRADE_SWAP`  
**Related**: Swap Execution Agents, Execute Action Endpoint, 1inch MCP, Hyperliquid Client

---

## Overview

Modification to the existing swap workflow's **CONFIRM step**. When a user requests a swap via chat (e.g., "swap 100 USDC to PURR"), the agent response now includes an `available_swaps` array containing quotes from **ALL configured providers** (Hyperliquid, 1inch, 0x). Quotes are fetched in parallel, sorted by best output amount, and cached in Redis for 5 minutes. The user selects their preferred provider, and the execute endpoint uses the corresponding `provider_id` to look up the cached quote.

---

## Swap Flow (Updated)

```
User: "swap 100 USDC to PURR"
│
├── Step 1: Intent Detection → SWAP
│   entities: {from: "USDC", to: "PURR", amount: "100"}
│
├── Step 2: Quote Aggregation (NEW — parallel)
│   ├── Hyperliquid Spot → quote in 200ms
│   ├── 1inch API → quote in 500ms
│   └── 0x API → quote in 400ms (or unavailable)
│
├── Step 3: CONFIRM Response (agent_message)
│   ├── agent_message.content = "I found 2 swap options for 100 USDC → PURR..."
│   ├── enrichment.available_swaps = [HL, 1inch, 0x]
│   └── enrichment.pending_action = {action_type: "swap", ...}
│
├── Step 4: User selects provider (frontend tap)
│   └── POST /api/v1/swap/execute { "provider_id": "hl_quote_abc123" }
│
└── Step 5: Execute
    ├── Lookup cached quote by provider_id
    ├── Build tx_data (1inch) or hl_order_data (Hyperliquid)
    └── Return for Privy SDK signing
```

---

## Response Schema — CONFIRM Step

### Enrichment Block: `available_swaps`

```python
class SwapQuote(BaseModel):
    provider: str                           # "hyperliquid", "1inch", "0x"
    provider_id: str | None                 # Cache key: "hl_quote_abc123" — used in /execute
    provider_display: str                   # "Hyperliquid Spot", "1inch", "0x Protocol"
    is_best: bool                           # True for highest to_amount
    is_available: bool                      # False if provider can't fill this swap
    unavailable_reason: str | None          # "Token PURR not supported on 0x"
    
    # Swap details (only present if is_available=true)
    from_token: str | None                  # "USDC"
    from_amount: str | None                 # "100"
    from_amount_usd: str | None             # "100.00"
    to_token: str | None                    # "PURR"
    to_amount: str | None                   # "4,267.89" — differs per provider
    to_amount_usd: str | None               # "100.00"
    
    # Costs
    fee_pct: str | None                     # "0.02"
    fee_usd: str | None                     # "0.02"
    gas_usd: str | None                     # "0.00" (HL), "$0.45" (1inch)
    total_cost_usd: str | None              # fee + gas
    
    # Execution info
    estimated_time_seconds: int | None      # 1 (HL), 15 (1inch on Ethereum)
    price_impact_pct: float | None          # 0.05
    slippage_tolerance_pct: float | None    # 1.0
    expires_at: str | None                  # ISO8601 — 5 min from quote time
    
    # Provider-specific metadata
    route: str | None                       # "USDC → PURR" or "USDC → ETH → PURR"
    dex_sources: list[str] | None           # ["Hyperliquid Spot"] or ["Uniswap V3", "SushiSwap"]

class SwapConfirmEnrichment(BaseModel):
    type: Literal["swap_confirm"] = "swap_confirm"
    available_swaps: list[SwapQuote]        # All provider quotes (sorted by to_amount DESC)
    best_provider: str                      # "hyperliquid" — convenience field
    from_token: str                         # "USDC"
    from_amount: str                        # "100"
    to_token: str                           # "PURR"
    providers_queried: int                  # 3
    providers_available: int                # 2
    quote_timestamp: str                    # ISO8601
    pending_action: PendingSwapAction       # For legacy /execute flow
```

### Example CONFIRM Response

```json
{
  "user_message": { "content": "swap 100 USDC to PURR", ... },
  "agent_message": {
    "content": "I found 2 swap options for 100 USDC → PURR:\n\n🏆 Best: Hyperliquid Spot — 4,267.89 PURR ($0.02 fee, instant)\n2nd: 1inch — 4,201.34 PURR ($0.75 total cost, ~15s)\n\nHyperliquid gives you 1.6% more PURR. Want to proceed with the best rate?",
    "agent_type": "swap_handler"
  },
  "routing": {
    "intent": "SWAP",
    "confidence": 0.97,
    "handler": "swap_quote_aggregator"
  },
  "enrichment": {
    "swap_confirm": {
      "type": "swap_confirm",
      "from_token": "USDC",
      "from_amount": "100",
      "to_token": "PURR",
      "best_provider": "hyperliquid",
      "providers_queried": 3,
      "providers_available": 2,
      "quote_timestamp": "2026-02-09T14:30:00Z",
      "available_swaps": [
        {
          "provider": "hyperliquid",
          "provider_id": "hl_quote_abc123",
          "provider_display": "Hyperliquid Spot",
          "is_best": true,
          "is_available": true,
          "unavailable_reason": null,
          "from_token": "USDC",
          "from_amount": "100",
          "from_amount_usd": "100.00",
          "to_token": "PURR",
          "to_amount": "4,267.89",
          "to_amount_usd": "100.00",
          "fee_pct": "0.02",
          "fee_usd": "0.02",
          "gas_usd": "0.00",
          "total_cost_usd": "0.02",
          "estimated_time_seconds": 1,
          "price_impact_pct": 0.05,
          "slippage_tolerance_pct": 1.0,
          "expires_at": "2026-02-09T14:35:00Z",
          "route": "USDC → PURR",
          "dex_sources": ["Hyperliquid Spot"]
        },
        {
          "provider": "1inch",
          "provider_id": "1inch_quote_def456",
          "provider_display": "1inch DEX Aggregator",
          "is_best": false,
          "is_available": true,
          "unavailable_reason": null,
          "from_token": "USDC",
          "from_amount": "100",
          "from_amount_usd": "100.00",
          "to_token": "PURR",
          "to_amount": "4,201.34",
          "to_amount_usd": "98.44",
          "fee_pct": "0.10",
          "fee_usd": "0.30",
          "gas_usd": "0.45",
          "total_cost_usd": "0.75",
          "estimated_time_seconds": 15,
          "price_impact_pct": 0.12,
          "slippage_tolerance_pct": 1.0,
          "expires_at": "2026-02-09T14:35:00Z",
          "route": "USDC → WETH → PURR",
          "dex_sources": ["Uniswap V3", "SushiSwap"]
        },
        {
          "provider": "0x",
          "provider_id": null,
          "provider_display": "0x Protocol",
          "is_best": false,
          "is_available": false,
          "unavailable_reason": "Token PURR not supported on 0x Protocol",
          "from_token": null,
          "from_amount": null,
          "from_amount_usd": null,
          "to_token": null,
          "to_amount": null,
          "to_amount_usd": null,
          "fee_pct": null,
          "fee_usd": null,
          "gas_usd": null,
          "total_cost_usd": null,
          "estimated_time_seconds": null,
          "price_impact_pct": null,
          "slippage_tolerance_pct": null,
          "expires_at": null,
          "route": null,
          "dex_sources": null
        }
      ],
      "pending_action": {
        "action_type": "swap",
        "from_token": "USDC",
        "to_token": "PURR",
        "amount": "100",
        "best_provider_id": "hl_quote_abc123"
      }
    }
  }
}
```

---

## Quote Aggregation Engine

### Parallel Provider Fetching

```python
class SwapQuoteAggregator:
    """Fetch quotes from all providers in parallel, sort by best output."""

    PROVIDERS = ["hyperliquid", "1inch", "0x"]
    QUOTE_TTL_SECONDS = 300  # 5 minutes

    async def get_quotes(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain_id: int,
        user_address: str,
    ) -> list[SwapQuote]:
        """Fetch all provider quotes in parallel."""

        # 1. Launch all provider queries simultaneously
        tasks = {
            "hyperliquid": self._get_hl_quote(from_token, to_token, amount),
            "1inch": self._get_1inch_quote(from_token, to_token, amount, chain_id, user_address),
            "0x": self._get_0x_quote(from_token, to_token, amount, chain_id),
        }

        results = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        # 2. Build quote objects
        quotes = []
        for provider, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                quotes.append(SwapQuote(
                    provider=provider,
                    provider_id=None,
                    provider_display=PROVIDER_DISPLAY_NAMES[provider],
                    is_best=False,
                    is_available=False,
                    unavailable_reason=self._format_error(provider, result),
                ))
            else:
                quotes.append(result)

        # 3. Sort available quotes by to_amount DESC (best deal first)
        available = [q for q in quotes if q.is_available]
        unavailable = [q for q in quotes if not q.is_available]

        available.sort(key=lambda q: float(q.to_amount.replace(",", "")), reverse=True)

        # 4. Mark best
        if available:
            available[0].is_best = True

        # 5. Cache each available quote by provider_id
        for quote in available:
            await self._cache.set(
                f"swap_quote:{quote.provider_id}",
                quote.model_dump(),
                ttl=self.QUOTE_TTL_SECONDS,
            )

        return available + unavailable

    async def _get_hl_quote(self, from_token, to_token, amount) -> SwapQuote:
        """Get Hyperliquid Spot quote."""
        # Check if token pair exists on HL Spot
        if not await self._hl_client.is_token_on_spot(to_token):
            return SwapQuote(
                provider="hyperliquid",
                provider_id=None,
                provider_display="Hyperliquid Spot",
                is_available=False,
                unavailable_reason=f"{to_token} not available on Hyperliquid Spot",
                is_best=False,
            )

        # Get order book for price estimation
        order_book = await self._hl_client.get_spot_order_book(f"{to_token}/USDC")
        estimated_output = self._estimate_fill(order_book, float(amount))

        provider_id = f"hl_quote_{uuid4().hex[:12]}"
        expires_at = (now() + timedelta(seconds=300)).isoformat()

        return SwapQuote(
            provider="hyperliquid",
            provider_id=provider_id,
            provider_display="Hyperliquid Spot",
            is_best=False,  # Will be set after sort
            is_available=True,
            from_token=from_token,
            from_amount=amount,
            from_amount_usd=amount,  # USDC = 1:1
            to_token=to_token,
            to_amount=f"{estimated_output:,.2f}",
            to_amount_usd=amount,
            fee_pct="0.02",
            fee_usd=f"{float(amount) * 0.0002:.2f}",
            gas_usd="0.00",
            total_cost_usd=f"{float(amount) * 0.0002:.2f}",
            estimated_time_seconds=1,
            price_impact_pct=self._calc_price_impact(order_book, float(amount)),
            slippage_tolerance_pct=1.0,
            expires_at=expires_at,
            route=f"{from_token} → {to_token}",
            dex_sources=["Hyperliquid Spot"],
        )

    async def _get_1inch_quote(self, from_token, to_token, amount, chain_id, user_address) -> SwapQuote:
        """Get 1inch quote via MCP or API."""
        try:
            quote = await self._1inch_client.get_quote(
                from_token_address=self._resolve_address(from_token, chain_id),
                to_token_address=self._resolve_address(to_token, chain_id),
                amount=self._to_wei(amount, from_token),
                chain_id=chain_id,
                from_address=user_address,
            )

            provider_id = f"1inch_quote_{uuid4().hex[:12]}"
            to_amount_human = self._from_wei(quote["toAmount"], to_token)

            return SwapQuote(
                provider="1inch",
                provider_id=provider_id,
                provider_display="1inch DEX Aggregator",
                is_best=False,
                is_available=True,
                from_token=from_token,
                from_amount=amount,
                from_amount_usd=amount,
                to_token=to_token,
                to_amount=f"{to_amount_human:,.2f}",
                to_amount_usd=f"{to_amount_human * float(self._get_price(to_token)):.2f}",
                fee_pct="0.10",
                fee_usd=f"{float(amount) * 0.001:.2f}",
                gas_usd=f"{quote.get('estimatedGas', 0) * self._gas_price_gwei * 1e-9 * self._eth_price:.2f}",
                total_cost_usd="...",  # fee + gas
                estimated_time_seconds=15,
                price_impact_pct=float(quote.get("priceImpact", 0)),
                slippage_tolerance_pct=1.0,
                expires_at=(now() + timedelta(seconds=300)).isoformat(),
                route=" → ".join(quote.get("protocols", [[]])[0]),
                dex_sources=quote.get("protocols_names", []),
            )
        except Exception as e:
            return SwapQuote(
                provider="1inch",
                provider_id=None,
                provider_display="1inch DEX Aggregator",
                is_best=False,
                is_available=False,
                unavailable_reason=str(e),
            )
```

---

## Execute Endpoint (Updated)

### Request

```
POST /api/v1/swap/execute
```

**Auth**: Required (JWT Bearer Token)

```json
{
  "provider_id": "hl_quote_abc123"
}
```

### Execute Logic

```python
class ExecuteSwapHandler:
    """Execute a swap using a cached provider quote."""

    async def handle(self, command: ExecuteSwapCommand) -> SwapExecuteResult:
        provider_id = command.provider_id

        # 1. Lookup cached quote
        cached_quote = await self._cache.get(f"swap_quote:{provider_id}")
        if not cached_quote:
            raise PreviewNotFoundError("Quote expired or not found. Please request a new quote.")

        # 2. Verify quote hasn't expired
        if now() > datetime.fromisoformat(cached_quote["expires_at"]):
            await self._cache.delete(f"swap_quote:{provider_id}")
            raise PreviewExpiredError("Quote has expired. Please request a new quote.")

        # 3. Verify user owns this quote
        # (stored with user_id association)

        # 4. Route to provider-specific executor
        provider = cached_quote["provider"]

        if provider == "hyperliquid":
            return await self._execute_hl_swap(cached_quote)
        elif provider == "1inch":
            return await self._execute_1inch_swap(cached_quote)
        elif provider == "0x":
            return await self._execute_0x_swap(cached_quote)

        raise ValueError(f"Unknown provider: {provider}")

    async def _execute_hl_swap(self, quote: dict) -> SwapExecuteResult:
        """Build Hyperliquid order data for Privy signing."""
        return SwapExecuteResult(
            provider="hyperliquid",
            execution_type="hl_order",
            hl_order_data={
                "asset": quote["to_token"],
                "is_buy": True,
                "sz": quote["to_amount"],
                "limit_px": "...",  # Calculated with slippage
                "order_type": {"limit": {"tif": "Ioc"}},
            },
            # No tx_data — Hyperliquid uses L1 signing, not EVM tx
        )

    async def _execute_1inch_swap(self, quote: dict) -> SwapExecuteResult:
        """Build 1inch transaction for Privy signing."""
        swap_tx = await self._1inch_client.get_swap(
            from_token=quote["from_token_address"],
            to_token=quote["to_token_address"],
            amount=quote["from_amount_wei"],
            from_address=quote["user_address"],
            slippage=quote["slippage_tolerance_pct"],
        )

        return SwapExecuteResult(
            provider="1inch",
            execution_type="evm_transaction",
            tx_data={
                "to": swap_tx["tx"]["to"],
                "data": swap_tx["tx"]["data"],
                "value": swap_tx["tx"]["value"],
                "gas_limit": swap_tx["tx"]["gas"],
                "chain_id": quote["chain_id"],
            },
        )
```

### Execute Response

```python
class SwapExecuteResult(BaseModel):
    provider: str                           # "hyperliquid" | "1inch" | "0x"
    execution_type: str                     # "hl_order" | "evm_transaction"
    tx_data: dict | None                    # For EVM-based providers (1inch, 0x)
    hl_order_data: dict | None              # For Hyperliquid L1
    status: str = "ready_to_sign"           # Frontend triggers Privy signing
    message: str = "Transaction ready for signing"
```

---

## Redis Cache Schema

```python
# Key: swap_quote:{provider_id}
# TTL: 300 seconds (5 minutes)
# Value: JSON
{
    "provider": "hyperliquid",
    "provider_id": "hl_quote_abc123",
    "user_id": "user-uuid",
    "from_token": "USDC",
    "from_token_address": "0x833...",
    "to_token": "PURR",
    "to_token_address": "0x...",
    "from_amount": "100",
    "from_amount_wei": "100000000",
    "to_amount": "4267.89",
    "chain_id": 8453,
    "user_address": "0x7a23...",
    "slippage_tolerance_pct": 1.0,
    "expires_at": "2026-02-09T14:35:00Z",
    "created_at": "2026-02-09T14:30:00Z",
    # Provider-specific execution data
    "execution_params": { ... }
}
```

---

## Provider Configuration

### Supported Providers

| Provider | Token Support | Gas | Speed | Best For |
|----------|--------------|-----|-------|----------|
| **Hyperliquid Spot** | ~50 meme tokens + USDC | $0 | 1s | Meme tokens, USDC pairs |
| **1inch** | All ERC-20 tokens | Variable | 15s | Major tokens, multi-hop routes |
| **0x Protocol** | Most ERC-20 tokens | Variable | 15s | Alternative to 1inch |

### Provider Selection (Auto-Best)

```python
# For legacy clients that don't support available_swaps:
# The execute_data field still contains the best provider's tx
pending_action = {
    "action_type": "swap",
    "best_provider_id": available_swaps[0].provider_id,  # Best quote
    # Legacy fields for backwards compatibility
    "from_token": "USDC",
    "to_token": "PURR",
    "amount": "100",
}
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Presentation** | `controllers/swap/swap_execute.py` | POST /swap/execute (updated) |
| **Application** | `services/swap_quote_aggregator.py` | Parallel provider querying |
| **Application** | `commands/swap/execute_swap.py` | Execute handler (updated) |
| **Domain** | `entities/swap_quote.py` | SwapQuote, SwapExecuteResult |
| **Domain** | `ports/swap_provider.py` | SwapProvider protocol (per-provider) |
| **Infrastructure** | `adapters/external/hyperliquid_client.py` | HL Spot quotes + orders |
| **Infrastructure** | `adapters/external/1inch_client.py` | 1inch API quotes + swap TX |
| **Infrastructure** | `adapters/external/0x_client.py` | 0x Protocol quotes |
| **Infrastructure** | `adapters/cache/redis_quote_cache.py` | Redis quote caching |

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Total quote aggregation | < 1.5s (parallel, slowest provider dominates) |
| Hyperliquid quote | < 300ms |
| 1inch quote | < 800ms |
| 0x quote | < 600ms |
| Execute (cache lookup + build TX) | < 500ms |
| Provider timeout | 2s per provider (fail fast) |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| All providers fail | "Unable to get swap quotes right now. Please try again." |
| Only HL fails | Show 1inch + 0x quotes (HL marked unavailable) |
| Quote expired on execute | "Your quote has expired. Let me get fresh prices." → re-fetch |
| Insufficient balance | "You need 100 USDC but only have 50 USDC." — detected pre-quote |
| Token not found | "I don't recognize token '{X}'. Did you mean...?" |

---

## Frontend Rendering

```
┌─────────────────────────────────────────┐
│  🔄 Swap 100 USDC → PURR               │
│                                         │
│  Available Options:                     │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 🏆 BEST                            ││
│  │ Hyperliquid Spot                    ││
│  │                                     ││
│  │ 4,267.89 PURR                      ││
│  │ Fee: $0.02 · Gas: $0.00 · ⚡ 1s    ││
│  │                                     ││
│  │ [   Swap with Hyperliquid   ]       ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │ 1inch DEX Aggregator                ││
│  │                                     ││
│  │ 4,201.34 PURR  (-1.6%)             ││
│  │ Fee: $0.30 · Gas: $0.45 · ~15s     ││
│  │ Route: USDC → WETH → PURR          ││
│  │                                     ││
│  │ [    Swap with 1inch    ]           ││
│  └─────────────────────────────────────┘│
│                                         │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐│
│  │ 0x Protocol              ⚠️         ││
│  │ PURR not supported                  ││
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘│
│                                         │
│  ℹ️ Quotes expire in 4:32              │
└─────────────────────────────────────────┘
```

---

## Open Items

- [ ] 0x Protocol integration (API key + implementation)
- [ ] Cross-chain swaps (e.g., USDC on Base → PURR on HyperEVM) via bridge
- [ ] Price impact warning threshold (> 1% = yellow, > 5% = red)
- [ ] Max slippage per provider (user configurable)
- [ ] Quote refresh: auto-refresh every 30s while user is viewing
- [ ] Analytics: track which provider users choose (preference data)
- [ ] Rate limiting per provider API keys
- [ ] 1inch account configuration fix (currently blocked)

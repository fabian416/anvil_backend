# Swap System Technical Specification

> **Version:** 2.0
> **Date:** 2026-01-25  
> **Status:** Production
> **Authors:** @prompt-engineer @fastapi-expert @business-analyst

---

## Executive Summary

The Anvil Swap System enables conversational token swaps through AI-powered chat. Currently uses **Hyperliquid Spot** as the sole provider, supporting **meme tokens only** paired with USDC.

### Current State

| Provider | Status | Token Coverage | Integration Level |
|----------|--------|----------------|-------------------|
| Hyperliquid Spot | ✅ Active | 50+ meme tokens (PURR, TRUMP, PEPE, etc.) | Full |
| 1inch | 🟡 Available | 100+ major tokens (ETH, BTC, etc.) | MCP Ready |
| 0x Protocol | 🟡 Available | 100+ major tokens | Frontend Ready |
| Hyperliquid Perps | 🟡 Available | 30+ perpetual futures | MCP Ready |

### Critical Limitation

⚠️ **Hyperliquid Spot does NOT support major tokens** (ETH, BTC, SOL, etc.). These are only available via:
- Hyperliquid Perps (perpetual futures, not spot)
- 1inch DEX Aggregator (requires API key + MCP integration)
- 0x Protocol (frontend execution via Privy wallet)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REQUEST                                  │
│  "swap 100 USDC to PURR"  OR  "swap 100 USDC to ETH"           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              POST /api/v1/conversations/{id}/messages            │
│  conversations_router.py:send_message()                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              IntentDetectorV2.detect()                           │
│  Detects: SWAP or MOONPAY_SWAP (confidence: 0.90+)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SwapHandlerV2                                       │
│  - Validates tokens against HYPERLIQUID_SPOT_TOKENS             │
│  - If major token → Returns helpful error message               │
│  - If meme token → Fetches real-time quote from Hyperliquid     │
│  - Returns quote with execute_data                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │ Token?  │
                    └────┬────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
┌──────────────────────┐   ┌──────────────────────────────────┐
│ MEME TOKEN           │   │ MAJOR TOKEN (ETH, BTC, etc.)     │
│ (PURR, TRUMP, etc.)  │   │                                  │
│                      │   │ ⚠️ ERROR MESSAGE                 │
│ ✅ Hyperliquid Quote │   │ "ETH not available on            │
│ ✅ Real-time price   │   │  Hyperliquid Spot. Use perps     │
│ ✅ Execute ready     │   │  or external DEX aggregators"    │
└──────────────────────┘   └──────────────────────────────────┘
```

---

## 2. Current Implementation

### 2.1 Supported Tokens (Hyperliquid Spot)

```python
# File: src/app/application/chat/handlers/swap_handler_v2.py

HYPERLIQUID_SPOT_TOKENS = {
    "USDC",  # Quote currency (required for all swaps)
    "PURR", "HFUN", "TRUMP", "PEPE", "MOG", "POINTS", "JEFF",
    "GMEOW", "LICK", "MANLET", "SIX", "WAGMI", "CAPPY",
    "XULIAN", "RUG", "CZ", "BAGS", "ANSEM", "TATE", "FUN",
    "BIGBEN", "KOBE", "VEGAS", "PUMP", "SCHIZO", "CATNIP",
    "HAPPY", "SELL", "HBOOST", "GPT", "PANDA", "HODL", "RAGE",
    "ASI", "LEAP", "VAPOR", "X", "PILL", "CAT", "HPEPE",
    "MBAPPE", "MAGA", "OMNIX", "COKE", "MEOW", "ANT", "NEIRO",
}

# Major tokens explicitly NOT supported on Hyperliquid Spot
MAJOR_TOKENS_NOT_SUPPORTED = {
    "ETH", "BTC", "SOL", "WBTC", "WETH", "LINK", "UNI", "AAVE",
    "CRV", "MKR", "DAI", "USDT", "MATIC", "ARB", "OP", "AVAX",
    "DOT", "ATOM", "APT", "SUI", "SEI", "TIA", "INJ", "FTM",
}
```

### 2.2 Handler Flow

```python
# File: src/app/application/chat/handlers/swap_handler_v2.py

class SwapHandlerV2:
    async def handle(self, message: str, ...) -> HandlerResult:
        # 1. Extract swap info from message
        swap_info = self._extract_swap_info(message, context)
        
        # 2. If incomplete, ask for missing info (multi-turn)
        if not swap_info.is_complete:
            return self._ask_next_step(swap_info, language)
        
        # 3. Generate quote (validates tokens)
        return await self._generate_quote(swap_info, language)
    
    async def _generate_quote(self, swap_info, language) -> HandlerResult:
        # Check if tokens are on Hyperliquid Spot
        if swap_info.from_token not in self.HYPERLIQUID_SPOT_TOKENS:
            return self._token_not_supported_error(swap_info.from_token, language)
        
        if swap_info.to_token not in self.HYPERLIQUID_SPOT_TOKENS:
            return self._token_not_supported_error(swap_info.to_token, language)
        
        # Get real quote from Hyperliquid
        quote = await self._hyperliquid.get_spot_quote(
            from_token=swap_info.from_token,
            to_token=swap_info.to_token,
            amount=swap_info.amount,
        )
        
        return HandlerResult(
            content=self._format_quote(quote, language),
            execute_data={
                "action_type": "swap",
                "provider": "hyperliquid",
                "from_token": swap_info.from_token,
                "to_token": swap_info.to_token,
                "amount": swap_info.amount,
                "quote_amount": quote.to_amount,
                "fee_percent": 0.02,  # Hyperliquid 0.02% fee
            }
        )
```

### 2.3 Dependency Injection

```python
# File: src/app/setup/ioc/chat_phase2.py

@provide
def provide_hyperliquid_client(self) -> HyperliquidClient | None:
    """Provide HyperliquidClient for spot swap quotes."""
    return HyperliquidClient(testnet=False)

@provide
def provide_swap_handler_v2(
    self,
    hyperliquid_client: HyperliquidClient | None,
) -> SwapHandlerV2:
    """Provide SwapHandlerV2 with Hyperliquid spot (ONLY provider)."""
    return SwapHandlerV2(hyperliquid_client=hyperliquid_client)
```

---

## 3. Error Messages for Unsupported Tokens

When a user requests a swap for a major token (ETH, BTC, etc.), the system returns a helpful multi-language error:

```
⚠️ ETH Not Available for Spot Swap

ETH is a major token that is NOT available on Hyperliquid Spot.

Hyperliquid Spot only supports meme tokens paired with USDC:
• PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, etc.

For ETH trading:
• Hyperliquid offers perpetual futures (perps) for ETH
• For spot swaps, use DEX aggregators like 1inch or Uniswap

Available on Anvil for ETH:
• 📈 Check price and market data
• 📊 Portfolio tracking
• 🔮 Price predictions via Hunter AI
```

---

## 4. Enabling Additional Providers

### 4.1 Enable 1inch DEX Aggregator

**Purpose:** Support major tokens (ETH, BTC, SOL, etc.) for spot swaps.

**Step 1: Configure API Key**

```toml
# config/local/.secrets.toml
[oneinch]
api_key = "your-1inch-api-key"
```

**Step 2: Enable MCP Server**

```toml
# config/local/config.toml
[mcp.servers]
oneinch_enabled = true
```

**Step 3: Start 1inch MCP Server**

```bash
make mcp.oneinch  # Port 8081
```

**Step 4: Modify SwapHandlerV2 to use 1inch**

```python
# src/app/application/chat/handlers/swap_handler_v2.py

class SwapHandlerV2:
    def __init__(
        self,
        hyperliquid_client: HyperliquidClient | None = None,
        oneinch_client: OneInchMCPServer | None = None,  # ADD THIS
    ):
        self._hyperliquid = hyperliquid_client
        self._oneinch = oneinch_client  # ADD THIS
    
    async def _generate_quote(self, swap_info, language) -> HandlerResult:
        # Try Hyperliquid first (meme tokens)
        if self._is_meme_token_pair(swap_info):
            return await self._get_hyperliquid_quote(swap_info, language)
        
        # Fall back to 1inch for major tokens
        if self._oneinch and self._is_major_token_pair(swap_info):
            return await self._get_oneinch_quote(swap_info, language)
        
        return self._provider_not_available_error(swap_info, language)
    
    async def _get_oneinch_quote(self, swap_info, language) -> HandlerResult:
        quote = await self._oneinch._get_swap_quote(
            chain_id=1,  # Ethereum mainnet
            from_token=TOKEN_ADDRESSES[swap_info.from_token],
            to_token=TOKEN_ADDRESSES[swap_info.to_token],
            amount=self._to_wei(swap_info.amount, swap_info.from_token),
        )
        
        return HandlerResult(
            content=self._format_quote(quote, language),
            execute_data={
                "action_type": "swap",
                "provider": "oneinch",  # Frontend uses 0x/Privy
                "chain": "ethereum",
                "from_token": swap_info.from_token,
                "to_token": swap_info.to_token,
                "amount": swap_info.amount,
                "quote_amount": self._from_wei(quote["estimated_output"], swap_info.to_token),
            }
        )
```

**Step 5: Update DI Provider**

```python
# src/app/setup/ioc/chat_phase2.py

@provide
def provide_swap_handler_v2(
    self,
    hyperliquid_client: HyperliquidClient | None,
    oneinch_mcp: OneInchMCPServer | None,  # ADD THIS
) -> SwapHandlerV2:
    return SwapHandlerV2(
        hyperliquid_client=hyperliquid_client,
        oneinch_client=oneinch_mcp,  # ADD THIS
    )
```

---

### 4.2 Enable 0x Protocol (Frontend Execution)

**Purpose:** Support major tokens with frontend-executed swaps via Privy wallet.

0x Protocol is already configured for frontend execution. The backend provides quote estimates, and the frontend calls 0x API directly for real-time quotes and executes with Privy.

**Response Format:**

```json
{
  "execute": {
    "action_type": "swap",
    "provider": "privy_0x",
    "chain": "base",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1",
    "quote_amount": "2850.45"
  }
}
```

**Frontend Flow:**
1. Receives `execute.provider = "privy_0x"`
2. Calls 0x API for real-time quote
3. User confirms in Privy modal
4. Executes on-chain

---

### 4.3 Enable Hyperliquid Perps

**Purpose:** Enable perpetual futures trading for major tokens (ETH-PERP, BTC-PERP, etc.).

**Step 1: Enable MCP Server**

```bash
make mcp.hyperliquid  # Port 8090
```

**Step 2: Create Perps Handler**

```python
# src/app/application/chat/handlers/perps_handler.py

class PerpsHandler:
    """Handler for perpetual futures trading on Hyperliquid."""
    
    SUPPORTED_PERPS = {
        "ETH", "BTC", "SOL", "ARB", "OP", "DOGE", "MATIC",
        "LINK", "AVAX", "APT", "SUI", "INJ", "TIA", "SEI",
    }
    
    def __init__(self, hyperliquid_client: HyperliquidClient):
        self._hyperliquid = hyperliquid_client
    
    async def handle(self, message: str, ...) -> HandlerResult:
        """Handle perps trading requests."""
        # Extract perps info: symbol, side (long/short), size, leverage
        perps_info = self._extract_perps_info(message)
        
        # Get funding rate and mark price
        funding = await self._hyperliquid.get_funding_rate(f"{perps_info.symbol}-PERP")
        order_book = await self._hyperliquid.get_order_book(f"{perps_info.symbol}-PERP")
        
        return HandlerResult(
            content=self._format_perps_quote(perps_info, funding, order_book),
            execute_data={
                "action_type": "perps",
                "provider": "hyperliquid",
                "symbol": f"{perps_info.symbol}-PERP",
                "side": perps_info.side,
                "size": perps_info.size,
                "leverage": perps_info.leverage,
            }
        )
```

**Step 3: Add Intent Detection**

```python
# Add PERPS intent to IntentDetectorV2
PERPS_PATTERNS = [
    r"(?:long|short)\s+\d+\s*(?:x|X)?\s*(?:ETH|BTC|SOL)",
    r"open\s+(?:long|short)",
    r"perpetual|perp|leverage",
]
```

---

## 5. Provider Comparison

| Feature | Hyperliquid Spot | 1inch | 0x Protocol | Hyperliquid Perps |
|---------|------------------|-------|-------------|-------------------|
| Token Support | Meme tokens only | 100+ major tokens | 100+ major tokens | 30+ perps |
| Gas Fees | Zero | Variable by chain | Variable by chain | Zero |
| Trading Fee | 0.02% | Variable (0.1-0.3%) | Variable | 0.02% |
| Execution | Backend | Backend/MCP | Frontend (Privy) | Backend |
| API Key | Not required | Required | Frontend SDK | Required for trading |
| MCP Port | N/A (direct client) | 8081 | N/A | 8090 |

---

## 6. Configuration Files

### 6.1 MCP Server Configuration

```toml
# config/local/config.toml

[mcp]
enabled = true

[mcp.servers]
oneinch_enabled = true      # Port 8081 - DEX aggregation
defillama_enabled = true    # Port 8082 - Protocol data
thegraph_enabled = true     # Port 8083 - Blockchain queries
coingecko_enabled = true    # Port 8084 - Price feeds
aave_enabled = true         # Port 8085 - Lending protocol
portfolio_enabled = true    # Port 8086 - Portfolio tracking
perplexity_enabled = true   # Port 8087 - Web research
morpho_enabled = true       # Port 8088 - Lending optimizer
curve_enabled = true        # Port 8089 - Stablecoin DEX
hyperliquid_enabled = true  # Port 8090 - Perpetuals
layerzero_enabled = true    # Port 8091 - Cross-chain bridge
```

### 6.2 API Keys

```toml
# config/local/.secrets.toml

[oneinch]
api_key = "your-1inch-api-key"

[hyperliquid]
api_key = "your-hyperliquid-api-key"      # For trading
api_secret = "your-hyperliquid-secret"     # For signing
```

---

## 7. Testing

### 7.1 Valid Swap (Meme Token)

```bash
curl -X POST "http://localhost:8080/api/v1/conversations/{id}/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "swap 100 USDC to PURR", "language": "en"}'
```

**Expected Response:**
```json
{
  "agent_message": {
    "content": "🔵 **HYPERLIQUID SPOT**\n\n💱 **Swap Quote**\n\n**From:** 100 USDC\n**To:** ~1,234.56 PURR\n\n**Rate:** 1 USDC = 12.3456 PURR\n**Spread:** 5.2 bps\n**Network:** Hyperliquid\n\nReady to execute?"
  },
  "execute": {
    "action_type": "swap",
    "provider": "hyperliquid",
    "from_token": "USDC",
    "to_token": "PURR",
    "amount": "100",
    "quote_amount": "1234.56",
    "fee_percent": 0.02
  }
}
```

### 7.2 Invalid Swap (Major Token)

```bash
curl -X POST "http://localhost:8080/api/v1/conversations/{id}/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "swap 100 USDC to ETH", "language": "en"}'
```

**Expected Response:**
```json
{
  "agent_message": {
    "content": "⚠️ **ETH Not Available for Spot Swap**\n\n**ETH** is a major token that is **NOT available on Hyperliquid Spot**.\n\nHyperliquid Spot only supports **meme tokens** paired with USDC:\n• PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, etc.\n\n**For ETH trading:**\n• Hyperliquid offers **perpetual futures** (perps) for ETH\n• For spot swaps, use DEX aggregators like 1inch or Uniswap"
  },
  "execute": null,
  "metadata": {
    "error": "token_not_supported",
    "token": "ETH",
    "is_major_token": true,
    "suggestion": "use_perps_or_dex"
  }
}
```

---

## 8. Roadmap

### Phase 1: Current State (Complete)
- ✅ Hyperliquid Spot integration (meme tokens)
- ✅ Multi-language error messages
- ✅ Clear user guidance for unsupported tokens

### Phase 2: 1inch Integration (Estimated: 2 days)
- [ ] Configure 1inch API key
- [ ] Update SwapHandlerV2 to use 1inch for major tokens
- [ ] Add token address mappings
- [ ] Test ETH/BTC/SOL swaps

### Phase 3: Hyperliquid Perps (Estimated: 3 days)
- [ ] Create PerpsHandler
- [ ] Add PERPS intent detection
- [ ] Implement funding rate display
- [ ] Add leverage selection UI

### Phase 4: Cross-Chain Bridges (Estimated: 5 days)
- [ ] Enable LayerZero MCP (port 8091)
- [ ] Create BridgeHandler
- [ ] Support ETH→ARB, ETH→OP, ETH→BASE

---

## 9. Files Modified

| File | Purpose |
|------|---------|
| `src/app/application/chat/handlers/swap_handler_v2.py` | Main swap handler |
| `src/app/infrastructure/adapters/external/hyperliquid_client.py` | Hyperliquid API client |
| `src/app/setup/ioc/chat_phase2.py` | Dependency injection |
| `src/app/presentation/http/controllers/chat/conversations_router.py` | HTTP routing |
| `anvil_knowledge/features/swap.json` | Knowledge base |

---

## 10. References

- [Hyperliquid API Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [1inch API Docs](https://docs.1inch.io/)
- [0x API Docs](https://0x.org/docs/api)
- Internal: `src/app/infrastructure/mcp/servers/oneinch_mcp.py`
- Internal: `src/app/infrastructure/mcp/servers/hyperliquid_mcp.py`

---

*Document generated following CTO Engineering Methodology Framework*

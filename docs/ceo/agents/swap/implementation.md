# Swap Workflow Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.SWAP_WORKFLOW
│   └── services/
│       └── agent_squad/
│           └── authenticated_supervisor.py  # Routing rules
│
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── workflows/
│       │           ├── base_workflow_agent.py   # Base class
│       │           └── swap_workflow_agent.py   # Main agent
│       └── external/
│           ├── hyperliquid_client.py      # Primary provider
│           ├── oneinch_client.py          # Fallback
│           ├── lifi_client.py             # Cross-chain
│           └── coingecko_client.py        # Price enrichment
│
├── setup/
│   └── ioc/
│       └── agent_squad_infrastructure.py   # DI registration
│
└── application/
    └── chat/
        └── commands/
            └── send_message_with_supervisor.py  # Entry point

anvil_knowledge/
└── features/
    └── swap.json                           # Knowledge base
```

---

## Core Files

### 1. SwapWorkflowAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py`
**Lines**: ~1,722

#### Class Definition

```python
class SwapWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step swap workflow agent.
    
    Steps:
    1. parse_request: Extract from_token, to_token, amount, chain
    2. fetch_data: Get quotes from appropriate provider
    3. confirm: Show quote, wait for user confirmation
    4. execute: Generate execute_data for frontend
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 165-187 | Initialize with clients |
| `process_step` | 197-246 | Main step router |
| `_handle_parse_request` | 248-343 | Extract swap params |
| `_handle_token_selection` | 345-395 | Interactive picker |
| `_check_unsupported_tokens` | 397-435 | Validate tokens |
| `_handle_fetch_quote` | 538-625 | Get quote, check balance |
| `_get_funding_recommendation` | 627-665 | Insufficient funds message |
| `_fetch_market_enrichment` | 667-751 | CoinGecko prices |
| `_handle_confirm` | 753-796 | User intent parsing |
| `_handle_execute` | 798-854 | Generate execute_data |
| `_build_insufficient_balance_message` | 856-913 | Block execution |
| `_extract_swap_params` | 915-959 | LLM + regex extraction |
| `_parse_swap_params_regex` | 961-1018 | Fallback parsing |
| `_is_hyperliquid_swap` | 1020-1048 | Provider detection |
| `_fetch_quote` | 1050-1181 | Provider routing |

#### Token Configuration

```python
# Lines 54-96
HYPERLIQUID_SPOT_TOKENS = {
    "USDC",  # Quote currency
    "PURR", "HFUN", "TRUMP", "PEPE", "MOG", "POINTS", "JEFF",
    "GMEOW", "LICK", "MANLET", "SIX", "WAGMI", "CAPPY",
    "XULIAN", "RUG", "CZ", "BAGS", "ANSEM", "TATE", "FUN",
    "BIGBEN", "KOBE", "VEGAS", "PUMP", "SCHIZO", "CATNIP",
    "HAPPY", "SELL", "HBOOST", "GPT", "PANDA", "HODL", "RAGE",
    "ASI", "LEAP", "VAPOR", "X", "PILL", "CAT", "HPEPE",
    "MBAPPE", "MAGA", "OMNIX", "COKE", "MEOW", "ANT", "NEIRO",
}

UNSUPPORTED_SWAP_TOKENS = {
    "ETH", "BTC", "SOL", "WBTC", "WETH", "LINK", "UNI", "AAVE",
    "CRV", "MKR", "DAI", "USDT", "MATIC", "ARB", "OP", "AVAX",
    "DOT", "ATOM", "APT", "SUI", "SEI", "TIA", "INJ", "FTM",
    "XRP", "ADA", "DOGE", "LTC", "SHIB",
}

POPULAR_MEME_TOKENS = [
    ("PURR", "Hyperliquid's native meme token"),
    ("TRUMP", "Political meme token"),
    ("PEPE", "Classic frog meme"),
    ("HFUN", "Hyperliquid Fun token"),
    ("MOG", "Mog Coin"),
    ("JEFF", "Jeff token"),
    ("WAGMI", "We're All Gonna Make It"),
    ("GMEOW", "Cat meme token"),
    ("CAPPY", "Cappy token"),
    ("MANLET", "Manlet meme"),
]
```

#### Token Addresses

```python
# Lines 98-127
TOKEN_ADDRESSES = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    },
    "base": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    },
    # ... polygon, arbitrum
}

TOKEN_DECIMALS = {
    "ETH": 18, "WETH": 18, "MATIC": 18,
    "USDC": 6, "USDT": 6,
    "DAI": 18, "WBTC": 8, "BTC": 8,
}
```

---

### 2. HyperliquidClient

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

#### Key Methods

```python
class HyperliquidClient:
    """Client for Hyperliquid Spot exchange."""
    
    async def get_spot_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
    ) -> SpotQuote:
        """
        Get quote from Hyperliquid Spot order book.
        
        Returns:
            SpotQuote with:
            - to_amount: Amount of destination token
            - mid_price: Mid-market price
            - price: Execution price
            - spread_bps: Spread in basis points
        """
    
    async def get_spot_meta(self) -> dict:
        """Get available spot markets."""
    
    async def get_spot_order_book(self, market: str) -> dict:
        """Get real-time order book."""
```

---

### 3. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_swap_workflow_agent(
    self,
    llm_client: LLMClientGateway,
    oneinch_client: OneInchClientProtocol | None,
    lifi_client: LiFiClientProtocol | None,
    coingecko_client: CoinGeckoClient | None,
    settings: AgentSquadSettings,
) -> SwapWorkflowAgent:
    """
    Provide Swap Workflow Agent for authenticated users.
    
    This agent handles multi-step swap operations:
    1. Parse swap request (tokens, amount)
    2. Route to appropriate provider based on token type
    3. Fetch quotes
    4. Confirm with user
    5. Generate execute_data for frontend
    """
    hyperliquid_client = None
    
    # Create Hyperliquid client if API secret is available
    if settings.hyperliquid_api_secret:
        try:
            from app.infrastructure.adapters.external.hyperliquid_client import (
                HyperliquidClient,
            )
            hyperliquid_client = HyperliquidClient(
                api_secret=settings.hyperliquid_api_secret,
            )
            logger.info("✅ Hyperliquid enabled for SwapWorkflowAgent")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create Hyperliquid client: {e}")
    
    return SwapWorkflowAgent(
        llm_client=llm_client,
        oneinch_client=oneinch_client,
        lifi_client=lifi_client,
        coingecko_client=coingecko_client,
        hyperliquid_client=hyperliquid_client,
    )
```

---

### 4. Supervisor Routing

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
# Lines 981-1000
"""
5. SWAP EXECUTION (CRITICAL - Multi-step workflow):
   - "swap X to Y", "exchange X for Y", "convert X to Y" → "swap_workflow"
   - The swap_workflow agent handles the COMPLETE multi-step swap process
   - Use "swap_workflow" when user wants to EXECUTE a swap (has specific amount)
   - Examples: "swap 1 ETH to USDC", "exchange 100 USDC for PURR"
   - DO NOT combine swap_workflow with other agents - it handles everything
"""

# Example mappings
"swap 1 ETH to USDC" → {{"tasks":[{{"agent_type":"swap_workflow"}}]}}
"exchange 100 USDC for ETH" → {{"tasks":[{{"agent_type":"swap_workflow"}}]}}
"best swap rate ETH to USDC" → {{"tasks":[{{"agent_type":"hunter_ai"}}]}}
```

---

### 5. Knowledge Base

**File**: `anvil_knowledge/features/swap.json`

```json
{
  "feature_name": "Token Swap",
  "category": "trading_execution",
  "description": "Execute instant meme token swaps on Hyperliquid Spot...",
  
  "supported_provider": {
    "name": "Hyperliquid Spot",
    "gas_fees": "ZERO",
    "trading_fee": "0.02%",
    "speed": "20,000+ TPS"
  },
  
  "supported_tokens": {
    "quote_currency": "USDC (required for all swaps)",
    "meme_tokens_supported": ["PURR", "TRUMP", "PEPE", ...],
    "major_tokens_NOT_supported": ["ETH", "BTC", "SOL", ...]
  },
  
  "common_questions": {
    "q1": {
      "question": "Can I swap ETH or BTC on Anvil?",
      "answer": "No, Hyperliquid Spot only supports meme tokens..."
    }
  }
}
```

---

## Balance Awareness Implementation

### UserContext Check

```python
# In _handle_fetch_quote (lines 538-625)

# Check user balance and prepare recommendation if insufficient
funding_recommendation = ""
if user_context.needs_funding_recommendation:
    logger.info(
        f"[SwapWorkflow] User has insufficient funds: "
        f"portfolio_state={user_context.portfolio_state}, "
        f"balance=${user_context.total_balance_usd:.2f}"
    )
    funding_recommendation = self._get_funding_recommendation(
        from_token=from_token,
        language=user_context.language,
    )
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `user_context.needs_funding_recommendation` | Property checking if balance < $1 |
| `_get_funding_recommendation()` | Multi-language funding message |
| `_build_insufficient_balance_message()` | Block execution message |
| `_build_swap_user_balance_section()` | Balance display in token selection |

### Behavior Matrix

| Portfolio State | Balance | Quote Shown | Execute Data | Next Step |
|-----------------|---------|-------------|--------------|-----------|
| Empty | $0 | ✅ Yes | ❌ No | PARSE_REQUEST |
| Starter | < swap amount | ✅ Yes | ❌ No | PARSE_REQUEST |
| Established | >= swap amount | ✅ Yes | ✅ Yes | CONFIRM |

---

## Error Handling

### Quote Errors

```python
# Lines 1500-1579
def _get_quote_error_response(self, error: str, language: str) -> str:
    """User-friendly error message without technical details."""
    error_lower = error.lower() if error else ""
    
    if "404" in error_lower or "not found" in error_lower:
        reason = "This token pair may not be available on this network."
    elif "insufficient" in error_lower:
        reason = "Insufficient balance for this swap."
    elif "slippage" in error_lower:
        reason = "Price movement too high. Try a smaller amount."
    elif "timeout" in error_lower:
        reason = "The request timed out. Please try again."
    else:
        # Generic - don't expose technical details
        reason = "Unable to get a quote at this time."
    
    return f"""⚠️ **Swap Quote Unavailable**

{reason}

**What you can try:**
• Check if the token is available on this network
• Try a different token pair
• Try again in a moment
"""
```

### Unsupported Token Messages

```python
# Lines 437-497
def _build_unsupported_message(self, from_token, to_token, unsupported_tokens, language):
    """Build message for unsupported tokens."""
    return f"""❌ **Swap not supported: {from_token} → {to_token}**

Anvil uses **Hyperliquid Spot** for swaps, which only supports 
**meme tokens paired with USDC**.

**Tokens like {', '.join(unsupported_tokens)} are not available for swaps.**

**✅ What you CAN do on Anvil:**
• `swap 100 USDC to PURR`
• `swap 50 USDC to TRUMP`

**💡 For major tokens, you can:**
• **Check prices:** "what's the price of ETH?"
• **Buy crypto:** "buy ETH" (fiat on-ramp)
• **Use external DEXs:** Uniswap, 1inch
"""
```

---

## Logging

### Debug Statements

```python
# Throughout swap_workflow_agent.py
logger.info(f"[SwapWorkflow] Processing step={step}, message={message.value[:50]}...")
logger.info(f"[SwapWorkflow] Restart detected - resetting state")
logger.info(f"[SwapWorkflow] Fetching quote: {amount} {from_token} → {to_token}")
logger.info(f"[SwapWorkflow] Using Hyperliquid Spot for meme token swap")
logger.info(f"[SwapWorkflow] User has insufficient funds: ${balance:.2f}")
logger.info(f"[SwapWorkflow] Not advancing to confirm - user needs funding")
logger.warning(f"[SwapWorkflow] Hyperliquid quote failed: {error}")
logger.warning(f"[SwapWorkflow] Failed to fetch token prices: {e}")
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/workflows/test_swap_workflow_agent.py -v

# Integration tests
pytest tests/integration/test_swap_workflow.py -v

# Hyperliquid client tests
pytest tests/integration/test_hyperliquid_client.py -v

# All workflow tests
pytest tests/ -k swap -v
```

### Test Cases

```python
# Token parsing
def test_extract_swap_params_full():
    params = await agent._extract_swap_params("swap 100 USDC to PURR")
    assert params["from_token"] == "USDC"
    assert params["to_token"] == "PURR"
    assert params["amount"] == "100"

def test_extract_swap_params_partial():
    params = await agent._extract_swap_params("swap 100 USDC")
    assert params["from_token"] == "USDC"
    assert params["amount"] == "100"
    assert "to_token" not in params or not params["to_token"]

# Provider detection
def test_is_hyperliquid_swap_meme_token():
    assert agent._is_hyperliquid_swap("USDC", "PURR") == True
    assert agent._is_hyperliquid_swap("TRUMP", "USDC") == True

def test_is_hyperliquid_swap_major_token():
    assert agent._is_hyperliquid_swap("ETH", "USDC") == False
    assert agent._is_hyperliquid_swap("USDC", "BTC") == False

# Balance awareness
def test_needs_funding_recommendation_empty():
    context = UserContext(portfolio_state="empty", total_balance_usd=0)
    assert context.needs_funding_recommendation == True

def test_needs_funding_recommendation_funded():
    context = UserContext(portfolio_state="established", total_balance_usd=500)
    assert context.needs_funding_recommendation == False
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Token parsing | < 100ms | LLM + regex fallback |
| Quote fetch | < 500ms | Hyperliquid real-time |
| Price enrichment | < 300ms | CoinGecko parallel |
| Total response | < 2s | All steps combined |

### Optimization Techniques

1. **Parallel price fetching**: CoinGecko bulk API
2. **Regex fallback**: Skip LLM when possible
3. **In-memory caching**: Token prices 30s TTL
4. **Early validation**: Check tokens before quote

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added Hyperliquid Spot |
| 2026-01-29 | Added balance awareness |
| 2026-01-29 | Added token selection flow |
| 2026-01-29 | Added user-friendly errors |

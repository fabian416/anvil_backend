# Swap Workflow Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **SWAP_WORKFLOW** agent, providing meme token swaps via Hyperliquid Spot with zero gas fees.

### Key Components

- **SwapWorkflowAgent**: Multi-step workflow orchestrator
- **HyperliquidClient**: Primary swap provider
- **Balance Awareness**: User context validation
- **Provider Routing**: Intelligent provider selection

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SWAP WORKFLOW ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   conversations_router   │
                    │  POST /{id}/messages     │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Application Layer      │
                    │   (Supervisor Command)   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ AuthenticatedSupervisor  │
                    │   Coordinator            │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│  Detect       │    │   Route to        │    │   Execute       │
│  Intent       │    │   swap_workflow   │    │   Agent         │
└───────────────┘    └──────────┬────────┘    └─────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  SwapWorkflowAgent   │
                    │  (Infrastructure)    │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Hyperliquid  │    │   CoinGecko      │    │   1inch/LiFi    │
│  Spot Client  │    │   Client         │    │   (Fallback)    │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Workflow Agents (multi-step operations for authenticated users)
    SWAP_WORKFLOW = "swap_workflow"  # Multi-step swap workflow
```

### Workflow State

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py`

```python
class WorkflowStep(Enum):
    PARSE_REQUEST = "parse_request"
    FETCH_DATA = "fetch_data"
    CONFIRM = "confirm"
    EXECUTE = "execute"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowState:
    step: str = WorkflowStep.PARSE_REQUEST.value
    data: dict = field(default_factory=dict)
    confirmed: bool = False
    cancelled: bool = False
    execute_data: dict | None = None
    error: str | None = None
```

### User Context

```python
@dataclass
class UserContext:
    is_authenticated: bool = False
    wallet_address: str | None = None
    language: str = "en"
    total_balance_usd: float = 0.0
    portfolio_state: str = "empty"  # empty, starter, established

    @property
    def needs_funding_recommendation(self) -> bool:
        """Check if user needs help funding their wallet."""
        return self.portfolio_state == "empty" or self.total_balance_usd < 1.0
```

---

## Application Layer

### Supervisor Integration

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
"""
5. SWAP EXECUTION (CRITICAL - Multi-step workflow):
   - "swap X to Y", "exchange X for Y", "convert X to Y" → "swap_workflow"
   - The swap_workflow agent handles the COMPLETE process autonomously
   - Use when user wants to EXECUTE a swap (has specific amount)
   - Examples: "swap 1 ETH to USDC", "exchange 100 USDC for PURR"
   - DO NOT combine with other agents - it handles everything internally
"""
```

### Routing Examples

```python
"swap 1 ETH to USDC" → {{"tasks":[{{"agent_type":"swap_workflow"}}]}}
"exchange 100 USDC for ETH" → {{"tasks":[{{"agent_type":"swap_workflow"}}]}}
"convert 0.5 ETH to DAI" → {{"tasks":[{{"agent_type":"swap_workflow"}}]}}
"best swap rate ETH to USDC" → {{"tasks":[{{"agent_type":"hunter_ai"}}]}}
```

---

## Infrastructure Layer

### SwapWorkflowAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py`

**Lines**: ~1,722

```python
class SwapWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step swap workflow agent.
    
    Steps:
    1. parse_request: Extract from_token, to_token, amount, chain
    2. fetch_data: Get quotes from appropriate provider
    3. confirm: Show quote, wait for user confirmation
    4. execute: Generate execute_data for frontend
    
    Features:
    - Intelligent provider routing based on token type
    - Meme token swaps via Hyperliquid Spot (zero gas fees)
    - Same-chain major token swaps via 1inch
    - Cross-chain swaps via LiFi
    - User modification support
    - Multi-language support
    """
```

### Key Methods

| Method | Purpose | Step |
|--------|---------|------|
| `process_step()` | Main step router | All |
| `_handle_parse_request()` | Extract swap params | 1 |
| `_handle_token_selection()` | Interactive token picker | 1.5 |
| `_handle_fetch_quote()` | Get quote, check balance | 2 |
| `_handle_confirm()` | User intent parsing | 3 |
| `_handle_execute()` | Generate execute_data | 4 |
| `_is_hyperliquid_swap()` | Check token support | Util |
| `_fetch_quote()` | Provider routing | Util |
| `_check_unsupported_tokens()` | Validate tokens | Util |
| `_get_funding_recommendation()` | Balance message | Util |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway | None = None,      # Parameter extraction
    oneinch_client: OneInchClient | None = None,     # Major token fallback
    lifi_client: LiFiClient | None = None,           # Cross-chain fallback
    coingecko_client: CoinGeckoClient | None = None, # Price enrichment
    hyperliquid_client: HyperliquidClient | None = None,  # Primary provider
):
```

---

## Provider Routing Logic

### Decision Flow

```python
async def _fetch_quote(self, from_token, to_token, amount, chain, to_chain, wallet):
    """
    Provider Selection:
    1. Hyperliquid Spot: For meme tokens (PURR, TRUMP, etc.) paired with USDC
    2. 1inch: For major tokens same-chain swaps
    3. LiFi: For cross-chain swaps
    """
    
    is_cross_chain = to_chain and to_chain.lower() != chain.lower()
    
    # Route 1: Hyperliquid for meme tokens
    if self._is_hyperliquid_swap(from_token, to_token) and not is_cross_chain:
        if self._hyperliquid:
            quote = await self._hyperliquid.get_spot_quote(...)
            return {
                "output_amount": quote.to_amount,
                "price_impact": quote.spread_bps / 100,
                "gas_estimate": 0,  # Zero gas!
                "aggregator": "hyperliquid",
            }
    
    # Route 2: Cross-chain via LiFi
    if is_cross_chain:
        if self._lifi:
            quote = await self._lifi.get_quote(...)
            return {..., "aggregator": "lifi"}
    
    # Route 3: Same-chain major tokens via 1inch
    if self._oneinch:
        quote = await self._oneinch.get_swap_quote(...)
        return {..., "aggregator": "1inch"}
```

### Hyperliquid Swap Detection

```python
HYPERLIQUID_SPOT_TOKENS = {
    "USDC",  # Quote currency (required)
    "PURR", "HFUN", "TRUMP", "PEPE", "MOG", "POINTS", "JEFF",
    "GMEOW", "LICK", "MANLET", "SIX", "WAGMI", "CAPPY",
    # ... 50+ meme tokens
}

def _is_hyperliquid_swap(self, from_token, to_token):
    """
    Check if swap should use Hyperliquid Spot.
    
    Requirements:
    - One token MUST be USDC
    - Other token must be a supported meme token
    """
    from_upper = from_token.upper()
    to_upper = to_token.upper()
    
    # Check if one is USDC and other is meme token
    if from_upper == "USDC" and to_upper in HYPERLIQUID_SPOT_TOKENS:
        return True
    if to_upper == "USDC" and from_upper in HYPERLIQUID_SPOT_TOKENS:
        return True
    
    return False
```

---

## Balance Awareness

### Check Flow

```python
async def _handle_fetch_quote(self, message, state, user_context):
    # Check user balance BEFORE fetching quote
    funding_recommendation = ""
    if user_context.needs_funding_recommendation:
        logger.info(f"User has insufficient funds: ${user_context.total_balance_usd:.2f}")
        funding_recommendation = self._get_funding_recommendation(from_token, language)
    
    # Fetch quote (still show for reference)
    quote_result = await self._fetch_quote(...)
    
    # Only advance to confirm if user has funds
    if not user_context.needs_funding_recommendation:
        state.step = WorkflowStep.CONFIRM.value
    else:
        # Stay in parse_request - user needs to fund first
        state.step = WorkflowStep.PARSE_REQUEST.value
    
    # Format response with funding recommendation prepended
    response = self._format_quote_response(state.data, language)
    if funding_recommendation:
        response = funding_recommendation + "\n" + response
    
    return response, state
```

### Funding Recommendation

```python
def _get_funding_recommendation(self, from_token: str, language: str) -> str:
    """Helpful message for users with insufficient funds."""
    return f"""💡 **Heads up:** Your portfolio appears to have limited funds.

To complete this swap, you'll need **{from_token}** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer {from_token} from another wallet

Here's the swap quote you requested:
"""
```

### Execution Block

```python
async def _handle_execute(self, message, state, user_context):
    # Block execution if insufficient funds
    if user_context.needs_funding_recommendation:
        logger.info(f"Blocking execution - insufficient funds")
        response = self._build_insufficient_balance_message(...)
        state.error = "insufficient_balance"
        # NO execute_data generated
        return response, state
    
    # User has funds - generate execute_data
    execute_data = self._build_execute_data(...)
    state.execute_data = execute_data
    state.step = WorkflowStep.COMPLETED.value
    
    return self._format_execute_response(...), state
```

---

## Token Selection Flow

### Trigger Condition

```python
# If user provides USDC + amount but no destination token
if from_token == "USDC" and amount and not to_token:
    state.data["awaiting_token_selection"] = True
    response = await self._get_token_selection_prompt(...)
    return response, state
```

### Selection Prompt

```python
async def _get_token_selection_prompt(self, from_token, amount, user_context):
    # Fetch prices for popular tokens
    prices = await self._fetch_token_prices()
    
    # Build numbered list
    token_lines = []
    for i, (symbol, description) in enumerate(POPULAR_MEME_TOKENS, 1):
        price_info = f" • ${prices.get(symbol.lower(), 0):,.6f}"
        token_lines.append(f"**{i}.** {symbol}{price_info}")
    
    return f"""🔄 **Swap {amount} {from_token}**

**Select a meme token to receive:**

{token_list}

**Reply with:**
• A number (1-10) to select
• Or type the token name (e.g., PURR)
"""
```

### Handle Selection

```python
async def _handle_token_selection(self, message, state, user_context):
    user_input = message.value.strip().upper()
    
    selected_token = None
    
    # Number selection (1-10)
    if user_input.isdigit():
        index = int(user_input) - 1
        if 0 <= index < len(POPULAR_MEME_TOKENS):
            selected_token = POPULAR_MEME_TOKENS[index][0]
    
    # Direct symbol entry
    if not selected_token and user_input in HYPERLIQUID_SPOT_TOKENS:
        selected_token = user_input
    
    if selected_token:
        state.data["to_token"] = selected_token
        state.step = WorkflowStep.FETCH_DATA.value
        return await self._handle_fetch_quote(message, state, user_context)
    else:
        # Invalid - show menu again
        return self._get_invalid_selection_response(user_input, language), state
```

---

## Restart Detection

```python
async def process_step(self, message, state, user_context):
    step = state.step
    text_lower = message.value.lower().strip()
    
    # Check for NEW swap request (restart detection)
    if step not in (PARSE_REQUEST, CANCELLED, COMPLETED):
        restart_keywords = [
            "swap", "exchange", "trade", "cambiar", "trocar",
            "i want to swap", "quiero cambiar",
        ]
        is_restart = any(kw in text_lower for kw in restart_keywords)
        
        if is_restart:
            logger.info("Restart detected - resetting state")
            state = WorkflowState()
            state.step = WorkflowStep.PARSE_REQUEST.value
            return await self._handle_parse_request(message, state, user_context)
```

---

## Error Handling

### Quote Errors

```python
def _get_quote_error_response(self, error, language):
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
        reason = "Unable to get a quote at this time."
    
    return f"""⚠️ **Swap Quote Unavailable**

{reason}

**What you can try:**
• Check if the token is available on this network
• Try a different token pair
• Try again in a moment
"""
```

### Unsupported Tokens

```python
def _check_unsupported_tokens(self, from_token, to_token, language):
    """Check if tokens are supported on Hyperliquid Spot."""
    from_supported = from_token in HYPERLIQUID_SPOT_TOKENS
    to_supported = to_token in HYPERLIQUID_SPOT_TOKENS
    
    if not from_supported or not to_supported:
        return self._build_unsupported_message(...)
    
    # One token must be USDC
    if from_token != "USDC" and to_token != "USDC":
        return self._build_usdc_required_message(...)
    
    return None  # Tokens are valid
```

---

## Logging

### Debug Logging

```python
logger.info(f"[SwapWorkflow] Processing step={step}, message={message.value[:50]}...")
logger.info(f"[SwapWorkflow] Fetching quote: {amount} {from_token} → {to_token}")
logger.info(f"[SwapWorkflow] Using Hyperliquid Spot for meme token swap")
logger.warning(f"[SwapWorkflow] Hyperliquid quote failed: {error}")
logger.info(f"[SwapWorkflow] Restart detected - user starting new swap flow")
```

### Enable Debug Mode

```python
import logging
logging.getLogger("app.infrastructure.adapters.agent_squad.agents.workflows").setLevel(logging.DEBUG)
```

---

## Testing

### Unit Tests

```python
def test_hyperliquid_swap_detection():
    agent = SwapWorkflowAgent(...)
    
    # Valid Hyperliquid swaps
    assert agent._is_hyperliquid_swap("USDC", "PURR") == True
    assert agent._is_hyperliquid_swap("TRUMP", "USDC") == True
    
    # Invalid - major tokens
    assert agent._is_hyperliquid_swap("ETH", "USDC") == False
    assert agent._is_hyperliquid_swap("USDC", "BTC") == False
    
    # Invalid - no USDC
    assert agent._is_hyperliquid_swap("PURR", "TRUMP") == False

def test_balance_awareness():
    agent = SwapWorkflowAgent(...)
    
    # Empty portfolio
    context = UserContext(portfolio_state="empty", total_balance_usd=0)
    assert context.needs_funding_recommendation == True
    
    # Funded portfolio
    context = UserContext(portfolio_state="established", total_balance_usd=500)
    assert context.needs_funding_recommendation == False
```

### Integration Tests

```bash
# Run swap workflow tests
pytest tests/integration/test_swap_workflow.py -v

# Run Hyperliquid client tests
pytest tests/integration/test_hyperliquid_client.py -v
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Token parsing | < 100ms | ~50ms |
| Hyperliquid quote | < 500ms | ~300ms |
| Price enrichment | < 300ms | ~200ms |
| Total response | < 2s | ~1s |

### Caching Strategy

| Data Type | TTL | Storage |
|-----------|-----|---------|
| Token prices | 30s | In-memory |
| Order book | Real-time | No cache |
| Token list | 5min | In-memory |

---

## Dependencies

### Required

```
httpx>=0.25.0       # HTTP client
web3>=6.0.0         # Ethereum (fallback)
```

### Optional

```
hyperliquid-python  # Hyperliquid API
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added Hyperliquid Spot integration |
| 2026-01-29 | Added balance awareness |
| 2026-01-29 | Added token selection flow |
| 2026-01-29 | Added unsupported token handling |

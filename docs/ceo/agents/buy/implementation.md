# Buy Workflow Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.BUY_WORKFLOW
│   └── services/
│       └── agent_squad/
│           └── authenticated_supervisor.py  # Routing rules
│
├── infrastructure/
│   └── adapters/
│       └── agent_squad/
│           └── agents/
│               └── workflows/
│                   ├── base_workflow_agent.py   # Base class
│                   └── buy_workflow_agent.py    # Main agent
│
├── setup/
│   └── ioc/
│       └── agent_squad_infrastructure.py   # DI registration
│
└── application/
    └── chat/
        └── commands/
            └── send_message_with_supervisor.py  # Entry point
```

---

## Core Files

### 1. BuyWorkflowAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py`
**Lines**: ~883

#### Class Definition

```python
class BuyWorkflowAgent(BaseWorkflowAgent):
    """
    AGNO-based multi-step crypto purchase workflow agent.
    
    Steps:
    1. parse_request: Extract crypto, fiat amount, and currency
    2. validate: Check supported assets and prepare purchase
    3. confirm: Show purchase details, wait for confirmation
    4. execute: Generate execute_data for Privy modal
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 86-96 | Initialize with LLM client |
| `process_step` | 106-159 | Main step router |
| `_handle_parse_request` | 165-233 | Extract buy params |
| `_extract_buy_params` | 344-391 | Parse amount, crypto, fiat |
| `_handle_validate` | 235-275 | Validate crypto is USDC |
| `_handle_confirm` | 277-323 | User confirmation |
| `_handle_execute` | 325-338 | Generate execute_data |
| `_format_usdc_only_message` | 419-472 | Redirect unsupported |
| `_ask_for_usdc_amount` | 474-539 | Prompt for amount |
| `_format_buy_review` | 618-694 | Show purchase details |
| `_build_buy_execute_data` | 823-849 | Create Privy payload |
| `_is_confirmation` | 855-863 | Detect "yes" |
| `_is_cancellation` | 865-883 | Detect "no" |

#### Token Configuration

```python
# Lines 43-47
# Supported cryptocurrencies for purchase (USDC only)
SUPPORTED_CRYPTOS = {
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
}

# Lines 49-59
# Unsupported cryptos - used for friendly error messages
UNSUPPORTED_CRYPTOS = {
    "eth": {"symbol": "ETH", "name": "Ethereum", "emoji": "Ξ"},
    "usdt": {"symbol": "USDT", "name": "Tether", "emoji": "💵"},
    "btc": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
    "bitcoin": {"symbol": "BTC", "name": "Bitcoin", "emoji": "₿"},
    "sol": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
    "solana": {"symbol": "SOL", "name": "Solana", "emoji": "◎"},
    "matic": {"symbol": "MATIC", "name": "Polygon", "emoji": "🟣"},
    "polygon": {"symbol": "MATIC", "name": "Polygon", "emoji": "🟣"},
}

# Lines 62-65
# Supported fiat currencies
SUPPORTED_FIATS = {"USD", "EUR", "GBP", "CAD", "AUD"}

# Supported networks
SUPPORTED_NETWORKS = ["Base", "Ethereum", "Polygon", "Arbitrum"]
```

---

### 2. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_buy_workflow_agent(
    self,
    llm_client: LLMClientGateway,
) -> BuyWorkflowAgent:
    """
    Provide Buy Workflow Agent for authenticated users.
    
    This agent handles multi-step crypto purchase operations:
    1. Parse buy request (crypto, fiat amount, currency)
    2. Validate supported assets
    3. Show purchase review and wait for confirmation
    4. Generate execute_data for Privy modal
    
    Integrations:
    - Privy SDK for MoonPay/Coinbase on-ramp
    """
    return BuyWorkflowAgent(llm_client=llm_client)
```

---

### 3. Supervisor Routing

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
# Lines 1027-1033
"""
11. BUY CRYPTO EXECUTION (CRITICAL - Multi-step workflow):
    - "buy $100 of ETH", "purchase crypto", "buy USDC with card" → "buy_workflow"
    - The buy_workflow agent handles the COMPLETE multi-step purchase process
    - Use when user wants to BUY crypto with fiat (card, Apple Pay, etc.)
    - Examples: "buy $50 of ETH", "purchase 100 dollars of USDC", "buy crypto"
    - DO NOT combine with other agents - it handles everything internally
"""

# Example mappings
"buy $100 of ETH" → {{"tasks":[{{"agent_type":"buy_workflow"}}]}}
"purchase 50 dollars of USDC" → {{"tasks":[{{"agent_type":"buy_workflow"}}]}}
"buy crypto" → {{"tasks":[{{"agent_type":"buy_workflow"}}]}}
```

---

## Amount Parsing Implementation

### Extract Buy Params

```python
# Lines 344-391
async def _extract_buy_params(self, text: str) -> dict[str, Any]:
    """Extract buy parameters from text.
    
    Returns only explicitly found parameters. Does NOT default values.
    """
    params: dict[str, Any] = {}
    
    # Regex for amount (with currency symbols)
    amount_match = re.search(
        r"(?:[\$€£])?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:dollars?|usd|eur|gbp)?",
        text,
        re.I,
    )
    if amount_match:
        amount_value = amount_match.group(1).replace(",", "")
        params["amount"] = amount_value
    
    # Detect fiat currency
    if "$" in text or "dollar" in text or "usd" in text:
        params["fiat"] = "USD"
    elif "€" in text or "euro" in text or "eur" in text:
        params["fiat"] = "EUR"
    elif "£" in text or "pound" in text or "gbp" in text:
        params["fiat"] = "GBP"
    
    # Check for USDC (only supported crypto)
    if re.search(r'\busdc\b', text, re.I):
        params["crypto"] = "USDC"
    else:
        # Check for unsupported cryptos
        for key, info in UNSUPPORTED_CRYPTOS.items():
            if re.search(rf'\b{re.escape(key)}\b', text, re.I):
                params["unsupported_crypto"] = info["symbol"]
                break
    
    return params
```

### Amount Format Examples

| Input | Result |
|-------|--------|
| `"$100"` | `{"amount": "100", "fiat": "USD"}` |
| `"100 dollars"` | `{"amount": "100", "fiat": "USD"}` |
| `"€50"` | `{"amount": "50", "fiat": "EUR"}` |
| `"buy 1000"` | `{"amount": "1000"}` |
| `"buy eth"` | `{"unsupported_crypto": "ETH"}` |
| `"buy usdc"` | `{"crypto": "USDC"}` |

---

## Execute Data Structure

### Build Execute Data

```python
# Lines 823-849
def _build_buy_execute_data(
    self,
    crypto: str,
    amount: str,
    fiat: str,
    wallet_address: str | None,
) -> dict[str, Any]:
    """Build execute_data for buy action.
    
    Uses standard ExecuteActionData fields for API consistency:
    - to_token: The crypto being purchased
    - amount: The fiat amount to spend
    - from_token: The fiat currency (USD, EUR, etc.)
    """
    return {
        "action_type": "buy",
        "provider": "privy",
        "chain": "base",
        "to_token": crypto.upper(),      # USDC
        "amount": str(amount),            # Fiat amount
        "from_token": fiat.upper(),       # USD, EUR, etc.
        "recipient": wallet_address,      # Destination wallet
        "quote_id": f"buy-{crypto.lower()}-{amount}",
    }
```

### Execute Data Example

```json
{
  "action_type": "buy",
  "provider": "privy",
  "chain": "base",
  "to_token": "USDC",
  "amount": "100",
  "from_token": "USD",
  "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "quote_id": "buy-usdc-100"
}
```

---

## Response Formatting

### Purchase Review

```python
# Lines 618-694
def _format_buy_review(self, data: dict, language: str) -> str:
    crypto = data.get("crypto", "USDC")
    amount = data.get("amount", "0")
    fiat = data.get("fiat", "USD")
    
    crypto_info = SUPPORTED_CRYPTOS.get(crypto.lower(), {"emoji": "💵"})
    emoji = crypto_info.get("emoji", "💵")
    
    currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "C$", "AUD": "A$"}
    symbol = currency_symbols.get(fiat, "$")
    
    return f"""💳 **Review Your Purchase**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Buying:** {crypto} {emoji}
💵 **Amount:** {symbol}{amount} {fiat}
🌐 **Network:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Payment Options:**
• Credit/Debit Card
• Apple Pay / Google Pay
"""
```

### USDC Only Message

```python
# Lines 419-472
def _format_usdc_only_message(self, requested_crypto: str, language: str) -> str:
    return f"""💡 **USDC Only Available**

I see you want to buy **{requested_crypto}**, but currently only **USDC** 
is available for direct purchase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Here's a tip:** You can buy USDC first, then swap it for {requested_crypto} instantly!

Would you like to buy USDC instead?

💬 Just tell me how much (e.g., "$100" or "500 dollars")
"""
```

---

## Confirmation Handling

### Is Confirmation

```python
# Lines 855-863
def _is_confirmation(self, text: str) -> bool:
    confirm_words = [
        "yes", "y", "confirm", "ok", "proceed", "continue", "do it", "buy",
        "sí", "si", "confirmar", "vale", "continuar", "comprar",
        "sim", "confirmar", "prosseguir",
        "是", "确认", "好", "继续", "购买",
    ]
    return any(word in text for word in confirm_words)
```

### Is Cancellation

```python
# Lines 865-883
def _is_cancellation(self, text: str) -> bool:
    """Check if text is a cancellation using word boundary matching."""
    import re
    
    # Single-character and exact-match words (use word boundaries)
    cancel_patterns = [
        r'\bno\b', r'\bn\b', r'\bcancel\b', r'\babort\b', r'\bstop\b',
        r'\bnevermind\b', r'\bforget it\b',
        r'\bcancelar\b', r'\babortar\b', r'\bparar\b',
    ]
    
    if any(re.search(pattern, text) for pattern in cancel_patterns):
        return True
    
    # For CJK characters (no word boundaries)
    cjk_cancel_words = ["取消", "不", "停止"]
    return any(word in text for word in cjk_cancel_words)
```

---

## Logging

### Debug Statements

```python
logger.info(f"[BuyWorkflow] Processing step={step}, message={message.value[:50]}...")
logger.info(f"[BuyWorkflow] Parse request - existing_crypto={existing_crypto}, existing_amount={existing_amount}, message={text[:30]}")
logger.info(f"[BuyWorkflow] Using existing parameters from state, proceeding to validate")
logger.info(f"[BuyWorkflow] User requested unsupported crypto: {unsupported_crypto}")
logger.info(f"[BuyWorkflow] Parameters complete: {crypto} {amount} {fiat}, proceeding to validate")
logger.info(f"[BuyWorkflow] Have crypto={crypto}, asking for amount")
logger.info(f"[BuyWorkflow] Have amount={amount}, defaulting to USDC")
logger.info(f"[BuyWorkflow] No parameters detected, asking for USDC amount")
logger.info(f"[BuyWorkflow] Restart detected - user starting new buy flow, resetting state")
logger.info(f"[BuyWorkflow] Extracted params: {params}")
logger.warning(f"[BuyWorkflow] Unknown step: {step}")
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/workflows/test_buy_workflow_agent.py -v

# Integration tests
pytest tests/integration/test_buy_workflow.py -v

# All workflow tests
pytest tests/ -k buy -v
```

### Test Cases

```python
# Amount parsing
def test_extract_amount_dollar_sign():
    params = await agent._extract_buy_params("buy $100")
    assert params["amount"] == "100"
    assert params["fiat"] == "USD"

def test_extract_amount_written():
    params = await agent._extract_buy_params("buy 50 dollars")
    assert params["amount"] == "50"
    assert params["fiat"] == "USD"

def test_extract_amount_euro():
    params = await agent._extract_buy_params("buy €75")
    assert params["amount"] == "75"
    assert params["fiat"] == "EUR"

# Crypto detection
def test_extract_usdc():
    params = await agent._extract_buy_params("buy usdc")
    assert params["crypto"] == "USDC"

def test_detect_unsupported_crypto():
    params = await agent._extract_buy_params("buy eth")
    assert params["unsupported_crypto"] == "ETH"

# Confirmation
def test_confirmation_yes():
    assert agent._is_confirmation("yes") == True
    assert agent._is_confirmation("confirmar") == True
    assert agent._is_confirmation("是") == True

def test_cancellation_no():
    assert agent._is_cancellation("no") == True
    assert agent._is_cancellation("cancel") == True
    assert agent._is_cancellation("取消") == True
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Parse params | < 100ms | Regex only (no LLM) |
| Validation | < 50ms | Dict lookup |
| Total response | < 500ms | All steps combined |

### Optimization Notes

- No external API calls during workflow (Privy is frontend-only)
- Regex parsing preferred over LLM for simple extraction
- State persistence via conversation context

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | USDC-only constraint added |
| 2026-01-29 | Smart redirection for unsupported cryptos |
| 2026-01-29 | Multi-language support |

# Portfolio Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.PORTFOLIO
│   ├── ports/
│   │   └── agent_squad/
│   │       └── agent_gateway.py          # AgentGateway interface
│   └── services/
│       └── agent_squad/
│           └── authenticated_supervisor.py  # Routing rules
│
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── portfolio_agent.py    # Main agent
│       └── external/
│           └── coingecko_client.py       # Price API
│
├── application/
│   └── chat/
│       ├── commands/
│       │   └── send_message_with_supervisor.py  # Entry point
│       └── services/
│           └── user_data_service.py      # Portfolio data
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. PortfolioAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/portfolio_agent.py`
**Lines**: ~438

#### Class Definition

```python
class PortfolioAgent:
    """
    Portfolio Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Portfolio optimization & rebalancing
    
    Capabilities:
    - Modern Portfolio Theory (MPT) optimization
    - Risk-adjusted returns
    - Efficient frontier analysis
    - Rebalancing recommendations
    - Diversification analysis
    - Correlation analysis
    - Sharpe ratio optimization
    
    Model: gemini-2.0-flash (Vertex AI)
    Temperature: 0.3 (balanced)
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 45-67 | Initialize with LLM and CoinGecko |
| `agent_type` | 69-72 | Return AgentType.PORTFOLIO |
| `execute` | 74-245 | Main entry point |
| `is_available` | 247-249 | Availability check |
| `_extract_user_context` | 251-277 | Get portfolio from context |
| `_build_portfolio_context` | 279-367 | Format holdings string |
| `_get_authenticated_system_prompt` | 369-392 | Auth user prompt |
| `_get_system_prompt` | 394-437 | Guest user prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    coingecko_client: Any | None = None,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 2000,
):
    self._llm_client = llm_client
    self._coingecko_client = coingecko_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_portfolio_agent(
    self,
    llm_client: LLMClientGateway,
    coingecko_client: CoinGeckoClient | None,
) -> PortfolioAgent:
    """Provide Portfolio agent with optional CoinGecko integration."""
    return PortfolioAgent(
        llm_client=llm_client,
        coingecko_client=coingecko_client,
    )
```

---

### 3. Supervisor Routing

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
# Lines 976-980
"""
4. PORTFOLIO (authenticated - REAL data):
   - "my portfolio", "my balance", "my holdings" → "portfolio" agent
   - "portfolio value", "total holdings" → "portfolio" agent
"""

# Lines 1076-1084
"""
18. PORTFOLIO ANALYSIS (authenticated - use REAL data):
    - Portfolio rebalancing suggestions → "portfolio" + "hunter_ai"
    - Risk-adjusted recommendations → "portfolio" + "risk_analyzer"
    - "Should I rebalance my portfolio" → "portfolio" + "hunter_ai"
    - Allocation optimization → "portfolio" + "defi_yield"
"""

# Example mappings
"my portfolio" → {{"tasks":[{{"agent_type":"portfolio"}}]}}
"my balance" → {{"tasks":[{{"agent_type":"portfolio"}}]}}
"I have 70% ETH and 30% BTC. Should I rebalance?" → {{"tasks":[
    {{"agent_type":"portfolio"}},
    {{"agent_type":"hunter_ai", "depends_on":["portfolio"]}}
]}}
```

---

## User Context Extraction

### Implementation

```python
# Lines 251-277
def _extract_user_context(self, conversation_context: ConversationContext) -> dict | None:
    """Extract user context from conversation metadata."""
    if not conversation_context.user_metadata:
        return None
    
    # Check for user_context or direct portfolio data
    if "user_context" in conversation_context.user_metadata:
        return conversation_context.user_metadata["user_context"]
    
    # Check for direct portfolio data
    if "portfolio" in conversation_context.user_metadata:
        return conversation_context.user_metadata
    
    # Check for flat structure (supervisor injection)
    if conversation_context.user_metadata.get("is_authenticated"):
        return {
            "user_id": conversation_context.user_metadata.get("user_id"),
            "wallet_address": conversation_context.user_metadata.get("wallet_address"),
            "portfolio_summary": conversation_context.user_metadata.get("portfolio_summary"),
            "primary_wallet": {
                "address": conversation_context.user_metadata.get("wallet_address"),
                "chain_type": conversation_context.user_metadata.get("wallet_chain"),
            } if conversation_context.user_metadata.get("wallet_address") else None,
        }
    
    return None
```

### Context Injection (Supervisor)

```python
# From authenticated_supervisor.py lines 1205-1217
if self._context_aware:
    if conversation_context.user_metadata is None:
        conversation_context.user_metadata = {}
    conversation_context.user_metadata["portfolio_state"] = self._context_aware.portfolio_state
    conversation_context.user_metadata["total_balance_usd"] = float(self._context_aware.total_balance_usd or 0)
    conversation_context.user_metadata["has_connected_wallet"] = self._context_aware.has_connected_wallet
```

---

## Portfolio Context Building

### Implementation

```python
# Lines 279-367
def _build_portfolio_context(self, user_context: dict) -> str:
    """Build portfolio context string from user data.
    
    Same format as wallet agent: balance-based message with suggestions.
    Do NOT show wallet address here (use wallet agent for that).
    """
    lines = []
    
    portfolio = user_context.get("portfolio", {})
    portfolio_summary = user_context.get("portfolio_summary", {})
    
    # Get total balance
    total_value = 0
    if portfolio_summary:
        total_value = float(portfolio_summary.get("total_value_usd", 0) or 0)
    elif portfolio:
        if hasattr(portfolio, "total_value_usd"):
            total_value = portfolio.total_value_usd or 0
        else:
            total_value = portfolio.get("total_value_usd", 0) or 0
    
    # Empty portfolio - same format as wallet: recommend buy/receive
    if not portfolio or total_value == 0:
        lines.append("**Total Balance:** $0.00")
        lines.append("")
        lines.append("**🚀 Get Started:**")
        lines.append("")
        lines.append("Your portfolio is empty. Add funds to get started:")
        lines.append("")
        lines.append("• 💳 **Buy crypto** - Say \"buy crypto\" to purchase USDC")
        lines.append("• 📥 **Receive crypto** - Transfer tokens from another wallet")
        lines.append("")
        lines.append("Once you have funds you can:")
        lines.append("• 🔄 **Swap** - Trade between cryptocurrencies")
        lines.append("• 💰 **Earn yield** - Deposit into DeFi protocols")
        return "\n".join(lines)
    
    # Funded portfolio
    lines.append(f"**Portfolio Value:** ${total_value:,.2f}")
    lines.append(f"**Token Count:** {token_count}")
    
    if chains:
        lines.append(f"**Chains:** {', '.join(chains)}")
    
    if top_holdings:
        lines.append("\n**Top Holdings:**")
        for holding in top_holdings[:5]:
            symbol = holding.get("symbol", "Unknown")
            amount = holding.get("amount", 0)
            value_usd = holding.get("value_usd", 0)
            lines.append(f"- {symbol}: {amount:,.4f} (${value_usd:,.2f})")
    
    # Suggestions based on balance
    lines.append("")
    lines.append("**💡 What you can do:**")
    
    # Check for stablecoins
    stablecoin_symbols = {"USDC", "USDT", "DAI"}
    has_stablecoins = any(
        h.get("symbol", "").upper() in stablecoin_symbols 
        for h in top_holdings
    )
    
    if has_stablecoins:
        lines.append("• 💰 **Earn yield** - Say \"deposit USDC\" or \"compare USDC rates\"")
    lines.append("• 🔄 **Swap** - Say \"swap\" to trade between cryptocurrencies")
    if total_value < 100:
        lines.append("• 💳 **Buy more** - Say \"buy crypto\" to add funds")
    
    return "\n".join(lines)
```

---

## CoinGecko Integration

### Price Fetching

```python
# Lines 98-152
if self._coingecko_client:
    try:
        logger.info("🔍 Fetching real-time prices from CoinGecko for PortfolioAgent")
        
        # Token pattern matching
        token_patterns = {
            "bitcoin": "bitcoin",
            "btc": "bitcoin",
            "ethereum": "ethereum",
            "eth": "ethereum",
            "usdc": "usd-coin",
            "usdt": "tether",
            "dai": "dai",
            "wbtc": "wrapped-bitcoin",
            "sol": "solana",
            "avax": "avalanche-2",
            "matic": "matic-network",
            "polygon": "matic-network",
        }
        
        # Detect tokens from message
        for keyword, token_id in token_patterns.items():
            if keyword in message_lower and token_id not in tokens_to_fetch:
                tokens_to_fetch.append(token_id)
        
        # Default tokens if portfolio query
        if not tokens_to_fetch and any(word in message_lower for word in ["price", "prices", "portfolio", "value", "valuation"]):
            tokens_to_fetch = ["bitcoin", "ethereum", "usd-coin"]
        
        # Fetch prices
        if tokens_to_fetch:
            prices = await self._coingecko_client.get_prices_bulk(tokens_to_fetch)
            
            if prices:
                price_data_context = "\n\n**REAL-TIME TOKEN PRICES FROM COINGECKO:**\n"
                for token_id, price_data in prices.items():
                    if price_data:
                        price_data_context += f"- {token_id.upper()}: ${price_data.usd:,.2f}"
                        if price_data.change_24h is not None:
                            change_sign = "+" if price_data.change_24h >= 0 else ""
                            price_data_context += f" ({change_sign}{price_data.change_24h:.2f}% 24h)"
                        price_data_context += "\n"
                
                logger.info(f"✅ Fetched prices for {len(prices)} tokens from CoinGecko")
    
    except Exception as e:
        logger.warning(f"⚠️ Failed to fetch CoinGecko prices: {e}")
        price_data_context = ""
```

---

## System Prompts

### Authenticated User Prompt

```python
# Lines 369-392
def _get_authenticated_system_prompt(self) -> str:
    """Get system prompt for authenticated users with real data."""
    return """You are the Portfolio Optimizer for Anvil.

**CRITICAL - USE THE CONTEXT EXACTLY:**
1. Use ONLY the portfolio data provided in the context - do not invent numbers
2. For EMPTY portfolio: Use the EXACT suggestions from context (buy crypto, receive crypto)
3. For portfolio WITH holdings: Use the EXACT suggestions from context (swap, earn yield)
4. Do NOT show wallet address - that is for the wallet agent
5. Keep responses CONCISE - mirror the structure from the context

**RESPONSE FORMAT:**
- Start with balance (e.g. "Your balance: $0.00" or "Portfolio value: $X")
- Then include the suggestion bullets from the context exactly as written
- No long explanations

**DO NOT:**
- Show wallet address
- Say "buy 100 USD of ETH" - use "buy crypto"
- Make up suggestions - use only what is in the context
- Add unnecessary disclaimers"""
```

### Guest User Prompt

```python
# Lines 394-437
def _get_system_prompt(self) -> str:
    """Get system prompt for portfolio agent (guest users)."""
    return """You are the Portfolio Optimizer, Anvil's portfolio management specialist.

**CRITICAL: AUTHENTICATION REQUIREMENT**
- Portfolio features require user authentication
- If the user is NOT authenticated, inform them:
  "To view your portfolio, please sign in or create an account."
- DO NOT attempt to retrieve portfolio data for unauthenticated users

Your expertise:
- Modern Portfolio Theory (MPT) optimization
- Risk-adjusted returns maximization
- Efficient frontier analysis
- Portfolio rebalancing strategies
- Diversification analysis
- Correlation analysis
- Sharpe ratio optimization
- Risk parity strategies

For portfolio recommendations (authenticated users only), provide:
- Optimal allocation (percentages)
- Expected return (annualized)
- Expected volatility (standard deviation)
- Sharpe ratio
- Diversification score
- Rebalancing trades (if needed)
"""
```

---

## Source Attribution

### Building Sources

```python
# Lines 187-224
from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
    create_llm_source,
    create_database_source,
    create_api_source,
)

sources = []
fetched_at = datetime.now(UTC)

# Add database source (portfolio data)
sources.append(create_database_source(
    citation_text="Your portfolio data from Anvil",
    fetched_at=fetched_at,
    metadata={"query_type": "portfolio_snapshot"},
))

# Add LLM source
model_name = response.get("model", "Unknown")
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))

# Add CoinGecko source if prices were fetched
if self._coingecko_client and price_data_context:
    sources.append(create_api_source(
        source_name="CoinGecko",
        url="https://www.coingecko.com/",
        citation_text="Real-time token prices from CoinGecko",
        fetched_at=fetched_at,
    ))
```

---

## Response Building

### AgentResponse Structure

```python
# Lines 233-245
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=tools_used,
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
        "provider": provider_info,
        "is_authenticated": is_authenticated,
    },
)
```

### Tools Used

```python
# Lines 222-231
tools_used = ["llm_gateway"]
if self._coingecko_client and price_data_context:
    tools_used.append("coingecko_api")

# Add portfolio repository if we used real data
if is_authenticated and user_portfolio_context:
    tools_used.append("portfolio_repository")
```

---

## Logging

### Debug Statements

```python
logger.info(f"📊 PortfolioAgent using real user data for authenticated user")
logger.info(f"🔍 Fetching real-time prices from CoinGecko for PortfolioAgent")
logger.info(f"✅ Fetched prices for {len(prices)} tokens from CoinGecko")
logger.warning(f"⚠️ No price data returned from CoinGecko")
logger.warning(f"⚠️ Failed to fetch CoinGecko prices: {e}, continuing with LLM-only response")
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_portfolio_agent.py -v

# Integration tests
pytest tests/integration/test_portfolio_agent.py -v

# All portfolio tests
pytest tests/ -k portfolio -v
```

### Test Cases

```python
# User context extraction
def test_extract_user_context_authenticated():
    context = ConversationContext(
        user_metadata={"is_authenticated": True, "portfolio_summary": {}}
    )
    result = agent._extract_user_context(context)
    assert result is not None

def test_extract_user_context_guest():
    context = ConversationContext(user_metadata=None)
    result = agent._extract_user_context(context)
    assert result is None

# Portfolio context building
def test_build_portfolio_context_empty():
    user_context = {"portfolio": {"total_value_usd": 0}}
    result = agent._build_portfolio_context(user_context)
    assert "Total Balance: $0.00" in result
    assert "buy crypto" in result.lower()

def test_build_portfolio_context_funded():
    user_context = {
        "portfolio": {
            "total_value_usd": 1000,
            "token_count": 2,
            "top_holdings": [
                {"symbol": "USDC", "amount": 500, "value_usd": 500},
                {"symbol": "ETH", "amount": 0.25, "value_usd": 500},
            ],
        }
    }
    result = agent._build_portfolio_context(user_context)
    assert "Portfolio Value: $1,000.00" in result
    assert "earn yield" in result.lower()
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Context extraction | < 10ms | Dict lookup |
| Context building | < 50ms | String formatting |
| CoinGecko fetch | < 300ms | Async HTTP |
| LLM response | < 1s | Vertex AI |
| Total | < 1.5s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added CoinGecko integration |
| 2026-01-29 | Added context-aware suggestions |
| 2026-01-29 | Added source attribution |

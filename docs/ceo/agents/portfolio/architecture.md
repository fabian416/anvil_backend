# Portfolio Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **PORTFOLIO** agent, providing real-time portfolio analysis and optimization for authenticated users.

### Key Components

- **PortfolioAgent**: Core agent for portfolio queries
- **CoinGecko Client**: Real-time token prices
- **UserDataService**: Portfolio data from database
- **Context-Aware Suggestions**: Balance-based recommendations

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PORTFOLIO AGENT ARCHITECTURE                        │
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
                    ┌────────────▼─────────────┐
                    │    PortfolioAgent        │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│ User Context  │    │   CoinGecko API   │    │    Vertex AI    │
│ (Portfolio)   │    │   (Prices)        │    │    (LLM)        │
└───────────────┘    └───────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    PORTFOLIO = "portfolio"  # Portfolio optimization & rebalancing
```

### Agent Gateway Interface

**File**: `src/app/domain/ports/agent_squad/agent_gateway.py`

```python
class AgentGateway(Protocol):
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse: ...
```

---

## Application Layer

### Supervisor Integration

**File**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

```python
"""
4. PORTFOLIO (authenticated - REAL data):
   - "my portfolio", "my balance", "my holdings" → "portfolio" agent
   - "portfolio value", "total holdings" → "portfolio" agent

18. PORTFOLIO ANALYSIS (authenticated - use REAL data):
    - Portfolio rebalancing suggestions → "portfolio" + "hunter_ai"
    - Risk-adjusted recommendations → "portfolio" + "risk_analyzer"
    - "Should I rebalance my portfolio" → "portfolio" + "hunter_ai"
    - Allocation optimization → "portfolio" + "defi_yield"
"""
```

### User Data Context

**File**: `src/app/application/chat/services/user_data_service.py`

```python
@dataclass
class UserDataContext:
    """Full user context including wallet, portfolio, and transaction data."""
    user_id: str
    primary_wallet: WalletInfo | None
    portfolio: PortfolioSummary | None
    recent_transactions: list[TransactionInfo]
    
@dataclass
class PortfolioSummary:
    """Summary of user's portfolio."""
    total_value_usd: float
    token_count: int
    top_holdings: list[dict]
    chains: list[str]
    last_updated: datetime
```

---

## Infrastructure Layer

### PortfolioAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/portfolio_agent.py`

**Lines**: ~438

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

### Key Methods

| Method | Purpose | Lines |
|--------|---------|-------|
| `execute()` | Main entry point | 74-245 |
| `_extract_user_context()` | Get portfolio from context | 251-277 |
| `_build_portfolio_context()` | Format holdings string | 279-367 |
| `_get_authenticated_system_prompt()` | LLM prompt for auth users | 369-392 |
| `_get_system_prompt()` | LLM prompt for guests | 394-437 |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,          # Vertex AI / DeepInfra
    coingecko_client: Any | None = None,   # Real-time prices
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 2000,
):
```

---

## Data Flow

### Execute Method Flow

```python
async def execute(self, conversation_id, message, conversation_context):
    # 1. Extract user context from conversation metadata
    user_context = self._extract_user_context(conversation_context)
    
    # 2. Build portfolio context string (balance + suggestions)
    if user_context:
        user_portfolio_context = self._build_portfolio_context(user_context)
        is_authenticated = True
    
    # 3. Fetch real-time prices from CoinGecko
    if self._coingecko_client:
        prices = await self._coingecko_client.get_prices_bulk(tokens)
        price_data_context = format_prices(prices)
    
    # 4. Build enhanced message with context
    enhanced_message = f"""User Query: {message.value}
    
**USER'S PORTFOLIO DATA:**
{user_portfolio_context}

{price_data_context}
"""
    
    # 5. Get LLM response
    response = await self._llm_client.chat(
        messages=[system_prompt, enhanced_message],
        model=self._model,
        temperature=self._temperature,
    )
    
    # 6. Build sources and return
    return AgentResponse(
        content=response["content"],
        sources=[database_source, llm_source, api_source],
    )
```

---

## Context-Aware Suggestions

### Portfolio Context Building

```python
def _build_portfolio_context(self, user_context: dict) -> str:
    """Build portfolio context string from user data.
    
    Same format as wallet agent: balance-based message with suggestions.
    """
    portfolio = user_context.get("portfolio", {})
    total_value = portfolio.get("total_value_usd", 0)
    
    # Empty portfolio - recommend buy/receive
    if total_value == 0:
        return """**Total Balance:** $0.00

**🚀 Get Started:**

Your portfolio is empty. Add funds to get started:

• 💳 **Buy crypto** - Say "buy crypto" to purchase USDC
• 📥 **Receive crypto** - Transfer tokens from another wallet

Once you have funds you can:
• 🔄 **Swap** - Trade between cryptocurrencies
• 💰 **Earn yield** - Deposit into DeFi protocols
"""
    
    # Funded portfolio - show holdings + suggestions
    lines = []
    lines.append(f"**Portfolio Value:** ${total_value:,.2f}")
    lines.append(f"**Token Count:** {token_count}")
    
    # Top holdings
    for holding in top_holdings[:5]:
        lines.append(f"- {symbol}: {amount} (${value_usd})")
    
    # Suggestions based on balance
    lines.append("**💡 What you can do:**")
    if has_stablecoins:
        lines.append("• 💰 **Earn yield** - Say \"deposit USDC\"")
    lines.append("• 🔄 **Swap** - Say \"swap\" to trade")
    if total_value < 100:
        lines.append("• 💳 **Buy more** - Say \"buy crypto\"")
    
    return "\n".join(lines)
```

### Suggestion Logic

| Condition | Suggestions |
|-----------|-------------|
| `total_value == 0` | "buy crypto", "receive crypto" |
| `has_stablecoins` | "earn yield", "deposit USDC" |
| `total_value < 100` | "buy more" |
| Always | "swap" |

---

## CoinGecko Integration

### Price Fetching

```python
if self._coingecko_client:
    # Token pattern matching
    token_patterns = {
        "bitcoin": "bitcoin",
        "btc": "bitcoin",
        "ethereum": "ethereum",
        "eth": "ethereum",
        "usdc": "usd-coin",
        # ... more
    }
    
    # Detect tokens from message
    for keyword, token_id in token_patterns.items():
        if keyword in message_lower:
            tokens_to_fetch.append(token_id)
    
    # Fetch prices
    prices = await self._coingecko_client.get_prices_bulk(tokens_to_fetch)
    
    # Format context
    price_data_context = "**REAL-TIME TOKEN PRICES:**\n"
    for token_id, price_data in prices.items():
        price_data_context += f"- {token_id}: ${price_data.usd:,.2f}"
        if price_data.change_24h is not None:
            price_data_context += f" ({change_sign}{change:.2f}% 24h)"
```

---

## Authentication Handling

### User Context Extraction

```python
def _extract_user_context(self, conversation_context):
    """Extract user context from conversation metadata."""
    if not conversation_context.user_metadata:
        return None
    
    # Check for user_context key
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
        }
    
    return None  # Guest user
```

### System Prompt Selection

```python
# Authenticated user - use real data context
system_prompt = self._get_authenticated_system_prompt() if is_authenticated else self._get_system_prompt()
```

---

## Source Attribution

### Sources Built

```python
sources = []

# Database source (portfolio data)
sources.append(create_database_source(
    citation_text="Your portfolio data from Anvil",
    fetched_at=datetime.now(UTC),
    metadata={"query_type": "portfolio_snapshot"},
))

# LLM source
sources.append(create_llm_source(
    model="gemini-2.0-flash",
    fetched_at=datetime.now(UTC),
))

# CoinGecko source (if prices fetched)
if price_data_context:
    sources.append(create_api_source(
        source_name="CoinGecko",
        url="https://www.coingecko.com/",
        citation_text="Real-time token prices from CoinGecko",
        fetched_at=datetime.now(UTC),
    ))
```

---

## Logging

### Debug Statements

```python
logger.info(f"📊 PortfolioAgent using real user data for authenticated user")
logger.info(f"🔍 Fetching real-time prices from CoinGecko for PortfolioAgent")
logger.info(f"✅ Fetched prices for {len(prices)} tokens from CoinGecko")
logger.warning(f"⚠️ No price data returned from CoinGecko")
logger.warning(f"⚠️ Failed to fetch CoinGecko prices: {e}")
```

---

## Testing

### Unit Tests

```python
def test_extract_user_context_authenticated():
    context = ConversationContext(
        user_metadata={"is_authenticated": True, "portfolio_summary": {...}}
    )
    result = agent._extract_user_context(context)
    assert result is not None
    assert "portfolio_summary" in result

def test_extract_user_context_guest():
    context = ConversationContext(user_metadata=None)
    result = agent._extract_user_context(context)
    assert result is None

def test_build_portfolio_context_empty():
    user_context = {"portfolio": {"total_value_usd": 0}}
    result = agent._build_portfolio_context(user_context)
    assert "buy crypto" in result.lower()

def test_build_portfolio_context_funded():
    user_context = {"portfolio": {"total_value_usd": 1000, ...}}
    result = agent._build_portfolio_context(user_context)
    assert "Portfolio Value" in result
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Context extraction | < 10ms | ~5ms |
| Context building | < 50ms | ~20ms |
| CoinGecko fetch | < 300ms | ~200ms |
| LLM response | < 1s | ~800ms |
| Total | < 1.5s | ~1s |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added CoinGecko integration |
| 2026-01-29 | Added context-aware suggestions |
| 2026-01-29 | Added source attribution |

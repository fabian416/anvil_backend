# Hunter AI Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented

---

## Overview

This document defines the shortcut patterns and routing configuration for the Hunter AI agent.

---

## Shortcut Patterns

### Price Queries

| Pattern | Agent | Description |
|---------|-------|-------------|
| `price of {token}` | hunter_ai | Single token price |
| `{token} price` | hunter_ai | Single token price |
| `current price of {token}` | hunter_ai | Real-time price |
| `what's {token} trading at` | hunter_ai | Current price |
| `{token} and {token} prices` | hunter_ai | Multi-token prices |
| `best prices` | hunter_ai | Top token prices |

### Swap Rate Queries

| Pattern | Agent | Description |
|---------|-------|-------------|
| `swap rate {from} to {to}` | hunter_ai | Swap rate quote |
| `best rate for {from} to {to}` | hunter_ai | Best swap rate |
| `convert {amount} {from} to {to}` | hunter_ai | Conversion rate |
| `exchange rate {from}/{to}` | hunter_ai | Exchange rate |

### Market Analysis

| Pattern | Agent | Description |
|---------|-------|-------------|
| `market sentiment for {token}` | hunter_ai | Sentiment analysis |
| `{token} sentiment` | hunter_ai | Token sentiment |
| `whale activity for {token}` | hunter_ai | Large transactions |
| `is {token} bullish or bearish` | hunter_ai | Market direction |
| `{token} technical analysis` | hunter_ai | Technical indicators |

---

## Multi-Language Support

### English (en)

| Pattern | Example |
|---------|---------|
| `price of {token}` | "price of ETH" |
| `what's the price of {token}` | "what's the price of Bitcoin?" |
| `{token} and {token} prices` | "BTC and ETH prices" |
| `swap rate` | "swap rate ETH to USDC" |

### Spanish (es)

| Pattern | Example |
|---------|---------|
| `precio de {token}` | "precio de ETH" |
| `cuál es el precio de {token}` | "cuál es el precio de Bitcoin?" |
| `precios de {token} y {token}` | "precios de BTC y ETH" |
| `tasa de cambio` | "tasa de cambio ETH a USDC" |

### Portuguese (pt)

| Pattern | Example |
|---------|---------|
| `preço de {token}` | "preço de ETH" |
| `qual é o preço de {token}` | "qual é o preço de Bitcoin?" |
| `preços de {token} e {token}` | "preços de BTC e ETH" |
| `taxa de câmbio` | "taxa de câmbio ETH para USDC" |

### Chinese (zh)

| Pattern | Example |
|---------|---------|
| `{token}的价格` | "ETH的价格" |
| `{token}价格是多少` | "比特币价格是多少?" |
| `{token}和{token}的价格` | "BTC和ETH的价格" |
| `汇率` | "ETH兑USDC汇率" |

---

## Supervisor Routing Configuration

### Routing Rules

Located in `src/app/domain/services/agent_squad/authenticated_supervisor.py`:

```python
"""
13. PRICE/MARKET DATA:
    - Token prices → "hunter_ai"
    - Gas prices → "gas_optimizer"
    - Market sentiment → "hunter_ai"
    
9. SWAP RATE INFO (price information only - no execution):
   - "what's the rate for ETH to USDC", "best swap rate" (NO specific amount) → "hunter_ai"
   - "price of ETH", "ETH price in USDC" → "hunter_ai"
   
16. ADVANCED MARKET ANALYSIS:
    - Historical patterns, bull/bear market cycles → "hunter_ai"
    - Correlation analysis between tokens → "hunter_ai"
    - Whale activity, large transactions → "hunter_ai"
"""
```

### Example Mappings

```python
"price of ETH" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get current ETH price","depends_on":[]}}]}}
"BTC and ETH prices" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get BTC and ETH prices","depends_on":[]}}]}}
"best swap rate ETH to USDC" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get swap rate for ETH to USDC","depends_on":[]}}]}}
"whale activity for BTC" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze whale activity for BTC","depends_on":[]}}]}}
```

---

## Differentiation from Other Agents

### Hunter AI vs Knowledge Agent

| Query | Agent | Why |
|-------|-------|-----|
| "price of ETH" | hunter_ai | Asks for real-time data |
| "what is Ethereum?" | knowledge | Asks for explanation |
| "ETH market data" | hunter_ai | Asks for market info |
| "how does Ethereum work?" | knowledge | Educational question |

### Hunter AI vs Swap Workflow

| Query | Agent | Why |
|-------|-------|-----|
| "swap rate ETH to USDC" | hunter_ai | Rate info only |
| "swap 1 ETH to USDC" | swap_workflow | Execution intent |
| "best rate for ETH/USDC" | hunter_ai | Rate comparison |
| "exchange 100 USDC for ETH" | swap_workflow | Execution intent |

### Hunter AI vs Money Market Workflow

| Query | Agent | Why |
|-------|-------|-----|
| "AAVE token price" | hunter_ai | Token price query |
| "Aave rates for ETH" | money_market_workflow | Protocol rates |
| "AAVE market cap" | hunter_ai | Market data |
| "best lending rates" | money_market_workflow | Protocol comparison |

---

## Intent Detection

### Keywords for Hunter AI

```python
HUNTER_AI_KEYWORDS = [
    # Price queries
    "price", "prices", "price of", "current price",
    "trading at", "worth", "valued at",
    
    # Market data
    "market cap", "volume", "24h change",
    "high", "low", "ath", "all time high",
    
    # Swap rates (info only)
    "swap rate", "exchange rate", "conversion rate",
    "best rate", "rate for",
    
    # Sentiment
    "sentiment", "bullish", "bearish",
    "market sentiment", "social sentiment",
    
    # Analysis
    "whale activity", "large transactions",
    "technical analysis", "pattern",
    "correlation", "market cycle",
    
    # Multi-language
    "precio", "preço", "价格",
    "tasa", "taxa", "汇率",
]
```

---

## API Response Examples

### Price Query Request

```http
POST /api/v1/conversations/{conversation_id}/messages
Authorization: Bearer {token}

{
  "content": "price of ETH",
  "language": "en"
}
```

### Price Query Response

```json
{
  "agent_message": {
    "content": "📊 **ETH Market Data**\n\n**Current Price:** $2,988.55\n**24h Change:** -0.83%\n**Market Cap:** $360.75B\n**24h Volume:** $21.95B",
    "sources": [
      {
        "source_type": "api",
        "source_name": "CoinGecko",
        "citation_text": "Real-time price data for ETHEREUM",
        "relevance_score": 1.0
      }
    ],
    "routing": {
      "intent": "SUPERVISOR_WORKFLOW",
      "handler": "authenticated_supervisor"
    },
    "enrichment": {
      "agents_used": ["hunter_ai"]
    }
  }
}
```

### Multi-Token Response

```json
{
  "agent_message": {
    "content": "📊 **Market Overview**\n\n**BITCOIN:**\n- Current Price: $92,619.00\n- 24h Change: +1.25%\n\n**ETHEREUM:**\n- Current Price: $2,988.55\n- 24h Change: -0.83%",
    "sources": [
      {
        "source_type": "api",
        "source_name": "CoinGecko",
        "source_id": "coin:bitcoin"
      },
      {
        "source_type": "api",
        "source_name": "CoinGecko",
        "source_id": "coin:ethereum"
      }
    ]
  }
}
```

---

## Shortcut Configuration (JSON)

For the shortcuts API endpoint:

```json
{
  "shortcuts": [
    {
      "category": "market",
      "items": [
        {
          "text": "Price of ETH",
          "translations": {
            "en": "Price of ETH",
            "es": "Precio de ETH",
            "pt": "Preço de ETH",
            "zh": "ETH价格"
          },
          "agent": "hunter_ai",
          "icon": "📊"
        },
        {
          "text": "BTC and ETH prices",
          "translations": {
            "en": "BTC and ETH prices",
            "es": "Precios de BTC y ETH",
            "pt": "Preços de BTC e ETH",
            "zh": "BTC和ETH价格"
          },
          "agent": "hunter_ai",
          "icon": "📈"
        },
        {
          "text": "Market sentiment",
          "translations": {
            "en": "Market sentiment",
            "es": "Sentimiento del mercado",
            "pt": "Sentimento do mercado",
            "zh": "市场情绪"
          },
          "agent": "hunter_ai",
          "icon": "🎯"
        },
        {
          "text": "Whale activity",
          "translations": {
            "en": "Whale activity",
            "es": "Actividad de ballenas",
            "pt": "Atividade de baleias",
            "zh": "鲸鱼活动"
          },
          "agent": "hunter_ai",
          "icon": "🐋"
        }
      ]
    }
  ]
}
```

---

## Testing

### Unit Tests

```python
def test_price_query_routes_to_hunter():
    """Test price queries route correctly."""
    supervisor = AuthenticatedSupervisorCoordinator(...)
    
    plan = await supervisor.create_workflow_plan("price of ETH", ...)
    
    assert plan.tasks[0].agent_type == AgentType.HUNTER_AI

def test_swap_execution_routes_to_workflow():
    """Test swap execution routes to workflow (not hunter)."""
    supervisor = AuthenticatedSupervisorCoordinator(...)
    
    plan = await supervisor.create_workflow_plan("swap 1 ETH to USDC", ...)
    
    assert plan.tasks[0].agent_type == AgentType.SWAP_WORKFLOW
```

### Multi-Language Tests

```python
@pytest.mark.parametrize("query,expected_agent", [
    ("price of ETH", AgentType.HUNTER_AI),
    ("precio de ETH", AgentType.HUNTER_AI),
    ("preço de ETH", AgentType.HUNTER_AI),
    ("ETH价格", AgentType.HUNTER_AI),
])
def test_multi_language_routing(query, expected_agent):
    """Test routing works in all supported languages."""
    supervisor = AuthenticatedSupervisorCoordinator(...)
    
    plan = await supervisor.create_workflow_plan(query, ...)
    
    assert plan.tasks[0].agent_type == expected_agent
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial shortcut configuration |
| 2026-01-29 | Multi-language support added |
| 2026-01-29 | Differentiation rules documented |

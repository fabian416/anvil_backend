# Anvil Knowledge Base

## Overview

This directory contains comprehensive JSON documentation of all Anvil features, designed to be injected into LLM prompts for enhanced, accurate responses to users and investors.

**Purpose**: Provide structured, detailed context to LLMs so they can answer questions about Anvil with institutional-grade accuracy.

**Target Audiences**:
- Users learning to use Anvil
- Investors evaluating Anvil's capabilities
- Developers integrating with Anvil API

---

## Files Structure

```
anvil_knowledge/
├── README.md                       # This file - usage guide
├── features/
│   ├── overview.json              # Complete Anvil overview (default answer for "what can you do?")
│   ├── swap.json                  # Token swap feature details
│   ├── hunter_ai.json             # Hunter AI market intelligence
│   ├── ultra.json                 # ULTRA DeFi automation suite
│   └── shortcuts.json             # All command shortcuts and usage patterns
└── integrations/ (future)
    ├── aave.json                  # Aave lending protocol
    ├── hyperliquid.json           # Hyperliquid perpetual futures
    ├── compound.json              # Compound lending protocol
    └── ... (more protocols)
```

---

## File Descriptions

### 1. **overview.json** (2,800+ lines)
**When to use**: User asks "what can you do?" or "what is Anvil?"

**Contents**:
- Core capabilities (trading, market intelligence, DeFi automation, lending, portfolio)
- 18 AI agents description
- Getting started guides (users vs investors)
- Security features, pricing, use cases
- Competitive advantages and value propositions

**Key Sections**:
```json
{
  "core_capabilities": {
    "trading_execution": {...},
    "market_intelligence": {...},
    "defi_automation": {...}
  },
  "unique_features": {
    "agent_squad": "18 specialized AI agents",
    "cost_efficiency": "99% cost savings vs OpenAI"
  },
  "getting_started": {
    "for_users": {...},
    "for_investors": {
      "competitive_advantages": [...],
      "market_position": "..."
    }
  }
}
```

---

### 2. **swap.json** (1,300+ lines)
**When to use**: User asks about swapping tokens, DEX aggregators, or execution

**Contents**:
- Step-by-step how swap works
- Supported aggregators (1inch, Hyperliquid, UniswapX) with technical specs
- Multi-language command formats
- Rate comparison examples with real savings
- Safety features (slippage, MEV protection, gas optimization)
- Implementation details (handlers, MCP servers)

**Example Use Case**:
```
User: "How does Anvil swap work?"
→ Inject: swap.json["how_it_works"] + swap.json["supported_aggregators"]

User: "What aggregators do you support?"
→ Inject: swap.json["supported_aggregators"] + swap.json["rate_comparison_example"]
```

**Key Sections**:
```json
{
  "how_it_works": {
    "step_1": "User requests swap",
    "step_2": "Query multiple DEX aggregators in parallel",
    "step_3": "Compare rates and find best execution",
    "step_4": "Display swap details",
    "step_5": "Execute with MEV protection"
  },
  "rate_comparison_example": {
    "query": "swap 1000 USDC to ETH",
    "aggregator_quotes": [...],
    "user_savings": "$8.50 in gas + better rate"
  }
}
```

---

### 3. **hunter_ai.json** (1,500+ lines)
**When to use**: User asks about market intelligence, sentiment, predictions, or trading signals

**Contents**:
- 5 core capabilities (sentiment, price prediction, risk signals, trading signals, patterns)
- Real vs simulated data transparency
- Multi-source aggregation (news, social, on-chain, technical)
- Accuracy metrics (82% sentiment correlation, 73% 24h prediction accuracy)
- Competitive advantages vs Bloomberg Terminal ($2000/month → free)

**Example Use Case**:
```
User: "What is Hunter AI?"
→ Inject: hunter_ai.json["core_capabilities"] + hunter_ai.json["unique_features"]

User: "How accurate are your predictions?"
→ Inject: hunter_ai.json["accuracy_metrics"] + hunter_ai.json["common_questions"]["q2"]

Investor: "What data sources do you use?"
→ Inject: hunter_ai.json["data_sources_detail"] + hunter_ai.json["real_vs_demo_data"]
```

**Key Sections**:
```json
{
  "core_capabilities": [
    {
      "name": "Sentiment Analysis",
      "data_sources": ["Twitter", "Reddit", "Discord", "News"],
      "confidence_score": "0-100%",
      "example_response": "📊 Sentiment Analysis for BTC..."
    }
  ],
  "accuracy_metrics": {
    "sentiment_analysis": {"accuracy": "82% correlation with price movements"},
    "price_predictions": {"24h_accuracy": "73% within predicted range"}
  },
  "competitive_advantages": {
    "vs_paid_terminals": {
      "challenge": "Bloomberg Terminal ($2000/month)",
      "anvil_solution": "Free for authenticated users, 99% cheaper"
    }
  }
}
```

---

### 4. **ultra.json** (2,500+ lines)
**When to use**: User asks about DeFi automation, arbitrage, flash loans, or MEV protection

**Contents**:
- 4 core components (Arbitrage Discovery, Flash Loan Engine, MEV Protection, Auto Executor)
- Real-time arbitrage detection with profit analysis
- Multi-protocol flash loan support (Aave V3, Balancer, Uniswap V3)
- Flashbots MEV protection (free)
- Automated trading bot with risk management

**Example Use Case**:
```
User: "What is ULTRA?"
→ Inject: ultra.json["core_capabilities"]

User: "How do flash loans work?"
→ Inject: ultra.json["core_capabilities"][1] (Flash Loan Engine)

User: "Can Anvil protect me from MEV attacks?"
→ Inject: ultra.json["core_capabilities"][2] (MEV Protection) + ultra.json["common_questions"]["q4"]

Investor: "What's your competitive advantage in DeFi automation?"
→ Inject: ultra.json["competitive_advantages"] + ultra.json["investor_highlights"]
```

**Key Sections**:
```json
{
  "core_capabilities": [
    {
      "name": "Arbitrage Discovery",
      "arbitrage_types": ["2-hop", "3-hop", "Triangle", "Cross-DEX"],
      "min_profit": "$50 or 0.5%",
      "real_data": true
    },
    {
      "name": "Flash Loan Engine",
      "protocols_supported": [
        {"name": "Balancer", "fee": "0.00%"},
        {"name": "Uniswap V3", "fee": "0.00%"}
      ]
    },
    {
      "name": "MEV Protection",
      "protection_levels": ["NONE", "BASIC", "ADVANCED", "MAXIMUM"],
      "supported_relays": ["Flashbots (FREE)", "MEV Blocker", "Eden Network"]
    }
  ]
}
```

---

### 5. **shortcuts.json** (1,800+ lines)
**When to use**: User asks "what commands can I use?" or needs help with command syntax

**Contents**:
- All 16 intent types with command patterns
- Multi-language support (English, Spanish, Portuguese, Chinese)
- Quick start commands (5 most common)
- Command categories (Trading, Market Intelligence, DeFi Automation, etc.)
- Multi-step flows and cancellation keywords
- Power user tips

**Example Use Case**:
```
User: "How do I check Bitcoin price?"
→ Inject: shortcuts.json["command_categories"]["price_queries"]

User: "What commands can I use for trading?"
→ Inject: shortcuts.json["command_categories"]["trading_swaps"] + shortcuts.json["command_categories"]["defi_automation"]

User: "Show me all Hunter AI commands"
→ Inject: shortcuts.json["command_categories"]["market_intelligence"]
```

**Key Sections**:
```json
{
  "quick_start_commands": [
    {
      "command": "swap 100 USDC to ETH",
      "category": "Trading",
      "languages": {
        "english": "swap 100 USDC to ETH",
        "spanish": "cambiar 100 USDC a ETH"
      }
    }
  ],
  "command_categories": {
    "trading_swaps": {...},
    "market_intelligence": {...},
    "defi_automation": {...}
  },
  "power_user_tips": [...]
}
```

---

## How to Use for LLM Context Injection

### Basic Pattern

```python
import json

def get_knowledge_context(user_query: str, detected_intent: str) -> str:
    """
    Dynamically select and inject relevant knowledge based on query and intent.
    """

    # Load relevant JSON file(s)
    if "what can you do" in user_query.lower():
        with open("anvil_knowledge/features/overview.json") as f:
            knowledge = json.load(f)
        return json.dumps(knowledge, indent=2)

    elif detected_intent == "SWAP":
        with open("anvil_knowledge/features/swap.json") as f:
            knowledge = json.load(f)
        return json.dumps(knowledge, indent=2)

    elif detected_intent.startswith("HUNTER_"):
        with open("anvil_knowledge/features/hunter_ai.json") as f:
            knowledge = json.load(f)
        return json.dumps(knowledge, indent=2)

    elif detected_intent.startswith("ULTRA_"):
        with open("anvil_knowledge/features/ultra.json") as f:
            knowledge = json.load(f)
        return json.dumps(knowledge, indent=2)

    elif "command" in user_query.lower() or "how do i" in user_query.lower():
        with open("anvil_knowledge/features/shortcuts.json") as f:
            knowledge = json.load(f)
        return json.dumps(knowledge, indent=2)

    else:
        # Default to overview for general questions
        with open("anvil_knowledge/features/overview.json") as f:
            knowledge = json.load(f)
        return json.dumps(knowledge["core_capabilities"], indent=2)


def augment_llm_prompt(user_query: str, detected_intent: str) -> str:
    """
    Create enhanced LLM prompt with injected knowledge.
    """

    knowledge_context = get_knowledge_context(user_query, detected_intent)

    system_prompt = f"""You are Anvil, a DeFi assistant. Use the following knowledge base to answer questions accurately.

KNOWLEDGE BASE:
{knowledge_context}

INSTRUCTIONS:
- Answer based on the knowledge base above
- Be specific with numbers, features, and technical details
- For investors: emphasize competitive advantages, metrics, and market opportunity
- For users: focus on how to use features with examples
- Always cite specific data sources when discussing accuracy or real-time data

USER QUERY: {user_query}
"""

    return system_prompt
```

---

### Advanced: Selective Injection

**Problem**: Full JSON files are large (2,000+ lines) and may exceed token limits.

**Solution**: Extract only relevant sections based on query keywords.

```python
def get_targeted_knowledge(user_query: str, detected_intent: str) -> dict:
    """
    Extract only relevant sections of JSON based on query keywords.
    """

    query_lower = user_query.lower()

    if detected_intent == "HUNTER_SENTIMENT":
        with open("anvil_knowledge/features/hunter_ai.json") as f:
            full_knowledge = json.load(f)

        # Extract only sentiment-related sections
        return {
            "capability": full_knowledge["core_capabilities"][0],  # Sentiment Analysis
            "data_sources": full_knowledge["data_sources_detail"],
            "accuracy": full_knowledge["accuracy_metrics"]["sentiment_analysis"],
            "example_response": full_knowledge["command_formats"]["sentiment_analysis"]["example_response"]
        }

    elif "competitive advantage" in query_lower or "investor" in query_lower:
        # Investor-focused response
        with open("anvil_knowledge/features/overview.json") as f:
            full_knowledge = json.load(f)

        return {
            "competitive_advantages": full_knowledge["getting_started"]["for_investors"]["competitive_advantages"],
            "value_proposition": full_knowledge["getting_started"]["for_investors"]["value_proposition"],
            "market_position": full_knowledge["getting_started"]["for_investors"]["market_position"]
        }

    # ... more targeted extractions
```

---

### Example Integration in `conversations_router.py`

```python
# In conversations_router.py

from anvil_knowledge.knowledge_injector import get_knowledge_context, augment_llm_prompt

# ... existing code ...

# After intent detection
detected_intent = intent_detector.detect(message.content)

# Inject knowledge into LLM prompt
enhanced_system_prompt = augment_llm_prompt(
    user_query=message.content,
    detected_intent=detected_intent.intent
)

# Use enhanced prompt with LLM
llm_response = await llm_gateway.generate_response(
    system_prompt=enhanced_system_prompt,
    user_message=message.content
)
```

---

## Intent-to-JSON Mapping

| Intent Pattern | Primary JSON File | Secondary Files |
|----------------|-------------------|-----------------|
| `what can you do?` | overview.json | shortcuts.json |
| `SWAP` | swap.json | overview.json (core_capabilities.trading_execution) |
| `HUNTER_*` | hunter_ai.json | - |
| `ULTRA_*` | ultra.json | - |
| `PROTOCOL_SEARCH` | overview.json | (future: integrations/*.json) |
| `GENERAL_CONVERSATION` | overview.json | shortcuts.json |
| Help/Commands | shortcuts.json | overview.json |

---

## Expected Impact

### Before (No Knowledge Injection)
```
User: "What is Hunter AI?"
LLM: "I don't have specific information about Hunter AI. It might be a market intelligence feature."
```

### After (With Knowledge Injection)
```
User: "What is Hunter AI?"
LLM: "Hunter AI is Anvil's advanced market intelligence system that provides:

1. **Sentiment Analysis**: Multi-source tracking across Twitter, Reddit, Discord, and news outlets
   - 82% correlation with actual price movements
   - Real-time news via RSS feeds (CoinDesk, CoinTelegraph)
   - Confidence scores (0-100%) for each analysis

2. **Price Predictions**: AI-powered forecasting for 24h, 1 week, and 1 month horizons
   - 73% accuracy within predicted range (24h predictions)
   - Uses technical analysis, on-chain metrics, and sentiment data

3. **Risk Signals**: Early warning system for market risks and volatility spikes
   - 4 risk categories: volatility, liquidity, smart contract, market manipulation

4. **Trading Signals**: Buy/sell recommendations with technical indicators
   - 68% win rate (signals that moved in predicted direction)
   - RSI, MACD, Bollinger Bands, volume analysis

**Competitive Advantage**: Bloomberg Terminal costs $2,000/month, Hunter AI is free for authenticated users."
```

---

## Quality Metrics

### Accuracy Improvements (Expected)
- **Feature Coverage**: 90% of user questions answerable from knowledge base (vs 40% before)
- **Response Accuracy**: 95% factually correct responses (vs 65% before)
- **Investor Queries**: 100% coverage for competitive advantages, pricing, capabilities

### User Experience Improvements
- **Specificity**: Concrete numbers, features, and examples (not vague descriptions)
- **Discovery**: Users discover 70% more features through enhanced responses
- **Confidence**: 85% user satisfaction with answer quality (target)

---

## Maintenance

### When to Update

1. **New Features**: Add new JSON files in `features/` or update existing
2. **Accuracy Changes**: Update `accuracy_metrics` sections when backtests improve
3. **Pricing Changes**: Update `pricing` sections in all relevant files
4. **Protocol Integrations**: Add new files in `integrations/` (future)
5. **Data Source Changes**: Update `data_sources_detail` and `real_vs_demo_data` sections

### Versioning

Each JSON file should include metadata:
```json
{
  "version": "1.0.0",
  "last_updated": "2025-01-14",
  "changelog": [
    "2025-01-14: Initial creation with complete feature documentation"
  ]
}
```

---

## Future Enhancements

### Planned Files

1. **integrations/aave.json** - Aave lending protocol integration
2. **integrations/hyperliquid.json** - Hyperliquid perpetual futures
3. **integrations/compound.json** - Compound lending protocol
4. **integrations/uniswap.json** - Uniswap DEX integration
5. **integrations/1inch.json** - 1inch aggregator integration

### RAG Implementation (Phase 2)

Convert JSON files to vector embeddings for semantic search:
- Use Pinecone or Weaviate for vector storage
- Embed each section separately for granular retrieval
- Semantic search: "how does anvil make money?" → retrieves relevant monetization sections

---

## Developer Notes

### File Size Considerations

- **overview.json**: 2,800 lines (~150KB) - Use selectively or extract sections
- **swap.json**: 1,300 lines (~70KB) - Full file OK for swap-related queries
- **hunter_ai.json**: 1,500 lines (~80KB) - Full file OK for Hunter AI queries
- **ultra.json**: 2,500 lines (~135KB) - Use selectively for specific ULTRA capabilities
- **shortcuts.json**: 1,800 lines (~95KB) - Full file OK for command help

**Token Limits**:
- Claude 3.5 Sonnet: 200K tokens input (~750KB text)
- GPT-4 Turbo: 128K tokens input (~500KB text)
- Gemini Pro 1.5: 1M tokens input (~3.5MB text)

**Recommendation**: Full file injection is safe for most queries. For complex multi-turn conversations, extract targeted sections to preserve context window.

---

## Contact

Questions about knowledge base structure or usage? Contact the AI team or refer to:
- Implementation: `src/app/application/chat/services/knowledge_injector.py` (to be created)
- Integration: `src/app/presentation/http/controllers/chat/conversations_router.py`
- Documentation: `docs/KNOWLEDGE_BASE_INTEGRATION.md` (to be created)

---

**Last Updated**: 2025-01-14
**Version**: 1.0.0
**Maintainer**: AI Engineering Team

# Knowledge Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **KNOWLEDGE** agent is Anvil's educational specialist, providing accurate, detailed information about DeFi, crypto, blockchain, Web3, and Anvil platform features. It leverages a dynamic knowledge base (JSON files) to ensure responses are accurate and up-to-date.

### Key Differentiators

- **Dynamic Knowledge Base**: Loads context from JSON files in `anvil_knowledge/features/`
- **Intent-Based Knowledge Selection**: Selects relevant knowledge based on query intent
- **Multi-Language Support**: Responds in the user's language (English, Spanish, Portuguese, Chinese)
- **Protocol Comparisons**: Detailed comparisons of DeFi protocols (Aave vs Compound, etc.)
- **Guest and Authenticated**: Available for both guest and authenticated users

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Chat patterns and multi-language support |

---

## Quick Start

### For Developers

1. Read `architecture.md` for the hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for chat integration

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Test multi-language responses
3. Verify protocol comparison quality

---

## Key Features

### 1. Knowledge Areas

| Area | Topics | Status |
|------|--------|--------|
| **Anvil Platform** | Wallet, Swap, Lending, Portfolio, Hunter AI, ULTRA | ✅ Complete |
| **DeFi Protocols** | Aave, Compound, MakerDAO, Uniswap, Curve, etc. | ✅ Complete |
| **Crypto/Tokens** | Bitcoin, Ethereum, Stablecoins, DeFi tokens | ✅ Complete |
| **Blockchain** | Smart contracts, Gas, L2s, Bridges | ✅ Complete |
| **NFTs** | NFT basics, Marketplaces, Collections | ✅ Complete |

### 2. Knowledge Base Files

| File | Content |
|------|---------|
| `overview.json` | Anvil platform overview |
| `swap.json` | Token swap features (Hyperliquid Spot) |
| `hunter_ai.json` | Hunter AI sentiment and analysis |
| `ultra.json` | ULTRA arbitrage bot |
| `portfolio.json` | Portfolio management |
| `wallet.json` | Wallet management |
| `lending_morpho.json` | Morpho lending vaults |
| `money_market.json` | Money market rates |
| `gas_optimizer.json` | Gas optimization |
| `risk_analyzer.json` | Risk analysis |
| `shortcuts.json` | Command shortcuts |

### 3. Query Types

| Query Type | Example | Intent |
|------------|---------|--------|
| **What is X?** | "What is Anvil?" | anvil_knowledge |
| **Protocol Compare** | "Aave vs Compound" | defi_protocol |
| **Swap Capabilities** | "What swaps can I do?" | SWAP |
| **DeFi Concepts** | "What is yield farming?" | general_question |
| **Anvil Features** | "How does Hunter AI work?" | HUNTER_SENTIMENT |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → KnowledgeAgent
    ↓ (Data Sources)
External Systems
    - Knowledge Base (JSON files)
    - Vertex AI LLM (formatting)
```

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE AGENT FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "What is Anvil?"                                     │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: knowledge      │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    KnowledgeAgent       │                               │
│  │                         │                               │
│  │  1. Detect intent       │ → anvil_knowledge             │
│  │  2. Load KnowledgeInj.  │ → Lazy initialization         │
│  │  3. Get relevant JSON   │ → overview.json               │
│  │  4. Format context      │ → Structured text             │
│  │  5. Build LLM messages  │ → System + User prompt        │
│  │  6. Call Vertex AI      │ → gemini-2.0-flash            │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  Educational Response   │                               │
│  │  with Anvil knowledge   │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Routing Rules

```python
# From authenticated_supervisor.py

6. SWAP INFORMATION (what swaps are available - educational):
   - "what type of swaps can I do" → "knowledge" agent
   - "can I swap ETH" → "knowledge" agent
   - "how do swaps work on Anvil" → "knowledge" agent
   
15. EDUCATIONAL:
    - DeFi explanations → "knowledge"
    - Protocol comparisons → "knowledge"
    - Swap capabilities → "knowledge"
```

### Routing Examples

| User Query | Agent | Reason |
|------------|-------|--------|
| "What is Anvil?" | knowledge | Platform info |
| "What is DeFi?" | knowledge | Educational |
| "Aave vs Compound" | knowledge | Protocol comparison |
| "What swaps can I do?" | knowledge | Capability info |
| "How does lending work?" | knowledge | Educational |
| "What is an NFT?" | knowledge | Educational |

---

## Example Conversations

### What is Anvil?

```
User: "What is Anvil?"

Agent:
Anvil is a comprehensive DeFi platform that provides:

**Core Features:**
• 🔗 **Multi-Chain Wallet Management** - Manage wallets across chains
• 🔄 **Token Swaps** - Meme token swaps via Hyperliquid Spot
• 💰 **Lending** - Supply assets to earn yield via Morpho
• 📊 **Portfolio Tracking** - Real-time portfolio analytics
• 🎯 **Hunter AI** - Market sentiment and price analysis
• ⚡ **ULTRA** - Arbitrage discovery and flash loans

**What Makes Anvil Unique:**
• AI-powered market analysis
• Zero gas fees on Hyperliquid
• Multi-protocol lending aggregation
• Real-time portfolio tracking
```

### Protocol Comparison

```
User: "Aave vs Compound"

Agent:
**Aave vs Compound - Key Differences:**

**Aave:**
• Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Avalanche)
• Flash loans (uncollateralized instant loans)
• Variable AND stable interest rates
• Larger TVL (~$10B+)
• Advanced features (credit delegation, isolation mode)

**Compound:**
• Pioneer in DeFi lending (launched 2018)
• cToken model (interest-bearing tokens)
• Primarily Ethereum mainnet
• Simpler, battle-tested architecture
• COMP governance token

**Which to Choose?**
• Aave: More features, multi-chain access
• Compound: Simpler, highly battle-tested
• Both are reputable protocols
```

### Swap Capabilities

```
User: "What type of swaps can I do?"

Agent:
**Anvil Swap Capabilities via Hyperliquid Spot:**

**Supported Tokens (MEME ONLY):**
• PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, LICK, MANLET
• 50+ meme tokens available
• All pairs use USDC as quote currency

**Benefits:**
• ZERO gas fees (Hyperliquid L1)
• 0.02% trading fee (lower than most DEXs)
• 20,000+ TPS with sub-second execution
• Real-time order book pricing

**Important Limitation:**
Major tokens like ETH, BTC, SOL, LINK, UNI, AAVE are **NOT available** 
on Hyperliquid Spot. For those, use external DEX aggregators.

**Anvil can still help with major tokens:**
• Price checking and market data
• Portfolio tracking
• Market analysis via Hunter AI
```

### Multi-Language (Spanish)

```
User: "¿Qué es Anvil?"

Agent:
Anvil es una plataforma DeFi integral que proporciona:

**Características Principales:**
• 🔗 **Gestión de Billeteras Multi-Cadena** - Gestiona billeteras
• 🔄 **Intercambios de Tokens** - Meme tokens vía Hyperliquid Spot
• 💰 **Suministro de Activos** - Deposita para ganar rendimiento
• 📊 **Seguimiento de Cartera** - Análisis en tiempo real
• 🎯 **Hunter AI** - Sentimiento de mercado y análisis de precios

Note: Uses "suministro de activos" (supply assets), NOT "préstamos" (loans).
```

---

## Knowledge Injection

### How It Works

```python
# 1. Detect intent from query
intent = self._detect_knowledge_intent(query)  # e.g., "SWAP"

# 2. Load KnowledgeInjector
knowledge_dict = self._knowledge_injector.get_knowledge_for_intent(
    user_query=message.value,
    detected_intent=intent,
    user_type=user_type,
)

# 3. Format as context string
knowledge_context = self._format_knowledge_context(knowledge_dict)

# 4. Include in LLM prompt
messages = self._build_messages(message, context, knowledge_context)
```

### Intent Detection

| Keywords | Intent |
|----------|--------|
| anvil, what is anvil | `anvil_knowledge` |
| hunter, sentiment | `HUNTER_SENTIMENT` |
| ultra, arbitrage, flash loan | `ULTRA_ARBITRAGE` |
| swap, exchange, trade | `SWAP` |
| portfolio, balance | `PORTFOLIO` |
| wallet | `WALLET` |
| lending, morpho, vault | `LENDING_MORPHO` |
| gas, transaction fee | `GAS_OPTIMIZER` |
| risk, safe, tvl | `RISK_ANALYZER` |
| aave, compound, uniswap | `defi_protocol` |

---

## Configuration

### Default Parameters

```python
# From knowledge_agent.py

# LLM Configuration
model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.5           # Lower for factual responses
max_tokens = 1500           # More for detailed explanations

# Data Sources
- Knowledge Base (JSON files in anvil_knowledge/features/)
- Vertex AI LLM (response generation)
```

### Response Structure

```python
AgentResponse(
    content="Educational response...",
    agent_type=AgentType.KNOWLEDGE,
    tools_used=["knowledge_base"] if knowledge_context else [],
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
        SourceInfo(source_type="api", source_name="Anvil Knowledge Base", ...),
    ],
    metadata={
        "tokens_used": 500,
        "latency_ms": 800,
        "model": "gemini-2.0-flash",
        "provider": "Vertex AI",
        "knowledge_base_used": True,
        "intent": "anvil_knowledge",
    },
)
```

---

## Critical Rules

### Language Matching

**Respond in the user's language:**

| User Language | Response Language |
|---------------|-------------------|
| English | English |
| Spanish | Spanish |
| Portuguese | Portuguese |
| Chinese | Chinese |

### Terminology (Lending)

**NEVER use "préstamos" in Spanish** - Anvil supports LENDING only, NOT borrowing.

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| préstamos | suministro de activos |
| take a loan | supply assets |
| borrow | lend, deposit |

### Direct Answers

**NEVER ask for clarification on DeFi topics:**

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| "What would you like to know about DeFi?" | Provide the information directly |
| "Could you be more specific?" | Answer the question as asked |

### Off-Topic Handling

**Politely decline non-crypto topics:**

| Topic | Response |
|-------|----------|
| Cooking | "I'm specialized in DeFi and crypto. What would you like to know about DeFi?" |
| History | "I'm focused on blockchain and crypto. How can I help with DeFi?" |
| Sports | "I specialize in cryptocurrency. Ask me about DeFi, tokens, or NFTs!" |

---

## Testing Checklist

### Unit Tests
- [ ] Intent detection for all intents
- [ ] Knowledge context formatting
- [ ] Message building (direct questions)
- [ ] Message building (complex questions)
- [ ] Multi-language detection

### Integration Tests
- [ ] Complete knowledge query flow
- [ ] Knowledge base loading
- [ ] Source attribution
- [ ] Protocol comparison quality

### E2E Tests
- [ ] "What is Anvil?" response
- [ ] "Aave vs Compound" response
- [ ] Spanish language response
- [ ] Off-topic handling

---

## Related Documentation

- **Hunter AI**: `/docs/ceo/agents/hunter/` (market data)
- **ULTRA**: `/docs/ceo/agents/ultra/` (arbitrage)
- **Swap Workflow**: `/docs/ceo/agents/swap/` (swap execution)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (lending execution)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added knowledge base integration |
| 1.0 | 2026-01-29 | Added protocol comparison support |

---

**End of Knowledge Agent Specification**

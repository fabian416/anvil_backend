# Knowledge Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, multi-language support, and supervisor routing for the **KNOWLEDGE** agent.

---

## Query Patterns by Topic

### Anvil Platform

| Pattern | Example | Intent |
|---------|---------|--------|
| what is anvil | "What is Anvil?" | anvil_knowledge |
| anvil features | "What features does Anvil have?" | anvil_knowledge |
| capabilities | "What can you do?" | anvil_knowledge |
| how does anvil | "How does Anvil work?" | anvil_knowledge |

### DeFi Education

| Pattern | Example | Intent |
|---------|---------|--------|
| what is defi | "What is DeFi?" | general_question |
| what is yield farming | "What is yield farming?" | general_question |
| what is staking | "What is staking?" | general_question |
| explain X | "Explain liquidity pools" | general_question |

### Protocol Comparisons

| Pattern | Example | Intent |
|---------|---------|--------|
| X vs Y | "Aave vs Compound" | defi_protocol |
| compare X and Y | "Compare Uniswap and SushiSwap" | defi_protocol |
| difference between | "Difference between Aave and Compound" | defi_protocol |
| which is better | "Which is better: Curve or Balancer?" | defi_protocol |

### Swap Capabilities

| Pattern | Example | Intent |
|---------|---------|--------|
| what swaps can I do | "What type of swaps can I do?" | SWAP |
| what tokens can I swap | "What tokens can I swap?" | SWAP |
| can I swap X | "Can I swap ETH?" | SWAP |
| how do swaps work | "How do swaps work on Anvil?" | SWAP |

### Crypto/Tokens

| Pattern | Example | Intent |
|---------|---------|--------|
| what is BTC | "What is Bitcoin?" | general_question |
| what is ETH | "What is Ethereum?" | general_question |
| what is USDC | "What is USDC?" | general_question |
| what is X token | "What is AAVE token?" | general_question |

### NFTs

| Pattern | Example | Intent |
|---------|---------|--------|
| what is NFT | "What is an NFT?" | general_question |
| where to buy NFTs | "Where can I buy NFTs?" | general_question |
| NFT marketplaces | "What are the best NFT marketplaces?" | general_question |

---

## Multi-Language Examples

### English (en)

```
Primary Commands:
• "What is Anvil?"
• "What is DeFi?"
• "Aave vs Compound"
• "What swaps can I do?"
• "What is Bitcoin?"
• "Explain yield farming"

Response:
• Clear, educational explanations
• Bullet points for features
• Examples when helpful
```

### Spanish (es)

```
Primary Commands:
• "¿Qué es Anvil?"
• "¿Qué es DeFi?"
• "Aave vs Compound"
• "¿Qué swaps puedo hacer?"
• "¿Qué es Bitcoin?"
• "Explica yield farming"

Response (in Spanish):
• Uses "suministro de activos" NOT "préstamos"
• Clear explanations in Spanish
• Same quality as English responses

IMPORTANT:
❌ NEVER use "préstamos" (loans/borrowing)
✅ Use "suministro de activos" (supply assets)
```

### Portuguese (pt)

```
Primary Commands:
• "O que é Anvil?"
• "O que é DeFi?"
• "Aave vs Compound"
• "Quais swaps posso fazer?"
• "O que é Bitcoin?"
• "Explique yield farming"

Response (in Portuguese):
• Clear explanations in Portuguese
• Same quality as English responses
```

### Chinese (zh)

```
Primary Commands:
• "什么是Anvil？"
• "什么是DeFi？"
• "Aave vs Compound"
• "我可以做什么交换？"
• "什么是比特币？"
• "解释yield farming"

Response (in Chinese):
• Clear explanations in Chinese
• Same quality as English responses
```

---

## Supervisor Routing Configuration

### From authenticated_supervisor.py

```python
"""
6. SWAP INFORMATION (what swaps are available - educational):
   - "what type of swaps can I do", "what swaps can I make" → "knowledge" agent
   - "can I swap ETH", "can I swap BTC", "how do swaps work on Anvil" → "knowledge" agent
   - CRITICAL: Use "knowledge" when user asks ABOUT swap capabilities (informational)
   
15. EDUCATIONAL:
    - DeFi explanations → "knowledge"
    - Protocol comparisons → "knowledge"
    - Swap capabilities → "knowledge" (what swaps can I do, what tokens are supported)
"""
```

### Routing Examples

```python
# Educational queries → knowledge agent
"what is defi" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain DeFi"}}]}}
"compare aave vs compound" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Compare Aave and Compound"}}]}}
"what type of swaps can I do" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain Anvil swap capabilities"}}]}}
"can I swap ETH" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain ETH is NOT supported for swaps"}}]}}
"what is defi? also check gas prices" → {{"tasks":[
    {{"agent_type":"knowledge","task_description":"Explain DeFi concepts"}},
    {{"agent_type":"gas_optimizer","task_description":"Get current gas prices"}}
]}}
```

### From guest_supervisor.py

```python
"""
3. INFORMATIONAL vs ACTION QUERIES (CRITICAL FOR GUESTS):
   **INFORMATIONAL QUERIES → Can answer directly:**
   - "can i swap?" / "can i trade?" / "can i lend?" → "knowledge" (asking about capabilities)
   - "how do i swap?" / "how to swap?" / "how to lend?" → "knowledge" (asking for instructions)
   - "what swaps are supported?" / "what lending protocols?" → "knowledge" (asking about features)
   - "what is a swap?" / "explain swapping" / "what is lending?" → "knowledge" (asking for education)
   
   **DeFi concepts, education, capability questions** → "knowledge"
   **Protocol comparisons and explanations** → "knowledge" (e.g., "Aave vs Compound")
   **DeFi protocol questions** → "knowledge" (Aave, Compound, Uniswap, Curve, etc.)
"""
```

---

## Intent Mapping

### Intent to Knowledge File

| Intent | Knowledge File | Topics |
|--------|----------------|--------|
| `anvil_knowledge` | overview.json | Anvil platform |
| `HUNTER_SENTIMENT` | hunter_ai.json | Hunter AI |
| `ULTRA_ARBITRAGE` | ultra.json | ULTRA arbitrage |
| `SWAP` | swap.json | Token swaps |
| `PORTFOLIO` | portfolio.json | Portfolio |
| `WALLET` | wallet.json | Wallet |
| `LENDING_MORPHO` | lending_morpho.json | Lending |
| `GAS_OPTIMIZER` | gas_optimizer.json | Gas |
| `RISK_ANALYZER` | risk_analyzer.json | Risk |
| `defi_protocol` | (built-in) | Protocol comparisons |
| `general_question` | (built-in) | General DeFi |

---

## API Response Examples

### Educational Query

```json
{
  "agent_message": {
    "content": "DeFi (Decentralized Finance) is a financial system built on blockchain technology that operates without traditional intermediaries like banks...\n\n**Key Features:**\n• Permissionless access\n• Transparent and auditable\n• Programmable money via smart contracts\n• 24/7 global availability\n\n**Common DeFi Applications:**\n• Lending and borrowing (Aave, Compound)\n• Decentralized exchanges (Uniswap, Curve)\n• Yield farming and staking\n• Stablecoins (USDC, DAI)",
    "role": "assistant",
    "agent_type": "knowledge"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 100},
      {"agent_type": "knowledge", "duration_ms": 850}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash with Anvil knowledge base",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Protocol Comparison

```json
{
  "agent_message": {
    "content": "**Aave vs Compound - Key Differences:**\n\n**Aave:**\n• Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Avalanche)\n• Flash loans (uncollateralized instant loans)\n• Variable AND stable interest rates\n• Larger TVL (~$10B+)\n• Advanced features (credit delegation, isolation mode)\n\n**Compound:**\n• Pioneer in DeFi lending (launched 2018)\n• cToken model (interest-bearing tokens)\n• Primarily Ethereum mainnet\n• Simpler, battle-tested architecture\n• COMP governance token\n\n**Which to Choose?**\n• Aave: More features, multi-chain access\n• Compound: Simpler, highly battle-tested\n• Both are reputable protocols",
    "role": "assistant",
    "agent_type": "knowledge"
  },
  "execute_data": null,
  "enrichment": {
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash with Anvil knowledge base",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Swap Capabilities

```json
{
  "agent_message": {
    "content": "**Anvil Swap Capabilities via Hyperliquid Spot:**\n\n**Supported Tokens (MEME ONLY):**\n• PURR, TRUMP, PEPE, HFUN, MOG, GMEOW, LICK, MANLET\n• 50+ meme tokens available\n• All pairs use USDC as quote currency\n\n**Benefits:**\n• ZERO gas fees (Hyperliquid L1)\n• 0.02% trading fee (lower than most DEXs)\n• 20,000+ TPS with sub-second execution\n• Real-time order book pricing\n\n**Important Limitation:**\nMajor tokens like ETH, BTC, SOL, LINK, UNI, AAVE are **NOT available** on Hyperliquid Spot. For those, use external DEX aggregators.\n\n**Anvil can still help with major tokens:**\n• Price checking and market data\n• Portfolio tracking\n• Market analysis via Hunter AI",
    "role": "assistant",
    "agent_type": "knowledge"
  },
  "execute_data": null,
  "enrichment": {
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "Anvil Knowledge Base",
        "citation_text": "Anvil platform knowledge and features",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Spanish Response

```json
{
  "agent_message": {
    "content": "Anvil es una plataforma DeFi integral que proporciona:\n\n**Características Principales:**\n• 🔗 **Gestión de Billeteras Multi-Cadena** - Gestiona billeteras en múltiples redes\n• 🔄 **Intercambios de Tokens** - Meme tokens vía Hyperliquid Spot\n• 💰 **Suministro de Activos** - Deposita para ganar rendimiento via Morpho\n• 📊 **Seguimiento de Cartera** - Análisis en tiempo real\n• 🎯 **Hunter AI** - Sentimiento de mercado y análisis de precios\n• ⚡ **ULTRA** - Descubrimiento de arbitraje y flash loans\n\n**Lo que hace único a Anvil:**\n• Análisis de mercado impulsado por IA\n• Cero tarifas de gas en Hyperliquid\n• Agregación de préstamos multi-protocolo\n• Seguimiento de cartera en tiempo real",
    "role": "assistant",
    "agent_type": "knowledge"
  }
}
```

---

## Knowledge vs Action Distinction

### Knowledge Agent (Informational)

| Query Type | Example | Agent |
|------------|---------|-------|
| What can I do? | "What swaps can I do?" | knowledge |
| How does it work? | "How do swaps work?" | knowledge |
| What is X? | "What is Aave?" | knowledge |
| Compare X and Y | "Aave vs Compound" | knowledge |

### Action Agents (Execution)

| Query Type | Example | Agent |
|------------|---------|-------|
| Execute swap | "Swap 100 USDC to PEPE" | swap_workflow |
| Execute lending | "Supply 1000 USDC to Morpho" | lending_workflow |
| Buy crypto | "Buy 100 USDC" | buy_workflow |

---

## Off-Topic Handling

### Supported Topics

| Category | Examples | Handled? |
|----------|----------|----------|
| Anvil Platform | Features, capabilities | ✅ Yes |
| DeFi | Yield farming, lending, DEXs | ✅ Yes |
| Crypto | Bitcoin, Ethereum, tokens | ✅ Yes |
| Blockchain | Smart contracts, gas, L2s | ✅ Yes |
| NFTs | NFT basics, marketplaces | ✅ Yes |
| Web3 | DAOs, governance | ✅ Yes |

### Off-Topic (Politely Declined)

| Category | Examples | Response |
|----------|----------|----------|
| Cooking | Recipes, food | "I'm specialized in DeFi and crypto..." |
| History | Historical events | "I'm focused on blockchain and crypto..." |
| Sports | Teams, games | "I specialize in cryptocurrency..." |
| General | Weather, news | "I can help with DeFi, tokens, or NFTs..." |

---

## Creative Requests

### Allowed (Crypto-Related)

| Request | Example | Response |
|---------|---------|----------|
| Crypto poems | "Write a poem about gas fees" | ✅ Creative poem about Ethereum gas |
| DeFi stories | "Tell a story about yield farming" | ✅ Creative story |
| Token analogies | "Explain Bitcoin like I'm 5" | ✅ Simple explanation |

---

## Common User Flows

### Flow 1: Educational Query

```
User: "What is DeFi?"
→ Supervisor routes to knowledge agent
→ KnowledgeAgent detects intent: general_question
→ Built-in DeFi knowledge (no JSON needed)
→ LLM generates educational response
→ Returns formatted explanation
```

### Flow 2: Anvil Feature Query

```
User: "What can you do?"
→ Supervisor routes to knowledge agent
→ KnowledgeAgent detects intent: anvil_knowledge
→ Loads overview.json from knowledge base
→ Formats knowledge as context
→ LLM generates Anvil-specific response
```

### Flow 3: Protocol Comparison

```
User: "Aave vs Compound"
→ Supervisor routes to knowledge agent
→ KnowledgeAgent detects intent: defi_protocol
→ Built-in protocol knowledge
→ Adds comparison instruction suffix
→ LLM generates detailed comparison
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Knowledge Agent Shortcuts**

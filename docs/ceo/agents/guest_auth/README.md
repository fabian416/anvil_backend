# Guest Auth Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Guest-Only)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **GUEST_AUTH** agent handles authentication requirements for restricted features when guest (unauthenticated) users attempt to perform actions that require a wallet or account. It generates context-aware registration messages using knowledge base integration and LLM.

### Key Differentiators

- **Guest-Only Agent**: Only used in guest supervisor flow
- **Context-Aware Messages**: Uses knowledge base to generate tailored prompts
- **Multi-Language Support**: EN, ES, PT, ZH
- **Feature Detection**: Identifies which restricted feature user wants
- **LLM-Enhanced**: Generates personalized registration messages

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and auth prompts |

---

## Quick Start

### For Users

**Restricted Features (Require Login):**
```
• "my portfolio" → Portfolio access prompt
• "my balance" → Wallet access prompt
• "swap 100 USDC to ETH" → Execute swap prompt
• "lend 100 USDC" → Lending transaction prompt
• "buy crypto" → Account verification prompt
• "send crypto" → Wallet connection prompt
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for message templates

---

## Key Features

### 1. Restricted Feature Detection

| Feature | Keywords | Reason |
|---------|----------|--------|
| **Portfolio** | my portfolio, my holdings | portfolio_access |
| **Balance** | my balance, wallet balance | wallet_access |
| **Activity** | my transactions, history | transaction_history |
| **Receive** | my address, deposit address | wallet_address |
| **Buy** | buy crypto, purchase bitcoin | buy_crypto |
| **Send** | send crypto, transfer | send_crypto |
| **Lending** | lend, deposit, morpho | execute_deposit |

### 2. Multi-Language Support

| Language | Code | CTA Message |
|----------|------|-------------|
| English | en | Sign Up Free |
| Spanish | es | Regístrate Gratis |
| Portuguese | pt | Cadastre-se Grátis |
| Mandarin | zh | 免费注册 |

### 3. Context-Aware Generation

Uses knowledge base + LLM to generate messages specific to the user's intent:

```
User: "Supply 1000 USDC to Morpho"

Agent (context-aware):
"To supply USDC to Morpho vaults and start earning yield, you'll need to 
create an account. This allows you to securely connect your wallet and 
execute DeFi transactions.

👉 Sign Up Free"
```

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Guest Supervisor)
Infrastructure Layer → GuestAuthAgent
    ↓
External Systems
    - KnowledgeInjector (JSON knowledge base)
    - Vertex AI (LLM for contextual messages)
```

### Guest Auth Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   GUEST AUTH FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Guest User: "swap 100 USDC to ETH"                         │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │   Guest Supervisor      │                               │
│  │   Detects: transaction  │                               │
│  │   → requires login      │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │   GuestAuthAgent        │                               │
│  │                         │                               │
│  │  1. Detect intent       │ → SWAP                        │
│  │  2. Load knowledge      │ → swap.json                   │
│  │  3. Generate message    │ → LLM with context            │
│  │  4. Add CTA             │ → "Sign Up Free"              │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  Response: Context-aware registration prompt                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Guest Supervisor Rules

```python
# From guest_supervisor.py

# ACTION REQUESTS → "guest_auth" agent (REQUIRES LOGIN):
"swap 100 USDC to ETH" → guest_auth (specific transaction - needs wallet)
"lend 100 USDC" → guest_auth (lending transaction - needs wallet)
"buy crypto" → guest_auth (buying crypto - needs account)
"my balance" → guest_auth (requires wallet)
"my portfolio" → guest_auth (requires wallet)
"my transactions" → guest_auth (requires login)

# Information queries → Can answer directly (other agents)
"what is DeFi?" → knowledge (no login needed)
"BTC price" → hunter_ai (no login needed)
```

---

## Example Conversations

### Portfolio Access (English)

```
User: "my portfolio"

Agent:
💼 **Unlock Your Complete Portfolio Dashboard**

Track all your DeFi positions in one place! With a free account, you'll get:

✨ **Real-time Portfolio Tracking**
• View all your assets across multiple chains
• Monitor your total portfolio value
• Track performance over time

📊 **Advanced Analytics**
• Asset allocation breakdown
• Profit/loss analysis
• Risk exposure metrics

🔔 **Smart Alerts**
• Price movement notifications
• Liquidation risk warnings
• Yield opportunity alerts

🎯 **AI-Powered Insights**
• Portfolio optimization suggestions
• Rebalancing recommendations
• Tax optimization strategies

**It's free and takes less than 30 seconds to sign up!**

👉 Sign Up Free
```

### Lending Transaction (Context-Aware)

```
User: "Supply 1000 USDC to Morpho"

Agent:
To supply USDC to Morpho vaults and start earning yield, you'll need to 
create an account. This allows you to securely connect your wallet and 
execute DeFi transactions.

👉 Sign Up Free
```

### Buy Crypto (Spanish)

```
User: "comprar crypto"

Agent:
🔐 **Cuenta Requerida**

Para comprar cripto con dinero fiat, necesitas crear una cuenta y completar 
la verificación.

Regístrate para:
• Comprar cripto con tarjeta o transferencia bancaria
• Acceder a múltiples proveedores
• Obtener las mejores tasas

👉 Regístrate Gratis
```

---

## Configuration

### Default Parameters

```python
# From guest_auth_agent.py

model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.3           # Consistent responses
max_tokens = 500            # Short messages
```

### Response Structure

```python
AgentResponse(
    content="Context-aware registration message...",
    agent_type=AgentType.GUEST_AUTH,
    tools_used=["auth_detection", "knowledge_base"],
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash",
                   citation_text="Generated with knowledge base", ...),
    ],
    metadata={
        "tokens_used": 100,
        "latency_ms": 300,
        "model": "gemini-2.0-flash",
        "knowledge_used": True,
        "provider": "vertex_ai",
    },
)
```

---

## Message Templates

### By Feature Type

| Feature | Template Key | Description |
|---------|-------------|-------------|
| Portfolio | portfolio_access | Full dashboard unlock |
| Balance | wallet_access | Wallet connection |
| Activity | transaction_history | Transaction history access |
| Receive | wallet_address | Deposit address |
| Buy | buy_crypto | Fiat on-ramp |
| Send | send_crypto | Token transfer |
| Lending | execute_deposit | DeFi deposit |
| General | execute_action | Generic DeFi action |

### CTA Messages

| Language | CTA |
|----------|-----|
| English | Sign Up Free |
| Spanish | Regístrate Gratis |
| Portuguese | Cadastre-se Grátis |
| Mandarin | 免费注册 |

---

## Testing Checklist

### Unit Tests
- [ ] Feature detection logic
- [ ] Knowledge intent mapping
- [ ] Language detection
- [ ] Message generation

### Integration Tests
- [ ] Knowledge injector loading
- [ ] LLM contextual generation
- [ ] Source attribution

### E2E Tests
- [ ] Complete guest auth flow
- [ ] Multi-language responses
- [ ] Fallback message generation

---

## Related Documentation

- **Chat Agent**: `/docs/ceo/agents/chat/` (also has restricted feature detection)
- **Knowledge Agent**: `/docs/ceo/agents/knowledge/` (knowledge base)
- **Guest Supervisor**: `src/app/domain/services/agent_squad/guest_supervisor.py`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added knowledge integration |
| 1.0 | 2026-01-29 | Added context-aware generation |
| 1.0 | 2026-01-29 | Added multi-language support |

---

**End of Guest Auth Agent Specification**

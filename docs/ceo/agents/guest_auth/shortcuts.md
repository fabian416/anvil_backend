# Guest Auth Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the authentication prompts, message templates, and multi-language support for the **GUEST_AUTH** agent.

---

## Restricted Feature Patterns

### Features Requiring Authentication

| Category | Keywords | Template |
|----------|----------|----------|
| **Portfolio** | my portfolio, my holdings, list my tokens | portfolio_access |
| **Balance** | my balance, wallet balance, how much do I have | wallet_access |
| **Activity** | my transactions, transaction history, my activity | transaction_history |
| **Receive** | my address, wallet address, receive crypto | wallet_address |
| **Buy** | buy crypto, purchase bitcoin, buy with card | buy_crypto |
| **Send** | send crypto, transfer tokens, send to wallet | send_crypto |
| **Lending** | lend, deposit, morpho, supply | execute_deposit |

---

## Supervisor Routing Examples

### Guest Supervisor

```python
# From guest_supervisor.py

# Transaction actions → guest_auth
"swap 100 USDC to ETH" → {"agent_type":"guest_auth","task_description":"Handle swap transaction request - requires login"}
"buy crypto" → {"agent_type":"guest_auth","task_description":"Handle buy crypto request - requires authentication"}
"lend 100 usdc" → {"agent_type":"guest_auth","task_description":"Handle lending transaction - requires login"}

# Wallet queries → guest_auth
"my balance" → {"agent_type":"guest_auth","task_description":"Handle restricted feature - requires login"}
"my portfolio" → {"agent_type":"guest_auth","task_description":"Handle portfolio request - requires login"}
"show my wallets" → {"agent_type":"guest_auth","task_description":"Handle wallet request - requires login"}

# Transaction history → guest_auth
"my transactions" → {"agent_type":"guest_auth","task_description":"Handle transaction history request - requires login"}
```

---

## Message Templates

### Portfolio Access (Full Template)

#### English

```
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

#### Spanish

```
💼 **Desbloquea Tu Panel de Portafolio Completo**

¡Rastrea todas tus posiciones DeFi en un solo lugar! Con una cuenta gratuita, obtendrás:

✨ **Seguimiento de Portafolio en Tiempo Real**
• Ver todos tus activos en múltiples cadenas
• Monitorear el valor total de tu portafolio
• Rastrear el rendimiento a lo largo del tiempo

📊 **Análisis Avanzados**
...

👉 Regístrate Gratis
```

### Wallet Access (Compact Template)

#### English

```
🔐 **Wallet Access Required**

To view your balance and wallet holdings, you need to create an account 
and connect your wallet.

Sign up to:
• View real-time balances
• Track your holdings
• Monitor your positions

👉 Sign Up Free
```

### Buy Crypto

#### English

```
🔐 **Account Required**

To buy crypto with fiat, you need to create an account and complete verification.

Sign up to:
• Buy crypto with card or bank transfer
• Access multiple on-ramp providers
• Get the best rates

👉 Sign Up Free
```

### Transaction History

#### English

```
🔐 **Account Required**

To view your transaction history and past activity, you need to create 
an account.

Sign up to:
• View all transactions
• Track your trading history
• Export transaction records

👉 Sign Up Free
```

---

## Context-Aware Examples

### Lending (Knowledge-Enhanced)

```
User: "Supply 1000 USDC to Morpho"

Agent (context-aware):
To supply USDC to Morpho vaults and start earning yield, you'll need to 
create an account. This allows you to securely connect your wallet and 
execute DeFi transactions.

👉 Sign Up Free
```

### Swap (Knowledge-Enhanced)

```
User: "Swap ETH to USDC"

Agent (context-aware):
To execute token swaps on Anvil via our integrated DEX aggregators, you'll 
need to create an account. Once signed up, you can swap tokens instantly 
with optimized routing.

👉 Sign Up Free
```

### Buy Crypto (Knowledge-Enhanced)

```
User: "Buy crypto with my card"

Agent (context-aware):
To purchase crypto with a credit card or bank transfer, you'll need to 
create an account and complete a quick verification. This gives you access 
to multiple on-ramp providers for the best rates.

👉 Sign Up Free
```

---

## CTA Messages by Language

| Language | CTA |
|----------|-----|
| English (en) | Sign Up Free |
| Spanish (es) | Regístrate Gratis |
| Portuguese (pt) | Cadastre-se Grátis |
| Mandarin (zh) | 免费注册 |

---

## API Response Examples

### Portfolio Request

```json
{
  "agent_message": {
    "content": "💼 **Unlock Your Complete Portfolio Dashboard**\n\nTrack all your DeFi positions in one place!...\n\n👉 Sign Up Free",
    "role": "assistant",
    "agent_type": "guest_auth"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 60},
      {"agent_type": "guest_auth", "duration_ms": 50}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Lending Request (Context-Aware)

```json
{
  "agent_message": {
    "content": "To supply USDC to Morpho vaults and start earning yield, you'll need to create an account. This allows you to securely connect your wallet and execute DeFi transactions.\n\n👉 Sign Up Free",
    "role": "assistant",
    "agent_type": "guest_auth"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 60},
      {"agent_type": "guest_auth", "duration_ms": 400}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash with knowledge base",
        "metadata": {"knowledge_used": true},
        "relevance_score": 1.0
      }
    ]
  },
  "metadata": {
    "knowledge_used": true,
    "tokens_used": 100
  }
}
```

---

## Knowledge Intent Mapping

| Intent | Knowledge File | Description |
|--------|----------------|-------------|
| LENDING_MORPHO | lending_morpho.json | Morpho vault lending |
| SWAP | swap.json | Token swap capabilities |
| BUY | buy.json | Fiat on-ramp |
| SEND | transfer.json | Token transfers |
| PORTFOLIO | portfolio.json | Portfolio tracking |
| WALLET | wallet.json | Wallet management |
| ACTIVITY | activity.json | Transaction history |

---

## Feature to Reason Mapping

```python
feature_to_reason = {
    "balance": "wallet_access",
    "activity": "transaction_history",
    "receive": "wallet_address",
    "buy": "buy_crypto",
    "send": "send_crypto",
    "portfolio": "portfolio_access",
    "lending": "execute_deposit",
    "general": "execute_action",
}
```

---

## Additional Message Types

### Demo Disclaimer

```python
GUEST_DEMO_DISCLAIMER = {
    "en": "You're in demo mode. Some features require registration.",
    "es": "Estás en modo demo. Algunas funciones requieren registro.",
    "pt": "Você está no modo demo. Alguns recursos requerem registro.",
    "zh": "您处于演示模式。某些功能需要注册。",
}
```

### Rate Limit Warning

```python
GUEST_RATE_LIMIT_MESSAGES = {
    "en": "You've reached the message limit for demo mode. Sign up for unlimited access.",
    "es": "Has alcanzado el límite de mensajes del modo demo. Regístrate para acceso ilimitado.",
    "pt": "Você atingiu o limite de mensagens do modo demo. Cadastre-se para acesso ilimitado.",
    "zh": "您已达到演示模式的消息限制。注册以获得无限访问。",
}
```

### Welcome Message

```python
GUEST_WELCOME_MESSAGES = {
    "en": "Welcome to Anvil! I'm your AI assistant for DeFi. Ask me about protocols, yields, or risks. Note: Some features require registration.",
    "es": "¡Bienvenido a Anvil! Soy tu asistente de IA para DeFi. Pregúntame sobre protocolos, rendimientos o riesgos. Nota: Algunas funciones requieren registro.",
    "pt": "Bem-vindo ao Anvil! Sou seu assistente de IA para DeFi. Pergunte-me sobre protocolos, rendimentos ou riscos. Nota: Alguns recursos requerem registro.",
    "zh": "欢迎来到 Anvil！我是您的 DeFi AI 助手。问我关于协议、收益或风险的问题。注意：某些功能需要注册。",
}
```

---

## Error Handling

### Knowledge Loading Failure

```python
# If knowledge injector fails, use static message
try:
    knowledge_dict = self._knowledge_injector.get_knowledge_for_intent(...)
except Exception as e:
    logger.warning(f"Error loading knowledge: {e}")
    # Fallback to static template
```

### LLM Generation Failure

```python
# If LLM fails, use static message
if not custom_message:
    restricted_feature = self._detect_restricted_feature(message.value)
    custom_message = self._get_custom_message(restricted_feature, context)
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Guest Auth Agent Shortcuts**

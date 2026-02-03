# Buy Workflow Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the shortcut patterns, multi-language support, and supervisor routing for the **BUY_WORKFLOW** agent.

---

## Primary Patterns

### Buy Execution Patterns

| Pattern | Example | Agent |
|---------|---------|-------|
| `buy [amount] of [crypto]` | "buy $100 of USDC" | buy_workflow |
| `purchase [amount] of [crypto]` | "purchase 50 dollars of USDC" | buy_workflow |
| `buy crypto` | "buy crypto" | buy_workflow |
| `buy [crypto]` | "buy USDC" | buy_workflow |
| `buy [amount]` | "buy $100" | buy_workflow (defaults to USDC) |
| `purchase with card` | "purchase with card" | buy_workflow |
| `I want to buy` | "I want to buy crypto" | buy_workflow |

### Unsupported Crypto (Redirected)

| Pattern | Example | Result |
|---------|---------|--------|
| `buy ETH` | "buy $100 of ETH" | Redirects to USDC |
| `buy BTC` | "buy Bitcoin" | Redirects to USDC |
| `buy SOL` | "purchase SOL" | Redirects to USDC |

---

## Multi-Language Examples

### English (en)

```
Primary Commands:
• "buy $100 of USDC"
• "purchase 50 dollars of crypto"
• "buy crypto"
• "I want to buy USDC"

Amount Inputs:
• "$100" / "100 dollars" / "100 USD"
• "500" / "$500" / "five hundred"

Confirmation:
• "yes", "confirm", "ok", "proceed", "do it", "buy"

Cancellation:
• "cancel", "no", "stop", "never mind", "abort"

Modification:
• "change to $200"
• "make it 500 instead"
```

### Spanish (es)

```
Primary Commands:
• "comprar $100 de USDC"
• "comprar cripto"
• "quiero comprar USDC"

Amount Inputs:
• "$100" / "100 dólares" / "cien dólares"

Confirmation:
• "sí", "si", "confirmar", "vale", "continuar", "comprar"

Cancellation:
• "cancelar", "no", "abortar", "parar"

Modification:
• "cambiar a $200"
• "que sean 500"
```

### Portuguese (pt)

```
Primary Commands:
• "comprar $100 de USDC"
• "comprar cripto"
• "quero comprar USDC"

Amount Inputs:
• "$100" / "100 dólares" / "cem dólares"

Confirmation:
• "sim", "confirmar", "prosseguir"

Cancellation:
• "cancelar", "não", "parar"

Modification:
• "mudar para $200"
• "fazer 500 em vez"
```

### Chinese (zh)

```
Primary Commands:
• "购买 $100 USDC"
• "购买加密货币"
• "我想买 USDC"

Amount Inputs:
• "$100" / "100美元" / "一百美元"

Confirmation:
• "是", "确认", "好", "继续", "购买"

Cancellation:
• "取消", "不", "停止"

Modification:
• "改为 $200"
• "改成 500"
```

---

## Supervisor Routing Configuration

### From authenticated_supervisor.py

```python
"""
11. BUY CRYPTO EXECUTION (CRITICAL - Multi-step workflow):
    - "buy $100 of ETH", "purchase crypto", "buy USDC with card" → "buy_workflow" agent ONLY
    - The buy_workflow agent handles the COMPLETE multi-step purchase process autonomously
    - Use "buy_workflow" when user wants to BUY crypto with fiat (card, Apple Pay, etc.)
    - Examples: "buy $50 of ETH", "purchase 100 dollars of USDC", "buy crypto"
    - DO NOT combine buy_workflow with other agents - it handles everything internally
"""
```

### Routing Examples

```python
# Execution requests → buy_workflow
"buy $100 of ETH" → {{"tasks":[{{"agent_type":"buy_workflow","task_description":"Execute buy: $100 of ETH"}}]}}
"purchase 50 dollars of USDC" → {{"tasks":[{{"agent_type":"buy_workflow","task_description":"Execute buy: $50 of USDC"}}]}}
"buy crypto" → {{"tasks":[{{"agent_type":"buy_workflow","task_description":"Execute buy: need crypto and amount"}}]}}
```

---

## Restart Detection Keywords

### Buy Restart Patterns

When user is in the middle of a buy flow and says any of these, the workflow restarts:

```python
restart_keywords = [
    # English
    "buy crypto", "buy usdc", "purchase crypto", "purchase usdc",
    "i want to buy",
    
    # Spanish
    "comprar cripto", "comprar usdc",
    "quiero comprar",
]

# Also simple commands
is_simple_buy = text_lower in ("buy", "buy crypto", "comprar", "comprar cripto", "purchase")
```

### Example

```
Current State: CONFIRM step (showing $100 USDC purchase)

User: "buy $200"

Agent: [Restarts workflow, shows $200 USDC review]
```

---

## Amount Format Support

### Supported Formats

| Format | Example | Parsed |
|--------|---------|--------|
| Dollar sign | `$100` | 100 USD |
| Written | `100 dollars` | 100 USD |
| Euro sign | `€50` | 50 EUR |
| Written euro | `50 euros` | 50 EUR |
| Pound sign | `£200` | 200 GBP |
| Comma separator | `1,000` | 1000 |
| Decimal | `99.50` | 99.50 |
| Plain number | `500` | 500 (default USD) |

### Regex Pattern

```python
r"(?:[\$€£])?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:dollars?|usd|eur|gbp)?"
```

---

## Intent Detection Patterns

### Confirmation Intents

```python
confirm_words = [
    # English
    "yes", "y", "confirm", "ok", "proceed", "continue", "do it", "buy",
    
    # Spanish
    "sí", "si", "confirmar", "vale", "continuar", "comprar",
    
    # Portuguese
    "sim", "confirmar", "prosseguir",
    
    # Chinese
    "是", "确认", "好", "继续", "购买",
]
```

### Cancellation Intents

```python
# Using word boundaries for accuracy
cancel_patterns = [
    r'\bno\b', r'\bn\b', r'\bcancel\b', r'\babort\b', r'\bstop\b',
    r'\bnevermind\b', r'\bforget it\b',
    r'\bcancelar\b', r'\babortar\b', r'\bparar\b',
]

# CJK characters (no word boundaries)
cjk_cancel_words = ["取消", "不", "停止"]
```

---

## API Response Examples

### Successful Purchase Review

```json
{
  "agent_message": {
    "content": "💳 **Review Your Purchase**\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰 **Buying:** USDC 💵\n💵 **Amount:** $100 USD\n🌐 **Network:** Base\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**Payment Options:**\n• Credit/Debit Card\n• Apple Pay / Google Pay",
    "role": "assistant",
    "agent_type": "buy_workflow"
  },
  "execute_data": {
    "action_type": "buy",
    "provider": "privy",
    "chain": "base",
    "to_token": "USDC",
    "amount": "100",
    "from_token": "USD",
    "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "quote_id": "buy-usdc-100"
  },
  "enrichment": {
    "agent_timings": [...],
    "sources": [...]
  }
}
```

### Unsupported Crypto Response

```json
{
  "agent_message": {
    "content": "💡 **USDC Only Available**\n\nI see you want to buy **ETH**, but currently only **USDC** is available for direct purchase...",
    "role": "assistant",
    "agent_type": "buy_workflow"
  },
  "execute_data": null,
  "enrichment": {...}
}
```

### Amount Prompt

```json
{
  "agent_message": {
    "content": "💵 **Buy USDC**\n\nHow much USDC would you like to buy?\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**USDC** is a stablecoin pegged 1:1 to the US Dollar - perfect for:\n• 🔄 Swapping to other cryptos (ETH, BTC, SOL...)\n• 💰 Earning yield in DeFi\n• 📤 Sending to friends\n\n💬 Enter the amount in USD (e.g., \"100\" or \"$500\")\n\n💡 *Minimum: $30*",
    "role": "assistant",
    "agent_type": "buy_workflow"
  },
  "execute_data": null,
  "enrichment": {...}
}
```

---

## JSON Shortcut Configuration

For the `/api/v1/chat/shortcuts` endpoint:

```json
{
  "category": "buy",
  "shortcuts": [
    {
      "id": "buy_crypto",
      "label": "Buy crypto",
      "patterns": {
        "en": ["buy crypto", "buy USDC", "purchase crypto"],
        "es": ["comprar cripto", "comprar USDC"],
        "pt": ["comprar cripto", "comprar USDC"],
        "zh": ["购买加密货币", "购买 USDC"]
      },
      "agent": "buy_workflow",
      "description": "Buy USDC with card, Apple Pay, or Google Pay"
    },
    {
      "id": "buy_amount",
      "label": "Buy $100",
      "patterns": {
        "en": ["buy $100", "buy 100 dollars", "purchase $100"],
        "es": ["comprar $100", "comprar 100 dólares"],
        "pt": ["comprar $100", "comprar 100 dólares"],
        "zh": ["购买 $100", "购买一百美元"]
      },
      "agent": "buy_workflow",
      "description": "Quick purchase with specified amount"
    }
  ]
}
```

---

## Differentiation from Other Agents

### buy_workflow vs swap_workflow

| Query | Agent | Reason |
|-------|-------|--------|
| "buy $100 of USDC" | buy_workflow | Fiat-to-crypto |
| "swap 100 USDC to PURR" | swap_workflow | Crypto-to-crypto |
| "purchase crypto" | buy_workflow | Fiat on-ramp |
| "exchange USDC for ETH" | swap_workflow | Token exchange |

### buy_workflow vs transfer_workflow

| Query | Agent | Reason |
|-------|-------|--------|
| "buy $100" | buy_workflow | Fiat purchase |
| "send ETH to 0x..." | transfer_workflow | Token transfer |

### buy_workflow vs hunter_ai

| Query | Agent | Reason |
|-------|-------|--------|
| "buy $100 of ETH" | buy_workflow | Purchase execution |
| "price of ETH" | hunter_ai | Information query |
| "should I buy ETH" | hunter_ai | Analysis query |

---

## Common User Flows

### Flow 1: Direct Purchase

```
User: "buy $100 of USDC"
→ Agent shows purchase review with execute_data
→ Frontend opens Privy modal
→ User completes payment
```

### Flow 2: Generic Buy

```
User: "buy crypto"
→ Agent asks for amount (defaults to USDC)
User: "100"
→ Agent shows $100 USDC review
```

### Flow 3: Unsupported Crypto

```
User: "buy ETH"
→ Agent explains USDC only
→ Agent suggests buy USDC + swap
User: "$100"
→ Agent shows $100 USDC review
```

### Flow 4: Modification

```
User: "buy $50 of USDC"
→ Agent shows $50 review
User: "change to $100"
→ Agent shows updated $100 review
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Buy Workflow Shortcuts**

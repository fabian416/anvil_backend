# Swap Workflow Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the shortcut patterns, multi-language support, and supervisor routing for the **SWAP_WORKFLOW** agent.

---

## Primary Patterns

### Swap Execution Patterns

| Pattern | Example | Agent |
|---------|---------|-------|
| `swap [amount] [token] to [token]` | "swap 100 USDC to PURR" | swap_workflow |
| `exchange [amount] [token] for [token]` | "exchange 50 USDC for TRUMP" | swap_workflow |
| `convert [amount] [token] to [token]` | "convert 1000 PEPE to USDC" | swap_workflow |
| `trade [token] to [token]` | "trade my PURR to USDC" | swap_workflow |
| `swap [token]` (partial) | "swap USDC" | swap_workflow (triggers selection) |

### Information Patterns (NOT swap_workflow)

| Pattern | Example | Agent |
|---------|---------|-------|
| `best swap rate [token] to [token]` | "best swap rate ETH to USDC" | hunter_ai |
| `what tokens can I swap` | "what tokens can I swap?" | knowledge |
| `price of [token]` | "price of PURR" | hunter_ai |

---

## Multi-Language Examples

### English (en)

```
Primary Commands:
• "swap 100 USDC to PURR"
• "exchange 50 USDC for TRUMP"
• "convert 1000 PEPE to USDC"
• "trade my PURR"

Confirmation:
• "yes", "confirm", "do it", "proceed"

Cancellation:
• "cancel", "no", "stop", "never mind"

Modification:
• "change to 200 USDC instead"
• "make it 50 instead"
• "use PEPE instead"
```

### Spanish (es)

```
Primary Commands:
• "cambiar 100 USDC a PURR"
• "intercambiar 50 USDC por TRUMP"
• "convertir 1000 PEPE a USDC"
• "quiero cambiar USDC"

Confirmation:
• "sí", "confirmar", "hazlo", "proceder"

Cancellation:
• "cancelar", "no", "parar", "dejarlo"

Modification:
• "cambiar a 200 USDC"
• "que sean 50"
```

### Portuguese (pt)

```
Primary Commands:
• "trocar 100 USDC para PURR"
• "cambiar 50 USDC por TRUMP"
• "converter 1000 PEPE para USDC"
• "quero trocar USDC"

Confirmation:
• "sim", "confirmar", "fazer", "prosseguir"

Cancellation:
• "cancelar", "não", "parar"

Modification:
• "mudar para 200 USDC"
• "fazer 50 em vez"
```

### Chinese (zh)

```
Primary Commands:
• "兑换 100 USDC 到 PURR"
• "交换 50 USDC 换 TRUMP"
• "转换 1000 PEPE 到 USDC"
• "我想交换 USDC"

Confirmation:
• "是", "确认", "执行", "继续"

Cancellation:
• "取消", "不", "停止"

Modification:
• "改为 200 USDC"
• "改成 50"
```

---

## Supervisor Routing Configuration

### From authenticated_supervisor.py

```python
"""
5. SWAP EXECUTION (CRITICAL - Multi-step workflow):
   - "swap X to Y", "exchange X for Y", "convert X to Y" (with specific amounts) → "swap_workflow" agent ONLY
   - The swap_workflow agent handles the COMPLETE multi-step swap process autonomously
   - Use "swap_workflow" when user wants to EXECUTE a swap (has specific amount like "0.5 ETH")
   - Examples: "swap 1 ETH to USDC", "exchange 100 USDC for ETH", "convert 0.5 ETH to DAI"
   - DO NOT combine swap_workflow with other agents - it handles everything internally
   
6. SWAP INFORMATION (what swaps are available - educational):
   - "what tokens can I swap", "swap options" → "knowledge" agent
   - "best swap rate", "compare swap prices" → "hunter_ai" agent
"""
```

### Routing Examples

```python
# Execution requests → swap_workflow
"swap 1 ETH to USDC" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Execute swap: 1 ETH to USDC"}}]}}
"exchange 100 USDC for ETH" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Execute swap: 100 USDC to ETH"}}]}}
"convert 0.5 ETH to DAI" → {{"tasks":[{{"agent_type":"swap_workflow","task_description":"Execute swap: 0.5 ETH to DAI"}}]}}

# Information requests → other agents
"best swap rate ETH to USDC" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get swap rate for ETH to USDC"}}]}}
"what tokens can I swap" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain available swap tokens"}}]}}
```

---

## Restart Detection Keywords

### Swap Restart Patterns

When user is in the middle of a swap flow and says any of these, the workflow restarts:

```python
restart_keywords = [
    # English
    "swap", "exchange", "trade",
    "i want to swap",
    
    # Spanish
    "cambiar", "intercambiar",
    "quiero cambiar", "quiero intercambiar",
    
    # Portuguese
    "trocar",
]
```

### Example

```
Current State: CONFIRM step (showing quote for 100 USDC → PURR)

User: "swap 200 USDC to TRUMP"

Agent: [Restarts workflow, shows new quote for 200 USDC → TRUMP]
```

---

## Token Selection Flow

### Trigger Pattern

When user provides only partial information:

```
User: "swap 100 USDC"       → Shows token selection menu
User: "exchange USDC"       → Asks for amount, then shows menu
User: "I want to swap"      → Asks for token and amount
```

### Selection Response Patterns

```python
# Number selection
"1" → Selects first token (PURR)
"5" → Selects fifth token (MOG)

# Direct symbol
"PURR" → Selects PURR
"trump" → Selects TRUMP (case-insensitive)
"Trump" → Selects TRUMP
```

### Invalid Selection Response

```
User: "xyz"

Agent:
❌ **Invalid selection:** "xyz"

Please enter:
• A number from **1-10** to select a token
• Or type a valid token symbol like **PURR**, **TRUMP**, **PEPE**

**Available tokens:** PURR, TRUMP, PEPE, HFUN, MOG, JEFF, WAGMI, GMEOW, CAPPY, MANLET
```

---

## Intent Detection Patterns

### Confirmation Intents

```python
def _parse_user_intent(self, message: str) -> str:
    text = message.lower().strip()
    
    # Confirm patterns
    if any(word in text for word in [
        "yes", "confirm", "do it", "proceed", "go ahead",
        "sí", "si", "confirmar", "hazlo",
        "sim", "confirmar", "fazer",
        "是", "确认", "执行",
    ]):
        return "confirm"
    
    # Cancel patterns
    if any(word in text for word in [
        "cancel", "no", "stop", "never mind", "abort",
        "cancelar", "no", "parar", "dejarlo",
        "cancelar", "não", "parar",
        "取消", "不", "停止",
    ]):
        return "cancel"
    
    # Modification patterns
    if any(word in text for word in [
        "change", "instead", "make it", "use", "switch",
        "cambiar a", "que sean", "usar",
        "mudar para", "fazer",
        "改为", "改成",
    ]):
        return "modify"
    
    return "unclear"
```

---

## API Response Examples

### Successful Quote (With Funds)

```json
{
  "agent_message": {
    "content": "📊 **Swap Quote**\n\n**100 USDC** → **1,234.56 PURR**\n\n💰 **Your Balance:** ~$500.00 ✅\n• Price Impact: 0.05%\n• Network: HYPERLIQUID\n• Aggregator: HYPERLIQUID\n\n⛽ **Est. Gas:** ~$0.0000",
    "role": "assistant",
    "agent_type": "swap_workflow"
  },
  "execute_data": {
    "action_type": "swap",
    "provider": "hyperliquid",
    "chain": "hyperliquid",
    "from_token": "USDC",
    "to_token": "PURR",
    "amount": "100",
    "slippage": 1.0
  },
  "enrichment": {
    "agent_timings": [
      {
        "agent_type": "supervisor",
        "duration_ms": 150
      },
      {
        "agent_type": "swap_workflow",
        "duration_ms": 450
      }
    ],
    "sources": [
      {
        "source_type": "api",
        "source_name": "Hyperliquid Spot",
        "citation_text": "Real-time order book quote"
      }
    ]
  }
}
```

### Quote With Insufficient Funds

```json
{
  "agent_message": {
    "content": "💡 **Heads up:** Your portfolio appears to have limited funds...\n\n📊 **Swap Quote**\n**100 USDC** → **1,234.56 PURR**",
    "role": "assistant",
    "agent_type": "swap_workflow"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [...],
    "sources": [...]
  }
}
```

### Unsupported Token

```json
{
  "agent_message": {
    "content": "❌ **Swap not supported: USDC → ETH**\n\nAnvil uses **Hyperliquid Spot** for swaps...",
    "role": "assistant",
    "agent_type": "swap_workflow"
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
  "category": "swap",
  "shortcuts": [
    {
      "id": "swap_meme",
      "label": "Swap meme tokens",
      "patterns": {
        "en": ["swap", "swap USDC", "swap to PURR"],
        "es": ["cambiar", "intercambiar USDC"],
        "pt": ["trocar", "trocar USDC"],
        "zh": ["兑换", "交换 USDC"]
      },
      "agent": "swap_workflow",
      "description": "Trade meme tokens on Hyperliquid Spot with zero gas fees"
    },
    {
      "id": "swap_quote",
      "label": "Get swap quote",
      "patterns": {
        "en": ["swap 100 USDC to PURR", "exchange 50 USDC for TRUMP"],
        "es": ["cambiar 100 USDC a PURR"],
        "pt": ["trocar 100 USDC para PURR"],
        "zh": ["兑换 100 USDC 到 PURR"]
      },
      "agent": "swap_workflow",
      "description": "Get real-time swap quote from Hyperliquid"
    }
  ]
}
```

---

## Differentiation from Other Agents

### swap_workflow vs hunter_ai

| Query | Agent | Reason |
|-------|-------|--------|
| "swap 100 USDC to PURR" | swap_workflow | Execution request |
| "best swap rate ETH to USDC" | hunter_ai | Information/rate query |
| "price of PURR" | hunter_ai | Price query |
| "compare swap prices" | hunter_ai | Comparison query |

### swap_workflow vs knowledge

| Query | Agent | Reason |
|-------|-------|--------|
| "swap 100 USDC to PURR" | swap_workflow | Execution request |
| "what tokens can I swap" | knowledge | Educational query |
| "how does swap work" | knowledge | Explanation query |
| "what is Hyperliquid" | knowledge | Protocol info |

### swap_workflow vs buy_workflow

| Query | Agent | Reason |
|-------|-------|--------|
| "swap 100 USDC to PURR" | swap_workflow | Crypto-to-crypto |
| "buy crypto" | buy_workflow | Fiat-to-crypto |
| "buy 100 USDC" | buy_workflow | Fiat on-ramp |
| "purchase ETH with card" | buy_workflow | Fiat payment |

---

## Error Flow Shortcuts

### User Tries Unsupported Token

```
User: "swap ETH to USDC"

Agent: [Shows unsupported message with alternatives]
```

### User Tries Non-USDC Pair

```
User: "swap PURR to TRUMP"

Agent:
❌ **Swap requires USDC: PURR → TRUMP**

Hyperliquid Spot only supports swaps **paired with USDC**.

**Try instead:**
• `swap PURR to USDC` - Sell PURR for USDC
• `swap USDC to TRUMP` - Buy TRUMP with USDC

**Two-step swap:**
1. First: `swap PURR to USDC`
2. Then: `swap USDC to TRUMP`
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Swap Workflow Shortcuts**

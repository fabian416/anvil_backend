# Activity/Transaction History Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented

---

## Overview

This document defines the shortcut patterns and routing configuration for the Activity/Transaction History feature.

---

## Shortcut Patterns

### Primary Patterns

| Pattern | Agent | Description |
|---------|-------|-------------|
| `my activity` | transaction_history | Show user's activity feed |
| `my transactions` | transaction_history | Show transaction list |
| `recent activity` | transaction_history | Show recent transactions |
| `show activity` | transaction_history | Display activity summary |
| `transaction history` | transaction_history | Show full history |
| `what have I done` | transaction_history | Show activity summary |
| `past swaps` | transaction_history | Show swap history |
| `activity summary` | transaction_history | Summarize activity |
| `show transactions` | transaction_history | Display transactions |

---

## Multi-Language Support

### English (en)

| Pattern | Example |
|---------|---------|
| `my activity` | "my activity" |
| `my transactions` | "show my transactions" |
| `recent activity` | "what's my recent activity" |
| `transaction history` | "show transaction history" |

### Spanish (es)

| Pattern | Example |
|---------|---------|
| `mi actividad` | "mi actividad" |
| `mis transacciones` | "mostrar mis transacciones" |
| `actividad reciente` | "cuál es mi actividad reciente" |
| `historial de transacciones` | "mostrar historial" |

### Portuguese (pt)

| Pattern | Example |
|---------|---------|
| `minha atividade` | "minha atividade" |
| `minhas transações` | "mostrar minhas transações" |
| `atividade recente` | "qual é minha atividade recente" |
| `histórico de transações` | "mostrar histórico" |

### Chinese (zh)

| Pattern | Example |
|---------|---------|
| `我的活动` | "我的活动" |
| `我的交易` | "显示我的交易" |
| `最近活动` | "最近的活动是什么" |
| `交易历史` | "显示交易历史" |

---

## Supervisor Routing Configuration

### Routing Rules

Located in `src/app/domain/services/agent_squad/authenticated_supervisor.py`:

```python
3. TRANSACTION HISTORY (authenticated - REAL data):
   - "my transactions", "transaction history", "recent activity" → "transaction_history" agent
   - "show transactions", "past swaps", "activity summary" → "transaction_history" agent
   - "my activity", "show activity", "what have I done" → "transaction_history" agent
```

### Example Mappings

```python
"my transactions" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show user's transaction history","depends_on":[]}}]}}
"recent activity" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show recent transaction activity","depends_on":[]}}]}}
"my activity" → {{"tasks":[{{"agent_type":"transaction_history","task_description":"Show user's activity and transactions","depends_on":[]}}]}}
```

---

## Differentiation from Other Agents

### Activity vs Portfolio

| Query | Agent | Why |
|-------|-------|-----|
| "my activity" | transaction_history | Asks about actions taken |
| "my portfolio" | portfolio | Asks about current holdings |
| "my balance" | portfolio | Asks about current value |
| "my transactions" | transaction_history | Asks about past transactions |

### Activity vs Wallet

| Query | Agent | Why |
|-------|-------|-----|
| "my activity" | transaction_history | Asks about transactions |
| "my wallet" | wallet | Asks about wallet address |
| "my wallet address" | wallet | Asks about address specifically |

---

## Intent Detection

### Keywords for Transaction History

```python
TRANSACTION_HISTORY_KEYWORDS = [
    "activity",
    "transactions",
    "transaction history",
    "recent activity",
    "show activity",
    "past swaps",
    "what have I done",
    "activity summary",
    "show transactions",
    # Spanish
    "actividad",
    "transacciones",
    "historial",
    # Portuguese
    "atividade",
    "transações",
    "histórico",
    # Chinese
    "活动",
    "交易",
    "历史",
]
```

### Keywords NOT for Transaction History

These go to other agents:

```python
# Portfolio agent
"portfolio", "balance", "holdings", "value", "assets"

# Wallet agent
"wallet", "wallet address", "address"
```

---

## API Response Examples

### Request

```http
POST /api/v1/conversations/{conversation_id}/messages
Authorization: Bearer {token}

{
  "content": "my activity",
  "language": "en"
}
```

### Response (Empty Balance)

```json
{
  "agent_message": {
    "content": "Your balance: $0.00\n\n• 💳 **Buy crypto** - Say \"buy crypto\" to purchase USDC...\n• 📥 **Receive crypto** - Transfer tokens from another wallet...",
    "routing": {
      "intent": "SUPERVISOR_WORKFLOW",
      "handler": "authenticated_supervisor"
    },
    "enrichment": {
      "agents_used": ["transaction_history"]
    }
  }
}
```

### Response (With Transactions)

```json
{
  "agent_message": {
    "content": "**Transaction Summary:**\n- Total Transactions: 15\n- 30-Day Volume: $2,450.00\n- Most Active Chain: Base\n\n**Recent Transactions (5 shown):**\n\n**1. SWAP** ✅\n   - Hash: `0x7a2b3...`\n...",
    "routing": {
      "intent": "SUPERVISOR_WORKFLOW",
      "handler": "authenticated_supervisor"
    },
    "enrichment": {
      "agents_used": ["transaction_history"]
    }
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
      "category": "activity",
      "items": [
        {
          "text": "My activity",
          "translations": {
            "en": "My activity",
            "es": "Mi actividad",
            "pt": "Minha atividade",
            "zh": "我的活动"
          },
          "agent": "transaction_history",
          "icon": "📋"
        },
        {
          "text": "Transaction history",
          "translations": {
            "en": "Transaction history",
            "es": "Historial de transacciones",
            "pt": "Histórico de transações",
            "zh": "交易历史"
          },
          "agent": "transaction_history",
          "icon": "📜"
        },
        {
          "text": "Recent activity",
          "translations": {
            "en": "Recent activity",
            "es": "Actividad reciente",
            "pt": "Atividade recente",
            "zh": "最近活动"
          },
          "agent": "transaction_history",
          "icon": "🕐"
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
def test_my_activity_routes_to_transaction_history():
    """Test 'my activity' routes correctly."""
    supervisor = AuthenticatedSupervisorCoordinator(...)
    
    plan = await supervisor.create_workflow_plan("my activity", ...)
    
    assert plan.tasks[0].agent_type == AgentType.TRANSACTION_HISTORY

def test_my_portfolio_routes_to_portfolio():
    """Test 'my portfolio' routes to portfolio (not transaction_history)."""
    supervisor = AuthenticatedSupervisorCoordinator(...)
    
    plan = await supervisor.create_workflow_plan("my portfolio", ...)
    
    assert plan.tasks[0].agent_type == AgentType.PORTFOLIO
```

### Multi-Language Tests

```python
@pytest.mark.parametrize("query,expected_agent", [
    ("my activity", AgentType.TRANSACTION_HISTORY),
    ("mi actividad", AgentType.TRANSACTION_HISTORY),
    ("minha atividade", AgentType.TRANSACTION_HISTORY),
    ("我的活动", AgentType.TRANSACTION_HISTORY),
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
| 2026-01-29 | Added "my activity" routing |
| 2026-01-29 | Multi-language support added |

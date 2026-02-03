# Transfer Workflow Shortcuts

**Version**: 1.0
**Date**: 2026-01-29

---

## Overview

This document defines the shortcut patterns for the Transfer Workflow, enabling users to initiate transfers through natural language commands.

---

## Shortcut Definitions

### 1. Transfer Token

**Intent**: `TRANSFER`

**Patterns**:
```
send {amount} {token} to {address}
transfer {amount} {token} to {address}
send {token} to {address}
transfer to {address}
```

**Examples**:
| Language | Example |
|----------|---------|
| English | "send 100 USDC to 0x742d..." |
| English | "transfer 50 ETH to vitalik.eth" |
| Spanish | "enviar 100 USDC a 0x742d..." |
| Spanish | "transferir 50 ETH a 0x742d..." |
| Portuguese | "enviar 100 USDC para 0x742d..." |
| Chinese | "发送 100 USDC 到 0x742d..." |

**Agent Routing**: `transfer_workflow`

**Parameters**:
- `token`: Token symbol (USDC, ETH, etc.)
- `amount`: Amount to transfer
- `recipient`: Wallet address

---

### 2. Send to Contact

**Intent**: `TRANSFER_CONTACT`

**Patterns**:
```
send {amount} {token} to {name}
pay {name} {amount} {token}
```

**Examples**:
- "send 50 USDC to John"
- "pay Alice 100 DAI"

**Note**: Contact names require address book lookup (future feature)

---

## Pattern Matching

### Token Extraction

```python
TOKEN_PATTERNS = [
    r"(\d+(?:\.\d+)?)\s*(eth|usdc|usdt|dai|weth|wbtc)",
    r"(eth|usdc|usdt|dai|weth|wbtc)\s*(\d+(?:\.\d+)?)",
]
```

### Address Extraction

```python
ADDRESS_PATTERNS = {
    # EVM addresses
    "evm": r"0x[a-fA-F0-9]{40}",
    # Solana addresses
    "solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}",
    # ENS names (future)
    "ens": r"[a-z0-9-]+\.eth",
}
```

### Amount Extraction

```python
AMOUNT_PATTERNS = [
    r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # $1,000.00
    r"(\d+(?:\.\d+)?)",                   # 100.5
]
```

---

## Multi-Language Keywords

### Send/Transfer Keywords

| Language | Keywords |
|----------|----------|
| English | send, transfer, pay |
| Spanish | enviar, transferir, pagar |
| Portuguese | enviar, transferir, pagar |
| Chinese | 发送, 转账, 支付 |

### Destination Keywords

| Language | Keywords |
|----------|----------|
| English | to, for |
| Spanish | a, para |
| Portuguese | para, a |
| Chinese | 到, 给 |

---

## Shortcut Configuration

### JSON Format

```json
{
  "shortcuts": [
    {
      "id": "transfer",
      "pattern": "send|transfer|enviar|transferir",
      "intent": "TRANSFER",
      "agent": "transfer_workflow",
      "examples": {
        "en": [
          "send 100 USDC to 0x742d35Cc...",
          "transfer ETH to my friend",
          "send tokens"
        ],
        "es": [
          "enviar 100 USDC a 0x742d35Cc...",
          "transferir ETH a mi amigo"
        ],
        "pt": [
          "enviar 100 USDC para 0x742d35Cc...",
          "transferir ETH para meu amigo"
        ],
        "zh": [
          "发送 100 USDC 到 0x742d35Cc...",
          "转账 ETH 给朋友"
        ]
      },
      "parameters": {
        "token": {
          "type": "string",
          "required": false,
          "default": null
        },
        "amount": {
          "type": "number",
          "required": false,
          "default": null
        },
        "recipient": {
          "type": "string",
          "required": false,
          "default": null
        }
      }
    }
  ]
}
```

---

## Intent Detection

### IntentDetectorV2 Integration

The transfer intent is detected by `IntentDetectorV2`:

```python
# Intent patterns
TRANSFER_PATTERNS = [
    r"send\s+\d+",
    r"transfer\s+\d+",
    r"send\s+\w+\s+to",
    r"transfer\s+to",
    r"enviar\s+\d+",
    r"transferir\s+\d+",
]

def detect_intent(message: str) -> Intent:
    for pattern in TRANSFER_PATTERNS:
        if re.search(pattern, message.lower()):
            return Intent.TRANSFER
```

### Supervisor Routing

For authenticated users, the supervisor routes transfer intents:

```python
# authenticated_supervisor.py

# Pattern matching for fresh workflow detection
TRANSFER_KEYWORDS = [
    "send", "transfer", "pay",
    "enviar", "transferir", "pagar",
]

def _detect_fresh_workflow_start(self, message: str) -> str | None:
    for keyword in TRANSFER_KEYWORDS:
        if keyword in message.lower():
            return "transfer_workflow"
    return None
```

---

## Workflow Continuation

### Wallet Address Recognition

The supervisor recognizes wallet addresses as valid workflow input:

```python
# Pattern for wallet addresses
is_parameter_like = (
    # EVM wallet addresses (0x followed by 40 hex chars)
    re.match(r'^0x[a-fA-F0-9]{40}$', user_msg_original) or
    # Solana wallet addresses (32-44 alphanumeric base58)
    re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', user_msg_original)
)
```

### Amount Recognition

```python
# Numeric values (amounts)
is_parameter_like = (
    re.match(r'^[\$]?\d+\.?\d*$', user_msg_lower) or
    user_msg_lower == "all"
)
```

---

## Conversation Flow Examples

### Complete Flow (English)

```
User: "send 100 USDC"
Agent: "📤 Sending 100 💵 USDC
        Where should I send this?
        💡 Paste the destination wallet address"

User: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
Agent: "🔍 Review Your Transfer
        📤 Sending: 100 USDC 💵
        📍 To: 0x742d35...f44e
        🔒 Safety Score: 65/100 (Medium Risk)
        ⚠️ You haven't sent to this address before"

User: "yes"
Agent: "✅ Transfer ready!" [execute_data provided]
```

### Complete Flow (Spanish)

```
User: "enviar 100 USDC"
Agent: "📤 Enviando 100 💵 USDC
        ¿A dónde debo enviarlo?
        💡 Pega la dirección de la billetera destino"

User: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
Agent: "🔍 Revisa Tu Transferencia
        📤 Enviando: 100 USDC 💵
        📍 A: 0x742d35...f44e
        🔒 Puntuación de Seguridad: 65/100 (Riesgo Medio)"

User: "sí"
Agent: "✅ ¡Transferencia lista!" [execute_data provided]
```

---

## API Response

### Shortcuts Endpoint

```
GET /api/v1/chat/shortcuts?lang=en
```

**Response** (transfer section):
```json
{
  "shortcuts": [
    {
      "category": "transfer",
      "title": "Send Tokens",
      "icon": "📤",
      "items": [
        {
          "text": "Send 100 USDC",
          "action": "send 100 USDC"
        },
        {
          "text": "Transfer ETH",
          "action": "transfer ETH"
        },
        {
          "text": "Send to address",
          "action": "send to 0x..."
        }
      ]
    }
  ]
}
```

---

## Error Messages

### Invalid Address

```
❌ Invalid Address

The address `wallet` doesn't appear to be valid.

Supported formats:
• Ethereum/Base: `0x` followed by 40 hex characters
• Solana: 32-44 alphanumeric characters

Please paste a valid wallet address.
```

### Missing Amount

```
💵 Send USDC

How much USDC would you like to send?

💡 Examples:
• `100` (one hundred USDC)
• `1000` (one thousand USDC)
• `all` (send entire balance)

💬 Enter the amount to continue
```

### Missing Token

```
📤 Transfer Tokens

Which token would you like to send?

Available tokens:
• ETH (Ethereum)
• USDC (USD Coin)
• USDT (Tether)
• DAI (Dai)
• WBTC (Wrapped Bitcoin)

💬 Type the token name or symbol
```

---

## Testing Shortcuts

### Test Cases

| Input | Expected Intent | Expected Agent |
|-------|-----------------|----------------|
| "send 100 USDC" | TRANSFER | transfer_workflow |
| "transfer ETH to 0x..." | TRANSFER | transfer_workflow |
| "enviar 50 DAI" | TRANSFER | transfer_workflow |
| "send tokens" | TRANSFER | transfer_workflow |
| "0x742d35..." | CONTINUATION | transfer_workflow |
| "yes" | CONFIRMATION | transfer_workflow |
| "cancel" | CANCELLATION | transfer_workflow |

---

## Related Documentation

- [README.md](./README.md) - Overview
- [architecture.md](./architecture.md) - Architecture details
- [safety_analysis.md](./safety_analysis.md) - Safety checks
- [implementation.md](./implementation.md) - Code details

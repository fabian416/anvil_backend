# Chat Execute Endpoint

Execute DeFi actions recommended by the chat AI.

## Endpoint

```http
POST /api/v1/user/chat/conversations/{conversation_id}/execute
```

## Overview

The execute endpoint allows users to act on recommendations from the chat AI. It supports a two-step confirmation flow:

1. **Simulate** (`confirmed: false`) - Get transaction preview without executing
2. **Execute** (`confirmed: true`) - Execute the transaction on-chain

## Supported Actions

| Action | Description | Required Fields |
|--------|-------------|-----------------|
| `swap` | Token swap via DEX | `from_token`, `to_token`, `amount` |
| `deposit` | Deposit to lending protocol | `protocol`, `token`, `amount` |
| `withdraw` | Withdraw from lending protocol | `protocol`, `token`, `amount` |
| `transfer` | Send tokens to address | `to_address`, `token`, `amount` |
| `approve` | Approve token spending | `spender`, `token`, `amount` |
| `bridge` | Cross-chain bridge | `from_chain`, `to_chain`, `token`, `amount` |

## Request Format

```json
{
  "action": "swap",
  "params": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.5",
    "slippage": 0.5
  },
  "confirmed": false,
  "language": "en"
}
```

## Examples

### Swap Simulation

**Request**:
```http
POST /api/v1/user/chat/conversations/abc123/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "action": "swap",
  "params": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0"
  },
  "confirmed": false,
  "language": "en"
}
```

**Response** (Simulation):
```json
{
  "status": "simulated",
  "action": "swap",
  "preview": {
    "from_token": "ETH",
    "from_amount": "1.0",
    "to_token": "USDC",
    "to_amount": "3024.50",
    "exchange_rate": "3024.50",
    "price_impact": "0.12%",
    "gas_estimate": "0.002 ETH",
    "gas_usd": "$6.05"
  },
  "message": "Ready to swap 1.0 ETH for ~3,024.50 USDC. Confirm to execute.",
  "requires_confirmation": true
}
```

### Swap Execution

**Request**:
```http
POST /api/v1/user/chat/conversations/abc123/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "action": "swap",
  "params": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0"
  },
  "confirmed": true,
  "language": "en"
}
```

**Response** (Executed):
```json
{
  "status": "executed",
  "action": "swap",
  "result": {
    "transaction_hash": "0x1234...abcd",
    "block_number": 12345678,
    "from_amount": "1.0",
    "to_amount": "3024.50",
    "gas_used": "0.0018 ETH"
  },
  "message": "Successfully swapped 1.0 ETH for 3,024.50 USDC",
  "explorer_url": "https://etherscan.io/tx/0x1234...abcd"
}
```

### Deposit to Aave

**Request**:
```http
POST /api/v1/user/chat/conversations/abc123/execute

{
  "action": "deposit",
  "params": {
    "protocol": "aave",
    "token": "USDC",
    "amount": "1000"
  },
  "confirmed": false,
  "language": "en"
}
```

**Response**:
```json
{
  "status": "simulated",
  "action": "deposit",
  "preview": {
    "protocol": "Aave V3",
    "token": "USDC",
    "amount": "1000",
    "current_apy": "4.25%",
    "estimated_daily_yield": "$0.12",
    "estimated_yearly_yield": "$42.50"
  },
  "message": "Ready to deposit 1,000 USDC to Aave V3 at 4.25% APY. Confirm to execute.",
  "requires_confirmation": true
}
```

### Bridge to Arbitrum

**Request**:
```http
POST /api/v1/user/chat/conversations/abc123/execute

{
  "action": "bridge",
  "params": {
    "from_chain": "ethereum",
    "to_chain": "arbitrum",
    "token": "USDC",
    "amount": "500"
  },
  "confirmed": false,
  "language": "en"
}
```

**Response**:
```json
{
  "status": "simulated",
  "action": "bridge",
  "preview": {
    "from_chain": "Ethereum",
    "to_chain": "Arbitrum",
    "token": "USDC",
    "amount": "500",
    "receive_amount": "499.50",
    "bridge_fee": "0.50 USDC",
    "estimated_time": "~10 minutes"
  },
  "message": "Ready to bridge 500 USDC from Ethereum to Arbitrum. Confirm to execute.",
  "requires_confirmation": true
}
```

## Multi-Language Support

The endpoint supports responses in multiple languages:

| Language | Code |
|----------|------|
| English | `en` |
| Spanish | `es` |
| Portuguese | `pt` |
| Mandarin | `zh` |
| French | `fr` |

**Example (Spanish)**:
```json
{
  "action": "swap",
  "params": {...},
  "confirmed": false,
  "language": "es"
}
```

**Response**:
```json
{
  "message": "Listo para intercambiar 1.0 ETH por ~3,024.50 USDC. Confirma para ejecutar."
}
```

## Error Responses

### Insufficient Balance
```json
{
  "status": "error",
  "error_code": "INSUFFICIENT_BALANCE",
  "message": "Insufficient ETH balance. You have 0.5 ETH but need 1.0 ETH.",
  "details": {
    "required": "1.0",
    "available": "0.5",
    "token": "ETH"
  }
}
```

### Invalid Action
```json
{
  "status": "error",
  "error_code": "INVALID_ACTION",
  "message": "Unsupported action: 'stake'. Supported actions: swap, deposit, withdraw, transfer, approve, bridge"
}
```

### Wallet Not Connected
```json
{
  "status": "error",
  "error_code": "WALLET_NOT_CONNECTED",
  "message": "Please connect your wallet to execute transactions."
}
```

## Implementation

The execute endpoint uses:
- **1inch** for swap quotes and execution
- **Aave Gateway** for money market operations
- **Morpho Gateway** for lending operations
- **LiFi** for cross-chain bridges

See `src/app/application/chat/commands/execute_action.py` for implementation.

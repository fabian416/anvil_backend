# ULTRA Arbitrage Bot API Reference

**Version**: 1.0
**Date**: 2026-01-29
**Base URL**: `/api/v1/ultra`

---

## Overview

The ULTRA Arbitrage Bot provides REST APIs for:

- **Arbitrage Discovery**: Find profitable opportunities
- **Flash Loans**: Multi-protocol flash loan support
- **MEV Protection**: Flashbots integration
- **Auto Executor**: Automated trading

All endpoints require authentication unless otherwise noted.

---

## Arbitrage Discovery

### GET /arbitrage/discover

Discover arbitrage opportunities across all DEXes.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| capital | float | No | 10000 | Starting capital USD |
| type | string | No | null | Filter: 2hop, 3hop, triangle |
| min_profit | float | No | null | Minimum profit USD |

**Response**:

```json
[
  {
    "opportunity_id": "ARB-1638360000-0001",
    "type": "2hop",
    "path": [
      {
        "dex": "uniswap_v2",
        "token_in": "WETH",
        "token_out": "USDC",
        "amount_in": "10000",
        "amount_out": "20000000",
        "price": "2000.0",
        "liquidity": "1000000",
        "fee_percentage": 0.3
      },
      {
        "dex": "sushiswap",
        "token_in": "USDC",
        "token_out": "WETH",
        "amount_in": "20000000",
        "amount_out": "10050",
        "price": "0.0005025",
        "liquidity": "1000000",
        "fee_percentage": 0.3
      }
    ],
    "expected_profit_usd": "95.50",
    "profit_percentage": 0.955,
    "required_capital": "10000",
    "estimated_gas_cost": "15.00",
    "confidence_score": 0.85
  }
]
```

**Example**:

```bash
curl "https://api.anvil.com/api/v1/ultra/arbitrage/discover?capital=10000&type=2hop&min_profit=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /arbitrage/opportunities

List previously discovered opportunities.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | int | No | 10 | Maximum results (1-100) |
| sort_by | string | No | profit | Sort: profit, confidence, timestamp |

**Response**: Same as `/discover`

---

### POST /arbitrage/simulate

Simulate opportunity execution with slippage.

**Request Body**:

```json
{
  "opportunity_id": "ARB-1638360000-0001"
}
```

**Response**:

```json
{
  "opportunity_id": "ARB-1638360000-0001",
  "type": "2hop",
  "expected_profit": "95.50",
  "simulated_profit": "94.55",
  "slippage_impact": "0.95",
  "success_probability": 0.85,
  "recommendation": "Execute"
}
```

---

### GET /arbitrage/statistics

Get discovery statistics.

**Response**:

```json
{
  "total_opportunities": 15,
  "by_type": {
    "2hop": 8,
    "3hop": 5,
    "triangle": 2
  },
  "total_potential_profit": "1250.00",
  "average_profit": "83.33",
  "best_opportunity": {
    "id": "ARB-1638360000-0001",
    "type": "2hop",
    "profit": "150.00"
  }
}
```

---

## Flash Loans

### GET /flash-loans/protocols

Get available flash loan protocols.

**Response**:

```json
{
  "protocols": [
    {
      "protocol": "aave_v3",
      "name": "Aave V3",
      "fee_percentage": 0.09,
      "max_loan_usd": "10000000",
      "supported_tokens": ["USDC", "USDT", "DAI", "WETH", "WBTC"],
      "requires_collateral": false
    },
    {
      "protocol": "balancer",
      "name": "Balancer",
      "fee_percentage": 0.0,
      "max_loan_usd": "5000000",
      "supported_tokens": ["USDC", "USDT", "DAI", "WETH"],
      "requires_collateral": false
    },
    {
      "protocol": "uniswap_v3",
      "name": "Uniswap V3",
      "fee_percentage": 0.0,
      "max_loan_usd": "20000000",
      "supported_tokens": ["USDC", "USDT", "DAI", "WETH", "WBTC"],
      "requires_collateral": false
    }
  ],
  "best_protocol": {
    "name": "Balancer",
    "fee_percent": 0.0
  }
}
```

---

### POST /flash-loans/simulate

Simulate flash loan execution.

**Request Body**:

```json
{
  "protocol": "aave_v3",
  "token": "USDC",
  "amount": 100000,
  "callback_strategy": "arbitrage"
}
```

**Response**:

```json
{
  "protocol": "aave_v3",
  "token": "USDC",
  "amount": "100000",
  "fee_usd": "90.00",
  "gas_cost_usd": "5.00",
  "total_cost": "95.00",
  "estimated_profit": "150.00",
  "net_profit": "55.00",
  "status": "profitable",
  "recommendation": "Execute"
}
```

---

### POST /flash-loans/execute

Execute flash loan on-chain.

**Request Body**:

```json
{
  "protocol": "aave_v3",
  "token": "USDC",
  "amount": 100000,
  "receiver_address": "0x...",
  "callback_data": "0x..."
}
```

**Response**:

```json
{
  "status": "success",
  "tx_hash": "0x1234567890abcdef...",
  "gas_used": 300000,
  "gas_price_gwei": 30,
  "profit_usd": "55.00",
  "fees_paid": "95.00",
  "execution_time": "2026-01-29T12:00:00Z"
}
```

---

## MEV Protection

### GET /mev/protection-info

Get MEV protection configuration.

**Response**:

```json
{
  "protection_level": "advanced",
  "use_flashbots": true,
  "use_private_relay": true,
  "use_mev_share": false,
  "max_gas_price_gwei": 150,
  "simulation_enabled": true,
  "mempool_scanning_enabled": false,
  "scanner_active": false,
  "features": {
    "private_relay": true,
    "bundle_simulation": true,
    "sandwich_prevention": true,
    "frontrunning_protection": true
  },
  "protection_levels": {
    "standard": "Basic Flashbots relay",
    "high": "Multi-relay + bundle optimization",
    "maximum": "Private relay + max gas priority"
  },
  "recommendation": "Use HIGH or MAXIMUM for trades >$10K"
}
```

---

### POST /mev/submit-bundle

Submit MEV-protected transaction bundle.

**Request Body**:

```json
{
  "transactions": [
    {
      "to": "0x...",
      "data": "0x...",
      "value": "0",
      "gas_limit": 200000
    }
  ],
  "expected_profit": 150.00,
  "protection_level": "high"
}
```

**Response**:

```json
{
  "bundle_id": "BUNDLE-1638360000-0001",
  "status": "submitted",
  "target_block": 18000001,
  "bundle_hash": "0x...",
  "protection_level": "high",
  "estimated_inclusion": "~12 seconds"
}
```

---

### GET /mev/check-status/{bundle_id}

Check bundle inclusion status.

**Response**:

```json
{
  "bundle_id": "BUNDLE-1638360000-0001",
  "status": "included",
  "block_number": 18000001,
  "profit_realized": "148.50",
  "gas_used": 180000,
  "inclusion_time": "2026-01-29T12:00:12Z"
}
```

---

## Auto Executor

### GET /auto-executor/status

Get automated executor status and metrics.

**Response**:

```json
{
  "status": "running",
  "metrics": {
    "total_trades": 150,
    "successful_trades": 142,
    "failed_trades": 8,
    "total_profit_usd": 12500.00,
    "average_profit_per_trade": 88.03,
    "success_rate": 94.67,
    "uptime_hours": 168,
    "last_trade": "2026-01-29T11:55:00Z"
  },
  "config": {
    "min_profit_threshold": 50,
    "max_capital_per_trade": 100000,
    "enabled_arbitrage_types": ["2hop", "3hop"],
    "protection_level": "high",
    "auto_execute": true
  },
  "current_activity": {
    "scanning": true,
    "pending_opportunities": 3,
    "executing": false
  }
}
```

---

### POST /auto-executor/start

Start automated arbitrage execution.

**Request Body**:

```json
{
  "min_profit": 100,
  "max_capital": 50000,
  "protection_level": "high",
  "arbitrage_types": ["2hop", "3hop"]
}
```

**Response**:

```json
{
  "status": "started",
  "message": "Auto-executor started successfully",
  "config": {
    "min_profit_threshold": 100,
    "max_capital_per_trade": 50000,
    "protection_level": "high"
  }
}
```

---

### POST /auto-executor/stop

Stop automated execution.

**Response**:

```json
{
  "status": "stopped",
  "message": "Auto-executor stopped successfully",
  "summary": {
    "session_duration": "4h 30m",
    "trades_executed": 15,
    "total_profit": 1250.00
  }
}
```

---

## Error Responses

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid token |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error |

### Error Response Format

```json
{
  "detail": "Invalid arbitrage type: invalid. Must be: 2hop, 3hop, triangle",
  "code": "INVALID_TYPE"
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Discovery | 10/min |
| Simulation | 20/min |
| Execution | 5/min |
| Status | 60/min |

---

## Authentication

All endpoints require Bearer token authentication:

```bash
curl "https://api.anvil.com/api/v1/ultra/..." \
  -H "Authorization: Bearer $TOKEN"
```

---

## WebSocket (Future)

Real-time opportunity streaming:

```javascript
const ws = new WebSocket("wss://api.anvil.com/ws/ultra/opportunities");
ws.onmessage = (event) => {
  const opportunity = JSON.parse(event.data);
  console.log(`New opportunity: $${opportunity.expected_profit_usd}`);
};
```

---

## SDK Example (Python)

```python
import httpx

class ULTRAClient:
    def __init__(self, token: str):
        self.client = httpx.AsyncClient(
            base_url="https://api.anvil.com/api/v1/ultra",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    async def discover_arbitrage(self, capital: float = 10000):
        response = await self.client.get(
            "/arbitrage/discover",
            params={"capital": capital},
        )
        return response.json()
    
    async def get_flash_loan_protocols(self):
        response = await self.client.get("/flash-loans/protocols")
        return response.json()
    
    async def submit_protected(self, transactions: list, profit: float):
        response = await self.client.post(
            "/mev/submit-bundle",
            json={"transactions": transactions, "expected_profit": profit},
        )
        return response.json()

# Usage
async def main():
    client = ULTRAClient(token="your-token")
    
    # Find opportunities
    opportunities = await client.discover_arbitrage(capital=10000)
    print(f"Found {len(opportunities)} opportunities")
    
    # Get best
    if opportunities:
        best = opportunities[0]
        print(f"Best: ${best['expected_profit_usd']} profit")
```

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-01-29 | Initial API release |

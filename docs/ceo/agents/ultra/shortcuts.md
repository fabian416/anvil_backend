# ULTRA Arbitrage Bot Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented

---

## Overview

This document defines the chat tool integration patterns for the ULTRA Arbitrage Bot.

---

## Tool Definitions

### Tool Types

```python
class ULTRAToolType(Enum):
    FLASH_LOANS = "ultra_flash_loans"
    ARBITRAGE_DISCOVERY = "ultra_arbitrage_discovery"
    MEV_PROTECTION = "ultra_mev_protection"
    AUTO_EXECUTOR = "ultra_auto_executor"
```

### Available Tools

| Tool Name | Type | Description |
|-----------|------|-------------|
| `get_flash_loan_info` | FLASH_LOANS | Get flash loan protocols and rates |
| `discover_arbitrage` | ARBITRAGE_DISCOVERY | Find arbitrage opportunities |
| `check_mev_protection` | MEV_PROTECTION | Check MEV protection status |
| `get_auto_executor_status` | AUTO_EXECUTOR | Get bot status and metrics |

---

## Tool Parameters

### get_flash_loan_info

```json
{
  "name": "get_flash_loan_info",
  "type": "ultra_flash_loans",
  "description": "Get information about flash loan protocols and best rates. Compares Aave V3, Balancer, and Uniswap V3 flash loan providers.",
  "parameters": {
    "type": "object",
    "properties": {
      "token_symbol": {
        "type": "string",
        "description": "Token to borrow via flash loan (e.g., ETH, USDC, DAI)"
      },
      "amount": {
        "type": "number",
        "description": "Amount to borrow (in token units)"
      }
    },
    "required": ["token_symbol", "amount"]
  }
}
```

### discover_arbitrage

```json
{
  "name": "discover_arbitrage",
  "type": "ultra_arbitrage_discovery",
  "description": "Scan for profitable arbitrage opportunities across DEXes. Analyzes 2-hop, 3-hop, and triangle arbitrage paths.",
  "parameters": {
    "type": "object",
    "properties": {
      "token_symbol": {
        "type": "string",
        "description": "Base token for arbitrage (e.g., ETH, USDC)"
      },
      "capital": {
        "type": "number",
        "description": "Available capital for arbitrage (in USD)"
      },
      "min_profit": {
        "type": "number",
        "description": "Minimum profit threshold in USD (default: 50)",
        "default": 50
      }
    },
    "required": ["token_symbol", "capital"]
  }
}
```

### check_mev_protection

```json
{
  "name": "check_mev_protection",
  "type": "ultra_mev_protection",
  "description": "Check MEV protection status and simulate protected execution. Uses Flashbots private relay.",
  "parameters": {
    "type": "object",
    "properties": {
      "opportunity_id": {
        "type": "string",
        "description": "Arbitrage opportunity ID from discovery (optional)"
      },
      "protection_level": {
        "type": "string",
        "description": "MEV protection level: standard, high, maximum",
        "default": "high",
        "enum": ["standard", "high", "maximum"]
      }
    },
    "required": []
  }
}
```

### get_auto_executor_status

```json
{
  "name": "get_auto_executor_status",
  "type": "ultra_auto_executor",
  "description": "Get automated arbitrage executor status and configuration. Shows trades, success rate, and profit.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

---

## Chat Query Patterns

### Flash Loan Queries

| Pattern | Tool | Example |
|---------|------|---------|
| `flash loan {token}` | flash_loans | "flash loan 100 ETH" |
| `flash loan info for {token}` | flash_loans | "flash loan info for USDC" |
| `borrow {amount} {token}` | flash_loans | "borrow 50000 USDC" |
| `best flash loan rate` | flash_loans | "best flash loan rate for DAI" |

### Arbitrage Queries

| Pattern | Tool | Example |
|---------|------|---------|
| `find arbitrage` | arbitrage_discovery | "find arbitrage opportunities" |
| `arbitrage for {token}` | arbitrage_discovery | "arbitrage for ETH" |
| `scan for arbitrage` | arbitrage_discovery | "scan for arbitrage with $10000" |
| `profitable trades` | arbitrage_discovery | "find profitable trades" |

### MEV Queries

| Pattern | Tool | Example |
|---------|------|---------|
| `mev protection` | mev_protection | "check mev protection" |
| `flashbots status` | mev_protection | "flashbots status" |
| `protect my trade` | mev_protection | "protect my trade" |
| `sandwich protection` | mev_protection | "enable sandwich protection" |

### Auto Executor Queries

| Pattern | Tool | Example |
|---------|------|---------|
| `bot status` | auto_executor | "auto executor status" |
| `trading bot` | auto_executor | "check trading bot" |
| `auto trading` | auto_executor | "auto trading status" |
| `arbitrage bot` | auto_executor | "arbitrage bot metrics" |

---

## Response Formatting

### Flash Loans Response

```python
def _format_flash_loans_response(token: str, amount: float, data: dict) -> str:
    result = f"⚡ **Flash Loan Info for {amount} {token}:**\n\n"
    result += "**Available Protocols:**\n"
    
    for protocol in data.get("protocols", [])[:3]:
        name = protocol.get("name", "Unknown")
        fee = protocol.get("fee_percent", 0)
        liquidity = protocol.get("available_liquidity", 0)
        
        result += f"• **{name}**\n"
        result += f"  - Fee: {fee}%\n"
        result += f"  - Liquidity: ${liquidity:,.0f}\n"
    
    best = data.get("best_protocol", {})
    if best:
        result += f"\n**Recommended:** {best.get('name')} ({best.get('fee_percent')}% fee)"
    
    return result
```

### Arbitrage Response

```python
def _format_arbitrage_response(token: str, capital: float, data: dict) -> str:
    result = f"🔍 **Arbitrage Opportunities for {token}:**\n\n"
    
    opportunities = data.get("opportunities", [])
    if not opportunities:
        return result + f"No profitable opportunities found with ${capital:,.0f} capital."
    
    result += f"**Found {len(opportunities)} opportunities:**\n\n"
    
    for i, opp in enumerate(opportunities[:3], 1):
        profit = opp.get("estimated_profit_usd", 0)
        gas_cost = opp.get("estimated_gas_cost_usd", 0)
        net_profit = profit - gas_cost
        path = opp.get("path", [])
        
        emoji = "🟢" if net_profit > 100 else "🟡" if net_profit > 50 else "⚪"
        
        result += f"{emoji} **Opportunity #{i} ({opp.get('type')}):**\n"
        result += f"• Gross Profit: ${profit:.2f}\n"
        result += f"• Gas Cost: ${gas_cost:.2f}\n"
        result += f"• **Net Profit: ${net_profit:.2f}**\n"
        
        if path:
            result += f"• Path: {' → '.join(path)}\n"
        result += "\n"
    
    return result
```

### MEV Response

```python
def _format_mev_response(protection_level: str, data: dict) -> str:
    result = f"🛡️ **MEV Protection Status:**\n\n"
    result += f"**Protection Level:** {protection_level.upper()}\n\n"
    
    result += "**Flashbots Integration:**\n"
    result += "• ✅ Private transaction relay\n"
    result += "• ✅ Bundle simulation\n"
    result += "• ✅ Sandwich attack prevention\n"
    result += "• ✅ Front-running protection\n\n"
    
    result += "**Protection Levels:**\n"
    result += "• **Standard:** Basic Flashbots relay\n"
    result += "• **High:** Multi-relay + bundle optimization\n"
    result += "• **Maximum:** Private relay + max gas priority\n\n"
    
    result += "**Recommendation:** Use HIGH or MAXIMUM for trades >$10K"
    
    return result
```

### Auto Executor Response

```python
def _format_auto_executor_response(data: dict) -> str:
    status = data.get("status", "stopped")
    
    result = f"🤖 **Auto-Executor Status:**\n\n"
    
    if status == "running":
        result += "**Status:** 🟢 RUNNING\n\n"
    elif status == "paused":
        result += "**Status:** 🟡 PAUSED\n\n"
    else:
        result += "**Status:** 🔴 STOPPED\n\n"
    
    metrics = data.get("metrics", {})
    total_trades = metrics.get("total_trades", 0)
    successful = metrics.get("successful_trades", 0)
    total_profit = metrics.get("total_profit_usd", 0)
    success_rate = (successful / total_trades * 100) if total_trades > 0 else 0
    
    result += "**Performance:**\n"
    result += f"• Total Trades: {total_trades}\n"
    result += f"• Successful: {successful}\n"
    result += f"• Success Rate: {success_rate:.1f}%\n"
    result += f"• **Total Profit: ${total_profit:,.2f}**\n"
    
    return result
```

---

## Multi-Language Support

### English (en)

| Pattern | Example |
|---------|---------|
| Flash loans | "flash loan info for ETH" |
| Arbitrage | "find arbitrage opportunities" |
| MEV protection | "check mev protection" |
| Auto executor | "arbitrage bot status" |

### Spanish (es)

| Pattern | Example |
|---------|---------|
| Préstamos flash | "información de préstamo flash para ETH" |
| Arbitraje | "buscar oportunidades de arbitraje" |
| Protección MEV | "verificar protección MEV" |
| Auto ejecutor | "estado del bot de arbitraje" |

### Portuguese (pt)

| Pattern | Example |
|---------|---------|
| Empréstimos flash | "informação de empréstimo flash para ETH" |
| Arbitragem | "encontrar oportunidades de arbitragem" |
| Proteção MEV | "verificar proteção MEV" |
| Auto executor | "status do bot de arbitragem" |

### Chinese (zh)

| Pattern | Example |
|---------|---------|
| 闪电贷 | "ETH闪电贷信息" |
| 套利 | "寻找套利机会" |
| MEV保护 | "检查MEV保护" |
| 自动执行 | "套利机器人状态" |

---

## Shortcut Configuration (JSON)

For the shortcuts API endpoint:

```json
{
  "shortcuts": [
    {
      "category": "ultra",
      "items": [
        {
          "text": "Find arbitrage",
          "translations": {
            "en": "Find arbitrage opportunities",
            "es": "Buscar oportunidades de arbitraje",
            "pt": "Encontrar oportunidades de arbitragem",
            "zh": "寻找套利机会"
          },
          "agent": "ultra",
          "tool": "discover_arbitrage",
          "icon": "🔍"
        },
        {
          "text": "Flash loan info",
          "translations": {
            "en": "Flash loan info for USDC",
            "es": "Información de préstamo flash para USDC",
            "pt": "Informação de empréstimo flash para USDC",
            "zh": "USDC闪电贷信息"
          },
          "agent": "ultra",
          "tool": "get_flash_loan_info",
          "icon": "⚡"
        },
        {
          "text": "MEV protection",
          "translations": {
            "en": "Check MEV protection",
            "es": "Verificar protección MEV",
            "pt": "Verificar proteção MEV",
            "zh": "检查MEV保护"
          },
          "agent": "ultra",
          "tool": "check_mev_protection",
          "icon": "🛡️"
        },
        {
          "text": "Bot status",
          "translations": {
            "en": "Arbitrage bot status",
            "es": "Estado del bot de arbitraje",
            "pt": "Status do bot de arbitragem",
            "zh": "套利机器人状态"
          },
          "agent": "ultra",
          "tool": "get_auto_executor_status",
          "icon": "🤖"
        }
      ]
    }
  ]
}
```

---

## Intent Detection

### Keywords for ULTRA

```python
ULTRA_KEYWORDS = [
    # Flash loans
    "flash loan", "flash loans", "borrow", "flash borrow",
    "aave flash", "balancer flash", "uniswap flash",
    
    # Arbitrage
    "arbitrage", "arb", "profit opportunity",
    "cross-dex", "triangle", "price difference",
    
    # MEV
    "mev", "flashbots", "front-running", "sandwich",
    "private relay", "bundle", "protected",
    
    # Auto executor
    "auto executor", "trading bot", "arbitrage bot",
    "automated trading", "bot status",
    
    # Multi-language
    "préstamo flash", "empréstimo flash", "闪电贷",
    "arbitraje", "arbitragem", "套利",
    "protección", "proteção", "保护",
]
```

---

## Supervisor Routing

### Routing Rules

```python
"""
17. ULTRA ARBITRAGE:
    - Flash loan queries → ULTRA tools
    - Arbitrage discovery → ULTRA tools
    - MEV protection → ULTRA tools
    - Auto executor → ULTRA tools
"""
```

### Example Mappings

```python
"flash loan for 100 ETH" → ultra_flash_loans
"find arbitrage opportunities" → ultra_arbitrage_discovery
"check mev protection" → ultra_mev_protection
"arbitrage bot status" → ultra_auto_executor
```

---

## Testing

### Unit Tests

```python
def test_flash_loan_tool_invocation():
    """Test flash loan tool is invoked correctly."""
    executor = ULTRAToolExecutor()
    
    result = await executor.execute_tool(
        tool_type=ULTRAToolType.FLASH_LOANS,
        parameters={"token_symbol": "USDC", "amount": 100000},
    )
    
    assert "Flash Loan Info" in result
    assert "Aave V3" in result or "Balancer" in result

def test_arbitrage_discovery_tool():
    """Test arbitrage discovery tool."""
    executor = ULTRAToolExecutor()
    
    result = await executor.execute_tool(
        tool_type=ULTRAToolType.ARBITRAGE_DISCOVERY,
        parameters={"token_symbol": "ETH", "capital": 10000},
    )
    
    assert "Arbitrage Opportunities" in result
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial tool definitions |
| 2026-01-29 | Multi-language support |
| 2026-01-29 | Response formatting |

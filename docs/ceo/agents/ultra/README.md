# ULTRA Arbitrage Bot Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete Implementation
**Author**: Claude Code (Senior Python Backend Engineer)

---

## Overview

This directory contains comprehensive documentation for the **ULTRA Arbitrage Bot**, Anvil's advanced DeFi automation system providing:

- **Flash Loans**: Multi-protocol flash loan support (Aave V3, Balancer, Uniswap V3)
- **Arbitrage Discovery**: Multi-hop arbitrage opportunity scanning (2-hop, 3-hop, triangle)
- **MEV Protection**: Flashbots integration for front-running protection
- **Auto Executor**: Automated arbitrage execution with risk management

---

## Document Structure

### 1. [`architecture.md`](./architecture.md)

**Purpose**: Complete hexagonal architecture design for ULTRA

**Contents**:
- Domain layer components
- Application layer services
- Infrastructure adapters
- API controllers

### 2. [`implementation.md`](./implementation.md)

**Purpose**: Implementation details and code references

**Contents**:
- File locations and structure
- Key classes and methods
- Configuration options
- Tool definitions

### 3. [`api_reference.md`](./api_reference.md)

**Purpose**: REST API documentation

**Contents**:
- Endpoint specifications
- Request/response models
- Authentication requirements
- Usage examples

### 4. [`shortcuts.md`](./shortcuts.md)

**Purpose**: Chat integration patterns

**Contents**:
- Tool definitions for agents
- Chat-based invocations
- Response formatting

---

## Quick Start

### For Developers

1. **Read the architecture** (`architecture.md`) to understand the design
2. **Review implementation** (`implementation.md`) for code locations
3. **Check API reference** (`api_reference.md`) for endpoint usage

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Test arbitrage discovery with different capital levels
3. Verify MEV protection simulation

---

## Key Features

### 1. Flash Loans

| Protocol | Fee | Max Loan | Status |
|----------|-----|----------|--------|
| Aave V3 | 0.09% | $10M | ✅ Active |
| Balancer | 0% | $5M | ✅ Active |
| Uniswap V3 | 0% | $20M | ✅ Active |

### 2. Arbitrage Types

| Type | Description | Confidence |
|------|-------------|------------|
| 2-hop | Cross-DEX price differences | 85% |
| 3-hop | Multi-token circular paths | 75% |
| Triangle | Same-DEX triangular arbitrage | 80% |
| Cross-DEX | Real-time price scanning | 90% |

### 3. Supported DEXes

| DEX | Status | Tokens |
|-----|--------|--------|
| Uniswap V2 | ✅ Active | All |
| Uniswap V3 | ✅ Active | All |
| SushiSwap | ✅ Active | All |
| Curve | ✅ Active | Stables |
| Balancer | ✅ Active | All |

### 4. MEV Protection Levels

| Level | Features | Recommended For |
|-------|----------|-----------------|
| Standard | Basic Flashbots relay | < $5K trades |
| High | Multi-relay + optimization | $5K - $50K |
| Maximum | Private relay + max priority | > $50K |

---

## Architecture Principles

### Hexagonal Architecture (Clean Architecture)

```
Domain Layer (Entities, Value Objects)
    ↓
Application Layer (Discovery, Engine, Protection)
    ↓
Infrastructure Layer (DEX Adapters, Flashbots Client)
    ↓
Presentation Layer (REST API Controllers)
```

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ULTRA Arbitrage Bot                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Arbitrage       │  │ Flash Loan      │  │ MEV         │ │
│  │ Discovery       │  │ Engine          │  │ Protection  │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           ▼                    ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  Auto Executor                          ││
│  │         (Orchestrates all components)                   ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  DEX Adapters: Uniswap, SushiSwap, Curve, Balancer     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Arbitrage Discovery

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ultra/arbitrage/discover` | GET | Find arbitrage opportunities |
| `/api/v1/ultra/arbitrage/opportunities` | GET | List discovered opportunities |
| `/api/v1/ultra/arbitrage/simulate` | POST | Simulate opportunity execution |
| `/api/v1/ultra/arbitrage/statistics` | GET | Get discovery statistics |

### Flash Loans

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ultra/flash-loans/protocols` | GET | List available protocols |
| `/api/v1/ultra/flash-loans/simulate` | POST | Simulate flash loan |
| `/api/v1/ultra/flash-loans/execute` | POST | Execute flash loan |

### MEV Protection

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ultra/mev/protection-info` | GET | Get protection status |
| `/api/v1/ultra/mev/submit-bundle` | POST | Submit protected bundle |
| `/api/v1/ultra/mev/check-status` | GET | Check bundle status |

### Auto Executor

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ultra/auto-executor/status` | GET | Get executor status |
| `/api/v1/ultra/auto-executor/start` | POST | Start auto execution |
| `/api/v1/ultra/auto-executor/stop` | POST | Stop auto execution |

---

## Chat Integration

### Tool Types

```python
class ULTRAToolType(Enum):
    FLASH_LOANS = "ultra_flash_loans"
    ARBITRAGE_DISCOVERY = "ultra_arbitrage_discovery"
    MEV_PROTECTION = "ultra_mev_protection"
    AUTO_EXECUTOR = "ultra_auto_executor"
```

### Example Chat Queries

| Query | Tool | Response |
|-------|------|----------|
| "Find arbitrage for ETH" | arbitrage_discovery | List of opportunities |
| "Flash loan info for USDC" | flash_loans | Protocol comparison |
| "Check MEV protection" | mev_protection | Protection status |
| "Auto executor status" | auto_executor | Bot metrics |

---

## Example Conversations

### Arbitrage Discovery

```
User: "Find arbitrage opportunities with $10,000"

Agent:
🔍 **Arbitrage Opportunities for WETH:**

Found 3 opportunities:

🟢 **Opportunity #1 (2hop):**
• Gross Profit: $150.00
• Gas Cost: $15.00
• **Net Profit: $135.00**
• Path: Uniswap V2 → SushiSwap

🟡 **Opportunity #2 (triangle):**
• Gross Profit: $85.00
• Gas Cost: $20.00
• **Net Profit: $65.00**
• Path: WETH → USDC → DAI → WETH

**Total Potential (Top 3):** $275.00
```

### Flash Loan Info

```
User: "Get flash loan info for 100,000 USDC"

Agent:
⚡ **Flash Loan Info for 100,000 USDC:**

**Available Protocols:**
• **Balancer**
  - Fee: 0%
  - Liquidity: $2,000,000

• **Aave V3**
  - Fee: 0.09%
  - Liquidity: $5,000,000

• **Uniswap V3**
  - Fee: 0%
  - Liquidity: $10,000,000

**Recommended:** Balancer (0% fee)
```

### MEV Protection

```
User: "Check MEV protection status"

Agent:
🛡️ **MEV Protection Status:**

**Protection Level:** HIGH

**Flashbots Integration:**
• ✅ Private transaction relay
• ✅ Bundle simulation
• ✅ Sandwich attack prevention
• ✅ Front-running protection

**Recommendation:** Use HIGH or MAXIMUM for trades >$10K
```

---

## Configuration

### Default Parameters

```python
# Arbitrage Config
min_profit_usd = 50.0        # Min $50 profit
min_profit_percentage = 0.5%  # Min 0.5%
max_capital_per_trade = 100K  # Max $100K

# Flash Loan Config
aave_v3_fee = 0.09%          # 0.09%
balancer_fee = 0%            # 0%
uniswap_v3_fee = 0%          # 0%

# MEV Config
protection_level = ADVANCED   # Flashbots + optimization
max_gas_price_gwei = 150     # Max 150 gwei
```

---

## Testing Checklist

### Unit Tests
- [ ] ArbitrageDiscovery methods
- [ ] FlashLoanEngine calculations
- [ ] MEVProtection bundle creation

### Integration Tests
- [ ] DEX price fetching
- [ ] Flashbots relay simulation
- [ ] End-to-end arbitrage flow

### E2E Tests
- [ ] API endpoint responses
- [ ] Chat tool invocations
- [ ] Auto executor lifecycle

---

## Related Documentation

- **Chat Tool Executor**: `src/app/application/chat/services/ultra_tool_executor.py`
- **Tool Definitions**: `src/app/domain/value_objects/agent_tools/ultra_tools.py`
- **Hunter AI Agent**: `/docs/ceo/agents/hunter/` (market data)
- **Swap Workflow**: Uses some shared DEX infrastructure

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**End of ULTRA Arbitrage Bot Specification**

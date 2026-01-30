# Gas Optimizer Agent - Complete Index

> **Project:** Anvil DeFi Chat - Gas Fee Optimization
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **GAS_OPTIMIZER** agent, Anvil's multi-chain gas fee optimization system.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and gas topics |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Web3Client integration
- Chain detection logic
- Gas price calculation
- Timing recommendations

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Web3Client gas fetching
- Response building

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Gas analysis patterns and topics:

**Key Contents:**
- Supported query types
- Chain-specific queries
- Comparison patterns
- Timing recommendations

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Real-Time Ethereum | ✅ | Live gas prices via Web3Client |
| Multi-Chain Support | ✅ | 7 chains supported |
| Gas Tiers | ✅ | Slow/Standard/Fast |
| USD Estimates | ✅ | Cost projections |
| Timing Recommendations | ✅ | Low/Moderate/High |
| Layer 2 Suggestions | ✅ | Cost-saving alternatives |
| Source Attribution | ✅ | Blockchain sources |

### Supported Chains (7)

| Chain | Real-Time | Cost Savings |
|-------|-----------|--------------|
| Ethereum | ✅ Yes | Baseline |
| Polygon | Guidance | ~95% |
| Arbitrum | Guidance | ~90% |
| Optimism | Guidance | ~85% |
| Base | Guidance | ~90% |
| Avalanche | Guidance | Very cheap |
| BSC | Guidance | Much cheaper |

---

## 📊 Key Metrics

### Performance Targets

- **Web3Client Gas Fetch**: < 500ms
- **LLM Analysis**: < 1000ms
- **Total Response**: < 2s

### Gas Analysis Capabilities

- **Real-time prices**: Ethereum (Alchemy/Infura)
- **Price tiers**: Slow, Standard, Fast
- **USD estimates**: For standard transfers
- **Timing advice**: Based on current levels
- **L2 suggestions**: When gas is high

---

## 🔗 Related Specifications

### Agent Dependencies

- **Web3Client**: For real-time gas prices
- **Hunter AI**: For market context
- **Swap Workflow**: For transaction execution

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/gas_optimizer_agent.py`

**External Clients:**
- `src/app/infrastructure/adapters/external/web3_client.py`

**Application Layer:**
- `src/app/application/agents/library/gas_optimization_expert.py` (config)

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_gas_optimizer_agent)

**Knowledge Base:**
- `anvil_knowledge/features/gas_optimizer.json`

---

## 🚀 Gas Analysis Journey

### Standard Flow

```
1. User says: "What are gas prices on Ethereum?"
   → Supervisor routes to gas_optimizer

2. Detect chain from message
   → "ethereum" detected

3. Fetch real-time gas prices
   → Web3Client.get_gas_price()
   → Returns: base_fee, priority_fee, max_fee

4. Calculate tiers
   → Slow: base_fee only
   → Standard: base_fee + priority_fee
   → Fast: max_fee

5. Estimate USD costs
   → (gwei × 21000 / 1e9) × ETH_price

6. Generate recommendations
   → If < 30 gwei: "Low - execute now"
   → If 30-100 gwei: "Moderate - proceed"
   → If > 100 gwei: "High - wait or L2"

7. Return response
   → Gas prices + recommendations
```

### Multi-Chain Flow

```
1. User says: "Compare gas on Ethereum vs Arbitrum"
   → Supervisor routes to gas_optimizer

2. Detect chains from message
   → ["ethereum", "arbitrum"] detected

3. For Ethereum:
   → Real-time gas prices from Web3Client

4. For Arbitrum:
   → Typical gas price guidance
   → ~90% savings vs Ethereum

5. Generate comparison
   → Side-by-side costs
   → Savings calculation
   → Recommendation

6. Return response
   → Comparison table + advice
```

---

## 🔑 Critical Rules

### Chain Detection Patterns

```python
# Ethereum
if any(word in message_lower for word in ["ethereum", "eth", "mainnet"]):
    chains_to_check.append("ethereum")

# Polygon
if any(word in message_lower for word in ["polygon", "matic"]):
    chains_to_check.append("polygon")

# Arbitrum
if any(word in message_lower for word in ["arbitrum", "arb"]):
    chains_to_check.append("arbitrum")

# Default: Ethereum
if not chains_to_check:
    chains_to_check = ["ethereum"]
```

### Gas Thresholds

```python
# Low gas (< 30 gwei)
→ "Good time to send transactions"

# Moderate gas (30-100 gwei)
→ "Standard transactions should work well"

# High gas (> 100 gwei)
→ "Consider waiting or using Layer 2"
```

---

## 📝 Document Maintenance

**Last Updated:** 2026-01-29
**Review Frequency:** Monthly

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**For questions or clarifications, refer to the README.md in this directory.**

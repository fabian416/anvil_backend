# Transfer Workflow Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete Implementation
**Author**: Claude Code (Senior Python Backend Engineer)

---

## Overview

This directory contains comprehensive documentation for the **Transfer Workflow** feature, enabling secure token transfers with advanced safety analysis including:

- **EOA vs Smart Contract detection**
- **Etherscan address labels** (exchanges, DeFi protocols)
- **Interaction history** (first-time recipient detection)
- **Safety score and risk levels**
- **Multi-language support** (en, es, pt, zh)

---

## Document Structure

### 1. [`architecture.md`](./architecture.md)

**Purpose**: Complete hexagonal architecture design for transfer workflow

**Contents**:
- Domain layer entities and value objects
- Safety analysis data structures
- Workflow step handlers
- Web3 and Etherscan integration
- Multi-agent coordination

### 2. [`safety_analysis.md`](./safety_analysis.md)

**Purpose**: Detailed safety check implementation

**Contents**:
- Phase 1: EOA vs Contract detection
- Phase 2: Etherscan API integration
- Phase 3: Future compliance integration
- Safety score calculation
- Risk level classification

### 3. [`implementation.md`](./implementation.md)

**Purpose**: Implementation details and code references

**Contents**:
- File locations and structure
- Dependency injection configuration
- API endpoints
- Error handling

### 4. [`shortcuts.md`](./shortcuts.md)

**Purpose**: Shortcut configuration for transfer intents

**Contents**:
- Pattern matching
- Multi-language examples
- Agent routing

---

## Quick Start

### For Developers

1. **Read the architecture** (`architecture.md`) to understand the workflow design
2. **Review safety analysis** (`safety_analysis.md`) for security implementation
3. **Check implementation** (`implementation.md`) for code locations

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Check safety score edge cases in `safety_analysis.md`
3. Test multi-language support

---

## Key Features

### 1. Multi-Step Workflow

The transfer workflow follows a structured multi-step process:

```
PARSE_REQUEST → FETCH_DATA → CONFIRM → EXECUTE → COMPLETED
```

| Step | Description |
|------|-------------|
| `PARSE_REQUEST` | Extract token, amount, and recipient from user message |
| `FETCH_DATA` | Validate address and perform safety analysis |
| `CONFIRM` | Show transfer review with safety info |
| `EXECUTE` | Generate execute_data for frontend |
| `COMPLETED` | Transfer successful |

### 2. Safety Analysis (Phase 1 + 2)

| Check | Source | Description |
|-------|--------|-------------|
| **Address Type** | Web3 RPC | EOA vs Smart Contract detection |
| **Address Labels** | Etherscan API V2 | Contract names, categories |
| **Verification** | Etherscan API V2 | Contract source code verified |
| **Interaction History** | Etherscan API V2 | Previous transfers to recipient |
| **Known Addresses** | Local Database | Exchanges, DeFi protocols |
| **Blocklist** | Local Database | Known scam/risky addresses |

### 3. Safety Score (0-100)

| Factor | Points |
|--------|--------|
| Known safe address | +20 |
| Verified contract | +10 |
| Previous interactions (5+) | +15 |
| Previous interactions (2-4) | +10 |
| Previous interactions (1) | +5 |
| EOA (not contract) | +5 |
| First-time recipient | -10 |
| Unverified contract | -5 |
| Unknown contract | -15 |
| Blockers (scam/risky) | -50 |

### 4. Risk Levels

| Score | Level | Emoji | Action |
|-------|-------|-------|--------|
| 80-100 | Low | 🟢 | Proceed with confidence |
| 60-79 | Medium | 🟡 | Proceed with caution |
| 40-59 | High | 🟠 | Review carefully |
| 0-39 | Critical | 🔴 | Consider cancelling |

---

## Architecture Principles

### Hexagonal Architecture (Clean Architecture)

```
Domain Layer (Safety Analysis, Workflow State)
    ↓
Application Layer (Supervisor Coordinator)
    ↓
Infrastructure Layer (Web3Client, EtherscanClient)
    ↓
Presentation Layer (Chat Endpoints)
```

### CQRS Pattern

- **Commands**: Execute transfers
- **Queries**: Get address info, safety analysis

### Port-Adapter Pattern

- **Ports**: `Web3ClientProtocol`, `EtherscanClient`
- **Adapters**: Web3 RPC, Etherscan API V2

---

## External Integrations

### 1. Web3 Client

**Purpose**: EOA vs Contract detection, balance checks

**Methods**:
- `is_contract(address)` - Check if address has bytecode
- `get_balance(address)` - Get native token balance
- `get_token_balance(token, wallet)` - Get ERC20 balance

### 2. Etherscan API V2

**Purpose**: Address labels, verification status, interaction history

**Endpoint**: `https://api.etherscan.io/v2/api?chainid={chain_id}`

**Features**:
- Single API key for 60+ EVM chains
- Contract source code verification
- Address labels (exchanges, protocols)
- Transaction history

**Configuration**:
```toml
[etherscan]
API_KEY = "your-key-here"
```

---

## Supported Tokens

| Token | Symbol | Decimals | Emoji |
|-------|--------|----------|-------|
| Ethereum | ETH | 18 | Ξ |
| Wrapped Ethereum | WETH | 18 | Ξ |
| USD Coin | USDC | 6 | 💵 |
| Tether | USDT | 6 | 💵 |
| Dai | DAI | 18 | 💰 |
| Wrapped Bitcoin | WBTC | 8 | ₿ |

---

## Supported Networks

| Network | Chain ID | Address Pattern |
|---------|----------|-----------------|
| Ethereum | 1 | `0x[a-fA-F0-9]{40}` |
| Base | 8453 | `0x[a-fA-F0-9]{40}` |
| Polygon | 137 | `0x[a-fA-F0-9]{40}` |
| Arbitrum | 42161 | `0x[a-fA-F0-9]{40}` |
| Optimism | 10 | `0x[a-fA-F0-9]{40}` |
| Solana | - | Base58 (32-44 chars) |

---

## Example Conversation

```
User: "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

Agent: 
🔍 **Review Your Transfer**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📤 **Sending:** 100 USDC 💵
📍 **To:** `0x742d35...f44e`
🌐 **Network:** Base
⚡ **Est. Fee:** ~$0.01-0.10 (Base L2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 **Safety Analysis**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 **Safety Score:** 65/100 (Medium Risk)
👤 External Wallet

**⚠️ Warnings:**
• You haven't sent to this address before

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **REMINDER:**
• Once confirmed, this transaction CANNOT be reversed
• Double-check the destination address

User: "yes"

Agent: ✅ Transfer ready! [execute_data provided to frontend]
```

---

## Testing Checklist

### Unit Tests
- [ ] Address validation (EVM, Solana)
- [ ] Safety score calculation
- [ ] Risk level classification
- [ ] Workflow state transitions

### Integration Tests
- [ ] Web3 contract detection
- [ ] Etherscan API calls
- [ ] Supervisor workflow continuation

### E2E Tests
- [ ] Complete transfer flow
- [ ] First-time recipient warning
- [ ] Known address detection
- [ ] Multi-language support

---

## Related Documentation

- **Lending Workflow**: `/docs/ceo/agents/lending/`
- **Swap Workflow**: `/docs/ceo/agents/swap/` (if exists)
- **Chat Architecture**: `/docs/ceo/CHAT_ARCHITECTURE.md`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**End of Transfer Workflow Specification**

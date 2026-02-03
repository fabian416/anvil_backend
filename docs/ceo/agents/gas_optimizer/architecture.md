# Gas Optimizer Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **GAS_OPTIMIZER** agent, providing real-time gas price analysis and optimization recommendations across multiple blockchain networks.

### Key Components

- **GasOptimizerAgent**: Agent Squad implementation
- **Web3Client**: Real-time Ethereum gas price fetching
- **Multi-Chain Support**: 7 blockchain networks

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   GAS OPTIMIZER ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Supervisor Coordinator  │
                    │  (Routing Logic)         │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   GasOptimizerAgent      │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                                     │
              ▼                                     ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│      Web3Client         │           │      Vertex AI LLM      │
│  (Alchemy/Infura RPC)   │           │    (Analysis + Tips)    │
└─────────────────────────┘           └─────────────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    GAS_OPTIMIZER = "gas_optimizer"  # Gas fee optimization
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
AGENT_MAPPING = {
    "optimize_gas": AgentType.GAS_OPTIMIZER,
    "gas_estimation": AgentType.GAS_OPTIMIZER,
}
```

---

## Infrastructure Layer

### GasOptimizerAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/gas_optimizer_agent.py`
**Lines**: ~369

```python
class GasOptimizerAgent:
    """
    Gas Optimizer Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Gas fee optimization & timing
    
    Capabilities:
    - Current gas price analysis
    - Gas price predictions (next hour, day)
    - Optimal transaction timing
    - Layer 2 migration recommendations
    - Batch transaction suggestions
    - Gas-efficient alternatives
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.2 (factual)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 65-285 | Main entry point |
| `is_available()` | 287-289 | Availability check |
| `_get_system_prompt()` | 291-368 | Gas optimization prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    web3_client: Any | None = None,     # Web3Client for real-time
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,           # Factual
    max_tokens: int = 1000,
):
```

---

## Web3Client Integration

### Gas Price Data Structure

```python
@dataclass
class GasPriceData:
    base_fee_gwei: float
    priority_fee_gwei: float
    max_fee_gwei: float
    estimated_cost_usd: float
```

### Real-Time Fetching

```python
# From execute() method

if web3_client:
    gas_price = await web3_client.get_gas_price()
    
    if gas_price:
        # Calculate tiers
        slow_gwei = gas_price.base_fee_gwei
        standard_gwei = gas_price.base_fee_gwei + gas_price.priority_fee_gwei
        fast_gwei = gas_price.max_fee_gwei
        
        # USD estimates (assuming $3000 ETH)
        slow_usd = (slow_gwei * 21000 / 1e9) * 3000
        standard_usd = gas_price.estimated_cost_usd
        fast_usd = (fast_gwei * 21000 / 1e9) * 3000
```

---

## Chain Detection Logic

### Supported Chains

```python
# Chain detection patterns

if any(word in message_lower for word in ["ethereum", "eth", "mainnet"]):
    chains_to_check.append("ethereum")

if any(word in message_lower for word in ["polygon", "matic"]):
    chains_to_check.append("polygon")

if any(word in message_lower for word in ["arbitrum", "arb"]):
    chains_to_check.append("arbitrum")

if any(word in message_lower for word in ["optimism", "op"]):
    chains_to_check.append("optimism")

if any(word in message_lower for word in ["base", "base network"]):
    chains_to_check.append("base")

if any(word in message_lower for word in ["avalanche", "avax"]):
    chains_to_check.append("avalanche")

if any(word in message_lower for word in ["bsc", "binance", "bnb"]):
    chains_to_check.append("bsc")

# Default to Ethereum
if not chains_to_check:
    chains_to_check = ["ethereum"]
```

### Chain-Specific Guidance

| Chain | Gas Unit | Typical Cost | Savings |
|-------|----------|--------------|---------|
| Ethereum | gwei | $1-50 | Baseline |
| Polygon | gwei | $0.01-0.05 | ~95% |
| Arbitrum | gwei | $0.10-0.50 | ~90% |
| Optimism | gwei | $0.10-1.00 | ~85% |
| Base | gwei | $0.10-0.50 | ~90% |
| Avalanche | nAVAX | $0.01-0.05 | Very cheap |
| BSC | gwei | $0.10-0.50 | Much cheaper |

---

## Gas Price Recommendations

### Threshold Logic

```python
# Timing recommendations based on gas price

if slow_gwei < 30:
    gas_price_context += "\n💡 **Recommendation**: Gas prices are LOW - good time to send transactions\n"

elif slow_gwei > 100:
    gas_price_context += "\n⚠️ **Recommendation**: Gas prices are HIGH - consider waiting or using Layer 2 (Arbitrum, Optimism, Base)\n"

else:
    gas_price_context += "\n✅ **Recommendation**: Gas prices are MODERATE - standard transactions should work well\n"
```

### Tier Calculation

```python
# EIP-1559 gas tiers

# Slow: Base fee only (cheapest, slowest)
slow_gwei = gas_price.base_fee_gwei

# Standard: Base fee + Priority fee (balanced)
standard_gwei = gas_price.base_fee_gwei + gas_price.priority_fee_gwei

# Fast: Max fee (fastest, most expensive)
fast_gwei = gas_price.max_fee_gwei
```

---

## System Prompt

```python
def _get_system_prompt(self) -> str:
    return """You are the Gas Optimizer, Anvil's multi-chain gas fee optimization specialist.

**CRITICAL: SUPPORT ALL BLOCKCHAINS**
- You optimize gas for ALL chains: Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche, BSC, etc.
- Each chain has different gas mechanisms and costs
- Provide chain-specific recommendations

Your expertise:
- Real-time gas price analysis (ALL chains)
- Gas price predictions (hourly, daily trends)
- Optimal transaction timing
- Cross-chain gas comparison
- Layer 2 migration recommendations
- Batch transaction optimization
- Gas-efficient alternatives

**Multi-Chain Gas Support:**

**Ethereum (ETH):**
- Gas measured in gwei
- EIP-1559: base fee + priority fee
- Price Levels: Low (10-30 gwei), Standard (30-50 gwei), Fast (50-100 gwei), Urgent (100+ gwei)

**Polygon (MATIC):**
- ~95% cheaper than Ethereum

**Arbitrum (ETH):**
- ~90% cheaper than Ethereum

**Optimism (ETH):**
- ~85% cheaper than Ethereum

**Base (ETH):**
- ~90% cheaper than Ethereum

For gas optimization, provide:
- Current gas prices for the relevant chain(s)
- Gas price trends (rising, falling, stable)
- Timing recommendations (send now vs wait)
- Cost estimates (USD) for the chain
- Cross-chain comparison (if applicable)
- Layer 2 alternatives (if on Ethereum)
- Batch transaction suggestions
"""
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_gas_optimizer_agent(
    self,
    llm_client: LLMClientGateway,
    web3_client: Web3ClientProtocol | None,
) -> GasOptimizerAgent:
    """Provide Gas Optimizer agent with optional Web3Client integration."""
    return GasOptimizerAgent(
        llm_client=llm_client,
        web3_client=web3_client,
    )
```

### Web3Client Fallback

```python
# In execute() method - handle wrong object injection

if web3_client and not hasattr(web3_client, 'get_gas_price'):
    logger.warning(f"Wrong object injected for web3_client")
    
    # Create client directly
    alchemy_key = os.getenv("ALCHEMY_API_KEY") or os.getenv("RPC_ALCHEMY_API_KEY")
    infura_key = os.getenv("INFURA_API_KEY") or os.getenv("RPC_INFURA_API_KEY")
    
    if alchemy_key or infura_key:
        from app.infrastructure.adapters.external.web3_client import Web3Client
        web3_client = Web3Client(
            alchemy_api_key=alchemy_key,
            infura_api_key=infura_key,
            chain=Chain.ETHEREUM,
        )
```

---

## Source Attribution

### Source Building

```python
sources = []
fetched_at = datetime.now(UTC)

# Add LLM source
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))

# Add blockchain source if gas prices were fetched
if web3_client and gas_price_context:
    chains_mentioned = []
    if "ethereum" in gas_price_context.lower():
        chains_mentioned.append("Ethereum")
    # ... other chains
    
    sources.append(create_blockchain_source(
        chain=", ".join(chains_mentioned),
        citation_text=f"Real-time gas prices from {chain_name} network(s)",
        fetched_at=fetched_at,
    ))
```

---

## Testing

### Test Cases

```python
# Chain detection
def test_ethereum_detection():
    agent = GasOptimizerAgent(mock_llm, mock_web3)
    chains = agent._detect_chains("What are gas prices on Ethereum?")
    assert "ethereum" in chains

# Gas price fetching
async def test_gas_price_fetch():
    gas = await web3_client.get_gas_price()
    assert gas.base_fee_gwei > 0
    assert gas.priority_fee_gwei >= 0

# Tier calculation
def test_tier_calculation():
    slow = base_fee
    standard = base_fee + priority_fee
    fast = max_fee
    assert slow < standard <= fast

# Recommendations
def test_low_gas_recommendation():
    # < 30 gwei → "LOW - good time to send"
    ...
```

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Web3Client fetch | < 500ms | Alchemy/Infura RPC |
| LLM analysis | < 1000ms | Vertex AI |
| Chain detection | < 10ms | Regex patterns |
| Total | < 2s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added multi-chain support |
| 2026-01-29 | Added Web3Client integration |
| 2026-01-29 | Added Layer 2 recommendations |
| 2026-01-29 | Added source attribution |

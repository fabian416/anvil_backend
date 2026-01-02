# ULTRA System

ULTRA is the advanced DeFi automation suite for Anvil, providing arbitrage discovery, flash loans, MEV protection, and automated trading.

## Overview

| Component | Description | Status |
|-----------|-------------|--------|
| **Arbitrage Discovery** | Multi-hop arbitrage opportunity detection | ✅ Working |
| **Flash Loan Engine** | Multi-protocol flash loan support | ✅ Working |
| **MEV Protection** | Flashbots integration for private transactions | ✅ Working |
| **Auto Executor** | Automated trading bot | ✅ Working |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ULTRA System                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────┐     ┌───────────────────┐               │
│  │ ArbitrageDiscovery│     │  FlashLoanEngine  │               │
│  │ - 2-hop           │     │ - Aave V3         │               │
│  │ - 3-hop           │     │ - Balancer        │               │
│  │ - Triangle        │     │ - Uniswap V3      │               │
│  └─────────┬─────────┘     └─────────┬─────────┘               │
│            │                         │                          │
│            ▼                         ▼                          │
│  ┌───────────────────────────────────────────────┐             │
│  │            ArbitrageExecutor                  │             │
│  │  Executes profitable opportunities with       │             │
│  │  MEV protection and flash loan support        │             │
│  └───────────────────┬───────────────────────────┘             │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────┐             │
│  │              MEVProtection                    │             │
│  │  - Flashbots relay                            │             │
│  │  - Private transactions                       │             │
│  │  - Bundle optimization                        │             │
│  └───────────────────────────────────────────────┘             │
│                                                                 │
│  ┌───────────────────────────────────────────────┐             │
│  │              AutoExecutor                     │             │
│  │  - Continuous scanning                        │             │
│  │  - Risk management                            │             │
│  │  - Automated execution                        │             │
│  └───────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Arbitrage Discovery

**Location**: `src/app/application/ultra/arbitrage_discovery.py`

Discovers arbitrage opportunities across multiple DEXes:

- **2-hop Arbitrage**: Buy on DEX A, sell on DEX B
- **3-hop Arbitrage**: Multi-token path across DEXes
- **Triangle Arbitrage**: Circular path on same DEX
- **Cross-DEX Arbitrage**: Real-time price comparison via 1inch

#### Data Sources

| Source | Type | Status | Notes |
|--------|------|--------|-------|
| **1inch API** | Real prices | 🟢 Ready | Requires API key |
| **CoinGecko** | Price reference | 🟢 Working | Rate limited (free) |
| **DeFiLlama** | TVL/Liquidity | 🟢 Working | No rate limits |
| **Simulated** | Demo data | 🟡 Fallback | Realistic variations |

#### Usage (Simulated Data):
```python
from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery
from decimal import Decimal

discovery = ArbitrageDiscovery()
opportunities = await discovery.discover_all_opportunities(Decimal("10000"))

for opp in opportunities:
    print(f"{opp.type.value}: ${opp.expected_profit_usd} profit")
```

#### Usage (Real Data with 1inch):
```python
from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery
from decimal import Decimal

discovery = ArbitrageDiscovery()

# Real-time prices via 1inch API
opportunities = await discovery.discover_with_real_data(
    capital=Decimal("10000"),
    oneinch_api_key="your-1inch-api-key",
    chain="ethereum"  # or "arbitrum", "base"
)

for opp in opportunities:
    is_real = opp.metadata.get("is_real_data", False)
    print(f"{opp.type.value}: ${opp.expected_profit_usd} (real={is_real})")
```

#### DEX Price Fetcher

**Location**: `src/app/application/ultra/dex_price_fetcher.py`

Standalone module for fetching real DEX prices:

```python
from app.application.ultra.dex_price_fetcher import DEXPriceFetcher
from decimal import Decimal

fetcher = DEXPriceFetcher(oneinch_api_key="...")

# Get real-time price
price = await fetcher.get_token_price("ETH")
print(f"ETH: ${price.price_usd} (source: {price.source})")

# Get quotes from multiple DEXes
quotes = await fetcher.get_multi_dex_quotes("WETH", "USDC", Decimal("1"))
for q in quotes:
    print(f"{q.dex}: {q.to_amount} USDC")

# Find arbitrage opportunity
arb = await fetcher.find_arbitrage_opportunity("WETH", "USDC", Decimal("10000"))
if arb:
    print(f"Profit: ${arb['net_profit_usd']}")

await fetcher.close()
```

**Supported DEXes**:
- Uniswap V2/V3
- SushiSwap
- Curve
- Balancer
- 1inch Aggregator (best price across all DEXes)

---

### 2. Flash Loan Engine

**Location**: `src/app/application/ultra/flash_loan_engine.py`

Multi-protocol flash loan support with unified interface:

| Protocol | Fee | Max Loan | Tokens |
|----------|-----|----------|--------|
| Aave V3 | 0.09% | $10M | USDC, USDT, DAI, WETH, WBTC |
| Balancer | 0.00% | $5M | USDC, USDT, DAI, WETH |
| Uniswap V3 | 0.00% | $20M | USDC, USDT, DAI, WETH, WBTC |

**Usage**:
```python
from app.application.ultra.flash_loan_engine import FlashLoanEngine, FlashLoanProtocol

engine = FlashLoanEngine()

# Get best protocol for loan
best = await engine.get_best_protocol("USDC", Decimal("100000"))
print(f"Best: {best}")  # FlashLoanProtocol.BALANCER (lowest fee)

# Get all protocols
protocols = await engine.get_protocols()
for p in protocols:
    print(f"{p.name}: {p.fee_percentage*100:.2f}% fee")
```

---

### 3. MEV Protection

**Location**: `src/app/application/ultra/mev_protection.py`

Protects transactions from MEV attacks using Flashbots:

**Protection Levels**:
- `NONE`: Public mempool (risky)
- `BASIC`: Private relay only
- `ADVANCED`: Flashbots + bundle optimization
- `MAXIMUM`: All protections + MEV-share

**Features**:
- Private transaction submission
- Bundle optimization
- Sandwich attack prevention
- Front-running protection

**Usage**:
```python
from app.application.ultra.mev_protection import MEVProtection

mev = MEVProtection()
info = mev.get_protection_info()

print(f"Level: {info['protection_level']}")
print(f"Flashbots: {info['use_flashbots']}")
print(f"Private Relay: {info['use_private_relay']}")
```

---

### 4. Auto Executor

**Location**: `src/app/application/ultra/auto_executor.py`

Automated trading bot with risk management:

**Features**:
- Continuous opportunity scanning
- Automatic profitable trade execution
- Integrated risk management
- MEV-protected execution

**States**:
- `STOPPED`: Bot is off
- `RUNNING`: Actively scanning and executing
- `PAUSED`: Temporarily suspended

**Usage**:
```python
from app.application.ultra.auto_executor import AutoExecutor

executor = AutoExecutor()

# Start automated trading
await executor.start()

# Check status
status = executor.get_status()
print(f"Status: {status['status']}")
print(f"Executions: {status['total_executions']}")

# Stop bot
await executor.stop()
```

---

## Chat Integration

ULTRA is fully integrated with the chat system:

### Authenticated Users

```http
POST /api/v1/user/chat/conversations/{id}/messages
{
  "content": "find arbitrage opportunities with $10000"
}
```

**Supported Intents**:
- `ultra_arbitrage`: "find arbitrage", "arbitrage opportunities"
- `ultra_flash_loans`: "flash loans", "borrow without collateral"
- `ultra_mev_protection`: "mev protection", "protect from frontrunning"
- `ultra_auto_executor`: "start trading bot", "auto executor status"

### Guest Users

Guest users can access ULTRA features in read-only mode:

```http
POST /api/v1/guest/chat
{
  "content": "tell me about flash loans",
  "language": "en"
}
```

---

## API Endpoints

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/user/ultra/arbitrage` | GET | Discover arbitrage opportunities |
| `/api/v1/user/ultra/flash-loans` | GET | Get flash loan protocols |
| `/api/v1/user/ultra/mev` | GET | Get MEV protection status |
| `/api/v1/user/ultra/auto-executor` | GET/POST | Control auto executor |

### Controllers

- `src/app/presentation/http/controllers/ultra/arbitrage.py`
- `src/app/presentation/http/controllers/ultra/flash_loans.py`
- `src/app/presentation/http/controllers/ultra/mev.py`
- `src/app/presentation/http/controllers/ultra/auto_executor.py`

---

## Risk Management

### Trade Validation

All trades are validated against risk parameters:

```python
from app.application.ultra.risk_manager import RiskManager, RiskProfile

risk_manager = RiskManager(RiskProfile(
    max_position_size=Decimal("50000"),
    max_daily_loss=Decimal("1000"),
    max_concurrent_trades=5,
))

allowed, reason = risk_manager.validate_trade(
    capital=Decimal("10000"),
    expected_profit=Decimal("50"),
    gas_cost=Decimal("10"),
)
```

### Risk Metrics

- Position size limits
- Daily loss limits
- Concurrent trade limits
- Success rate tracking

---

## Testing

Run ULTRA tests:

```bash
# Unit tests
pytest tests/integration/ultra/ -v

# Specific component
pytest tests/integration/ultra/test_arbitrage_discovery.py -v
pytest tests/integration/ultra/test_flash_loans.py -v
pytest tests/integration/ultra/test_mev_execution.py -v
```

---

## Configuration

ULTRA uses default configurations that can be customized:

### Arbitrage Config

```python
ArbitrageConfig(
    min_profit_usd=Decimal("50.0"),      # Min $50 profit
    min_profit_percentage=Decimal("0.005"),  # Min 0.5%
    min_confidence_score=0.7,            # Min 70% confidence
    max_capital_per_trade=Decimal("100000"),  # Max $100K
    max_slippage=Decimal("0.01"),        # Max 1%
)
```

### Flash Loan Config

```python
FlashLoanConfig(
    aave_v3_fee=Decimal("0.0009"),      # 0.09%
    min_profit_threshold=Decimal("10.0"),  # Min $10
    max_loan_amount_usd=Decimal("1000000"),  # Max $1M
)
```

### MEV Config

```python
MEVConfig(
    protection_level=ProtectionLevel.ADVANCED,
    use_flashbots=True,
    use_private_relay=True,
    max_gas_price_gwei=150,
)
```

---

## Future Enhancements

1. **Real DEX Integration**: Connect to actual on-chain price feeds
2. **Cross-Chain Arbitrage**: Multi-chain opportunity detection
3. **JIT Liquidity**: Just-in-time liquidity provision
4. **MEV-Share Revenue**: Revenue sharing from captured MEV
5. **ML-Based Detection**: Machine learning for opportunity prediction

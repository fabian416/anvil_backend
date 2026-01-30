# ULTRA Arbitrage Bot Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── application/
│   └── ultra/
│       ├── arbitrage_discovery.py      # Multi-hop discovery
│       ├── arbitrage_executor.py       # Execution engine
│       ├── auto_executor.py            # Automated trading
│       ├── contracts.py                # Smart contract ABIs
│       ├── dex_price_fetcher.py        # Real-time DEX prices
│       ├── flash_loan_engine.py        # Flash loan management
│       ├── flash_loan_executor.py      # On-chain execution
│       ├── flashbots_client.py         # Flashbots relay
│       ├── mempool_scanner.py          # Attack detection
│       ├── mev_protection.py           # MEV bundle protection
│       └── risk_manager.py             # Risk parameters
│
├── presentation/
│   └── http/
│       └── controllers/
│           └── ultra/
│               ├── arbitrage.py        # Discovery endpoints
│               ├── auto_executor.py    # Executor endpoints
│               ├── flash_loans.py      # Flash loan endpoints
│               └── mev.py              # MEV endpoints
│
├── domain/
│   ├── ultra/
│   │   ├── entities/                   # Domain entities
│   │   ├── value_objects/              # Value objects
│   │   ├── services/                   # Domain services
│   │   └── ports/                      # Interfaces
│   │
│   └── value_objects/
│       └── agent_tools/
│           └── ultra_tools.py          # Chat tool definitions
│
└── application/
    └── chat/
        └── services/
            └── ultra_tool_executor.py  # Chat tool executor
```

---

## Core Components

### 1. Arbitrage Discovery

**File**: `src/app/application/ultra/arbitrage_discovery.py`

**Lines**: ~800

**Key Classes**:

| Class | Description |
|-------|-------------|
| `ArbitrageType` | Enum: TWO_HOP, THREE_HOP, TRIANGLE, CROSS_DEX |
| `DEX` | Enum: UNISWAP_V2, UNISWAP_V3, SUSHISWAP, CURVE, BALANCER |
| `TradingPair` | Token swap on a DEX |
| `ArbitrageOpportunity` | Complete opportunity details |
| `ArbitrageConfig` | Discovery configuration |
| `ArbitrageDiscovery` | Main discovery engine |

**Key Methods**:

| Method | Description |
|--------|-------------|
| `discover_2hop_arbitrage()` | Cross-DEX price differences |
| `discover_3hop_arbitrage()` | Multi-token circular paths |
| `discover_triangle_arbitrage()` | Same-DEX triangular |
| `discover_all_opportunities()` | Run all in parallel |
| `discover_with_real_data()` | Use 1inch API |
| `simulate_opportunity()` | Calculate slippage impact |

### 2. Flash Loan Engine

**File**: `src/app/application/ultra/flash_loan_engine.py`

**Lines**: ~500

**Key Classes**:

| Class | Description |
|-------|-------------|
| `FlashLoanProtocol` | Enum: AAVE_V3, BALANCER, UNISWAP_V3 |
| `LoanStatus` | Enum: PENDING, SIMULATING, EXECUTING, SUCCESS, FAILED |
| `FlashLoanConfig` | Fees, limits, safety parameters |
| `FlashLoanRequest` | Loan request parameters |
| `FlashLoanResult` | Execution result |
| `ProtocolInfo` | Protocol details |
| `FlashLoanEngine` | Main engine |

**Key Methods**:

| Method | Description |
|--------|-------------|
| `get_protocols()` | List available protocols |
| `get_best_protocol()` | Select by fee and liquidity |
| `calculate_fees()` | Calculate total costs |
| `estimate_gas()` | Estimate gas usage |
| `validate_loan_request()` | Validate request parameters |
| `simulate_loan()` | Simulate execution |
| `execute_loan()` | Execute on-chain |

### 3. MEV Protection

**File**: `src/app/application/ultra/mev_protection.py`

**Lines**: ~800

**Key Classes**:

| Class | Description |
|-------|-------------|
| `BundleStatus` | Enum: PENDING, SUBMITTED, INCLUDED, FAILED |
| `ProtectionLevel` | Enum: NONE, BASIC, ADVANCED, MAXIMUM |
| `Transaction` | Transaction details |
| `MEVBundle` | Protected bundle |
| `FlashbotsResponse` | Relay response |
| `MEVConfig` | Protection configuration |
| `MEVProtection` | Main protection engine |

**Key Methods**:

| Method | Description |
|--------|-------------|
| `create_bundle()` | Create protected bundle |
| `simulate_bundle()` | Simulate execution |
| `submit_to_flashbots()` | Submit to Flashbots |
| `submit_bundle()` | Submit with best method |
| `check_bundle_status()` | Check inclusion |
| `start_scanner()` | Start mempool scanning |
| `check_transaction_safety()` | Detect attacks |
| `submit_protected()` | Auto-protected submission |

---

## Configuration

### Arbitrage Config

```python
@dataclass
class ArbitrageConfig:
    # Profitability thresholds
    min_profit_usd: Decimal = Decimal("50.0")      # Min $50
    min_profit_percentage: Decimal = Decimal("0.005")  # Min 0.5%
    min_confidence_score: float = 0.7              # Min 70%
    
    # Risk parameters
    max_capital_per_trade: Decimal = Decimal("100000")  # Max $100K
    max_slippage: Decimal = Decimal("0.01")        # Max 1%
    max_gas_price_gwei: int = 100                  # Max 100 gwei
    
    # Discovery settings
    enabled_dexes: list[DEX] = [UNISWAP_V2, UNISWAP_V3, SUSHISWAP, CURVE, BALANCER]
    enabled_tokens: list[str] = ["WETH", "USDC", "USDT", "DAI", "WBTC"]
    
    # Performance
    max_concurrent_checks: int = 10
    cache_ttl_seconds: int = 5
```

### Flash Loan Config

```python
@dataclass
class FlashLoanConfig:
    # Protocol fees (as decimal)
    aave_v3_fee: Decimal = Decimal("0.0009")   # 0.09%
    balancer_fee: Decimal = Decimal("0.0000")  # 0%
    uniswap_v3_fee: Decimal = Decimal("0.0000")  # 0%
    
    # Gas limits
    max_gas_price_gwei: int = 100
    gas_limit: int = 500000
    
    # Safety parameters
    min_profit_threshold: Decimal = Decimal("10.0")
    max_loan_amount_usd: Decimal = Decimal("1000000")
    slippage_tolerance: Decimal = Decimal("0.005")
    
    # Execution
    enable_simulation: bool = True
    enable_auto_execute: bool = False
```

### MEV Config

```python
@dataclass
class MEVConfig:
    # Protection settings
    protection_level: ProtectionLevel = ProtectionLevel.ADVANCED
    use_flashbots: bool = True
    use_private_relay: bool = True
    use_mev_share: bool = False
    
    # Bundle settings
    max_bundle_size: int = 5
    bundle_timeout_blocks: int = 3
    min_profit_for_bundle: Decimal = Decimal("100.0")
    
    # Gas settings
    max_gas_price_gwei: int = 150
    max_priority_fee_gwei: int = 50
    gas_price_buffer: Decimal = Decimal("1.1")
    
    # Safety
    enable_simulation: bool = True
    require_profit_guarantee: bool = True
```

---

## Tool Definitions

**File**: `src/app/domain/value_objects/agent_tools/ultra_tools.py`

### Tool Types

```python
class ULTRAToolType(Enum):
    FLASH_LOANS = "ultra_flash_loans"
    ARBITRAGE_DISCOVERY = "ultra_arbitrage_discovery"
    MEV_PROTECTION = "ultra_mev_protection"
    AUTO_EXECUTOR = "ultra_auto_executor"
```

### Tool Definitions

```python
ULTRA_TOOLS = [
    ULTRAToolDefinition(
        name="get_flash_loan_info",
        type=ULTRAToolType.FLASH_LOANS,
        description="Get flash loan protocols and rates",
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["token_symbol", "amount"],
        },
    ),
    ULTRAToolDefinition(
        name="discover_arbitrage",
        type=ULTRAToolType.ARBITRAGE_DISCOVERY,
        description="Scan for profitable arbitrage opportunities",
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {"type": "string"},
                "capital": {"type": "number"},
                "min_profit": {"type": "number", "default": 50},
            },
            "required": ["token_symbol", "capital"],
        },
    ),
    ULTRAToolDefinition(
        name="check_mev_protection",
        type=ULTRAToolType.MEV_PROTECTION,
        description="Check MEV protection status",
        parameters={
            "type": "object",
            "properties": {
                "opportunity_id": {"type": "string"},
                "protection_level": {
                    "type": "string",
                    "enum": ["standard", "high", "maximum"],
                    "default": "high",
                },
            },
        },
    ),
    ULTRAToolDefinition(
        name="get_auto_executor_status",
        type=ULTRAToolType.AUTO_EXECUTOR,
        description="Get automated executor status",
        parameters={
            "type": "object",
            "properties": {},
        },
    ),
]
```

---

## API Integration

### Request Flow

```
1. User sends "Find arbitrage for ETH" to chat
2. Supervisor routes to ULTRA tool
3. ULTRAToolExecutor.execute_tool() called
4. ArbitrageDiscovery.discover_all_opportunities()
5. Format response with opportunities
6. Return to user with sources
```

### Response Structure

```json
{
  "agent_message": {
    "content": "🔍 **Arbitrage Opportunities for WETH:**\n\n...",
    "sources": [
      {
        "source_type": "api",
        "source_name": "DEX Aggregator",
        "citation_text": "Real-time arbitrage from DEXes"
      }
    ]
  }
}
```

---

## Protocol Information

### Flash Loan Protocols

| Protocol | Fee | Max Loan | Tokens |
|----------|-----|----------|--------|
| Aave V3 | 0.09% | $10M | USDC, USDT, DAI, WETH, WBTC |
| Balancer | 0% | $5M | USDC, USDT, DAI, WETH |
| Uniswap V3 | 0% | $20M | USDC, USDT, DAI, WETH, WBTC |

### DEX Support

| DEX | Base Fee | Liquidity | Status |
|-----|----------|-----------|--------|
| Uniswap V2 | 0.3% | High | ✅ |
| Uniswap V3 | 0.05-1% | High | ✅ |
| SushiSwap | 0.3% | Medium | ✅ |
| Curve | 0.04% | High (Stables) | ✅ |
| Balancer | Variable | Medium | ✅ |

---

## Error Handling

### Discovery Errors

```python
try:
    opportunities = await discovery.discover_all_opportunities(capital)
except Exception as e:
    return f"❌ Error discovering arbitrage: {str(e)}"
```

### Flash Loan Errors

```python
is_valid, error = await engine.validate_loan_request(request)
if not is_valid:
    return FlashLoanResult(
        status=LoanStatus.FAILED,
        error_message=error,
    )
```

### MEV Errors

```python
if bundle.expected_profit < self.config.min_profit_for_bundle:
    raise ValueError(f"Profit ${expected_profit} below minimum")
```

---

## Logging

### Debug Logging

```python
logger.info(f"🔍 Discovering arbitrage with ${capital} capital")
logger.info(f"📊 Found {len(opportunities)} opportunities")
logger.warning(f"⚠️ Low liquidity detected: ${liquidity}")
logger.error(f"❌ Flash loan failed: {error}")
```

### Enable Debug Mode

```python
import logging
logging.getLogger("app.application.ultra").setLevel(logging.DEBUG)
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/ultra/test_arbitrage_discovery.py
pytest tests/unit/ultra/test_flash_loan_engine.py
pytest tests/unit/ultra/test_mev_protection.py

# Integration tests
pytest tests/integration/test_ultra_api.py

# All tests
make code.test
```

### Test Files

- `tests/unit/ultra/test_arbitrage_discovery.py`
- `tests/unit/ultra/test_flash_loan_engine.py`
- `tests/unit/ultra/test_mev_protection.py`
- `tests/integration/test_ultra_api.py`

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| 2-hop discovery | < 2s | ~1.5s |
| 3-hop discovery | < 3s | ~2.5s |
| All opportunities | < 5s | ~4s |
| Flash loan sim | < 2s | ~1s |
| Bundle creation | < 1s | ~500ms |
| API response | < 500ms | ~300ms |

### Caching Strategy

| Data Type | TTL | Storage |
|-----------|-----|---------|
| DEX prices | 5s | In-memory |
| Opportunities | 30s | In-memory |
| Protocol info | 5min | In-memory |
| Bundle status | Real-time | In-memory |

---

## Dependencies

### Required

```
httpx>=0.25.0       # HTTP client
web3>=6.0.0         # Ethereum
eth-account>=0.10.0 # Signing
```

### Optional

```
alchemy-sdk         # Mempool access
flashbots           # Flashbots relay
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added mempool scanning |
| 2026-01-29 | Added 1inch integration |
| 2026-01-29 | Added chat tool integration |

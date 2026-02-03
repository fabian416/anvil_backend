# ULTRA Arbitrage Bot Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **ULTRA Arbitrage Bot**, providing advanced DeFi automation including flash loans, arbitrage discovery, and MEV protection.

### Key Components

- **Arbitrage Discovery**: Multi-hop opportunity scanning
- **Flash Loan Engine**: Multi-protocol flash loan support
- **MEV Protection**: Flashbots integration
- **Auto Executor**: Automated execution with risk management

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ULTRA ARBITRAGE ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (REST API Controllers)  │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│  Arbitrage    │    │   Flash Loans     │    │   MEV           │
│  Controller   │    │   Controller      │    │   Controller    │
└───────┬───────┘    └──────────┬────────┘    └────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Application Layer   │
                    │  (Business Logic)    │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Arbitrage    │    │  Flash Loan      │    │   MEV           │
│  Discovery    │    │  Engine          │    │   Protection    │
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Infrastructure      │
                    │  (External APIs)     │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  DEX Price    │    │  Flashbots       │    │   Mempool       │
│  Fetcher      │    │  Client          │    │   Scanner       │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Enums

```python
# Arbitrage Types
class ArbitrageType(str, Enum):
    TWO_HOP = "2hop"
    THREE_HOP = "3hop"
    TRIANGLE = "triangle"
    CROSS_DEX = "cross_dex"

# Supported DEXes
class DEX(str, Enum):
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    BALANCER = "balancer"

# Flash Loan Protocols
class FlashLoanProtocol(str, Enum):
    AAVE_V3 = "aave_v3"
    BALANCER = "balancer"
    UNISWAP_V3 = "uniswap_v3"

# MEV Protection Levels
class ProtectionLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    MAXIMUM = "maximum"
```

### Data Classes

```python
@dataclass
class ArbitrageOpportunity:
    opportunity_id: str
    type: ArbitrageType
    path: list[TradingPair]
    expected_profit_usd: Decimal
    profit_percentage: Decimal
    required_capital: Decimal
    estimated_gas_cost: Decimal
    confidence_score: float
    timestamp: datetime

@dataclass
class TradingPair:
    dex: DEX
    token_in: str
    token_out: str
    amount_in: Decimal
    amount_out: Decimal
    price: Decimal
    liquidity: Decimal
    fee_percentage: Decimal

@dataclass
class FlashLoanRequest:
    protocol: FlashLoanProtocol
    token_address: str
    amount: Decimal
    receiver_address: str
    callback_data: bytes

@dataclass
class MEVBundle:
    bundle_id: str
    transactions: list[Transaction]
    target_block: int
    gas_price: int
    priority_fee: int
    expected_profit: Decimal
    status: BundleStatus
```

---

## Application Layer

### Arbitrage Discovery

**File**: `src/app/application/ultra/arbitrage_discovery.py`

```python
class ArbitrageDiscovery:
    """Arbitrage opportunity discovery engine."""
    
    def __init__(self, config: ArbitrageConfig = None):
        self.config = config or ArbitrageConfig()
    
    async def discover_2hop_arbitrage(capital: Decimal) -> list[ArbitrageOpportunity]:
        """Discover 2-hop cross-DEX arbitrage."""
        # Buy on DEX1, sell on DEX2
    
    async def discover_3hop_arbitrage(capital: Decimal) -> list[ArbitrageOpportunity]:
        """Discover 3-hop multi-token paths."""
        # A → B → C → A across DEXes
    
    async def discover_triangle_arbitrage(dex: DEX, capital: Decimal) -> list[ArbitrageOpportunity]:
        """Discover triangle arbitrage on single DEX."""
        # A → B → C → A on same DEX
    
    async def discover_all_opportunities(capital: Decimal) -> list[ArbitrageOpportunity]:
        """Run all discovery methods in parallel."""
    
    async def discover_with_real_data(capital: Decimal, oneinch_api_key: str) -> list[ArbitrageOpportunity]:
        """Use real DEX data via 1inch API."""
```

### Flash Loan Engine

**File**: `src/app/application/ultra/flash_loan_engine.py`

```python
class FlashLoanEngine:
    """Flash loan execution engine."""
    
    def __init__(self, config: FlashLoanConfig = None):
        self.config = config or FlashLoanConfig()
        self._protocols = self._initialize_protocols()
    
    async def get_protocols() -> list[ProtocolInfo]:
        """Get available flash loan protocols."""
    
    async def get_best_protocol(token: str, amount_usd: Decimal) -> FlashLoanProtocol:
        """Select best protocol by fee and liquidity."""
    
    async def calculate_fees(protocol: FlashLoanProtocol, amount_usd: Decimal) -> Decimal:
        """Calculate total fees including gas."""
    
    async def simulate_loan(request: FlashLoanRequest) -> FlashLoanResult:
        """Simulate flash loan execution."""
    
    async def execute_loan(request: FlashLoanRequest) -> FlashLoanResult:
        """Execute flash loan on-chain."""
```

### MEV Protection

**File**: `src/app/application/ultra/mev_protection.py`

```python
class MEVProtection:
    """MEV protection engine."""
    
    def __init__(self, config: MEVConfig = None):
        self.config = config or MEVConfig()
    
    async def create_bundle(transactions: list[Transaction], expected_profit: Decimal) -> MEVBundle:
        """Create MEV-protected bundle."""
    
    async def simulate_bundle(bundle: MEVBundle) -> tuple[bool, str]:
        """Simulate bundle execution."""
    
    async def submit_to_flashbots(bundle: MEVBundle) -> FlashbotsResponse:
        """Submit bundle to Flashbots relay."""
    
    async def submit_bundle(bundle: MEVBundle) -> FlashbotsResponse:
        """Submit with best protection method."""
    
    async def check_transaction_safety(token_pair: tuple, amount_usd: Decimal) -> dict:
        """Check for MEV attacks in mempool."""
    
    async def submit_protected(signed_tx: str) -> dict:
        """Submit with automatic MEV protection."""
```

### Auto Executor

**File**: `src/app/application/ultra/auto_executor.py`

```python
class AutoExecutor:
    """Automated arbitrage executor."""
    
    async def start():
        """Start auto execution."""
    
    async def stop():
        """Stop auto execution."""
    
    async def get_status() -> dict:
        """Get executor status and metrics."""
    
    async def execute_opportunity(opportunity: ArbitrageOpportunity) -> ExecutionResult:
        """Execute a specific opportunity."""
```

---

## Infrastructure Layer

### DEX Price Fetcher

**File**: `src/app/application/ultra/dex_price_fetcher.py`

```python
class DEXPriceFetcher:
    """Fetches real-time prices from DEXes."""
    
    def __init__(self, oneinch_api_key: str = None, chain: str = "ethereum"):
        self.oneinch_api_key = oneinch_api_key
        self.chain = chain
    
    async def get_quote(from_token: str, to_token: str, amount: Decimal) -> Quote:
        """Get swap quote from 1inch aggregator."""
    
    async def find_arbitrage_opportunity(token_a: str, token_b: str, capital: Decimal) -> dict:
        """Find arbitrage between two tokens."""
```

### Flashbots Client

**File**: `src/app/application/ultra/flashbots_client.py`

```python
class FlashbotsClient:
    """Client for Flashbots relay."""
    
    async def send_bundle(signed_txs: list[str], target_block: int) -> str:
        """Send bundle to Flashbots."""
    
    async def get_bundle_status(bundle_hash: str) -> dict:
        """Check bundle inclusion status."""

class MEVBlockerClient:
    """Client for MEV Blocker (simpler, no signing)."""
    
    async def send_raw_transaction(signed_tx: str) -> str:
        """Send transaction via MEV Blocker."""
```

### Mempool Scanner

**File**: `src/app/application/ultra/mempool_scanner.py`

```python
class MempoolScanner:
    """Real-time mempool scanner for attack detection."""
    
    def __init__(self, alchemy_api_key: str, chain: Chain):
        self.alchemy_api_key = alchemy_api_key
    
    async def start():
        """Start mempool monitoring."""
    
    async def stop():
        """Stop mempool monitoring."""
    
    async def detect_attack_on_transaction(token_pair: tuple, our_gas_price: int, our_amount_usd: Decimal) -> Attack:
        """Detect if our transaction is being attacked."""
    
    async def get_mempool_statistics() -> dict:
        """Get current mempool stats."""
```

---

## Presentation Layer

### Arbitrage Controller

**File**: `src/app/presentation/http/controllers/ultra/arbitrage.py`

```python
router = APIRouter(prefix="/user/ultra/arbitrage", tags=["ultra-arbitrage"])

@router.get("/discover")
async def discover_opportunities(capital: float, type: str = None, min_profit: float = None):
    """Discover arbitrage opportunities."""

@router.get("/opportunities")
async def list_opportunities(limit: int = 10, sort_by: str = "profit"):
    """List discovered opportunities."""

@router.post("/simulate")
async def simulate_opportunity(request: SimulationRequest):
    """Simulate opportunity execution."""

@router.get("/statistics")
async def get_statistics():
    """Get discovery statistics."""
```

### Flash Loans Controller

**File**: `src/app/presentation/http/controllers/ultra/flash_loans.py`

```python
router = APIRouter(prefix="/user/ultra/flash-loans", tags=["ultra-flash-loans"])

@router.get("/protocols")
async def get_protocols():
    """Get available flash loan protocols."""

@router.post("/simulate")
async def simulate_flash_loan(request: FlashLoanSimulationRequest):
    """Simulate flash loan execution."""

@router.post("/execute")
async def execute_flash_loan(request: FlashLoanExecuteRequest):
    """Execute flash loan on-chain."""
```

### MEV Controller

**File**: `src/app/presentation/http/controllers/ultra/mev.py`

```python
router = APIRouter(prefix="/user/ultra/mev", tags=["ultra-mev"])

@router.get("/protection-info")
async def get_protection_info():
    """Get MEV protection configuration."""

@router.post("/submit-bundle")
async def submit_bundle(request: BundleRequest):
    """Submit MEV-protected bundle."""

@router.get("/check-status/{bundle_id}")
async def check_bundle_status(bundle_id: str):
    """Check bundle inclusion status."""
```

---

## Chat Integration

### Tool Executor

**File**: `src/app/application/chat/services/ultra_tool_executor.py`

```python
class ULTRAToolExecutor:
    """Executes ULTRA tools and formats responses for chat."""
    
    async def execute_tool(tool_type: ULTRAToolType, parameters: dict) -> str:
        """Execute ULTRA tool and format response."""
    
    async def _execute_flash_loans(params: dict) -> str:
        """Execute flash loan info."""
    
    async def _execute_arbitrage_discovery(params: dict) -> str:
        """Execute arbitrage discovery."""
    
    async def _execute_mev_protection(params: dict) -> str:
        """Execute MEV protection check."""
    
    async def _execute_auto_executor(params: dict) -> str:
        """Execute auto executor status."""
```

### Tool Definitions

**File**: `src/app/domain/value_objects/agent_tools/ultra_tools.py`

```python
ULTRA_TOOLS = [
    ULTRAToolDefinition(
        name="get_flash_loan_info",
        type=ULTRAToolType.FLASH_LOANS,
        description="Get flash loan protocols and rates",
        parameters={...},
    ),
    ULTRAToolDefinition(
        name="discover_arbitrage",
        type=ULTRAToolType.ARBITRAGE_DISCOVERY,
        description="Scan for profitable arbitrage opportunities",
        parameters={...},
    ),
    ULTRAToolDefinition(
        name="check_mev_protection",
        type=ULTRAToolType.MEV_PROTECTION,
        description="Check MEV protection status",
        parameters={...},
    ),
    ULTRAToolDefinition(
        name="get_auto_executor_status",
        type=ULTRAToolType.AUTO_EXECUTOR,
        description="Get automated executor status",
        parameters={...},
    ),
]
```

---

## Data Flow

### Arbitrage Discovery Flow

```
1. User requests arbitrage discovery
2. ArbitrageDiscovery fetches prices from all DEXes
3. Calculate profit for 2-hop, 3-hop, triangle paths
4. Filter by min_profit and confidence
5. Sort by expected profit
6. Return opportunities with gas estimates
```

### Flash Loan Execution Flow

```
1. User requests flash loan
2. FlashLoanEngine selects best protocol
3. Simulate execution with slippage
4. Calculate fees and gas costs
5. If profitable, execute on-chain
6. Repay loan within same transaction
7. Return result with profit
```

### MEV Protection Flow

```
1. User submits transaction
2. Check mempool for attacks
3. If attack detected, route via Flashbots
4. Create bundle with priority fee
5. Submit to private relay
6. Wait for block inclusion
7. Return confirmation
```

---

## Error Handling

### Discovery Errors

```python
try:
    opportunities = await discovery.discover_all_opportunities(capital)
except DEXConnectionError:
    return {"error": "Unable to fetch DEX prices", "code": "DEX_UNAVAILABLE"}
except InsufficientLiquidityError:
    return {"error": "Insufficient liquidity", "code": "LOW_LIQUIDITY"}
```

### Flash Loan Errors

```python
try:
    result = await engine.execute_loan(request)
except LoanAmountExceededError:
    return {"error": "Amount exceeds protocol limit", "code": "AMOUNT_EXCEEDED"}
except InsufficientProfitError:
    return {"error": "Profit below threshold", "code": "LOW_PROFIT"}
```

### MEV Errors

```python
try:
    response = await protection.submit_bundle(bundle)
except FlashbotsRejectedError:
    return {"error": "Bundle rejected by Flashbots", "code": "BUNDLE_REJECTED"}
except BundleNotIncludedError:
    return {"error": "Bundle not included in block", "code": "NOT_INCLUDED"}
```

---

## Testing Strategy

### Unit Tests

```python
def test_arbitrage_discovery():
    discovery = ArbitrageDiscovery()
    opportunities = await discovery.discover_2hop_arbitrage(Decimal("10000"))
    assert len(opportunities) > 0
    assert all(o.expected_profit_usd > 0 for o in opportunities)

def test_flash_loan_fees():
    engine = FlashLoanEngine()
    fees = await engine.calculate_fees(FlashLoanProtocol.AAVE_V3, Decimal("100000"))
    assert fees == Decimal("95.0")  # 0.09% + gas

def test_mev_bundle_creation():
    protection = MEVProtection()
    tx = Transaction(to="0x...", data="0x...", ...)
    bundle = await protection.create_bundle([tx], Decimal("150"))
    assert bundle.status == BundleStatus.PENDING
```

### Integration Tests

```python
async def test_real_dex_prices():
    fetcher = DEXPriceFetcher(oneinch_api_key="...")
    quote = await fetcher.get_quote("WETH", "USDC", Decimal("1"))
    assert quote.output_amount > 0

async def test_flashbots_simulation():
    protection = MEVProtection()
    bundle = await protection.create_bundle([...], Decimal("100"))
    success, error = await protection.simulate_bundle(bundle)
    assert success
```

---

## Summary

ULTRA Arbitrage Bot implements:

1. **Hexagonal Architecture**: Clean separation of layers
2. **Multi-Protocol Flash Loans**: Aave V3, Balancer, Uniswap V3
3. **Arbitrage Discovery**: 2-hop, 3-hop, triangle, cross-DEX
4. **MEV Protection**: Flashbots, private relays, mempool scanning
5. **Auto Execution**: Automated trading with risk management
6. **Chat Integration**: Tool definitions for agent invocation
7. **REST API**: Full CRUD for all operations

All implementations follow established codebase patterns.

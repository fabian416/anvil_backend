# Balance & Position Data Model - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El modelo de datos de balances y posiciones en Anvil Backend está diseñado para:

1. **Portfolio Snapshots**: Capturas point-in-time de holdings de wallets
2. **Token Holdings**: Balances de tokens nativos y ERC-20 con valores USD
3. **DeFi Positions**: Posiciones en protocolos (Aave, Morpho, Compound)
4. **Perpetual Positions**: Posiciones de futuros (Hyperliquid)
5. **Earn Positions**: Posiciones de yield farming y staking
6. **Chain Addresses**: Balances por cadena para wallets multi-chain

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       BALANCE & POSITION DATA MODEL                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌────────────────┐
                                    │     Users      │
                                    └───────┬────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               │                            │                            │
               ▼                            ▼                            ▼
    ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
    │     Wallets      │         │  Earn Positions  │         │Hyperliquid Pos.  │
    └────────┬─────────┘         └──────────────────┘         └──────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────┐┌────────┐┌────────────────────┐
│ Chain  ││Portf.  ││   Transactions     │
│ Addr.  ││Snapshot│└────────────────────┘
└────────┘└───┬────┘
              │
              ▼
       ┌─────────────┐
       │   Token     │
       │  Holdings   │
       └─────────────┘

    ╔════════════════════════════════════════╗
    ║       EXTERNAL DeFi POSITIONS          ║
    ║  (Read from APIs, not persisted)       ║
    ╠════════════════════════════════════════╣
    ║  • Aave Position (lending/borrowing)   ║
    ║  • Morpho Position (vault deposits)    ║
    ║  • Compound Position (lending)         ║
    ║  • Perpetual Position (futures)        ║
    ╚════════════════════════════════════════╝
```

---

## Core Entities

### 1. PortfolioSnapshot Entity

**Location**: `src/app/domain/entities/portfolio_snapshot.py`

Represents a point-in-time capture of a wallet's holdings.

```python
@dataclass(eq=False, kw_only=True)
class PortfolioSnapshot(Entity[PortfolioSnapshotId]):
    """Point-in-time snapshot of wallet portfolio."""
    
    wallet_id: WalletId              # Wallet this belongs to
    chain: ChainType                 # Blockchain network
    total_usd: Decimal               # Total portfolio value in USD
    native_balance: Decimal          # Native token balance (ETH, MATIC)
    native_usd_value: Decimal | None # USD value of native balance
    captured_at: datetime            # When snapshot was taken
    created_at: CreatedAt
    holdings: list[TokenHolding]     # Individual token holdings
    
    # Computed Properties
    @property
    def token_count(self) -> int:
        """Number of token holdings (excluding native)."""
        return len(self.holdings)
    
    @property
    def has_value(self) -> bool:
        """Check if portfolio has any USD value."""
        return self.total_usd > 0
```

### 2. TokenHolding Entity

**Location**: `src/app/domain/entities/portfolio_snapshot.py`

Represents a single token holding within a snapshot.

```python
@dataclass
class TokenHolding:
    """Single token holding in a portfolio snapshot."""
    
    id_: TokenHoldingId
    snapshot_id: PortfolioSnapshotId
    token_address: str | None        # None for native token
    symbol: str                      # Token symbol (ETH, USDC)
    name: str                        # Token name
    decimals: int                    # Token decimals (usually 18)
    amount: Decimal                  # Raw amount in token units
    usd_value: Decimal | None        # USD value
    usd_price: Decimal | None        # Price per token in USD
    percentage: float                # % of total portfolio
```

### 3. ChainAddress Entity

**Location**: `src/app/domain/entities/chain_address.py`

Tracks balances per chain for multi-chain wallets.

```python
@dataclass(eq=False, kw_only=True)
class ChainAddress(Entity[ChainAddressId]):
    """Chain-specific address with balance."""
    
    wallet_id: WalletId
    chain: ChainType
    address: str
    is_active: bool
    balance_usd: Decimal             # Total USD value on this chain
    last_balance_update: datetime | None
    created_at: CreatedAt
```

### 4. EarnPosition Entity

**Location**: `src/app/domain/entities/earn_position.py`

Represents a yield farming or staking position.

```python
@dataclass(eq=False, kw_only=True)
class EarnPosition(Entity[EarnPositionId]):
    """Yield farming/staking position."""
    
    user_id: UserId
    wallet_id: WalletId
    chain: ChainType
    protocol: str                    # e.g., "aave", "compound", "yearn"
    asset: str                       # Token symbol
    amount_deposited: Decimal        # Original deposit amount
    current_value: Decimal | None    # Current value including rewards
    apy: Decimal | None              # APY at deposit time
    current_apy: Decimal | None      # Current APY
    rewards_earned: Decimal          # Accumulated rewards (in token)
    rewards_earned_usd: Decimal      # Rewards in USD
    status: EarnStatus               # ACTIVE, WITHDRAWN, EMERGENCY_EXIT
    
    # Transaction tracking
    transaction_hash: str | None
    deposit_tx_hash: str | None
    withdraw_tx_hash: str | None
    
    # Timestamps
    deposited_at: CreatedAt
    withdrawn_at: datetime | None
    created_at: CreatedAt
```

### 5. HyperliquidPosition Entity

**Location**: `src/app/domain/entities/hyperliquid_position.py`

Represents a perpetual futures position on Hyperliquid.

```python
@dataclass(eq=False, kw_only=True)
class HyperliquidPosition(Entity[HyperliquidPositionId]):
    """Perpetual futures position on Hyperliquid."""
    
    user_id: UserId
    wallet_id: WalletId
    symbol: str                      # e.g., "BTC-PERP"
    side: Side                       # LONG or SHORT
    leverage: Decimal                # Position leverage (1-100x)
    size: Decimal                    # Position size
    entry_price: Decimal             # Average entry price
    mark_price: Decimal | None       # Current market price
    liquidation_price: Decimal | None
    
    # PnL tracking
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal
    margin: Decimal                  # Margin requirement
    
    # Funding
    funding_rate: Decimal | None
    last_funding_payment: Decimal | None
    
    status: PositionStatus           # OPEN, CLOSED, LIQUIDATED
    hyperliquid_order_id: str | None
    
    # Timestamps
    opened_at: CreatedAt
    closed_at: datetime | None
    created_at: CreatedAt
```

---

## DeFi Position Entities (External - Not Persisted)

These entities represent positions read from external DeFi protocols via APIs. They are NOT persisted to the database.

### 6. AavePosition Entity

**Location**: `src/app/domain/entities/lending/aave_position.py`

Represents a complete lending/borrowing position on Aave V3.

```python
@dataclass
class AaveSupplyPosition:
    """Supply position for a single asset."""
    asset_address: str
    symbol: str
    balance: Decimal                 # Token amount supplied
    balance_usd: Decimal             # USD value
    apy: Decimal                     # Supply APY
    is_collateral: bool              # Used as collateral?

@dataclass
class AaveBorrowPosition:
    """Borrow position for a single asset."""
    asset_address: str
    symbol: str
    balance: Decimal                 # Token amount borrowed
    balance_usd: Decimal             # USD value
    apy: Decimal                     # Borrow APY
    borrow_type: str                 # "variable" or "stable"

@dataclass
class AavePosition:
    """Complete Aave V3 position."""
    
    user_address: str
    chain: str                       # "ethereum", "arbitrum", etc.
    
    # Aggregated values
    total_collateral_usd: Decimal
    total_debt_usd: Decimal
    available_borrow_usd: Decimal
    net_worth_usd: Decimal           # collateral - debt
    
    # Health metrics
    health_factor: Decimal           # > 1 is safe
    current_ltv: Decimal             # Current LTV ratio
    max_ltv: Decimal                 # Maximum LTV
    
    # E-mode (efficiency mode)
    e_mode_category: int
    e_mode_label: str | None
    
    # Individual positions
    supplies: list[AaveSupplyPosition]
    borrows: list[AaveBorrowPosition]
    
    updated_at: datetime | None
    
    # Computed properties
    @property
    def is_healthy(self) -> bool:
        """HF > 1"""
        return self.health_factor > 1
    
    @property
    def is_at_risk(self) -> bool:
        """1 < HF < 1.5"""
        return Decimal("1") < self.health_factor < Decimal("1.5")
    
    @property
    def is_liquidatable(self) -> bool:
        """HF < 1"""
        return self.health_factor < 1
    
    @property
    def total_supply_apy(self) -> Decimal:
        """Weighted average supply APY."""
    
    @property
    def total_borrow_apy(self) -> Decimal:
        """Weighted average borrow APY."""
    
    @property
    def net_apy(self) -> Decimal:
        """Supply earnings - borrow costs."""
```

### 7. MorphoPosition Entity

**Location**: `src/app/domain/entities/lending/morpho_position.py`

Represents a deposit in a MetaMorpho vault.

```python
@dataclass
class MorphoPosition:
    """MetaMorpho vault deposit position."""
    
    user_address: str
    vault_address: str
    vault_name: str
    asset_symbol: str
    shares: Decimal                  # Vault shares owned
    assets: Decimal                  # Current value in underlying
    deposited_assets: Decimal        # Original deposit amount
    apy: Decimal                     # Current vault APY
    deposited_at: datetime | None
    
    # Computed properties
    @property
    def earnings(self) -> Decimal:
        """Current - deposited."""
        return self.assets - self.deposited_assets
    
    @property
    def earnings_pct(self) -> Decimal:
        """Earnings as percentage."""
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.earnings > 0
```

### 8. Position Entity (Perpetual Futures)

**Location**: `src/app/domain/entities/perpetual/position.py`

Generic perpetual futures position (protocol-agnostic).

```python
@dataclass
class Position:
    """Open perpetual futures position."""
    
    symbol: str                      # e.g., "BTC-PERP"
    side: str                        # "long" or "short"
    size: Decimal
    entry_price: Decimal
    mark_price: Decimal
    unrealized_pnl: Decimal
    leverage: Decimal
    liquidation_price: Decimal
    margin_ratio: Decimal
    
    # Computed properties
    @property
    def pnl_pct(self) -> Decimal:
        """PnL as percentage of entry."""
    
    @property
    def position_value(self) -> Decimal:
        """Current position value = size * mark_price."""
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
```

---

## Enumerations

### EarnStatus

```python
class EarnStatus(Enum):
    ACTIVE = "active"              # Position is earning
    WITHDRAWN = "withdrawn"        # User withdrew funds
    EMERGENCY_EXIT = "emergency_exit"  # Emergency withdrawal
```

### PositionStatus

```python
class PositionStatus(Enum):
    OPEN = "open"                  # Position is active
    CLOSED = "closed"              # User closed position
    LIQUIDATED = "liquidated"      # Position was liquidated
```

### Side

```python
class Side(Enum):
    LONG = "long"                  # Bullish position
    SHORT = "short"                # Bearish position
```

---

## Database Schema

### Portfolio Snapshots Table

```sql
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Snapshot data
    chain VARCHAR(50) NOT NULL,           -- ChainType enum
    total_usd NUMERIC(20, 8) NOT NULL DEFAULT 0,
    native_balance NUMERIC(36, 18) NOT NULL DEFAULT 0,
    native_usd_value NUMERIC(20, 8),
    
    -- Timestamps
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_portfolio_snapshots_wallet_captured 
    ON portfolio_snapshots(wallet_id, captured_at);
CREATE INDEX idx_portfolio_snapshots_wallet_id ON portfolio_snapshots(wallet_id);
CREATE INDEX idx_portfolio_snapshots_chain ON portfolio_snapshots(chain);
CREATE INDEX idx_portfolio_snapshots_captured_at ON portfolio_snapshots(captured_at);
```

### Token Holdings Table

```sql
CREATE TABLE token_holdings (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    snapshot_id INTEGER NOT NULL REFERENCES portfolio_snapshots(id) ON DELETE CASCADE,
    
    -- Token data
    token_address VARCHAR(42),            -- NULL for native token
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    decimals INTEGER NOT NULL DEFAULT 18,
    
    -- Balance and value
    amount NUMERIC(36, 18) NOT NULL DEFAULT 0,
    usd_value NUMERIC(20, 8),
    usd_price NUMERIC(20, 8),
    percentage NUMERIC(10, 6) NOT NULL DEFAULT 0
);

-- Indexes
CREATE INDEX ix_token_holdings_snapshot_token 
    ON token_holdings(snapshot_id, token_address);
CREATE INDEX idx_token_holdings_snapshot_id ON token_holdings(snapshot_id);
CREATE INDEX idx_token_holdings_token_address ON token_holdings(token_address);
```

### Chain Addresses Table

```sql
CREATE TABLE chain_addresses (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Chain details
    chain VARCHAR(50) NOT NULL,           -- ChainType enum
    address VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Balance tracking
    balance_usd NUMERIC(20, 2) DEFAULT 0.00,
    last_balance_update TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_wallet_chain UNIQUE (wallet_id, chain)
);

-- Indexes
CREATE INDEX idx_chain_addresses_wallet_id ON chain_addresses(wallet_id);
CREATE INDEX idx_chain_addresses_chain ON chain_addresses(chain);
CREATE INDEX idx_chain_addresses_is_active ON chain_addresses(is_active);
```

### Earn Positions Table

```sql
CREATE TABLE earn_positions (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Position details
    chain VARCHAR(50) NOT NULL,           -- ChainType enum
    protocol VARCHAR(50) NOT NULL,        -- "aave", "compound", "yearn"
    asset VARCHAR(20) NOT NULL,
    amount_deposited NUMERIC(30, 18) NOT NULL,
    current_value NUMERIC(30, 18),
    
    -- APY tracking
    apy NUMERIC(8, 4),                    -- APY at deposit (e.g., 5.25%)
    current_apy NUMERIC(8, 4),            -- Current APY
    rewards_earned NUMERIC(30, 18) DEFAULT 0,
    rewards_earned_usd NUMERIC(20, 2) DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- EarnStatus enum
    
    -- Transaction tracking
    transaction_hash VARCHAR(66),
    deposit_tx_hash VARCHAR(66),
    withdraw_tx_hash VARCHAR(66),
    
    -- Timestamps
    deposited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    withdrawn_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_earn_positions_user_id ON earn_positions(user_id);
CREATE INDEX idx_earn_positions_chain ON earn_positions(chain);
CREATE INDEX idx_earn_positions_protocol ON earn_positions(protocol);
CREATE INDEX idx_earn_positions_status ON earn_positions(status);
CREATE INDEX idx_earn_positions_deposited_at ON earn_positions(deposited_at);
```

### Hyperliquid Positions Table

```sql
CREATE TABLE hyperliquid_positions (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Position details
    symbol VARCHAR(20) NOT NULL,          -- "BTC-PERP", "ETH-PERP"
    side VARCHAR(10) NOT NULL,            -- Side enum: "long", "short"
    leverage NUMERIC(5, 2) NOT NULL,      -- 1.00 - 100.00
    size NUMERIC(30, 18) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    mark_price NUMERIC(20, 8),
    liquidation_price NUMERIC(20, 8),
    
    -- PnL
    unrealized_pnl NUMERIC(20, 8),
    realized_pnl NUMERIC(20, 8) DEFAULT 0,
    margin NUMERIC(20, 8) NOT NULL,
    
    -- Funding
    funding_rate NUMERIC(10, 6),          -- e.g., 0.0001 (0.01%)
    last_funding_payment NUMERIC(20, 8),
    
    -- Status
    status VARCHAR(20) DEFAULT 'open',    -- PositionStatus enum
    hyperliquid_order_id VARCHAR(100),
    
    -- Timestamps
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_hyperliquid_positions_user_id ON hyperliquid_positions(user_id);
CREATE INDEX idx_hyperliquid_positions_symbol ON hyperliquid_positions(symbol);
CREATE INDEX idx_hyperliquid_positions_status ON hyperliquid_positions(status);
CREATE INDEX idx_hyperliquid_positions_opened_at ON hyperliquid_positions(opened_at);
```

---

## Repository Interface

### PortfolioRepository

**Location**: `src/app/domain/ports/portfolio/portfolio_repository.py`

```python
class PortfolioRepository(Protocol):
    """Repository for portfolio snapshot persistence."""
    
    # CRUD Operations
    async def get_by_id(self, snapshot_id: PortfolioSnapshotId) -> PortfolioSnapshot | None
    async def get_latest_by_wallet(
        self, wallet_id: WalletId, chain: ChainType | None = None
    ) -> PortfolioSnapshot | None
    async def get_by_wallet(
        self, wallet_id: WalletId, *, chain: ChainType | None = None, 
        limit: int = 50, offset: int = 0
    ) -> list[PortfolioSnapshot]
    async def get_history(
        self, wallet_id: WalletId, start_date: datetime, end_date: datetime,
        *, chain: ChainType | None = None
    ) -> list[PortfolioSnapshot]
    
    async def save(self, snapshot: PortfolioSnapshot) -> PortfolioSnapshot
    async def save_holding(self, holding: TokenHolding) -> TokenHolding
    async def delete(self, snapshot_id: PortfolioSnapshotId) -> bool
    async def delete_old_snapshots(
        self, wallet_id: WalletId, *, keep_count: int = 100
    ) -> int
    
    # Analytics
    async def count_snapshots(self, wallet_id: WalletId | None = None) -> int
    async def get_portfolio_value_history(
        self, wallet_id: WalletId, start_date: datetime, end_date: datetime
    ) -> list[tuple[datetime, float]]
```

---

## Factory Methods

### PortfolioSnapshot Creation

```python
# Create portfolio snapshot
snapshot = PortfolioSnapshot.create(
    wallet_id=WalletId(123),
    chain=ChainType.ETHEREUM,
    native_balance=Decimal("1.5"),
    native_usd_value=Decimal("3000.00"),
)

# Add native token holding
native = TokenHolding.create_native(
    snapshot_id=snapshot.id_,
    chain=ChainType.ETHEREUM,
    amount=Decimal("1.5"),
    usd_value=Decimal("3000.00"),
    usd_price=Decimal("2000.00"),
)
snapshot.add_holding(native)

# Add ERC-20 token holding
usdc = TokenHolding.create_erc20(
    snapshot_id=snapshot.id_,
    token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    symbol="USDC",
    name="USD Coin",
    decimals=6,
    amount=Decimal("1000"),
    usd_value=Decimal("1000.00"),
    usd_price=Decimal("1.00"),
)
snapshot.add_holding(usdc)
```

### AavePosition Creation

```python
# Create from API response
position = AavePosition.from_dict({
    "user_address": "0x...",
    "chain": "ethereum",
    "total_collateral_usd": "10000",
    "total_debt_usd": "5000",
    "health_factor": "2.0",
    "supplies": [
        {"asset_address": "0x...", "symbol": "WETH", 
         "balance": "5", "balance_usd": "10000", "apy": "2.5"}
    ],
    "borrows": [
        {"asset_address": "0x...", "symbol": "USDC",
         "balance": "5000", "balance_usd": "5000", "apy": "4.5"}
    ]
})

# Check health
if position.is_at_risk:
    print(f"Warning: Health factor {position.health_factor}")
```

---

## Data Flow Examples

### 1. Portfolio Snapshot Capture

```
Transaction Confirmed      Worker                      Database
        │                    │                            │
        │   Event: TX_CONFIRMED                           │
        │ ─────────────────► │                            │
        │                    │                            │
        │                    │  Fetch balance from RPC    │
        │                    │ ◄───────────────────────── │
        │                    │                            │
        │                    │  Fetch token prices        │
        │                    │ ◄── CoinGecko API          │
        │                    │                            │
        │                    │  Create PortfolioSnapshot  │
        │                    │  + TokenHoldings           │
        │                    │                            │
        │                    │  save(snapshot)        ───►│
        │                    │                            │
```

### 2. DeFi Position Query

```
User                     Backend                    Aave API
  │                         │                          │
  │  GET /portfolio/defi    │                          │
  │ ───────────────────────►│                          │
  │                         │                          │
  │                         │  getUserAccountData()    │
  │                         │ ─────────────────────────►
  │                         │                          │
  │                         │◄── AavePosition          │
  │                         │                          │
  │◄── { positions: [...] } │                          │
```

### 3. Earn Position Tracking

```
User                     Backend                    Database
  │                         │                          │
  │  POST /earn/deposit     │                          │
  │  {protocol, asset, amt} │                          │
  │ ───────────────────────►│                          │
  │                         │                          │
  │                         │  Execute deposit on-chain │
  │                         │                          │
  │                         │  Create EarnPosition     │
  │                         │  status=ACTIVE            │
  │                         │  save(position)      ───►│
  │                         │                          │
  │◄── {position_id, tx_hash}│                          │
```

---

## Analytics Queries

### Portfolio Value History

```python
# Get 30-day value history
history = await portfolio_repo.get_portfolio_value_history(
    wallet_id=WalletId(123),
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
)
# [(2025-01-01, 10000.00), (2025-01-02, 10500.00), ...]
```

### Earn Position Statistics

```sql
-- Total deposited by protocol
SELECT protocol, SUM(amount_deposited) as total_deposited
FROM earn_positions
WHERE status = 'active'
GROUP BY protocol;

-- Total rewards earned
SELECT SUM(rewards_earned_usd) as total_rewards
FROM earn_positions
WHERE user_id = :user_id;
```

### Health Factor Monitoring

```python
# Check all positions at risk
for position in aave_positions:
    if position.is_at_risk:
        alert(f"Position {position.user_address} HF: {position.health_factor}")
    elif position.is_liquidatable:
        critical_alert(f"LIQUIDATION RISK: {position.user_address}")
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Entities** | `domain/entities/portfolio_snapshot.py` | Snapshot + TokenHolding |
| | `domain/entities/chain_address.py` | Chain-specific balance |
| | `domain/entities/earn_position.py` | Yield farming position |
| | `domain/entities/hyperliquid_position.py` | Perp futures position |
| | `domain/entities/lending/aave_position.py` | Aave V3 position |
| | `domain/entities/lending/morpho_position.py` | Morpho vault position |
| | `domain/entities/perpetual/position.py` | Generic perp position |
| **Enums** | `domain/enums/earn_status.py` | Earn position status |
| | `domain/enums/position_status.py` | Trading position status |
| | `domain/enums/side.py` | Long/Short side |
| **Ports** | `domain/ports/portfolio/portfolio_repository.py` | Repository interface |
| **Mappings** | `infrastructure/persistence_sqla/mappings/portfolio_snapshot.py` | DB mapping |
| | `infrastructure/persistence_sqla/mappings/defi_operations.py` | Earn/Hyperliquid |

---

## Best Practices

### Snapshot Frequency

```python
# Capture snapshots on:
# 1. Transaction confirmation
# 2. User request (with rate limiting)
# 3. Daily scheduled job

# Cleanup old snapshots
deleted = await portfolio_repo.delete_old_snapshots(
    wallet_id=wallet_id,
    keep_count=100,  # Keep last 100 snapshots
)
```

### Price Precision

```python
# Use Decimal for all monetary values
from decimal import Decimal

# Token amounts: 18 decimal precision
amount = Decimal("1.123456789012345678")

# USD values: 8 decimal precision
usd_value = Decimal("1234.56789012")
```

### Health Factor Thresholds

```python
# Health factor monitoring thresholds
HEALTHY_THRESHOLD = Decimal("2.0")      # > 2.0 is safe
WARNING_THRESHOLD = Decimal("1.5")      # 1.5 - 2.0 needs attention
DANGER_THRESHOLD = Decimal("1.2")       # 1.2 - 1.5 is risky
CRITICAL_THRESHOLD = Decimal("1.0")     # < 1.0 can be liquidated
```

---

**Last Updated**: January 2, 2026

# Earn Provider Integration - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de Earn Providers proporciona:

1. **Multi-Protocol Support**: Morpho, Aave, Compound integrations
2. **Yield Optimization**: AI-powered yield discovery and comparison
3. **MCP Servers**: AI agent tools for lending operations
4. **Position Tracking**: User position management and earnings
5. **Health Factor Monitoring**: Liquidation risk assessment
6. **Multi-Chain**: Ethereum, Base, Polygon, Arbitrum support

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           EARN PROVIDER ARCHITECTURE                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   User (Chat)   │
                                    │  "deposit USDC  │
                                    │   for best APY" │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │    DeFi Yield Agent      │
                              │  (Yield Optimization)    │
                              └──────────┬───────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌───────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ Morpho MCP    │              │   Aave MCP      │              │  Compound       │
│ Server (8088) │              │ Server (8085)   │              │  Adapter        │
└───────┬───────┘              └────────┬────────┘              └────────┬────────┘
        │                               │                                │
        ▼                               ▼                                ▼
┌───────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ MorphoGateway │              │  AaveGateway    │              │CompoundGateway  │
│   (Port)      │              │    (Port)       │              │   (Port)        │
└───────┬───────┘              └────────┬────────┘              └────────┬────────┘
        │                               │                                │
        ▼                               ▼                                ▼
┌───────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ MorphoClient  │              │   AaveClient    │              │ CompoundClient  │
│ (GraphQL API) │              │   (RPC/Graph)   │              │   (RPC/API)     │
└───────────────┘              └─────────────────┘              └─────────────────┘
        │                               │                                │
        └───────────────────────────────┼────────────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────────┐
                              │   EarnPosition Entity    │
                              │   (Database Persistence) │
                              └──────────────────────────┘
```

---

## Protocol Providers

### 1. Morpho Protocol

**Purpose**: MetaMorpho vaults and Morpho Blue markets for optimized yield.

**Location**: `src/app/infrastructure/adapters/external/morpho_client.py`

#### Morpho Client

```python
class MorphoClient:
    """
    Morpho Protocol API client using official GraphQL endpoint.
    
    Features:
    - Multi-chain support (Ethereum + Base)
    - MetaMorpho vault discovery (V1 and V2)
    - Morpho Blue market data
    - User position tracking
    - Real-time APY data
    """
    
    MORPHO_API_URL = "https://blue-api.morpho.org/graphql"
    
    CHAIN_IDS = {
        "ethereum": 1,
        "base": 8453,
    }
```

#### Morpho Gateway Port

**Location**: `src/app/domain/ports/morpho_gateway.py`

```python
class MorphoGateway(Protocol):
    """Port interface for Morpho Protocol operations."""
    
    async def get_vaults(
        self,
        asset: str | None = None,
        chain: str = "ethereum",
    ) -> list[MorphoVault]: ...
    
    async def get_vault_details(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> MorphoVault: ...
    
    async def get_vault_apy(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> VaultAPY: ...
    
    async def get_markets(
        self,
        chain: str = "ethereum",
    ) -> list[MorphoMarket]: ...
    
    async def get_user_positions(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> list[MorphoPosition]: ...
```

#### Morpho MCP Server

**Location**: `src/app/infrastructure/mcp/servers/morpho_mcp.py`

| Tool | Description |
|------|-------------|
| `morpho_get_vaults` | Get vaults with APY/risk data |
| `morpho_get_vault_details` | Detailed vault info |
| `morpho_get_vault_apy` | APY breakdown |
| `morpho_get_markets` | Morpho Blue markets |
| `morpho_get_user_positions` | User positions |
| `morpho_compare_yields` | Cross-protocol comparison |

```bash
# Run Morpho MCP Server
make mcp.morpho  # Port 8088
```

---

### 2. Aave V3 Protocol

**Purpose**: Lending/borrowing with supply APY and health factor monitoring.

**Location**: `src/app/infrastructure/adapters/external/aave_client.py`

#### Aave Client

```python
class AaveClient:
    """Low-level client for Aave V3 protocol."""
    
    # Chain-specific Aave V3 Pool addresses
    AAVE_V3_POOLS = {
        "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
    }
```

#### Aave Gateway Port

**Location**: `src/app/domain/ports/aave_gateway.py`

```python
class AaveGateway(Protocol):
    """Port interface for Aave V3 Protocol operations."""
    
    async def get_markets(
        self,
        asset: str | None = None,
        chain: str = "ethereum",
    ) -> list[AaveMarket]: ...
    
    async def get_user_position(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> AavePosition: ...
    
    async def get_health_factor(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> HealthFactor: ...
    
    async def get_supply_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal: ...
    
    async def get_borrow_apy(
        self,
        asset: str,
        chain: str = "ethereum",
        rate_type: str = "variable",
    ) -> Decimal: ...
```

#### Aave MCP Server

**Location**: `src/app/infrastructure/mcp/servers/aave_mcp.py`

| Tool | Description |
|------|-------------|
| `get_market_data` | Lending/borrowing rates |
| `get_user_positions` | User supply/borrow positions |
| `calculate_health_factor` | Health factor and risk |
| `get_available_to_borrow` | Max borrowing capacity |
| `supply_asset` | Supply assets to earn yield |
| `borrow_asset` | Borrow against collateral |
| `repay_loan` | Repay borrowed assets |
| `withdraw_supply` | Withdraw supplied assets |
| `get_liquidation_risk` | Liquidation risk analysis |

```bash
# Run Aave MCP Server
make mcp.aave  # Port 8085
```

---

### 3. Compound Protocol

**Purpose**: Additional lending option for yield diversification.

**Location**: `src/app/infrastructure/adapters/external/compound_client.py`

---

## Domain Entities

### EarnPosition Entity

**Location**: `src/app/domain/entities/earn_position.py`

Represents a user's yield farming or staking position (persisted).

```python
@dataclass(eq=False, kw_only=True)
class EarnPosition(Entity[EarnPositionId]):
    user_id: UserId
    wallet_id: WalletId
    chain: ChainType
    protocol: str                    # "morpho", "aave", "compound"
    asset: str                       # "USDC", "ETH"
    amount_deposited: Decimal
    current_value: Optional[Decimal]
    apy: Optional[Decimal]           # APY at deposit time
    current_apy: Optional[Decimal]   # Live APY
    rewards_earned: Decimal
    rewards_earned_usd: Decimal
    status: EarnStatus               # ACTIVE, WITHDRAWN, EMERGENCY_EXIT
    transaction_hash: Optional[str]
    deposit_tx_hash: Optional[str]
    withdraw_tx_hash: Optional[str]
    deposited_at: CreatedAt
    withdrawn_at: Optional[datetime]
    created_at: CreatedAt
```

### MorphoPosition Entity

**Location**: `src/app/domain/entities/lending/morpho_position.py`

External API entity (not persisted, fetched from Morpho API).

```python
@dataclass
class MorphoPosition:
    user_address: str
    vault_address: str
    vault_name: str
    asset_symbol: str
    shares: Decimal = Decimal("0")
    assets: Decimal = Decimal("0")       # Current value
    deposited_assets: Decimal = Decimal("0")  # Original deposit
    apy: Decimal = Decimal("0")
    deposited_at: datetime | None = None
    
    @property
    def earnings(self) -> Decimal:
        """Calculate earnings (current - deposited)."""
        return self.assets - self.deposited_assets
    
    @property
    def earnings_pct(self) -> Decimal:
        """Calculate earnings as percentage."""
        if self.deposited_assets == 0:
            return Decimal("0")
        return self.earnings / self.deposited_assets * 100
```

### AavePosition Entity

**Location**: `src/app/domain/entities/lending/aave_position.py`

External API entity with supply/borrow tracking and health factor.

---

## Enumerations

### EarnStatus

**Location**: `src/app/domain/enums/earn_status.py`

```python
class EarnStatus(str, Enum):
    ACTIVE = "active"              # Position is earning yield
    WITHDRAWN = "withdrawn"        # Fully withdrawn
    EMERGENCY_EXIT = "emergency_exit"  # Emergency withdrawal
```

---

## Value Objects

### HealthFactor

**Location**: `src/app/domain/value_objects/lending/health_factor.py`

```python
@dataclass(frozen=True)
class HealthFactor:
    value: Decimal
    risk_level: str    # "low", "moderate", "high", "critical"
    liquidation_threshold: Decimal
    
    @property
    def is_safe(self) -> bool:
        return self.value >= Decimal("1.5")
    
    @property
    def is_liquidatable(self) -> bool:
        return self.value < Decimal("1.0")
```

### VaultAPY

**Location**: `src/app/domain/value_objects/lending/vault_apy.py`

```python
@dataclass(frozen=True)
class VaultAPY:
    vault_address: str
    base_apy: Decimal      # Base yield
    supply_apy: Decimal    # Supply rate
    reward_apy: Decimal    # Token rewards
    total_apy: Decimal     # Combined APY
    fee_percentage: Decimal
    net_apy: Decimal       # After fees
```

---

## AI Agents

### DeFi Yield Agent

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/defi_yield_agent_openai.py`

```python
class DefiYieldAgentOpenAI:
    """
    DeFi Yield Agent - Yield farming & APY optimization.
    
    Capabilities:
    - Find best yield opportunities
    - APY comparison (Aave, Compound, Curve, Convex)
    - Liquidity pool analysis
    - Impermanent loss calculation
    - Yield farming strategies
    - Auto-compounding recommendations
    
    Model: gpt-4o (complex DeFi reasoning)
    Temperature: 0.3 (balanced)
    """
```

### Lending Borrowing Agent

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/advanced/lending_borrowing_agent_aave.py`

Specialized agent for Aave lending/borrowing operations.

### Lending Agent (Agno)

**Location**: `src/app/infrastructure/agno/lending_agent.py`

MCP-based lending agent using Aave and Morpho tools.

---

## Database Schema

### earn_positions Table

```sql
CREATE TABLE earn_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    wallet_id INTEGER NOT NULL REFERENCES wallets(id),
    chain VARCHAR(50) NOT NULL,
    protocol VARCHAR(100) NOT NULL,           -- "morpho", "aave", "compound"
    asset VARCHAR(50) NOT NULL,               -- "USDC", "ETH"
    amount_deposited NUMERIC(36, 18) NOT NULL,
    current_value NUMERIC(36, 18),
    apy NUMERIC(10, 6),                       -- APY at deposit time
    current_apy NUMERIC(10, 6),               -- Live APY
    rewards_earned NUMERIC(36, 18) DEFAULT 0,
    rewards_earned_usd NUMERIC(36, 18) DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    transaction_hash VARCHAR(66),
    deposit_tx_hash VARCHAR(66),
    withdraw_tx_hash VARCHAR(66),
    deposited_at TIMESTAMP WITH TIME ZONE NOT NULL,
    withdrawn_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_earn_user_id (user_id),
    INDEX idx_earn_wallet_id (wallet_id),
    INDEX idx_earn_protocol (protocol),
    INDEX idx_earn_status (status)
);
```

---

## API Integration

### ExecuteActionCommand Deposit/Withdraw

**Location**: `src/app/application/chat/commands/execute_action.py`

```python
async def _handle_deposit(
    self,
    action_id: UUID,
    wallet_address: str,
    token: str,
    amount: str,
    protocol: str,          # "morpho", "aave", "compound"
    vault_address: Optional[str],
    chain: str,
    confirmed: bool,
    language: str,
) -> ActionResult:
    """Handle deposit action."""
    
async def _handle_withdraw(
    self,
    action_id: UUID,
    wallet_address: str,
    token: str,
    amount: str,
    protocol: str,
    vault_address: Optional[str],
    chain: str,
    confirmed: bool,
    language: str,
) -> ActionResult:
    """Handle withdrawal action."""
```

### Request Schema

```json
{
  "action_type": "deposit",
  "from_token": "USDC",
  "amount": "1000",
  "protocol": "morpho",
  "vault_address": "0x...",
  "chain": "base",
  "confirmed": false
}
```

---

## Multi-Chain Support

### Supported Chains

| Chain | ID | Morpho | Aave | Compound |
|-------|------|--------|------|----------|
| Ethereum | 1 | ✅ | ✅ | ✅ |
| Base | 8453 | ✅ | ✅ | ❌ |
| Polygon | 137 | ❌ | ✅ | ❌ |
| Arbitrum | 42161 | ❌ | ✅ | ❌ |
| Optimism | 10 | ❌ | ✅ | ❌ |
| Avalanche | 43114 | ❌ | ✅ | ❌ |

---

## Health Factor Monitoring

### Risk Levels

| Health Factor | Risk Level | Color | Action |
|---------------|------------|-------|--------|
| ≥ 2.0 | Low | 🟢 Green | Safe |
| 1.5 - 2.0 | Moderate | 🟡 Yellow | Monitor |
| 1.2 - 1.5 | High | 🟠 Orange | Add collateral |
| < 1.2 | Critical | 🔴 Red | Urgent action |
| < 1.0 | Liquidatable | ⚠️ | Position at risk |

### Health Factor Calculation

```python
# Health Factor = (Total Collateral * Liquidation Threshold) / Total Debt
health_factor = (collateral_usd * 0.80) / debt_usd

# Example:
# Collateral: $21,000
# Debt: $5,000
# HF = (21000 * 0.80) / 5000 = 3.36 (Safe)
```

---

## Yield Comparison

### DefiLlama Integration

Uses DefiLlama for cross-protocol APY comparison.

```python
# Compare yields across protocols
comparison = await call_tool("morpho_compare_yields", {
    "asset": "USDC",
    "protocols": ["morpho", "aave", "compound"],
    "chain": "ethereum",
})
```

### Comparison Response

```json
{
  "asset": "USDC",
  "comparisons": [
    {
      "protocol": "morpho",
      "vault_name": "Steakhouse USDC",
      "apy": "8.50%",
      "net_apy": "7.65%",
      "risk_tier": "medium",
      "tvl": "$50,000,000"
    },
    {
      "protocol": "aave",
      "asset": "USDC",
      "apy": "2.50%",
      "risk_tier": "low"
    }
  ],
  "best_option": {...}
}
```

---

## Configuration

### Feature Flags

```python
# src/app/setup/config/mcp.py
class MCPServersSettings:
    morpho_enabled: bool = True
    aave_enabled: bool = True
```

### MCP Server Ports

| Server | Port | Purpose |
|--------|------|---------|
| Morpho | 8088 | MetaMorpho vaults, Morpho Blue |
| Aave | 8085 | Aave V3 lending/borrowing |

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Morpho Client** | `adapters/external/morpho_client.py` | GraphQL API client |
| **Morpho Gateway** | `domain/ports/morpho_gateway.py` | Port interface |
| **Morpho Adapter** | `adapters/external/morpho_adapter.py` | Gateway implementation |
| **Morpho MCP** | `mcp/servers/morpho_mcp.py` | AI agent tools |
| **Aave Client** | `adapters/external/aave_client.py` | RPC/API client |
| **Aave Gateway** | `domain/ports/aave_gateway.py` | Port interface |
| **Aave Adapter** | `adapters/external/aave_adapter.py` | Gateway implementation |
| **Aave MCP** | `mcp/servers/aave_mcp.py` | AI agent tools |
| **EarnPosition** | `domain/entities/earn_position.py` | Persisted position |
| **MorphoPosition** | `domain/entities/lending/morpho_position.py` | External position |
| **HealthFactor** | `domain/value_objects/lending/health_factor.py` | Risk value object |
| **DeFi Yield Agent** | `agents/defi_yield_agent_openai.py` | Yield optimization |
| **Execute Action** | `chat/commands/execute_action.py` | Deposit/withdraw |
| **DB Mapping** | `persistence_sqla/mappings/defi_operations.py` | SQLAlchemy |

---

## Usage Examples

### Get Best Vaults

```python
# Via MCP Tool
vaults = await call_tool("morpho_get_vaults", {
    "asset": "USDC",
    "chain": "base",
    "sort_by": "apy",
    "limit": 5,
})

# Via Client
client = MorphoClient()
vaults = await client.get_base_usdc_vaults(whitelisted=True)
```

### Check User Position

```python
# Morpho positions
positions = await morpho_gateway.get_user_positions(
    address="0x...",
    chain="base",
)

for p in positions:
    print(f"{p.vault_name}: ${p.assets} (earned: ${p.earnings})")

# Aave position with health factor
position = await aave_gateway.get_user_position(
    address="0x...",
    chain="ethereum",
)
print(f"Health Factor: {position.health_factor}")
```

### Execute Deposit via Chat

```python
# Step 1: Simulate
result = await execute_action.execute(
    user_id=123,
    conversation_id=conv_id,
    action_type="deposit",
    from_token="USDC",
    amount="1000",
    protocol="morpho",
    vault_address="0x...",
    chain="base",
    confirmed=False,
)

# Step 2: Confirm
if user_confirms():
    result = await execute_action.execute(
        ...,
        confirmed=True,
    )
```

---

## Best Practices

### 1. Always Check Health Factor Before Borrow

```python
health = await aave_gateway.get_health_factor(address, chain)
if health.value < Decimal("1.5"):
    raise RiskTooHighError("Health factor too low for borrow")
```

### 2. Compare APYs Before Deposit

```python
comparison = await morpho_mcp.compare_yields(asset="USDC")
best = max(comparison, key=lambda x: x["apy"])
```

### 3. Track Position Earnings

```python
position = await morpho_gateway.get_user_positions(address)
for p in positions:
    if p.earnings > Decimal("100"):
        notify_user(f"Earned ${p.earnings} on {p.vault_name}")
```

### 4. Monitor Liquidation Risk

```python
risk = await aave_mcp.get_liquidation_risk(chain_id, address)
if risk["risk_level"] in ["high", "critical"]:
    alert_user(risk["recommendations"])
```

---

## Security Considerations

### Transaction Limits

- Deposit: $100,000 max
- Uses TransactionApprovalService for high-value transactions

### Health Factor Alerts

- Automatic alerts when HF < 1.5
- Critical alerts when HF < 1.2

### Vault Verification

- Only use whitelisted/curated vaults
- Verify curator addresses

---

**Last Updated**: January 2, 2026

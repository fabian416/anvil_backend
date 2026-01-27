# Lending Workflow Architecture

**Version**: 1.0
**Date**: 2026-01-27
**Status**: Specification
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **Lending Workflow** feature, supporting **Aave V3** and **Morpho Protocol** operations through MCP server integration (ports 8085 and 8088).

### Key Features

- **Supply/Deposit Operations**: Automatic wallet signature flow
- **Borrow Operations**: Health factor monitoring and risk assessment
- **Leverage Loop**: Semi-automatic with sequential signatures
- **Health Check Monitoring**: Real-time liquidation risk tracking
- **Multi-Agent Flows**: Market Scanner → Risk Agent → Executor Agent
- **User Context Awareness**: Different flows for guest vs authenticated users
- **Balance Validation**: Check wallet balance before transaction execution

### Supported Protocols

1. **Morpho Protocol** (MCP Port 8088)
   - MetaMorpho vault operations (supply only)
   - Yield optimization
   - Position tracking
   - APY comparison

2. **Aave V3** (MCP Port 8085)
   - Supply/borrow operations
   - Health factor monitoring
   - Liquidation risk assessment
   - Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche)

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LENDING ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│  Lending      │    │   Shortcuts       │    │   Guest Chat    │
│  Endpoints    │    │   Endpoint        │    │   Endpoint      │
└───────┬───────┘    └──────────┬────────┘    └────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Application Layer   │
                    │  (CQRS + Interactors)│
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Commands     │    │    Queries       │    │   Handlers      │
│  (Writes)     │    │    (Reads)       │    │  (Orchestrators)│
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │    Domain Layer      │
                    │  (Business Logic)    │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Entities     │    │  Value Objects   │    │   Services      │
│  (Identity)   │    │  (Immutable)     │    │ (Business Logic)│
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Ports (Interfaces)  │
                    └───────────┬──────────┘
                                │
                    ┌───────────▼──────────┐
                    │ Infrastructure Layer │
                    │    (Adapters)        │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Aave MCP     │    │   Morpho MCP     │    │  Balance Checker│
│  Adapter      │    │   Adapter        │    │   (Portfolio)   │
│  (Port 8085)  │    │   (Port 8088)    │    │                 │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Entities

#### 1. `LendingPosition` Entity
**Location**: `src/app/domain/entities/lending/lending_position.py`

```python
@dataclass
class LendingPosition:
    """
    Aggregate root for lending positions.

    Represents user's complete lending state across all protocols.
    """

    position_id: UUID
    user_id: UUID
    protocol: Protocol  # AAVE | MORPHO
    chain: str

    # Supply positions
    supplies: list[SupplyPosition]

    # Borrow positions (Aave only)
    borrows: list[BorrowPosition]

    # Health metrics
    health_factor: HealthFactor
    total_collateral_usd: Decimal
    total_debt_usd: Decimal

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Business invariants
    def can_borrow(self, amount: Decimal) -> bool:
        """Check if user can borrow without liquidation risk."""

    def requires_repayment(self) -> bool:
        """Check if position requires immediate action."""

    def calculate_max_borrow(self, target_hf: Decimal = Decimal("1.5")) -> Decimal:
        """Calculate maximum safe borrow amount."""
```

#### 2. `SupplyPosition` Entity
**Location**: `src/app/domain/entities/lending/supply_position.py`

```python
@dataclass
class SupplyPosition:
    """Supply position for a single asset."""

    asset: str
    amount: Decimal
    amount_usd: Decimal
    apy: Decimal
    is_collateral: bool
    protocol: Protocol
    vault_address: str | None  # For Morpho
```

#### 3. `BorrowPosition` Entity
**Location**: `src/app/domain/entities/lending/borrow_position.py`

```python
@dataclass
class BorrowPosition:
    """Borrow position for a single asset (Aave only)."""

    asset: str
    amount: Decimal
    amount_usd: Decimal
    apy: Decimal
    rate_mode: str  # "variable" | "stable"
    debt_token_address: str
```

### Value Objects

#### 1. `HealthFactor` Value Object
**Location**: `src/app/domain/value_objects/lending/health_factor.py`

```python
@dataclass(frozen=True)
class HealthFactor:
    """
    Health factor value object with risk analysis.

    Formula: (Collateral × Liquidation Threshold) / Total Debt

    Risk Levels:
    - >= 2.0: Low risk (safe)
    - >= 1.5: Moderate risk
    - >= 1.2: High risk (monitor closely)
    - < 1.2: Critical risk (urgent action needed)
    - < 1.0: Liquidatable
    """

    value: Decimal

    def __post_init__(self):
        if self.value < Decimal("0"):
            raise ValueError("Health factor cannot be negative")

    @property
    def risk_level(self) -> RiskLevel:
        """Get risk level classification."""

    @property
    def is_healthy(self) -> bool:
        """Check if position is healthy (HF > 1.0)."""

    @property
    def is_liquidatable(self) -> bool:
        """Check if position can be liquidated (HF < 1.0)."""

    @property
    def buffer_percentage(self) -> Decimal:
        """Calculate price drop % before liquidation."""
```

#### 2. `Protocol` Enum
**Location**: `src/app/domain/enums/protocol.py`

```python
class Protocol(str, Enum):
    """Supported lending protocols."""

    AAVE = "aave"
    MORPHO = "morpho"
```

#### 3. `LendingAction` Enum
**Location**: `src/app/domain/enums/lending_action.py`

```python
class LendingAction(str, Enum):
    """Lending operation types."""

    SUPPLY = "supply"
    WITHDRAW = "withdraw"
    BORROW = "borrow"
    REPAY = "repay"
    LEVERAGE_LOOP = "leverage_loop"
    HEALTH_CHECK = "health_check"
```

### Domain Services

#### 1. `LendingService`
**Location**: `src/app/domain/services/lending_service.py`

```python
class LendingService:
    """
    Domain service for lending business logic.

    Coordinates between Aave and Morpho protocols.
    """

    def calculate_leverage_loop(
        self,
        initial_collateral: Decimal,
        target_leverage: Decimal,
        collateral_ltv: Decimal,
    ) -> LeverageLoopPlan:
        """
        Calculate leverage loop iterations.

        Returns plan with steps and final multiplier.
        """

    def validate_borrow_safety(
        self,
        position: LendingPosition,
        borrow_amount: Decimal,
        min_health_factor: Decimal = Decimal("1.5"),
    ) -> BorrowValidation:
        """Validate if borrow is safe."""

    def recommend_repay_amount(
        self,
        position: LendingPosition,
        target_health_factor: Decimal = Decimal("2.0"),
    ) -> Decimal:
        """Calculate optimal repay amount to reach target HF."""
```

### Domain Ports (Interfaces)

#### 1. `LendingGateway`
**Location**: `src/app/domain/ports/lending_gateway.py`

```python
class LendingGateway(Protocol):
    """
    Port for lending operations.

    Abstracts protocol-specific implementations.
    """

    async def get_position(
        self,
        user_address: str,
        protocol: Protocol,
        chain: str,
    ) -> LendingPosition:
        """Get user's lending position."""

    async def supply(
        self,
        user_address: str,
        asset: str,
        amount: Decimal,
        protocol: Protocol,
        chain: str,
    ) -> TransactionResult:
        """Supply assets to lending protocol."""

    async def borrow(
        self,
        user_address: str,
        asset: str,
        amount: Decimal,
        protocol: Protocol,
        chain: str,
        rate_mode: str = "variable",
    ) -> TransactionResult:
        """Borrow assets from lending protocol."""

    async def calculate_health_factor(
        self,
        collateral_usd: Decimal,
        debt_usd: Decimal,
        liquidation_threshold: Decimal,
    ) -> HealthFactor:
        """Calculate health factor from position data."""
```

#### 2. `BalanceGateway`
**Location**: `src/app/domain/ports/balance_gateway.py`

```python
class BalanceGateway(Protocol):
    """Port for checking wallet balances."""

    async def get_token_balance(
        self,
        user_address: str,
        token_address: str,
        chain: str,
    ) -> Decimal:
        """Get token balance for user."""

    async def get_native_balance(
        self,
        user_address: str,
        chain: str,
    ) -> Decimal:
        """Get native token (ETH) balance."""
```

---

## Application Layer

### Commands (CQRS Write Operations)

#### 1. `SupplyCommand`
**Location**: `src/app/application/lending/commands/supply_command.py`

```python
@dataclass
class SupplyCommand:
    """Command to supply assets to lending protocol."""

    user_id: UUID
    protocol: Protocol
    asset: str
    amount: Decimal
    chain: str
    use_as_collateral: bool = True

    # Validation
    def validate(self) -> None:
        if self.amount <= 0:
            raise InvalidAmountError("Amount must be positive")
```

#### 2. `BorrowCommand`
**Location**: `src/app/application/lending/commands/borrow_command.py`

```python
@dataclass
class BorrowCommand:
    """Command to borrow assets from lending protocol."""

    user_id: UUID
    protocol: Protocol
    asset: str
    amount: Decimal
    chain: str
    rate_mode: str = "variable"
    min_health_factor: Decimal = Decimal("1.5")
```

#### 3. `LeverageLoopCommand`
**Location**: `src/app/application/lending/commands/leverage_loop_command.py`

```python
@dataclass
class LeverageLoopCommand:
    """Command to execute leverage loop strategy."""

    user_id: UUID
    protocol: Protocol
    collateral_asset: str
    initial_amount: Decimal
    target_leverage: Decimal
    chain: str
    max_iterations: int = 5
```

### Queries (CQRS Read Operations)

#### 1. `GetUserPositionQuery`
**Location**: `src/app/application/lending/queries/get_user_position_query.py`

```python
@dataclass
class GetUserPositionQuery:
    """Query for user's lending position."""

    user_id: UUID
    protocol: Protocol
    chain: str
```

#### 2. `CalculateHealthFactorQuery`
**Location**: `src/app/application/lending/queries/calculate_health_factor_query.py`

```python
@dataclass
class CalculateHealthFactorQuery:
    """Query to calculate health factor."""

    user_id: UUID
    protocol: Protocol
    chain: str
    simulated_borrow: Decimal | None = None  # For simulation
```

### Interactors (Use Case Orchestration)

#### 1. `SupplyInteractor`
**Location**: `src/app/application/lending/interactors/supply_interactor.py`

```python
class SupplyInteractor:
    """
    Orchestrates supply operation.

    Flow:
    1. Validate user balance
    2. Check transaction requirements
    3. Execute supply via MCP adapter
    4. Update position tracking
    5. Return transaction result
    """

    def __init__(
        self,
        lending_gateway: LendingGateway,
        balance_gateway: BalanceGateway,
        user_context: UserContextService,
    ):
        self._lending = lending_gateway
        self._balance = balance_gateway
        self._user_context = user_context

    async def execute(self, command: SupplyCommand) -> SupplyResult:
        """Execute supply operation with validation."""

        # 1. Get user wallet address
        user = await self._user_context.get_user(command.user_id)

        # 2. Validate balance
        balance = await self._balance.get_token_balance(
            user.wallet_address,
            command.asset,
            command.chain,
        )

        if balance < command.amount:
            raise InsufficientBalanceError(
                f"Balance: {balance}, Required: {command.amount}"
            )

        # 3. Execute supply
        result = await self._lending.supply(
            user_address=user.wallet_address,
            asset=command.asset,
            amount=command.amount,
            protocol=command.protocol,
            chain=command.chain,
        )

        return SupplyResult(
            transaction_hash=result.tx_hash,
            amount=command.amount,
            asset=command.asset,
            protocol=command.protocol,
        )
```

#### 2. `BorrowInteractor`
**Location**: `src/app/application/lending/interactors/borrow_interactor.py`

```python
class BorrowInteractor:
    """
    Orchestrates borrow operation with health factor monitoring.

    Flow:
    1. Get current position
    2. Calculate health factor impact
    3. Validate minimum health factor
    4. Execute borrow
    5. Track position changes
    """

    async def execute(self, command: BorrowCommand) -> BorrowResult:
        """Execute borrow with safety checks."""

        # 1. Get current position
        position = await self._lending.get_position(
            user_address=user.wallet_address,
            protocol=command.protocol,
            chain=command.chain,
        )

        # 2. Validate health factor impact
        validation = await self._lending_service.validate_borrow_safety(
            position=position,
            borrow_amount=command.amount,
            min_health_factor=command.min_health_factor,
        )

        if not validation.is_safe:
            raise UnsafeBorrowError(
                f"Borrow would result in HF={validation.projected_health_factor}, "
                f"minimum required={command.min_health_factor}"
            )

        # 3. Execute borrow
        result = await self._lending.borrow(
            user_address=user.wallet_address,
            asset=command.asset,
            amount=command.amount,
            protocol=command.protocol,
            chain=command.chain,
            rate_mode=command.rate_mode,
        )

        return BorrowResult(
            transaction_hash=result.tx_hash,
            amount=command.amount,
            asset=command.asset,
            new_health_factor=validation.projected_health_factor,
        )
```

---

## Infrastructure Layer

### MCP Adapters

#### 1. `AaveMCPAdapter`
**Location**: `src/app/infrastructure/adapters/lending/aave_mcp_adapter.py`

```python
class AaveMCPAdapter(LendingGateway):
    """
    Adapter for Aave MCP server (port 8085).

    Implements LendingGateway port for Aave operations.
    """

    def __init__(
        self,
        mcp_client: MCPClient,
        cache: ExternalAPICache,
    ):
        self._client = mcp_client
        self._cache = cache
        self._base_url = "http://localhost:8085"

    async def get_position(
        self,
        user_address: str,
        protocol: Protocol,
        chain: str,
    ) -> LendingPosition:
        """Get user position from Aave MCP."""

        # Call Aave MCP get_user_positions tool
        response = await self._client.call_tool(
            server_url=self._base_url,
            tool_name="get_user_positions",
            arguments={
                "chain_id": _chain_to_id(chain),
                "user_address": user_address,
            },
        )

        return self._transform_position(response, Protocol.AAVE)

    async def supply(
        self,
        user_address: str,
        asset: str,
        amount: Decimal,
        protocol: Protocol,
        chain: str,
    ) -> TransactionResult:
        """Execute supply via Aave MCP."""

        response = await self._client.call_tool(
            server_url=self._base_url,
            tool_name="supply_asset",
            arguments={
                "user_id": str(user_id),
                "chain_id": _chain_to_id(chain),
                "asset": asset,
                "amount": str(amount),
                "from_address": user_address,
                "use_as_collateral": True,
            },
        )

        return TransactionResult(
            tx_hash=response.get("transaction_hash"),
            status="pending",
        )
```

#### 2. `MorphoMCPAdapter`
**Location**: `src/app/infrastructure/adapters/lending/morpho_mcp_adapter.py`

```python
class MorphoMCPAdapter(LendingGateway):
    """
    Adapter for Morpho MCP server (port 8088).

    Implements LendingGateway port for Morpho operations.
    """

    def __init__(
        self,
        mcp_client: MCPClient,
        morpho_gateway: MorphoGateway,  # Existing adapter
        cache: ExternalAPICache,
    ):
        self._client = mcp_client
        self._morpho = morpho_gateway
        self._cache = cache
        self._base_url = "http://localhost:8088"

    async def get_position(
        self,
        user_address: str,
        protocol: Protocol,
        chain: str,
    ) -> LendingPosition:
        """Get user position from Morpho."""

        # Use existing MorphoGateway
        positions = await self._morpho.get_user_positions(
            address=user_address,
            chain=chain,
        )

        return self._transform_positions(positions, Protocol.MORPHO)
```

#### 3. `BalanceChecker`
**Location**: `src/app/infrastructure/adapters/portfolio/balance_checker.py`

```python
class BalanceChecker(BalanceGateway):
    """
    Adapter for checking wallet balances.

    Uses Portfolio MCP server or Web3 RPC calls.
    """

    def __init__(
        self,
        portfolio_mcp: PortfolioMCPServer,
        web3_client: Web3Client,
    ):
        self._portfolio = portfolio_mcp
        self._web3 = web3_client

    async def get_token_balance(
        self,
        user_address: str,
        token_address: str,
        chain: str,
    ) -> Decimal:
        """Get ERC20 token balance."""

        try:
            # Try Portfolio MCP first
            response = await self._portfolio.call_tool(
                "get_user_balance",
                {
                    "user_address": user_address,
                    "chain": chain,
                },
            )

            # Find token in response
            for token in response.get("balances", []):
                if token["address"].lower() == token_address.lower():
                    return Decimal(token["balance"])

            return Decimal("0")

        except Exception:
            # Fallback to direct RPC call
            return await self._web3.get_erc20_balance(
                user_address,
                token_address,
                chain,
            )
```

---

## Presentation Layer

### HTTP Endpoints

#### 1. Lending Endpoints
**Location**: `src/app/presentation/http/controllers/lending/lending_router.py`

```python
router = APIRouter(prefix="/api/v1/lending", tags=["lending"])

@router.post("/supply")
@inject
async def supply_assets(
    request: SupplyRequest,
    interactor: SupplyInteractor = FromDishka(),
    current_user: CurrentUserService = FromDishka(),
) -> SupplyResponse:
    """
    Supply assets to lending protocol.

    Requires authentication. Validates balance before execution.
    """

@router.post("/borrow")
@inject
async def borrow_assets(
    request: BorrowRequest,
    interactor: BorrowInteractor = FromDishka(),
    current_user: CurrentUserService = FromDishka(),
) -> BorrowResponse:
    """
    Borrow assets from lending protocol.

    Validates health factor. Requires authentication.
    """

@router.get("/position")
@inject
async def get_position(
    protocol: Protocol,
    chain: str,
    interactor: GetPositionInteractor = FromDishka(),
    current_user: CurrentUserService = FromDishka(),
) -> PositionResponse:
    """Get user's lending position."""

@router.post("/leverage-loop")
@inject
async def execute_leverage_loop(
    request: LeverageLoopRequest,
    interactor: LeverageLoopInteractor = FromDishka(),
    current_user: CurrentUserService = FromDishka(),
) -> LeverageLoopResponse:
    """
    Execute leverage loop strategy.

    Requires sequential wallet signatures.
    """
```

#### 2. Shortcuts Integration
**Location**: Integration with existing shortcuts endpoint

```python
# Add to shortcuts.json
{
  "pattern": "show lending rates for [asset]",
  "intent": "LENDING_RATES",
  "handler": "lending_handler",
  "examples": [
    "show lending rates for USDC",
    "what are the best lending rates for ETH?",
    "compare lending rates on Aave vs Morpho"
  ]
}
```

---

## User Context Awareness

### Guest Users

**Capabilities**:
- View lending rates (read-only)
- Compare protocols
- View market data
- Educational content

**Restrictions**:
- Cannot execute transactions
- Cannot view personal positions
- Limited to 20 queries/hour

### Authenticated Users

**Capabilities**:
- All guest capabilities
- Execute supply operations
- Execute borrow operations (Aave only)
- Execute leverage loops
- Track positions
- Unlimited queries

**Implementation**:
```python
class UserContextService:
    """Service to determine user capabilities."""

    async def can_execute_transactions(self, user_id: UUID | None) -> bool:
        """Check if user can execute transactions."""
        return user_id is not None

    async def get_lending_capabilities(
        self,
        user_id: UUID | None,
    ) -> LendingCapabilities:
        """Get user's lending capabilities."""

        if user_id is None:
            return LendingCapabilities(
                can_view=True,
                can_supply=False,
                can_borrow=False,
                can_leverage=False,
            )

        return LendingCapabilities(
            can_view=True,
            can_supply=True,
            can_borrow=True,
            can_leverage=True,
        )
```

---

## Multi-Agent Workflow

### Agent Coordination

```python
# Market Scanner Agent → Risk Agent → Executor Agent

class LendingAgentCoordinator:
    """Coordinates multi-agent lending workflows."""

    async def execute_lending_workflow(
        self,
        user_message: str,
        user_id: UUID,
        conversation_id: UUID,
    ) -> WorkflowResult:
        """
        Execute multi-agent lending workflow.

        Flow:
        1. Market Scanner: Find best rates
        2. Risk Agent: Assess health factor impact
        3. Executor Agent: Generate transaction data
        """

        # Step 1: Market Scanner
        market_result = await self._market_scanner.scan(
            message=user_message,
            protocols=[Protocol.AAVE, Protocol.MORPHO],
        )

        # Step 2: Risk Agent
        risk_assessment = await self._risk_agent.assess(
            user_id=user_id,
            operation=market_result.recommended_operation,
        )

        if risk_assessment.risk_level == "high":
            return WorkflowResult(
                recommendation="Consider reducing amount",
                risk_warning=risk_assessment.warning,
            )

        # Step 3: Executor Agent
        execution_plan = await self._executor.prepare(
            user_id=user_id,
            operation=market_result.recommended_operation,
        )

        return WorkflowResult(
            recommended_operation=market_result.recommended_operation,
            risk_level=risk_assessment.risk_level,
            execution_plan=execution_plan,
        )
```

---

## Dependencies

### Dishka DI Configuration

**Location**: `src/app/setup/ioc/lending.py`

```python
class LendingProvider(Provider):
    """Dependency injection for lending features."""

    scope = Scope.REQUEST

    # Domain Services
    lending_service = provide(LendingService)

    # Ports → Adapters
    lending_gateway_aave = provide(
        source=AaveMCPAdapter,
        provides=LendingGateway,
    )

    lending_gateway_morpho = provide(
        source=MorphoMCPAdapter,
        provides=LendingGateway,
    )

    balance_gateway = provide(
        source=BalanceChecker,
        provides=BalanceGateway,
    )

    # Interactors
    supply_interactor = provide(SupplyInteractor)
    borrow_interactor = provide(BorrowInteractor)
    leverage_loop_interactor = provide(LeverageLoopInteractor)
    get_position_interactor = provide(GetPositionInteractor)
```

---

## Error Handling

### Domain Exceptions

```python
# src/app/domain/exceptions/lending.py

class LendingError(DomainException):
    """Base lending exception."""

class InsufficientBalanceError(LendingError):
    """User has insufficient balance."""

class UnsafeBorrowError(LendingError):
    """Borrow would violate health factor minimum."""

class HealthFactorTooLowError(LendingError):
    """Health factor below safe threshold."""

class ProtocolNotSupportedError(LendingError):
    """Protocol not supported for operation."""
```

---

## Summary

This architecture implements the **Hexagonal Architecture** pattern with:

1. **Clear layer separation**: Domain → Application → Infrastructure → Presentation
2. **CQRS pattern**: Separate commands (writes) and queries (reads)
3. **Port-Adapter pattern**: Protocol-agnostic interfaces with MCP adapters
4. **User context awareness**: Different capabilities for guest vs authenticated users
5. **Balance validation**: Pre-transaction balance checks
6. **Health factor monitoring**: Real-time risk assessment
7. **Multi-agent coordination**: Market Scanner → Risk Agent → Executor Agent

All implementations follow the established codebase patterns and integrate seamlessly with existing infrastructure.

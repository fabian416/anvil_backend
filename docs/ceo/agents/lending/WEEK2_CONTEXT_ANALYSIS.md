# Week 2 Context Management Analysis - CQRS & Database Implementation

**Date:** 2026-01-27
**Author:** Context Manager Agent
**Methodology:** MIT Systems Thinking + Stanford Design Thinking + First Principles Analysis
**Status:** Analysis Complete - Ready for Implementation

---

## Executive Summary

This document analyzes context management requirements for Week 2 of the Lending Workflow implementation, focusing on CQRS pattern implementation and database schema design. The analysis maps how context flows through architectural layers and identifies critical gaps that must be addressed for safe, efficient lending operations.

### Key Findings

| Area | Current State | Week 2 Target | Gap |
|------|---------------|---------------|-----|
| Interactor Context | Partial (workflow agents only) | Full CQRS context injection | **P0** |
| Repository Filtering | None | user_id-scoped queries | **P0** |
| Context Caching | Redis 24h TTL | Tiered caching strategy | **P1** |
| Context Security | Basic auth | Full audit trail | **P1** |
| Performance | Unknown | <5 DB queries, <100ms enrichment | **P1** |

---

## 1. Context Flow Diagrams

### 1.1 Current Context Flow (AS-IS)

```
                          +-------------------+
                          |   HTTP Request    |
                          | (JWT in header)   |
                          +--------+----------+
                                   |
                                   v
+------------------------------+---+-----------------------------------+
|        PRESENTATION LAYER    |   |                                   |
+------------------------------+---v-----------------------------------+
|  conversations_router.py         |                                   |
|  - Extract user_id from JWT      |                                   |
|  - Get chat_user from token      |                                   |
|  - Get UserContextAware          |  <-- UserContextService           |
|    (portfolio_state, balance)    |                                   |
+------------------------------+---+-----------------------------------+
                                   |
                                   v
+------------------------------+---+-----------------------------------+
|        APPLICATION LAYER     |   |                                   |
+------------------------------+---v-----------------------------------+
|  AuthenticatedSupervisor         |                                   |
|  - set_user_context(user_id,     |                                   |
|      wallet_address,             |                                   |
|      portfolio_summary)          |                                   |
|  - set_context_aware(ctx)        |  <-- UserContextAware entity      |
|  - Injects into user_metadata    |                                   |
+------------------------------+---+-----------------------------------+
                                   |
                                   v
+------------------------------+---+-----------------------------------+
|      INFRASTRUCTURE LAYER    |   |                                   |
+------------------------------+---v-----------------------------------+
|  BaseWorkflowAgent               |                                   |
|  - _extract_user_context()       |                                   |
|    Returns UserContext:          |                                   |
|    - user_id                     |                                   |
|    - wallet_address              |                                   |
|    - language                    |                                   |
|    - is_authenticated            |                                   |
|    - portfolio_state             |                                   |
|    - total_balance_usd           |                                   |
|    - has_connected_wallet        |                                   |
+------------------------------+---+-----------------------------------+
                                   |
                                   v
+------------------------------+---+-----------------------------------+
|          MCP ADAPTERS        |   |                                   |
+------------------------------+---v-----------------------------------+
|  MorphoGateway / AaveMcpAdapter  |                                   |
|  - NO user context passed!       |  <-- CRITICAL GAP                 |
|  - Queries are protocol-wide     |                                   |
|  - No user_id filtering          |                                   |
+------------------------------------------------------------------+
```

### 1.2 Target Context Flow (TO-BE) for Week 2

```
                          +-------------------+
                          |   HTTP Request    |
                          | (JWT + language)  |
                          +--------+----------+
                                   |
                                   v
+------------------------------------------------------------------+
|        PRESENTATION LAYER (Router)                               |
+------------------------------------------------------------------+
|  Context Extraction:                                             |
|  - user_id: UUID from JWT claims                                 |
|  - language: Accept-Language or query param                      |
|  - wallet_address: from UserContextAware                         |
|  - portfolio_state: from UserContextAware                        |
|  - token_balances: LAZY LOAD on demand (via IBalanceChecker)     |
+------------------------------+-----------------------------------+
                               |
                               v
+------------------------------------------------------------------+
|        APPLICATION LAYER (Interactors)                           |
+------------------------------------------------------------------+
|                                                                  |
|  +----------------------+    +----------------------+            |
|  | SupplyInteractor     |    | BorrowInteractor     |            |
|  +----------------------+    +----------------------+            |
|  | Context Input:       |    | Context Input:       |            |
|  | - user_id (UUID)     |    | - user_id (UUID)     |            |
|  | - wallet_address     |    | - wallet_address     |            |
|  | - protocol           |    | - protocol           |            |
|  | - chain              |    | - chain              |            |
|  | - language           |    | - language           |            |
|  +----------+-----------+    | - current_positions  |            |
|             |                | - risk_tolerance     |            |
|             v                +----------+-----------+            |
|  +----------------------+               |                        |
|  | Balance Validation   |               v                        |
|  | via IBalanceChecker  |    +----------------------+            |
|  +----------------------+    | HF Validation        |            |
|                              | via HealthFactorSvc  |            |
|                              +----------------------+            |
+------------------------------+-----------------------------------+
                               |
                               v
+------------------------------------------------------------------+
|        DOMAIN LAYER (Services)                                   |
+------------------------------------------------------------------+
|  LendingService:                                                 |
|  - validate_supply(user_context, amount, asset, protocol)        |
|  - validate_borrow(user_context, amount, collateral, HF_target)  |
|  - calculate_health_factor_impact(positions, new_debt)           |
|                                                                  |
|  Context Required:                                               |
|  - user_positions: list[LendingPosition]                         |
|  - market_rates: dict[protocol, APYData]                         |
|  - token_prices: dict[token, Decimal]                            |
+------------------------------+-----------------------------------+
                               |
                               v
+------------------------------------------------------------------+
|        INFRASTRUCTURE LAYER (Repositories)                       |
+------------------------------------------------------------------+
|  LendingPositionRepository:                                      |
|  - get_by_user(user_id: UUID) -> list[LendingPosition]           |
|  - get_by_user_and_protocol(user_id, protocol)                   |
|  - save(position: LendingPosition)                               |
|                                                                  |
|  Context Filters (ALL queries include):                          |
|  - user_id: Required for all user-scoped queries                 |
|  - protocol: Optional filter (aave, morpho)                      |
|  - chain: Optional filter (ethereum, base)                       |
|  - status: Optional filter (active, closed)                      |
+------------------------------------------------------------------+
```

---

## 2. Interactor Context Requirements

### 2.1 SupplyInteractor Context

**Location:** `src/app/application/lending/commands/supply.py`

| Context Variable | Type | Source | Required | Caching |
|------------------|------|--------|----------|---------|
| `user_id` | UUID | JWT claims | Yes | N/A |
| `wallet_address` | str | UserContextAware.primary_wallet_address | Yes | 1h (context) |
| `token_balance` | Decimal | IBalanceChecker | Yes | **NO CACHE** |
| `protocol` | str | Request param | Yes | N/A |
| `chain` | str | Request param | Yes | N/A |
| `language` | str | Request header | Yes | N/A |
| `current_apy` | Decimal | MorphoGateway/AaveAdapter | No | 60s |
| `gas_estimate` | Decimal | GasEstimator | No | 30s |

**Context Flow for SupplyInteractor:**

```python
@dataclass
class SupplyCommand:
    """Command input for supply operation."""
    user_id: UUID
    wallet_address: str
    protocol: str  # "aave" | "morpho"
    chain: str     # "ethereum" | "base"
    asset: str     # Token symbol (USDC, ETH)
    amount: Decimal
    language: str = "en"

    # Optional context (enriched by interactor)
    token_balance: Decimal | None = None
    current_apy: Decimal | None = None


class SupplyInteractor:
    """
    Orchestrates supply operation with full context.

    Context Sources:
    1. SupplyCommand - user input context
    2. IBalanceChecker - real-time balance validation
    3. MorphoGateway/AaveAdapter - protocol APY data
    4. LendingPositionRepository - existing positions
    """

    async def execute(self, command: SupplyCommand) -> SupplyResult:
        # 1. Validate user exists
        user = await self._user_repo.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(command.user_id)

        # 2. Check token balance (NEVER CACHED)
        balance = await self._balance_checker.get_balance(
            wallet_address=command.wallet_address,
            token_address=self._get_token_address(command.asset),
            chain=command.chain,
        )
        if balance < command.amount:
            raise InsufficientBalanceError(
                asset=command.asset,
                required=command.amount,
                available=balance,
                language=command.language,
            )

        # 3. Get current APY (cached 60s)
        apy = await self._get_protocol_apy(
            protocol=command.protocol,
            asset=command.asset,
            chain=command.chain,
        )

        # 4. Generate execute_data
        execute_data = self._build_execute_data(command, apy)

        # 5. Save pending position (for tracking)
        position = LendingPosition(
            user_id=command.user_id,
            protocol=command.protocol,
            chain=command.chain,
            asset=command.asset,
            amount=command.amount,
            status=PositionStatus.PENDING,
        )
        await self._position_repo.save(position)

        return SupplyResult(
            execute_data=execute_data,
            position_id=position.id,
            estimated_apy=apy,
        )
```

### 2.2 BorrowInteractor Context

**Location:** `src/app/application/lending/commands/borrow.py`

| Context Variable | Type | Source | Required | Caching |
|------------------|------|--------|----------|---------|
| `user_id` | UUID | JWT claims | Yes | N/A |
| `wallet_address` | str | UserContextAware | Yes | 1h |
| `current_positions` | list[Position] | LendingPositionRepo | Yes | 30s |
| `collateral_usd` | Decimal | Calculated from positions | Yes | 30s |
| `debt_usd` | Decimal | Calculated from positions | Yes | 30s |
| `current_hf` | Decimal | HealthFactorService | Yes | **30s MAX** |
| `projected_hf` | Decimal | Calculated | Yes | N/A |
| `token_prices` | dict | PriceOracle | Yes | 30s |
| `risk_tolerance` | str | UserLendingPreferences | No | 1h |
| `language` | str | Request header | Yes | N/A |

**Context Flow for BorrowInteractor:**

```python
@dataclass
class BorrowCommand:
    """Command input for borrow operation."""
    user_id: UUID
    wallet_address: str
    protocol: str
    chain: str
    asset: str      # Asset to borrow
    amount: Decimal
    language: str = "en"


@dataclass
class BorrowContext:
    """Enriched context for borrow validation."""
    command: BorrowCommand
    current_positions: list[LendingPosition]
    collateral_usd: Decimal
    debt_usd: Decimal
    current_health_factor: HealthFactor
    token_prices: dict[str, Decimal]
    risk_tolerance: str  # conservative, moderate, aggressive


class BorrowInteractor:
    """
    Orchestrates borrow operation with health factor validation.

    CRITICAL: Health factor validation prevents unsafe borrows.
    Users with HF < 1.2 after borrow are BLOCKED.
    """

    async def execute(self, command: BorrowCommand) -> BorrowResult:
        # 1. Build enriched context
        context = await self._build_context(command)

        # 2. Calculate projected health factor
        borrow_value_usd = command.amount * context.token_prices[command.asset]
        projected_debt = context.debt_usd + borrow_value_usd

        projected_hf = HealthFactor.calculate(
            collateral_usd=context.collateral_usd,
            debt_usd=projected_debt,
            liquidation_threshold=self._get_liquidation_threshold(command.protocol),
        )

        # 3. Validate health factor (CRITICAL SAFETY CHECK)
        min_safe_hf = self._get_min_hf(context.risk_tolerance)
        if projected_hf.value < min_safe_hf:
            return BorrowResult(
                success=False,
                blocked=True,
                reason=self._format_unsafe_borrow_message(
                    current_hf=context.current_health_factor.value,
                    projected_hf=projected_hf.value,
                    min_safe_hf=min_safe_hf,
                    language=command.language,
                ),
                health_factor_impact={
                    "current": float(context.current_health_factor.value),
                    "projected": float(projected_hf.value),
                    "minimum_safe": float(min_safe_hf),
                },
            )

        # 4. Generate execute_data
        execute_data = self._build_execute_data(command, context, projected_hf)

        return BorrowResult(
            success=True,
            execute_data=execute_data,
            health_factor_impact={
                "current": float(context.current_health_factor.value),
                "projected": float(projected_hf.value),
                "risk_level": projected_hf.risk_level.value,
            },
        )

    async def _build_context(self, command: BorrowCommand) -> BorrowContext:
        """Build enriched context with parallel fetches."""
        # Parallel fetch for performance
        positions_task = self._position_repo.get_by_user_and_protocol(
            user_id=command.user_id,
            protocol=command.protocol,
            status=PositionStatus.ACTIVE,
        )
        prices_task = self._price_oracle.get_prices(
            tokens=[command.asset],
            chain=command.chain,
        )
        preferences_task = self._preferences_repo.get_by_user(command.user_id)

        positions, prices, preferences = await asyncio.gather(
            positions_task, prices_task, preferences_task
        )

        # Calculate current health factor
        collateral_usd = sum(p.collateral_value_usd for p in positions)
        debt_usd = sum(p.debt_value_usd for p in positions)

        current_hf = HealthFactor.calculate(
            collateral_usd=collateral_usd,
            debt_usd=debt_usd,
            liquidation_threshold=self._get_liquidation_threshold(command.protocol),
        )

        return BorrowContext(
            command=command,
            current_positions=positions,
            collateral_usd=collateral_usd,
            debt_usd=debt_usd,
            current_health_factor=current_hf,
            token_prices=prices,
            risk_tolerance=preferences.risk_tolerance if preferences else "moderate",
        )
```

### 2.3 HealthCheckQueryHandler Context

**Location:** `src/app/application/lending/queries/health_check.py`

| Context Variable | Type | Source | Required | Caching |
|------------------|------|--------|----------|---------|
| `user_id` | UUID | JWT claims | Yes | N/A |
| `protocols` | list[str] | Request param or "all" | Yes | N/A |
| `positions` | list[Position] | LendingPositionRepo | Yes | 30s |
| `health_factors` | dict[protocol, HF] | Calculated | Yes | 30s |
| `alert_thresholds` | dict | UserLendingPreferences | No | 1h |
| `language` | str | Request header | Yes | N/A |

**Context Aggregation for Cross-Protocol View:**

```python
@dataclass
class HealthCheckQuery:
    """Query input for health check."""
    user_id: UUID
    protocols: list[str] | None = None  # None = all protocols
    include_history: bool = False
    language: str = "en"


@dataclass
class HealthCheckResult:
    """Health check result with cross-protocol aggregation."""
    positions_by_protocol: dict[str, list[LendingPosition]]
    health_factors: dict[str, HealthFactor]  # protocol -> HF
    overall_health: str  # "healthy", "warning", "danger"
    alerts: list[HealthAlert]
    recommendations: list[str]


class HealthCheckQueryHandler:
    """
    Handles health check queries with cross-protocol aggregation.

    Optimized for read-only operations with caching.
    """

    async def handle(self, query: HealthCheckQuery) -> HealthCheckResult:
        # 1. Get all user positions (cached 30s)
        positions = await self._position_repo.get_by_user(
            user_id=query.user_id,
            status=PositionStatus.ACTIVE,
        )

        # 2. Group by protocol
        positions_by_protocol: dict[str, list[LendingPosition]] = {}
        for pos in positions:
            if query.protocols is None or pos.protocol in query.protocols:
                positions_by_protocol.setdefault(pos.protocol, []).append(pos)

        # 3. Calculate health factors per protocol
        health_factors: dict[str, HealthFactor] = {}
        for protocol, protocol_positions in positions_by_protocol.items():
            collateral = sum(p.collateral_value_usd for p in protocol_positions)
            debt = sum(p.debt_value_usd for p in protocol_positions)

            health_factors[protocol] = HealthFactor.calculate(
                collateral_usd=collateral,
                debt_usd=debt,
                liquidation_threshold=self._get_liquidation_threshold(protocol),
            )

        # 4. Determine overall health
        overall_health = self._calculate_overall_health(health_factors)

        # 5. Generate alerts and recommendations
        alerts = self._generate_alerts(health_factors, query.language)
        recommendations = self._generate_recommendations(
            positions_by_protocol, health_factors, query.language
        )

        return HealthCheckResult(
            positions_by_protocol=positions_by_protocol,
            health_factors=health_factors,
            overall_health=overall_health,
            alerts=alerts,
            recommendations=recommendations,
        )
```

---

## 3. Repository Context Requirements

### 3.1 User-Scoped Query Pattern

**ALL repository queries MUST include user_id filter:**

```python
class LendingPositionRepository(Protocol):
    """
    Port for lending position persistence.

    SECURITY: All queries MUST be scoped to user_id.
    NO global queries that could leak user data.
    """

    async def get_by_user(
        self,
        user_id: UUID,
        status: PositionStatus | None = None,
    ) -> list[LendingPosition]:
        """Get all positions for a user."""
        ...

    async def get_by_user_and_protocol(
        self,
        user_id: UUID,
        protocol: str,
        status: PositionStatus | None = None,
    ) -> list[LendingPosition]:
        """Get positions for a specific protocol."""
        ...

    async def get_by_id(
        self,
        position_id: UUID,
        user_id: UUID,  # REQUIRED for security
    ) -> LendingPosition | None:
        """
        Get position by ID with user verification.

        CRITICAL: user_id is required to prevent
        unauthorized access to other users' positions.
        """
        ...
```

### 3.2 Multi-Protocol Position Aggregation

```python
class LendingPositionRepositorySqla(LendingPositionRepository):
    """
    SQLAlchemy implementation with efficient aggregation.
    """

    async def get_aggregated_by_user(
        self,
        user_id: UUID,
    ) -> dict[str, PositionAggregate]:
        """
        Get aggregated positions grouped by protocol.

        Uses single query with GROUP BY for efficiency.
        """
        query = (
            select(
                LendingPositionModel.protocol,
                func.sum(LendingPositionModel.collateral_usd).label("total_collateral"),
                func.sum(LendingPositionModel.debt_usd).label("total_debt"),
                func.count(LendingPositionModel.id).label("position_count"),
            )
            .where(
                LendingPositionModel.user_id == user_id,
                LendingPositionModel.status == PositionStatus.ACTIVE.value,
            )
            .group_by(LendingPositionModel.protocol)
        )

        result = await self._session.execute(query)

        return {
            row.protocol: PositionAggregate(
                total_collateral=row.total_collateral,
                total_debt=row.total_debt,
                position_count=row.position_count,
            )
            for row in result
        }
```

### 3.3 Caching Strategy for Repository Queries

| Query Type | Cache Key Pattern | TTL | Invalidation |
|------------|-------------------|-----|--------------|
| User positions | `lending:positions:{user_id}` | 30s | On transaction confirm |
| Protocol positions | `lending:positions:{user_id}:{protocol}` | 30s | On transaction confirm |
| Position by ID | `lending:position:{position_id}` | 60s | On update |
| Aggregated positions | `lending:aggregate:{user_id}` | 30s | On any position change |

```python
class CachedLendingPositionRepository:
    """
    Repository wrapper with Redis caching.
    """

    def __init__(
        self,
        inner: LendingPositionRepository,
        redis: Redis,
    ):
        self._inner = inner
        self._redis = redis

    async def get_by_user(
        self,
        user_id: UUID,
        status: PositionStatus | None = None,
    ) -> list[LendingPosition]:
        cache_key = f"lending:positions:{user_id}"
        if status:
            cache_key += f":{status.value}"

        # Try cache
        cached = await self._redis.get(cache_key)
        if cached:
            return [LendingPosition.from_dict(p) for p in json.loads(cached)]

        # Fetch and cache
        positions = await self._inner.get_by_user(user_id, status)
        await self._redis.setex(
            cache_key,
            30,  # 30 second TTL
            json.dumps([p.to_dict() for p in positions]),
        )

        return positions

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all cached positions for a user."""
        pattern = f"lending:positions:{user_id}*"
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)
```

---

## 4. Context Variables Gap Analysis

### 4.1 P0 Context Variables (CRITICAL - Week 2 Must Have)

| Variable | Current Status | Week 2 Implementation |
|----------|----------------|----------------------|
| `user_id` | Available via JWT | Pass to all interactors and repositories |
| `wallet_address` | Available via UserContextAware | Pass to SupplyInteractor for balance check |
| `balance_by_token` | **MISSING** | Integrate IBalanceChecker into SupplyInteractor |
| `risk_profile` | **MISSING** | Add `user_lending_preferences` table |
| `health_factor` | Available via MCP (mock) | Calculate from real positions in DB |
| `current_positions` | **MISSING** | Implement LendingPositionRepository |

### 4.2 P1 Context Variables (HIGH - Week 2 Should Have)

| Variable | Current Status | Week 2 Implementation |
|----------|----------------|----------------------|
| `gas_estimate` | Not in context | Add via GasEstimator adapter |
| `language` | Available | Pass through all layers |
| `subscription_tier` | In AuthenticatedContext | Propagate to interactors for rate limits |
| `protocol_status` | Not tracked | Add health check via MCP |

### 4.3 Context Variable Flow Matrix

```
                    Router  Supervisor  Interactor  Domain  Repository
user_id               [X]        [X]        [X]      [X]        [X]
wallet_address        [X]        [X]        [X]      [ ]        [ ]
language              [X]        [X]        [X]      [X]        [ ]
portfolio_state       [X]        [X]        [X]      [ ]        [ ]
total_balance_usd     [X]        [X]        [X]      [ ]        [ ]
token_balances        [ ]        [ ]       [X]*     [X]*       [ ]
current_positions     [ ]        [ ]       [X]*     [X]*      [X]*
health_factor         [ ]        [ ]       [X]*     [X]*       [ ]
risk_tolerance        [ ]        [ ]       [X]*     [X]*      [X]*

[X] = Currently available
[X]* = To be implemented in Week 2
[ ] = Not needed at this layer
```

---

## 5. Caching Strategy Recommendations

### 5.1 Cache Tiers

| Tier | Data Type | TTL | Justification |
|------|-----------|-----|---------------|
| **NEVER CACHE** | Token balances | 0s | Balance changes with every tx |
| **NEVER CACHE** | Transaction status | 0s | Must be real-time |
| **Safety Critical** | Health factors | 30s MAX | Stale HF could allow unsafe borrow |
| **Safety Critical** | Token prices | 30s | Used in HF calculation |
| **Frequent Read** | User positions | 60s | Read often, changes rarely |
| **Slow Change** | APY rates | 60s | Changes slowly |
| **User Preferences** | Risk tolerance | 1h | Rarely changes |
| **Static** | Protocol config | 24h | Changes with deployments |

### 5.2 Cache Invalidation Strategy

```python
class LendingCacheInvalidator:
    """
    Centralized cache invalidation for lending operations.

    Called after successful transaction confirmation.
    """

    async def on_transaction_confirmed(
        self,
        user_id: UUID,
        protocol: str,
        transaction_type: str,  # supply, borrow, repay, withdraw
    ) -> None:
        """Invalidate relevant caches after transaction."""

        # Always invalidate positions
        await self._redis.delete(f"lending:positions:{user_id}")
        await self._redis.delete(f"lending:positions:{user_id}:{protocol}")
        await self._redis.delete(f"lending:aggregate:{user_id}")

        # Invalidate health factor cache
        await self._redis.delete(f"lending:health:{user_id}")

        # Invalidate context aware (triggers recalculation)
        await self._redis.delete(f"context:user:{user_id}")

        logger.info(
            f"Invalidated lending caches for user {user_id} "
            f"after {transaction_type} on {protocol}"
        )
```

### 5.3 Cache Key Namespacing

```
anvil:lending:positions:{user_id}           # User positions
anvil:lending:positions:{user_id}:{protocol} # Protocol-specific
anvil:lending:health:{user_id}              # Health factor
anvil:lending:aggregate:{user_id}           # Aggregated view
anvil:lending:tx:{conversation_id}:{action_id} # Pending transaction
anvil:context:user:{user_id}                # User context
anvil:market:apy:{protocol}:{asset}:{chain} # APY data
anvil:market:price:{token}:{chain}          # Token prices
```

---

## 6. Context Security Considerations

### 6.1 User Data Isolation

**CRITICAL RULE:** Users can ONLY access their own positions.

```python
class SecurePositionRepository:
    """
    Repository with mandatory user_id verification.
    """

    async def get_by_id(
        self,
        position_id: UUID,
        requesting_user_id: UUID,
    ) -> LendingPosition | None:
        """
        Get position with user verification.

        SECURITY: Always verify position belongs to requesting user.
        """
        position = await self._inner.get_by_id(position_id)

        if position is None:
            return None

        if position.user_id != requesting_user_id:
            # Log security event
            logger.warning(
                f"SECURITY: User {requesting_user_id} attempted to access "
                f"position {position_id} belonging to {position.user_id}"
            )
            # Return None (don't reveal position exists)
            return None

        return position
```

### 6.2 Context Variable Sanitization

```python
@dataclass
class SupplyCommand:
    """Supply command with input validation."""

    user_id: UUID
    wallet_address: str
    protocol: str
    chain: str
    asset: str
    amount: Decimal

    def __post_init__(self):
        """Validate all inputs."""
        # Validate wallet address format
        if not self._is_valid_eth_address(self.wallet_address):
            raise InvalidWalletAddressError(self.wallet_address)

        # Validate protocol
        if self.protocol not in SUPPORTED_PROTOCOLS:
            raise UnsupportedProtocolError(self.protocol)

        # Validate chain
        if self.chain not in SUPPORTED_CHAINS:
            raise UnsupportedChainError(self.chain)

        # Validate amount is positive
        if self.amount <= Decimal("0"):
            raise InvalidAmountError(self.amount)

        # Sanitize asset (uppercase, strip whitespace)
        self.asset = self.asset.upper().strip()

    @staticmethod
    def _is_valid_eth_address(address: str) -> bool:
        """Validate Ethereum address format."""
        import re
        return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))
```

### 6.3 Audit Trail for Context Access

```python
class AuditedInteractor:
    """
    Base interactor with audit logging.
    """

    async def execute_with_audit(
        self,
        command: Any,
        audit_context: AuditContext,
    ) -> Any:
        """Execute with full audit trail."""
        start_time = time.time()

        try:
            result = await self.execute(command)

            # Log successful execution
            await self._audit_log.record(
                event_type="LENDING_COMMAND_SUCCESS",
                user_id=command.user_id,
                command_type=type(command).__name__,
                command_data=self._sanitize_for_audit(command),
                result_summary=self._summarize_result(result),
                duration_ms=int((time.time() - start_time) * 1000),
                ip_address=audit_context.ip_address,
                user_agent=audit_context.user_agent,
            )

            return result

        except Exception as e:
            # Log failed execution
            await self._audit_log.record(
                event_type="LENDING_COMMAND_FAILURE",
                user_id=command.user_id,
                command_type=type(command).__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
            raise
```

---

## 7. Performance Optimization

### 7.1 Query Count Targets

| Operation | Target DB Queries | Target MCP Calls | Target Latency |
|-----------|-------------------|------------------|----------------|
| Supply command | <=3 | 1 | <200ms |
| Borrow command | <=4 | 1-2 | <300ms |
| Health check query | <=2 | 0 | <100ms |
| Position list | <=1 | 0 | <50ms |

### 7.2 Parallel Context Enrichment

```python
class BorrowInteractor:
    """
    Borrow interactor with parallel context fetching.
    """

    async def _build_context(self, command: BorrowCommand) -> BorrowContext:
        """
        Build context with parallel fetches.

        Performance: 3 parallel requests instead of sequential.
        Expected latency: ~100ms (max of 3) vs ~300ms (sum of 3)
        """
        async with asyncio.TaskGroup() as tg:
            positions_task = tg.create_task(
                self._position_repo.get_by_user_and_protocol(
                    user_id=command.user_id,
                    protocol=command.protocol,
                )
            )
            prices_task = tg.create_task(
                self._price_oracle.get_prices([command.asset])
            )
            preferences_task = tg.create_task(
                self._preferences_repo.get_by_user(command.user_id)
            )

        return BorrowContext(
            positions=positions_task.result(),
            prices=prices_task.result(),
            preferences=preferences_task.result(),
        )
```

### 7.3 Database Index Strategy

```sql
-- Position queries by user (most common)
CREATE INDEX idx_lending_positions_user_id
ON lending_positions(user_id);

-- Position queries by user + protocol
CREATE INDEX idx_lending_positions_user_protocol
ON lending_positions(user_id, protocol);

-- Position queries by user + status (active positions)
CREATE INDEX idx_lending_positions_user_status
ON lending_positions(user_id, status)
WHERE status = 'active';

-- Transaction history by user
CREATE INDEX idx_lending_transactions_user_created
ON lending_transactions(user_id, created_at DESC);
```

---

## 8. Context Observability

### 8.1 Structured Logging Format

```python
# Context variables in structured logs
logger.info(
    "Processing supply command",
    extra={
        "user_id": str(command.user_id),
        "wallet_address": command.wallet_address[:10] + "...",  # Truncated for security
        "protocol": command.protocol,
        "chain": command.chain,
        "asset": command.asset,
        "amount": str(command.amount),
        "context": {
            "balance_checked": True,
            "balance_sufficient": True,
            "apy_fetched": True,
            "cache_hits": {
                "apy": True,
                "positions": False,
            },
        },
    }
)
```

### 8.2 Context Flow Tracing

```python
@dataclass
class ContextTrace:
    """Trace context flow through layers."""
    trace_id: str
    user_id: UUID
    operation: str

    # Layer timestamps
    router_entry: datetime
    supervisor_entry: datetime | None = None
    interactor_entry: datetime | None = None
    domain_entry: datetime | None = None
    repository_entry: datetime | None = None

    # Context enrichment
    balance_fetch_ms: int | None = None
    position_fetch_ms: int | None = None
    price_fetch_ms: int | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "trace_id": self.trace_id,
            "user_id": str(self.user_id),
            "operation": self.operation,
            "timings": {
                "router_to_supervisor_ms": self._delta_ms(
                    self.router_entry, self.supervisor_entry
                ),
                "supervisor_to_interactor_ms": self._delta_ms(
                    self.supervisor_entry, self.interactor_entry
                ),
                "balance_fetch_ms": self.balance_fetch_ms,
                "position_fetch_ms": self.position_fetch_ms,
                "price_fetch_ms": self.price_fetch_ms,
            },
        }
```

### 8.3 Monitoring Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `lending_context_enrichment_duration_ms` | Histogram | Time to enrich context |
| `lending_cache_hit_rate` | Gauge | Cache hit ratio by key type |
| `lending_context_validation_failures` | Counter | Validation failures by type |
| `lending_db_queries_per_request` | Histogram | DB queries per operation |
| `lending_mcp_calls_per_request` | Histogram | MCP calls per operation |

---

## 9. Implementation Checklist for Week 2

### 9.1 Day 8-10: CQRS Implementation

- [ ] **Task 2.1: SupplyCommand + SupplyInteractor**
  - [ ] Create `SupplyCommand` dataclass with validation
  - [ ] Implement `SupplyInteractor` with balance check
  - [ ] Inject `IBalanceChecker` via Dishka
  - [ ] Add context logging
  - [ ] Unit tests for command validation

- [ ] **Task 2.2: BorrowCommand + BorrowInteractor**
  - [ ] Create `BorrowCommand` dataclass
  - [ ] Implement parallel context fetching
  - [ ] Add health factor validation
  - [ ] Add risk tolerance check
  - [ ] Unit tests for HF validation

- [ ] **Task 2.3: HealthCheckQuery + Handler**
  - [ ] Create `HealthCheckQuery` dataclass
  - [ ] Implement cross-protocol aggregation
  - [ ] Add caching (30s TTL)
  - [ ] Unit tests for aggregation

### 9.2 Day 11-14: Database & Repository

- [ ] **Task 2.4: Alembic Migrations**
  - [ ] Create `lending_positions` table
  - [ ] Create `lending_supplies` table
  - [ ] Create `lending_borrows` table
  - [ ] Create `lending_transactions` table
  - [ ] Add indexes for user_id queries
  - [ ] Add foreign keys to chat_users

- [ ] **Task 2.5: SQLAlchemy Mappings**
  - [ ] Create `LendingPositionModel`
  - [ ] Create `LendingSupplyModel`
  - [ ] Create `LendingBorrowModel`
  - [ ] Create `LendingTransactionModel`
  - [ ] Configure relationships

- [ ] **Task 2.6: Repository Implementation**
  - [ ] Implement `LendingPositionRepositorySqla`
  - [ ] Implement `LendingTransactionRepositorySqla`
  - [ ] Add user_id filtering to all queries
  - [ ] Integration tests with test database

- [ ] **Task 2.7: Caching Layer**
  - [ ] Implement `CachedLendingPositionRepository`
  - [ ] Implement `LendingCacheInvalidator`
  - [ ] Configure Redis key patterns
  - [ ] Add cache metrics

### 9.3 Context Integration Tasks

- [ ] **Context Injection**
  - [ ] Update `conversations_router.py` to pass context to interactors
  - [ ] Update `AuthenticatedSupervisor` to inject lending context
  - [ ] Add context trace logging

- [ ] **Context Validation**
  - [ ] Implement wallet address validation
  - [ ] Implement protocol validation
  - [ ] Implement chain validation
  - [ ] Implement amount validation

- [ ] **Context Security**
  - [ ] Add user_id verification to all repository methods
  - [ ] Implement audit logging
  - [ ] Add rate limiting by user

---

## 10. References

**Gap Analysis Documents:**
- [GAP_ANALYSIS.md](./GAP_ANALYSIS.md) - Backend implementation gaps
- [CONTEXT_MANAGEMENT_GAP.md](./CONTEXT_MANAGEMENT_GAP.md) - Context gaps (source)
- [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) - Full roadmap

**Existing Code References:**
- `src/app/application/chat/services/user_context_service.py` - Context aggregation
- `src/app/domain/chat/entities/user_context_aware.py` - Context entity
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py` - Workflow context
- `src/app/application/chat/handlers/lending_handler.py` - Current lending handler
- `src/app/domain/services/agent_squad/authenticated_supervisor.py` - Context injection

---

**Document Status:** Complete - Ready for Implementation
**Next Review Date:** After Week 2 completion
**Owner:** Backend Engineering Team
**Last Updated:** 2026-01-27

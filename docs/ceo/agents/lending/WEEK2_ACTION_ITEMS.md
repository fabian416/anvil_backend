# Week 2 Action Items - Lending Feature

**Status**: 🔴 **WEEK 2 NOT STARTED**
**Created**: 2026-01-27
**Priority**: P0 - CRITICAL
**Assignee**: @backend-engineer

---

## Summary

Week 1 (Health Factor Validation) is **COMPLETE** ✅
Week 2 (CQRS & Database) is **NOT STARTED** ❌

**Critical Finding**: Only example code exists. No production CQRS commands, no database tables, no repositories.

---

## Priority 0 - Critical (Must Complete This Week)

### 1. Database Schema Implementation

**Estimated Time**: 2 days
**Status**: ❌ NOT STARTED

**Tasks:**
- [ ] Create Alembic migration for `lending_positions` table
  ```bash
  alembic revision -m "add lending_positions table"
  ```
  - UUID primary key
  - Foreign key to users table
  - Health factor fields (current_hf, projected_hf, liquidation_threshold)
  - Risk level enum (low, moderate, high, critical, liquidatable)
  - Indexes on user_id, wallet_address, protocol, risk_level

- [ ] Create Alembic migration for `lending_supplies` table
  - UUID primary key
  - Foreign key to lending_positions (CASCADE DELETE)
  - Asset information (symbol, address, decimals)
  - Amount fields (amount, amount_usd)
  - Yield information (supply_apy, reward_apy, total_apy)
  - Collateral status (is_collateral, ltv)
  - Protocol-specific fields (atoken_address for Aave, vault_address for Morpho)

- [ ] Create Alembic migration for `lending_borrows` table
  - UUID primary key
  - Foreign key to lending_positions (CASCADE DELETE)
  - Asset information (symbol, address, decimals)
  - Borrow details (amount, amount_usd)
  - Interest rate (borrow_apy, rate_mode: variable/stable)
  - Debt token address

- [ ] Create Alembic migration for `lending_transactions` table
  - UUID primary key
  - User reference (user_id, wallet_address)
  - Position reference (position_id, nullable)
  - Transaction details (tx_hash UNIQUE, action_type, protocol, chain)
  - Asset information (symbol, address, amount, amount_usd)
  - Status (pending, confirmed, failed, reverted)
  - Health factor impact (hf_before, hf_after)
  - Error information (error_message, error_code)
  - Metadata JSONB

- [ ] Apply migrations
  ```bash
  alembic upgrade head
  ```

- [ ] Verify tables in PostgreSQL
  ```sql
  \dt lending_*
  SELECT * FROM lending_positions LIMIT 1;
  ```

**Files to Create:**
```
src/app/infrastructure/persistence_sqla/alembic/versions/
├── 2026_01_28_XXXX-add_lending_positions_table.py
├── 2026_01_28_XXXX-add_lending_supplies_table.py
├── 2026_01_28_XXXX-add_lending_borrows_table.py
└── 2026_01_28_XXXX-add_lending_transactions_table.py
```

**Reference**: `docs/ceo/agents/lending/database_schema.md`

---

### 2. SQLAlchemy Mappings

**Estimated Time**: 1 day
**Status**: ❌ NOT STARTED
**Depends On**: Database migrations complete

**Tasks:**
- [ ] Create lending mappings file
  - Location: `src/app/infrastructure/persistence_sqla/mappings/lending.py`
  - Use imperative mapping (NOT declarative)
  - Map domain entities to database tables
  - Define relationships (one-to-many for supplies/borrows)

- [ ] Create table definitions
  - Import `Table` from sqlalchemy
  - Define all 4 tables with proper column types
  - Match Alembic migration schemas exactly

- [ ] Map domain entities
  ```python
  from app.domain.entities.lending import AavePosition, MorphoPosition
  from sqlalchemy.orm import registry, relationship

  mapper_registry = registry()

  mapper_registry.map_imperatively(
      AavePosition,
      lending_positions_table,
      properties={
          "supplies": relationship(SupplyPosition, ...),
          "borrows": relationship(BorrowPosition, ...),
      }
  )
  ```

- [ ] Verify entity remains pure (no SQLAlchemy imports in domain)

**Files to Create:**
```
src/app/infrastructure/persistence_sqla/mappings/lending.py
```

**Reference**: Existing mappings in `mappings/` directory

---

### 3. Repository Port & Adapter

**Estimated Time**: 1.5 days
**Status**: ❌ NOT STARTED
**Depends On**: SQLAlchemy mappings complete

**Tasks:**
- [ ] Define ILendingRepository port (domain layer)
  - Location: `src/app/domain/ports/lending_repository.py`
  ```python
  from typing import Protocol, List, Optional
  from uuid import UUID

  class ILendingRepository(Protocol):
      async def save_position(self, position: LendingPosition) -> None: ...
      async def get_position(self, position_id: UUID) -> Optional[LendingPosition]: ...
      async def get_user_positions(self, user_id: UUID) -> List[LendingPosition]: ...
      async def get_position_by_wallet(self, wallet: str, protocol: str) -> Optional[LendingPosition]: ...
      async def save_transaction(self, tx: LendingTransaction) -> None: ...
      async def update_transaction_status(self, tx_hash: str, status: str) -> None: ...
  ```

- [ ] Implement SQLAlchemyLendingRepository (infrastructure layer)
  - Location: `src/app/infrastructure/persistence_sqla/repositories/lending_repository.py`
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession

  class SQLAlchemyLendingRepository:
      def __init__(self, session: AsyncSession):
          self._session = session

      async def save_position(self, position: LendingPosition) -> None:
          self._session.add(position)
          await self._session.commit()
  ```

- [ ] Add transaction handling (commit/rollback)
- [ ] Add error handling (PostgreSQL-specific errors)
- [ ] Add logging

**Files to Create:**
```
src/app/domain/ports/lending_repository.py
src/app/infrastructure/persistence_sqla/repositories/lending_repository.py
```

---

### 4. Production CQRS Commands

**Estimated Time**: 2 days
**Status**: ❌ NOT STARTED (example only)
**Depends On**: Repository, Health Factor Validator

**Tasks:**

#### SupplyCommand
- [ ] Create `SupplyCommand` dataclass
  - Location: `src/app/application/lending/commands/supply.py`
  ```python
  @dataclass(frozen=True)
  class SupplyCommand:
      user_id: UUID
      wallet: str
      protocol: str  # "aave" | "morpho"
      asset: str
      amount: Decimal
      chain: str = "ethereum"
  ```

- [ ] Create `SupplyResult` dataclass
  ```python
  @dataclass(frozen=True)
  class SupplyResult:
      status: str  # "awaiting_signature"
      execute_data: dict  # Transaction calldata for Privy
      validation: HealthFactorResult
      message: str
  ```

- [ ] Create `SupplyInteractor`
  - Validate balance (via IBalanceChecker port)
  - Validate health factor improvement (optional)
  - Generate execute_data (via IAaveExecutor or IMorphoExecutor port)
  - Save intent to database (via ILendingRepository)
  - Return SupplyResult

#### BorrowCommand
- [ ] Create production `BorrowCommand` (copy from example)
- [ ] Create production `BorrowResult`
- [ ] Create production `BorrowInteractor`
  - **CRITICAL**: Health factor validation BEFORE execute_data
  - Validate collateral sufficiency
  - Block if HF < 1.2
  - Generate execute_data only if safe
  - Save intent to database
  - Return BorrowResult

#### HealthCheckQuery
- [ ] Create `HealthCheckQuery` dataclass
  ```python
  @dataclass(frozen=True)
  class HealthCheckQuery:
      wallet: str
      chain: str = "ethereum"
  ```

- [ ] Create `HealthCheckResult` dataclass (read-optimized)
  ```python
  @dataclass(frozen=True)
  class HealthCheckResult:
      positions: List[PositionSummary]
      total_collateral_usd: Decimal
      total_debt_usd: Decimal
      min_health_factor: Decimal
      risk_level: RiskLevel
  ```

- [ ] Create `HealthCheckQueryHandler`
  - Read-only operation (no side effects)
  - Fetch from database (via ILendingRepository)
  - OR fetch from MCP servers (via IAaveGateway)
  - Return aggregated health metrics

**Files to Create:**
```
src/app/application/lending/commands/
├── supply.py
├── borrow.py (production version)
└── __init__.py

src/app/application/lending/queries/
├── health_check.py
└── __init__.py

src/app/application/lending/interactors/
├── supply_interactor.py
├── borrow_interactor.py
└── health_check_query_handler.py
```

---

### 5. Dependency Injection Configuration

**Estimated Time**: 0.5 day
**Status**: ❌ NOT STARTED
**Depends On**: All above components complete

**Tasks:**
- [ ] Create lending IoC provider
  - Location: `src/app/setup/ioc/lending.py`

  ```python
  from dishka import Provider, Scope, provide
  from sqlalchemy.ext.asyncio import AsyncSession

  from app.application.lending.commands.supply import SupplyInteractor
  from app.application.lending.commands.borrow import BorrowInteractor
  from app.application.lending.queries.health_check import HealthCheckQueryHandler
  from app.domain.ports.lending_repository import ILendingRepository
  from app.infrastructure.persistence_sqla.repositories.lending_repository import (
      SQLAlchemyLendingRepository,
  )

  class LendingProvider(Provider):
      scope = Scope.REQUEST

      # Interactors
      supply_interactor = provide(SupplyInteractor)
      borrow_interactor = provide(BorrowInteractor)
      health_check_handler = provide(HealthCheckQueryHandler)

      # Repositories
      @provide
      def lending_repository(self, session: AsyncSession) -> ILendingRepository:
          return SQLAlchemyLendingRepository(session)

      # Domain services (already registered elsewhere, just reference)
      # hf_validator = provide(HealthFactorValidator)
  ```

- [ ] Register provider in main container
  - Location: `src/app/setup/ioc/__init__.py` or main app setup

  ```python
  from .lending import LendingProvider

  container = make_async_container(
      # ... existing providers
      LendingProvider(),
  )
  ```

- [ ] Verify dependency resolution
  ```python
  # Test DI resolution
  async with container() as request_container:
      interactor = await request_container.get(SupplyInteractor)
      assert interactor is not None
  ```

**Files to Create:**
```
src/app/setup/ioc/lending.py
```

**Files to Modify:**
```
src/app/setup/ioc/__init__.py (or wherever container is created)
```

---

## Priority 1 - High (Complete by End of Week 2)

### 6. Exception Hierarchy

**Estimated Time**: 0.5 day
**Status**: ⚠️ PARTIAL (only UnsafeBorrowError exists)

**Tasks:**
- [ ] Create complete exception hierarchy
  - Location: `src/app/domain/exceptions/lending.py`

  ```python
  class LendingError(Exception):
      """Base exception for lending operations"""
      pass

  class BalanceInsufficientError(LendingError):
      """Raised when user has insufficient balance"""
      def __init__(self, required: Decimal, available: Decimal, asset: str):
          self.required = required
          self.available = available
          self.asset = asset
          super().__init__(
              f"Insufficient {asset} balance. Required: {required}, Available: {available}"
          )

  class UnsafeBorrowError(LendingError):
      """Raised when borrow would result in unsafe health factor (already exists)"""
      pass

  class PositionNotFoundError(LendingError):
      """Raised when lending position not found"""
      pass

  class ProtocolNotSupportedError(LendingError):
      """Raised when protocol is not supported"""
      pass
  ```

**Files to Create:**
```
src/app/domain/exceptions/lending.py
```

---

### 7. Application Layer Tests

**Estimated Time**: 1 day
**Status**: ❌ NOT STARTED
**Depends On**: Commands/queries implemented

**Tasks:**
- [ ] Create command validation tests
  - Test: SupplyCommand with invalid amounts
  - Test: BorrowCommand with invalid protocol
  - Test: HealthCheckQuery with invalid wallet

- [ ] Create interactor tests with mocked ports
  ```python
  @pytest.mark.asyncio
  async def test_supply_interactor_success(mocker):
      # Mock dependencies
      balance_checker = mocker.Mock(spec=IBalanceChecker)
      balance_checker.check_balance.return_value = True

      executor = mocker.Mock(spec=IAaveExecutor)
      executor.generate_supply_calldata.return_value = {"to": "0x...", "data": "0x..."}

      repository = mocker.Mock(spec=ILendingRepository)

      # Test
      interactor = SupplyInteractor(balance_checker, executor, repository)
      result = await interactor.execute(SupplyCommand(...))

      assert result.status == "awaiting_signature"
      assert result.execute_data is not None
  ```

- [ ] Create error handling tests
  - Test: Insufficient balance raises BalanceInsufficientError
  - Test: Unsafe borrow raises UnsafeBorrowError
  - Test: Invalid protocol raises ProtocolNotSupportedError

**Files to Create:**
```
tests/unit/application/lending/
├── commands/
│   ├── test_supply_interactor.py
│   └── test_borrow_interactor.py
└── queries/
    └── test_health_check_query_handler.py
```

**Target Coverage**: >85% application layer

---

### 8. Integration Tests

**Estimated Time**: 1 day
**Status**: ❌ NOT STARTED
**Depends On**: Repository implemented

**Tasks:**
- [ ] Create repository integration tests (with test database)
  ```python
  @pytest.mark.integration
  async def test_save_and_retrieve_position(test_db_session):
      repository = SQLAlchemyLendingRepository(test_db_session)

      # Create position
      position = LendingPosition(...)
      await repository.save_position(position)

      # Retrieve position
      retrieved = await repository.get_position(position.id)

      assert retrieved.id == position.id
      assert retrieved.total_collateral_usd == position.total_collateral_usd
  ```

- [ ] Create migration tests
  - Test: Alembic upgrade/downgrade works
  - Test: All constraints enforced
  - Test: Indexes created

- [ ] Create transaction tests
  - Test: Rollback on error
  - Test: Commit on success

**Files to Create:**
```
tests/integration/persistence/
├── test_lending_repository.py
└── test_lending_migrations.py
```

**Target Coverage**: >70% infrastructure layer

---

## Verification Checklist

### Before Marking Week 2 Complete:

- [ ] **Database**
  - [ ] All 4 tables created in PostgreSQL
  - [ ] Migrations can upgrade/downgrade
  - [ ] Indexes exist on all query columns
  - [ ] Constraints enforced (check with invalid data)

- [ ] **Repository**
  - [ ] Can save positions to database
  - [ ] Can retrieve positions by ID, wallet, user_id
  - [ ] Can save transactions
  - [ ] Transactions rollback on error

- [ ] **CQRS**
  - [ ] SupplyCommand returns execute_data
  - [ ] BorrowCommand blocks unsafe borrows (HF < 1.2)
  - [ ] HealthCheckQuery returns read-only data
  - [ ] No business logic in commands/queries

- [ ] **Dependency Injection**
  - [ ] All interactors can be instantiated
  - [ ] Repositories injected correctly
  - [ ] Scopes are REQUEST level

- [ ] **Tests**
  - [ ] Domain: >90% coverage (already achieved ✅)
  - [ ] Application: >85% coverage
  - [ ] Infrastructure: >70% coverage
  - [ ] All tests pass

- [ ] **Type Safety**
  - [ ] MyPy passes with no errors
  - [ ] All functions have type hints
  - [ ] No `Any` types used

---

## Timeline

**Total Estimated Time**: 7 days (can be parallelized to 5 days)

### Day 1-2: Database Foundation
- Create all 4 Alembic migrations
- Apply migrations to local database
- Verify tables created correctly

### Day 3: Mappings & Repository
- Create SQLAlchemy mappings
- Define ILendingRepository port
- Implement SQLAlchemyLendingRepository adapter
- Test basic CRUD operations

### Day 4-5: CQRS Implementation
- Implement SupplyCommand + SupplyInteractor
- Implement BorrowCommand + BorrowInteractor (production version)
- Implement HealthCheckQuery + HealthCheckQueryHandler
- Integrate with repository

### Day 6: Dependency Injection & Testing
- Configure lending IoC provider
- Add application layer tests (mocked ports)
- Add integration tests (with database)

### Day 7: Verification & Cleanup
- Run all tests
- Verify test coverage (>85% application, >70% infrastructure)
- Run MyPy type checking
- Code review
- Update documentation

---

## Success Criteria

Week 2 is **COMPLETE** when:

1. ✅ All 4 database tables exist and migrations work
2. ✅ Can save and retrieve lending positions from database
3. ✅ Production SupplyCommand, BorrowCommand, HealthCheckQuery implemented
4. ✅ BorrowCommand blocks unsafe borrows (HF < 1.2)
5. ✅ Dependency injection configured and working
6. ✅ Test coverage: >90% domain, >85% application, >70% infrastructure
7. ✅ All tests pass
8. ✅ MyPy type checking passes

---

## Notes

- **Example code is NOT production code**: The `borrow_example.py` file is for reference only
- **Follow hexagonal architecture**: Keep domain pure, use ports/adapters
- **Test-driven development**: Write tests as you implement
- **Commit frequently**: Small, focused commits with clear messages

---

**Status**: 🔴 **READY TO START**
**Next Review**: After Day 3 (database + repository complete)
**Final Review**: After Day 7 (all Week 2 tasks complete)

**Assignee**: @backend-engineer
**Reviewer**: @code-review-waltz
**Created**: 2026-01-27

# Week 4 (Days 25-27) Implementation Summary

**Status:** ✅ COMPLETE
**Date:** 2026-01-27
**Revision:** lending_core_002

---

## Implementation Overview

Successfully implemented Week 4 remaining database tables and views from the lending workflow roadmap:

### Part 1: Database Tables (4 Tables)

1. **user_lending_preferences** - User risk preferences and notification settings
2. **lending_health_checks** - Health factor monitoring history
3. **leverage_loop_executions** - Multi-step leverage loop tracking
4. **lending_alerts** - Alert notifications for users

### Part 2: Database Views (2 Views)

1. **user_lending_summary** - Aggregated user lending positions across protocols
2. **protocol_comparison** - Real-time protocol comparison metrics

---

## Files Created/Modified

### 1. Alembic Migration

**File:** `src/app/infrastructure/persistence_sqla/alembic/versions/2026_01_27_0200-lending_core_002_remaining_tables_views.py`

**Revision ID:** `lending_core_002`
**Depends on:** `lending_core_001`

**Features:**
- Creates 5 new PostgreSQL ENUMs (risk_tolerance, health_factor_level, loop_status, alert_type, alert_severity)
- Creates 4 new tables with proper indexes and constraints
- Creates 2 database views for aggregated queries
- Full upgrade/downgrade support
- Idempotent ENUM creation using DO $$ blocks

**Key Design Decisions:**
- All foreign keys reference `chat_users(id)` with CASCADE delete
- Proper indexing for common query patterns (user_id, status, timestamps)
- PostgreSQL-specific features (ARRAY, JSONB, partial indexes)
- Numeric precision: Decimal(78,18) for token amounts, Decimal(10,2) for health factors

### 2. Domain Entities (4 Entities)

#### 2.1 UserLendingPreferences

**File:** `src/app/domain/entities/lending/user_lending_preferences.py`

**Attributes:**
- `risk_tolerance`: 'conservative' | 'moderate' | 'aggressive'
- `min_health_factor`: Minimum acceptable HF (default: 1.5)
- `max_leverage`: Maximum leverage multiplier (default: 3.0)
- `preferred_protocol`: 'aave' | 'morpho' | NULL
- `auto_rebalance`: Enable automatic rebalancing
- `notification_health_threshold`: HF threshold for alerts (default: 1.3)
- `notification_email`: Email for notifications
- `notification_enabled`: Enable/disable notifications

**Business Logic:**
- Validates risk_tolerance enum values
- Validates min_health_factor range (1.0-10.0)
- Validates max_leverage range (1.0-10.0)
- Helper properties: `is_conservative`, `is_moderate`, `is_aggressive`, `should_notify_health_issues`

#### 2.2 LendingHealthCheck

**File:** `src/app/domain/entities/lending/lending_health_check.py`

**Attributes:**
- `health_factor`: Current HF value
- `health_factor_level`: 'safe' | 'caution' | 'danger' | 'critical' | 'liquidatable'
- `total_collateral_usd`: Total collateral value
- `total_debt_usd`: Total debt value
- `available_to_borrow_usd`: Remaining borrowing capacity
- `liquidation_price`: Estimated liquidation price

**Business Logic:**
- Validates health_factor_level enum values
- Validates non-negative collateral and debt values
- Computed properties: `is_safe`, `is_at_risk`, `requires_immediate_action`, `ltv_ratio`, `collateralization_ratio`

#### 2.3 LeverageLoopExecution

**File:** `src/app/domain/entities/lending/leverage_loop_execution.py`

**Attributes:**
- `initial_amount`: Starting collateral amount
- `target_leverage`: Target leverage multiplier
- `actual_leverage`: Achieved leverage
- `total_steps`: Total steps required
- `current_step`: Current step (0-indexed)
- `steps_completed`: Array of completed transaction hashes
- `status`: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled'
- `final_health_factor`: Final HF after completion
- `total_gas_used`: Total gas consumed
- `total_cost_usd`: Total execution cost

**Business Logic:**
- Validates status enum values
- Validates step counts and ranges
- Validates target_leverage >= 1.0
- Computed properties: `is_pending`, `is_in_progress`, `is_completed`, `is_failed`, `is_cancelled`, `is_terminal`, `progress_percentage`, `steps_remaining`, `leverage_efficiency`

#### 2.4 LendingAlert

**File:** `src/app/domain/entities/lending/lending_alert.py`

**Attributes:**
- `alert_type`: 'health_factor_low' | 'liquidation_risk' | 'position_closed' | 'loop_completed' | 'loop_failed' | 'rate_change'
- `severity`: 'info' | 'warning' | 'critical'
- `title`: Alert title
- `message`: Alert message
- `health_factor`: Current HF (if applicable)
- `threshold_value`: Threshold that triggered alert
- `current_value`: Current value that crossed threshold
- `is_read`: Read status
- `sent_at`: Timestamp when sent

**Business Logic:**
- Validates alert_type and severity enum values
- Validates non-empty title and message
- Computed properties: `is_info`, `is_warning`, `is_critical`, `is_unread`, `was_sent`, `is_health_related`, `is_position_related`, `is_loop_related`

### 3. SQLAlchemy Mappings (4 Mappings)

All mappings follow imperative mapping pattern (metadata-only, no domain entity coupling):

1. **user_lending_preferences_mapping.py** - Maps `user_lending_preferences` table
2. **lending_health_check_mapping.py** - Maps `lending_health_checks` table
3. **leverage_loop_execution_mapping.py** - Maps `leverage_loop_executions` table
4. **lending_alert_mapping.py** - Maps `lending_alerts` table

**Key Features:**
- Idempotent mapping registration
- Proper PostgreSQL ENUM references (create_type=False)
- All indexes defined in __table_args__
- Default values and server defaults properly set

### 4. Repository Implementation

**Updated Files:**
- `src/app/domain/ports/lending_repository.py` (Interface)
- `src/app/infrastructure/persistence_sqla/repositories/lending_repository.py` (Implementation)

**New Methods Added (12 methods):**

#### User Preferences (2 methods)
- `save_user_preferences(preferences)` - Upsert user preferences (ON CONFLICT user_id)
- `get_user_preferences(user_id)` - Get user preferences

#### Health Checks (2 methods)
- `save_health_check(check)` - Save health check snapshot
- `get_recent_health_checks(user_id, protocol, limit)` - Get recent checks

#### Leverage Loop Executions (4 methods)
- `save_loop_execution(execution)` - Create loop execution
- `get_loop_execution(loop_id)` - Get by ID
- `update_loop_execution(execution)` - Update progress/status
- `get_user_loop_executions(user_id, status, limit)` - Get user's loops

#### Alerts (4 methods)
- `create_alert(alert)` - Create new alert
- `get_unread_alerts(user_id, severity)` - Get unread alerts
- `mark_alert_as_read(alert_id)` - Mark alert as read
- `get_user_alerts(user_id, include_read, limit)` - Get all alerts

**Implementation Pattern:**
- All methods use raw SQL via SQLAlchemy Core (not ORM)
- Proper transaction management (commit/rollback)
- Custom `RepositoryError` exception for all failures
- Decimal conversions for numeric precision
- Optional parameter handling with SQL `(:param IS NULL OR ...)`

### 5. Registry Updates

**Updated:** `src/app/infrastructure/persistence_sqla/mappings/all.py`

**Changes:**
- Added 4 new mapping imports
- Registered 4 new mapping functions in `map_tables()`
- Maintains initialization order for proper dependencies

**Updated:** `src/app/domain/entities/lending/__init__.py`

**Changes:**
- Added 4 new entity exports
- Updated `__all__` list

---

## Database Schema Details

### Table: user_lending_preferences

**Purpose:** Store user-specific risk preferences and notification settings

**Key Columns:**
- `user_id` - UNIQUE constraint (one preference per user)
- `risk_tolerance` - ENUM with CHECK constraint
- `min_health_factor` - Default 1.5, CHECK (1.0-10.0)
- `max_leverage` - Default 3.0, CHECK (1.0-10.0)
- `preferred_protocol` - VARCHAR(20), nullable
- `notification_health_threshold` - Default 1.3

**Indexes:**
- `idx_user_lending_preferences_user_id` on (user_id)

### Table: lending_health_checks

**Purpose:** Track health factor checks over time for monitoring

**Key Columns:**
- `user_id` - Foreign key to chat_users
- `protocol` - VARCHAR(20)
- `chain` - VARCHAR(50)
- `health_factor` - Numeric(10,2)
- `health_factor_level` - ENUM ('safe', 'caution', 'danger', 'critical', 'liquidatable')
- `total_collateral_usd` - Numeric(18,2)
- `total_debt_usd` - Numeric(18,2)

**Indexes:**
- `idx_lending_health_checks_user_id` on (user_id)
- `idx_lending_health_checks_checked_at` on (checked_at)
- `idx_lending_health_checks_health_level` on (health_factor_level)
- `idx_lending_health_checks_user_protocol` on (user_id, protocol)

### Table: leverage_loop_executions

**Purpose:** Track leverage loop executions with multi-step state management

**Key Columns:**
- `user_id` - Foreign key to chat_users
- `protocol` - VARCHAR(20)
- `asset_address` - VARCHAR(42)
- `asset_symbol` - VARCHAR(10)
- `initial_amount` - Numeric(78,18)
- `target_leverage` - Numeric(3,1)
- `actual_leverage` - Numeric(3,1), nullable
- `total_steps` - INTEGER
- `current_step` - INTEGER, default 0
- `steps_completed` - TEXT[], default '{}'
- `status` - ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
- `metadata` - JSONB

**Indexes:**
- `idx_leverage_loop_user_id` on (user_id)
- `idx_leverage_loop_status` on (status)
- `idx_leverage_loop_created_at` on (created_at)
- `idx_leverage_loop_user_status` on (user_id, status)

### Table: lending_alerts

**Purpose:** Store alerts for liquidation risk, HF drops, and position changes

**Key Columns:**
- `user_id` - Foreign key to chat_users
- `position_id` - Foreign key to lending_positions (nullable)
- `alert_type` - ENUM (6 types)
- `severity` - ENUM ('info', 'warning', 'critical')
- `title` - VARCHAR(255)
- `message` - TEXT
- `health_factor` - Numeric(10,2), nullable
- `is_read` - BOOLEAN, default false
- `metadata` - JSONB

**Indexes:**
- `idx_lending_alerts_user_id` on (user_id)
- `idx_lending_alerts_is_read` on (is_read)
- `idx_lending_alerts_severity` on (severity)
- `idx_lending_alerts_created_at` on (created_at)
- `idx_lending_alerts_user_unread` on (user_id, is_read) WHERE is_read = false (partial index)

### View: user_lending_summary

**Purpose:** Aggregated view of user's complete lending positions

**Columns:**
- `user_id`, `email`
- `total_positions`, `supply_positions`, `borrow_positions`
- `protocols_used`
- `total_supplied_usd`, `total_borrowed_usd`
- `min_health_factor`
- `avg_supply_apy`, `avg_borrow_apy`
- `unread_critical_alerts`
- `last_activity_at`

**Use Cases:**
- Dashboard summary display
- Quick health overview
- Risk assessment

### View: protocol_comparison

**Purpose:** Real-time comparison view across protocols

**Columns:**
- `protocol`, `chain`, `asset_symbol`, `position_type`
- `unique_users`, `total_positions`
- `total_tvl_usd`
- `avg_apy`, `min_apy`, `max_apy`
- `avg_health_factor`
- `active_positions`, `liquidated_positions`
- `last_updated`

**Use Cases:**
- Protocol selection
- Yield optimization
- Market analysis

---

## Architecture Compliance

### Hexagonal Architecture Principles

✅ **Domain Layer Independence:**
- Entities have NO infrastructure dependencies
- All business logic in domain entities
- Proper value object pattern (frozen dataclasses)
- Domain invariants validated in `__post_init__`

✅ **Port-Adapter Pattern:**
- `ILendingRepository` defines domain port (interface)
- `SQLAlchemyLendingRepository` implements adapter
- Repository uses raw SQL (not ORM) for CQRS pattern

✅ **Dependency Inversion:**
- Domain defines interfaces (ports)
- Infrastructure implements interfaces (adapters)
- Application layer depends on domain ports only

✅ **Separation of Concerns:**
- Domain entities: Pure business logic
- Mappings: Database metadata only (no domain coupling)
- Repository: Data access implementation
- Transactions: Handled in repository layer

### CQRS Pattern

✅ **Command-Query Separation:**
- Write operations: `save_*`, `create_*`, `update_*`
- Read operations: `get_*` (returns domain entities)
- Views: Optimized for read queries

✅ **Performance Optimization:**
- Raw SQL queries for performance
- Proper indexing for common queries
- Partial indexes for filtered queries
- Database views for aggregations

---

## Testing Strategy

### Unit Tests (Domain Layer)

Test each entity's business logic:

```python
# Test: UserLendingPreferences validation
def test_user_preferences_validates_risk_tolerance():
    with pytest.raises(ValueError, match="Invalid risk_tolerance"):
        UserLendingPreferences(
            risk_tolerance="invalid",
            # ... other fields
        )

def test_user_preferences_validates_min_health_factor():
    with pytest.raises(ValueError, match="Invalid min_health_factor"):
        UserLendingPreferences(
            min_health_factor=Decimal("0.5"),  # Below 1.0
            # ... other fields
        )

# Test: LendingHealthCheck computed properties
def test_health_check_is_at_risk():
    check = LendingHealthCheck(
        health_factor_level="danger",
        # ... other fields
    )
    assert check.is_at_risk is True
    assert check.requires_immediate_action is False

# Test: LeverageLoopExecution state transitions
def test_loop_execution_progress_percentage():
    execution = LeverageLoopExecution(
        total_steps=4,
        current_step=2,
        # ... other fields
    )
    assert execution.progress_percentage == Decimal("50")

# Test: LendingAlert classification
def test_alert_is_health_related():
    alert = LendingAlert(
        alert_type="health_factor_low",
        # ... other fields
    )
    assert alert.is_health_related is True
    assert alert.is_loop_related is False
```

### Integration Tests (Repository Layer)

Test repository operations against test database:

```python
# Test: User preferences upsert
async def test_save_user_preferences_upsert(lending_repo, test_user_id):
    prefs_v1 = create_preferences(user_id=test_user_id, risk_tolerance="conservative")
    await lending_repo.save_user_preferences(prefs_v1)

    prefs_v2 = create_preferences(user_id=test_user_id, risk_tolerance="aggressive")
    await lending_repo.save_user_preferences(prefs_v2)

    result = await lending_repo.get_user_preferences(test_user_id)
    assert result.risk_tolerance == "aggressive"  # Updated, not duplicate

# Test: Health checks with protocol filter
async def test_get_recent_health_checks_filtered(lending_repo, test_user_id):
    await lending_repo.save_health_check(create_check(user_id=test_user_id, protocol="aave"))
    await lending_repo.save_health_check(create_check(user_id=test_user_id, protocol="morpho"))

    aave_checks = await lending_repo.get_recent_health_checks(test_user_id, protocol="aave")
    assert len(aave_checks) == 1
    assert aave_checks[0].protocol == "aave"

# Test: Loop execution state updates
async def test_update_loop_execution_progress(lending_repo, test_loop_id):
    loop = await lending_repo.get_loop_execution(test_loop_id)

    updated_loop = dataclasses.replace(
        loop,
        current_step=loop.current_step + 1,
        status="in_progress",
        updated_at=datetime.now(timezone.utc)
    )

    await lending_repo.update_loop_execution(updated_loop)

    result = await lending_repo.get_loop_execution(test_loop_id)
    assert result.current_step == loop.current_step + 1
    assert result.status == "in_progress"

# Test: Unread alerts filtering
async def test_get_unread_alerts_filtered(lending_repo, test_user_id):
    await lending_repo.create_alert(create_alert(user_id=test_user_id, severity="info", is_read=False))
    await lending_repo.create_alert(create_alert(user_id=test_user_id, severity="critical", is_read=False))
    await lending_repo.create_alert(create_alert(user_id=test_user_id, severity="critical", is_read=True))

    critical_unread = await lending_repo.get_unread_alerts(test_user_id, severity="critical")
    assert len(critical_unread) == 1
    assert critical_unread[0].severity == "critical"
    assert critical_unread[0].is_read is False
```

### E2E Tests (Views)

Test database views:

```python
async def test_user_lending_summary_view(db_session, test_user_id):
    # Create positions
    await create_lending_position(user_id=test_user_id, position_type="supply", amount_usd=1000)
    await create_lending_position(user_id=test_user_id, position_type="borrow", amount_usd=500, health_factor=1.8)

    # Query view
    result = await db_session.execute(
        "SELECT * FROM user_lending_summary WHERE user_id = :user_id",
        {"user_id": test_user_id}
    )
    row = result.fetchone()

    assert row.total_positions == 2
    assert row.supply_positions == 1
    assert row.borrow_positions == 1
    assert row.total_supplied_usd == 1000
    assert row.total_borrowed_usd == 500
    assert row.min_health_factor == 1.8

async def test_protocol_comparison_view(db_session):
    # Create positions across protocols
    await create_positions_for_comparison()

    result = await db_session.execute(
        "SELECT * FROM protocol_comparison WHERE protocol = 'aave' AND asset_symbol = 'ETH'"
    )
    row = result.fetchone()

    assert row.total_tvl_usd > 0
    assert row.avg_apy is not None
    assert row.active_positions > 0
```

---

## Migration Execution

### Apply Migration

```bash
# Check current revision
alembic current

# Show pending migrations
alembic history --verbose

# Apply migration
alembic upgrade lending_core_002

# Verify migration
alembic current
# Expected: lending_core_002 (head)
```

### Verify Tables

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'user_lending%'
  OR table_name LIKE 'lending_%'
  OR table_name LIKE 'leverage_%';

-- Check ENUMs created
SELECT t.typname, e.enumlabel
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typname LIKE '%enum'
ORDER BY t.typname, e.enumsortorder;

-- Check views exist
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_schema = 'public'
  AND (table_name = 'user_lending_summary' OR table_name = 'protocol_comparison');

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('user_lending_preferences', 'lending_health_checks',
                    'leverage_loop_executions', 'lending_alerts')
ORDER BY tablename, indexname;
```

### Rollback (if needed)

```bash
# Rollback to previous revision
alembic downgrade lending_core_001

# This will:
# - Drop all 4 tables
# - Drop both views
# - Drop all 5 ENUMs
```

---

## Usage Examples

### 1. Save User Preferences

```python
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.entities.lending import UserLendingPreferences
from app.infrastructure.persistence_sqla.repositories.lending_repository import (
    SQLAlchemyLendingRepository
)

# Create preferences
preferences = UserLendingPreferences(
    id=uuid4(),
    user_id=user_id,
    risk_tolerance="moderate",
    min_health_factor=Decimal("1.5"),
    max_leverage=Decimal("3.0"),
    preferred_protocol="aave",
    auto_rebalance=False,
    notification_health_threshold=Decimal("1.3"),
    notification_email="user@example.com",
    notification_enabled=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

# Save (upserts on user_id conflict)
await lending_repo.save_user_preferences(preferences)

# Retrieve
user_prefs = await lending_repo.get_user_preferences(user_id)
if user_prefs and user_prefs.should_notify_health_issues:
    print(f"Notify at HF: {user_prefs.notification_health_threshold}")
```

### 2. Record Health Check

```python
from app.domain.entities.lending import LendingHealthCheck

# Create health check snapshot
check = LendingHealthCheck(
    id=uuid4(),
    user_id=user_id,
    protocol="aave",
    chain="ethereum",
    health_factor=Decimal("1.42"),
    health_factor_level="caution",
    total_collateral_usd=Decimal("5000.00"),
    total_debt_usd=Decimal("3500.00"),
    available_to_borrow_usd=Decimal("500.00"),
    liquidation_price=Decimal("2800.50"),
    checked_at=datetime.now(timezone.utc),
)

# Save check
await lending_repo.save_health_check(check)

# Get recent checks
recent_checks = await lending_repo.get_recent_health_checks(
    user_id=user_id,
    protocol="aave",
    limit=10
)

for check in recent_checks:
    if check.is_at_risk:
        print(f"⚠️ Risk detected: HF={check.health_factor} ({check.health_factor_level})")
```

### 3. Track Leverage Loop Execution

```python
from app.domain.entities.lending import LeverageLoopExecution

# Create loop execution
execution = LeverageLoopExecution(
    id=uuid4(),
    user_id=user_id,
    protocol="morpho",
    chain="ethereum",
    asset_address="0x...",
    asset_symbol="ETH",
    initial_amount=Decimal("1.0"),
    target_leverage=Decimal("3.0"),
    actual_leverage=None,
    total_steps=3,
    current_step=0,
    steps_completed=[],
    status="pending",
    final_health_factor=None,
    final_collateral_usd=None,
    final_debt_usd=None,
    total_gas_used=None,
    total_cost_usd=None,
    error_message=None,
    metadata={"initiated_by": "user_request"},
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
    completed_at=None,
)

# Save initial state
await lending_repo.save_loop_execution(execution)

# Update progress after each step
for step in range(1, execution.total_steps + 1):
    # Execute step...
    tx_hash = await execute_loop_step(step)

    # Update execution state
    execution = await lending_repo.get_loop_execution(execution.id)
    updated = dataclasses.replace(
        execution,
        current_step=step,
        steps_completed=execution.steps_completed + [tx_hash],
        status="in_progress" if step < execution.total_steps else "completed",
        updated_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc) if step == execution.total_steps else None,
    )
    await lending_repo.update_loop_execution(updated)

    print(f"Progress: {updated.progress_percentage}% ({updated.steps_remaining} steps remaining)")
```

### 4. Create and Manage Alerts

```python
from app.domain.entities.lending import LendingAlert

# Create critical health factor alert
alert = LendingAlert(
    id=uuid4(),
    user_id=user_id,
    position_id=position_id,
    alert_type="health_factor_low",
    severity="critical",
    title="Health Factor Critical",
    message="Your health factor has dropped to 1.15. Add collateral or repay debt to avoid liquidation.",
    health_factor=Decimal("1.15"),
    threshold_value=Decimal("1.30"),
    current_value=Decimal("1.15"),
    is_read=False,
    sent_at=None,
    metadata={"trigger": "health_check_monitor"},
    created_at=datetime.now(timezone.utc),
)

# Save alert
await lending_repo.create_alert(alert)

# Get unread critical alerts
critical_alerts = await lending_repo.get_unread_alerts(
    user_id=user_id,
    severity="critical"
)

for alert in critical_alerts:
    print(f"🚨 {alert.title}: {alert.message}")
    if alert.is_health_related:
        print(f"   Current HF: {alert.current_value}, Threshold: {alert.threshold_value}")

    # Mark as read after user views
    await lending_repo.mark_alert_as_read(alert.id)
```

### 5. Query Aggregated Views

```python
# Get user lending summary
result = await db_session.execute(
    "SELECT * FROM user_lending_summary WHERE user_id = :user_id",
    {"user_id": user_id}
)
summary = result.fetchone()

print(f"Total Positions: {summary.total_positions}")
print(f"Supplied: ${summary.total_supplied_usd:.2f}")
print(f"Borrowed: ${summary.total_borrowed_usd:.2f}")
print(f"Min HF: {summary.min_health_factor}")
print(f"Unread Critical Alerts: {summary.unread_critical_alerts}")

# Compare protocols
result = await db_session.execute(
    """
    SELECT protocol, asset_symbol, avg_apy, total_tvl_usd, active_positions
    FROM protocol_comparison
    WHERE asset_symbol = :asset
    ORDER BY avg_apy DESC
    """,
    {"asset": "ETH"}
)

print("\nProtocol Comparison for ETH:")
for row in result:
    print(f"{row.protocol}: APY={row.avg_apy}%, TVL=${row.total_tvl_usd}, Positions={row.active_positions}")
```

---

## Next Steps (Week 4 Continued)

### Days 27-28: Testing

1. **Unit Tests:**
   - Test all domain entity validations
   - Test computed properties and business logic
   - Target: 90% domain coverage

2. **Integration Tests:**
   - Test all repository methods
   - Test transaction handling (commit/rollback)
   - Test concurrent operations
   - Target: 70% repository coverage

3. **E2E Tests:**
   - Test database views
   - Test complex queries with joins
   - Test performance with large datasets

### Week 5: Advanced Features

1. **Leverage Loop Implementation** (Days 22-24)
   - Multi-step state machine
   - Redis state persistence
   - Health factor monitoring per step

2. **Alert System** (Day 26)
   - Celery background job for monitoring
   - Email/push notification integration
   - Alert aggregation and deduplication

3. **Health Factor Monitoring** (Day 27)
   - Scheduled health checks
   - Price oracle integration
   - Automatic alert creation

---

## Performance Considerations

### Index Strategy

1. **Single Column Indexes:**
   - High selectivity columns (user_id, status)
   - Timestamp columns for sorting (created_at, checked_at)

2. **Composite Indexes:**
   - Common filter combinations (user_id + protocol, user_id + status)
   - Support for ORDER BY clauses

3. **Partial Indexes:**
   - Filtered queries (unread alerts WHERE is_read = false)
   - Active records (WHERE status = 'active')

### Query Optimization

1. **Use Database Views:**
   - Pre-aggregated data in `user_lending_summary`
   - Protocol comparison calculations in `protocol_comparison`

2. **Proper JOIN Strategy:**
   - LEFT JOIN for optional relationships (position_id in alerts)
   - Filter predicates before joins when possible

3. **Pagination:**
   - All list queries have LIMIT clause
   - Consider OFFSET for large result sets
   - Use cursor-based pagination for real-time data

### Monitoring

1. **Slow Query Log:**
   - Monitor queries > 100ms
   - Analyze EXPLAIN plans for optimization

2. **Index Usage:**
   - Track index hit rates
   - Identify unused indexes

3. **Connection Pooling:**
   - Reuse database connections
   - Set appropriate pool size

---

## Success Criteria

✅ **All 4 tables created** with proper constraints and indexes
✅ **Both views created** with correct aggregation logic
✅ **All 4 domain entities** with business logic and validation
✅ **All 4 SQLAlchemy mappings** registered and functional
✅ **12 new repository methods** implemented with proper error handling
✅ **Migration runs successfully** (upgrade/downgrade)
✅ **Alembic head** points to lending_core_002
✅ **No breaking changes** to existing lending_core_001 tables

---

## Conclusion

Week 4 (Days 25-27) implementation is **COMPLETE**. All remaining database tables, views, domain entities, mappings, and repository methods have been successfully implemented following hexagonal architecture principles and CQRS patterns.

The lending system now has complete database infrastructure for:
- User preferences and risk management
- Health factor monitoring and historical tracking
- Leverage loop multi-step execution tracking
- Alert system for user notifications
- Aggregated views for dashboard and analytics

**Next Phase:** Proceed to Week 4 Days 27-28 for comprehensive testing, followed by Week 5 for advanced feature implementation (leverage loops, alert system, health monitoring).

---

**Document Version:** 1.0
**Last Updated:** 2026-01-27
**Migration Revision:** lending_core_002
**Status:** ✅ READY FOR TESTING

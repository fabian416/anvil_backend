# Lending Celery Background Tasks

**Created**: 2026-01-28  
**Status**: ✅ Implementation Complete  
**Location**: `src/app/application/lending/tasks.py` + `src/app/infrastructure/celery/tasks.py`

---

## Overview

Celery background tasks for lending operations provide periodic monitoring, health checks, and alert generation for lending positions across Aave and Morpho protocols.

---

## Tasks Implemented

### 1. Monitor Health Factors (`monitor_lending_health_factors`)

**Purpose**: Periodically monitor all active lending positions and check health factors.

**Schedule**: Every 15 minutes (`crontab(minute="*/15")`)

**Operations**:
- Fetches all active positions from Aave and Morpho protocols
- Calculates current health factors for each position
- Saves health check snapshots to `lending_health_checks` table
- Generates alerts for critical positions (HF < 1.5)

**Implementation**:
- **Application Task**: `MonitorHealthFactorsTask` in `src/app/application/lending/tasks.py`
- **Celery Wrapper**: `monitor_lending_health_factors` in `src/app/infrastructure/celery/tasks.py`

**Returns**:
```python
{
    "positions_checked": int,
    "alerts_created": int,
    "critical_positions": int,
}
```

---

### 2. Check User Health Factor (`check_user_lending_health`)

**Purpose**: Check health factor for a specific user position (on-demand or critical monitoring).

**Schedule**: On-demand (can be triggered manually or by other tasks)

**Operations**:
- Fetches user's current position from protocol
- Calculates health factor
- Saves health check snapshot
- Creates alerts if health factor is critical (< 1.5)

**Parameters**:
- `user_id` (str): User UUID as string
- `protocol` (str): Protocol name ("aave" or "morpho")
- `chain` (str): Blockchain network (default: "ethereum")

**Implementation**:
- **Application Task**: `CheckUserHealthFactorTask` in `src/app/application/lending/tasks.py`
- **Celery Wrapper**: `check_user_lending_health` in `src/app/infrastructure/celery/tasks.py`

**Returns**: `LendingHealthCheck` entity

**Alert Creation**:
- **Critical** (HF < 1.2): Creates "liquidation_risk" or "health_factor_low" alert with severity "critical"
- **Warning** (HF 1.2-1.5): Creates "health_factor_low" alert with severity "warning"

---

### 3. Refresh Positions (`refresh_lending_positions`)

**Purpose**: Refresh lending positions from protocols to keep database in sync with on-chain state.

**Schedule**: Every hour at :30 (`crontab(minute=30)`)

**Operations**:
- Fetches latest position data from Aave and Morpho
- Updates positions in database
- Triggers health checks if needed

**Implementation**:
- **Application Task**: `RefreshPositionsTask` in `src/app/application/lending/tasks.py`
- **Celery Wrapper**: `refresh_lending_positions` in `src/app/infrastructure/celery/tasks.py`

**Returns**:
```python
{
    "positions_refreshed": int,
    "errors": int,
}
```

---

## Celery Beat Schedule

All tasks are registered in `celery_app.conf.beat_schedule`:

```python
# Lending health factor monitoring
"monitor-lending-health-factors": {
    "task": "monitor_lending_health_factors",
    "schedule": crontab(minute="*/15"),  # Every 15 minutes
},
# Lending position refresh
"refresh-lending-positions": {
    "task": "refresh_lending_positions",
    "schedule": crontab(minute=30),  # Every hour at :30
},
```

---

## Architecture

### Application Layer Tasks

Located in `src/app/application/lending/tasks.py`:

1. **MonitorHealthFactorsTask**: Orchestrates periodic health monitoring
2. **CheckUserHealthFactorTask**: Handles individual user health checks
3. **RefreshPositionsTask**: Manages position data synchronization

### Infrastructure Layer Wrappers

Located in `src/app/infrastructure/celery/tasks.py`:

- Celery task wrappers that use Dishka dependency injection
- Follow the same pattern as existing tasks (`cleanup_expired_sessions`, etc.)

### Dependencies (Protocols)

Tasks use Protocol-based interfaces for dependency injection:

- **LendingRepository**: Port for repository operations
- **PositionProvider**: Port for fetching positions from protocols

**Note**: These protocols need to be registered in the IOC container (`src/app/setup/ioc/`) with concrete implementations.

---

## Health Factor Classification

Health factors are classified into levels:

| Health Factor | Level | Risk | Action |
|--------------|-------|------|--------|
| >= 2.0 | `safe` | Low | None |
| >= 1.5 | `caution` | Moderate | Monitor |
| >= 1.2 | `danger` | High | Add collateral |
| >= 1.0 | `critical` | Critical | Urgent action |
| < 1.0 | `liquidatable` | Liquidatable | Immediate action |

---

## Alert Types

### Health Factor Alerts

- **Type**: `health_factor_low` or `liquidation_risk`
- **Severity**: `warning` (HF 1.2-1.5) or `critical` (HF < 1.2)
- **Trigger**: Health factor drops below threshold

### Alert Fields

- `alert_type`: Type of alert
- `severity`: Alert severity level
- `title`: Alert title (e.g., "🚨 Liquidation Risk Detected")
- `message`: Detailed alert message
- `health_factor`: Current health factor value
- `threshold_value`: Threshold that triggered alert
- `current_value`: Current value that crossed threshold
- `metadata`: Additional context (protocol, chain, collateral, debt)

---

## Next Steps

### 1. Implement Repository Ports

Create concrete implementations for:
- `LendingRepository` protocol
- `PositionProvider` protocol

**Location**: `src/app/infrastructure/adapters/lending/`

### 2. Register in IOC Container

Add providers in `src/app/setup/ioc/lending.py`:

```python
class LendingProvider(Provider):
    @provide
    def get_lending_repository(self, adapter: LendingRepositorySqla) -> LendingRepository:
        return adapter
    
    @provide
    def get_position_provider(self, adapter: PositionProviderAdapter) -> PositionProvider:
        return adapter
```

### 3. Implement Active User Query

Add method to repository to get users with active lending positions:

```python
async def get_users_with_active_positions(self) -> list[UUID]:
    """Get list of user IDs with active lending positions."""
    ...
```

### 4. Test Tasks

Create integration tests for:
- Health factor monitoring
- Alert generation
- Position refresh

**Location**: `tests/integration/lending/test_celery_tasks.py`

---

## Usage Examples

### Manual Task Execution

```python
# Check health for specific user
from app.infrastructure.celery.tasks import check_user_lending_health

check_user_lending_health.delay(
    user_id="123e4567-e89b-12d3-a456-426614174000",
    protocol="aave",
    chain="ethereum",
)
```

### Monitoring Task Execution

```python
# Monitor all positions (runs automatically every 15 minutes)
from app.infrastructure.celery.tasks import monitor_lending_health_factors

monitor_lending_health_factors.delay()
```

---

## References

- **Architecture**: [docs/ceo/agents/lending/architecture.md](./architecture.md)
- **Implementation Plan**: [docs/ceo/agents/lending/implementation_plan.md](./implementation_plan.md)
- **Database Schema**: [docs/ceo/agents/lending/database_schema.md](./database_schema.md)
- **Celery Tasks Pattern**: [src/app/infrastructure/celery/tasks.py](../../../../src/app/infrastructure/celery/tasks.py)
- **Maintenance Tasks**: [src/app/application/maintenance/tasks.py](../../../../src/app/application/maintenance/tasks.py)

---

## Related Documentation

- **Health Factor Monitoring**: See `WEEK4_IMPLEMENTATION_SUMMARY.md` for health check implementation
- **Alert System**: See `WEEK4_CODE_REVIEW.md` for alert table schema
- **Risk Analysis**: See `risk_analysis.md` for risk thresholds and monitoring strategies

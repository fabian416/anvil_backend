# Week 4 Context Flow Validation - Leverage Loop Multi-Step Workflows

**Date:** 2026-01-27
**Author:** Context Manager Agent
**Methodology:** @cto.md Systematic Validation (MIT Systems Thinking + First Principles Analysis)
**Status:** Validation Complete - Implementation Gaps Identified

---

## Executive Summary

This document validates the context flow for Week 4 leverage loop implementation, focusing on multi-step workflow context persistence, user preferences integration, health check monitoring, and remaining database tables.

### Validation Results Summary

| Component | Status | Issues Found | Severity |
|-----------|--------|--------------|----------|
| Leverage Loop Context Flow | **NOT IMPLEMENTED** | No LeverageLoopInteractor exists | **P0** |
| Multi-Step State Persistence | **NOT IMPLEMENTED** | No `leverage_loop_executions` table | **P0** |
| Context Invalidation Handling | **PARTIAL** | HF validation exists, but per-step not implemented | **P0** |
| User Preferences Integration | **NOT IMPLEMENTED** | No `user_lending_preferences` table | **P1** |
| Health Check Context | **PARTIAL** | Query handler exists, no history table | **P1** |
| Alert Context Management | **NOT IMPLEMENTED** | No `lending_alerts` table | **P1** |
| Caching Strategy | **DEFINED** | Need implementation for loop state | **P1** |
| Security Validation | **PARTIAL** | Single-step security exists | **P1** |
| Performance Targets | **ESTIMATED** | Need benchmarking | **P2** |
| Observability | **PARTIAL** | Basic logging exists, needs enhancement | **P2** |

---

## 1. Leverage Loop Context Flow Diagram

### 1.1 Target Context Flow (TO-BE)

```
User Request: "Loop ETH for 3x leverage"
         |
         v
+------------------------------------------------------------------+
|  PRESENTATION LAYER (conversations_router.py)                     |
+------------------------------------------------------------------+
|  Context Extraction:                                             |
|  - user_id: UUID from JWT claims                                 |
|  - wallet_address: from UserContextAware                         |
|  - language: from Accept-Language header                         |
|  - conversation_id: from URL params                              |
+------------------------------+-----------------------------------+
                               |
                               v
+------------------------------------------------------------------+
|  APPLICATION LAYER (LeverageLoopInteractor) - NOT YET IMPLEMENTED |
+------------------------------------------------------------------+
|  Initial Context Required:                                       |
|  - user_id: UUID (from JWT)                                      |
|  - wallet_address: str (for balance check)                       |
|  - asset: str (ETH, WETH, wstETH)                                |
|  - initial_balance: Decimal (from IBalanceChecker, NEVER cached) |
|  - target_leverage: Decimal (2.0-4.0)                            |
|  - current_positions: list[Position] (for HF calculation)        |
|  - current_debt: Decimal (for HF calculation)                    |
|  - min_health_factor: Decimal (from user preferences or 1.5)     |
|                                                                  |
|  Step Calculation:                                               |
|  1. Fetch current position via AaveGateway                       |
|  2. Calculate required steps for target leverage                 |
|  3. Validate initial HF is safe                                  |
|  4. Generate step plan with per-step HF projections              |
|  5. Save LeverageLoopExecution to database (status=pending)      |
+------------------------------+-----------------------------------+
                               |
                               v
+------------------------------------------------------------------+
|  STEP EXECUTION LOOP (Per User Approval)                         |
+------------------------------------------------------------------+
|  Per-Step Context:                                               |
|  - loop_id: UUID (to retrieve state from DB)                     |
|  - current_step: int (which step in the loop, 0-indexed)         |
|  - steps_completed: list[str] (transaction hashes)               |
|  - current_collateral: Decimal (accumulated, from fresh fetch)   |
|  - current_debt: Decimal (accumulated, from fresh fetch)         |
|  - current_hf: Decimal (recalculated per step, NEVER cached)     |
|  - gas_estimate: Decimal (for next step, 30s cache OK)           |
|                                                                  |
|  Step Types:                                                     |
|  - SUPPLY: Deposit collateral to Aave                            |
|  - BORROW: Borrow against collateral                             |
|  - SWAP: Convert borrowed to collateral asset                    |
+------------------------------------------------------------------+
                               |
     +-------------------------+-------------------------+
     |                         |                         |
     v                         v                         v
+---------------+    +------------------+    +------------------+
| Step 1: SUPPLY|    | Step 2: BORROW   |    | Step 3: SWAP     |
| User Approval |    | User Approval    |    | User Approval    |
+-------+-------+    +--------+---------+    +--------+---------+
        |                     |                       |
        v                     v                       v
+------------------------------------------------------------------+
|  POST-STEP VALIDATION                                            |
+------------------------------------------------------------------+
|  After Each Step:                                                |
|  1. Wait for transaction confirmation                            |
|  2. Refresh position data from chain (NO CACHE)                  |
|  3. Recalculate health factor                                    |
|  4. Save lending_health_check record                             |
|  5. Update LeverageLoopExecution state in DB                     |
|  6. Check if HF still safe for next step                         |
|  7. If HF < threshold: BLOCK next step, show error               |
|  8. If all steps complete: Finalize loop                         |
+------------------------------------------------------------------+
```

### 1.2 Validation Status: NOT IMPLEMENTED

**Current State:**
- `LeverageLoopInteractor` does not exist in the codebase
- No `leverage_loop_executions` database table
- No multi-step state persistence mechanism
- Single-step supply/borrow interactors exist as foundation

**Gap Analysis:**

| Required Component | Status | Location |
|--------------------|--------|----------|
| LeverageLoopInteractor | **MISSING** | `src/app/application/lending/interactors/leverage_loop_interactor.py` |
| LeverageLoopCommand | **MISSING** | `src/app/application/lending/commands/leverage_loop_command.py` |
| LeverageLoopExecution entity | **MISSING** | `src/app/domain/entities/lending/leverage_loop_execution.py` |
| leverage_loop_executions table | **MISSING** | Needs Alembic migration |
| Multi-step state machine | **MISSING** | Needs Redis or DB persistence |

---

## 2. Multi-Step Context Persistence

### 2.1 Expected Context Flow

```
Step 1: User requests "3x leverage on ETH"
  |
  v
LeverageLoopInteractor.initiate()
  |
  +-- Fetch current positions (AaveGateway)
  +-- Calculate all steps needed
  +-- Validate initial HF >= 1.5
  +-- Save LeverageLoopExecution(status=pending, current_step=0)
  +-- Generate Step 1 execute_data (supply)
  |
  v
Return step 1 preview to user
  |
  v
User approves in Privy wallet
  |
  v
Transaction confirms on-chain
  |
  v
Frontend calls /execute endpoint with tx_hash
  |
  v
LeverageLoopInteractor.process_step_completion()
  |
  +-- Validate tx_hash matches expected
  +-- Update LeverageLoopExecution(current_step=1, steps_completed=[tx1])
  +-- Refresh position data (NO CACHE)
  +-- Recalculate HF
  +-- Save lending_health_check record
  +-- Check if HF still safe
  |
  v [If HF safe]
Generate Step 2 execute_data (borrow)
  |
  v
User approves step 2...
  |
  v
[Repeat until all steps completed]
```

### 2.2 Validation Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Loop state persisted after each step | **NOT IMPLEMENTED** | No LeverageLoopExecution entity/table |
| Context includes loop_id for state retrieval | **NOT IMPLEMENTED** | No loop_id tracking |
| HF recalculated with fresh data per step | **PARTIAL** | HF validator exists, per-step calls needed |
| Next step blocked if HF unsafe | **PARTIAL** | BorrowInteractor has blocking logic |
| State recovery after interruption | **NOT IMPLEMENTED** | No persistence mechanism |

### 2.3 Required Implementation

```python
# Proposed structure for leverage_loop_executions persistence

@dataclass
class LeverageLoopExecution:
    """
    Domain entity for tracking leverage loop execution state.
    """
    id: UUID
    user_id: UUID
    wallet_address: str
    position_id: UUID

    # Configuration
    asset: str  # ETH, WETH, wstETH
    initial_collateral: Decimal
    target_leverage: Decimal
    max_iterations: int
    min_health_factor: Decimal

    # Progress
    current_iteration: int = 0
    total_iterations: int = 0
    status: str = "pending"  # pending, in_progress, completed, failed, cancelled

    # Step tracking
    steps: list[LeverageLoopStep] = field(default_factory=list)

    # Results
    final_collateral_usd: Decimal | None = None
    final_debt_usd: Decimal | None = None
    final_leverage: Decimal | None = None
    final_health_factor: Decimal | None = None

    # Transaction tracking
    transaction_hashes: list[str] = field(default_factory=list)
    total_gas_cost_usd: Decimal | None = None

    # Error handling
    error_message: str | None = None
    failed_at_iteration: int | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
```

---

## 3. Context Invalidation Scenarios

### 3.1 Scenario 1: Price Drops During Loop

```
User completes step 1 (supply 1 ETH)
  |
  +-- Position: 1 ETH collateral, 0 debt
  +-- HF: Infinity (no debt)
  |
  v
ETH price drops 10% before step 2
  |
  v
User initiates step 2 (borrow 0.7 ETH worth of USDC)
  |
  v
System recalculates:
  +-- Collateral value: $3,330 (was $3,700)
  +-- Projected debt: $2,590
  +-- Projected HF: 1.06 (was 1.18 expected)
  |
  v [HF 1.06 < 1.2 threshold]
BLOCK step 2 with warning:
  "Price movement detected. Your projected Health Factor (1.06)
   is below the safe threshold (1.2). Please add collateral or
   reduce borrow amount to continue."
```

**Validation Status:** PARTIAL
- HF validation exists in BorrowInteractor (blocks at < min_health_factor)
- Need: Per-step recalculation with fresh price data
- Need: Clear error messaging for price movement scenarios

### 3.2 Scenario 2: HF Drops Below Threshold

```
User completes step 2 (borrow)
  |
  +-- Position: 1.7 ETH collateral, $2,500 debt
  +-- HF: 1.6
  |
  v
ETH price crashes 30% during step 2 confirmation
  |
  v
System refreshes position after step 2 confirmation:
  +-- Collateral value: $4,200 (was $6,000)
  +-- Actual debt: $2,500
  +-- Actual HF: 1.14 (was 1.6 projected)
  |
  v [HF 1.14 < 1.2 threshold]
BLOCK step 3 with emergency message:
  "EMERGENCY: Market conditions have changed. Your Health Factor
   dropped to 1.14 (CRITICAL). Loop paused for your safety.

   Options:
   1. Add $500 collateral to continue loop
   2. Cancel loop and keep current position
   3. Repay $400 debt to improve HF"
```

**Validation Status:** NOT IMPLEMENTED
- Need: Post-step HF recalculation
- Need: Loop pause mechanism
- Need: Recovery options presentation

### 3.3 Scenario 3: User Loses Balance

```
User completes step 1 (supply)
  |
  v
User transfers USDC to another wallet
  |
  v
User initiates step 2 (swap requires USDC)
  |
  v
System checks balance:
  +-- Required: $2,500 USDC
  +-- Available: $100 USDC
  |
  v [Insufficient balance]
BLOCK step 2:
  "Insufficient balance for swap. Required: $2,500 USDC,
   Available: $100 USDC. Please deposit more USDC or
   cancel the loop."
```

**Validation Status:** PARTIAL
- Balance check exists in SupplyInteractor
- Need: Pre-step balance validation for each step type
- Need: Clear messaging for balance scenarios

---

## 4. User Preferences Context Integration

### 4.1 Expected Context Flow

```
User initiates leverage loop
  |
  v
System fetches user_lending_preferences (cached 1h)
  |
  +-- If no preferences: Use defaults
  |     - min_health_factor: 1.5
  |     - max_leverage: 3.0
  |     - allow_leverage_loops: false (requires explicit opt-in)
  |
  +-- If preferences exist:
  |     - Apply user's min_health_factor
  |     - Apply user's max_leverage
  |     - Check allow_leverage_loops flag
  |
  v
Validate against user preferences:
  |
  +-- If target_leverage > max_leverage:
  |     BLOCK with warning: "Your max leverage setting is 3.0x.
  |     Please adjust target or update preferences."
  |
  +-- If allow_leverage_loops == false:
  |     BLOCK with warning: "Leverage loops are disabled in your
  |     preferences. Enable in Settings to continue."
  |
  v
Calculate steps with user's safety preferences
  |
  +-- Use user's min_health_factor for all HF checks
  +-- Apply notification thresholds from preferences
```

### 4.2 Validation Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Preferences loaded at start of loop | **NOT IMPLEMENTED** | No preferences table |
| Defaults used if no preferences | **NOT IMPLEMENTED** | Need default values |
| User can override defaults in request | **PLANNED** | Need command parameter |
| Preferences cached appropriately | **NOT IMPLEMENTED** | Need Redis caching |

### 4.3 user_lending_preferences Schema (From database_schema.md)

```sql
CREATE TABLE user_lending_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,

    -- Risk Preferences
    risk_tolerance VARCHAR(20) NOT NULL DEFAULT 'moderate',
    min_health_factor NUMERIC(5, 2) NOT NULL DEFAULT 1.5,

    -- Auto-Management Settings (Future)
    auto_repay_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    auto_repay_threshold NUMERIC(5, 2) NOT NULL DEFAULT 1.2,

    -- Notification Settings
    notify_health_factor_warning BOOLEAN NOT NULL DEFAULT TRUE,
    notify_health_factor_critical BOOLEAN NOT NULL DEFAULT TRUE,

    -- Leverage Settings
    max_leverage NUMERIC(5, 2) NOT NULL DEFAULT 2.0,
    allow_leverage_loops BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Implementation Status:** **NOT IMPLEMENTED**
- Table not created
- Repository not implemented
- Service layer not implemented
- No DI provider configured

---

## 5. Health Check Context Integration

### 5.1 Expected Context Flow

```
After each borrow step in leverage loop:
  |
  v
Calculate new Health Factor
  |
  +-- Fetch fresh position data (AaveGateway)
  +-- Apply HealthFactorValidator.calculate()
  |
  v
Save to lending_health_checks table
  |
  +-- position_id: Current position
  +-- health_factor: New HF value
  +-- total_collateral_usd: Current collateral
  +-- total_debt_usd: Current debt
  +-- risk_level: Derived from HF
  +-- checked_at: NOW()
  |
  v
Check notification thresholds (from user_lending_preferences)
  |
  +-- If HF < notify_health_factor_warning (default 1.5):
  |     Create lending_alert (severity=warning)
  |
  +-- If HF < notify_health_factor_critical (default 1.2):
  |     Create lending_alert (severity=critical)
```

### 5.2 Validation Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Health checks saved after each step | **NOT IMPLEMENTED** | No table/repository |
| Time-series data for monitoring | **NOT IMPLEMENTED** | Schema defined |
| Alerts triggered correctly | **NOT IMPLEMENTED** | No alert system |
| Historical HF tracking | **NOT IMPLEMENTED** | Need implementation |

### 5.3 lending_health_checks Schema (From database_schema.md)

```sql
CREATE TABLE lending_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL REFERENCES lending_positions(id),

    -- Health Metrics
    health_factor NUMERIC(20, 18) NOT NULL,
    total_collateral_usd NUMERIC(20, 6) NOT NULL,
    total_debt_usd NUMERIC(20, 6) NOT NULL,
    liquidation_threshold NUMERIC(5, 4) NOT NULL,

    -- Risk Assessment
    risk_level VARCHAR(20) NOT NULL,
    liquidation_price_usd NUMERIC(20, 6) NULL,
    buffer_percentage NUMERIC(8, 4) NULL,

    -- Action Recommendations
    recommended_action VARCHAR(50) NULL,
    recommended_repay_amount_usd NUMERIC(20, 6) NULL,

    -- Alert Status
    alert_sent BOOLEAN NOT NULL DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE NULL,

    -- Timestamps
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Implementation Status:** **NOT IMPLEMENTED**

---

## 6. Alert Context Management

### 6.1 Alert Creation Scenarios

| Trigger | Alert Type | Severity | Context Needed |
|---------|-----------|----------|----------------|
| HF drops below notification_threshold | `health_factor_warning` | warning | position_id, current_hf, threshold |
| HF drops below 1.2 | `health_factor_critical` | critical | position_id, current_hf, liquidation_price |
| Loop step fails | `loop_step_failed` | warning | loop_id, step_number, error_details |
| Loop completes successfully | `loop_completed` | info | loop_id, final_leverage, final_hf |
| Loop cancelled by user | `loop_cancelled` | info | loop_id, steps_completed, reason |
| Transaction fails | `transaction_failed` | warning | tx_hash, error_code, error_message |

### 6.2 Alert Context Required

```python
@dataclass
class LendingAlertContext:
    """Context for creating lending alerts."""

    # Required
    user_id: UUID
    alert_type: str  # health_factor_low, loop_completed, etc.
    severity: str    # info, warning, critical

    # Conditional (depends on alert_type)
    position_id: UUID | None = None
    loop_id: UUID | None = None

    # Values
    current_value: Decimal | None = None      # e.g., current HF
    threshold_value: Decimal | None = None    # e.g., min acceptable HF

    # Metadata
    metadata: dict | None = None  # loop_id, step_number, error details

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### 6.3 lending_alerts Schema (From database_schema.md)

**Note:** The `lending_alerts` table is referenced in the roadmap but not fully defined in database_schema.md. Proposed schema:

```sql
CREATE TABLE lending_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- Alert Details
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    -- References
    position_id UUID NULL REFERENCES lending_positions(id),
    loop_id UUID NULL REFERENCES leverage_loop_executions(id),
    health_check_id UUID NULL REFERENCES lending_health_checks(id),

    -- Values
    current_value NUMERIC(20, 6) NULL,
    threshold_value NUMERIC(20, 6) NULL,

    -- Metadata
    metadata JSONB NULL,

    -- Status
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    is_dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Implementation Status:** **NOT IMPLEMENTED**

---

## 7. Caching Strategy for Leverage Loops

### 7.1 Context Variable Caching Matrix

| Context Variable | TTL | Reason | Used In | Status |
|------------------|-----|--------|---------|--------|
| **Initial balance** | **NEVER CACHE** | Changes constantly | Step 0 validation | **CORRECT** (IBalanceChecker) |
| **User preferences** | 1h | Rarely changes | Loop calculation | **NOT IMPLEMENTED** |
| **Current HF** | **NEVER CACHE** | Safety critical | Every borrow step | **PARTIAL** (validator exists) |
| **Swap quotes** | 30s | Price volatility | Every swap step | **NOT IMPLEMENTED** |
| **Gas estimates** | 30s | Network congestion | Every step | **PARTIAL** |
| **Loop state** | DB persistence | Multi-step workflow | State recovery | **NOT IMPLEMENTED** |
| **Price data** | 30s | Used for HF calc | Every HF check | **PARTIAL** (mock provider) |
| **Current positions** | **NEVER CACHE** | Changes with txs | Every HF calc | **PARTIAL** |
| **Protocol APY** | 60s | Changes slowly | Step planning | **OK** (MCP caching) |

### 7.2 Cache Key Patterns

```
anvil:lending:loop:{loop_id}                      # Loop state (if Redis-backed)
anvil:lending:preferences:{user_id}               # User preferences (1h TTL)
anvil:lending:positions:{user_id}                 # Positions (30s TTL)
anvil:lending:health:{user_id}:{protocol}         # Health factor (30s TTL)
anvil:market:price:{token}:{chain}                # Token prices (30s TTL)
anvil:market:gas:{chain}                          # Gas estimates (30s TTL)
```

### 7.3 Critical Caching Rules

**NEVER CACHE (Safety Critical):**
- Token balances (changes with every transaction)
- Health factor calculations (must reflect current state)
- Current positions (changes with every transaction)
- Transaction status (must be real-time)

**Validation:** The existing IBalanceChecker does NOT cache, which is correct.

---

## 8. Security Validation for Multi-Step Workflows

### 8.1 Session Hijacking Prevention

| Check | Status | Implementation |
|-------|--------|----------------|
| loop_id tied to user_id | **NOT IMPLEMENTED** | Need DB constraint |
| JWT revalidated per step | **EXISTING** | JWT middleware validates every request |
| No step execution without auth | **EXISTING** | Authenticated routes require JWT |

### 8.2 Race Condition Prevention

| Check | Status | Implementation |
|-------|--------|----------------|
| Optimistic locking on updates | **NOT IMPLEMENTED** | Need version column |
| Check current_step matches expected | **NOT IMPLEMENTED** | Need step validation |
| Reject duplicate step submissions | **NOT IMPLEMENTED** | Need idempotency keys |

**Proposed Implementation:**

```python
# In LeverageLoopExecution entity
class LeverageLoopExecution:
    # ... existing fields ...
    version: int = 0  # Optimistic locking

    def validate_step_progression(self, expected_step: int) -> None:
        """
        Validate step progression is correct.

        Raises:
            StepMismatchError: If expected step doesn't match current
        """
        if self.current_step != expected_step:
            raise StepMismatchError(
                f"Expected step {expected_step}, but current is {self.current_step}"
            )
```

### 8.3 Authorization Validation

| Check | Status | Evidence |
|-------|--------|----------|
| User can only access their own loops | **EXISTING PATTERN** | Repository filters by user_id |
| No cross-user loop execution | **NEED IMPLEMENTATION** | Add explicit check |
| Admin endpoints for debugging | **NOT IMPLEMENTED** | Optional future feature |

---

## 9. Performance Analysis

### 9.1 3x Leverage Loop Performance Targets

**Typical 3x Leverage Loop (9 steps total):**

| Phase | Target Duration | Operations |
|-------|-----------------|------------|
| Initial calculation | <500ms | HF calc + balance check + step generation |
| Per-step backend | <500ms | Load state + recalculate HF + generate execute_data + save state |
| User approval time | ~30s (variable) | User reviews and signs in Privy |
| Transaction confirmation | ~12s (Ethereum) | Block confirmation |
| Total loop time | ~4.5 minutes | 9 steps x ~30s average |

### 9.2 Per-Step Breakdown

```
Load loop state from DB          ~50ms
Refresh position from chain      ~150ms (MCP call)
Recalculate health factor        ~50ms (pure calculation)
Generate execute_data            ~100ms (MCP call for calldata)
Save updated state to DB         ~50ms
-------------------------------------------
Total backend per step:          ~400ms (target: <500ms)
```

### 9.3 Performance Validation

| Target | Estimated | Status |
|--------|-----------|--------|
| Initial calculation <500ms | ~400ms | **ACHIEVABLE** |
| Step execution <500ms | ~400ms | **ACHIEVABLE** |
| State persistence <100ms | ~50ms | **ACHIEVABLE** |
| No unnecessary MCP calls | Need review | **NEED VALIDATION** |

---

## 10. Context Observability

### 10.1 Logging Requirements

**Log each loop lifecycle event:**

```python
# Loop initiation
logger.info(
    "Leverage loop initiated",
    extra={
        "loop_id": str(loop_id),
        "user_id": str(user_id),
        "asset": asset,
        "target_leverage": float(target_leverage),
        "total_steps": total_steps,
        "initial_hf": float(current_hf),
    }
)

# Step started
logger.info(
    "Leverage loop step started",
    extra={
        "loop_id": str(loop_id),
        "step_number": current_step,
        "step_type": step_type,  # supply, borrow, swap
        "expected_hf_after": float(projected_hf),
    }
)

# Step completed
logger.info(
    "Leverage loop step completed",
    extra={
        "loop_id": str(loop_id),
        "step_number": current_step,
        "tx_hash": tx_hash,
        "actual_hf": float(new_hf),
        "gas_used_usd": float(gas_cost),
    }
)

# Step failed
logger.warning(
    "Leverage loop step failed",
    extra={
        "loop_id": str(loop_id),
        "step_number": current_step,
        "error": str(error),
        "retry_available": retry_available,
    }
)

# Loop completed
logger.info(
    "Leverage loop completed",
    extra={
        "loop_id": str(loop_id),
        "final_leverage": float(actual_leverage),
        "final_hf": float(final_hf),
        "total_steps_executed": steps_completed,
        "total_gas_cost_usd": float(total_gas),
        "duration_seconds": duration,
    }
)

# Loop cancelled
logger.info(
    "Leverage loop cancelled",
    extra={
        "loop_id": str(loop_id),
        "reason": cancellation_reason,
        "steps_completed": steps_completed,
        "current_hf": float(current_hf),
    }
)
```

### 10.2 Metrics to Monitor

| Metric | Type | Description |
|--------|------|-------------|
| `lending_loop_initiated_total` | Counter | Total loops initiated |
| `lending_loop_completed_total` | Counter | Successfully completed loops |
| `lending_loop_failed_total` | Counter | Failed loops by error type |
| `lending_loop_cancelled_total` | Counter | User-cancelled loops |
| `lending_loop_step_duration_ms` | Histogram | Per-step execution time |
| `lending_loop_total_duration_s` | Histogram | Total loop completion time |
| `lending_loop_hf_at_completion` | Histogram | Final HF distribution |
| `lending_loop_gas_cost_usd` | Histogram | Total gas cost per loop |

---

## 11. Integration Checklist Results

### Week 4 Components Validation

| Component | Status | Action Required |
|-----------|--------|-----------------|
| LeverageLoopInteractor | **MISSING** | Create interactor with multi-step state |
| LeverageLoopCommand | **MISSING** | Create command dataclass |
| LeverageLoopExecution entity | **MISSING** | Create domain entity |
| leverage_loop_executions table | **MISSING** | Create Alembic migration |
| user_lending_preferences table | **MISSING** | Create Alembic migration |
| lending_health_checks table | **MISSING** | Create Alembic migration |
| lending_alerts table | **MISSING** | Create Alembic migration (schema TBD) |
| Loop state persists correctly | **NOT IMPLEMENTED** | DB persistence required |
| Context includes loop_id | **NOT IMPLEMENTED** | Add to command/context |
| HF recalculated per step | **PARTIAL** | Validator exists, per-step calls needed |
| User preferences applied | **NOT IMPLEMENTED** | Preferences table required |
| Health checks saved | **NOT IMPLEMENTED** | Health checks table required |
| Alerts created when needed | **NOT IMPLEMENTED** | Alerts table required |
| No caching for safety data | **CORRECT** | Balance checker is cache-free |
| Security validated | **PARTIAL** | Single-step security exists |
| Performance targets met | **ESTIMATED** | Need benchmarking |
| Logging comprehensive | **PARTIAL** | Basic logging exists |

---

## 12. Critical Issues Found

### P0 - Must Fix Before Week 4 Completion

| Issue | Location | Impact | Resolution |
|-------|----------|--------|------------|
| LeverageLoopInteractor missing | `application/lending/interactors/` | No leverage loop functionality | Create interactor with state machine |
| leverage_loop_executions table missing | Database | No loop state persistence | Create Alembic migration |
| Per-step HF recalculation not implemented | LeverageLoopInteractor | Safety gap in multi-step | Integrate HF validator per step |
| User cannot cancel loop mid-execution | N/A | No abort mechanism | Add cancellation endpoint |
| Step validation missing | LeverageLoopInteractor | Duplicate step risk | Add step progression validation |

### P1 - Should Fix

| Issue | Location | Impact | Resolution |
|-------|----------|--------|------------|
| user_lending_preferences table missing | Database | No personalization | Create Alembic migration |
| lending_health_checks table missing | Database | No monitoring history | Create Alembic migration |
| lending_alerts table missing | Database | No notification system | Create Alembic migration |
| Mock price provider in production | LendingProvider | Inaccurate HF calculations | Implement real IPriceProvider |
| No optimistic locking on loop state | Database | Race condition risk | Add version column |
| No idempotency for step execution | Interactor | Duplicate execution risk | Add idempotency keys |

### P2 - Nice to Have

| Issue | Location | Impact | Resolution |
|-------|----------|--------|------------|
| Performance benchmarking | E2E tests | Unknown actual latency | Add performance tests |
| Structured logging incomplete | All interactors | Reduced observability | Add extra context to logs |
| Metrics not implemented | Prometheus | No monitoring | Add metric instrumentation |

---

## 13. Recommendations

### Immediate Actions (Week 4)

1. **Create Core Infrastructure**
   ```bash
   # Files to create:
   src/app/domain/entities/lending/leverage_loop_execution.py
   src/app/application/lending/commands/leverage_loop_command.py
   src/app/application/lending/interactors/leverage_loop_interactor.py
   ```

2. **Create Database Tables**
   ```bash
   # Alembic migration for:
   - leverage_loop_executions
   - user_lending_preferences
   - lending_health_checks
   - lending_alerts
   ```

3. **Implement Real Price Provider**
   - Replace MockPriceProvider in LendingProvider
   - Use CoinGecko MCP or portfolio service

4. **Add Per-Step HF Validation**
   - Integrate HealthFactorValidatorService into loop interactor
   - Add post-confirmation HF check
   - Implement loop pause on HF threshold breach

### Architecture Improvements

1. **State Machine Implementation**
   ```python
   class LeverageLoopStateMachine:
       STATES = ['pending', 'in_progress', 'paused', 'completed', 'failed', 'cancelled']
       TRANSITIONS = {
           'pending': ['in_progress', 'cancelled'],
           'in_progress': ['paused', 'completed', 'failed'],
           'paused': ['in_progress', 'cancelled'],
           # ...
       }
   ```

2. **Idempotency Pattern**
   - Add idempotency key to step execution
   - Store in Redis with 24h TTL
   - Reject duplicate requests

3. **Recovery Mechanism**
   - Detect interrupted loops on user login
   - Offer resume or cancel options
   - Track loop state in `conversation_metadata`

### Security Hardening

1. **Add Explicit User Verification**
   ```python
   async def validate_loop_ownership(self, loop_id: UUID, user_id: UUID) -> None:
       loop = await self._repository.get_by_id(loop_id)
       if loop.user_id != user_id:
           logger.warning(
               "SECURITY: User attempted to access another user's loop",
               extra={"requesting_user": str(user_id), "loop_owner": str(loop.user_id)}
           )
           raise UnauthorizedLoopAccessError()
   ```

2. **Add Rate Limiting**
   - Max 3 concurrent loops per user
   - Max 10 loops per hour
   - Max 100 steps per day

---

## 14. Related Documentation

- [WEEK2_CONTEXT_ANALYSIS.md](./WEEK2_CONTEXT_ANALYSIS.md) - Context flow analysis for CQRS
- [WEEK3_CONTEXT_VALIDATION.md](./WEEK3_CONTEXT_VALIDATION.md) - Agent and shortcuts validation
- [database_schema.md](./database_schema.md) - Complete database schema specification
- [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) - Full implementation roadmap
- [USER_APPROVAL_GAP.md](./USER_APPROVAL_GAP.md) - User approval flow analysis

---

## 15. Summary

### Current Implementation State

The Week 4 leverage loop implementation has **significant gaps**:

1. **Multi-step state persistence**: NOT IMPLEMENTED
   - No `leverage_loop_executions` table
   - No state machine for loop lifecycle

2. **Per-step context validation**: PARTIAL
   - Single-step HF validation exists (BorrowInteractor)
   - Per-step validation in loop context not implemented

3. **User preferences**: NOT IMPLEMENTED
   - No `user_lending_preferences` table
   - Hardcoded defaults only

4. **Health monitoring**: PARTIAL
   - Query handler exists
   - No historical tracking (no `lending_health_checks` table)

5. **Alert system**: NOT IMPLEMENTED
   - No `lending_alerts` table
   - No notification triggers

### Foundation Strengths

The existing foundation is solid:
- BorrowInteractor with HF validation pattern
- SupplyInteractor with balance validation
- HealthFactorValidatorService with proper domain/application separation
- IBalanceChecker correctly never caches
- Dishka DI properly configured for lending services
- lending_risk.json knowledge base with multi-language support

### Estimated Effort

| Component | Days | Dependencies |
|-----------|------|--------------|
| LeverageLoopInteractor | 3-4 | None |
| Database migrations (4 tables) | 2 | None |
| Per-step HF validation | 1 | Interactor |
| User preferences integration | 2 | Table migration |
| Health check tracking | 1 | Table migration |
| Alert system | 2 | Table migration |
| Testing | 2-3 | All above |
| **Total** | **13-15 days** | |

---

**Document Status:** Validation Complete - Implementation Gaps Identified
**Next Review:** After Week 4 implementation begins
**Owner:** Backend Engineering Team
**Last Updated:** 2026-01-27

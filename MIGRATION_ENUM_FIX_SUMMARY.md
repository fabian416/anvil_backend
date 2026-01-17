# Alembic Migration ENUM Fix Summary

## Problem
Migration files were using `sa.Enum().create()` which caused PostgreSQL ENUM type duplication errors when `op.create_table()` tried to create the ENUM type again.

## Solution Applied
Fixed all migration files to use the correct pattern:

### Pattern 1: ENUM Creation (in upgrade())
**Before:**
```python
sa.Enum("value1", "value2", name="enumname").create(op.get_bind(), checkfirst=True)
```

**After:**
```python
connection = op.get_bind()
connection.execute(sa.text("CREATE TYPE enumname AS ENUM ('value1', 'value2')"))
```

### Pattern 2: ENUM Usage in Columns
**Before:**
```python
sa.Column("column_name", sa.Enum("value1", "value2", name="enumname"), nullable=False)
```

**After:**
```python
sa.Column("column_name", postgresql.ENUM("value1", "value2", name="enumname", create_type=False), nullable=False)
```

## Fixed Migration Files

### 1. Initial Migration
**File:** `2025_11_26_1138-f122cb03e498_initial_migration.py`
**ENUMs Fixed:**
- `userrole`: ('admin', 'moderator', 'user', 'guest')

### 2. Wallet and Transaction Tables
**File:** `2025_11_27_0200-b2c3d4e5f6g7_add_wallet_and_transaction_tables.py`
**ENUMs Fixed:**
- `walletprovider`: ('privy', 'external')
- `chaintype`: ('arbitrum', 'base', 'hyperliquid')
- `walletstatus`: ('inactive', 'active', 'deleted')

### 3. DeFi Operations Tables
**File:** `2025_11_27_0300-c3d4e5f6g7h8_add_defi_operations_tables.py`
**ENUMs Fixed:**
- `side`: ('long', 'short')
- `positionstatus`: ('open', 'closed', 'liquidated')
- `earnstatus`: ('active', 'withdrawn', 'emergency_exit')
- `frequency`: ('daily', 'weekly', 'biweekly', 'monthly')
- `schedulestatus`: ('active', 'paused', 'completed', 'failed')

### 4. AI Telemetry Tables
**File:** `2025_11_27_0400-d4e5f6g7h8i9_add_ai_telemetry_tables.py`
**ENUMs Fixed:**
- `llmprovider`: ('vertex', 'bedrock', 'openai')
- `llmstatus`: ('success', 'failed', 'rate_limited', 'fallback')
- `agentexecutionstatus`: ('pending', 'running', 'completed', 'failed', 'canceled')
- `agenttaskstatus`: ('pending', 'running', 'completed', 'failed', 'skipped')
- `agenttoolstatus`: ('success', 'failed', 'timeout')
- `ratelimiteventtype`: ('rate_limit', 'quota_exceeded', 'throttle', 'timeout')
- `costalerttype`: ('daily_threshold', 'weekly_threshold', 'monthly_threshold', 'user_spike')
- `feedbacktype`: ('helpful', 'not_helpful', 'incorrect', 'offensive', 'other')
- `modelstatus`: ('inactive', 'active', 'deprecated')

## Migration Files NOT Modified
The following migration was already fixed correctly:
- `2025_11_27_0100-a1b2c3d4e5f6_add_chat_feature_tables.py` (template used for fixes)

## Verification

### No More sa.Enum().create() Patterns
```bash
grep -r "sa\.Enum.*\.create" versions/*.py
# Result: No matches found
```

### All ENUMs Use create_type=False
```bash
grep -c "create_type=False" versions/*.py
# Results:
# - 2025_11_26_1138-f122cb03e498_initial_migration.py: 1
# - 2025_11_27_0200-b2c3d4e5f6g7_add_wallet_and_transaction_tables.py: 4
# - 2025_11_27_0300-c3d4e5f6g7h8_add_defi_operations_tables.py: 7
# - 2025_11_27_0400-d4e5f6g7h8i9_add_ai_telemetry_tables.py: 11
```

### All ENUMs Created with Raw SQL
```bash
grep -c "CREATE TYPE.*AS ENUM" versions/*.py
# Results:
# - 2025_11_26_1138-f122cb03e498_initial_migration.py: 1
# - 2025_11_27_0200-b2c3d4e5f6g7_add_wallet_and_transaction_tables.py: 3
# - 2025_11_27_0300-c3d4e5f6g7h8_add_defi_operations_tables.py: 5
# - 2025_11_27_0400-d4e5f6g7h8i9_add_ai_telemetry_tables.py: 9
```

## Benefits
1. **No ENUM Duplication Errors**: PostgreSQL will not attempt to create ENUM types twice
2. **Proper Type Management**: ENUMs are created once with raw SQL, then referenced with `create_type=False`
3. **Clean Migrations**: All migration files now follow the same consistent pattern
4. **Backward Compatible**: Downgrade functions properly drop ENUMs using `sa.Enum(name="...").drop()`

## Next Steps
Run migrations to verify the fixes work correctly:
```bash
cd anvil_backend
alembic upgrade head
```

If you need to reset and reapply migrations:
```bash
alembic downgrade base
alembic upgrade head
```

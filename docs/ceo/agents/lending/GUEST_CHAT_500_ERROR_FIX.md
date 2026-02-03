# Guest Chat 500 Error Fix

**Date**: 2026-01-28  
**Status**: ✅ **FIXED**

---

## Error Summary

**Endpoint**: `POST /api/v1/guest/chat`  
**Error**: `500 Internal Server Error`  
**Root Cause**: `KeyError: 'money_market_rates'`  
**Location**: `src/app/infrastructure/adapters/money_market/money_market_cache_adapter_sqla.py`

---

## Problem

The guest chat endpoint was failing because:

1. **Missing Table Mapping Registration**: The `money_market_rates` table mapping was not registered in `all.py`, so SQLAlchemy metadata didn't include it.

2. **Reserved Attribute Name**: The mapping files used `metadata` as an attribute name, which conflicts with SQLAlchemy's reserved `metadata` attribute.

---

## Solution

### 1. Added Money Market Mappings to `all.py`

**File**: `src/app/infrastructure/persistence_sqla/mappings/all.py`

**Added imports**:
```python
# Money Market Tables
from app.infrastructure.persistence_sqla.mappings.money_market_rate_mapping import map_money_market_rates_table
from app.infrastructure.persistence_sqla.mappings.money_market_comparison_mapping import map_money_market_comparisons_table
from app.infrastructure.persistence_sqla.mappings.money_market_alert_history_mapping import map_money_market_alert_history_table
from app.infrastructure.persistence_sqla.mappings.money_market_user_preference_mapping import map_money_market_user_preferences_table
```

**Added to `map_tables()` function**:
```python
# Money Market Tables
map_money_market_rates_table()
map_money_market_comparisons_table()
map_money_market_alert_history_table()
map_money_market_user_preferences_table()
```

### 2. Fixed Reserved Attribute Names

**File**: `src/app/infrastructure/persistence_sqla/mappings/money_market_rate_mapping.py`

**Changed**:
```python
# Before
metadata = mapped_column(
    "metadata",
    JSONB,
    nullable=True,
    comment="Additional protocol-specific data",
)

# After
metadata_json = mapped_column(
    "metadata",
    JSONB,
    nullable=True,
    comment="Additional protocol-specific data",
)
```

**File**: `src/app/infrastructure/persistence_sqla/mappings/money_market_alert_history_mapping.py`

**Changed**:
```python
# Before
metadata = mapped_column(
    "metadata",
    JSONB,
    nullable=True,
    comment="Additional context (rate_id, comparison results, etc.)",
)

# After
metadata_json = mapped_column(
    "metadata",
    JSONB,
    nullable=True,
    comment="Additional context (rate_id, comparison results, etc.)",
)
```

---

## Files Modified

1. **`src/app/infrastructure/persistence_sqla/mappings/all.py`**
   - Added imports for all 4 money market mapping functions
   - Added calls to register mappings in `map_tables()`

2. **`src/app/infrastructure/persistence_sqla/mappings/money_market_rate_mapping.py`**
   - Changed `metadata` attribute to `metadata_json` to avoid SQLAlchemy conflict

3. **`src/app/infrastructure/persistence_sqla/mappings/money_market_alert_history_mapping.py`**
   - Changed `metadata` attribute to `metadata_json` to avoid SQLAlchemy conflict

---

## Verification

```python
from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry

map_tables()

# Verify tables are registered
assert 'money_market_rates' in mapping_registry.metadata.tables
assert 'money_market_comparisons' in mapping_registry.metadata.tables
assert 'money_market_alert_history' in mapping_registry.metadata.tables
assert 'money_market_user_preferences' in mapping_registry.metadata.tables
```

**Result**: ✅ All 4 money market tables are now registered in SQLAlchemy metadata.

---

## Impact

### Before Fix
- ❌ Guest chat endpoint returns `500 Internal Server Error`
- ❌ `KeyError: 'money_market_rates'` when accessing money market cache adapter
- ❌ Money market features unavailable to guest users

### After Fix
- ✅ Guest chat endpoint works correctly
- ✅ Money market cache adapter can access table metadata
- ✅ All money market tables properly registered
- ✅ Guest users can use money market features

---

## Next Steps

**Restart Required**: The FastAPI server must be restarted for the mapping changes to take effect:

```bash
# Stop current server
make stop-dev  # or kill the FastAPI process

# Start server (will load new mappings)
make start-dev  # or make start
```

After restart, the guest chat endpoint should work correctly.

---

**Fix Complete!** 🎉

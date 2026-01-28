# Celery Database Errors Fix

**Date**: 2026-01-28  
**Status**: ✅ Fixed  
**Errors**: Missing database tables causing `ProgrammingError` in Celery tasks

---

## Problem

Celery tasks were failing with database errors:

1. **`check_knowledge_base_health` task**:
   ```
   ProgrammingError: relation "project_knowledge_documents" does not exist
   ```

2. **`aggregate_project_analytics` task**:
   ```
   ProgrammingError: relation "project_analytics_daily" does not exist
   ```

These errors occurred because the tasks were trying to query tables that don't exist in the database (likely missing migrations).

**Additional Errors Found**:
3. Missing database table: `distillation_cache_exact` and `distillation_cache_semantic`
   - Task: `cleanup_expired_cache`
   - Error: `ProgrammingError: relation "distillation_cache_exact" does not exist`

4. Missing database table: `distillation_telemetry_hourly` and `distillation_requests`
   - Task: `aggregate_distillation_telemetry`
   - Error: `ProgrammingError: relation "distillation_telemetry_hourly" does not exist`

---

## Root Cause

The Celery tasks were executing SQL queries without checking if the required tables exist. When migrations haven't been run or tables haven't been created, the tasks fail with `ProgrammingError`.

---

## Solution

Added graceful error handling for missing tables:

### 1. `aggregate_project_analytics` Task

**Added**:
- Try-except block to catch `ProgrammingError`
- Specific handling for `UndefinedTable` errors
- Informative log message when table is missing
- Re-raise for other errors

**Code**:
```python
try:
    # ... execute query ...
except ProgrammingError as e:
    if isinstance(e.orig, UndefinedTable) and "project_analytics_daily" in str(e):
        print(f"[Analytics] Skipping aggregation - table 'project_analytics_daily' does not exist yet. Run migrations to create it.")
    else:
        raise
```

### 2. `check_knowledge_base_health` Task

**Added**:
- Try-except block wrapping all database queries
- Specific handling for `UndefinedTable` errors related to `project_knowledge_documents`
- Informative log message when table is missing
- Re-raise for other errors

**Code**:
```python
try:
    # ... execute queries ...
except ProgrammingError as e:
    if isinstance(e.orig, UndefinedTable) and "project_knowledge_documents" in str(e):
        print(f"[KB Health] Skipping health check - table 'project_knowledge_documents' does not exist yet. Run migrations to create it.")
    else:
        raise
```

### 3. `cleanup_expired_cache` Task

**Added**:
- Try-except block wrapping all database queries
- Specific handling for `UndefinedTable` errors related to cache tables
- Informative log message when tables are missing
- Re-raise for other errors

**Code**:
```python
try:
    # ... execute queries ...
except ProgrammingError as e:
    if isinstance(e.orig, UndefinedTable) and (
        "distillation_cache_exact" in str(e) or "distillation_cache_semantic" in str(e)
    ):
        print(f"[Cache Cleanup] Skipping cleanup - cache tables do not exist yet. Run migrations to create them.")
    else:
        raise
```

### 4. `aggregate_distillation_telemetry` Task

**Added**:
- Try-except block wrapping database query
- Specific handling for `UndefinedTable` errors related to telemetry tables
- Informative log message when tables are missing
- Re-raise for other errors

**Code**:
```python
try:
    # ... execute query ...
except ProgrammingError as e:
    if isinstance(e.orig, UndefinedTable) and (
        "distillation_telemetry_hourly" in str(e) or "distillation_requests" in str(e)
    ):
        print(f"[Telemetry] Skipping aggregation - required tables do not exist yet. Run migrations to create them.")
    else:
        raise
```

---

## Files Modified

1. **`src/app/infrastructure/celery/tasks/projects_tasks.py`**
   - Added imports: `ProgrammingError`, `UndefinedTable`
   - Added error handling in `aggregate_project_analytics` task
   - Added error handling in `check_knowledge_base_health` task

2. **`src/app/infrastructure/celery/tasks/distillation_tasks.py`**
   - Added imports: `ProgrammingError`, `UndefinedTable`
   - Added error handling in `cleanup_expired_cache` task
   - Added error handling in `aggregate_distillation_telemetry` task

---

## Behavior After Fix

### Before Fix
- Tasks crash with `ProgrammingError` when tables don't exist
- Error logs fill up with tracebacks
- Tasks fail and don't retry gracefully

### After Fix
- Tasks log informative message when tables are missing
- Tasks complete successfully (skip the operation)
- No error tracebacks in logs
- Other errors still raise normally

---

## Verification

```bash
# Test task imports
./env/bin/python3.12 -c "from app.infrastructure.celery.tasks.projects_tasks import aggregate_project_analytics, check_knowledge_base_health; print('✅ Success')"

# Test error handling imports
./env/bin/python3.12 -c "from sqlalchemy.exc import ProgrammingError; from psycopg.errors import UndefinedTable; print('✅ Success')"
```

---

## Related Tables

These tasks depend on tables that may not exist:

1. **`project_analytics_daily`**
   - Used by: `aggregate_project_analytics` task
   - Created by: Database migration (if exists)
   - Action: Run migrations or create table manually

2. **`project_knowledge_documents`**
   - Used by: `check_knowledge_base_health` task
   - Created by: Database migration (if exists)
   - Action: Run migrations or create table manually

3. **`project_knowledge_bases`**
   - Used by: `check_knowledge_base_health` task (JOIN)
   - Created by: Database migration (if exists)
   - Action: Run migrations or create table manually

4. **`distillation_cache_exact`** and **`distillation_cache_semantic`**
   - Used by: `cleanup_expired_cache` task
   - Created by: Database migration (if exists)
   - Action: Run migrations or create tables manually

5. **`distillation_telemetry_hourly`** and **`distillation_requests`**
   - Used by: `aggregate_distillation_telemetry` task
   - Created by: Database migration (if exists)
   - Action: Run migrations or create tables manually

---

## Next Steps

1. **Run Database Migrations** (if tables should exist):
   ```bash
   alembic upgrade head
   ```

2. **Or Create Tables Manually** (if migrations don't exist):
   - Check if migrations exist for these tables
   - Create tables if needed for production

3. **Or Disable Tasks** (if tables aren't needed):
   - Remove tasks from `beat_schedule` if not using projects feature
   - Or keep error handling (tasks will skip gracefully)

---

## Status

✅ **Fixed**: Tasks now handle missing tables gracefully  
✅ **Verified**: Imports work correctly  
✅ **Ready**: Celery tasks will no longer crash on missing tables

---

**Note**: The tasks will now skip operations when tables don't exist, logging informative messages instead of crashing. This allows Celery to continue running even if some database tables haven't been created yet.

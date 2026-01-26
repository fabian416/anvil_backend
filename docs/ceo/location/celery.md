# Location & System Config Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Recommended Implementation  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Location & System Config module currently has **no dedicated Celery tasks**. Data initialization is performed via HTTP endpoints triggered manually.

This document outlines **recommended Celery tasks** for improved data management and automation.

---

## 1. Current State

### No Existing Celery Tasks

The location system currently operates without background tasks:
- **Country/City data initialization** via manual HTTP POST requests
- **No scheduled updates** for geographic data
- **No audit log cleanup** tasks
- **No settings sync** tasks

### Current Data Flow (Manual)
```
Admin POST → Init Handler → CSV Parsing → Database Upsert → Response
                                ↓
                        dump/countries.csv
                        dump/cities.csv
```

---

## 2. Recommended Celery Tasks

### 2.1 Initialize Geographic Data

**Task Name**: `init_geographic_data`  
**Priority**: HIGH  
**Schedule**: On-demand (or weekly for updates)

**Purpose**: Automated initialization of country and city data.

**Recommendation**:
```python
@celery_app.task(name="init_geographic_data")
def init_geographic_data(force_update: bool = False):
    """
    Initialize geographic data from CSV files.
    
    Args:
        force_update: If True, re-process all records even if they exist
    """
    async def runner(container):
        from app.infrastructure.atlas.handlers.init_countries import InitCountriesHandler
        from app.infrastructure.atlas.handlers.init_cities import InitCitiesHandler
        from app.infrastructure.adapters.types import MainAsyncSession
        
        session = await container.get(MainAsyncSession)
        
        # Initialize countries first
        countries_handler = InitCountriesHandler(session=session)
        countries_result = await countries_handler.execute()
        
        print(f"[Geographic Data] Countries: {countries_result}")
        
        # Then initialize cities (depends on countries)
        cities_handler = InitCitiesHandler(session=session)
        cities_result = await cities_handler.execute()
        
        print(f"[Geographic Data] Cities: {cities_result}")
        
        return {
            "countries": countries_result,
            "cities": cities_result,
        }
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule** (Optional - for updates):
```python
"init-geographic-data-weekly": {
    "task": "init_geographic_data",
    "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday at 2 AM
},
```

---

### 2.2 Clean Old Audit Logs

**Task Name**: `clean_old_audit_logs`  
**Priority**: MEDIUM  
**Schedule**: Weekly (Sunday at 3:00 AM)

**Purpose**: Archive and clean old audit logs for compliance.

**Recommendation**:
```python
@celery_app.task(name="clean_old_audit_logs")
def clean_old_audit_logs(retention_days: int = 90):
    """
    Clean audit logs older than retention period.
    
    Compliance considerations:
    - Security-related logs: 7 years
    - Admin actions: 3 years
    - General operations: 90 days
    
    Args:
        retention_days: Default retention for non-critical logs
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, timedelta, UTC
        
        session = await container.get(MainAsyncSession)
        
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        
        # Clean old non-critical audit logs
        query = text("""
            DELETE FROM audit_logs
            WHERE created_at < :cutoff
            AND action NOT IN ('SECURITY_ALERT', 'ADMIN_CONFIG_CHANGE', 'USER_DATA_ACCESS')
        """)
        
        result = await session.execute(query, {"cutoff": cutoff_date})
        deleted_count = result.rowcount
        
        await session.commit()
        
        print(f"[Audit Cleanup] Deleted {deleted_count} old audit log entries")
        return {"deleted_count": deleted_count}
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"clean-old-audit-logs": {
    "task": "clean_old_audit_logs",
    "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday at 3 AM
},
```

---

### 2.3 Sync Settings to Cache

**Task Name**: `sync_settings_to_cache`  
**Priority**: MEDIUM  
**Schedule**: Every 5 minutes

**Purpose**: Sync application settings from database to Redis cache.

**Recommendation**:
```python
@celery_app.task(name="sync_settings_to_cache")
def sync_settings_to_cache():
    """
    Sync settings from database to Redis cache for fast access.
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.cache.redis_client import RedisClient
        import json
        
        session = await container.get(MainAsyncSession)
        redis_client = await container.get(RedisClient)
        
        # Fetch all non-sensitive settings
        query = text("""
            SELECT key, value, scope
            FROM settings
            WHERE is_sensitive = false
        """)
        
        result = await session.execute(query)
        settings = result.fetchall()
        
        # Store in Redis
        settings_dict = {
            row.key: {
                "value": row.value,
                "scope": row.scope,
            }
            for row in settings
        }
        
        redis_client.set(
            "system:settings:cache",
            json.dumps(settings_dict),
            ex=600  # 10 minute TTL
        )
        
        print(f"[Settings Sync] Synced {len(settings)} settings to cache")
        return {"synced_count": len(settings)}
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-settings-to-cache": {
    "task": "sync_settings_to_cache",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
},
```

---

### 2.4 Validate Geographic Data Integrity

**Task Name**: `validate_geographic_data`  
**Priority**: LOW  
**Schedule**: Monthly (1st of month at 4:00 AM)

**Purpose**: Validate consistency between countries and cities tables.

**Recommendation**:
```python
@celery_app.task(name="validate_geographic_data")
def validate_geographic_data():
    """
    Validate geographic data integrity.
    
    Checks:
    - All cities have valid country_id references
    - No duplicate country ISO codes
    - Coordinate ranges are valid
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        
        session = await container.get(MainAsyncSession)
        issues = []
        
        # Check for orphaned cities (no matching country)
        orphan_query = text("""
            SELECT COUNT(*) as count
            FROM cities c
            LEFT JOIN countries co ON c.country_id = co.id
            WHERE co.id IS NULL
        """)
        orphan_count = (await session.execute(orphan_query)).scalar_one()
        if orphan_count > 0:
            issues.append(f"Orphaned cities: {orphan_count}")
        
        # Check for duplicate ISO codes
        dup_iso_query = text("""
            SELECT iso3, COUNT(*) as count
            FROM countries
            GROUP BY iso3
            HAVING COUNT(*) > 1
        """)
        dup_results = (await session.execute(dup_iso_query)).fetchall()
        if dup_results:
            issues.append(f"Duplicate ISO3 codes: {[r.iso3 for r in dup_results]}")
        
        # Check for invalid coordinates
        invalid_coords_query = text("""
            SELECT COUNT(*) as count
            FROM countries
            WHERE latitude IS NOT NULL AND (latitude < -90 OR latitude > 90)
               OR longitude IS NOT NULL AND (longitude < -180 OR longitude > 180)
        """)
        invalid_coords = (await session.execute(invalid_coords_query)).scalar_one()
        if invalid_coords > 0:
            issues.append(f"Invalid coordinates: {invalid_coords}")
        
        print(f"[Data Validation] Issues found: {len(issues)}")
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
        }
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"validate-geographic-data-monthly": {
    "task": "validate_geographic_data",
    "schedule": crontab(hour=4, minute=0, day_of_month=1),  # 1st of month at 4 AM
},
```

---

### 2.5 Export Audit Logs

**Task Name**: `export_audit_logs`  
**Priority**: LOW  
**Schedule**: Monthly (Last day of month at 5:00 AM)

**Purpose**: Export audit logs to archive storage for compliance.

**Recommendation**:
```python
@celery_app.task(name="export_audit_logs")
def export_audit_logs(month: int = None, year: int = None):
    """
    Export audit logs for a specific month to archive storage.
    
    Args:
        month: Month to export (defaults to previous month)
        year: Year to export (defaults to current year)
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, UTC
        import json
        from pathlib import Path
        
        session = await container.get(MainAsyncSession)
        
        # Default to previous month
        now = datetime.now(UTC)
        if month is None:
            month = (now.month - 1) or 12
        if year is None:
            year = now.year if month != 12 else now.year - 1
        
        # Query audit logs for the month
        query = text("""
            SELECT id, actor_user_id, action, entity, entity_id,
                   payload_json, ip_address, user_agent, created_at
            FROM audit_logs
            WHERE EXTRACT(MONTH FROM created_at) = :month
              AND EXTRACT(YEAR FROM created_at) = :year
            ORDER BY created_at
        """)
        
        result = await session.execute(query, {"month": month, "year": year})
        logs = result.fetchall()
        
        if not logs:
            print(f"[Audit Export] No logs found for {year}-{month:02d}")
            return {"exported_count": 0}
        
        # Export to JSON file
        export_dir = Path("archives/audit_logs")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        export_file = export_dir / f"audit_logs_{year}_{month:02d}.json"
        
        logs_data = [
            {
                "id": row.id,
                "actor_user_id": row.actor_user_id,
                "action": row.action,
                "entity": row.entity,
                "entity_id": row.entity_id,
                "payload": row.payload_json,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "created_at": row.created_at.isoformat(),
            }
            for row in logs
        ]
        
        with export_file.open("w") as f:
            json.dump(logs_data, f, indent=2)
        
        print(f"[Audit Export] Exported {len(logs)} logs to {export_file}")
        
        return {
            "exported_count": len(logs),
            "export_file": str(export_file),
        }
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"export-audit-logs-monthly": {
    "task": "export_audit_logs",
    "schedule": crontab(hour=5, minute=0, day_of_month="L"),  # Last day of month
},
```

---

## 3. Complete Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Weekly geographic data refresh (optional)
    "init-geographic-data-weekly": {
        "task": "init_geographic_data",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday at 2 AM
        "kwargs": {"force_update": False},
    },
    
    # Weekly audit log cleanup
    "clean-old-audit-logs": {
        "task": "clean_old_audit_logs",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday at 3 AM
    },
    
    # Settings cache sync every 5 minutes
    "sync-settings-to-cache": {
        "task": "sync_settings_to_cache",
        "schedule": crontab(minute="*/5"),
    },
    
    # Monthly data integrity validation
    "validate-geographic-data-monthly": {
        "task": "validate_geographic_data",
        "schedule": crontab(hour=4, minute=0, day_of_month=1),
    },
    
    # Monthly audit log export
    "export-audit-logs-monthly": {
        "task": "export_audit_logs",
        "schedule": crontab(hour=5, minute=0, day_of_month="L"),
    },
})
```

---

## 4. Task Summary

| Task | Status | Schedule | Description | Priority |
|------|--------|----------|-------------|----------|
| `init_geographic_data` | ❌ Missing | Weekly (optional) | Initialize countries/cities | HIGH |
| `clean_old_audit_logs` | ❌ Missing | Sunday 3 AM | Clean old audit entries | MEDIUM |
| `sync_settings_to_cache` | ❌ Missing | Every 5 min | Sync settings to Redis | MEDIUM |
| `validate_geographic_data` | ❌ Missing | Monthly 1st | Data integrity check | LOW |
| `export_audit_logs` | ❌ Missing | Monthly last | Archive audit logs | LOW |

---

## 5. Implementation Priority

### Phase 1 (High Priority)
1. `init_geographic_data` - Automate data initialization

### Phase 2 (Medium Priority)
2. `clean_old_audit_logs` - Compliance maintenance
3. `sync_settings_to_cache` - Performance optimization

### Phase 3 (Lower Priority)
4. `validate_geographic_data` - Data quality assurance
5. `export_audit_logs` - Compliance archival

---

## References

- **Main Tasks File**: `src/app/infrastructure/celery/tasks.py`
- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Init Countries Handler**: `src/app/infrastructure/atlas/handlers/init_countries.py`
- **Init Cities Handler**: `src/app/infrastructure/atlas/handlers/init_cities.py`
- **System Config Mapping**: `src/app/infrastructure/persistence_sqla/mappings/system_config.py`

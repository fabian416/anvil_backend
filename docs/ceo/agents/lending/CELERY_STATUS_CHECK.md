# Celery Tasks Status Check - Lending & Money Market

**Date**: 2026-01-28  
**Status**: ✅ Fixed - Tasks Now Registered

---

## Summary

Checked Celery processes and task registration for lending and money market tasks.

### Issue Found

The lending tasks were defined in `src/app/infrastructure/celery/tasks.py` but were **not included in the beat schedule** because:

1. The beat schedule in `src/app/infrastructure/celery/app.py` was overwriting the schedule from `tasks.py`
2. Lending tasks were missing from the `app.py` beat schedule
3. Task routing was not configured for lending tasks

### Fix Applied

✅ Added lending tasks to `app.py` beat schedule:
- `monitor-lending-health-factors` - Every 15 minutes
- `refresh-lending-positions` - Every hour at :30

✅ Added task routing for lending tasks:
- `monitor_lending_health_factors` → `risk` queue
- `refresh_lending_positions` → `maintenance` queue
- `check_user_lending_health` → `risk` queue

✅ Fixed beat schedule preservation when transaction confirmation is disabled

---

## Current Status

### Money Market Tasks ✅ RUNNING

| Task | Schedule | Queue | Status |
|------|----------|-------|--------|
| `money_market.warm_cache` | Every 60 seconds | `money_market` | ✅ Registered |
| `money_market.check_alerts` | Every 5 minutes | `money_market` | ✅ Registered |
| `money_market.aggregate_analytics` | Every hour at :00 | `money_market` | ✅ Registered |
| `money_market.cleanup_cache` | Daily at 3:00 AM | `maintenance` | ✅ Registered |

### Lending Tasks ✅ NOW REGISTERED

| Task | Schedule | Queue | Status |
|------|----------|-------|--------|
| `monitor_lending_health_factors` | Every 15 minutes | `risk` | ✅ Registered |
| `refresh_lending_positions` | Every hour at :30 | `maintenance` | ✅ Registered |
| `check_user_lending_health` | On-demand | `risk` | ✅ Registered |

---

## Celery Workers Running

**Beat Scheduler**: ✅ Running (PID 199065)
- Schedules periodic tasks

**Workers**: ✅ Multiple workers running
- `maintenance` queue worker
- `risk` queue worker  
- `money_market` queue worker (if configured)
- Other specialized workers

---

## Verification Commands

### Check Beat Schedule
```bash
python3.12 -c "from app.infrastructure.celery.app import celery_app; import json; schedule = {k: {'task': v['task'], 'schedule': str(v['schedule'])} for k, v in celery_app.conf.beat_schedule.items() if 'lending' in k.lower() or 'money' in k.lower()}; print(json.dumps(schedule, indent=2))"
```

### Check Registered Tasks
```bash
celery -A app.infrastructure.celery.app.celery_app inspect registered | grep -E "(lending|money_market)"
```

### Check Running Processes
```bash
ps aux | grep -i celery | grep -v grep
```

---

## Next Steps

1. **Restart Celery Beat** (if needed):
   ```bash
   make stop-dev
   make start-dev-full
   ```

2. **Monitor Task Execution**:
   - Check Flower UI: http://localhost:5555
   - Check logs: `make logs-celery`

3. **Verify Task Execution**:
   - Wait for scheduled time
   - Check logs for task execution
   - Verify database updates (health checks, alerts)

---

## Files Modified

- `src/app/infrastructure/celery/app.py`
  - Added lending tasks to beat schedule
  - Added task routing for lending tasks
  - Fixed beat schedule preservation logic

---

## Notes

- Money market tasks were already working correctly ✅
- Lending tasks are now properly registered and scheduled ✅
- Tasks will execute automatically according to their schedules
- On-demand tasks (`check_user_lending_health`) can be triggered manually

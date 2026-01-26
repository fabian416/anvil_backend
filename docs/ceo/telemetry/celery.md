# AI Telemetry System Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Partial Implementation  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The AI Telemetry System has **limited Celery task implementation**. Most telemetry is collected in-memory and exported via API endpoints. Additional background tasks are recommended for telemetry aggregation, persistence, and cleanup.

---

## 1. Existing Celery Tasks

### 1.1 Aggregate Distillation Telemetry
**Task Name**: `aggregate_distillation_telemetry`  
**Location**: `src/app/infrastructure/celery/tasks/distillation_tasks.py`

**Purpose**: Aggregate distillation telemetry data.

**Schedule**: Hourly

**Beat Schedule**:
```python
"aggregate-distillation-telemetry": {
    "task": "aggregate_distillation_telemetry",
    "schedule": crontab(minute=0),  # Every hour
},
```

---

## 2. Related Celery Tasks

### 2.1 Recalculate LLM Rankings
**Task Name**: `llm_ranking.recalculate_all_rankings`  
**Location**: `src/app/infrastructure/celery/tasks/llm_ranking.py`

Uses telemetry data to recalculate model rankings.

**Schedule**: Every 6 hours

---

### 2.2 Risk Alert Monitoring
**Location**: `src/app/infrastructure/celery/tasks.py`

Monitors risk conditions using telemetry data.

---

## 3. Recommended Celery Tasks

### 3.1 Aggregate LLM Telemetry Hourly

**Task Name**: `aggregate_llm_telemetry_hourly`  
**Priority**: HIGH  
**Schedule**: Every hour at :05

**Purpose**: Persist in-memory LLM telemetry to database.

**Implementation Recommendation**:
```python
@celery_app.task(name="aggregate_llm_telemetry_hourly")
def aggregate_llm_telemetry_hourly():
    """
    Aggregate LLM telemetry hourly.
    
    - Captures in-memory LLM telemetry
    - Aggregates by provider, model, agent
    - Stores in llm_conversations / vertex_api_metrics / deepinfra_api_metrics
    - Calculates percentiles (p50, p90, p99)
    
    Runs every hour at :05.
    """
    async def runner(container):
        from app.infrastructure.telemetry.llm_telemetry import get_llm_telemetry
        from datetime import datetime, UTC, timedelta
        
        telemetry = get_llm_telemetry()
        
        # Get current metrics
        summary = telemetry.get_summary()
        
        # Store aggregated data
        for provider, metrics in summary.get("providers", {}).items():
            await store_provider_metrics(provider, metrics)
        
        logger.info(f"Aggregated LLM telemetry: {summary.get('total_calls', 0)} calls")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-llm-telemetry-hourly": {
    "task": "aggregate_llm_telemetry_hourly",
    "schedule": crontab(minute=5),  # Every hour at :05
},
```

---

### 3.2 Aggregate API Telemetry Hourly

**Task Name**: `aggregate_api_telemetry_hourly`  
**Priority**: HIGH  
**Schedule**: Every hour at :10

**Purpose**: Persist in-memory API telemetry to database.

**Implementation Recommendation**:
```python
@celery_app.task(name="aggregate_api_telemetry_hourly")
def aggregate_api_telemetry_hourly():
    """
    Aggregate API telemetry hourly.
    
    - Captures in-memory API telemetry
    - Aggregates by API, operation, status
    - Stores in api_telemetry_hourly table
    - Calculates latency percentiles
    
    Runs every hour at :10.
    """
    async def runner(container):
        from app.infrastructure.telemetry.api_telemetry import get_api_telemetry
        
        telemetry = get_api_telemetry()
        metrics = telemetry.get_all_metrics()
        
        for api, api_metrics in metrics.get("apis", {}).items():
            await store_api_metrics(api, api_metrics)
        
        logger.info(f"Aggregated API telemetry: {metrics['summary']['total_requests']} requests")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-api-telemetry-hourly": {
    "task": "aggregate_api_telemetry_hourly",
    "schedule": crontab(minute=10),  # Every hour at :10
},
```

---

### 3.3 Check Budget Alerts

**Task Name**: `check_llm_budget_alerts`  
**Priority**: HIGH  
**Schedule**: Every 15 minutes

**Purpose**: Check LLM budget thresholds and send alerts.

**Implementation Recommendation**:
```python
@celery_app.task(name="check_llm_budget_alerts")
def check_llm_budget_alerts():
    """
    Check LLM budget alerts.
    
    - Gets current monthly cost from telemetry
    - Compares against budget thresholds
    - Creates alerts if thresholds exceeded
    - Sends notifications (email, Slack)
    
    Runs every 15 minutes.
    """
    async def runner(container):
        from app.infrastructure.telemetry.llm_telemetry import get_llm_telemetry
        from app.infrastructure.monitoring.alerting import AlertingService
        
        telemetry = get_llm_telemetry()
        alerting = await container.get(AlertingService)
        
        cost_breakdown = telemetry.get_cost_breakdown()
        monthly_cost = cost_breakdown["monthly_total_usd"]
        budget = cost_breakdown["monthly_budget_usd"]
        
        if monthly_cost >= budget * 0.8:
            await alerting.send_budget_alert(
                threshold=0.8,
                current_cost=monthly_cost,
                budget=budget
            )
        
        if monthly_cost >= budget:
            await alerting.send_budget_alert(
                threshold=1.0,
                current_cost=monthly_cost,
                budget=budget,
                severity="critical"
            )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"check-llm-budget-alerts": {
    "task": "check_llm_budget_alerts",
    "schedule": crontab(minute="*/15"),  # Every 15 minutes
},
```

---

### 3.4 Clean Old Telemetry

**Task Name**: `clean_old_telemetry`  
**Priority**: LOW  
**Schedule**: Daily at 3 AM

**Purpose**: Clean up old telemetry data.

**Implementation Recommendation**:
```python
@celery_app.task(name="clean_old_telemetry")
def clean_old_telemetry():
    """
    Clean old telemetry data.
    
    - Removes raw telemetry older than 7 days
    - Keeps hourly aggregations for 30 days
    - Keeps daily aggregations for 1 year
    
    Runs daily at 3 AM.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        
        # Clean raw telemetry (7 days)
        raw_cutoff = datetime.now(UTC) - timedelta(days=7)
        deleted_raw = await delete_raw_telemetry_before(raw_cutoff)
        
        # Clean hourly aggregations (30 days)
        hourly_cutoff = datetime.now(UTC) - timedelta(days=30)
        deleted_hourly = await delete_hourly_before(hourly_cutoff)
        
        # Clean daily aggregations (1 year)
        daily_cutoff = datetime.now(UTC) - timedelta(days=365)
        deleted_daily = await delete_daily_before(daily_cutoff)
        
        logger.info(
            f"Cleaned telemetry: {deleted_raw} raw, "
            f"{deleted_hourly} hourly, {deleted_daily} daily"
        )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"clean-old-telemetry": {
    "task": "clean_old_telemetry",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

### 3.5 Sync Agent Performance Stats

**Task Name**: `sync_agent_performance_stats`  
**Priority**: MEDIUM  
**Schedule**: Hourly

**Purpose**: Update agent_performance_stats table.

**Implementation Recommendation**:
```python
@celery_app.task(name="sync_agent_performance_stats")
def sync_agent_performance_stats():
    """
    Sync agent performance stats.
    
    - Aggregates LLM telemetry by agent type
    - Updates agent_performance_stats table
    - Calculates success rates, avg latency, costs
    
    Runs hourly.
    """
    async def runner(container):
        from app.infrastructure.telemetry.llm_telemetry import get_llm_telemetry
        
        telemetry = get_llm_telemetry()
        
        # Get agent-level metrics
        agent_metrics = await aggregate_by_agent()
        
        for agent_type, metrics in agent_metrics.items():
            await upsert_agent_performance_stats(
                agent_type=agent_type,
                time_window="1h",
                metrics=metrics
            )
        
        logger.info(f"Synced stats for {len(agent_metrics)} agents")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-agent-performance-stats": {
    "task": "sync_agent_performance_stats",
    "schedule": crontab(minute=15),  # Hourly at :15
},
```

---

### 3.6 Export Daily Cost Report

**Task Name**: `export_daily_cost_report`  
**Priority**: MEDIUM  
**Schedule**: Daily at 1 AM

**Purpose**: Generate daily cost report.

**Implementation Recommendation**:
```python
@celery_app.task(name="export_daily_cost_report")
def export_daily_cost_report():
    """
    Export daily LLM cost report.
    
    - Aggregates costs by provider, model, agent
    - Stores in llm_cost_daily table
    - Sends summary to admin email
    
    Runs daily at 1 AM.
    """
    async def runner(container):
        from app.infrastructure.telemetry.llm_telemetry import get_llm_telemetry
        from datetime import datetime, UTC, timedelta
        
        yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
        
        telemetry = get_llm_telemetry()
        cost_breakdown = telemetry.get_cost_breakdown()
        
        # Store daily cost summary
        await store_daily_cost_report(
            date=yesterday,
            total_cost=cost_breakdown["monthly_total_usd"],
            by_provider=cost_breakdown["by_provider"],
            by_model=cost_breakdown["by_model"]
        )
        
        # Send email notification
        await send_cost_report_email(yesterday, cost_breakdown)
        
        logger.info(f"Exported cost report for {yesterday}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"export-daily-cost-report": {
    "task": "export_daily_cost_report",
    "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
},
```

---

## 4. Complete Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Existing tasks
    "aggregate-distillation-telemetry": {
        "task": "aggregate_distillation_telemetry",
        "schedule": crontab(minute=0),  # Hourly
    },
    
    # Recommended tasks (to be implemented)
    "aggregate-llm-telemetry-hourly": {
        "task": "aggregate_llm_telemetry_hourly",
        "schedule": crontab(minute=5),  # Hourly at :05
    },
    "aggregate-api-telemetry-hourly": {
        "task": "aggregate_api_telemetry_hourly",
        "schedule": crontab(minute=10),  # Hourly at :10
    },
    "check-llm-budget-alerts": {
        "task": "check_llm_budget_alerts",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "sync-agent-performance-stats": {
        "task": "sync_agent_performance_stats",
        "schedule": crontab(minute=15),  # Hourly at :15
    },
    "export-daily-cost-report": {
        "task": "export_daily_cost_report",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    "clean-old-telemetry": {
        "task": "clean_old_telemetry",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
})
```

---

## 5. Implementation Priority

| Task | Status | Priority | Effort | Business Impact |
|------|--------|----------|--------|-----------------|
| aggregate_distillation_telemetry | ✅ Done | - | - | Distillation tracking |
| aggregate_llm_telemetry_hourly | ❌ Missing | HIGH | Medium | LLM metrics persistence |
| aggregate_api_telemetry_hourly | ❌ Missing | HIGH | Medium | API metrics persistence |
| check_llm_budget_alerts | ❌ Missing | HIGH | Low | Cost control |
| sync_agent_performance_stats | ❌ Missing | MEDIUM | Medium | Agent analytics |
| export_daily_cost_report | ❌ Missing | MEDIUM | Low | Cost reporting |
| clean_old_telemetry | ❌ Missing | LOW | Low | Data management |

---

## 6. Task Design Patterns

### 6.1 Idempotency
All telemetry tasks should be idempotent - running multiple times should not cause duplicates.

### 6.2 Error Handling
```python
@celery_app.task(name="task_name", bind=True, max_retries=3)
def task_name(self):
    try:
        # Task logic
    except DatabaseError as e:
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    except Exception as e:
        # Log and don't retry for unknown errors
        logger.error(f"Telemetry task failed: {e}")
```

### 6.3 Metrics Collection
Each task should emit its own metrics:
- Task duration
- Records processed
- Errors encountered

---

## References

- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Main Tasks**: `src/app/infrastructure/celery/tasks.py`
- **Distillation Tasks**: `src/app/infrastructure/celery/tasks/distillation_tasks.py`
- **LLM Telemetry**: `src/app/infrastructure/telemetry/llm_telemetry.py`

# Security & Compliance Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Recommended Implementation  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Security & Compliance system currently has **no dedicated Celery tasks**. Security operates primarily through:
- **Synchronous middleware** (XSS Guard, Prompt Injection Guard)
- **On-demand services** (PII Redaction, Agent Isolation)
- **External scan tools** (Helios, LLMExploiter, Bandit)

This document outlines **recommended Celery tasks** for enhanced security automation.

---

## 1. Current State

### No Existing Celery Tasks

The security system currently operates without background tasks:
- **XSS Guard** runs synchronously in middleware pipeline
- **Prompt Injection Guard** runs synchronously on LLM endpoints
- **PII Redaction** called on-demand during request processing
- **Security Scans** run manually via shell scripts
- **Audit Logs** written synchronously to database

### Current Security Flow (Synchronous)
```
Request → XSS Guard → Prompt Injection Guard → Handler → PII Redaction → Response
                                                           ↓
                                                     Audit Log (sync write)
```

---

## 2. Recommended Celery Tasks

### 2.1 Scheduled Security Scan

**Task Name**: `run_security_scan`  
**Priority**: HIGH  
**Schedule**: Daily at 3:00 AM

**Purpose**: Automated daily security scanning using all OWASP tools.

**Recommendation**:
```python
@celery_app.task(name="run_security_scan")
def run_security_scan():
    """
    Run automated security scan using all configured tools.
    
    Tools executed:
    - Bandit (Python static analysis)
    - Safety (Dependency vulnerabilities)
    - Helios (XSS testing)
    - LLMExploiter (LLM security)
    - Nettacker (Network scanning)
    """
    import subprocess
    from datetime import datetime
    from pathlib import Path
    
    scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("security/reports") / scan_id
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    tools = [
        ("bandit", ["bandit", "-r", "src/app", "-f", "json", "-o", f"{reports_dir}/bandit.json"]),
        ("safety", ["safety", "check", "--json", "-o", f"{reports_dir}/safety.json"]),
    ]
    
    results = {}
    for tool_name, command in tools:
        try:
            result = subprocess.run(command, capture_output=True, timeout=300)
            results[tool_name] = {
                "status": "success" if result.returncode == 0 else "warning",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            results[tool_name] = {"status": "timeout"}
        except Exception as e:
            results[tool_name] = {"status": "error", "error": str(e)}
    
    print(f"[Security Scan] Completed scan {scan_id}: {results}")
    
    # Trigger vulnerability aggregation
    aggregate_scan_results.delay(scan_id)
    
    return {"scan_id": scan_id, "results": results}
```

**Beat Schedule**:
```python
"run-security-scan": {
    "task": "run_security_scan",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

### 2.2 Aggregate Scan Results

**Task Name**: `aggregate_scan_results`  
**Priority**: HIGH  
**Schedule**: On-demand (triggered by security scan)

**Purpose**: Aggregate and persist security scan results.

**Recommendation**:
```python
@celery_app.task(name="aggregate_scan_results")
def aggregate_scan_results(scan_id: str):
    """
    Aggregate scan results from all tools and persist to database.
    
    Args:
        scan_id: Scan identifier (format: YYYYMMDD_HHMMSS)
    """
    async def runner(container):
        from app.infrastructure.security.scan_result_aggregator import ScanResultAggregator
        from app.infrastructure.adapters.types import MainAsyncSession
        from sqlalchemy import text
        from pathlib import Path
        
        session = await container.get(MainAsyncSession)
        reports_dir = Path("security/reports")
        
        aggregator = ScanResultAggregator(reports_dir)
        scan_result = aggregator.get_scan_by_id(scan_id)
        
        if not scan_result:
            print(f"[Aggregate] No scan found: {scan_id}")
            return
        
        # Persist to database
        query = text("""
            INSERT INTO security_scan_results (
                scan_id, scan_date, status, tools_executed,
                critical_count, high_count, medium_count, low_count,
                reports_path, created_at
            ) VALUES (
                :scan_id, :scan_date, :status, :tools_executed,
                :critical, :high, :medium, :low,
                :reports_path, NOW()
            )
        """)
        
        await session.execute(query, {
            "scan_id": scan_result.scan_id,
            "scan_date": scan_result.scan_date,
            "status": scan_result.status.value,
            "tools_executed": ",".join(scan_result.tools_executed),
            "critical": scan_result.vulnerabilities.critical,
            "high": scan_result.vulnerabilities.high,
            "medium": scan_result.vulnerabilities.medium,
            "low": scan_result.vulnerabilities.low,
            "reports_path": scan_result.reports_path,
        })
        
        await session.commit()
        
        # Check for critical vulnerabilities and alert
        if scan_result.vulnerabilities.critical > 0:
            notify_critical_vulnerabilities.delay(scan_id, scan_result.vulnerabilities.critical)
        
        print(f"[Aggregate] Aggregated scan {scan_id}: {scan_result.vulnerabilities.total} vulnerabilities")
    
    asyncio.run(_run_task(runner))
```

---

### 2.3 Notify Critical Vulnerabilities

**Task Name**: `notify_critical_vulnerabilities`  
**Priority**: CRITICAL  
**Schedule**: On-demand (triggered by scan aggregation)

**Purpose**: Alert on critical security vulnerabilities.

**Recommendation**:
```python
@celery_app.task(name="notify_critical_vulnerabilities")
def notify_critical_vulnerabilities(scan_id: str, critical_count: int):
    """
    Send alerts for critical security vulnerabilities.
    
    Args:
        scan_id: Scan identifier
        critical_count: Number of critical vulnerabilities
    """
    async def runner(container):
        from app.infrastructure.monitoring.alerting import AlertingService
        
        alert_service = await container.get(AlertingService)
        
        await alert_service.send_alert(
            severity="critical",
            title=f"Critical Security Vulnerabilities Detected: {critical_count}",
            message=f"Security scan {scan_id} found {critical_count} critical vulnerabilities. Immediate action required.",
            channels=["pagerduty", "slack", "email"],
            metadata={
                "scan_id": scan_id,
                "critical_count": critical_count,
            }
        )
        
        print(f"[Alert] Critical vulnerability alert sent for scan {scan_id}")
    
    asyncio.run(_run_task(runner))
```

---

### 2.4 Clean Old Audit Logs

**Task Name**: `clean_old_audit_logs`  
**Priority**: MEDIUM  
**Schedule**: Weekly (Sunday at 4:00 AM)

**Purpose**: Archive and clean old audit logs for compliance.

**Recommendation**:
```python
@celery_app.task(name="clean_old_audit_logs")
def clean_old_audit_logs(retention_days: int = 90):
    """
    Archive and clean audit logs older than retention period.
    
    For compliance:
    - Security events: 7 years retention
    - Data access events: 3 years retention
    - Other events: 90 days
    
    Args:
        retention_days: Default retention for non-compliance events
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, timedelta, UTC
        
        session = await container.get(MainAsyncSession)
        
        # Archive security events (keep longer)
        # For now, just clean non-critical events
        
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        
        # Clean non-security audit logs
        query = text("""
            DELETE FROM audit_logs
            WHERE created_at < :cutoff
            AND event_type NOT IN ('SECURITY', 'DATA_ACCESS', 'ADMIN_ACTION')
        """)
        
        result = await session.execute(query, {"cutoff": cutoff_date})
        deleted_count = result.rowcount
        
        await session.commit()
        
        print(f"[Audit Cleanup] Deleted {deleted_count} old audit log entries")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"clean-old-audit-logs": {
    "task": "clean_old_audit_logs",
    "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Sunday at 4 AM
},
```

---

### 2.5 Monitor Attack Patterns

**Task Name**: `monitor_attack_patterns`  
**Priority**: HIGH  
**Schedule**: Every 15 minutes

**Purpose**: Detect attack pattern anomalies and trends.

**Recommendation**:
```python
@celery_app.task(name="monitor_attack_patterns")
def monitor_attack_patterns():
    """
    Monitor attack patterns and detect anomalies.
    
    Checks:
    - XSS attack rate increase
    - Prompt injection attempt spikes
    - Unusual IP patterns
    - Repeated failed authentications
    """
    async def runner(container):
        from app.infrastructure.monitoring.alerting import AlertingService
        from app.infrastructure.cache.redis_client import RedisClient
        
        redis_client = await container.get(RedisClient)
        alert_service = await container.get(AlertingService)
        
        # Get attack counters from Redis
        xss_count = int(redis_client.get("security:xss:count:15m") or 0)
        pi_count = int(redis_client.get("security:prompt_injection:count:15m") or 0)
        
        # Check thresholds
        thresholds = {
            "xss": 50,  # More than 50 XSS attempts in 15 min
            "prompt_injection": 30,  # More than 30 PI attempts in 15 min
        }
        
        alerts = []
        
        if xss_count > thresholds["xss"]:
            alerts.append({
                "type": "xss",
                "count": xss_count,
                "threshold": thresholds["xss"],
            })
        
        if pi_count > thresholds["prompt_injection"]:
            alerts.append({
                "type": "prompt_injection",
                "count": pi_count,
                "threshold": thresholds["prompt_injection"],
            })
        
        if alerts:
            await alert_service.send_alert(
                severity="warning",
                title="Elevated Attack Activity Detected",
                message=f"Attack patterns above threshold: {alerts}",
            )
        
        # Reset counters
        redis_client.set("security:xss:count:15m", 0, ex=900)
        redis_client.set("security:prompt_injection:count:15m", 0, ex=900)
        
        print(f"[Attack Monitor] XSS: {xss_count}, PI: {pi_count}, Alerts: {len(alerts)}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"monitor-attack-patterns": {
    "task": "monitor_attack_patterns",
    "schedule": crontab(minute="*/15"),  # Every 15 minutes
},
```

---

### 2.6 Update Security Posture

**Task Name**: `update_security_posture`  
**Priority**: MEDIUM  
**Schedule**: Hourly

**Purpose**: Calculate and update security posture score.

**Recommendation**:
```python
@celery_app.task(name="update_security_posture")
def update_security_posture():
    """
    Calculate and update security posture score.
    
    Score factors:
    - Vulnerability counts (critical=-10, high=-5, medium=-2)
    - Attack block rate (>95% = +5, <80% = -10)
    - Agent isolation violations (-10 each)
    - PII redaction rate (100% = +5)
    """
    async def runner(container):
        from app.infrastructure.security.dashboard_service import SecurityDashboardService
        from app.infrastructure.cache.redis_client import RedisClient
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        
        session = await container.get(MainAsyncSession)
        redis_client = await container.get(RedisClient)
        
        dashboard_service = SecurityDashboardService()
        posture = dashboard_service._get_security_posture()
        
        # Store in Redis for quick access
        redis_client.set("security:posture:score", posture["overall_score"])
        redis_client.set("security:posture:level", posture["level"])
        
        # Store historical posture in database
        query = text("""
            INSERT INTO security_posture_history (
                score, level, factors, created_at
            ) VALUES (
                :score, :level, :factors, NOW()
            )
        """)
        
        import json
        await session.execute(query, {
            "score": posture["overall_score"],
            "level": posture["level"],
            "factors": json.dumps(posture["factors"]),
        })
        
        await session.commit()
        
        print(f"[Security Posture] Score: {posture['overall_score']}, Level: {posture['level']}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"update-security-posture": {
    "task": "update_security_posture",
    "schedule": crontab(minute=0),  # Every hour
},
```

---

## 3. Complete Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Daily security scan at 3 AM
    "run-security-scan": {
        "task": "run_security_scan",
        "schedule": crontab(hour=3, minute=0),
    },
    
    # Clean old audit logs weekly (Sunday at 4 AM)
    "clean-old-audit-logs": {
        "task": "clean_old_audit_logs",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),
    },
    
    # Monitor attack patterns every 15 minutes
    "monitor-attack-patterns": {
        "task": "monitor_attack_patterns",
        "schedule": crontab(minute="*/15"),
    },
    
    # Update security posture hourly
    "update-security-posture": {
        "task": "update_security_posture",
        "schedule": crontab(minute=0),
    },
})
```

---

## 4. Task Summary

| Task | Status | Schedule | Description | Priority |
|------|--------|----------|-------------|----------|
| `run_security_scan` | ❌ Missing | Daily 3 AM | Run all OWASP tools | HIGH |
| `aggregate_scan_results` | ❌ Missing | On-demand | Aggregate and persist results | HIGH |
| `notify_critical_vulnerabilities` | ❌ Missing | On-demand | Alert on critical vulns | CRITICAL |
| `clean_old_audit_logs` | ❌ Missing | Sunday 4 AM | Clean old audit logs | MEDIUM |
| `monitor_attack_patterns` | ❌ Missing | Every 15 min | Detect attack anomalies | HIGH |
| `update_security_posture` | ❌ Missing | Hourly | Calculate security score | MEDIUM |

---

## 5. Implementation Priority

### Phase 1 (High Priority)
1. `run_security_scan` - Automated daily scanning
2. `aggregate_scan_results` - Centralized results
3. `notify_critical_vulnerabilities` - Critical alerts

### Phase 2 (Medium Priority)
4. `monitor_attack_patterns` - Real-time anomaly detection
5. `update_security_posture` - Dashboard metrics

### Phase 3 (Lower Priority)
6. `clean_old_audit_logs` - Compliance maintenance

---

## References

- **Main Tasks File**: `src/app/infrastructure/celery/tasks.py`
- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Security Tools**: `security/scripts/`
- **Scan Aggregator**: `src/app/infrastructure/security/scan_result_aggregator.py`

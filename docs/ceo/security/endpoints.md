# Security & Compliance Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Security & Compliance system provides **admin-only APIs** for:
1. **Security Dashboard** - View scan results, metrics, and security posture
2. **Vulnerability Trends** - Track vulnerabilities over time
3. **Scan Management** - View historical scan results and tool details

**Base Path**: `/api/v1/admin/security`

> **Note**: This is an admin-only module. There are no guest or user endpoints.  
> **Note**: Security middleware (XSS, Prompt Injection) operates transparently on all endpoints.

---

## 1. Security Dashboard Endpoints

### GET /admin/security/dashboard

Get comprehensive security dashboard summary.

**Authentication**: Required (Admin)

**Response** (`SecurityDashboardSummarySchema`):
```json
{
  "latest_scan": {
    "scan_id": "20260125_143000",
    "scan_date": "2026-01-25T14:30:00Z",
    "status": "pass",
    "tools_executed": ["Bandit", "Safety", "Helios", "LLMExploiter"],
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 8,
      "info": 12,
      "total": 27
    },
    "reports_path": "security/reports/20260125_143000",
    "duration_seconds": 324.5,
    "errors": []
  },
  "total_scans": 45,
  "active_tools": ["Bandit", "Safety", "Helios", "LLMExploiter", "Nettacker"],
  "overall_status": "healthy"
}
```

**Overall Status Values**:
| Status | Condition |
|--------|-----------|
| `healthy` | No critical or high vulnerabilities |
| `warning` | High vulnerabilities present |
| `critical` | Critical vulnerabilities present |
| `unknown` | No scans available |

---

### GET /admin/security/scans/latest

Get the most recent security scan results.

**Authentication**: Required (Admin)

**Response** (`SecurityScanResultSchema`):
```json
{
  "scan_id": "20260125_143000",
  "scan_date": "2026-01-25T14:30:00Z",
  "status": "pass",
  "tools_executed": ["Bandit", "Safety", "Helios", "LLMExploiter"],
  "vulnerabilities": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 8,
    "info": 12,
    "total": 27
  },
  "reports_path": "security/reports/20260125_143000",
  "duration_seconds": 324.5,
  "errors": []
}
```

**Error Response** (404):
```json
{
  "detail": "No security scans found"
}
```

---

### GET /admin/security/scans/{scan_id}

Get specific security scan by ID.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `scan_id` | string | Scan identifier (format: YYYYMMDD_HHMMSS) |

**Response** (`SecurityScanResultSchema`): Same as latest scan response.

**Error Response** (404):
```json
{
  "detail": "Scan not found: 20260125_000000"
}
```

---

### GET /admin/security/scans

Get scan history with pagination.

**Authentication**: Required (Admin)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Maximum scans to return (1-100) |

**Response** (`ScanHistorySchema`):
```json
{
  "scans": [
    {
      "scan_id": "20260125_143000",
      "scan_date": "2026-01-25T14:30:00Z",
      "status": "pass",
      "tools_executed": ["Bandit", "Safety"],
      "vulnerabilities": {...},
      "reports_path": "security/reports/20260125_143000"
    },
    {
      "scan_id": "20260124_143000",
      "scan_date": "2026-01-24T14:30:00Z",
      "status": "warning",
      ...
    }
  ],
  "total_scans": 45
}
```

---

### GET /admin/security/scans/{scan_id}/tools

Get individual tool results for a specific scan.

**Authentication**: Required (Admin)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `scan_id` | string | Scan identifier |

**Response** (`ScanToolsSchema`):
```json
{
  "scan_id": "20260125_143000",
  "tools": [
    {
      "tool_name": "Bandit",
      "scan_date": "2026-01-25T14:30:00Z",
      "status": "completed",
      "vulnerabilities_found": 3,
      "report_path": "security/reports/20260125_143000/bandit.json",
      "details": {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 0
      }
    },
    {
      "tool_name": "Helios",
      "scan_date": "2026-01-25T14:31:00Z",
      "status": "completed",
      "vulnerabilities_found": 0,
      "report_path": "security/reports/20260125_143000/helios.json",
      "details": {
        "test_cases_run": 150,
        "xss_patterns_tested": 150
      }
    }
  ]
}
```

---

### GET /admin/security/trends

Get vulnerability trends over time.

**Authentication**: Required (Admin)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Number of days (1-90) |

**Response** (`VulnerabilityTrendsSchema`):
```json
{
  "dates": ["2026-01-25", "2026-01-24", "2026-01-23"],
  "critical": [0, 0, 1],
  "high": [2, 3, 2],
  "medium": [5, 4, 6],
  "low": [8, 7, 9]
}
```

---

### GET /admin/security/health

Security system health check.

**Authentication**: Required (Admin)

**Response**:
```json
{
  "status": "healthy",
  "reports_directory_exists": true,
  "latest_scan_id": "20260125_143000",
  "latest_scan_date": "2026-01-25T14:30:00Z"
}
```

**Unhealthy Response**:
```json
{
  "status": "unhealthy",
  "error": "Error checking security system health"
}
```

---

## 2. Security Middleware (Transparent)

Security middleware operates on **all endpoints** transparently:

### XSS Guard Middleware

**Applied to**: All HTTP requests  
**Protection**: 150+ XSS attack patterns from Helios

| Attack Type | Detection Pattern | Response |
|-------------|-------------------|----------|
| Script injection | `<script>...</script>` | 400 + XSS_ATTACK_DETECTED |
| Event handlers | `onclick=`, `onerror=` | 400 + XSS_ATTACK_DETECTED |
| JavaScript protocol | `javascript:` | 400 + XSS_ATTACK_DETECTED |
| SVG/iframe injection | `<svg>`, `<iframe>` | 400 + XSS_ATTACK_DETECTED |

**Blocked Response**:
```json
{
  "error": "XSS_ATTACK_DETECTED",
  "message": "Request blocked due to potential XSS attack",
  "details": "Request blocked due to potential XSS attack",
  "security_info": {
    "detected_patterns": 1,
    "protection": "Helios XSS Guard"
  }
}
```

**Security Headers Added**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`

---

### Prompt Injection Guard

**Applied to**: All chat/LLM endpoints  
**Protection**: 219 attack patterns from LLMExploiter (OWASP LLM01)

| Attack Type | Risk Level | Pattern Examples |
|-------------|------------|------------------|
| System override | CRITICAL | "ignore previous instructions" |
| Role manipulation | CRITICAL | "you are now a..." |
| Jailbreak | CRITICAL | "DAN mode", "evil mode" |
| Extraction | HIGH | "reveal system prompt" |
| Delimiter attacks | CRITICAL | "[SYSTEM]", "</system>" |

**Check Prompt Response**:
```json
{
  "is_safe": false,
  "risk_level": "critical",
  "detected_patterns": [
    {
      "type": "injection",
      "pattern": "ignore\\s+(all\\s+)?(previous|prior|above)",
      "severity": "critical"
    }
  ],
  "should_block": true
}
```

---

## 3. Security Tools Integrated

| Tool | Type | Patterns | OWASP Reference |
|------|------|----------|-----------------|
| **Helios** | XSS Testing | 150+ | OWASP Top 10 A03:2021 |
| **LLMExploiter** | LLM Security | 219 | OWASP LLM Top 10 LLM01 |
| **Bandit** | Python Static Analysis | - | OWASP Code Review |
| **Safety** | Dependency Scan | - | OWASP Dependency Check |
| **Nettacker** | Network Scanning | - | OWASP Testing Guide |

---

## 4. API Client Examples

### Get Security Dashboard
```bash
curl -X GET "http://localhost:8000/api/v1/admin/security/dashboard" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Get Latest Scan
```bash
curl -X GET "http://localhost:8000/api/v1/admin/security/scans/latest" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Get Scan History
```bash
curl -X GET "http://localhost:8000/api/v1/admin/security/scans?limit=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Get Tool Results
```bash
curl -X GET "http://localhost:8000/api/v1/admin/security/scans/20260125_143000/tools" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Get Vulnerability Trends
```bash
curl -X GET "http://localhost:8000/api/v1/admin/security/trends?days=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Security Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/admin/security/health" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## References

- **Dashboard Router**: `src/app/presentation/http/controllers/admin/security_dashboard_router.py`
- **Dashboard Schemas**: `src/app/presentation/http/controllers/admin/security_dashboard_schemas.py`
- **Scan Aggregator**: `src/app/infrastructure/security/scan_result_aggregator.py`
- **XSS Guard**: `src/app/infrastructure/security/middleware/xss_guard.py`
- **Prompt Injection Guard**: `src/app/infrastructure/security/middleware/prompt_injection_guard.py`

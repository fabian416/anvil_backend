# Module: Security Dashboard

**Route**: `/admin/overview/security`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/overview/security`

## 1. Overview
Displays the platform's security posture and vulnerability status. Aggregates results from security scanning tools (SAST/DAST), tracks vulnerabilities over time, and provides immediate visibility into critical security issues.

## 2. API Contract

### Get Security Dashboard
**Endpoint**: `GET /api/admin/security/dashboard`  
**Query Params**: None

#### Response Body (`SecurityDashboardResponse`)
| Field | Type | Description |
|---|---|---|
| `timestamp` | `string` | ISO 8601 timestamp of dashboard generation |
| `security_posture` | `SecurityPosture` | Overall security posture assessment |
| `latest_scan` | `LatestScan` | Most recent security scan results |
| `attack_statistics` | `AttackStatistics` | Attack attempt statistics |
| `total_scans` | `number` | Total number of scans performed |
| `active_tools` | `string[]` | List of active security tools |
| `overall_status` | `string` | Overall status: `healthy`, `warning`, `critical`, `unknown` |

**SecurityPosture Object**:
| Field | Type | Description |
|---|---|---|
| `overall_score` | `number` | Security score (0-100) |
| `level` | `string` | Security level: `EXCELLENT`, `GOOD`, `FAIR`, `POOR`, `CRITICAL` |

**LatestScan Object**:
| Field | Type | Description |
|---|---|---|
| `scan_id` | `string` | Unique scan identifier |
| `scan_date` | `string` | ISO 8601 scan date |
| `status` | `string` | Scan status: `completed`, `running`, `failed` |
| `vulnerabilities` | `VulnerabilityCounts` | Vulnerability counts by severity |

**VulnerabilityCounts Object**:
| Field | Type | Description |
|---|---|---|
| `critical` | `number` | Critical vulnerabilities count |
| `high` | `number` | High severity vulnerabilities count |
| `medium` | `number` | Medium severity vulnerabilities count |
| `low` | `number` | Low severity vulnerabilities count |

**AttackStatistics Object**:
| Field | Type | Description |
|---|---|---|
| `xss_attempts` | `AttackStats` | XSS attack statistics |
| `prompt_injections` | `AttackStats` | Prompt injection attack statistics |

**AttackStats Object**:
| Field | Type | Description |
|---|---|---|
| `total` | `number` | Total attack attempts |
| `blocked` | `number` | Successfully blocked attempts |

**JSON Example**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "security_posture": {
    "overall_score": 85,
    "level": "GOOD"
  },
  "latest_scan": {
    "scan_id": "20240115_103000",
    "scan_date": "2024-01-15T10:00:00Z",
    "status": "completed",
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 10
    }
  },
  "attack_statistics": {
    "xss_attempts": {
      "total": 150,
      "blocked": 150
    },
    "prompt_injections": {
      "total": 45,
      "blocked": 45
    }
  },
  "total_scans": 150,
  "active_tools": ["bandit", "semgrep", "safety", "owasp"],
  "overall_status": "warning"
}
```

### Get Latest Scan Details
**Endpoint**: `GET /api/admin/security/scans/latest`  
**Query Params**: None

#### Response Body (`SecurityScanResultResponse`)
| Field | Type | Description |
|---|---|---|
| `scan_id` | `string` | Unique scan identifier |
| `scan_date` | `string` | ISO 8601 scan date |
| `tools_executed` | `string[]` | List of tools that ran |
| `duration_seconds` | `number` | Scan duration in seconds |
| `reports_path` | `string` | Path to scan reports |
| `errors` | `string[]` | List of errors encountered |
| `vulnerabilities` | `VulnerabilityDetail[]` | Detailed vulnerability list |

### Get Vulnerability Trends
**Endpoint**: `GET /api/admin/security/trends`  
**Query Params**:
- `days` (number, optional): Lookback period in days (Default: 30, Max: 90).

#### Response Body (`VulnerabilityTrendsResponse`)
| Field | Type | Description |
|---|---|---|
| `dates` | `string[]` | Array of ISO 8601 dates |
| `critical` | `number[]` | Critical vulnerability counts per date |
| `high` | `number[]` | High severity counts per date |
| `medium` | `number[]` | Medium severity counts per date |
| `low` | `number[]` | Low severity counts per date |

**JSON Example**:
```json
{
  "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
  "critical": [0, 0, 0],
  "high": [2, 1, 2],
  "medium": [5, 5, 4],
  "low": [10, 9, 10]
}
```

### Get Scan History
**Endpoint**: `GET /api/admin/security/scans`  
**Query Params**:
- `limit` (number, optional): Records to return (Default: 10, Max: 100).

#### Response Body (`SecurityScanHistoryResponse`)
| Field | Type | Description |
|---|---|---|
| `scans` | `SecurityScanSummary[]` | List of scan summaries |
| `total` | `number` | Total number of scans |

**SecurityScanSummary Object**:
| Field | Type | Description |
|---|---|---|
| `scan_id` | `string` | Unique scan identifier |
| `scan_date` | `string` | ISO 8601 scan date |
| `status` | `string` | Scan status |
| `vulnerability_count` | `number` | Total vulnerabilities found |
| `critical_count` | `number` | Critical vulnerabilities |

### Get Specific Scan Details
**Endpoint**: `GET /api/admin/security/scans/{scan_id}`  
**Path Params**:
- `scan_id` (string, **required**): Scan identifier.

#### Response Body (`SecurityScanDetailResponse`)
| Field | Type | Description |
|---|---|---|
| `scan_id` | `string` | Unique scan identifier |
| `scan_date` | `string` | ISO 8601 scan date |
| `status` | `string` | Scan status |
| `tools_executed` | `string[]` | List of tools executed |
| `duration_seconds` | `number` | Scan duration |
| `vulnerabilities` | `VulnerabilityDetail[]` | Detailed vulnerability list |
| `reports_path` | `string` | Path to reports |

### Get System Health Check
**Endpoint**: `GET /api/admin/security/health`  
**Query Params**: None

#### Response Body (`SecurityHealthResponse`)
| Field | Type | Description |
|---|---|---|
| `status` | `string` | Health status: `healthy`, `degraded`, `unhealthy` |
| `reports_directory_exists` | `boolean` | Whether reports directory exists |
| `latest_scan_date` | `string \| null` | ISO 8601 date of latest scan or null |
| `active_tools_count` | `number` | Number of active security tools |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Scan not found | Show error: "Scan not found" |
| `500` | `Exception` | Internal server error | Show error: "Failed to load security dashboard" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useSecurityDashboard()` hook which fetches `/api/admin/security/dashboard`.
2. **Display**:
   - Security posture card: Display `security_posture.overall_score` and `security_posture.level` with color coding (Red for CRITICAL/POOR, Yellow for FAIR, Green for GOOD/EXCELLENT).
   - Latest scan card: Display `latest_scan.vulnerabilities` counts with severity badges.
   - Attack statistics: Display `attack_statistics` with blocked vs total counts.
   - Overall status banner: If `overall_status` is `critical`, show prominent red banner at top of page.
3. **Vulnerability Trends**: Call `GET /api/admin/security/trends?days=30` to display stacked area chart showing vulnerability trends over time.
4. **Scan History**: Call `GET /api/admin/security/scans?limit=10` to display recent scans in a table.
5. **Drill-down**: On scan click, navigate to scan details page or open modal with `GET /api/admin/security/scans/{scan_id}`.
6. **Health Check**: Periodically call `GET /api/admin/security/health` to verify scanning infrastructure is operational.

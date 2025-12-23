# Admin Module: Security Dashboard

> **Technical Specification**: `FRONTEND_ADMIN_DASHBOARD_SECURITY`
> **Backend Controller**: `src/app/presentation/http/controllers/admin/security_dashboard_router.py`
> **Base URL**: `/api/admin/security`

## 📖 Overview
The **Security Dashboard** provides visibility into the platform's security posture. It aggregates results from various security scanning tools (SAST/DAST), tracking vulnerabilities and system health over time.

### Key Capabilities
1.  **Vulnerability Trends**: Visualizing the rise/fall of security issues over time.
2.  **Latest Scan Results**: Immediate view of the most recent security check.
3.  **Tool Performance**: Status of individual security tools (e.g., Bandit, Semgrep).
4.  **Historical Logs**: Access to past scan reports for audit compliance.

---

## 🔌 API Endpoints

### 1. Security Overview
**GET** `/api/admin/security/dashboard`
The primary status endpoint. Returns the latest scan summary and overall health status.

**Response (`SecurityDashboardSummarySchema`)**:
```json
{
  "latest_scan": {
    "scan_id": "20231027_120000",
    "status": "completed",
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 10
    }
  },
  "total_scans": 150,
  "active_tools": ["bandit", "semgrep", "safety"],
  "overall_status": "warning" // healthy, warning, critical, unknown
}
```

### 2. Latest Scan Details
**GET** `/api/admin/security/scans/latest`
Detailed report of the most recent execution.

**Response (`SecurityScanResultSchema`)**:
```json
{
  "scan_id": "20231027_120000",
  "scan_date": "2023-10-27T12:00:00Z",
  "tools_executed": ["bandit", "safety"],
  "duration_seconds": 45,
  "reports_path": "/security/reports/...",
  "errors": []
}
```

### 3. Vulnerability Trends
**GET** `/api/admin/security/trends`
Time-series data for charting.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `days` | `int` | No | Lookback period (Default: 30, Max: 90). |

**Response (`VulnerabilityTrendsSchema`)**:
```json
{
  "dates": ["2023-10-01", "2023-10-02", ...],
  "critical": [0, 0, ...],
  "high": [2, 1, ...],
  "medium": [5, 5, ...]
}
```

### 4. Scan History
**GET** `/api/admin/security/scans`
Paginated list of past scans.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `limit` | `int` | No | Records to return (Default: 10). |

### 5. Specific Scan & Tool Details
**GET** `/api/admin/security/scans/{scan_id}`
**GET** `/api/admin/security/scans/{scan_id}/tools`
Drill down into a specific historical record or individual tool output.

### 6. System Health Check
**GET** `/api/admin/security/health`
Verifies if the scanning infrastructure is operational.

**Response**:
```json
{
  "status": "healthy",
  "reports_directory_exists": true,
  "latest_scan_date": "2023-10-27T12:00:00Z"
}
```

---

## 🎨 UI/UX Guidelines

### Critical States
- **Color Coding**: 
    - **Critical (Red)**: Requires immediate attention. Block deployments if possible.
    - **High (Orange)**: Urgent fix required.
    - **Medium (Yellow)**: Warning.
    - **Low/Info (Blue/Grey)**: Informational.
- **Overall Status**: The "Overall Status" badge should be the most prominent element on the page.

### Charts
- **Trend Line**: Stacked Area Chart showing vulnerabilities over time. Ideally, this graph should trend downwards (resolving issues).
- **Tool Status**: Simple "Traffic Light" indicators for each tool (Green = Ran successfully, Red = Failed to run).

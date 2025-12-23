# Admin Module: Chat Dashboard & Analytics

> **Technical Specification**: `FRONTEND_ADMIN_DASHBOARD_CHAT`
> **Backend Controller**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`
> **Base URL**: `/chat/dashboard`

## 📖 Overview
The **Chat Dashboard** provides a "Mission Control" view for the platform's AI interactions. It allows admins to monitor real-time usage, track agent performance, analyze costs, and detect system anomalies.

### Key Capabilities
1.  **High-Level Summary**: 30-day lookback on users, messages, and costs.
2.  **Agent Leaderboard**: Performance ranking by invocations, success rate, or cost.
3.  **Cost Tracking**: Granular breakdown of token usage and API spend.
4.  **Error Monitoring**: Analysis of failure rates and error types.
5.  **Export**: Data extraction for offline analysis (CSV/JSON).

---

## 🔌 API Endpoints

### 1. Dashboard Summary
**GET** `/chat/dashboard`
Get the high-level KPIs for the dashboard header.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `date_from` | `datetime` | No | Start of period (Default: -30d). |
| `date_to` | `datetime` | No | End of period (Default: Now). |

**Response (`AdminChatDashboardSummaryResponse`)**:
```json
{
  "total_conversations": 1250,
  "total_messages": 8900,
  "active_users_monthly": 450,
  "total_cost_usd": 125.50,
  "error_rate_percent": 0.5,
  "avg_response_time_ms": 1200
}
```

### 2. Agent Performance Leaderboard
**GET** `/chat/dashboard/agents/performance`
Compare how different agents (e.g., "Risk Analyst", "DeFi Sniper") are performing.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `sort_by` | `str` | No | `invocations`, `success_rate`, `avg_response_time`, `total_cost`. |
| `limit` | `int` | No | Top N agents (Default: 10). |

**Response (`AgentPerformanceResponse`)**:
```json
{
  "leaderboard": [
    {
      "agent_id": "defi-sniper-v1",
      "name": "DeFi Sniper",
      "invocations": 5000,
      "success_rate": 98.5,
      "avg_latency_ms": 800,
      "total_cost": 45.00
    }
  ],
  "trend_summary": "Access to DeFi Sniper increased by 15% this week."
}
```

### 3. Cost Tracking
**GET** `/chat/dashboard/costs`
Detailed financial breakdown.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `group_by` | `str` | No | `agent`, `model`, `day`, `user`. |

**Response (`CostTrackingResponse`)**:
```json
{
  "total_spend": 125.50,
  "breakdown": [
    { "key": "gpt-4-turbo", "cost": 80.00, "percentage": 63.7 },
    { "key": "claude-3-opus", "cost": 45.50, "percentage": 36.3 }
  ],
  "daily_trend": [
    { "date": "2024-03-01", "cost": 4.50 }
  ]
}
```

### 4. System Health & Errors
**GET** `/chat/dashboard/errors`
Monitor for system stability issues.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `severity` | `str` | No | `critical`, `high`, `medium`, `low`. |

**Response (`ErrorMonitoringResponse`)**:
```json
{
  "total_errors": 45,
  "error_rate": 0.005,
  "top_errors": [
    { "type": "RateLimitError", "count": 30, "last_seen": "..." },
    { "type": "ContextWindowExceeded", "count": 15, "last_seen": "..." }
  ]
}
```

### 5. Active Users
**GET** `/chat/dashboard/users/active`
User engagement metrics.

**Response (`ActiveUsersResponse`)**:
```json
{
  "dau": 120,
  "wau": 450,
  "mau": 1100,
  "retention_rate": 0.65,
  "avg_sessions_per_user": 2.5
}
```

### 6. Cache Efficiency
**GET** `/chat/dashboard/cache/efficiency`
Monitor semantic cache performance to optimize costs.

**Response (`CacheEfficiencyResponse`)**:
```json
{
  "hit_rate": 0.45,
  "miss_rate": 0.55,
  "estimated_savings_usd": 50.00,
  "latency_reduction_ms": 450
}
```

### 7. Export Data
**GET** `/chat/dashboard/export`
Download raw data.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `format` | `str` | **Yes** | `json`, `csv`. |
| `include_sections` | `List[str]` | No | `agents`, `costs`, `errors`, `users`. |

---

## 🎨 UI/UX Guidelines

### Data Visualization
- **KPI Cards**: Use "Sparklines" for the Summary endpoint to show the 30-day trend of each metric.
- **Charts**:
    - **Usage**: Line chart for Daily Active Users (DAU) and Message Volume.
    - **Cost**: Stacked Bar Chart grouped by `model` or `agent`.
    - **Performance**: Horizontal Bar Chart for the Agent Leaderboard.

### Interaction
- **Date Picker**: Global control that updates all widgets.
- **Drill-down**: Clicking a specific Agent in the leaderboard should navigate to a detailed Agent view (Future Scope).
- **Auto-Refresh**: Dashboard should poll every 60s or offer a "Refresh" button.

# Admin Module: LLM Telemetry

> **Technical Specification**: `FRONTEND_ADMIN_LLM_TELEMETRY`
> **Backend Controller**: `admin/llm/telemetry.py`
> **Base URL**: `/api/admin/llm/telemetry`

## 📖 Overview
The **LLM Telemetry** submodule enables administrators to monitor and analyze LLM orchestration metrics and analytics. It provides comprehensive insights into request volume, latency, costs, token usage, and performance by provider, model, and agent.

### Key Capabilities
1. **Overview Dashboard**: High-level summary of LLM metrics for a specified period.
2. **Time-Series Analytics**: Time-series data for charts and visualizations.
3. **Cost Analysis**: Comprehensive cost breakdown and projections.

---

## 🔌 API Endpoints

### 1. Get Telemetry Overview
**GET** `/api/admin/llm/telemetry/overview`
High-level telemetry summary.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `period` | `str` | No | Time period: `1h`, `24h`, `7d`, `30d` (default: `24h`). |

**Response (`TelemetryResponse`)**:
```json
{
  "success": true,
  "data": {
    "period": "24h",
    "total_requests": 45231,
    "success_rate": 0.987,
    "avg_latency_ms": 1245,
    "p95_latency_ms": 2500,
    "total_cost_usd": 127.45,
    "total_tokens": {
      "input": 15000000,
      "output": 8500000
    },
    "requests_by_provider": [
      {
        "provider": "vertex_ai",
        "count": 25000,
        "success_rate": 0.99,
        "avg_latency_ms": 1100
      }
    ],
    "requests_by_agent": [
      {
        "agent": "swap_agent",
        "count": 18000,
        "avg_latency_ms": 1050
      }
    ],
    "retry_rate": 0.032,
    "circuit_breakers_open": 0
  }
}
```

### 2. Get Telemetry Time-Series
**GET** `/api/admin/llm/telemetry/timeseries`
Time-series metrics for charts.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `metric` | `str` | No | Metric type: `requests`, `latency`, `cost`, `errors`, `tokens` (default: `requests`). |
| `period` | `str` | No | Time period: `1h`, `24h`, `7d`, `30d` (default: `24h`). |
| `group_by` | `str` | No | Grouping: `provider`, `model`, `agent` (default: `provider`). |
| `interval` | `str` | No | Interval: `auto`, `5m`, `1h`, `1d` (default: `auto`). |

**Response (`TelemetryResponse`)**:
```json
{
  "success": true,
  "data": {
    "metric": "requests",
    "period": "24h",
    "interval": "1h",
    "data": [
      {
        "timestamp": "2025-12-01T00:00:00Z",
        "value": 1500,
        "breakdown": {
          "vertex_ai": 800,
          "deepinfra": 400,
          "bedrock": 300
        }
      }
    ]
  }
}
```

### 3. Get Cost Analysis
**GET** `/api/admin/llm/telemetry/cost`
Cost analysis and projections.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `period` | `str` | No | Time period: `7d`, `30d`, `90d` (default: `30d`). |

**Response (`TelemetryResponse`)**:
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "total_cost_usd": 2847.50,
    "cost_by_provider": [
      {
        "provider": "vertex_ai",
        "cost": 1200.00,
        "percentage": 42.1
      }
    ],
    "cost_by_agent": [
      {
        "agent": "swap_agent",
        "cost": 1100.00,
        "requests": 180000
      }
    ],
    "cost_by_model": [
      {
        "model": "gemini-1.5-pro",
        "cost": 800.00
      }
    ],
    "daily_trend": [
      {
        "date": "2025-11-01",
        "cost": 85.50
      }
    ],
    "projected_monthly_cost": 3150.00,
    "budget_status": {
      "monthly_budget": 10000.00,
      "current_spend": 2847.50,
      "percentage_used": 28.5,
      "days_remaining": 15
    }
  }
}
```

---

## 🎨 UI/UX Guidelines

### Overview Dashboard
- **Summary Cards**: Display key metrics:
  - Total requests (with trend indicator)
  - Success rate (with color coding: green >0.95, yellow 0.90-0.95, red <0.90)
  - Average latency (with p95 indicator)
  - Total cost (with budget status)
  - Total tokens (input/output breakdown)
- **Provider Breakdown**: Pie chart or bar chart showing requests by provider.
- **Agent Breakdown**: Bar chart showing requests by agent.
- **Period Selector**: Dropdown to select time period (1h, 24h, 7d, 30d).
- **Refresh Button**: Manual refresh button to update data.

### Time-Series Charts
- **Chart Types**:
  - **Line Chart**: For request volume, latency, cost trends over time.
  - **Area Chart**: For cumulative metrics.
  - **Bar Chart**: For grouped comparisons.
- **Metric Selector**: Dropdown to select metric (requests, latency, cost, errors, tokens).
- **Group By Selector**: Dropdown to group by provider, model, or agent.
- **Interval Selector**: Dropdown to select time interval (auto, 5m, 1h, 1d).
- **Interactive Tooltips**: Show detailed values on hover.
- **Legend**: Color-coded legend for different groups.
- **Zoom Controls**: Allow zooming into specific time ranges.

### Cost Analysis Dashboard
- **Total Cost Display**: Large, prominent display of total cost with period.
- **Cost Breakdown Charts**:
  - **Pie Chart**: Cost by provider (percentage breakdown).
  - **Bar Chart**: Cost by agent (with request counts).
  - **Bar Chart**: Cost by model (top models).
- **Daily Trend Chart**: Line chart showing daily cost trends.
- **Budget Status Card**: 
  - Progress bar showing budget usage
  - Percentage used
  - Days remaining
  - Projected monthly cost
  - Color coding (green <50%, yellow 50-80%, red >80%)
- **Export Button**: Export cost data to CSV/Excel.

### Filters and Controls
- **Period Selector**: Consistent period selector across all views.
- **Date Range Picker**: Advanced date range selection for custom periods.
- **Provider Filter**: Multi-select filter for providers.
- **Agent Filter**: Multi-select filter for agents.
- **Model Filter**: Multi-select filter for models.
- **Apply Filters Button**: Apply selected filters.

### Data Visualization Best Practices
- **Color Consistency**: Use consistent colors for providers/agents/models across charts.
- **Responsive Design**: Charts should be responsive and work on different screen sizes.
- **Loading States**: Show loading indicators while fetching data.
- **Empty States**: Show helpful messages when no data is available.
- **Error States**: Display error messages if data fetch fails.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Data Privacy**: Ensure telemetry data doesn't expose sensitive user information.
- **Cost Data**: Cost data is sensitive; ensure proper access controls.

---

## 📝 Notes

- Telemetry data is aggregated from hourly snapshots for performance.
- Time-series data supports real-time updates for recent periods.
- Cost projections are estimates based on current spending patterns.
- Budget status requires budget configuration in the Budgets submodule.

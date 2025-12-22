# Chat Analytics Dashboard - API Quick Reference

Quick reference guide for all chat analytics endpoints.

## Admin Endpoints

Base URL: `/api/v1/admin/chat`

### Dashboard Summary
```
GET /dashboard
```
**Auth**: Admin required
**Params**: `date_from`, `date_to` (optional)
**Returns**: Complete dashboard overview with top agents, trends, and key metrics

### Agent Performance
```
GET /dashboard/agents/performance
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`, `agent_type` (optional), `sort_by`, `limit`
**Returns**: Agent leaderboard with performance metrics

### Cache Efficiency
```
GET /dashboard/cache/efficiency
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`
**Returns**: Cache hit rates, memory usage, performance impact

### Cost Tracking
```
GET /dashboard/costs
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`, `group_by`
**Returns**: Cost breakdown by agent/model/day/user

### Error Monitoring
```
GET /dashboard/errors
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`, `severity` (optional)
**Returns**: Error rates, types, trends

### Active Users
```
GET /dashboard/users/active
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`
**Returns**: DAU, WAU, MAU, retention rates

### Conversation Metrics
```
GET /dashboard/conversations/metrics
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`
**Returns**: Conversation stats, topics, activity patterns

### Export Data
```
GET /dashboard/export
```
**Auth**: Admin required
**Params**: `date_from`, `date_to`, `format`, `include_sections`
**Returns**: Exported dashboard data in JSON or CSV

## User Endpoints

Base URL: `/api/v1/user/chat`

### My Analytics Dashboard
```
GET /my-analytics
```
**Auth**: User required
**Params**: `date_from`, `date_to` (optional)
**Returns**: Personalized analytics overview

### Personal Usage Stats
```
GET /my-analytics/usage
```
**Auth**: User required
**Params**: `date_from`, `date_to`
**Returns**: Personal usage statistics and patterns

### Conversation Insights
```
GET /my-analytics/insights
```
**Auth**: User required
**Params**: `date_from`, `date_to`
**Returns**: Conversation patterns, topics, recommendations

### Personal Cost Breakdown
```
GET /my-analytics/costs
```
**Auth**: User required
**Params**: `date_from`, `date_to`, `group_by`
**Returns**: Personal spending analysis and tips

### Favorite Agents
```
GET /my-analytics/agents/favorites
```
**Auth**: User required
**Params**: `date_from`, `date_to`, `limit`
**Returns**: Most-used agents with performance metrics

### Historical Trends
```
GET /my-analytics/trends
```
**Auth**: User required
**Params**: `date_from`, `date_to`, `granularity`
**Returns**: Activity trends over time

### Conversation History
```
GET /my-analytics/conversations/history
```
**Auth**: User required
**Params**: `date_from`, `date_to`, `limit`
**Returns**: Conversation history analysis

### Export My Data
```
GET /my-analytics/export
```
**Auth**: User required
**Params**: `date_from`, `date_to`, `format`, `include_conversations`
**Returns**: Personal analytics export

## Common Query Parameters

### Date Range
- `date_from`: Start date (ISO 8601 format)
- `date_to`: End date (ISO 8601 format)
- Default: Last 30 days

### Pagination
- `limit`: Max items to return (1-100)
- `offset`: Pagination offset

### Grouping
- `group_by`: Dimension (agent, model, day, user, conversation)

### Filtering
- `agent_type`: Filter by specific agent
- `severity`: Filter by error severity (critical, high, medium, low)

### Export
- `format`: Export format (json, csv)
- `include_sections`: Sections to include (array)
- `include_conversations`: Include full conversation data (boolean)

### Sorting
- `sort_by`: Sort metric (invocations, success_rate, avg_response_time, total_cost)

### Granularity
- `granularity`: Time granularity (hourly, daily, weekly)

## Example Requests

### cURL Examples

#### Get Admin Dashboard
```bash
curl -X GET \
  'http://localhost:8000/api/v1/admin/chat/dashboard?date_from=2025-11-16T00:00:00Z&date_to=2025-12-16T00:00:00Z' \
  -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'
```

#### Get Personal Analytics
```bash
curl -X GET \
  'http://localhost:8000/api/v1/user/chat/my-analytics' \
  -H 'Authorization: Bearer YOUR_USER_TOKEN'
```

#### Get Cost Breakdown by Agent
```bash
curl -X GET \
  'http://localhost:8000/api/v1/user/chat/my-analytics/costs?group_by=agent' \
  -H 'Authorization: Bearer YOUR_USER_TOKEN'
```

#### Export Dashboard Data
```bash
curl -X GET \
  'http://localhost:8000/api/v1/admin/chat/dashboard/export?format=csv&include_sections=agents,costs,errors' \
  -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'
```

### JavaScript/TypeScript Examples

#### Fetch Admin Dashboard
```typescript
const response = await fetch(
  '/api/v1/admin/chat/dashboard?date_from=2025-11-16&date_to=2025-12-16',
  {
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  }
);
const dashboard = await response.json();
console.log(`Total conversations: ${dashboard.total_conversations}`);
```

#### Fetch User Analytics
```typescript
const response = await fetch('/api/v1/user/chat/my-analytics', {
  headers: {
    'Authorization': `Bearer ${userToken}`
  }
});
const analytics = await response.json();
console.log(`Your total cost: $${analytics.total_cost_usd}`);
```

#### Fetch Agent Performance
```typescript
const response = await fetch(
  '/api/v1/admin/chat/dashboard/agents/performance?sort_by=success_rate&limit=10',
  {
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  }
);
const performance = await response.json();
performance.leaderboard.forEach(agent => {
  console.log(`${agent.agent_name}: ${agent.success_rate * 100}% success rate`);
});
```

### Python Examples

#### Using httpx
```python
import httpx
from datetime import datetime, timedelta

async with httpx.AsyncClient() as client:
    # Get admin dashboard
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=30)

    response = await client.get(
        "http://localhost:8000/api/v1/admin/chat/dashboard",
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    dashboard = response.json()
    print(f"Total conversations: {dashboard['total_conversations']}")
    print(f"Cache hit rate: {dashboard['cache_hit_rate'] * 100:.1f}%")
```

#### Using requests
```python
import requests

# Get user analytics
response = requests.get(
    "http://localhost:8000/api/v1/user/chat/my-analytics",
    headers={"Authorization": f"Bearer {user_token}"}
)

if response.status_code == 200:
    analytics = response.json()
    print(f"Most used agent: {analytics['most_used_agent']}")
    print(f"Total cost: ${analytics['total_cost_usd']:.2f}")
```

## Response Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

## Error Response Format

```json
{
  "detail": "Error description",
  "code": "error_code",
  "field": "field_name"  // For validation errors
}
```

## Rate Limits

- Admin endpoints: 100 requests/minute
- User endpoints: 60 requests/minute
- Export endpoints: 10 requests/hour

Exceeded limits return HTTP 429 with:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

## Common Use Cases

### 1. Build a Real-time Dashboard
```typescript
// Poll every 30 seconds for updates
setInterval(async () => {
  const dashboard = await fetchAdminDashboard();
  updateCharts(dashboard);
}, 30000);
```

### 2. Generate Daily Reports
```python
# Scheduled job to export daily metrics
from datetime import datetime, timedelta

date_to = datetime.utcnow()
date_from = date_to - timedelta(days=1)

export = await analytics_service.export_dashboard_data(
    date_from=date_from,
    date_to=date_to,
    export_format="csv",
    include_sections=["agents", "costs", "errors"]
)

# Email report to admins
send_email(recipients=admins, attachment=export.data)
```

### 3. User Cost Monitoring
```typescript
// Show user their spending vs budget
const analytics = await fetchMyAnalytics();
const budget = 50.00;
const spent = analytics.total_cost_usd;
const remaining = budget - spent;

showBudgetAlert(spent, remaining);
```

### 4. Agent Performance Comparison
```python
# Compare agent success rates
performance = await admin_service.get_agent_performance(
    sort_by="success_rate",
    limit=10
)

for agent in performance.leaderboard:
    print(f"{agent.agent_name}: {agent.success_rate * 100:.1f}%")
```

## Best Practices

1. **Use Date Ranges**: Always specify date ranges for better performance
2. **Cache Results**: Cache dashboard data on the frontend for 5 minutes
3. **Pagination**: Use pagination for large datasets
4. **Error Handling**: Always handle HTTP errors gracefully
5. **Rate Limiting**: Implement client-side rate limiting
6. **Export Smart**: Only export necessary sections to reduce payload size

## Support

For full API documentation, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

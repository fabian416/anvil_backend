# Chat Analytics Dashboard Implementation

Comprehensive admin and user analytics dashboards for chat feature monitoring and insights.

## Overview

This implementation provides two separate dashboard systems:

1. **Admin Dashboard** - System-wide analytics for administrators
2. **User Analytics Dashboard** - Personalized analytics for individual users

Both dashboards follow hexagonal architecture principles and provide REST endpoints that return JSON data for frontend consumption.

## Architecture

### Layer Structure

```
Presentation Layer (HTTP Controllers)
├── Admin Dashboard Router
│   └── /api/v1/admin/chat/dashboard
└── User Analytics Router
    └── /api/v1/user/chat/my-analytics

Application Layer (Services)
├── AdminChatAnalyticsService
│   └── Data aggregation and computation
└── UserChatAnalyticsService
    └── Personalized metrics and insights

Domain Layer (Ports & Value Objects)
├── ConversationRepository (Port)
└── Analytics Value Objects
    ├── ConversationTrends
    ├── AgentUsageStats
    ├── CostMetrics
    └── etc.

Infrastructure Layer
└── Repository Implementations
```

### Design Principles

- **Hexagonal Architecture**: Services use domain ports, not direct database access
- **CQRS Pattern**: Optimized read models for analytics queries
- **Dependency Injection**: All dependencies injected via Dishka
- **Type Safety**: Full Pydantic models for all responses
- **RESTful Design**: Standard HTTP methods and status codes

## Admin Dashboard

### Endpoints

#### 1. Dashboard Summary
```http
GET /api/v1/admin/chat/dashboard
```

**Query Parameters:**
- `date_from` (optional): Start date (defaults to 30 days ago)
- `date_to` (optional): End date (defaults to now)

**Response:**
```json
{
  "date_from": "2025-11-16T00:00:00Z",
  "date_to": "2025-12-16T00:00:00Z",
  "total_conversations": 12847,
  "total_messages": 156392,
  "total_active_users": 2341,
  "total_cost_usd": 1245.87,
  "total_agent_invocations": 45678,
  "most_used_agent": "risk_analyzer",
  "avg_success_rate": 0.97,
  "avg_response_time_ms": 2650.5,
  "error_rate": 0.023,
  "cache_hit_rate": 0.78,
  "top_agents": [
    {
      "agent_type": "risk_analyzer",
      "agent_name": "Risk Analyzer",
      "rank": 1,
      "total_invocations": 4256,
      "success_rate": 0.98,
      "avg_response_time_ms": 2340,
      "total_cost_usd": 145.32,
      "error_count": 85,
      "last_used": "2025-12-16T10:30:00Z"
    }
  ],
  "conversation_trend": [...],
  "cost_trend": [...]
}
```

#### 2. Agent Performance Leaderboard
```http
GET /api/v1/admin/chat/dashboard/agents/performance
```

**Query Parameters:**
- `date_from`, `date_to`: Date range
- `agent_type` (optional): Filter by specific agent
- `sort_by`: Sort metric (invocations, success_rate, avg_response_time, total_cost)
- `limit`: Number of agents to return (1-50, default 10)

**Features:**
- Agent performance rankings
- Success rates and error counts
- Response time metrics
- Cost tracking per agent
- Historical trends

#### 3. Cache Efficiency Metrics
```http
GET /api/v1/admin/chat/dashboard/cache/efficiency
```

**Metrics:**
- Overall hit/miss rates
- Memory usage
- Cache statistics by type
- Performance impact measurements
- Time-series trends

#### 4. Cost Tracking
```http
GET /api/v1/admin/chat/dashboard/costs
```

**Query Parameters:**
- `group_by`: Dimension (agent, model, day, user)

**Features:**
- Total spend tracking
- Cost breakdown by agent/model/user
- Token usage statistics
- Cost projections
- Daily trends

#### 5. Error Monitoring
```http
GET /api/v1/admin/chat/dashboard/errors
```

**Query Parameters:**
- `severity` (optional): Filter by severity (critical, high, medium, low)

**Metrics:**
- Error rates and counts
- Errors by type/agent/severity
- Critical error tracking
- Trend analysis

#### 6. Active Users
```http
GET /api/v1/admin/chat/dashboard/users/active
```

**Metrics:**
- DAU, WAU, MAU
- User retention rates
- Activity levels
- New user tracking

#### 7. Conversation Metrics
```http
GET /api/v1/admin/chat/dashboard/conversations/metrics
```

**Features:**
- Conversation statistics
- Topic distribution
- Activity patterns
- Engagement metrics

#### 8. Data Export
```http
GET /api/v1/admin/chat/dashboard/export
```

**Query Parameters:**
- `format`: Export format (json, csv)
- `include_sections`: Sections to export

**Response:**
- Structured export data
- Metadata
- Download information

## User Analytics Dashboard

### Endpoints

#### 1. Personal Analytics Summary
```http
GET /api/v1/user/chat/my-analytics
```

**Authentication Required**: Yes

**Response:**
```json
{
  "date_from": "2025-11-16T00:00:00Z",
  "date_to": "2025-12-16T00:00:00Z",
  "total_conversations": 42,
  "total_messages": 524,
  "total_cost_usd": 12.45,
  "most_used_agent": "risk_analyzer",
  "conversation_completion_rate": 0.87,
  "avg_response_satisfaction": 4.3,
  "top_agents": [...],
  "most_active_day": "Thursday",
  "most_active_hour": 14,
  "cost_this_period": 12.45,
  "cost_change_percentage": 8.5,
  "recent_conversations": [...]
}
```

#### 2. Personal Usage Statistics
```http
GET /api/v1/user/chat/my-analytics/usage
```

**Metrics:**
- Conversation and message counts
- Session duration statistics
- Activity patterns
- Engagement metrics
- Growth comparisons

#### 3. Conversation Insights
```http
GET /api/v1/user/chat/my-analytics/insights
```

**Features:**
- Conversation patterns
- Topic distribution
- Question type analysis
- Decision velocity
- Productivity recommendations

#### 4. Personal Cost Breakdown
```http
GET /api/v1/user/chat/my-analytics/costs
```

**Query Parameters:**
- `group_by`: Dimension (agent, model, day, conversation)

**Features:**
- Personal spending analysis
- Cost per agent/model
- Token usage tracking
- Cost-saving tips

#### 5. Favorite Agents
```http
GET /api/v1/user/chat/my-analytics/agents/favorites
```

**Features:**
- Most-used agents
- Personal success rates
- Performance comparisons
- Recommended agents

#### 6. Historical Trends
```http
GET /api/v1/user/chat/my-analytics/trends
```

**Query Parameters:**
- `granularity`: Time granularity (hourly, daily, weekly)

**Features:**
- Activity trends
- Cost trends
- Peak usage times
- Comparative metrics

#### 7. Conversation History Analysis
```http
GET /api/v1/user/chat/my-analytics/conversations/history
```

**Features:**
- Recent conversation summaries
- Historical patterns
- Topic analysis
- Quality metrics

#### 8. Personal Data Export
```http
GET /api/v1/user/chat/my-analytics/export
```

**Query Parameters:**
- `format`: Export format (json, csv)
- `include_conversations`: Include full conversation data

## Implementation Details

### File Structure

```
src/app/
├── presentation/http/
│   ├── controllers/
│   │   ├── admin/
│   │   │   ├── chat_dashboard.py          # Admin endpoints
│   │   │   └── router.py                  # Updated with chat route
│   │   ├── chat/
│   │   │   └── analytics_dashboard.py     # User endpoints
│   │   └── user/
│   │       └── router.py                  # Updated with analytics route
│   └── schemas/
│       ├── admin_chat_dashboard.py        # Admin response models
│       └── user_chat_analytics.py         # User response models
├── application/chat/services/
│   ├── admin_analytics_service.py         # Admin service
│   └── user_analytics_service.py          # User service
├── domain/
│   ├── ports/
│   │   └── conversation_repository.py     # Data access port
│   └── value_objects/chat/
│       └── analytics.py                   # Analytics value objects
└── infrastructure/auth/
    └── context.py                         # Auth helpers
```

### Response Models

All responses use Pydantic models for:
- Type safety
- Automatic validation
- OpenAPI documentation
- Clear API contracts

Example response model:
```python
class AgentLeaderboardEntry(BaseModel):
    agent_type: str
    agent_name: str
    rank: int
    total_invocations: int
    success_rate: float = Field(..., ge=0, le=1)
    avg_response_time_ms: float
    total_cost_usd: float
    error_count: int
    last_used: Optional[datetime] = None
```

### Service Layer

Services handle all business logic:
- Data aggregation from repositories
- Metric computation
- Trend analysis
- Export formatting

Example service method:
```python
async def get_dashboard_summary(
    self,
    date_from: datetime,
    date_to: datetime,
) -> AdminChatDashboardSummaryResponse:
    """Get complete admin dashboard summary."""
    # Aggregate data from repository
    # Compute metrics
    # Return structured response
```

## Integration with Dependency Injection

All services are injected via Dishka:

```python
@router.get("/dashboard")
@inject
async def get_chat_dashboard(
    analytics_service: FromDishka[AdminChatAnalyticsService] = None,
) -> AdminChatDashboardSummaryResponse:
    # Service is automatically injected
    dashboard_data = await analytics_service.get_dashboard_summary(...)
    return dashboard_data
```

## Data Sources

### Current Implementation

The current implementation uses placeholder/mock data to demonstrate the API structure. This allows frontend development to proceed while the data aggregation logic is implemented.

### Production Implementation Tasks

To make this production-ready, implement actual data aggregation in the services:

1. **Query Conversation Repository**
   ```python
   conversations = await self._repository.list_conversations(
       user_id=user_id,
       date_from=date_from,
       date_to=date_to
   )
   ```

2. **Aggregate Metrics**
   - Count conversations and messages
   - Calculate averages
   - Identify patterns
   - Track costs

3. **Compute Trends**
   - Time-series data
   - Growth rates
   - Comparative metrics

4. **Generate Insights**
   - Topic clustering (ML)
   - Pattern detection
   - Recommendations

## Frontend Integration

### Usage Example

```typescript
// Fetch admin dashboard
const response = await fetch(
  '/api/v1/admin/chat/dashboard?date_from=2025-11-16&date_to=2025-12-16'
);
const dashboard = await response.json();

// Render charts
renderConversationTrend(dashboard.conversation_trend);
renderAgentLeaderboard(dashboard.top_agents);
renderCostTrend(dashboard.cost_trend);
```

### Chart Recommendations

1. **Line Charts**: Trends over time (conversations, costs, errors)
2. **Bar Charts**: Agent leaderboards, topic distribution
3. **Pie Charts**: Cost breakdown, agent usage percentage
4. **Heatmaps**: Activity by day/hour
5. **Tables**: Detailed metrics, error logs

## Security Considerations

### Admin Dashboard

- **Authentication**: Requires admin role
- **Authorization**: Role-based access control
- **Data Privacy**: No PII in admin views
- **Rate Limiting**: Prevent dashboard API abuse

### User Analytics

- **Authentication**: Requires valid user session
- **Authorization**: Users can only see their own data
- **Data Isolation**: Strict user_id filtering
- **Export Limits**: Rate-limited and size-capped

## Performance Optimization

### Caching Strategy

```python
# Cache dashboard summaries
@cache(ttl=300)  # 5 minutes
async def get_dashboard_summary(...):
    # Expensive aggregations cached
```

### Pagination

For large datasets:
```python
conversations = await self._repository.list_conversations(
    limit=20,
    offset=page * 20
)
```

### Database Indexes

Required indexes:
```sql
CREATE INDEX idx_conversations_user_created
ON conversations(user_id, created_at);

CREATE INDEX idx_messages_conversation_created
ON messages(conversation_id, created_at);

CREATE INDEX idx_agent_invocations_timestamp
ON agent_metrics(agent_type, timestamp);
```

## Testing

### Unit Tests

```python
async def test_get_dashboard_summary():
    # Mock repository
    mock_repo = Mock(spec=ConversationRepository)

    # Create service
    service = AdminChatAnalyticsService(mock_repo)

    # Call method
    result = await service.get_dashboard_summary(
        date_from=datetime(2025, 11, 16),
        date_to=datetime(2025, 12, 16)
    )

    # Assertions
    assert result.total_conversations > 0
    assert result.cache_hit_rate >= 0
```

### Integration Tests

```python
async def test_dashboard_endpoint(client: AsyncClient):
    response = await client.get(
        "/api/v1/admin/chat/dashboard",
        params={"date_from": "2025-11-16", "date_to": "2025-12-16"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_conversations" in data
    assert "top_agents" in data
```

## Monitoring

### Metrics to Track

- Dashboard API response times
- Cache hit rates
- Error rates
- Query performance
- Export sizes

### Alerts

- Dashboard API failures
- Slow queries (> 5s)
- High error rates
- Unusual cost spikes

## Future Enhancements

1. **Real-time Updates**: WebSocket support for live dashboards
2. **Custom Reports**: User-defined metric combinations
3. **Alerts**: Threshold-based notifications
4. **Comparative Analytics**: Compare periods, users, agents
5. **ML Insights**: Anomaly detection, predictive analytics
6. **Export Scheduling**: Scheduled report generation
7. **Dashboard Templates**: Pre-configured views for common use cases

## Dependencies

### Required Packages

```toml
[dependencies]
fastapi = ">=0.104.0"
pydantic = ">=2.0.0"
dishka = ">=1.0.0"
```

### Optional Packages

```toml
[optional-dependencies]
pandas = ">=2.0.0"  # For CSV exports
matplotlib = ">=3.7.0"  # For chart generation
scikit-learn = ">=1.3.0"  # For topic clustering
```

## API Documentation

Once integrated, full API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All endpoints are automatically documented with:
- Request parameters
- Response schemas
- Example values
- Error codes

## Support

For questions or issues:
1. Check API documentation at `/docs`
2. Review this implementation guide
3. Check service logs for errors
4. Contact the backend team

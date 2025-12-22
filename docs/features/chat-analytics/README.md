# Chat Analytics Dashboard

Comprehensive analytics and monitoring dashboards for the chat feature.

## Overview

This feature provides two separate dashboard systems for monitoring and analyzing chat usage:

1. **Admin Dashboard** - System-wide analytics for administrators
2. **User Analytics Dashboard** - Personalized insights for individual users

## Features

### Admin Dashboard

**Endpoint**: `/api/v1/admin/chat/dashboard`

Key capabilities:
- Real-time usage statistics across all users
- Agent performance leaderboards with success rates, response times, and costs
- Cache efficiency monitoring (hit rates, memory usage)
- Comprehensive cost tracking with breakdowns by agent, model, and time period
- Error rate monitoring with severity classification
- Active users tracking (DAU, WAU, MAU)
- Conversation metrics and topic analysis
- Data export capabilities in JSON and CSV formats

### User Analytics Dashboard

**Endpoint**: `/api/v1/user/chat/my-analytics`

Personal insights:
- Individual usage statistics (conversations, messages)
- Conversation pattern analysis
- Personal cost breakdown and spending trends
- Favorite agents with performance metrics
- Historical activity trends with daily/weekly charts
- Conversation history analysis
- Personalized recommendations
- Personal data export

## Architecture

Built using hexagonal architecture principles:

```
┌─────────────────────────────────────┐
│     Presentation Layer (HTTP)        │
│  - Admin Dashboard Router            │
│  - User Analytics Router             │
│  - Pydantic Response Schemas         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Application Layer (Services)     │
│  - AdminChatAnalyticsService         │
│  - UserChatAnalyticsService          │
│  - Data Aggregation Logic            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Domain Layer (Ports)             │
│  - ConversationRepository            │
│  - Analytics Value Objects           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Infrastructure Layer (Adapters)    │
│  - Database Adapters                 │
│  - Cache Implementations             │
└─────────────────────────────────────┘
```

## Quick Start

### For Frontend Developers

1. **Fetch Admin Dashboard**
   ```typescript
   const response = await fetch('/api/v1/admin/chat/dashboard');
   const dashboard = await response.json();
   ```

2. **Fetch User Analytics**
   ```typescript
   const response = await fetch('/api/v1/user/chat/my-analytics');
   const analytics = await response.json();
   ```

3. **Render Charts**
   - Use `conversation_trend` for time-series charts
   - Use `top_agents` for leaderboards
   - Use `cost_by_agent` for pie charts

### For Backend Developers

1. **Service Integration**
   ```python
   from app.application.chat.services.admin_analytics_service import AdminChatAnalyticsService

   # Service is auto-injected via Dishka
   @inject
   async def my_function(
       analytics_service: FromDishka[AdminChatAnalyticsService] = None
   ):
       dashboard = await analytics_service.get_dashboard_summary(...)
   ```

2. **Add Custom Metrics**
   - Extend value objects in `domain/value_objects/chat/analytics.py`
   - Add computation logic in service layer
   - Update response schemas

## Files Created

### Controllers (Presentation Layer)
- `/src/app/presentation/http/controllers/admin/chat_dashboard.py` - Admin endpoints
- `/src/app/presentation/http/controllers/chat/analytics_dashboard.py` - User endpoints

### Schemas (Response Models)
- `/src/app/presentation/http/schemas/admin_chat_dashboard.py` - Admin responses
- `/src/app/presentation/http/schemas/user_chat_analytics.py` - User responses

### Services (Application Layer)
- `/src/app/application/chat/services/admin_analytics_service.py` - Admin analytics
- `/src/app/application/chat/services/user_analytics_service.py` - User analytics

### Infrastructure
- `/src/app/infrastructure/auth/context.py` - Authentication helpers

### Documentation
- `/docs/features/chat-analytics/DASHBOARD_IMPLEMENTATION.md` - Detailed guide
- `/docs/features/chat-analytics/API_QUICK_REFERENCE.md` - API reference
- `/docs/features/chat-analytics/README.md` - This file

## API Endpoints

### Admin Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /admin/chat/dashboard` | Dashboard summary | Admin |
| `GET /admin/chat/dashboard/agents/performance` | Agent leaderboard | Admin |
| `GET /admin/chat/dashboard/cache/efficiency` | Cache metrics | Admin |
| `GET /admin/chat/dashboard/costs` | Cost tracking | Admin |
| `GET /admin/chat/dashboard/errors` | Error monitoring | Admin |
| `GET /admin/chat/dashboard/users/active` | User metrics | Admin |
| `GET /admin/chat/dashboard/conversations/metrics` | Conversation stats | Admin |
| `GET /admin/chat/dashboard/export` | Export data | Admin |

### User Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /user/chat/my-analytics` | Personal dashboard | User |
| `GET /user/chat/my-analytics/usage` | Usage stats | User |
| `GET /user/chat/my-analytics/insights` | Conversation insights | User |
| `GET /user/chat/my-analytics/costs` | Cost breakdown | User |
| `GET /user/chat/my-analytics/agents/favorites` | Favorite agents | User |
| `GET /user/chat/my-analytics/trends` | Historical trends | User |
| `GET /user/chat/my-analytics/conversations/history` | History analysis | User |
| `GET /user/chat/my-analytics/export` | Export data | User |

## Integration Status

### Current Status
- ✅ Controllers implemented
- ✅ Response schemas defined
- ✅ Service layer created
- ✅ Routers integrated
- ✅ API documentation complete
- ⏳ Data aggregation (using mock data)
- ⏳ Dependency injection setup
- ⏳ Database queries
- ⏳ Cache integration

### Next Steps

1. **Implement Data Aggregation**
   - Replace mock data with actual repository queries
   - Implement metric computation logic
   - Add trend calculation algorithms

2. **Configure Dependency Injection**
   - Register services in Dishka container
   - Set up repository bindings
   - Configure cache providers

3. **Database Optimization**
   - Add necessary indexes
   - Optimize queries for large datasets
   - Implement query caching

4. **Testing**
   - Unit tests for services
   - Integration tests for endpoints
   - Performance testing for large datasets

5. **Production Readiness**
   - Add rate limiting
   - Implement monitoring
   - Set up alerts
   - Enable CORS if needed

## Usage Examples

### Building a Dashboard UI

```typescript
// Fetch data
const dashboard = await fetchAdminDashboard();

// Render key metrics
renderMetric('Total Conversations', dashboard.total_conversations);
renderMetric('Total Users', dashboard.total_active_users);
renderMetric('Total Cost', `$${dashboard.total_cost_usd}`);
renderMetric('Cache Hit Rate', `${dashboard.cache_hit_rate * 100}%`);

// Render charts
renderLineChart('Conversation Trend', dashboard.conversation_trend);
renderBarChart('Top Agents', dashboard.top_agents);
renderPieChart('Cost by Agent', dashboard.cost_breakdown);
```

### Exporting Reports

```python
# Export admin dashboard data
export_data = await admin_service.export_dashboard_data(
    date_from=datetime(2025, 11, 1),
    date_to=datetime(2025, 11, 30),
    export_format="csv",
    include_sections=["agents", "costs", "errors"]
)

# Save to file
with open("november_report.csv", "w") as f:
    f.write(export_data.data)
```

### Monitoring Costs

```typescript
// Get user's cost breakdown
const costs = await fetch('/api/v1/user/chat/my-analytics/costs?group_by=agent');
const costData = await costs.json();

// Alert if over budget
const budget = 50.00;
if (costData.cost_summary.total_cost_usd > budget) {
  showAlert(`You've exceeded your budget by $${costData.cost_summary.total_cost_usd - budget}`);
}

// Show cost-saving tips
costData.cost_saving_tips.forEach(tip => {
  showTip(tip);
});
```

## Performance Considerations

### Caching Strategy
- Dashboard summaries: 5-minute cache
- Agent performance: 10-minute cache
- Cost data: 15-minute cache
- User analytics: 5-minute cache

### Query Optimization
- Use indexed queries for date ranges
- Implement pagination for large result sets
- Pre-aggregate common metrics
- Use materialized views for complex calculations

### Rate Limiting
- Admin endpoints: 100 req/min
- User endpoints: 60 req/min
- Export endpoints: 10 req/hour

## Security

### Authentication
- All endpoints require authentication
- Admin endpoints require admin role
- User endpoints enforce user isolation

### Authorization
- Admin: Can view all system data
- User: Can only view their own data
- No PII exposed in admin aggregations

### Data Privacy
- User data is filtered by user_id
- Export data is rate-limited
- Sensitive fields are redacted

## Monitoring

### Metrics to Track
- API response times
- Cache hit rates
- Query performance
- Error rates
- Export sizes

### Alerts
- API failures
- Slow queries (> 5s)
- High error rates
- Cost spikes

## Documentation

- [Detailed Implementation Guide](./DASHBOARD_IMPLEMENTATION.md)
- [API Quick Reference](./API_QUICK_REFERENCE.md)
- [OpenAPI Docs](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

## Support

For questions or issues:
1. Check API documentation at `/docs`
2. Review implementation guide
3. Check service logs
4. Contact backend team

## Contributing

When extending the dashboard:

1. **Adding New Metrics**
   - Define value object in domain layer
   - Add computation in service layer
   - Update response schema
   - Add endpoint in controller

2. **Code Style**
   - Follow hexagonal architecture
   - Use dependency injection
   - Type all parameters
   - Document all methods

3. **Testing**
   - Write unit tests for services
   - Write integration tests for endpoints
   - Test with large datasets
   - Validate response schemas

## License

Internal use only - part of Anvil backend system.

# Analytics Dashboard Implementation Guide

**Priority**: 2
**Status**: 70% Complete | Data Aggregation Needed
**Date**: December 16, 2025

---

## Summary

Analytics dashboard infrastructure (services, controllers, schemas, WebSocket) is complete. This guide provides the remaining steps to implement real data aggregation replacing TODO comments.

---

## Completed Work

✅ `user_analytics_service.py` - Service skeleton with method signatures
✅ `admin_analytics_service.py` - Service skeleton with method signatures
✅ `analytics_dashboard.py` - API controller with endpoints
✅ `analytics_handler.py` - WebSocket support for real-time updates
✅ `user_chat_analytics.py` - Complete Pydantic schemas
✅ `analytics_repository_adapter.py` - PostgreSQL adapter
✅ Database migrations for analytics entities

---

## Data Sources

Analytics data comes from existing tables:
- `conversations` - Conversation metadata, status, timestamps
- `messages` - Message content, costs, agent usage, timestamps
- `users` - User information
- `conversation_analytics` - Pre-aggregated analytics data

---

## Implementation Tasks

### Task 1: User Analytics Service - get_user_dashboard()

**File**: `src/app/application/chat/services/user_analytics_service.py`
**Function**: `get_user_dashboard()` (around line 50)

**Current**:
```python
async def get_user_dashboard(
    self,
    user_id: UUID,
) -> UserDashboardAnalytics:
    """Get comprehensive dashboard analytics for a user."""
    # TODO: Implement real data aggregation
    return UserDashboardAnalytics(...)
```

**Implementation**:
```python
async def get_user_dashboard(
    self,
    user_id: UUID,
) -> UserDashboardAnalytics:
    """Get comprehensive dashboard analytics for a user."""
    # Get conversation count
    conversation_count = await self._conversation_repository.count_by_user(user_id)

    # Get message count
    message_count = await self._message_repository.count_by_user(user_id)

    # Get active conversations (last 7 days)
    active_conversations = await self._conversation_repository.count_active_by_user(
        user_id=user_id,
        since=datetime.utcnow() - timedelta(days=7)
    )

    # Get total cost
    total_cost = await self._message_repository.sum_cost_by_user(user_id)

    # Get most used agent
    most_used_agent = await self._message_repository.get_most_used_agent(user_id)

    # Get conversation trend (last 30 days)
    trend = await self._conversation_repository.get_daily_counts(
        user_id=user_id,
        days=30
    )

    return UserDashboardAnalytics(
        total_conversations=conversation_count,
        total_messages=message_count,
        active_conversations=active_conversations,
        total_cost=total_cost,
        average_messages_per_conversation=message_count / max(conversation_count, 1),
        most_used_agent=most_used_agent,
        conversation_trend=trend,
    )
```

### Task 2: User Analytics Service - get_usage_stats()

**File**: `src/app/application/chat/services/user_analytics_service.py`
**Function**: `get_usage_stats()` (around line 70)

**Implementation**:
```python
async def get_usage_stats(
    self,
    user_id: UUID,
    period: str = "week",  # week, month, year
) -> UsageStatistics:
    """Get usage statistics for a time period."""
    # Calculate period dates
    now = datetime.utcnow()
    if period == "week":
        since = now - timedelta(days=7)
    elif period == "month":
        since = now - timedelta(days=30)
    else:  # year
        since = now - timedelta(days=365)

    # Get message stats
    message_stats = await self._message_repository.get_stats_by_period(
        user_id=user_id,
        since=since
    )

    # Get agent breakdown
    agent_breakdown = await self._message_repository.get_agent_usage_breakdown(
        user_id=user_id,
        since=since
    )

    # Get cost breakdown
    cost_breakdown = await self._message_repository.get_cost_breakdown(
        user_id=user_id,
        since=since
    )

    # Get peak usage hours
    peak_hours = await self._message_repository.get_peak_usage_hours(
        user_id=user_id,
        since=since
    )

    return UsageStatistics(
        period=period,
        total_messages=message_stats["total"],
        total_cost=cost_breakdown["total"],
        average_daily_messages=message_stats["daily_average"],
        agent_usage_breakdown=agent_breakdown,
        cost_breakdown_by_agent=cost_breakdown["by_agent"],
        peak_usage_hours=peak_hours,
    )
```

### Task 3: Admin Analytics Service - get_system_overview()

**File**: `src/app/application/chat/services/admin_analytics_service.py`
**Function**: `get_system_overview()` (around line 40)

**Implementation**:
```python
async def get_system_overview(self) -> SystemOverview:
    """Get system-wide analytics overview."""
    # Total users
    total_users = await self._user_repository.count_all()

    # Active users (last 30 days)
    active_users_30d = await self._user_repository.count_active_since(
        since=datetime.utcnow() - timedelta(days=30)
    )

    # Total conversations
    total_conversations = await self._conversation_repository.count_all()

    # Total messages
    total_messages = await self._message_repository.count_all()

    # Total cost
    total_cost = await self._message_repository.sum_all_costs()

    # Agent performance
    agent_performance = await self._message_repository.get_agent_performance_metrics()

    # System health metrics
    avg_response_time = await self._message_repository.get_average_response_time()
    error_rate = await self._message_repository.get_error_rate()

    # Growth metrics
    growth_metrics = await self._conversation_repository.get_growth_metrics(days=90)

    return SystemOverview(
        total_users=total_users,
        active_users_30d=active_users_30d,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_cost=total_cost,
        average_response_time_ms=avg_response_time,
        system_error_rate=error_rate,
        agent_performance=agent_performance,
        growth_metrics=growth_metrics,
    )
```

### Task 4: Add Repository Methods

You'll need to add these methods to the repositories:

**ConversationRepository methods**:
```python
async def count_by_user(self, user_id: UUID) -> int
async def count_active_by_user(self, user_id: UUID, since: datetime) -> int
async def get_daily_counts(self, user_id: UUID, days: int) -> List[Dict]
async def count_all(self) -> int
async def get_growth_metrics(self, days: int) -> Dict
```

**MessageRepository methods**:
```python
async def count_by_user(self, user_id: UUID) -> int
async def sum_cost_by_user(self, user_id: UUID) -> float
async def get_most_used_agent(self, user_id: UUID) -> Optional[str]
async def get_stats_by_period(self, user_id: UUID, since: datetime) -> Dict
async def get_agent_usage_breakdown(self, user_id: UUID, since: datetime) -> List[Dict]
async def get_cost_breakdown(self, user_id: UUID, since: datetime) -> Dict
async def get_peak_usage_hours(self, user_id: UUID, since: datetime) -> List[int]
async def count_all(self) -> int
async def sum_all_costs(self) -> float
async def get_agent_performance_metrics(self) -> List[Dict]
async def get_average_response_time(self) -> float
async def get_error_rate(self) -> float
```

### Task 5: Example Repository Implementation

**File**: `src/app/infrastructure/adapters/chat/conversation_repository_adapter.py`

```python
async def count_by_user(self, user_id: UUID) -> int:
    """Count conversations for a user."""
    async with self._session_factory() as session:
        result = await session.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user_id)
        )
        return result.scalar() or 0

async def count_active_by_user(self, user_id: UUID, since: datetime) -> int:
    """Count active conversations since a date."""
    async with self._session_factory() as session:
        result = await session.execute(
            select(func.count(Conversation.id))
            .where(
                Conversation.user_id == user_id,
                Conversation.last_message_at >= since
            )
        )
        return result.scalar() or 0

async def get_daily_counts(self, user_id: UUID, days: int) -> List[Dict]:
    """Get daily conversation counts."""
    async with self._session_factory() as session:
        since = datetime.utcnow() - timedelta(days=days)
        result = await session.execute(
            select(
                func.date(Conversation.created_at).label("date"),
                func.count(Conversation.id).label("count")
            )
            .where(
                Conversation.user_id == user_id,
                Conversation.created_at >= since
            )
            .group_by(func.date(Conversation.created_at))
            .order_by(func.date(Conversation.created_at))
        )
        return [{"date": str(row.date), "count": row.count} for row in result]
```

### Task 6: Register Analytics Routes

**File**: `src/app/presentation/http/controllers/api_v1_router.py`

Check if analytics router is registered:

```python
from app.presentation.http.controllers.chat.analytics_dashboard import (
    create_analytics_router,
)

# In sub_routers tuple:
create_analytics_router(),  # Add this if not present
```

### Task 7: Testing

**Create**: `tests/integration/analytics/test_analytics_dashboard.py`

```python
import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_user_dashboard(client, auth_headers):
    """Test user dashboard analytics."""
    response = client.get(
        "/api/v1/chat/analytics/dashboard",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_conversations" in data
    assert "total_messages" in data
    assert "total_cost" in data
    assert data["total_conversations"] >= 0


@pytest.mark.asyncio
async def test_usage_stats_week(client, auth_headers):
    """Test weekly usage statistics."""
    response = client.get(
        "/api/v1/chat/analytics/usage?period=week",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "week"
    assert "total_messages" in data
    assert "agent_usage_breakdown" in data


@pytest.mark.asyncio
async def test_admin_system_overview(client, admin_auth_headers):
    """Test admin system overview."""
    response = client.get(
        "/api/v1/chat/analytics/admin/system-overview",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_conversations" in data
    assert "agent_performance" in data
```

---

## Database Indexes for Performance

Add these indexes for faster analytics queries:

```sql
-- Conversation indexes
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at DESC);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);

-- Message indexes
CREATE INDEX idx_messages_user_created ON messages(user_id, created_at DESC);
CREATE INDEX idx_messages_agent_cost ON messages(agent_name, cost);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);

-- Analytics table indexes
CREATE INDEX idx_analytics_user_date ON conversation_analytics(user_id, date DESC);
```

---

## Caching Strategy

Add caching to improve dashboard performance:

```python
# In user_analytics_service.py
from app.infrastructure.cache.external_api_cache import cache_result

@cache_result(ttl=300)  # 5 minute cache
async def get_user_dashboard(self, user_id: UUID) -> UserDashboardAnalytics:
    # Implementation...
```

---

## Success Criteria

✅ All TODO comments removed from analytics services
✅ User dashboard returns real data (not mock data)
✅ Admin system overview shows accurate metrics
✅ Analytics queries complete in < 500ms
✅ Integration tests pass
✅ Dashboard loads without errors

---

## Estimated Time

- Task 1-3: Implement service methods: ~2 hours
- Task 4-5: Add repository methods: ~2 hours
- Task 6: Router registration: ~15 minutes
- Task 7: Write tests: ~1 hour
- Database indexes: ~30 minutes
- Caching: ~30 minutes

**Total**: ~6-7 hours

---

## Monitoring

After deployment, monitor:
- Dashboard load times
- Query performance
- Cache hit rates
- API error rates
- Data accuracy vs expectations

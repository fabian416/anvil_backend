# FRONTEND_USER_CHAT_ANALYTICS

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/chat/analytics_dashboard.py` & `user_chat_analytics.py`

## 1. Analytics Overview
These endpoints allow users to track their own AI interaction metrics, costs, and behaviors.

**Base URL**: `/api/v1/user/chat/my-analytics`

| Endpoint | Purpose |
| :--- | :--- |
| `/` | Dashboard Overview |
| `/usage` | Usage Statistics |
| `/insights` | Conversation Patterns |
| `/costs` | Cost Breakdown |
| `/agents/favorites` | Agent Preferences |
| `/trends` | Historical Charts |
| `/conversations/history` | History Analysis |
| `/export` | Data Export |

---

## 2. Endpoints

### 2.1 Get Dashboard Overview
**GET** `/api/v1/user/chat/my-analytics`

| Query Param | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `date_from` | `iso8601` | 30 days ago | Start date. |
| `date_to` | `iso8601` | Now | End date. |

**Response (200 OK):**
```json
{
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-30T00:00:00Z",
  "total_conversations": 45,
  "total_messages": 350,
  "total_cost_usd": 12.50,
  "most_used_agent": "hunter_ai",
  "conversation_completion_rate": 0.85,
  "avg_response_satisfaction": 4.5,
  "top_agents": [
    {
      "agent_type": "hunter_ai",
      "usage_percentage": 45.0
    }
  ],
  "cost_this_period": 12.50,
  "cost_change_percentage": 5.2
}
```

### 2.2 Get Usage Stats
**GET** `/api/v1/user/chat/my-analytics/usage`

Detailed usage metrics including activity heatmaps.

**Response (200 OK):**
```json
{
  "usage_stats": {
    "total_conversations": 45,
    "avg_messages_per_conversation": 7.8,
    "total_session_time_hours": 12.5,
    "most_active_hour": 14
  },
  "messages_by_day": { "Monday": 120, "Tuesday": 80 },
  "messages_by_hour": { "14": 50, "15": 30 },
  "conversation_growth": 12.5,
  "message_growth": 8.0
}
```

### 2.3 Get Cost Breakdown
**GET** `/api/v1/user/chat/my-analytics/costs`
*   Query `group_by`: `agent` | `model` | `day` | `conversation`

**Response (200 OK):**
```json
{
  "cost_summary": {
    "total_cost_usd": 12.50,
    "avg_cost_per_conversation": 0.27,
    "most_expensive_agent": "hunter_ai",
    "projected_monthly_cost_usd": 15.00
  },
  "cost_by_agent": {
    "hunter_ai": 8.50,
    "chat_agent": 2.00
  },
  "cost_saving_tips": ["Use basic chat for simple queries"]
}
```

### 2.4 Get Favorite Agents
**GET** `/api/v1/user/chat/my-analytics/agents/favorites`

**Response (200 OK):**
```json
{
  "favorite_agents": [
    {
      "agent_name": "Hunter AI",
      "usage_count": 150,
      "usage_percentage": 45.0,
      "success_rate": 0.98,
      "avg_response_time_ms": 1200
    }
  ],
  "best_performing_agent": "hunter_ai",
  "recommended_new_agents": ["risk_analyzer"]
}
```

### 2.5 Get Historical Trends
**GET** `/api/v1/user/chat/my-analytics/trends`
*   Query `granularity`: `hourly` | `daily` | `weekly`

**Response (200 OK):**
```json
{
  "conversation_trend": {
    "label": "Conversations",
    "trend_direction": "up",
    "data_points": [
      {
        "date": "2024-01-01",
        "conversations": 5,
        "cost_usd": 1.20
      }
    ]
  },
  "activity_consistency_score": 0.85
}
```

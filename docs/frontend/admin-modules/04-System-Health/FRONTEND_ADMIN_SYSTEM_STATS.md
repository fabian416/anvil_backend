# Admin Module: System Stats

> **Technical Specification**: `FRONTEND_ADMIN_SYSTEM_STATS`
> **Backend Controller**: `admin/stats/router.py`
> **Base URL**: `/api/admin/stats`

## 📖 Overview
The **System Stats** submodule provides high-level system statistics for administrators. It offers a quick overview of active conversations, message counts, agent usage, and other key system metrics.

### Key Capabilities
1. **System Overview**: View high-level system statistics.
2. **Active Conversations**: Monitor active conversation count.
3. **Message Statistics**: View total message counts.
4. **Agent Usage**: View agent usage statistics by type.

---

## 🔌 API Endpoints

### 1. Get Stats
**GET** `/api/admin/stats/`
Retrieve system statistics overview.

**Response (`AdminStats`)**:
```json
{
  "active_conversations": 10,
  "total_messages": 150,
  "active_agents": 5,
  "agent_usage": [
    {
      "agent_type": "trading",
      "count": 50
    },
    {
      "agent_type": "research",
      "count": 30
    }
  ]
}
```

**Response Fields**:
- `active_conversations`: Number of currently active conversations
- `total_messages`: Total number of messages in the system
- `active_agents`: Number of active agents
- `agent_usage`: Array of agent usage statistics by type

---

## 🎨 UI/UX Guidelines

### Stats Dashboard
- **Summary Cards**: Display key metrics in cards:
  - **Active Conversations**: Large number with "Active" label
  - **Total Messages**: Large number with "Total Messages" label
  - **Active Agents**: Large number with "Active Agents" label
- **Agent Usage Chart**: Visual representation of agent usage:
  - **Bar Chart**: Horizontal or vertical bar chart showing agent usage by type
  - **Pie Chart**: Alternative pie chart showing distribution
  - **Color Coding**: Different colors for each agent type
- **Refresh Button**: Manual refresh button to update statistics.
- **Auto-Refresh**: Optional auto-refresh toggle (every 30 seconds or 1 minute).

### Agent Usage Display
- **Agent Type Badges**: Display agent types with usage counts:
  - Trading: 50
  - Research: 30
  - Other agent types...
- **Visual Indicators**: Use icons or badges to represent different agent types.
- **Sorting**: Allow sorting by usage count (highest to lowest).

### Layout
- **Grid Layout**: Use a responsive grid layout for summary cards.
- **Chart Section**: Dedicated section for agent usage visualization.
- **Responsive Design**: Ensure dashboard works on different screen sizes.

### Data Updates
- **Loading State**: Show loading indicator while fetching stats.
- **Error State**: Display error message if stats fetch fails.
- **Empty State**: Show helpful message if no data is available.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Read-Only**: Currently read-only; no write operations.

---

## 📝 Notes

- This module provides a high-level overview; detailed metrics are available in the Metrics submodule.
- Stats are real-time and reflect current system state.
- Agent usage statistics may be expanded in the future to include more detailed breakdowns.

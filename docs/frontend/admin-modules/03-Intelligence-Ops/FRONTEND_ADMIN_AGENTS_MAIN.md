# Admin Module: Agent Management

> **Technical Specification**: `FRONTEND_ADMIN_AGENTS_MAIN`
> **Backend Controller**: `admin/agent/router.py`
> **Base URL**: `/api/admin/agents`

## 📖 Overview
The **Agent Management** submodule enables administrators to view and monitor AI agents available in the system. It provides a list of all agents with their types, names, descriptions, and active status.

### Key Capabilities
1. **Agent Registry**: View all available agents (Trading, Research, etc.).
2. **Status Monitoring**: Check which agents are active or inactive.
3. **Agent Information**: View agent type, name, and description.

---

## 🔌 API Endpoints

### 1. List Agents
**GET** `/api/admin/agents/`
Retrieve a list of all agents in the system.

**Response (`List[AgentRead]`)**:
```json
[
  {
    "type": "TRADING",
    "name": "Trading Agent",
    "description": "Analyzes market trends",
    "is_active": true
  },
  {
    "type": "RESEARCH",
    "name": "Research Agent",
    "description": "Deep dive into protocols",
    "is_active": true
  }
]
```

**Agent Types**:
- `TRADING`: Trading and market analysis agent
- `RESEARCH`: Research and protocol analysis agent
- Additional agent types may be added in the future

---

## 🎨 UI/UX Guidelines

### Agent List View
- **Display Format**: Cards or table showing agent information.
- **Columns/Card Fields**:
  - **Type**: Badge showing agent type (e.g., "Trading", "Research").
  - **Name**: Agent display name.
  - **Description**: Brief description of agent capabilities.
  - **Status**: Active/Inactive badge (Green for active, Grey for inactive).
- **Sorting**: Allow sorting by type, name, or status.
- **Filtering**: Filter by agent type or active status.

### Status Indicators
- **Active**: Green badge or dot.
- **Inactive**: Grey badge or dot.

### Future Enhancements
- Agent configuration management.
- Agent performance metrics.
- Agent usage statistics.
- Agent enable/disable controls.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Read-Only**: Currently read-only; future updates may require additional permissions.

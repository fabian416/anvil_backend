# FRONTEND_ADMIN_AGENTS

## Admin Agent Management Module

**User Type:** Administrator  
**Module:** Admin - Agent Management  
**Route:** `/admin/agents`  
**Platform:** Web (React)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Admin Agent Management** - Multi-Agent System Configuration

### Description
Administrative interface for managing DeFi multi-agent system, including agent listing, configuration, and status monitoring.

### Key Capabilities
- ✅ List all agents
- ✅ View agent details
- ✅ Monitor agent status
- ✅ Agent configuration overview

---

## 🔌 API Integration

### List Agents

```typescript
// GET /api/v1/admin/agents/
// Description: List all agents (admin only)
// Authentication: Required (Bearer token + Admin role)

interface AgentRead {
  type: string; // 'trading' | 'research' | 'risk' | 'yield' | 'portfolio'
  name: string;
  description: string;
  is_active: boolean;
}

const listAgents = async (): Promise<AgentRead[]> => {
  const response = await api.get('/api/v1/admin/agents/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Response (200 OK):
[
  {
    "type": "trading",
    "name": "Trading Agent",
    "description": "Analyzes market trends and provides trading insights",
    "is_active": true
  },
  {
    "type": "research",
    "name": "Research Agent",
    "description": "Deep dive into protocols and provides research insights",
    "is_active": true
  },
  {
    "type": "risk",
    "name": "Risk Agent",
    "description": "Monitors and analyzes protocol risks",
    "is_active": true
  }
]
```

---

## 🔗 React Hooks

```typescript
export function useAdminAgents() {
  return useQuery({
    queryKey: ['admin', 'agents'],
    queryFn: listAgents,
  });
}
```

---

## 🎨 React Components

```typescript
export function AdminAgentsList() {
  const { data: agents, isLoading } = useAdminAgents();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="agents-list">
      <h2>Multi-Agent System</h2>
      <div className="agents-grid">
        {agents?.map((agent) => (
          <div key={agent.type} className="agent-card">
            <h3>{agent.name}</h3>
            <p>{agent.description}</p>
            <span className={`status ${agent.is_active ? 'active' : 'inactive'}`}>
              {agent.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin Agent Management*  
*Backend Status: ✅ 100% Implemented (1 endpoint)*  
*Frontend Status: ✅ Ready for Implementation*

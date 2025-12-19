# FRONTEND_ADMIN_COMPLETE

## Complete Admin API Documentation

**User Type:** Administrator  
**Module:** Admin - Complete Platform Management  
**Platform:** Web (React)  
**Version:** 1.0

---

## 📋 Overview

Comprehensive admin interface covering user management, project configuration, distillation system, and analytics.

---

## 🔌 Admin Stats

```typescript
// GET /api/v1/admin/stats/
interface AdminStats {
  active_conversations: number;
  total_messages: number;
  active_agents: number;
  agent_usage: AgentUsage[];
}

const getAdminStats = async (): Promise<AdminStats> => {
  const response = await api.get('/api/v1/admin/stats/');
  return response.data;
};
```

---

## 👥 User Management

### 6 Admin User Endpoints

```typescript
// 1. GET /api/v1/admin/users - List users
// 2. PATCH /api/v1/admin/users/{email}/grant-admin - Grant admin
// 3. PATCH /api/v1/admin/users/{email}/revoke-admin - Revoke admin
// 4. PATCH /api/v1/admin/users/{email}/activate - Activate user
// 5. PATCH /api/v1/admin/users/{email}/deactivate - Deactivate user
// 6. PUT /api/v1/admin/users/{email}/password - Change user password
```

---

## 📦 Projects Management

### Complete Project CRUD

```typescript
// POST /api/v1/admin/projects/
interface ProjectCreate {
  slug: string;
  name: string;
  system_prompt: string;
  description?: string;
  icon?: string;
  color?: string;
  status?: string;
  visibility?: string;
  enabled_protocols?: string[];
  enabled_chains?: string[];
  enabled_tools?: string[];
  max_users?: number;
  is_featured?: boolean;
}

// GET /api/v1/admin/projects/ - List projects
// GET /api/v1/admin/projects/{id} - Get project
// PATCH /api/v1/admin/projects/{id} - Update project
// DELETE /api/v1/admin/projects/{id} - Delete project
// POST /api/v1/admin/projects/{id}/activate - Activate project

// Knowledge Management
// POST /api/v1/admin/projects/{id}/knowledge/documents
// GET /api/v1/admin/projects/{id}/knowledge/documents

// Assignment Rules
// POST /api/v1/admin/projects/{id}/assignment-rules
// GET /api/v1/admin/projects/{id}/assignment-rules
// PATCH /api/v1/admin/projects/{id}/assignment-rules/{rule_id}

// User Assignments
// POST /api/v1/admin/projects/{id}/assignments
// GET /api/v1/admin/projects/{id}/assignments
```

---

## ⚡ Distillation System

### Configuration & Management

```typescript
// Configuration
// GET /api/v1/admin/distillation/config
// PATCH /api/v1/admin/distillation/config

interface DistillationConfig {
  enabled: boolean;
  cache_enabled: boolean;
  static_responses_enabled: boolean;
  semantic_cache_enabled: boolean;
  min_confidence_threshold: number;
  semantic_similarity_threshold: number;
  max_classification_latency_ms: number;
}

// Static Responses
// POST /api/v1/admin/distillation/static-responses
// GET /api/v1/admin/distillation/static-responses
// PATCH /api/v1/admin/distillation/static-responses/{id}
// DELETE /api/v1/admin/distillation/static-responses/{id}

// Cache Management
// POST /api/v1/admin/distillation/cache/invalidate
// GET /api/v1/admin/distillation/cache/stats

// Telemetry
// GET /api/v1/admin/distillation/telemetry/requests
// GET /api/v1/admin/distillation/telemetry/summary
```

---

## 🔗 React Hooks

```typescript
export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: getAdminStats,
  });
}

export function useProjects() {
  return useQuery({
    queryKey: ['admin', 'projects'],
    queryFn: listProjects,
  });
}

export function useDistillationConfig() {
  return useQuery({
    queryKey: ['admin', 'distillation', 'config'],
    queryFn: getDistillationConfig,
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin - Complete Platform Management*  
*Backend Status: ✅ 100% Implemented (20+ endpoints)*  
*Frontend Status: ✅ Ready for Implementation*

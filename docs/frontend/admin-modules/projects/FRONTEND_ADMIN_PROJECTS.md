# FRONTEND_ADMIN_PROJECTS

## Admin Projects Management Module

**User Type:** Admin Only  
**Module:** Admin Projects - Project & Knowledge Management  
**Route:** `/admin/projects`  
**Platform:** Web (Admin Dashboard)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Admin Projects** - Manage Projects, Knowledge Base, and User Assignments

### Description
Comprehensive admin interface for managing DeFi AI projects, including project CRUD operations, knowledge document management, user assignment rules, and project-specific configurations.

### Key Capabilities
- ✅ Create/edit/delete projects
- ✅ Manage project status and visibility
- ✅ Upload and manage knowledge documents
- ✅ Configure assignment rules
- ✅ Assign users to projects
- ✅ Search projects
- ✅ Project analytics and metrics

---

## 🔌 API Integration

### Projects CRUD

#### 1. Create Project

```typescript
// POST /api/v1/admin/projects/
// Description: Create a new project with full configuration
// Authentication: Required (Admin role)

interface ProjectCreate {
  slug: string; // URL-friendly identifier
  name: string;
  description?: string;
  icon?: string; // Icon URL or emoji
  color?: string; // Hex color code
  banner_url?: string;
  status?: 'draft' | 'active' | 'archived';
  visibility?: 'public' | 'private' | 'team';
  system_prompt: string; // AI system prompt for the project
  welcome_message?: string;
  enabled_protocols?: string[]; // List of protocol IDs
  enabled_chains?: string[]; // List of chain names
  enabled_tools?: string[]; // List of tool names
  risk_config?: Record<string, any>; // Risk analysis configuration
  max_users?: number;
  display_order?: number;
  is_featured?: boolean;
}

const createProject = async (data: ProjectCreate): Promise<ProjectResponse> => {
  const response = await api.post('/api/v1/admin/projects/', data);
  return response.data;
};

// Example Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "slug": "defi-yield-optimizer",
  "name": "DeFi Yield Optimizer",
  "description": "AI-powered yield optimization across protocols",
  "icon": "🎯",
  "color": "#3B82F6",
  "status": "active",
  "visibility": "public",
  "system_prompt": "You are a DeFi yield optimization specialist...",
  "enabled_protocols": ["aave-v3", "compound", "curve"],
  "enabled_chains": ["ethereum", "arbitrum", "optimism"],
  "enabled_tools": ["swap", "supply", "yield_analysis"],
  "is_featured": true,
  "created_at": "2025-12-01T12:00:00Z",
  "updated_at": "2025-12-01T12:00:00Z"
}
```

#### 2. List Projects

```typescript
// GET /api/v1/admin/projects/?status=active&limit=50&offset=0
// Description: List all projects with filters
// Authentication: Required (Admin role)

const listProjects = async (filters?: {
  status?: string;
  visibility?: string;
  is_featured?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ProjectResponse[]> => {
  const response = await api.get('/api/v1/admin/projects/', { params: filters });
  return response.data;
};
```

#### 3. Get Project

```typescript
// GET /api/v1/admin/projects/{project_id}
// Description: Get single project details
// Authentication: Required (Admin role)

const getProject = async (projectId: string): Promise<ProjectResponse> => {
  const response = await api.get(`/api/v1/admin/projects/${projectId}`);
  return response.data;
};
```

#### 4. Update Project

```typescript
// PATCH /api/v1/admin/projects/{project_id}
// Description: Update project fields
// Authentication: Required (Admin role)

interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: 'draft' | 'active' | 'archived';
  system_prompt?: string;
  enabled_protocols?: string[];
  // ... other optional fields
}

const updateProject = async (
  projectId: string,
  updates: ProjectUpdate
): Promise<ProjectResponse> => {
  const response = await api.patch(`/api/v1/admin/projects/${projectId}`, updates);
  return response.data;
};
```

#### 5. Delete Project

```typescript
// DELETE /api/v1/admin/projects/{project_id}
// Description: Delete a project (soft delete)
// Authentication: Required (Admin role)

const deleteProject = async (projectId: string): Promise<void> => {
  await api.delete(`/api/v1/admin/projects/${projectId}`);
};
```

---

### Knowledge Documents

#### 6. Create Knowledge Document

```typescript
// POST /api/v1/admin/projects/{project_id}/knowledge
// Description: Upload knowledge document for project
// Authentication: Required (Admin role)

interface KnowledgeDocumentCreate {
  title: string;
  content: string; // Markdown or plain text
  document_type: 'protocol_guide' | 'faq' | 'strategy' | 'general';
  metadata?: Record<string, any>;
  is_active?: boolean;
}

const createKnowledgeDocument = async (
  projectId: string,
  data: KnowledgeDocumentCreate
): Promise<KnowledgeDocumentResponse> => {
  const response = await api.post(
    `/api/v1/admin/projects/${projectId}/knowledge`,
    data
  );
  return response.data;
};
```

#### 7. List Knowledge Documents

```typescript
// GET /api/v1/admin/projects/{project_id}/knowledge
// Description: List all knowledge documents for a project
// Authentication: Required (Admin role)

const listKnowledgeDocuments = async (
  projectId: string
): Promise<KnowledgeDocumentResponse[]> => {
  const response = await api.get(`/api/v1/admin/projects/${projectId}/knowledge`);
  return response.data;
};
```

---

### Assignment Rules

#### 8. Create Assignment Rule

```typescript
// POST /api/v1/admin/projects/assignments/rules
// Description: Create automatic user assignment rule
// Authentication: Required (Admin role)

interface AssignmentRuleCreate {
  project_id: string;
  rule_type: 'user_tier' | 'subscription' | 'manual';
  conditions: Record<string, any>;
  priority: number;
  is_active: boolean;
}

const createAssignmentRule = async (
  data: AssignmentRuleCreate
): Promise<AssignmentRuleResponse> => {
  const response = await api.post('/api/v1/admin/projects/assignments/rules', data);
  return response.data;
};

// Example Request:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "rule_type": "subscription",
  "conditions": {
    "subscription_tier": "PRO",
    "min_tier": "PRO"
  },
  "priority": 10,
  "is_active": true
}
```

#### 9. List Assignment Rules

```typescript
// GET /api/v1/admin/projects/{project_id}/assignments/rules
// Description: Get assignment rules for a project
// Authentication: Required (Admin role)

const listAssignmentRules = async (
  projectId: string
): Promise<AssignmentRuleResponse[]> => {
  const response = await api.get(
    `/api/v1/admin/projects/${projectId}/assignments/rules`
  );
  return response.data;
};
```

#### 10. Update Assignment Rule

```typescript
// PATCH /api/v1/admin/projects/assignments/rules/{rule_id}
// Description: Update assignment rule
// Authentication: Required (Admin role)

const updateAssignmentRule = async (
  ruleId: string,
  updates: Partial<AssignmentRuleCreate>
): Promise<AssignmentRuleResponse> => {
  const response = await api.patch(
    `/api/v1/admin/projects/assignments/rules/${ruleId}`,
    updates
  );
  return response.data;
};
```

---

### User Assignments

#### 11. Assign User to Project

```typescript
// POST /api/v1/admin/projects/{project_id}/users
// Description: Manually assign user to project
// Authentication: Required (Admin role)

interface UserAssignmentCreate {
  user_id: string;
  role?: 'member' | 'contributor' | 'admin';
  expiry_date?: string; // ISO 8601
}

const assignUserToProject = async (
  projectId: string,
  data: UserAssignmentCreate
): Promise<UserAssignmentResponse> => {
  const response = await api.post(
    `/api/v1/admin/projects/${projectId}/users`,
    data
  );
  return response.data;
};
```

#### 12. List Project Users

```typescript
// GET /api/v1/admin/projects/{project_id}/users
// Description: Get all users assigned to project
// Authentication: Required (Admin role)

const listProjectUsers = async (
  projectId: string
): Promise<UserAssignmentResponse[]> => {
  const response = await api.get(`/api/v1/admin/projects/${projectId}/users`);
  return response.data;
};
```

#### 13. Search Projects

```typescript
// GET /api/v1/admin/projects/search?q=yield
// Description: Search projects by name, description, or slug
// Authentication: Required (Admin role)

const searchProjects = async (query: string): Promise<ProjectResponse[]> => {
  const response = await api.get('/api/v1/admin/projects/search', {
    params: { q: query }
  });
  return response.data;
};
```

---

## 🔗 React Hooks

### useAdminProjects Hook

```typescript
export function useAdminProjects(filters?: ProjectFilters) {
  const queryClient = useQueryClient();
  
  const { data: projects, isLoading } = useQuery({
    queryKey: ['admin-projects', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/projects/', {
        params: filters
      });
      return response.data;
    },
  });
  
  const createProject = useMutation({
    mutationFn: async (data: ProjectCreate) => {
      const response = await api.post('/api/v1/admin/projects/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-projects'] });
      toast.success('Project created successfully');
    },
  });
  
  const updateProject = useMutation({
    mutationFn: async ({ id, updates }: { id: string; updates: ProjectUpdate }) => {
      const response = await api.patch(`/api/v1/admin/projects/${id}`, updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-projects'] });
      toast.success('Project updated successfully');
    },
  });
  
  const deleteProject = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/admin/projects/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-projects'] });
      toast.success('Project deleted successfully');
    },
  });
  
  return {
    projects: projects || [],
    isLoading,
    createProject: createProject.mutate,
    updateProject: updateProject.mutate,
    deleteProject: deleteProject.mutate,
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin Projects*  
*Backend Status: ✅ 100% Implemented (13 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*

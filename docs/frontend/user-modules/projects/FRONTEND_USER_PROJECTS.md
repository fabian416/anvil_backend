# FRONTEND_USER_PROJECTS

## User Projects Module

**User Type:** Authenticated User  
**Module:** Projects - Project Selection & Management  
**Route:** `/projects`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**User Projects** - Project Selection & Workspace Management

### Description
User-facing project management for selecting active workspaces, browsing available projects, and managing project assignments.

### Key Capabilities
- ✅ View assigned projects
- ✅ Browse available projects
- ✅ Select active project
- ✅ Join public projects
- ✅ Get project details by slug

---

## 🔌 API Integration

### 1. Get User Projects

```typescript
// GET /api/v1/projects/
interface UserProjectsResponse {
  assigned_projects: ProjectSummary[];
  active_project_id?: string;
}

const getUserProjects = async (): Promise<UserProjectsResponse> => {
  const response = await api.get('/api/v1/projects/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 2. List Available Projects

```typescript
// GET /api/v1/projects/available
const listAvailableProjects = async (): Promise<ProjectSummary[]> => {
  const response = await api.get('/api/v1/projects/available', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 3. Select Project

```typescript
// POST /api/v1/projects/{project_id}/select
const selectProject = async (projectId: string): Promise<void> => {
  await api.post(`/api/v1/projects/${projectId}/select`, {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
};
```

### 4. Join Project

```typescript
// POST /api/v1/projects/{project_id}/join
const joinProject = async (projectId: string): Promise<void> => {
  await api.post(`/api/v1/projects/${projectId}/join`, {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
};
```

### 5. Get Project by Slug

```typescript
// GET /api/v1/projects/{slug}
const getProjectBySlug = async (slug: string): Promise<ProjectSummary> => {
  const response = await api.get(`/api/v1/projects/${slug}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

---

## 🔗 React Hooks

```typescript
export function useUserProjects() {
  return useQuery({
    queryKey: ['user', 'projects'],
    queryFn: getUserProjects,
  });
}

export function useAvailableProjects() {
  return useQuery({
    queryKey: ['projects', 'available'],
    queryFn: listAvailableProjects,
  });
}

export function useSelectProject() {
  return useMutation({
    mutationFn: selectProject,
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: User Projects*  
*Backend Status: ✅ 100% Implemented (5 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*

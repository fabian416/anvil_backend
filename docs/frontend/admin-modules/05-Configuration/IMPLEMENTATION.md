# Configuration Module Implementation

> **Complete TypeScript/React Implementation for Configuration Module**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **Configuration** module manages global application settings and policy configurations that affect the entire platform. It provides controls for projects, feature flags, and Privy policy management.

### Key Capabilities
1. **Projects**: Feature flags, global maintenance mode, project CRUD, knowledge documents, assignment rules, user assignments
2. **Policy Management**: List, create, update Privy policies, manage policy rules

### Business Value
- **Global Control**: Configure platform-wide settings
- **Feature Management**: Enable/disable features for all users
- **Policy Control**: Manage wallet security policies
- **Project Management**: Configure AI projects and knowledge bases

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Admins need to configure global settings safely.

**Root Cause Analysis**:
- **Safety**: Global changes affect all users
- **Solution**: Caution indicators, confirmation modals, audit trail, impact warnings

**Design Decisions**:
1. **Caution**: UI should emphasize that changes affect ALL users
2. **Confirmation**: Require explicit confirmation for global changes
3. **Audit Trail**: Log all configuration changes
4. **Impact Warnings**: Show what will be affected by changes

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Nested Resource Endpoints** | Flat Structure | Organization vs. URL Length | Nested endpoints improve organization, but create longer URLs |
| **Policy Integration with Privy** | Internal Only | External Dependency vs. Feature Richness | Privy integration provides advanced features, but adds external dependency |
| **Asynchronous Document Processing** | Synchronous | Performance vs. Feedback | Async processing improves response time, but requires status polling |
| **Assignment Rules System** | Manual Only | Automation vs. Complexity | Rules enable automatic assignment, but require careful configuration |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│              Configuration                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Tabs: [Projects] [Policies]                       │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Projects                                          │  │
│  │ ┌──────────────┐  ┌──────────────┐               │  │
│  │ │ Project Card │  │ Project Card │               │  │
│  │ │ DeFi Analytics│ │ Trading Bot  │               │  │
│  │ │ ✅ Active    │  │ ✅ Active    │               │  │
│  │ │ [Edit]       │  │ [Edit]       │               │  │
│  │ └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Policies                                          │  │
│  │ ┌──────────────┐                                  │  │
│  │ │ Policy Table │                                  │  │
│  │ │ Name │ Rules │ Actions                          │  │
│  │ └──────────────┘                                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Color Palette
- **Active**: `#10B981` (Green)
- **Inactive**: `#6B7280` (Gray)
- **Warning**: `#F59E0B` (Amber) - Global impact warnings
- **Error**: `#EF4444` (Red) - Errors
- **Info**: `#3B82F6` (Blue) - Informational

#### Component Specifications

##### Global Impact Warning Component
```typescript
interface GlobalImpactWarningProps {
  message: string;
  affectedCount?: number;
}

export const GlobalImpactWarning: React.FC<GlobalImpactWarningProps> = ({
  message,
  affectedCount,
}) => {
  return (
    <div className="p-4 bg-amber-50 border-2 border-amber-200 rounded-lg mb-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-amber-800">Global Impact Warning</h3>
          <p className="mt-1 text-sm text-amber-700">{message}</p>
          {affectedCount !== undefined && (
            <p className="mt-1 text-sm text-amber-700">
              This change will affect <strong>{affectedCount.toLocaleString()}</strong> users.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
```

##### Project Card Component
```typescript
interface ProjectCardProps {
  project: Project;
  onEdit: (projectId: string) => void;
  onDelete: (projectId: string) => void;
  onActivate: (projectId: string) => void;
  onDeactivate: (projectId: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onEdit,
  onDelete,
  onActivate,
  onDeactivate,
}) => {
  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-6 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{project.name}</h3>
          <p className="text-sm text-gray-500">{project.description || 'No description'}</p>
        </div>
        <StatusBadge
          status={project.status === 'active' ? 'active' : 'inactive'}
        />
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Visibility:</span>
          <span className="font-medium capitalize">{project.visibility}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Max Users:</span>
          <span className="font-medium">{project.max_users || 'Unlimited'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Chains:</span>
          <span className="font-medium">{project.enabled_chains.length}</span>
        </div>
      </div>

      <div className="flex space-x-2">
        <button
          onClick={() => onEdit(project.id)}
          className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded text-sm"
        >
          Edit
        </button>
        {project.status === 'active' ? (
          <button
            onClick={() => onDeactivate(project.id)}
            className="px-4 py-2 bg-amber-100 hover:bg-amber-200 rounded text-sm"
          >
            Deactivate
          </button>
        ) : (
          <button
            onClick={() => onActivate(project.id)}
            className="px-4 py-2 bg-green-100 hover:bg-green-200 rounded text-sm"
          >
            Activate
          </button>
        )}
      </div>
    </div>
  );
};
```

##### Policy Editor Component
```typescript
interface PolicyEditorProps {
  policy: Policy | null;
  onSave: (policy: Policy) => void;
  onCancel: () => void;
}

export const PolicyEditor: React.FC<PolicyEditorProps> = ({
  policy,
  onSave,
  onCancel,
}) => {
  const [name, setName] = useState(policy?.name || '');
  const [description, setDescription] = useState(policy?.description || '');
  const [rules, setRules] = useState<PolicyRule[]>(policy?.rules || []);

  const handleAddRule = () => {
    setRules([...rules, { rule_type: '', rule_config: {}, priority: rules.length + 1 }]);
  };

  const handleRemoveRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
      <h3 className="text-lg font-semibold mb-4">
        {policy ? 'Edit Policy' : 'Create Policy'}
      </h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Policy Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            rows={3}
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Rules
            </label>
            <button
              onClick={handleAddRule}
              className="px-3 py-1 bg-blue-100 hover:bg-blue-200 rounded text-sm"
            >
              Add Rule
            </button>
          </div>
          {rules.map((rule, index) => (
            <PolicyRuleEditor
              key={index}
              rule={rule}
              index={index}
              onUpdate={(updatedRule) => {
                const newRules = [...rules];
                newRules[index] = updatedRule;
                setRules(newRules);
              }}
              onRemove={() => handleRemoveRule(index)}
            />
          ))}
        </div>

        <div className="flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave({ id: policy?.id || '', name, description, rules })}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Responsive Breakpoints

**Mobile** (< 640px):
- Single column layout
- Stacked project cards
- Bottom sheet for forms
- Tab navigation at bottom

**Tablet** (640px - 1024px):
- Two-column project grid
- Side panel for forms
- Tab navigation at top

**Desktop** (> 1024px):
- Three-column project grid
- Sidebar for filters
- Modal for forms
- Tab navigation at top

### Accessibility Requirements

1. **Screen Readers**:
   - Announce global impact warnings
   - Describe policy rules
   - Label all form inputs
   - Announce configuration changes

2. **Keyboard Navigation**:
   - Tab through all cards
   - Enter to edit
   - Escape to close modals
   - Arrow keys for navigation

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Warning indicators: 3:1 minimum
   - Form inputs: 4.5:1

---

## 🔌 API Endpoints

See `05-Configuration/API.md` for complete API documentation.

### Key Endpoints Summary

1. **Projects**: `GET /api/admin/projects`, `POST /api/admin/projects`, `PATCH /api/admin/projects/{project_id}`
2. **Knowledge Documents**: `GET /api/admin/projects/{project_id}/knowledge/documents`, `POST /api/admin/projects/{project_id}/knowledge`
3. **Assignment Rules**: `GET /api/admin/projects/{project_id}/assignment-rules`, `POST /api/admin/projects/{project_id}/assignment-rules`
4. **User Assignments**: `GET /api/admin/projects/{project_id}/assignments`, `POST /api/admin/projects/{project_id}/assignments`
5. **Policies**: `GET /api/admin/policies/`, `POST /api/admin/policies/`, `PATCH /api/admin/policies/{policy_id}`
6. **Policy Rules**: `POST /api/admin/policies/{policy_id}/rules`, `PATCH /api/admin/policies/{policy_id}/rules/{rule_id}`

---

## 🔄 User Flows & Use Cases

### Use Case 1: Create Project

**Actor**: Admin User  
**Goal**: Create a new AI project with configuration  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to `/admin/configuration` → Projects tab
2. **Initial State**: 
   - Projects list loads
   - Show "Create Project" button
3. **User Action**: User clicks "Create Project"
4. **System Response**:
   - Open create project modal
   - Show form with all fields
   - Display global impact warning
5. **User Action**: User fills form (name, description, enabled protocols, chains, etc.)
6. **System Response**:
   - Validate form
   - Show impact preview
7. **User Action**: User submits form
8. **System Response**:
   - Show confirmation modal (global impact warning)
   - Request explicit confirmation
9. **User Action**: User confirms
10. **System Response**:
    - Call `POST /api/admin/projects`
    - Show loading state
11. **System Response**:
    - On success: Add project to list, show success toast
    - On error: Show error message

#### Success Criteria
- [ ] Project is created successfully
- [ ] Global impact warning is displayed
- [ ] Form validation works
- [ ] Confirmation prevents mistakes

---

### Use Case 2: Create Policy

**Actor**: Admin User  
**Goal**: Create a new Privy policy for wallet security  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to `/admin/configuration` → Policies tab
2. **Initial State**: 
   - Policies list loads
   - Show "Create Policy" button
3. **User Action**: User clicks "Create Policy"
4. **System Response**:
   - Open policy editor
   - Show form with name, description, rules
5. **User Action**: User fills form and adds rules
6. **System Response**:
   - Validate form
   - Validate rule configuration
7. **User Action**: User submits form
8. **System Response**:
   - Call `POST /api/admin/policies/`
   - Show loading state
9. **System Response**:
   - On success: Add policy to list, show success toast
   - On error: Show error message (especially Privy API errors)

#### Success Criteria
- [ ] Policy is created successfully
- [ ] Form validation works
- [ ] Privy API errors are handled
- [ ] Policy appears in list

---

### Use Case 3: Process Knowledge Document

**Actor**: Admin User  
**Goal**: Process a knowledge document for a project  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to project details → Knowledge Documents
2. **Initial State**: 
   - Documents list loads
   - Show document with "Process" button
3. **User Action**: User clicks "Process Document"
4. **System Response**:
   - Call `POST /api/admin/projects/{project_id}/knowledge/{doc_id}/process`
   - Show loading state
   - Return 202 Accepted
5. **System Response**:
   - Show processing status indicator
   - Poll for status updates
6. **System Response**:
   - On completion: Update status, show success
   - On error: Show error message

#### Success Criteria
- [ ] Processing starts successfully
- [ ] Status updates are visible
- [ ] Completion is indicated
- [ ] Errors are handled

---

## 📁 File Structure

```
src/modules/admin/configuration/
├── Configuration.tsx
├── Configuration.types.ts
├── Configuration.hooks.ts
├── Configuration.service.ts
├── components/
│   ├── GlobalImpactWarning.tsx
│   ├── ProjectCard.tsx
│   ├── ProjectForm.tsx
│   ├── PolicyCard.tsx
│   ├── PolicyEditor.tsx
│   ├── PolicyRuleEditor.tsx
│   ├── KnowledgeDocumentList.tsx
│   ├── AssignmentRuleList.tsx
│   └── ConfirmationModal.tsx
├── tabs/
│   ├── ProjectsTab.tsx
│   └── PoliciesTab.tsx
├── hooks/
│   ├── useProjects.ts
│   ├── useProjectDetails.ts
│   ├── useKnowledgeDocuments.ts
│   ├── useAssignmentRules.ts
│   ├── usePolicies.ts
│   └── usePolicyRules.ts
├── services/
│   ├── project.service.ts
│   └── policy.service.ts
└── __tests__/
    ├── Configuration.test.tsx
    ├── ProjectCard.test.tsx
    └── services.test.ts
```

## 🔑 Key Implementation Files

### 1. Configuration Module

#### `Configuration.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type {
  ProjectResponse,
  ProjectCreate,
  ProjectUpdate,
  KnowledgeDocumentResponse,
  KnowledgeDocumentCreate,
  AssignmentRuleResponse,
  AssignmentRuleCreate,
  UserAssignmentResponse,
  ListPoliciesResponse,
  GetPolicyResponse,
  CreatePolicyRequest,
  UpdatePolicyRequestBody,
  PolicyRuleRequestBody,
} from './Configuration.types';

export const configurationService = {
  // Projects
  async listProjects(params?: {
    status?: string;
    visibility?: string;
    is_featured?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<ProjectResponse[]> {
    const response = await apiClient.get<ProjectResponse[]>(
      '/api/admin/projects',
      { params }
    );
    return response.data;
  },

  async createProject(data: ProjectCreate): Promise<ProjectResponse> {
    const response = await apiClient.post<ProjectResponse>(
      '/api/admin/projects',
      data
    );
    return response.data;
  },

  async getProject(projectId: string): Promise<ProjectResponse> {
    const response = await apiClient.get<ProjectResponse>(
      `/api/admin/projects/${projectId}`
    );
    return response.data;
  },

  async updateProject(
    projectId: string,
    data: ProjectUpdate
  ): Promise<ProjectResponse> {
    const response = await apiClient.patch<ProjectResponse>(
      `/api/admin/projects/${projectId}`,
      data
    );
    return response.data;
  },

  async deleteProject(projectId: string): Promise<void> {
    await apiClient.delete(`/api/admin/projects/${projectId}`);
  },

  async activateProject(projectId: string): Promise<void> {
    await apiClient.post(`/api/admin/projects/${projectId}/activate`);
  },

  async deactivateProject(projectId: string): Promise<void> {
    await apiClient.post(`/api/admin/projects/${projectId}/deactivate`);
  },

  // Knowledge Documents
  async listKnowledgeDocuments(projectId: string): Promise<KnowledgeDocumentResponse[]> {
    const response = await apiClient.get<KnowledgeDocumentResponse[]>(
      `/api/admin/projects/${projectId}/knowledge/documents`
    );
    return response.data;
  },

  async createKnowledgeDocument(
    projectId: string,
    data: KnowledgeDocumentCreate
  ): Promise<KnowledgeDocumentResponse> {
    const response = await apiClient.post<KnowledgeDocumentResponse>(
      `/api/admin/projects/${projectId}/knowledge`,
      data
    );
    return response.data;
  },

  async processKnowledgeDocument(
    projectId: string,
    docId: string
  ): Promise<void> {
    await apiClient.post(
      `/api/admin/projects/${projectId}/knowledge/${docId}/process`
    );
  },

  // Assignment Rules
  async listAssignmentRules(projectId: string): Promise<AssignmentRuleResponse[]> {
    const response = await apiClient.get<AssignmentRuleResponse[]>(
      `/api/admin/projects/${projectId}/assignment-rules`
    );
    return response.data;
  },

  async createAssignmentRule(
    projectId: string,
    data: AssignmentRuleCreate
  ): Promise<AssignmentRuleResponse> {
    const response = await apiClient.post<AssignmentRuleResponse>(
      `/api/admin/projects/${projectId}/assignment-rules`,
      data
    );
    return response.data;
  },

  // Policies
  async listPolicies(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ListPoliciesResponse> {
    const response = await apiClient.get<ListPoliciesResponse>(
      '/api/admin/policies/',
      { params }
    );
    return response.data;
  },

  async getPolicy(policyId: string): Promise<GetPolicyResponse> {
    const response = await apiClient.get<GetPolicyResponse>(
      `/api/admin/policies/${policyId}`
    );
    return response.data;
  },

  async createPolicy(data: CreatePolicyRequest): Promise<CreatePolicyResponse> {
    const response = await apiClient.post<CreatePolicyResponse>(
      '/api/admin/policies/',
      data
    );
    return response.data;
  },

  async updatePolicy(
    policyId: string,
    data: UpdatePolicyRequestBody
  ): Promise<UpdatePolicyResponse> {
    const response = await apiClient.patch<UpdatePolicyResponse>(
      `/api/admin/policies/${policyId}`,
      data
    );
    return response.data;
  },

  // Policy Rules
  async createPolicyRule(
    policyId: string,
    data: PolicyRuleRequestBody
  ): Promise<PolicyRuleResponse> {
    const response = await apiClient.post<PolicyRuleResponse>(
      `/api/admin/policies/${policyId}/rules`,
      data
    );
    return response.data;
  },

  async updatePolicyRule(
    policyId: string,
    ruleId: string,
    data: PolicyRuleRequestBody
  ): Promise<PolicyRuleResponse> {
    const response = await apiClient.patch<PolicyRuleResponse>(
      `/api/admin/policies/${policyId}/rules/${ruleId}`,
      data
    );
    return response.data;
  },

  async deletePolicyRule(policyId: string, ruleId: string): Promise<void> {
    await apiClient.delete(
      `/api/admin/policies/${policyId}/rules/${ruleId}`
    );
  },
};
```

#### `Configuration.types.ts`
```typescript
export interface ProjectResponse {
  id: string;                            // UUID
  slug: string;
  name: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  banner_url: string | null;
  status: string;
  visibility: string;
  system_prompt: string | null;
  welcome_message: string | null;
  enabled_protocols: string[];
  enabled_chains: string[];
  enabled_tools: string[];
  risk_config: { [key: string]: any } | null;
  max_users: number | null;
  display_order: number;
  is_featured: boolean;
  created_by: string;                    // UUID
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}

export interface Policy {
  id: string;                            // UUID
  name: string;
  description: string | null;
  rules: PolicyRule[];
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}

export interface PolicyRule {
  id: string;                            // UUID
  policy_id: string;                     // UUID
  rule_type: string;
  rule_config: { [key: string]: any };
  priority: number;
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

#### `Configuration.hooks.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { configurationService } from './Configuration.service';

export function useProjects(params?: {
  status?: string;
  visibility?: string;
  is_featured?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['admin', 'projects', params],
    queryFn: () => configurationService.listProjects(params),
    staleTime: 60000, // 1 minute
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProjectCreate) =>
      configurationService.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: ProjectUpdate;
    }) => configurationService.updateProject(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['admin', 'projects', variables.projectId],
      });
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] });
    },
  });
}

export function usePolicies(params?: {
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['admin', 'policies', params],
    queryFn: () => configurationService.listPolicies(params),
    staleTime: 60000, // 1 minute
  });
}

export function useCreatePolicy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePolicyRequest) =>
      configurationService.createPolicy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'policies'] });
    },
  });
}
```

#### `Configuration.tsx`
```typescript
'use client';

import React, { useState } from 'react';
import { ProjectsTab } from './tabs/ProjectsTab';
import { PoliciesTab } from './tabs/PoliciesTab';

type Tab = 'projects' | 'policies';

export const Configuration: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('projects');

  const tabs = [
    { id: 'projects' as Tab, label: 'Projects' },
    { id: 'policies' as Tab, label: 'Policies' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'projects':
        return <ProjectsTab />;
      case 'policies':
        return <PoliciesTab />;
      default:
        return <ProjectsTab />;
    }
  };

  return (
    <div className="configuration-container p-6">
      <h1 className="text-3xl font-bold mb-6">Configuration</h1>

      {/* Global Impact Warning */}
      <GlobalImpactWarning
        message="Changes in this module affect all users. Please review carefully before making changes."
      />

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};
```

## 📝 Complete File List

### Configuration Module
- [ ] `Configuration.tsx` - Main component
- [ ] `Configuration.types.ts` - TypeScript interfaces
- [ ] `Configuration.hooks.ts` - React hooks
- [ ] `Configuration.service.ts` - API service
- [ ] `components/GlobalImpactWarning.tsx` - Global impact warning
- [ ] `components/ProjectCard.tsx` - Project card component
- [ ] `components/ProjectForm.tsx` - Project form component
- [ ] `components/PolicyCard.tsx` - Policy card component
- [ ] `components/PolicyEditor.tsx` - Policy editor component
- [ ] `components/PolicyRuleEditor.tsx` - Policy rule editor
- [ ] `components/KnowledgeDocumentList.tsx` - Knowledge documents list
- [ ] `components/AssignmentRuleList.tsx` - Assignment rules list
- [ ] `components/ConfirmationModal.tsx` - Confirmation modal
- [ ] `tabs/ProjectsTab.tsx` - Projects tab
- [ ] `tabs/PoliciesTab.tsx` - Policies tab
- [ ] `hooks/useProjects.ts` - Projects hook
- [ ] `hooks/useProjectDetails.ts` - Project details hook
- [ ] `hooks/useKnowledgeDocuments.ts` - Knowledge documents hook
- [ ] `hooks/useAssignmentRules.ts` - Assignment rules hook
- [ ] `hooks/usePolicies.ts` - Policies hook
- [ ] `hooks/usePolicyRules.ts` - Policy rules hook
- [ ] `services/project.service.ts` - Project service
- [ ] `services/policy.service.ts` - Policy service
- [ ] `__tests__/Configuration.test.tsx` - Component tests
- [ ] `__tests__/ProjectCard.test.tsx` - Component tests
- [ ] `__tests__/services.test.ts` - Service tests

---

## 🧪 Testing Requirements

### Unit Tests

**Configuration Component**:
- [ ] Renders tab navigation correctly
- [ ] Switches tabs correctly
- [ ] Displays global impact warning
- [ ] Handles loading states
- [ ] Displays error states

**Project Card Component**:
- [ ] Renders project information correctly
- [ ] Displays status badge
- [ ] Triggers edit action
- [ ] Triggers activate/deactivate actions

**Policy Editor Component**:
- [ ] Renders form correctly
- [ ] Handles rule addition/removal
- [ ] Validates form
- [ ] Handles save action

**Services**:
- [ ] Calls correct API endpoints
- [ ] Handles query parameters
- [ ] Parses response correctly
- [ ] Handles errors (401, 403, 404, 502, 503)

### Integration Tests

**Configuration Flow**:
- [ ] Load projects list
- [ ] Create project
- [ ] Update project
- [ ] Activate/deactivate project
- [ ] Manage knowledge documents
- [ ] Create policy
- [ ] Update policy
- [ ] Manage policy rules

### E2E Tests

**Configuration Journey**:
- [ ] Login as admin → View configuration
- [ ] Create project
- [ ] Create policy
- [ ] Handle errors gracefully

### Performance Tests

- [ ] Projects list loads in < 2 seconds
- [ ] Project operations complete in < 1 second
- [ ] Policy operations complete in < 2 seconds
- [ ] Document processing status updates in < 1 second

### Accessibility Tests

- [ ] Screen reader announces global impact warnings
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] All interactive elements are focusable
- [ ] Forms are accessible

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Global Impact Understanding**
   - **Risk**: Admins don't understand global impact
   - **Mitigation**: Global impact warnings, confirmation modals, affected count display
   - **Validation**: User testing with admins

2. **Privy API Dependency**
   - **Risk**: External API failures affect policy operations
   - **Mitigation**: Error handling, retry logic, fallback UI
   - **Validation**: Test with Privy API failures

3. **Asynchronous Processing**
   - **Risk**: Document processing status unclear
   - **Mitigation**: Status polling, progress indicators, notifications
   - **Validation**: Test processing flows

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Policy Validation**
   - **Debt**: Invalid policies cause errors
   - **Cost**: Poor user experience, support burden
   - **Prevention**: Implement client-side validation before API call

2. **No Document Processing Status**
   - **Debt**: Users don't know processing status
   - **Cost**: Confusion, support requests
   - **Prevention**: Implement status polling and notifications

3. **No Assignment Rule Validation**
   - **Debt**: Invalid rules cause assignment failures
   - **Cost**: Users not assigned correctly
   - **Prevention**: Implement rule validation

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ Projects list loads in < 2 seconds (p95)
- ✅ Project operations complete in < 1 second
- ✅ Policy operations complete in < 2 seconds
- ✅ Document processing status updates in < 1 second
- ✅ Error recovery rate > 95%
- ✅ Accessibility score: 100/100 (WCAG 2.1 AA)

**Module-Specific Test Requirements**:
- **Unit Tests**: Component rendering, state management, service functions, form validation
- **Integration Tests**: API integration, project operations, policy operations, Privy API integration
- **E2E Tests**: Complete project creation flow, policy creation flow, document processing flow
- **Performance Tests**: Load with 100+ projects, 50+ policies, large knowledge bases
- **Accessibility Tests**: Screen reader navigation, keyboard shortcuts, color contrast

**Failure Detection & Monitoring**:
- Monitor API response times (alert if p95 > 2s)
- Track error rates (alert if > 1%)
- Alert on Privy API failures (502 errors)
- Monitor project operation success rates
- Track policy operation success rates
- Log all configuration changes for audit trail

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/admin/projects_router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/policies/list_policies.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/policies/create_policy.py`
- **Domain Entities**: `src/app/domain/projects/entities/project.py`
- **API Documentation**: `05-Configuration/API.md`
- **UI/UX Design**: `05-Configuration/UI_UX.md`
- **Related Modules**: 
  - Admin Overview (project metrics)
  - User Management (user assignments)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.

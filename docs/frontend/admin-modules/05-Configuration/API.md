# Configuration API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URLs**: `/api/admin/projects`, `/api/admin/policies`

---

## 📋 Table of Contents

1. [Projects Endpoints](#projects-endpoints)
2. [Policy Management Endpoints](#policy-management-endpoints)
3. [Request/Response Schemas](#requestresponse-schemas)
4. [Error Handling](#error-handling)
5. [API Design Trade-off Analysis](#api-design-trade-off-analysis)

---

## 🏗️ Projects Endpoints

### 1. List Projects

**Method**: `GET`  
**Endpoint**: `/api/admin/projects`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `status` | `string` | No | Filter by status | All statuses |
| `visibility` | `string` | No | Filter by visibility | All visibilities |
| `is_featured` | `boolean` | No | Filter by featured | All projects |
| `limit` | `number` | No | Max results | `50` |
| `offset` | `number` | No | Pagination offset | `0` |

**Valid `limit` Range**: 1-100

#### Response

##### Success Response (200 OK)
```typescript
interface ProjectResponse {
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
```

Returns `ProjectResponse[]`

---

### 2. Create Project

**Method**: `POST`  
**Endpoint**: `/api/admin/projects`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface ProjectCreate {
  slug: string;                          // Required: URL-friendly identifier
  name: string;                           // Required
  description?: string;
  icon?: string;
  color?: string;
  banner_url?: string;
  status?: string;
  visibility?: string;
  system_prompt?: string;
  welcome_message?: string;
  enabled_protocols?: string[];
  enabled_chains?: string[];
  enabled_tools?: string[];
  risk_config?: { [key: string]: any };
  max_users?: number;
  display_order?: number;
  is_featured?: boolean;
}
```

**JSON Example**:
```json
{
  "slug": "defi-analytics",
  "name": "DeFi Analytics",
  "description": "Advanced DeFi analytics and insights",
  "icon": "📊",
  "color": "#3B82F6",
  "status": "active",
  "visibility": "public",
  "enabled_protocols": ["aave", "compound"],
  "enabled_chains": ["ethereum", "polygon"],
  "enabled_tools": ["swap", "stake"],
  "max_users": 1000,
  "display_order": 1,
  "is_featured": true
}
```

#### Response

##### Success Response (201 Created)
Returns `ProjectResponse`

---

### 3. Get Project

**Method**: `GET`  
**Endpoint**: `/api/admin/projects/{project_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (200 OK)
Returns `ProjectResponse`

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `404` | `HTTPException` | Project not found | Show error: "Project not found" |

---

### 4. Update Project

**Method**: `PATCH`  
**Endpoint**: `/api/admin/projects/{project_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

##### Request Body
```typescript
interface ProjectUpdate {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  banner_url?: string;
  system_prompt?: string;
  welcome_message?: string;
  enabled_protocols?: string[];
  enabled_chains?: string[];
  enabled_tools?: string[];
  risk_config?: { [key: string]: any };
  max_users?: number;
  display_order?: number;
  is_featured?: boolean;
}
```

#### Response

##### Success Response (200 OK)
Returns `ProjectResponse`

---

### 5. Delete Project

**Method**: `DELETE`  
**Endpoint**: `/api/admin/projects/{project_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (204 No Content)
No response body

---

### 6. Activate Project

**Method**: `POST`  
**Endpoint**: `/api/admin/projects/{project_id}/activate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (200 OK)
```json
{
  "message": "Project activated",
  "project_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 7. Deactivate Project

**Method**: `POST`  
**Endpoint**: `/api/admin/projects/{project_id}/deactivate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (200 OK)
```json
{
  "message": "Project deactivated",
  "project_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 8. List Knowledge Documents

**Method**: `GET`  
**Endpoint**: `/api/admin/projects/{project_id}/knowledge/documents`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface KnowledgeDocumentResponse {
  id: string;                            // UUID
  knowledge_base_id: string;             // UUID (project_id)
  title: string;
  doc_type: string;
  tags: string[];
  priority: number;
  is_processed: boolean;
  chunk_count: number;
  processing_error: string | null;
  created_at: string;                   // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

Returns `KnowledgeDocumentResponse[]`

---

### 9. Create Knowledge Document

**Method**: `POST`  
**Endpoint**: `/api/admin/projects/{project_id}/knowledge`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

##### Request Body
```typescript
interface KnowledgeDocumentCreate {
  title: string;                         // Required
  doc_type: string;                      // Required
  tags?: string[];
  priority?: number;
}
```

#### Response

##### Success Response (201 Created)
Returns `KnowledgeDocumentResponse`

---

### 10. Get Knowledge Document

**Method**: `GET`  
**Endpoint**: `/api/admin/projects/{project_id}/knowledge/{doc_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |
| `doc_id` | `UUID` | **Yes** | Document identifier |

#### Response

##### Success Response (200 OK)
Returns `KnowledgeDocumentResponse`

---

### 11. Update Knowledge Document

**Method**: `PATCH`  
**Endpoint**: `/api/admin/projects/{project_id}/knowledge/{doc_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |
| `doc_id` | `UUID` | **Yes** | Document identifier |

##### Request Body
```typescript
interface KnowledgeDocumentUpdate {
  title?: string;
  tags?: string[];
  priority?: number;
}
```

#### Response

##### Success Response (200 OK)
Returns `KnowledgeDocumentResponse`

---

### 12. Process Knowledge Document

**Method**: `POST`  
**Endpoint**: `/api/admin/projects/{project_id}/knowledge/{doc_id}/process`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |
| `doc_id` | `UUID` | **Yes** | Document identifier |

#### Response

##### Success Response (202 Accepted)
```json
{
  "message": "Document processing started",
  "doc_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Note**: This is an asynchronous operation.

---

### 13. List Assignment Rules

**Method**: `GET`  
**Endpoint**: `/api/admin/projects/{project_id}/assignment-rules`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface AssignmentRuleResponse {
  id: string;                            // UUID
  project_id: string;                    // UUID
  rule_name: string;
  condition_type: string;
  condition_params: { [key: string]: any };
  priority: number;
  auto_switch: boolean;
  is_active: boolean;
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

Returns `AssignmentRuleResponse[]`

---

### 14. Create Assignment Rule

**Method**: `POST`  
**Endpoint**: `/api/admin/projects/{project_id}/assignment-rules`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

##### Request Body
```typescript
interface AssignmentRuleCreate {
  rule_name: string;                     // Required
  condition_type: string;                 // Required
  condition_params: { [key: string]: any }; // Required
  priority?: number;
  auto_switch?: boolean;
}
```

#### Response

##### Success Response (201 Created)
Returns `AssignmentRuleResponse`

---

### 15. Update Assignment Rule

**Method**: `PATCH`  
**Endpoint**: `/api/admin/projects/{project_id}/assignment-rules/{rule_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |
| `rule_id` | `UUID` | **Yes** | Rule identifier |

##### Request Body
```typescript
interface AssignmentRuleUpdate {
  rule_name?: string;
  condition_params?: { [key: string]: any };
  priority?: number;
  auto_switch?: boolean;
  is_active?: boolean;
}
```

#### Response

##### Success Response (200 OK)
Returns `AssignmentRuleResponse`

---

### 16. List User Assignments

**Method**: `GET`  
**Endpoint**: `/api/admin/projects/{project_id}/assignments`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface UserAssignmentResponse {
  id: string;                            // UUID
  user_id: string;                       // UUID
  project_id: string;                    // UUID
  assignment_type: string;               // "manual" | "rule_based"
  assignment_reason: string | null;
  is_active: boolean;
  assigned_at: string;                   // ISO 8601
  last_active_at: string | null;         // ISO 8601
}
```

Returns `UserAssignmentResponse[]`

---

### 17. Assign User to Project

**Method**: `POST`  
**Endpoint**: `/api/admin/projects/{project_id}/assignments`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project identifier |

##### Request Body
```typescript
interface UserAssignmentCreate {
  user_id: string;                       // UUID, Required
  assignment_reason?: string;
}
```

#### Response

##### Success Response (201 Created)
Returns `UserAssignmentResponse`

---

## 🔐 Policy Management Endpoints

### 18. List Policies

**Method**: `GET`  
**Endpoint**: `/api/admin/policies/`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |
| `offset` | `number` | No | Pagination offset | `0` |

#### Response

##### Success Response (200 OK)
```typescript
interface ListPoliciesResponse {
  policies: Policy[];
  total: number;
  limit: number;
  offset: number;
}

interface Policy {
  id: string;                            // UUID
  name: string;
  description: string | null;
  rules: PolicyRule[];
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

---

### 19. Get Policy

**Method**: `GET`  
**Endpoint**: `/api/admin/policies/{policy_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `policy_id` | `UUID` | **Yes** | Policy identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface GetPolicyResponse {
  id: string;                            // UUID
  name: string;
  description: string | null;
  rules: PolicyRule[];
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

---

### 20. Create Policy

**Method**: `POST`  
**Endpoint**: `/api/admin/policies/`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Request Body
```typescript
interface CreatePolicyRequest {
  name: string;                          // Required
  description?: string;
  rules?: PolicyRuleCreate[];
}

interface PolicyRuleCreate {
  rule_type: string;                     // Required
  rule_config: { [key: string]: any };   // Required
  priority?: number;
}
```

**JSON Example**:
```json
{
  "name": "High Security Policy",
  "description": "Strict security requirements",
  "rules": [
    {
      "rule_type": "max_transaction_amount",
      "rule_config": {
        "max_amount_usd": 10000
      },
      "priority": 1
    }
  ]
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface CreatePolicyResponse {
  id: string;                            // UUID
  name: string;
  description: string | null;
  rules: PolicyRule[];
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

---

### 21. Update Policy

**Method**: `PATCH`  
**Endpoint**: `/api/admin/policies/{policy_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `policy_id` | `UUID` | **Yes** | Policy identifier |

##### Request Body
```typescript
interface UpdatePolicyRequestBody {
  name?: string;
  description?: string;
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface UpdatePolicyResponse {
  id: string;                            // UUID
  name: string;
  description: string | null;
  updated_at: string;                    // ISO 8601
}
```

---

### 22. Create Policy Rule

**Method**: `POST`  
**Endpoint**: `/api/admin/policies/{policy_id}/rules`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `policy_id` | `UUID` | **Yes** | Policy identifier |

##### Request Body
```typescript
interface PolicyRuleRequestBody {
  rule_type: string;                     // Required
  rule_config: { [key: string]: any };   // Required
  priority?: number;
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface PolicyRuleResponse {
  id: string;                            // UUID
  policy_id: string;                     // UUID
  rule_type: string;
  rule_config: { [key: string]: any };
  priority: number;
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}
```

---

### 23. Update Policy Rule

**Method**: `PATCH`  
**Endpoint**: `/api/admin/policies/{policy_id}/rules/{rule_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `policy_id` | `UUID` | **Yes** | Policy identifier |
| `rule_id` | `UUID` | **Yes** | Rule identifier |

##### Request Body
```typescript
interface PolicyRuleRequestBody {
  rule_config?: { [key: string]: any };
  priority?: number;
}
```

#### Response

##### Success Response (200 OK)
Returns `PolicyRuleResponse`

---

### 24. Delete Policy Rule

**Method**: `DELETE`  
**Endpoint**: `/api/admin/policies/{policy_id}/rules/{rule_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `policy_id` | `UUID` | **Yes** | Policy identifier |
| `rule_id` | `UUID` | **Yes** | Rule identifier |

#### Response

##### Success Response (204 No Content)
No response body

---

## 📝 Request/Response Schemas

### Complete TypeScript Interfaces

See individual endpoint sections above for detailed schemas.

### Common Types

```typescript
// Policy rule
interface PolicyRule {
  id: string;                            // UUID
  policy_id: string;                     // UUID
  rule_type: string;
  rule_config: { [key: string]: any };
  priority: number;
  created_at: string;                    // ISO 8601
  updated_at: string;                    // ISO 8601
}

// Error response format
interface ErrorResponse {
  detail: string;
}
```

---

## ⚠️ Error Handling

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Authorization Errors (403)**
   - Not admin user
   - **Action**: Show error: "Admin access required"

3. **Validation Errors (400)**
   - Invalid project data
   - Invalid policy data
   - **Action**: Show inline field errors

4. **Not Found Errors (404)**
   - Project not found
   - Policy not found
   - Rule not found
   - **Action**: Show error: "Resource not found"

5. **Service Unavailable (503)**
   - Backend service down
   - Privy API error (for policies)
   - **Action**: Show error message + Retry button

6. **Bad Gateway (502)**
   - Privy API error (for policy operations)
   - **Action**: Show error: "Unable to connect to Privy" + Retry

### Error Handling Summary

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid parameters | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `PolicyNotFoundError` | Policy not found | Show error: "Policy not found" |
| `404` | `HTTPException` | Project not found | Show error: "Project not found" |
| `502` | `PolicyQueryError` | Privy API error | Show error: "Unable to connect to Privy" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

## 🔐 Authentication

All endpoints require:
- **Bearer Token**: Admin JWT token in `Authorization` header
- **Admin Role**: User must have admin privileges

**Header Format**:
```http
Authorization: Bearer {jwt_token}
```

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Nested Resource Endpoints** | Flat Structure | Organization vs. URL Length | Nested endpoints (e.g., `/projects/{id}/knowledge`) improve organization, but create longer URLs |
| **Policy Integration with Privy** | Internal Only | External Dependency vs. Feature Richness | Privy integration provides advanced features, but adds external dependency |
| **Asynchronous Document Processing** | Synchronous | Performance vs. Feedback | Async processing improves response time, but requires status polling |
| **Assignment Rules System** | Manual Only | Automation vs. Complexity | Rules enable automatic assignment, but require careful configuration |

### Risk Assessment

**Cognitive Limitations:**
- Nested endpoints may be confusing for some admins
- Policy configuration requires understanding of Privy concepts
- Assignment rules may be complex to configure

**Technical Debt:**
- Privy API integration adds external dependency
- Document processing requires background job management
- Assignment rules evaluation may become slow with many rules

**Validation Strategy:**
- ✅ Monitor project creation/update performance
- ✅ Track policy operation success rates
- ✅ Alert on Privy API failures
- ✅ Monitor document processing queue

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/admin/projects_router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/policies/list_policies.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/policies/create_policy.py`
- **Domain Entities**: `src/app/domain/projects/entities/project.py`
- **Frontend Implementation**: `05-Configuration/IMPLEMENTATION.md`
- **UI/UX Design**: `05-Configuration/UI_UX.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready

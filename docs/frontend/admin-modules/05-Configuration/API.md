# Configuration API Documentation

> **Complete API Documentation**  
> **Base URLs**: `/api/admin/projects`, `/api/admin/policies`

---

## 🏗️ Projects Endpoints

### Projects
- **GET** `/api/admin/projects` - List projects
- **POST** `/api/admin/projects` - Create project
- **GET** `/api/admin/projects/{project_id}` - Get project
- **PATCH** `/api/admin/projects/{project_id}` - Update project
- **DELETE** `/api/admin/projects/{project_id}` - Delete project
- **POST** `/api/admin/projects/{project_id}/activate` - Activate project
- **POST** `/api/admin/projects/{project_id}/deactivate` - Deactivate project

### Knowledge Documents
- **GET** `/api/admin/projects/{project_id}/knowledge` - List documents
- **POST** `/api/admin/projects/{project_id}/knowledge` - Create document
- **GET** `/api/admin/projects/{project_id}/knowledge/{doc_id}` - Get document
- **PATCH** `/api/admin/projects/{project_id}/knowledge/{doc_id}` - Update document
- **POST** `/api/admin/projects/{project_id}/knowledge/{doc_id}/process` - Process document

### Assignment Rules
- **GET** `/api/admin/projects/{project_id}/assignments/rules` - List rules
- **POST** `/api/admin/projects/{project_id}/assignments/rules` - Create rule
- **PATCH** `/api/admin/projects/{project_id}/assignments/rules/{rule_id}` - Update rule
- **GET** `/api/admin/projects/{project_id}/assignments/users` - List user assignments

---

## 🔐 Policy Management Endpoints

### Policies
- **GET** `/api/admin/policies/` - List policies
- **GET** `/api/admin/policies/{policy_id}` - Get policy
- **POST** `/api/admin/policies/` - Create policy
- **PATCH** `/api/admin/policies/{policy_id}` - Update policy

### Policy Rules
- **POST** `/api/admin/policies/{policy_id}/rules` - Create rule
- **PATCH** `/api/admin/policies/{policy_id}/rules/{rule_id}` - Update rule
- **DELETE** `/api/admin/policies/{policy_id}/rules/{rule_id}` - Delete rule

---

## ⚠️ Error Handling

| Status | Error Code | Description |
|--------|------------|-------------|
| `401` | `AuthenticationError` | Not authenticated |
| `403` | `AuthorizationError` | Not authorized |
| `404` | `PolicyNotFoundError` | Policy not found |
| `502` | `PolicyQueryError` | Privy API error |
| `503` | `DataMapperError` | Service unavailable |

---

## 🔐 Authentication

All endpoints require admin authentication with Bearer token.

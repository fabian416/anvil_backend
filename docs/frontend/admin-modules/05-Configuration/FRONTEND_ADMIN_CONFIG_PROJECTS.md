# Module: Project Configuration

**Route**: `/admin/configuration/projects`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/configuration/projects`

## 1. Overview
Manages AI projects and their configurations. Projects define feature flags, global maintenance mode, knowledge documents, assignment rules, and user assignments. Changes affect all users, so caution and confirmation are required.

## 2. API Contract

### List Projects
**Endpoint**: `GET /api/admin/projects`  
**Query Params**:
- `status` (string, optional): Filter by status.
- `visibility` (string, optional): Filter by visibility.
- `is_featured` (boolean, optional): Filter by featured status.
- `limit` (number, optional): Max results (Default: 50, Max: 100).
- `offset` (number, optional): Pagination offset (Default: 0).

#### Response Body (`ProjectResponse[]`)
Array of project objects.

**ProjectResponse Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Project UUID |
| `slug` | `string` | URL-friendly identifier |
| `name` | `string` | Project name |
| `description` | `string \| null` | Project description |
| `icon` | `string \| null` | Icon identifier |
| `color` | `string \| null` | Color hex code |
| `banner_url` | `string \| null` | Banner image URL |
| `status` | `string` | Project status |
| `visibility` | `string` | Visibility setting |
| `system_prompt` | `string \| null` | System prompt |
| `welcome_message` | `string \| null` | Welcome message |
| `enabled_protocols` | `string[]` | Enabled protocols |
| `enabled_chains` | `string[]` | Enabled chains |
| `enabled_tools` | `string[]` | Enabled tools |
| `risk_config` | `{ [key: string]: any } \| null` | Risk configuration |
| `max_users` | `number \| null` | Maximum users or null for unlimited |
| `display_order` | `number` | Display order |
| `is_featured` | `boolean` | Whether project is featured |
| `created_by` | `string` | Creator UUID |
| `created_at` | `string` | ISO 8601 creation timestamp |
| `updated_at` | `string` | ISO 8601 update timestamp |

**JSON Example**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "slug": "defi-analytics",
    "name": "DeFi Analytics",
    "description": "Advanced DeFi analytics and insights",
    "icon": "📊",
    "color": "#3B82F6",
    "banner_url": "https://example.com/banner.jpg",
    "status": "active",
    "visibility": "public",
    "system_prompt": "You are a DeFi analytics assistant...",
    "welcome_message": "Welcome to DeFi Analytics!",
    "enabled_protocols": ["aave", "compound"],
    "enabled_chains": ["ethereum", "polygon"],
    "enabled_tools": ["swap", "stake"],
    "risk_config": {"max_slippage": 0.05},
    "max_users": 1000,
    "display_order": 1,
    "is_featured": true,
    "created_by": "660e8400-e29b-41d4-a716-446655440001",
    "created_at": "2023-10-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
]
```

### Create Project
**Endpoint**: `POST /api/admin/projects`  
**Query Params**: None

#### Request Body (`ProjectCreate`)
| Field | Type | Description |
|---|---|---|
| `slug` | `string` | URL-friendly identifier (required) |
| `name` | `string` | Project name (required) |
| `description` | `string` | Optional: Project description |
| `icon` | `string` | Optional: Icon identifier |
| `color` | `string` | Optional: Color hex code |
| `banner_url` | `string` | Optional: Banner image URL |
| `status` | `string` | Optional: Project status |
| `visibility` | `string` | Optional: Visibility setting |
| `system_prompt` | `string` | Optional: System prompt |
| `welcome_message` | `string` | Optional: Welcome message |
| `enabled_protocols` | `string[]` | Optional: Enabled protocols |
| `enabled_chains` | `string[]` | Optional: Enabled chains |
| `enabled_tools` | `string[]` | Optional: Enabled tools |
| `risk_config` | `{ [key: string]: any }` | Optional: Risk configuration |
| `max_users` | `number` | Optional: Maximum users |
| `display_order` | `number` | Optional: Display order |
| `is_featured` | `boolean` | Optional: Whether project is featured |

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

#### Response Body (`ProjectResponse`)
Returns created project object.

### Get Project
**Endpoint**: `GET /api/admin/projects/{project_id}`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response Body (`ProjectResponse`)
Returns project object.

### Update Project
**Endpoint**: `PATCH /api/admin/projects/{project_id}`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Request Body (`ProjectUpdate`)
Same fields as `ProjectCreate`, all optional.

#### Response Body (`ProjectResponse`)
Returns updated project object.

### Delete Project
**Endpoint**: `DELETE /api/admin/projects/{project_id}`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response
`204 No Content` - No response body

### Activate Project
**Endpoint**: `POST /api/admin/projects/{project_id}/activate`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response
`200 OK` - Returns success message

### Deactivate Project
**Endpoint**: `POST /api/admin/projects/{project_id}/deactivate`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response
`200 OK` - Returns success message

### List Knowledge Documents
**Endpoint**: `GET /api/admin/projects/{project_id}/knowledge/documents`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response Body (`KnowledgeDocumentResponse[]`)
Array of knowledge document objects.

**KnowledgeDocumentResponse Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Document UUID |
| `knowledge_base_id` | `string` | Knowledge base UUID (project_id) |
| `title` | `string` | Document title |
| `doc_type` | `string` | Document type |
| `tags` | `string[]` | Document tags |
| `priority` | `number` | Priority |
| `is_processed` | `boolean` | Whether document is processed |
| `chunk_count` | `number` | Number of chunks |
| `processing_error` | `string \| null` | Processing error or null |
| `created_at` | `string` | ISO 8601 creation timestamp |
| `updated_at` | `string` | ISO 8601 update timestamp |

### Create Knowledge Document
**Endpoint**: `POST /api/admin/projects/{project_id}/knowledge`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Request Body (`KnowledgeDocumentCreate`)
| Field | Type | Description |
|---|---|---|
| `title` | `string` | Document title (required) |
| `doc_type` | `string` | Document type (required) |
| `tags` | `string[]` | Optional: Document tags |
| `priority` | `number` | Optional: Priority |

#### Response Body (`KnowledgeDocumentResponse`)
Returns created knowledge document object.

### Process Knowledge Document
**Endpoint**: `POST /api/admin/projects/{project_id}/knowledge/{doc_id}/process`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.
- `doc_id` (string, **required**): Document UUID.

#### Response
`202 Accepted` - Processing started asynchronously

### List Assignment Rules
**Endpoint**: `GET /api/admin/projects/{project_id}/assignment-rules`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response Body (`AssignmentRuleResponse[]`)
Array of assignment rule objects.

**AssignmentRuleResponse Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Rule UUID |
| `project_id` | `string` | Project UUID |
| `rule_type` | `string` | Rule type |
| `rule_config` | `{ [key: string]: any }` | Rule configuration |
| `priority` | `number` | Rule priority |
| `is_active` | `boolean` | Whether rule is active |
| `created_at` | `string` | ISO 8601 creation timestamp |

### Create Assignment Rule
**Endpoint**: `POST /api/admin/projects/{project_id}/assignment-rules`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Request Body (`AssignmentRuleCreate`)
| Field | Type | Description |
|---|---|---|
| `rule_type` | `string` | Rule type (required) |
| `rule_config` | `{ [key: string]: any }` | Rule configuration (required) |
| `priority` | `number` | Optional: Priority |
| `is_active` | `boolean` | Optional: Whether rule is active (Default: true) |

### List User Assignments
**Endpoint**: `GET /api/admin/projects/{project_id}/assignments`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Response Body (`UserAssignmentResponse[]`)
Array of user assignment objects.

**UserAssignmentResponse Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Assignment UUID |
| `project_id` | `string` | Project UUID |
| `user_id` | `string` | User UUID |
| `assigned_at` | `string` | ISO 8601 assignment timestamp |
| `assigned_by` | `string` | Assigner UUID |

### Create User Assignment
**Endpoint**: `POST /api/admin/projects/{project_id}/assignments`  
**Path Params**:
- `project_id` (string, **required**): Project UUID.

#### Request Body (`UserAssignmentCreate`)
| Field | Type | Description |
|---|---|---|
| `user_id` | `string` | User UUID (required) |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Project not found | Show error: "Project not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid project configuration" |
| `409` | `DomainConflictError` | Project slug already exists | Show error: "Project slug already exists" |
| `500` | `Exception` | Internal server error | Show error: "Failed to manage project" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useProjects({ status, visibility, is_featured, limit, offset })` hook which fetches `/api/admin/projects`.
2. **Display**:
   - Project cards/table: Display projects array with columns: Name, Status (badge), Visibility, Max Users, Featured, Actions.
   - Status badges: Color-code by status (Active=Green, Inactive=Grey).
   - Featured indicator: Show badge if `is_featured` is true.
3. **Create Project**: On "Create Project" button click:
   - Open create project modal/form.
   - Show global impact warning: "This change affects all users. Please review carefully."
   - Collect all project fields (slug, name, description, enabled protocols/chains/tools, etc.).
   - Validate slug is URL-friendly and unique.
   - On submit, show confirmation modal with global impact warning.
   - Call `POST /api/admin/projects` with request body.
   - On success: Add project to list, show success toast, invalidate query cache.
4. **Update Project**: On "Edit" button click:
   - Open edit modal with current values pre-populated.
   - Show global impact warning.
   - On submit, show confirmation modal.
   - Call `PATCH /api/admin/projects/{project_id}` with request body.
   - On success: Update display, show success toast, invalidate query cache.
5. **Delete Project**: On "Delete" button click:
   - Show confirmation modal with global impact warning: "This will delete the project and affect all assigned users. Are you sure?"
   - On confirm, call `DELETE /api/admin/projects/{project_id}`.
   - On success: Remove from list, show success toast, invalidate query cache.
6. **Activate/Deactivate**: On activate/deactivate button click:
   - Show confirmation modal with global impact warning.
   - Call respective endpoint (`POST /api/admin/projects/{project_id}/activate` or `/deactivate`).
   - On success: Update status, show success toast, invalidate query cache.
7. **Knowledge Documents**: 
   - Navigate to project details → Knowledge Documents section.
   - Call `GET /api/admin/projects/{project_id}/knowledge/documents` to list documents.
   - On "Process Document" click, call `POST /api/admin/projects/{project_id}/knowledge/{doc_id}/process`.
   - Poll for processing status updates (document will have `is_processed` flag).
8. **Assignment Rules**: 
   - Navigate to project details → Assignment Rules section.
   - Call `GET /api/admin/projects/{project_id}/assignment-rules` to list rules.
   - Create/update/delete rules as needed.
9. **User Assignments**: 
   - Navigate to project details → User Assignments section.
   - Call `GET /api/admin/projects/{project_id}/assignments` to list assignments.
   - Create assignments as needed.

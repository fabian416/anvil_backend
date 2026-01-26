# Projects & Knowledge Bases Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Projects & Knowledge Bases system provides APIs for:
1. **Project Management** - CRUD operations for DeFi assistant projects
2. **Knowledge Base Management** - Document upload, processing, RAG retrieval
3. **Assignment Rules** - Auto-assignment logic for users
4. **User Assignments** - Manual and automatic user-project linking
5. **Project Selection** - User-facing project switching

**Base Paths**: 
- Admin: `/api/v1/admin/projects`
- User: `/api/v1/user/projects`

---

## 1. Admin Project Endpoints

### POST /admin/projects

Create a new project.

**Authentication**: Required (Admin)

**Request Body** (`ProjectCreate`):
```json
{
  "slug": "defi-swing-trader",
  "name": "DeFi Swing Trader",
  "description": "Specialized for swing trading strategies",
  "icon": "📈",
  "color": "#4CAF50",
  "banner_url": "https://...",
  "status": "draft",
  "visibility": "public",
  "system_prompt": "You are a DeFi swing trading assistant...",
  "welcome_message": "Welcome to the Swing Trader!",
  "enabled_protocols": ["uniswap", "aave", "curve"],
  "enabled_chains": ["ethereum", "arbitrum", "polygon"],
  "enabled_tools": [
    "hunter_sentiment_analysis",
    "hunter_trading_signals",
    "hunter_price_prediction"
  ],
  "risk_config": {
    "max_risk_tolerance": 0.8,
    "max_single_asset_percent": 30,
    "max_capital_per_trade": 50000
  },
  "max_users": 1000,
  "display_order": 1,
  "is_featured": true
}
```

**Response** (`ProjectResponse`):
```json
{
  "id": "uuid",
  "slug": "defi-swing-trader",
  "name": "DeFi Swing Trader",
  "description": "...",
  "icon": "📈",
  "color": "#4CAF50",
  "banner_url": "https://...",
  "status": "draft",
  "visibility": "public",
  "system_prompt": "...",
  "welcome_message": "...",
  "enabled_protocols": ["uniswap", "aave", "curve"],
  "enabled_chains": ["ethereum", "arbitrum", "polygon"],
  "enabled_tools": ["hunter_sentiment_analysis", ...],
  "risk_config": {...},
  "max_users": 1000,
  "display_order": 1,
  "is_featured": true,
  "created_by": "uuid",
  "created_at": "2026-01-25T12:00:00Z",
  "updated_at": "2026-01-25T12:00:00Z"
}
```

---

### GET /admin/projects

List projects with filters.

**Authentication**: Required (Admin)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | - | Filter by status (draft, active, paused, archived) |
| `visibility` | string | - | Filter by visibility (public, private, invite_only) |
| `is_featured` | bool | - | Filter by featured flag |
| `limit` | int | 50 | Maximum results (1-100) |
| `offset` | int | 0 | Pagination offset |

**Response**: `List[ProjectResponse]`

---

### GET /admin/projects/{project_id}

Get project by ID.

**Authentication**: Required (Admin)

**Response**: `ProjectResponse`

---

### PATCH /admin/projects/{project_id}

Update project.

**Authentication**: Required (Admin)

**Request Body** (`ProjectUpdate`):
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "system_prompt": "Updated prompt...",
  "enabled_tools": ["hunter_sentiment_analysis", "hunter_risk_analysis"],
  "risk_config": {"max_risk_tolerance": 0.7}
}
```

---

### DELETE /admin/projects/{project_id}

Delete project.

**Authentication**: Required (Admin)

**Response**: `204 No Content`

---

### POST /admin/projects/{project_id}/activate

Activate project.

**Authentication**: Required (Admin)

**Response**: `ProjectResponse` with `status: "active"`

---

## 2. Knowledge Base Endpoints

### POST /admin/projects/{project_id}/knowledge/documents

Create and process a knowledge document.

**Authentication**: Required (Admin)

**Request Body** (`KnowledgeDocumentCreate`):
```json
{
  "title": "Uniswap V3 Guide",
  "content": "# Uniswap V3\n\nUniswap V3 introduces concentrated liquidity...",
  "doc_type": "markdown",
  "source_url": "https://docs.uniswap.org/...",
  "source_type": "manual",
  "tags": ["uniswap", "defi", "dex"],
  "priority": 1
}
```

**Response** (`KnowledgeDocumentResponse`):
```json
{
  "id": "uuid",
  "knowledge_base_id": "uuid",
  "title": "Uniswap V3 Guide",
  "doc_type": "markdown",
  "tags": ["uniswap", "defi", "dex"],
  "priority": 1,
  "is_processed": true,
  "chunk_count": 15,
  "processing_error": null,
  "created_at": "2026-01-25T12:00:00Z",
  "updated_at": "2026-01-25T12:00:00Z"
}
```

---

### GET /admin/projects/{project_id}/knowledge/documents

List knowledge documents for a project.

**Authentication**: Required (Admin)

**Response**: `List[KnowledgeDocumentResponse]`

---

## 3. Assignment Rules Endpoints

### POST /admin/projects/{project_id}/assignment-rules

Create assignment rule for a project.

**Authentication**: Required (Admin)

**Request Body** (`AssignmentRuleCreate`):
```json
{
  "rule_name": "High-Value Trader Rule",
  "condition_type": "portfolio_value",
  "condition_params": {
    "min_value_usd": 100000,
    "required_tokens": ["ETH", "BTC"]
  },
  "priority": 1,
  "auto_switch": true
}
```

**Response** (`AssignmentRuleResponse`):
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "rule_name": "High-Value Trader Rule",
  "condition_type": "portfolio_value",
  "condition_params": {...},
  "priority": 1,
  "auto_switch": true,
  "is_active": true,
  "created_at": "2026-01-25T12:00:00Z",
  "updated_at": "2026-01-25T12:00:00Z"
}
```

---

### GET /admin/projects/{project_id}/assignment-rules

List assignment rules for a project.

**Authentication**: Required (Admin)

**Response**: `List[AssignmentRuleResponse]`

---

### PATCH /admin/projects/{project_id}/assignment-rules/{rule_id}

Update assignment rule.

**Authentication**: Required (Admin)

**Request Body** (`AssignmentRuleUpdate`):
```json
{
  "rule_name": "Updated Rule Name",
  "condition_params": {"min_value_usd": 50000},
  "priority": 2,
  "auto_switch": false,
  "is_active": true
}
```

---

## 4. User Assignments Endpoints

### POST /admin/projects/{project_id}/assignments

Manually assign a user to a project.

**Authentication**: Required (Admin)

**Request Body** (`UserAssignmentCreate`):
```json
{
  "user_id": "uuid",
  "assignment_reason": "VIP customer upgrade"
}
```

**Response** (`UserAssignmentResponse`):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "project_id": "uuid",
  "assignment_type": "manual",
  "assignment_reason": "VIP customer upgrade",
  "is_active": true,
  "assigned_at": "2026-01-25T12:00:00Z",
  "last_active_at": null
}
```

---

### GET /admin/projects/{project_id}/assignments

List all user assignments for a project.

**Authentication**: Required (Admin)

**Response**: `List[UserAssignmentResponse]`

---

## 5. User Project Endpoints

### GET /user/projects

Get user's assigned projects and active project.

**Authentication**: Required (User)

**Response** (`UserProjectsResponse`):
```json
{
  "assigned_projects": [
    {
      "id": "uuid",
      "slug": "defi-swing-trader",
      "name": "DeFi Swing Trader",
      "description": "...",
      "icon": "📈",
      "color": "#4CAF50",
      "welcome_message": "Welcome!",
      "is_featured": true
    }
  ],
  "active_project_id": "uuid"
}
```

---

### GET /user/projects/available

List all publicly available projects.

**Authentication**: Required (User)

**Response**: `List[ProjectSummaryResponse]`

---

### POST /user/projects/{project_id}/select

Select (activate) a project for the current user.

**Authentication**: Required (User)

**Response**: `204 No Content`

---

### POST /user/projects/{project_id}/join

Join (self-assign to) a public project.

**Authentication**: Required (User)

**Response**: `204 No Content`

**Errors**:
- `403`: Project is not publicly available
- `400`: User is already assigned
- `400`: Project has reached maximum user capacity

---

### GET /user/projects/{project_slug}

Get project details by slug.

**Authentication**: Required (User)

**Response**: `ProjectSummaryResponse`

---

## 6. Project Templates

The system includes 5 pre-built project templates:

| Template | Slug | Tools | Risk Config |
|----------|------|-------|-------------|
| DeFi Swing Trader | `defi-swing-trader` | sentiment, trading signals, price prediction, risk analysis, portfolio optimization | max_risk: 0.8, max_single_asset: 30% |
| Arbitrage Hunter | `arbitrage-hunter` | sentiment, flash loans, arbitrage discovery, mev protection, auto executor | max_capital: $500K |
| Portfolio Manager | `portfolio-manager` | sentiment, risk analysis, portfolio optimization | max_risk: 0.6, max_single_asset: 25% |
| Conservative Investor | `conservative-investor` | sentiment, risk analysis, portfolio optimization | max_risk: 50, min_stablecoin: 30% |
| Day Trader | `day-trader` | sentiment, trading signals, price prediction, pattern recognition, risk analysis | max_risk: 0.9, max_single_asset: 40% |

---

## 7. API Client Examples

### Create Project
```bash
curl -X POST "http://localhost:8000/api/v1/admin/projects" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "my-project",
    "name": "My Project",
    "system_prompt": "You are a helpful assistant...",
    "enabled_tools": ["hunter_sentiment_analysis"]
  }'
```

### List User's Projects
```bash
curl -X GET "http://localhost:8000/api/v1/user/projects" \
  -H "Authorization: Bearer $USER_TOKEN"
```

### Join Public Project
```bash
curl -X POST "http://localhost:8000/api/v1/user/projects/{project_id}/join" \
  -H "Authorization: Bearer $USER_TOKEN"
```

### Add Knowledge Document
```bash
curl -X POST "http://localhost:8000/api/v1/admin/projects/{project_id}/knowledge/documents" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Protocol Guide",
    "content": "# Guide content...",
    "doc_type": "markdown"
  }'
```

---

## References

- **Admin Router**: `src/app/presentation/http/controllers/admin/projects_router.py`
- **User Router**: `src/app/presentation/http/controllers/user/projects_router.py`
- **Schemas**: `src/app/presentation/http/schemas/projects.py`
- **Application Commands**: `src/app/application/projects/commands/`
- **Application Queries**: `src/app/application/projects/queries/`

# AI Brain Module: Admin Endpoints Documentation

**Version:** 1.0.0
**Date:** 2026-01-26
**Status:** Design Specification
**Author:** Backend Architect (Claude Sonnet 4.5)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Authentication & Access Control](#authentication--access-control)
3. [Agent Configuration Endpoints](#agent-configuration-endpoints)
4. [Agent Prompts Endpoints](#agent-prompts-endpoints)
5. [Agent Knowledge Endpoints](#agent-knowledge-endpoints)
6. [Integration Configuration Endpoints](#integration-configuration-endpoints)
7. [Supervisor Configuration Endpoints](#supervisor-configuration-endpoints)
8. [Cache Management Endpoints](#cache-management-endpoints)
9. [Error Handling & Status Codes](#error-handling--status-codes)
10. [Implementation Guide](#implementation-guide)
11. [Testing Strategy](#testing-strategy)
12. [Security Considerations](#security-considerations)

---

## Executive Summary

### Purpose

The AI Brain Admin API provides comprehensive endpoints for managing the centralized knowledge and configuration system that controls how agents respond to users based on feature availability, integration status, and user context. This API enables dynamic, configuration-driven agent behavior without requiring code deployments.

### Key Features

- **Agent Configuration Management**: Enable/disable agents, update LLM parameters, manage dependencies
- **Dynamic Knowledge Control**: Manage knowledge entries with integration dependencies and context targeting
- **Prompt Versioning**: A/B test system prompts and track performance metrics
- **Integration Health**: Monitor and control external integration availability
- **Cache Optimization**: Warm cache, track metrics, invalidate stale data
- **Audit Logging**: Complete audit trail for all configuration changes

### Base URL

```
Production: https://api.anvil.com/api/v1/admin/ai-brain
Staging:    https://staging-api.anvil.com/api/v1/admin/ai-brain
Local:      http://localhost:8000/api/v1/admin/ai-brain
```

### Authentication

All endpoints require:
- **Admin role** via JWT authentication
- **Authorization header**: `Bearer {jwt_token}`
- **Rate limiting**: 100 requests/minute per admin user

---

## Authentication & Access Control

### Access Levels

#### Admin Role Requirements

All AI Brain admin endpoints require the `ADMIN` role. Admins are granted via:

```bash
# Grant admin access
POST /api/v1/admin/users/{user_id}/grant-admin

# Revoke admin access
POST /api/v1/admin/users/{user_id}/revoke-admin
```

#### Permission Matrix

| Endpoint Category | Read | Write | Delete | Cache Control |
|------------------|------|-------|--------|---------------|
| Agent Configuration | ✅ | ✅ | ❌ | ✅ |
| Agent Prompts | ✅ | ✅ | ✅ | ✅ |
| Agent Knowledge | ✅ | ✅ | ✅ | ✅ |
| Integration Config | ✅ | ✅ | ❌ | ✅ |
| Supervisor Config | ✅ | ✅ | ❌ | ✅ |
| Cache Management | ✅ | ✅ | ✅ | ✅ |

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API Gateway
    participant Auth Middleware
    participant Admin Endpoint
    participant Database

    Client->>API Gateway: Request with JWT
    API Gateway->>Auth Middleware: Validate JWT
    Auth Middleware->>Database: Check user role
    Database-->>Auth Middleware: User has ADMIN role
    Auth Middleware->>Admin Endpoint: Authorized request
    Admin Endpoint->>Database: Execute operation
    Database-->>Admin Endpoint: Result
    Admin Endpoint-->>Client: Response + Audit log
```

### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
X-Request-ID: uuid-v4-unique-request-id (optional)
X-Admin-Reason: "Updating knowledge for new feature" (optional, for audit)
```

### Error Responses

**401 Unauthorized** - Invalid or expired JWT:
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired authentication token",
  "status_code": 401
}
```

**403 Forbidden** - User lacks admin role:
```json
{
  "error": "forbidden",
  "message": "Admin role required for this operation",
  "status_code": 403,
  "required_role": "ADMIN",
  "user_role": "USER"
}
```

---

## Agent Configuration Endpoints

### Overview

Agent configuration endpoints manage the master configuration for all 18+ AI agents, including LLM parameters, feature toggles, and dependency management.

---

### List All Agent Configurations

**GET** `/api/v1/admin/ai-brain/agents`

List all agent configurations with optional filtering.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category: `core`, `enterprise`, `advanced`, `workflow` |
| `is_enabled` | boolean | No | Filter by enabled status |
| `depends_on_integration` | string | No | Filter agents that depend on specific integration (e.g., `hyperliquid`) |
| `limit` | integer | No | Max results (default: 100, max: 1000) |
| `offset` | integer | No | Pagination offset (default: 0) |
| `sort_by` | string | No | Sort field: `priority`, `agent_type`, `updated_at` (default: `priority`) |
| `sort_order` | string | No | `asc` or `desc` (default: `desc`) |

#### Request Example

```http
GET /api/v1/admin/ai-brain/agents?category=core&is_enabled=true&sort_by=priority
Authorization: Bearer {jwt_token}
```

#### Response Schema (200 OK)

```json
{
  "agents": [
    {
      "id": "uuid-v4",
      "agent_type": "knowledge",
      "agent_name": "Knowledge Agent",
      "agent_category": "core",
      "is_enabled": true,
      "is_available_for_guests": true,
      "is_available_for_authenticated": true,
      "is_available_for_premium": true,
      "model_name": "gemini-2.0-flash",
      "temperature": 0.5,
      "max_tokens": 1500,
      "fallback_agent": "chat",
      "requires_wallet": false,
      "requires_execution_capability": false,
      "depends_on_agents": ["chat"],
      "depends_on_integrations": [],
      "description": "Provides knowledge base information to users",
      "tags": ["core", "knowledge-retrieval"],
      "priority": 200,
      "version": 3,
      "configuration_hash": "sha256-hash-of-config",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-26T00:00:00Z",
      "created_by": "admin@anvil.com",
      "updated_by": "admin@anvil.com"
    },
    {
      "id": "uuid-v4",
      "agent_type": "swap_workflow",
      "agent_name": "Swap Workflow Agent",
      "agent_category": "workflow",
      "is_enabled": true,
      "is_available_for_guests": false,
      "is_available_for_authenticated": true,
      "is_available_for_premium": true,
      "model_name": "gemini-2.0-flash",
      "temperature": 0.7,
      "max_tokens": 1500,
      "fallback_agent": "knowledge",
      "requires_wallet": true,
      "requires_execution_capability": true,
      "depends_on_agents": ["knowledge", "risk_analyzer"],
      "depends_on_integrations": ["hyperliquid"],
      "description": "Executes token swap workflows with real-time quotes",
      "tags": ["workflow", "swap", "execution"],
      "priority": 250,
      "version": 5,
      "configuration_hash": "sha256-hash-of-config",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-26T12:00:00Z",
      "created_by": "admin@anvil.com",
      "updated_by": "admin@anvil.com"
    }
  ],
  "pagination": {
    "total": 18,
    "limit": 100,
    "offset": 0,
    "has_more": false
  },
  "filters_applied": {
    "category": "core",
    "is_enabled": true
  }
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/agents_router.py`
- **Handler**: `src/app/application/ai_brain/queries/get_agent_configurations.py`
- **Repository**: `src/app/infrastructure/adapters/ai_brain/agent_config_repository_sqla.py`

#### Business Logic

1. Validate admin authentication and authorization
2. Parse and validate query parameters
3. Query `agent_configurations` table with filters
4. Apply pagination and sorting
5. Return enriched results with metadata
6. Log query to audit log (if configured)

#### Cache Behavior

- **Cache Key**: `ai_brain:admin:agents:list:{filter_hash}`
- **TTL**: 5 minutes (300s)
- **Invalidation**: On any agent configuration update

---

### Get Specific Agent Configuration

**GET** `/api/v1/admin/ai-brain/agents/{agent_id}`

Retrieve detailed configuration for a specific agent by ID or agent_type.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | Yes | Agent UUID or `agent_type` (e.g., `knowledge`, `swap_workflow`) |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_dependencies` | boolean | No | Include dependent agents and integrations (default: true) |
| `include_prompts` | boolean | No | Include active prompts (default: false) |
| `include_knowledge` | boolean | No | Include associated knowledge entries (default: false) |

#### Request Example

```http
GET /api/v1/admin/ai-brain/agents/swap_workflow?include_dependencies=true&include_prompts=true
Authorization: Bearer {jwt_token}
```

#### Response Schema (200 OK)

```json
{
  "agent": {
    "id": "uuid-v4",
    "agent_type": "swap_workflow",
    "agent_name": "Swap Workflow Agent",
    "agent_category": "workflow",
    "is_enabled": true,
    "is_available_for_guests": false,
    "is_available_for_authenticated": true,
    "is_available_for_premium": true,
    "model_name": "gemini-2.0-flash",
    "temperature": 0.7,
    "max_tokens": 1500,
    "fallback_agent": "knowledge",
    "requires_wallet": true,
    "requires_execution_capability": true,
    "depends_on_agents": ["knowledge", "risk_analyzer"],
    "depends_on_integrations": ["hyperliquid"],
    "description": "Executes token swap workflows with real-time quotes",
    "tags": ["workflow", "swap", "execution"],
    "priority": 250,
    "version": 5,
    "configuration_hash": "sha256-hash-of-config",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-26T12:00:00Z",
    "created_by": "admin@anvil.com",
    "updated_by": "admin@anvil.com"
  },
  "dependencies": {
    "agents": [
      {
        "agent_type": "knowledge",
        "agent_name": "Knowledge Agent",
        "is_enabled": true
      },
      {
        "agent_type": "risk_analyzer",
        "agent_name": "Risk Analyzer Agent",
        "is_enabled": true
      }
    ],
    "integrations": [
      {
        "integration_key": "hyperliquid",
        "integration_name": "Hyperliquid Spot Exchange",
        "is_enabled": true,
        "health_status": "healthy"
      }
    ]
  },
  "active_prompts": [
    {
      "id": "uuid-v4",
      "prompt_type": "system",
      "user_type": null,
      "language": "en",
      "version": 2,
      "variant_name": "default",
      "is_active": true,
      "prompt_content": "You are a specialized swap workflow agent...",
      "estimated_tokens": 250,
      "created_at": "2026-01-15T00:00:00Z"
    }
  ]
}
```

#### Error Responses

**404 Not Found** - Agent not found:
```json
{
  "error": "not_found",
  "message": "Agent configuration not found",
  "status_code": 404,
  "agent_id": "unknown_agent"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/agents_router.py`
- **Handler**: `src/app/application/ai_brain/queries/get_agent_configuration.py`
- **Repository**: `src/app/infrastructure/adapters/ai_brain/agent_config_repository_sqla.py`

#### Business Logic

1. Validate admin authentication
2. Lookup agent by ID or agent_type
3. If `include_dependencies=true`, fetch dependent agents and integrations
4. If `include_prompts=true`, fetch active prompts
5. If `include_knowledge=true`, fetch associated knowledge entries
6. Return enriched agent configuration

#### Cache Behavior

- **Cache Key**: `ai_brain:config:agent:{agent_type}`
- **TTL**: 2 hours (7200s)
- **Invalidation**: On agent configuration update

---

### Update Agent Configuration

**PUT** `/api/v1/admin/ai-brain/agents/{agent_id}`

Update agent configuration settings.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | Yes | Agent UUID or `agent_type` |

#### Request Body Schema

```json
{
  "is_enabled": true,
  "is_available_for_guests": false,
  "is_available_for_authenticated": true,
  "is_available_for_premium": true,
  "model_name": "gemini-2.0-flash",
  "temperature": 0.7,
  "max_tokens": 1500,
  "fallback_agent": "knowledge",
  "depends_on_agents": ["knowledge", "risk_analyzer"],
  "depends_on_integrations": ["hyperliquid"],
  "description": "Updated description",
  "tags": ["workflow", "swap", "execution", "updated"],
  "priority": 250,
  "update_reason": "Adjusting temperature for better responses"
}
```

#### Field Validation

| Field | Type | Constraints |
|-------|------|-------------|
| `is_enabled` | boolean | Optional |
| `model_name` | string | Must be valid LLM model |
| `temperature` | float | 0.0 ≤ temperature ≤ 2.0 |
| `max_tokens` | integer | 1 ≤ max_tokens ≤ 100000 |
| `fallback_agent` | string | Must reference existing agent |
| `depends_on_agents` | array | All agents must exist |
| `depends_on_integrations` | array | All integrations must exist |
| `priority` | integer | Higher = more important |
| `update_reason` | string | Required, max 500 chars (for audit log) |

#### Request Example

```http
PUT /api/v1/admin/ai-brain/agents/swap_workflow
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "temperature": 0.8,
  "max_tokens": 2000,
  "update_reason": "Increasing creativity for better user engagement"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "agent": {
    "id": "uuid-v4",
    "agent_type": "swap_workflow",
    "agent_name": "Swap Workflow Agent",
    "temperature": 0.8,
    "max_tokens": 2000,
    "version": 6,
    "configuration_hash": "new-sha256-hash",
    "updated_at": "2026-01-26T13:00:00Z",
    "updated_by": "admin@anvil.com"
  },
  "changes": {
    "temperature": {
      "old": 0.7,
      "new": 0.8
    },
    "max_tokens": {
      "old": 1500,
      "new": 2000
    },
    "version": {
      "old": 5,
      "new": 6
    }
  },
  "cache_invalidated": [
    "ai_brain:config:agent:swap_workflow",
    "ai_brain:knowledge:swap_*:*:*"
  ],
  "audit_log_id": "uuid-v4"
}
```

#### Error Responses

**400 Bad Request** - Invalid field values:
```json
{
  "error": "validation_error",
  "message": "Invalid configuration values",
  "status_code": 400,
  "validation_errors": [
    {
      "field": "temperature",
      "error": "temperature must be between 0.0 and 2.0",
      "provided_value": 3.5
    }
  ]
}
```

**409 Conflict** - Dependency conflict:
```json
{
  "error": "dependency_conflict",
  "message": "Cannot disable agent: other agents depend on it",
  "status_code": 409,
  "dependent_agents": ["swap_workflow", "lending_workflow"],
  "suggestion": "Disable or update dependent agents first"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/agents_router.py`
- **Handler**: `src/app/application/ai_brain/commands/update_agent_configuration.py`
- **Repository**: `src/app/infrastructure/adapters/ai_brain/agent_config_repository_sqla.py`

#### Business Logic

1. Validate admin authentication and authorization
2. Validate request body against schema
3. Check for dependency conflicts
4. Begin database transaction
5. Update `agent_configurations` table
6. Increment version number
7. Generate new configuration hash
8. Record audit log entry
9. Invalidate Redis cache for agent and related knowledge
10. Commit transaction
11. Return updated configuration with change summary

#### Cache Invalidation Rules

When agent configuration changes:
1. Delete `ai_brain:config:agent:{agent_type}`
2. Delete all knowledge cache entries for this agent: `ai_brain:knowledge:*:{agent_type}:*`
3. Update `knowledge_cache_metadata` table with invalidation timestamp

#### Audit Logging

```sql
INSERT INTO audit_logs (
  entity_type, entity_id, action, user_id,
  changes, reason, ip_address, created_at
) VALUES (
  'agent_configuration',
  'swap_workflow',
  'UPDATE',
  'admin-user-uuid',
  '{"temperature": {"old": 0.7, "new": 0.8}, "max_tokens": {"old": 1500, "new": 2000}}',
  'Increasing creativity for better user engagement',
  '192.168.1.100',
  CURRENT_TIMESTAMP
);
```

---

### Enable Agent

**POST** `/api/v1/admin/ai-brain/agents/{agent_id}/enable`

Enable a previously disabled agent.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | Yes | Agent UUID or `agent_type` |

#### Request Body Schema

```json
{
  "reason": "Re-enabling after fixing integration issues"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "agent_type": "swap_workflow",
  "is_enabled": true,
  "updated_at": "2026-01-26T14:00:00Z",
  "cache_invalidated": true,
  "audit_log_id": "uuid-v4"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/agents_router.py`
- **Handler**: `src/app/application/ai_brain/commands/enable_agent.py`

---

### Disable Agent

**POST** `/api/v1/admin/ai-brain/agents/{agent_id}/disable`

Disable an agent (prevents it from being selected by supervisor).

#### Request Body Schema

```json
{
  "reason": "Disabling due to integration downtime",
  "force": false
}
```

**Note**: If `force=false` and other agents depend on this agent, request will fail with 409 Conflict.

#### Response Schema (200 OK)

```json
{
  "success": true,
  "agent_type": "swap_workflow",
  "is_enabled": false,
  "updated_at": "2026-01-26T14:00:00Z",
  "affected_agents": [],
  "cache_invalidated": true,
  "audit_log_id": "uuid-v4"
}
```

---

### Get Agent Dependencies

**GET** `/api/v1/admin/ai-brain/agents/{agent_id}/dependencies`

Get full dependency tree for an agent (agents and integrations it depends on, and agents that depend on it).

#### Response Schema (200 OK)

```json
{
  "agent_type": "swap_workflow",
  "depends_on": {
    "agents": [
      {
        "agent_type": "knowledge",
        "is_enabled": true,
        "health": "healthy"
      },
      {
        "agent_type": "risk_analyzer",
        "is_enabled": true,
        "health": "healthy"
      }
    ],
    "integrations": [
      {
        "integration_key": "hyperliquid",
        "is_enabled": true,
        "health_status": "healthy",
        "last_health_check": "2026-01-26T13:55:00Z"
      }
    ]
  },
  "depended_on_by": {
    "agents": []
  },
  "dependency_status": "healthy",
  "issues": []
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/agents_router.py`
- **Handler**: `src/app/application/ai_brain/queries/get_agent_dependencies.py`

---

## Agent Prompts Endpoints

### Overview

Agent prompts endpoints manage system prompts with versioning, A/B testing, and performance tracking.

---

### List All Prompts

**GET** `/api/v1/admin/ai-brain/prompts`

List all agent prompts with filtering and pagination.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_type` | string | No | Filter by agent type |
| `prompt_type` | string | No | Filter by prompt type: `system`, `user`, `supervisor`, `knowledge_base` |
| `is_active` | boolean | No | Filter by active status |
| `user_type` | string | No | Filter by user type: `guest`, `authenticated`, `premium` |
| `language` | string | No | Filter by language code (e.g., `en`, `es`) |
| `variant_name` | string | No | Filter by A/B test variant |
| `limit` | integer | No | Max results (default: 50, max: 500) |
| `offset` | integer | No | Pagination offset |
| `sort_by` | string | No | Sort field: `updated_at`, `success_rate`, `avg_response_time_ms` |

#### Request Example

```http
GET /api/v1/admin/ai-brain/prompts?agent_type=knowledge&is_active=true&language=en
Authorization: Bearer {jwt_token}
```

#### Response Schema (200 OK)

```json
{
  "prompts": [
    {
      "id": "uuid-v4",
      "agent_type": "knowledge",
      "prompt_type": "system",
      "prompt_content": "You are a specialized knowledge retrieval agent...",
      "prompt_content_compressed": "Knowledge retrieval agent...",
      "estimated_tokens": 250,
      "user_type": null,
      "language": "en",
      "version": 3,
      "is_active": true,
      "variant_name": "default",
      "traffic_percentage": 100.0,
      "avg_response_time_ms": 850,
      "success_rate": 98.5,
      "user_satisfaction_score": 4.6,
      "description": "Main system prompt for knowledge agent",
      "tags": ["system", "knowledge"],
      "created_at": "2026-01-10T00:00:00Z",
      "updated_at": "2026-01-20T00:00:00Z",
      "created_by": "admin@anvil.com",
      "activated_at": "2026-01-20T12:00:00Z"
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/prompts_router.py`
- **Handler**: `src/app/application/ai_brain/queries/get_prompts.py`

---

### Get Agent Prompts

**GET** `/api/v1/admin/ai-brain/prompts/{agent_id}`

Get all prompts for a specific agent, including inactive versions.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_inactive` | boolean | No | Include inactive prompts (default: false) |
| `include_performance` | boolean | No | Include performance metrics (default: true) |

#### Response Schema (200 OK)

```json
{
  "agent_type": "knowledge",
  "active_prompts": [
    {
      "id": "uuid-v4",
      "prompt_type": "system",
      "user_type": null,
      "language": "en",
      "version": 3,
      "is_active": true,
      "variant_name": "default",
      "traffic_percentage": 80.0,
      "prompt_content": "You are a specialized knowledge agent...",
      "estimated_tokens": 250,
      "performance": {
        "avg_response_time_ms": 850,
        "success_rate": 98.5,
        "user_satisfaction_score": 4.6,
        "total_uses": 15000
      }
    },
    {
      "id": "uuid-v4",
      "prompt_type": "system",
      "user_type": null,
      "language": "en",
      "version": 3,
      "is_active": true,
      "variant_name": "variant_a",
      "traffic_percentage": 20.0,
      "prompt_content": "You are an expert knowledge retrieval system...",
      "estimated_tokens": 220,
      "performance": {
        "avg_response_time_ms": 820,
        "success_rate": 99.1,
        "user_satisfaction_score": 4.7,
        "total_uses": 3800
      }
    }
  ],
  "inactive_prompts": [],
  "ab_tests": [
    {
      "test_name": "Knowledge Agent Prompt Optimization",
      "variants": ["default", "variant_a"],
      "traffic_split": [80, 20],
      "started_at": "2026-01-20T00:00:00Z",
      "status": "running",
      "winner": null
    }
  ]
}
```

---

### Create New Prompt Version

**POST** `/api/v1/admin/ai-brain/prompts/{agent_id}`

Create a new prompt version for an agent.

#### Request Body Schema

```json
{
  "prompt_type": "system",
  "prompt_content": "You are a highly specialized DeFi knowledge agent with expertise in...",
  "user_type": null,
  "language": "en",
  "variant_name": "variant_b",
  "traffic_percentage": 0.0,
  "description": "Testing more concise prompt structure",
  "tags": ["system", "experiment"],
  "auto_activate": false,
  "reason": "Testing new prompt structure for better token efficiency"
}
```

#### Field Validation

| Field | Type | Constraints |
|-------|------|-------------|
| `prompt_type` | string | Required. One of: `system`, `user`, `supervisor`, `knowledge_base` |
| `prompt_content` | string | Required. 10 ≤ length ≤ 50000 chars |
| `user_type` | string | Optional. One of: `guest`, `authenticated`, `premium`, `null` |
| `language` | string | Optional. Default: `en`. ISO 639-1 code |
| `variant_name` | string | Optional. Default: `default`. Max 50 chars |
| `traffic_percentage` | float | Optional. Default: 0.0. 0.0 ≤ value ≤ 100.0 |
| `auto_activate` | boolean | Optional. Default: false. If true, deactivates other prompts |

#### Response Schema (201 Created)

```json
{
  "success": true,
  "prompt": {
    "id": "uuid-v4",
    "agent_type": "knowledge",
    "prompt_type": "system",
    "version": 4,
    "is_active": false,
    "variant_name": "variant_b",
    "traffic_percentage": 0.0,
    "estimated_tokens": 280,
    "created_at": "2026-01-26T15:00:00Z",
    "created_by": "admin@anvil.com"
  },
  "audit_log_id": "uuid-v4"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/prompts_router.py`
- **Handler**: `src/app/application/ai_brain/commands/create_prompt.py`

#### Business Logic

1. Validate admin authentication
2. Validate request body
3. Estimate token count for prompt content
4. Create compressed version of prompt (optional)
5. Insert into `agent_prompts` table
6. Auto-increment version number
7. If `auto_activate=true`, deactivate other active prompts and activate this one
8. Record audit log
9. Return created prompt

---

### Update Prompt

**PUT** `/api/v1/admin/ai-brain/prompts/{prompt_id}`

Update an existing prompt (content, traffic percentage, etc.).

#### Request Body Schema

```json
{
  "prompt_content": "Updated prompt content...",
  "traffic_percentage": 50.0,
  "description": "Updated description",
  "reason": "Adjusting A/B test traffic split based on performance"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "prompt": {
    "id": "uuid-v4",
    "version": 5,
    "traffic_percentage": 50.0,
    "updated_at": "2026-01-26T15:30:00Z"
  },
  "changes": {
    "traffic_percentage": {
      "old": 20.0,
      "new": 50.0
    }
  },
  "audit_log_id": "uuid-v4"
}
```

---

### Delete Prompt

**DELETE** `/api/v1/admin/ai-brain/prompts/{prompt_id}`

Delete a prompt version (only inactive prompts can be deleted).

#### Request Body Schema

```json
{
  "reason": "Removing underperforming variant",
  "force": false
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "deleted_prompt_id": "uuid-v4",
  "audit_log_id": "uuid-v4"
}
```

#### Error Responses

**409 Conflict** - Cannot delete active prompt:
```json
{
  "error": "conflict",
  "message": "Cannot delete active prompt",
  "status_code": 409,
  "suggestion": "Deactivate prompt first or use force=true"
}
```

---

### Activate Prompt Version

**POST** `/api/v1/admin/ai-brain/prompts/{prompt_id}/activate`

Activate a prompt version (sets `is_active=true`).

#### Request Body Schema

```json
{
  "traffic_percentage": 100.0,
  "deactivate_others": true,
  "reason": "Promoting variant_a to production based on A/B test results"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "activated_prompt": {
    "id": "uuid-v4",
    "is_active": true,
    "traffic_percentage": 100.0,
    "activated_at": "2026-01-26T16:00:00Z"
  },
  "deactivated_prompts": [
    {
      "id": "uuid-v4-old",
      "variant_name": "default",
      "deactivated_at": "2026-01-26T16:00:00Z"
    }
  ],
  "audit_log_id": "uuid-v4"
}
```

---

### Start A/B Test

**POST** `/api/v1/admin/ai-brain/prompts/{prompt_id}/ab-test`

Start an A/B test with multiple prompt variants.

#### Request Body Schema

```json
{
  "test_name": "Knowledge Agent Prompt Optimization v2",
  "variants": [
    {
      "prompt_id": "uuid-v4-default",
      "traffic_percentage": 50.0
    },
    {
      "prompt_id": "uuid-v4-variant-a",
      "traffic_percentage": 30.0
    },
    {
      "prompt_id": "uuid-v4-variant-b",
      "traffic_percentage": 20.0
    }
  ],
  "duration_days": 7,
  "success_metric": "user_satisfaction_score",
  "reason": "Testing new prompt structures for better engagement"
}
```

#### Field Validation

- Sum of `traffic_percentage` must equal 100.0
- All prompts must belong to same agent
- All prompts must have same `prompt_type` and `user_type`

#### Response Schema (201 Created)

```json
{
  "success": true,
  "ab_test": {
    "id": "uuid-v4",
    "test_name": "Knowledge Agent Prompt Optimization v2",
    "agent_type": "knowledge",
    "variants": [
      {
        "prompt_id": "uuid-v4-default",
        "variant_name": "default",
        "traffic_percentage": 50.0,
        "is_active": true
      },
      {
        "prompt_id": "uuid-v4-variant-a",
        "variant_name": "variant_a",
        "traffic_percentage": 30.0,
        "is_active": true
      },
      {
        "prompt_id": "uuid-v4-variant-b",
        "variant_name": "variant_b",
        "traffic_percentage": 20.0,
        "is_active": true
      }
    ],
    "started_at": "2026-01-26T16:00:00Z",
    "ends_at": "2026-02-02T16:00:00Z",
    "status": "running"
  },
  "audit_log_id": "uuid-v4"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/prompts_router.py`
- **Handler**: `src/app/application/ai_brain/commands/start_ab_test.py`

---

## Agent Knowledge Endpoints

### Overview

Agent knowledge endpoints manage dynamic knowledge entries that replace static JSON files. Knowledge entries can be targeted by user type, language, and integration dependencies.

---

### List Knowledge Entries

**GET** `/api/v1/admin/ai-brain/knowledge`

List all knowledge entries with filtering and search.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `knowledge_category` | string | No | Filter by category: `feature`, `integration`, `protocol`, `general`, `error_message` |
| `agent_type` | string | No | Filter by agent type (knowledge can be shared across agents) |
| `intent_pattern` | string | No | Filter by intent pattern (e.g., `SWAP`, `HUNTER_SENTIMENT`) |
| `user_type` | string | No | Filter by user type: `guest`, `authenticated`, `premium` |
| `language` | string | No | Filter by language code |
| `is_enabled` | boolean | No | Filter by enabled status |
| `depends_on_integration` | string | No | Filter by integration dependency |
| `search` | string | No | Full-text search on title and description |
| `limit` | integer | No | Max results (default: 50, max: 500) |
| `offset` | integer | No | Pagination offset |
| `sort_by` | string | No | Sort field: `priority`, `access_count`, `updated_at` |

#### Request Example

```http
GET /api/v1/admin/ai-brain/knowledge?knowledge_category=feature&is_enabled=true&search=swap
Authorization: Bearer {jwt_token}
```

#### Response Schema (200 OK)

```json
{
  "knowledge_entries": [
    {
      "id": "uuid-v4",
      "knowledge_key": "swap_overview",
      "knowledge_category": "feature",
      "agent_types": ["knowledge", "chat", "swap_workflow"],
      "intent_patterns": ["SWAP", "EXCHANGE", "TRADE"],
      "title": "Token Swap Overview",
      "description": "Comprehensive information about token swap functionality",
      "content": {
        "feature_name": "Token Swap",
        "description": "Execute instant token swaps on Hyperliquid Spot exchange",
        "supported_provider": {
          "name": "Hyperliquid Spot",
          "chain": "Hyperliquid L1",
          "gas_fees": "ZERO"
        },
        "supported_tokens": ["USDC", "PURR", "TRUMP", "PEPE", "MOG"]
      },
      "content_compressed": null,
      "user_type": null,
      "language": "en",
      "depends_on_integrations": ["hyperliquid"],
      "fallback_knowledge_id": null,
      "is_enabled": true,
      "requires_feature_enabled": "swap",
      "parent_knowledge_id": null,
      "display_order": 1,
      "version": 2,
      "content_hash": "sha256-hash",
      "cache_key": "ai_brain:knowledge:swap_overview:*:en",
      "cache_ttl_seconds": 3600,
      "access_count": 15420,
      "last_accessed_at": "2026-01-26T15:00:00Z",
      "avg_retrieval_time_ms": 12,
      "tags": ["swap", "hyperliquid", "feature"],
      "priority": 200,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-20T00:00:00Z",
      "created_by": "admin@anvil.com",
      "updated_by": "admin@anvil.com"
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 50,
    "offset": 0,
    "has_more": false
  },
  "search_metadata": {
    "query": "swap",
    "matched_fields": ["title", "description", "content"]
  }
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/knowledge_router.py`
- **Handler**: `src/app/application/ai_brain/queries/get_knowledge_entries.py`

---

### Get Agent Knowledge

**GET** `/api/v1/admin/ai-brain/knowledge/{agent_id}`

Get all knowledge entries associated with a specific agent.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_type` | string | No | Filter by user type |
| `language` | string | No | Filter by language (default: `en`) |
| `include_disabled` | boolean | No | Include disabled knowledge (default: false) |

#### Response Schema (200 OK)

```json
{
  "agent_type": "knowledge",
  "knowledge_entries": [
    {
      "id": "uuid-v4",
      "knowledge_key": "swap_overview",
      "title": "Token Swap Overview",
      "is_enabled": true,
      "priority": 200,
      "access_count": 15420
    },
    {
      "id": "uuid-v4",
      "knowledge_key": "hunter_ai_sentiment",
      "title": "Hunter AI Sentiment Analysis",
      "is_enabled": true,
      "priority": 180,
      "access_count": 8320
    }
  ],
  "total_entries": 12,
  "integration_dependencies": {
    "hyperliquid": {
      "is_enabled": true,
      "health_status": "healthy",
      "affected_knowledge_count": 3
    }
  }
}
```

---

### Create Knowledge Entry

**POST** `/api/v1/admin/ai-brain/knowledge`

Create a new knowledge entry.

#### Request Body Schema

```json
{
  "knowledge_key": "lending_morpho_vaults",
  "knowledge_category": "feature",
  "agent_types": ["knowledge", "chat", "lending_workflow"],
  "intent_patterns": ["LENDING", "MORPHO", "VAULT", "SUPPLY"],
  "title": "Morpho Lending Vaults",
  "description": "Information about Morpho lending vault functionality",
  "content": {
    "feature_name": "Morpho Lending",
    "description": "Supply assets to Morpho vaults and earn yield",
    "supported_chains": ["Ethereum", "Base"],
    "supported_assets": ["USDC", "USDT", "DAI", "WETH"]
  },
  "user_type": null,
  "language": "en",
  "depends_on_integrations": ["morpho"],
  "fallback_knowledge_id": null,
  "is_enabled": true,
  "requires_feature_enabled": "lending",
  "parent_knowledge_id": null,
  "display_order": 1,
  "cache_ttl_seconds": 3600,
  "tags": ["lending", "morpho", "defi"],
  "priority": 180,
  "reason": "Adding knowledge for new Morpho lending feature"
}
```

#### Field Validation

| Field | Type | Constraints |
|-------|------|-------------|
| `knowledge_key` | string | Required. Unique. Max 100 chars. Format: `lowercase_with_underscores` |
| `knowledge_category` | string | Required. One of: `feature`, `integration`, `protocol`, `general`, `error_message` |
| `agent_types` | array | Required. Non-empty array of valid agent types |
| `intent_patterns` | array | Optional. Intent strings (uppercase) |
| `title` | string | Required. Max 255 chars |
| `content` | object | Required. Valid JSON object |
| `user_type` | string | Optional. One of: `guest`, `authenticated`, `premium`, `null` |
| `language` | string | Optional. Default: `en`. ISO 639-1 code |
| `depends_on_integrations` | array | Optional. Array of valid integration keys |
| `priority` | integer | Optional. Default: 100. Higher = more important |

#### Response Schema (201 Created)

```json
{
  "success": true,
  "knowledge": {
    "id": "uuid-v4",
    "knowledge_key": "lending_morpho_vaults",
    "version": 1,
    "content_hash": "sha256-hash",
    "cache_key": "ai_brain:knowledge:lending_morpho_vaults:*:en",
    "created_at": "2026-01-26T17:00:00Z",
    "created_by": "admin@anvil.com"
  },
  "cache_warmed": true,
  "audit_log_id": "uuid-v4"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/knowledge_router.py`
- **Handler**: `src/app/application/ai_brain/commands/create_knowledge_entry.py`

#### Business Logic

1. Validate admin authentication
2. Validate request body
3. Check `knowledge_key` uniqueness
4. Validate agent types and integrations exist
5. Generate content hash
6. Insert into `agent_knowledge` table
7. Warm Redis cache immediately
8. Record audit log
9. Return created knowledge entry

---

### Update Knowledge Entry

**PUT** `/api/v1/admin/ai-brain/knowledge/{knowledge_id}`

Update an existing knowledge entry.

#### Request Body Schema

```json
{
  "content": {
    "feature_name": "Morpho Lending",
    "description": "Updated description with more detail...",
    "supported_chains": ["Ethereum", "Base", "Optimism"]
  },
  "is_enabled": true,
  "priority": 200,
  "reason": "Adding Optimism support to knowledge"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "knowledge": {
    "id": "uuid-v4",
    "knowledge_key": "lending_morpho_vaults",
    "version": 2,
    "content_hash": "new-sha256-hash",
    "updated_at": "2026-01-26T17:30:00Z",
    "updated_by": "admin@anvil.com"
  },
  "changes": {
    "content.supported_chains": {
      "old": ["Ethereum", "Base"],
      "new": ["Ethereum", "Base", "Optimism"]
    },
    "priority": {
      "old": 180,
      "new": 200
    },
    "version": {
      "old": 1,
      "new": 2
    }
  },
  "cache_invalidated": [
    "ai_brain:knowledge:lending_morpho_vaults:*:en"
  ],
  "audit_log_id": "uuid-v4"
}
```

#### Implementation Location

- **Handler**: `src/app/application/ai_brain/commands/update_knowledge_entry.py`

#### Cache Invalidation

When knowledge is updated:
1. Delete Redis cache key: `ai_brain:knowledge:{knowledge_key}:{user_type}:{language}`
2. Update `knowledge_cache_metadata.invalidated_at`
3. Warm cache with new content immediately

---

### Delete Knowledge Entry

**DELETE** `/api/v1/admin/ai-brain/knowledge/{knowledge_id}`

Delete a knowledge entry.

#### Request Body Schema

```json
{
  "reason": "Feature deprecated, removing knowledge",
  "force": false
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "deleted_knowledge_id": "uuid-v4",
  "cache_invalidated": true,
  "audit_log_id": "uuid-v4"
}
```

---

### Invalidate Knowledge Cache

**POST** `/api/v1/admin/ai-brain/knowledge/invalidate-cache`

Manually invalidate Redis cache for specific knowledge or all knowledge.

#### Request Body Schema

```json
{
  "knowledge_key": "swap_overview",
  "invalidate_all": false,
  "warm_immediately": true,
  "reason": "Manual cache refresh after data source update"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "invalidated_keys": [
    "ai_brain:knowledge:swap_overview:guest:en",
    "ai_brain:knowledge:swap_overview:authenticated:en",
    "ai_brain:knowledge:swap_overview:premium:en"
  ],
  "warmed_keys": [
    "ai_brain:knowledge:swap_overview:guest:en",
    "ai_brain:knowledge:swap_overview:authenticated:en",
    "ai_brain:knowledge:swap_overview:premium:en"
  ],
  "timestamp": "2026-01-26T18:00:00Z"
}
```

---

## Integration Configuration Endpoints

### Overview

Integration configuration endpoints manage external integration availability, health status, and feature impact.

---

### List All Integrations

**GET** `/api/v1/admin/ai-brain/integrations`

List all integration configurations.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `integration_type` | string | No | Filter by type: `dex_aggregator`, `exchange`, `lending`, `data_provider`, `bridge`, `wallet` |
| `is_enabled` | boolean | No | Filter by enabled status |
| `health_status` | string | No | Filter by health: `healthy`, `degraded`, `down`, `maintenance` |
| `impacts_feature` | string | No | Filter by feature (e.g., `swap`, `lending`) |

#### Response Schema (200 OK)

```json
{
  "integrations": [
    {
      "id": "uuid-v4",
      "integration_key": "hyperliquid",
      "integration_name": "Hyperliquid Spot Exchange",
      "integration_type": "exchange",
      "is_enabled": true,
      "is_available_for_guests": false,
      "is_available_for_authenticated": true,
      "is_available_for_premium": true,
      "health_status": "healthy",
      "last_health_check_at": "2026-01-26T17:55:00Z",
      "health_check_error": null,
      "api_endpoint": "https://api.hyperliquid.xyz",
      "api_key_required": false,
      "rate_limit_per_minute": 60,
      "timeout_seconds": 30,
      "impacts_features": ["swap", "trading"],
      "impacts_agents": ["swap_workflow"],
      "fallback_integration_key": null,
      "avg_response_time_ms": 45,
      "error_rate": 0.01,
      "uptime_percentage": 99.95,
      "description": "High-performance spot exchange with zero gas fees",
      "documentation_url": "https://hyperliquid.gitbook.io",
      "tags": ["exchange", "spot", "zero-gas"],
      "priority": 200,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-26T17:55:00Z"
    }
  ],
  "pagination": {
    "total": 12,
    "limit": 100,
    "offset": 0
  },
  "health_summary": {
    "healthy": 11,
    "degraded": 1,
    "down": 0,
    "maintenance": 0
  }
}
```

---

### Get Integration Details

**GET** `/api/v1/admin/ai-brain/integrations/{integration_id}`

Get detailed information about a specific integration.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `integration_id` | string | Yes | Integration UUID or `integration_key` (e.g., `hyperliquid`) |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_health_history` | boolean | No | Include health check history (default: false) |
| `include_affected_knowledge` | boolean | No | Include affected knowledge entries (default: true) |

#### Response Schema (200 OK)

```json
{
  "integration": {
    "id": "uuid-v4",
    "integration_key": "hyperliquid",
    "integration_name": "Hyperliquid Spot Exchange",
    "integration_type": "exchange",
    "is_enabled": true,
    "health_status": "healthy",
    "last_health_check_at": "2026-01-26T17:55:00Z",
    "avg_response_time_ms": 45,
    "error_rate": 0.01,
    "uptime_percentage": 99.95
  },
  "affected_knowledge": [
    {
      "knowledge_key": "swap_overview",
      "title": "Token Swap Overview",
      "agent_types": ["knowledge", "chat", "swap_workflow"],
      "is_enabled": true
    }
  ],
  "affected_agents": [
    {
      "agent_type": "swap_workflow",
      "agent_name": "Swap Workflow Agent",
      "is_enabled": true
    }
  ],
  "health_history": []
}
```

---

### Update Integration Configuration

**PUT** `/api/v1/admin/ai-brain/integrations/{integration_id}`

Update integration configuration.

#### Request Body Schema

```json
{
  "is_enabled": true,
  "is_available_for_guests": false,
  "rate_limit_per_minute": 120,
  "timeout_seconds": 45,
  "description": "Updated description",
  "reason": "Increasing rate limit after provider upgrade"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "integration": {
    "id": "uuid-v4",
    "integration_key": "hyperliquid",
    "rate_limit_per_minute": 120,
    "updated_at": "2026-01-26T18:00:00Z"
  },
  "changes": {
    "rate_limit_per_minute": {
      "old": 60,
      "new": 120
    }
  },
  "cache_invalidated": [
    "ai_brain:integration:hyperliquid:status"
  ],
  "affected_knowledge_invalidated": 3,
  "audit_log_id": "uuid-v4"
}
```

---

### Enable Integration

**POST** `/api/v1/admin/ai-brain/integrations/{integration_id}/enable`

Enable a previously disabled integration.

#### Request Body Schema

```json
{
  "reason": "Re-enabling after maintenance window"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "integration_key": "hyperliquid",
  "is_enabled": true,
  "affected_knowledge_enabled": 3,
  "affected_agents_enabled": 1,
  "cache_invalidated": true,
  "audit_log_id": "uuid-v4"
}
```

---

### Disable Integration

**POST** `/api/v1/admin/ai-brain/integrations/{integration_id}/disable`

Disable an integration (triggers fallback knowledge).

#### Request Body Schema

```json
{
  "reason": "Emergency shutdown due to API issues",
  "enable_fallback": true
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "integration_key": "hyperliquid",
  "is_enabled": false,
  "fallback_integration": "1inch",
  "affected_knowledge_count": 3,
  "fallback_knowledge_activated": 2,
  "audit_log_id": "uuid-v4"
}
```

#### Business Logic

When integration is disabled:
1. Update `integration_configurations.is_enabled = false`
2. Query all knowledge entries with `depends_on_integrations = ['{integration_key}']`
3. For each knowledge entry:
   - If `fallback_knowledge_id` exists, activate fallback knowledge
   - If no fallback, disable knowledge entry
4. Invalidate all related cache entries
5. Log audit entry

---

### Check Integration Health

**GET** `/api/v1/admin/ai-brain/integrations/{integration_id}/health`

Perform real-time health check on an integration.

#### Response Schema (200 OK)

```json
{
  "integration_key": "hyperliquid",
  "health_status": "healthy",
  "health_check_performed_at": "2026-01-26T18:05:00Z",
  "response_time_ms": 42,
  "endpoint_tested": "https://api.hyperliquid.xyz/info",
  "http_status": 200,
  "error": null,
  "circuit_breaker_status": "closed",
  "uptime_percentage_24h": 99.95
}
```

#### Error Response (503 Service Unavailable)

```json
{
  "integration_key": "hyperliquid",
  "health_status": "down",
  "health_check_performed_at": "2026-01-26T18:05:00Z",
  "error": "Connection timeout after 5000ms",
  "circuit_breaker_status": "open",
  "fallback_available": true,
  "fallback_integration": "1inch"
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/integrations_router.py`
- **Handler**: `src/app/application/ai_brain/queries/check_integration_health.py`
- **Service**: `src/app/infrastructure/monitoring/integration_health_checker.py`

---

## Supervisor Configuration Endpoints

### Overview

Supervisor configuration endpoints manage orchestration settings for authenticated, guest, and premium supervisors.

---

### Get Supervisor Configuration

**GET** `/api/v1/admin/ai-brain/supervisor`

Get all supervisor configurations.

#### Response Schema (200 OK)

```json
{
  "supervisors": [
    {
      "id": "uuid-v4",
      "supervisor_type": "authenticated",
      "is_enabled": true,
      "max_agents_per_request": 5,
      "timeout_seconds": 120,
      "model_name": "gemini-2.0-flash",
      "temperature": 0.7,
      "max_tokens": 2000,
      "intent_confidence_threshold": 0.85,
      "fallback_agent": "chat",
      "max_context_messages": 10,
      "agent_priorities": {
        "swap_workflow": 200,
        "hunter_ai": 180,
        "knowledge": 150
      },
      "enable_intent_classification": true,
      "enable_multi_agent_coordination": true,
      "enable_context_preservation": true,
      "max_concurrent_agents": 3,
      "routing_timeout_seconds": 5,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-20T00:00:00Z"
    },
    {
      "id": "uuid-v4",
      "supervisor_type": "guest",
      "is_enabled": true,
      "max_agents_per_request": 3,
      "timeout_seconds": 60,
      "fallback_agent": "chat"
    }
  ]
}
```

---

### Update Supervisor Configuration

**PUT** `/api/v1/admin/ai-brain/supervisor`

Update supervisor configuration.

#### Request Body Schema

```json
{
  "supervisor_type": "authenticated",
  "max_agents_per_request": 7,
  "intent_confidence_threshold": 0.80,
  "agent_priorities": {
    "swap_workflow": 250,
    "hunter_ai": 200,
    "ultra": 180,
    "knowledge": 150
  },
  "reason": "Increasing agent capacity and adjusting priorities based on usage"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "supervisor": {
    "supervisor_type": "authenticated",
    "max_agents_per_request": 7,
    "intent_confidence_threshold": 0.80,
    "updated_at": "2026-01-26T18:30:00Z"
  },
  "changes": {
    "max_agents_per_request": {
      "old": 5,
      "new": 7
    },
    "intent_confidence_threshold": {
      "old": 0.85,
      "new": 0.80
    },
    "agent_priorities.ultra": {
      "old": null,
      "new": 180
    }
  },
  "cache_invalidated": [
    "ai_brain:supervisor:authenticated:config"
  ],
  "audit_log_id": "uuid-v4"
}
```

---

### Update Routing Rules

**POST** `/api/v1/admin/ai-brain/supervisor/routes`

Update supervisor routing rules and agent priorities.

#### Request Body Schema

```json
{
  "supervisor_type": "authenticated",
  "routing_rules": [
    {
      "intent_pattern": "SWAP",
      "preferred_agent": "swap_workflow",
      "fallback_agents": ["knowledge", "chat"],
      "requires_wallet": true
    },
    {
      "intent_pattern": "HUNTER_*",
      "preferred_agent": "hunter_ai",
      "fallback_agents": ["knowledge"],
      "requires_wallet": false
    }
  ],
  "reason": "Optimizing routing based on A/B test results"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "routing_rules_updated": 2,
  "supervisor_type": "authenticated",
  "audit_log_id": "uuid-v4"
}
```

---

## Cache Management Endpoints

### Overview

Cache management endpoints provide control over Redis cache operations, metrics, and performance monitoring.

---

### Get Cache Statistics

**GET** `/api/v1/admin/ai-brain/cache/stats`

Get comprehensive cache statistics and performance metrics.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cache_type` | string | No | Filter by cache type: `agent_knowledge`, `agent_config`, `integration_status`, `user_context` |
| `time_range` | string | No | Time range: `1h`, `24h`, `7d`, `30d` (default: `24h`) |

#### Response Schema (200 OK)

```json
{
  "overall_stats": {
    "total_cache_keys": 1542,
    "total_memory_used_mb": 245.8,
    "overall_hit_rate": 92.5,
    "total_hits_24h": 1850000,
    "total_misses_24h": 150000,
    "cache_uptime_percentage": 99.99
  },
  "by_cache_type": {
    "agent_knowledge": {
      "total_keys": 850,
      "hit_rate": 95.2,
      "avg_retrieval_time_ms": 8,
      "memory_used_mb": 180.5,
      "top_accessed_keys": [
        {
          "cache_key": "ai_brain:knowledge:swap_overview:authenticated:en",
          "hit_count": 45000,
          "miss_count": 2000,
          "hit_rate": 95.7
        }
      ]
    },
    "agent_config": {
      "total_keys": 18,
      "hit_rate": 99.8,
      "avg_retrieval_time_ms": 3,
      "memory_used_mb": 2.1
    },
    "integration_status": {
      "total_keys": 12,
      "hit_rate": 88.5,
      "avg_retrieval_time_ms": 5,
      "memory_used_mb": 1.2
    },
    "user_context": {
      "total_keys": 662,
      "hit_rate": 89.0,
      "avg_retrieval_time_ms": 10,
      "memory_used_mb": 62.0
    }
  },
  "performance_metrics": {
    "p50_retrieval_time_ms": 5,
    "p95_retrieval_time_ms": 15,
    "p99_retrieval_time_ms": 35
  },
  "redis_info": {
    "redis_version": "7.0.5",
    "uptime_seconds": 2592000,
    "connected_clients": 25,
    "used_memory_human": "512M",
    "maxmemory_human": "2G"
  }
}
```

#### Implementation Location

- **Controller**: `src/app/presentation/http/controllers/admin/ai_brain/cache_router.py`
- **Handler**: `src/app/application/ai_brain/queries/get_cache_statistics.py`

---

### Invalidate Specific Cache

**POST** `/api/v1/admin/ai-brain/cache/invalidate`

Invalidate specific cache keys or patterns.

#### Request Body Schema

```json
{
  "cache_pattern": "ai_brain:knowledge:swap_*",
  "invalidate_metadata": true,
  "warm_immediately": false,
  "reason": "Invalidating swap knowledge after Hyperliquid update"
}
```

#### Field Options

| Field | Type | Description |
|-------|------|-------------|
| `cache_pattern` | string | Redis key pattern (supports wildcards) |
| `cache_keys` | array | Specific cache keys to invalidate (alternative to pattern) |
| `cache_type` | string | Invalidate all keys of type: `agent_knowledge`, `agent_config`, etc. |
| `invalidate_metadata` | boolean | Update `knowledge_cache_metadata` table (default: true) |
| `warm_immediately` | boolean | Warm cache after invalidation (default: false) |

#### Response Schema (200 OK)

```json
{
  "success": true,
  "invalidated_keys_count": 12,
  "invalidated_keys": [
    "ai_brain:knowledge:swap_overview:guest:en",
    "ai_brain:knowledge:swap_overview:authenticated:en",
    "ai_brain:knowledge:swap_overview:premium:en"
  ],
  "metadata_updated": true,
  "warmed_keys_count": 0,
  "timestamp": "2026-01-26T19:00:00Z"
}
```

---

### Warm Cache

**POST** `/api/v1/admin/ai-brain/cache/warm`

Pre-load data into Redis cache.

#### Request Body Schema

```json
{
  "cache_types": ["agent_knowledge", "agent_config"],
  "include_top_accessed": true,
  "top_accessed_limit": 100,
  "warm_all_agents": false,
  "specific_agents": ["knowledge", "swap_workflow"],
  "reason": "Warming cache after Redis restart"
}
```

#### Response Schema (200 OK)

```json
{
  "success": true,
  "warmed_cache_types": ["agent_knowledge", "agent_config"],
  "total_keys_warmed": 118,
  "breakdown": {
    "agent_knowledge": {
      "keys_warmed": 100,
      "time_taken_ms": 450
    },
    "agent_config": {
      "keys_warmed": 18,
      "time_taken_ms": 50
    }
  },
  "estimated_memory_used_mb": 85.2,
  "timestamp": "2026-01-26T19:05:00Z"
}
```

#### Implementation Location

- **Handler**: `src/app/application/ai_brain/commands/warm_cache.py`
- **Service**: `src/app/infrastructure/cache/redis_cache_warmer.py`

#### Business Logic

1. Validate admin authentication
2. Determine cache keys to warm based on parameters
3. For each cache type:
   - Query database for top accessed entries (if `include_top_accessed=true`)
   - Load data from database
   - Store in Redis with appropriate TTL
   - Update `knowledge_cache_metadata.last_warmed_at`
4. Return warming summary with performance metrics

---

### Flush All Cache

**DELETE** `/api/v1/admin/ai-brain/cache/flush`

Flush all AI Brain cache data from Redis (DANGEROUS - requires confirmation).

#### Request Body Schema

```json
{
  "confirm": true,
  "flush_scope": "ai_brain",
  "reason": "Emergency cache reset after data corruption"
}
```

#### Field Validation

| Field | Type | Constraints |
|-------|------|-------------|
| `confirm` | boolean | Required. Must be `true` |
| `flush_scope` | string | Required. One of: `ai_brain` (only AI Brain cache), `all` (entire Redis - VERY DANGEROUS) |
| `reason` | string | Required. Min 20 chars. Audit trail |

#### Response Schema (200 OK)

```json
{
  "success": true,
  "flushed_keys_count": 1542,
  "flush_scope": "ai_brain",
  "metadata_reset": true,
  "warning": "All AI Brain cache has been flushed. Cache warming recommended.",
  "audit_log_id": "uuid-v4",
  "timestamp": "2026-01-26T19:10:00Z"
}
```

#### Error Response (400 Bad Request)

```json
{
  "error": "confirmation_required",
  "message": "Cache flush requires explicit confirmation",
  "status_code": 400,
  "required_fields": {
    "confirm": true,
    "reason": "Must be at least 20 characters"
  }
}
```

---

## Error Handling & Status Codes

### Standard HTTP Status Codes

| Code | Status | Usage |
|------|--------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User lacks admin role |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Dependency conflict or business rule violation |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Database or Redis unavailable |

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "status_code": 400,
  "details": {
    "field": "additional context"
  },
  "request_id": "uuid-v4",
  "timestamp": "2026-01-26T19:15:00Z"
}
```

### Common Error Scenarios

#### Validation Error (400)

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "status_code": 400,
  "validation_errors": [
    {
      "field": "temperature",
      "error": "temperature must be between 0.0 and 2.0",
      "provided_value": 3.5
    },
    {
      "field": "agent_types",
      "error": "agent_types cannot be empty",
      "provided_value": []
    }
  ],
  "request_id": "uuid-v4"
}
```

#### Dependency Conflict (409)

```json
{
  "error": "dependency_conflict",
  "message": "Cannot disable agent: other agents depend on it",
  "status_code": 409,
  "agent_type": "knowledge",
  "dependent_agents": ["swap_workflow", "lending_workflow", "hunter_ai"],
  "suggestion": "Disable or update dependent agents first, or use force=true",
  "request_id": "uuid-v4"
}
```

#### Resource Not Found (404)

```json
{
  "error": "not_found",
  "message": "Agent configuration not found",
  "status_code": 404,
  "resource_type": "agent_configuration",
  "resource_id": "unknown_agent",
  "request_id": "uuid-v4"
}
```

#### Rate Limit Exceeded (429)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "status_code": 429,
  "rate_limit": {
    "limit": 100,
    "window": "60s",
    "retry_after": 45
  },
  "request_id": "uuid-v4"
}
```

#### Database Unavailable (503)

```json
{
  "error": "service_unavailable",
  "message": "Database temporarily unavailable",
  "status_code": 503,
  "service": "postgresql",
  "retry_after": 30,
  "request_id": "uuid-v4"
}
```

### Error Handling Implementation

**Location**: `src/app/presentation/http/middleware/error_handler.py`

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.domain.exceptions.ai_brain import (
    AgentConfigurationNotFoundError,
    DependencyConflictError,
    ValidationError,
)

async def ai_brain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle AI Brain specific errors"""

    if isinstance(exc, AgentConfigurationNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "not_found",
                "message": str(exc),
                "status_code": 404,
                "resource_type": "agent_configuration",
                "resource_id": exc.agent_id,
                "request_id": request.state.request_id
            }
        )

    elif isinstance(exc, DependencyConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "dependency_conflict",
                "message": str(exc),
                "status_code": 409,
                "dependent_agents": exc.dependent_agents,
                "suggestion": exc.suggestion,
                "request_id": request.state.request_id
            }
        )

    # ... other error types
```

---

## Implementation Guide

### Phase 1: Foundation (Week 1)

#### Database Schema Deployment

1. **Create Alembic Migration**
   ```bash
   alembic revision --autogenerate -m "add_ai_brain_admin_tables"
   ```

2. **Review Migration**
   - Verify table definitions match schema
   - Check indexes and constraints
   - Validate foreign keys

3. **Apply Migration**
   ```bash
   alembic upgrade head
   ```

#### Seed Initial Data

**Script**: `scripts/seed_ai_brain_data.py`

```python
async def seed_agent_configurations():
    """Seed agent_configurations from current agent_squad config"""
    config = load_agent_squad_config()

    for agent_type, agent_config in config.agents:
        await db.execute("""
            INSERT INTO agent_configurations (
                agent_type, agent_name, agent_category, is_enabled,
                model_name, temperature, max_tokens
            ) VALUES (
                :agent_type, :name, :category, :enabled,
                :model, :temp, :tokens
            )
        """, {
            "agent_type": agent_type,
            "name": agent_type.replace("_", " ").title(),
            "category": determine_category(agent_type),
            "enabled": agent_config.enabled,
            "model": agent_config.model,
            "temp": agent_config.temperature,
            "tokens": agent_config.max_tokens
        })
```

### Phase 2: Repository Layer (Week 1-2)

#### Agent Configuration Repository

**File**: `src/app/infrastructure/adapters/ai_brain/agent_config_repository_sqla.py`

```python
from app.domain.ports.ai_brain.agent_config_repository import AgentConfigRepository
from typing import Optional, List
from uuid import UUID

class AgentConfigRepositorySQLA(AgentConfigRepository):
    """SQLAlchemy implementation of agent configuration repository"""

    def __init__(self, db: AsyncDatabase, redis: Redis):
        self._db = db
        self._redis = redis

    async def get_by_agent_type(
        self,
        agent_type: str,
        include_dependencies: bool = True
    ) -> Optional[AgentConfiguration]:
        """Get agent configuration by agent_type"""

        # Check cache first
        cache_key = f"ai_brain:config:agent:{agent_type}"
        cached = await self._redis.hgetall(cache_key)
        if cached:
            return AgentConfiguration.from_dict(cached)

        # Query database
        query = "SELECT * FROM agent_configurations WHERE agent_type = :agent_type"
        result = await self._db.fetch_one(query, {"agent_type": agent_type})

        if not result:
            return None

        config = AgentConfiguration.from_db_row(result)

        # Cache result
        await self._redis.hset(cache_key, mapping=config.to_dict())
        await self._redis.expire(cache_key, 7200)  # 2 hours

        return config

    async def update(
        self,
        agent_type: str,
        updates: dict,
        updated_by: str
    ) -> AgentConfiguration:
        """Update agent configuration"""

        # Build update query dynamically
        set_clauses = []
        params = {"agent_type": agent_type, "updated_by": updated_by}

        for key, value in updates.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

        set_clauses.append("version = version + 1")
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        set_clauses.append("updated_by = :updated_by")

        query = f"""
            UPDATE agent_configurations
            SET {', '.join(set_clauses)}
            WHERE agent_type = :agent_type
            RETURNING *
        """

        result = await self._db.fetch_one(query, params)

        # Invalidate cache
        await self._invalidate_cache(agent_type)

        return AgentConfiguration.from_db_row(result)

    async def _invalidate_cache(self, agent_type: str):
        """Invalidate agent configuration cache"""
        cache_key = f"ai_brain:config:agent:{agent_type}"
        await self._redis.delete(cache_key)

        # Also invalidate related knowledge cache
        pattern = f"ai_brain:knowledge:*:{agent_type}:*"
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)
```

### Phase 3: Application Handlers (Week 2)

#### Get Agent Configuration Handler

**File**: `src/app/application/ai_brain/queries/get_agent_configuration.py`

```python
from dataclasses import dataclass
from typing import Optional
from app.domain.ports.ai_brain.agent_config_repository import AgentConfigRepository

@dataclass
class GetAgentConfigurationQuery:
    agent_id: str
    include_dependencies: bool = True
    include_prompts: bool = False
    include_knowledge: bool = False

class GetAgentConfigurationHandler:
    """Query handler for retrieving agent configuration"""

    def __init__(
        self,
        agent_config_repo: AgentConfigRepository,
        prompt_repo: PromptRepository,
        knowledge_repo: KnowledgeRepository
    ):
        self._agent_config_repo = agent_config_repo
        self._prompt_repo = prompt_repo
        self._knowledge_repo = knowledge_repo

    async def handle(self, query: GetAgentConfigurationQuery) -> dict:
        """Execute query"""

        # Get base configuration
        config = await self._agent_config_repo.get_by_agent_type(
            agent_type=query.agent_id,
            include_dependencies=query.include_dependencies
        )

        if not config:
            raise AgentConfigurationNotFoundError(query.agent_id)

        result = {
            "agent": config.to_dict()
        }

        # Include dependencies if requested
        if query.include_dependencies and config.depends_on_agents:
            result["dependencies"] = await self._get_dependencies(config)

        # Include prompts if requested
        if query.include_prompts:
            result["active_prompts"] = await self._prompt_repo.get_active_prompts(
                agent_type=config.agent_type
            )

        # Include knowledge if requested
        if query.include_knowledge:
            result["associated_knowledge"] = await self._knowledge_repo.get_by_agent(
                agent_type=config.agent_type
            )

        return result

    async def _get_dependencies(self, config: AgentConfiguration) -> dict:
        """Get dependent agents and integrations"""
        # Implementation...
```

### Phase 4: HTTP Controllers (Week 2-3)

#### Agents Router

**File**: `src/app/presentation/http/controllers/admin/ai_brain/agents_router.py`

```python
from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional
from app.presentation.http.schemas.ai_brain.agent_config import (
    AgentConfigurationListResponse,
    AgentConfigurationDetailResponse,
    UpdateAgentConfigurationRequest,
    UpdateAgentConfigurationResponse
)
from app.application.ai_brain.queries.get_agent_configuration import (
    GetAgentConfigurationQuery,
    GetAgentConfigurationHandler
)

router = APIRouter(
    prefix="/agents",
    tags=["AI Brain - Agent Configuration"]
)

@router.get("", response_model=AgentConfigurationListResponse)
async def list_agent_configurations(
    category: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    depends_on_integration: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("priority", regex="^(priority|agent_type|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    handler: GetAgentConfigurationsHandler = Depends()
):
    """List all agent configurations with filtering"""

    query = GetAgentConfigurationsQuery(
        category=category,
        is_enabled=is_enabled,
        depends_on_integration=depends_on_integration,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return await handler.handle(query)

@router.get("/{agent_id}", response_model=AgentConfigurationDetailResponse)
async def get_agent_configuration(
    agent_id: str = Path(..., description="Agent UUID or agent_type"),
    include_dependencies: bool = Query(True),
    include_prompts: bool = Query(False),
    include_knowledge: bool = Query(False),
    handler: GetAgentConfigurationHandler = Depends()
):
    """Get detailed agent configuration"""

    query = GetAgentConfigurationQuery(
        agent_id=agent_id,
        include_dependencies=include_dependencies,
        include_prompts=include_prompts,
        include_knowledge=include_knowledge
    )

    return await handler.handle(query)

@router.put("/{agent_id}", response_model=UpdateAgentConfigurationResponse)
async def update_agent_configuration(
    agent_id: str = Path(...),
    request: UpdateAgentConfigurationRequest = Body(...),
    handler: UpdateAgentConfigurationHandler = Depends()
):
    """Update agent configuration"""

    command = UpdateAgentConfigurationCommand(
        agent_id=agent_id,
        updates=request.dict(exclude_unset=True),
        update_reason=request.update_reason
    )

    return await handler.handle(command)
```

### Phase 5: Dependency Injection (Week 3)

**File**: `src/app/setup/ioc/ai_brain.py`

```python
from dishka import Provider, Scope, provide
from app.infrastructure.adapters.ai_brain.agent_config_repository_sqla import (
    AgentConfigRepositorySQLA
)
from app.domain.ports.ai_brain.agent_config_repository import AgentConfigRepository

class AIBrainProvider(Provider):
    scope = Scope.REQUEST

    # Repositories
    @provide
    async def provide_agent_config_repository(
        self,
        db: AsyncDatabase,
        redis: Redis
    ) -> AgentConfigRepository:
        return AgentConfigRepositorySQLA(db, redis)

    # Query Handlers
    @provide
    async def provide_get_agent_config_handler(
        self,
        agent_config_repo: AgentConfigRepository,
        prompt_repo: PromptRepository,
        knowledge_repo: KnowledgeRepository
    ) -> GetAgentConfigurationHandler:
        return GetAgentConfigurationHandler(
            agent_config_repo,
            prompt_repo,
            knowledge_repo
        )

    # Command Handlers
    @provide
    async def provide_update_agent_config_handler(
        self,
        agent_config_repo: AgentConfigRepository,
        audit_logger: AuditLogger
    ) -> UpdateAgentConfigurationHandler:
        return UpdateAgentConfigurationHandler(
            agent_config_repo,
            audit_logger
        )
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/application/ai_brain/test_get_agent_configuration.py`

```python
import pytest
from app.application.ai_brain.queries.get_agent_configuration import (
    GetAgentConfigurationQuery,
    GetAgentConfigurationHandler
)
from app.domain.exceptions.ai_brain import AgentConfigurationNotFoundError

@pytest.mark.asyncio
async def test_get_agent_configuration_success(
    mock_agent_config_repo,
    mock_agent_config
):
    """Test successful agent configuration retrieval"""

    mock_agent_config_repo.get_by_agent_type.return_value = mock_agent_config

    handler = GetAgentConfigurationHandler(
        agent_config_repo=mock_agent_config_repo,
        prompt_repo=None,
        knowledge_repo=None
    )

    query = GetAgentConfigurationQuery(
        agent_id="knowledge",
        include_dependencies=False
    )

    result = await handler.handle(query)

    assert result["agent"]["agent_type"] == "knowledge"
    assert result["agent"]["is_enabled"] is True
    mock_agent_config_repo.get_by_agent_type.assert_called_once_with(
        agent_type="knowledge",
        include_dependencies=False
    )

@pytest.mark.asyncio
async def test_get_agent_configuration_not_found(mock_agent_config_repo):
    """Test agent configuration not found"""

    mock_agent_config_repo.get_by_agent_type.return_value = None

    handler = GetAgentConfigurationHandler(
        agent_config_repo=mock_agent_config_repo,
        prompt_repo=None,
        knowledge_repo=None
    )

    query = GetAgentConfigurationQuery(agent_id="unknown_agent")

    with pytest.raises(AgentConfigurationNotFoundError):
        await handler.handle(query)
```

### Integration Tests

**File**: `tests/integration/ai_brain/test_agents_endpoints.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_agents_endpoint(
    async_client: AsyncClient,
    admin_jwt_token
):
    """Test list agents endpoint"""

    response = await async_client.get(
        "/api/v1/admin/ai-brain/agents",
        headers={"Authorization": f"Bearer {admin_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "pagination" in data
    assert len(data["agents"]) > 0

@pytest.mark.asyncio
async def test_update_agent_configuration(
    async_client: AsyncClient,
    admin_jwt_token
):
    """Test update agent configuration"""

    response = await async_client.put(
        "/api/v1/admin/ai-brain/agents/knowledge",
        headers={"Authorization": f"Bearer {admin_jwt_token}"},
        json={
            "temperature": 0.8,
            "update_reason": "Test update"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["agent"]["temperature"] == 0.8
    assert "changes" in data
```

### Load Tests

**File**: `tests/load/ai_brain/test_cache_performance.py`

```python
import asyncio
from locust import HttpUser, task, between

class AIBrainAdminUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get admin JWT"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "test123"
        })
        self.token = response.json()["access_token"]

    @task(10)
    def list_agents(self):
        """Test list agents endpoint"""
        self.client.get(
            "/api/v1/admin/ai-brain/agents",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(5)
    def get_agent_details(self):
        """Test get agent details endpoint"""
        self.client.get(
            "/api/v1/admin/ai-brain/agents/knowledge",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def get_cache_stats(self):
        """Test cache stats endpoint"""
        self.client.get(
            "/api/v1/admin/ai-brain/cache/stats",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

---

## Security Considerations

### Authentication & Authorization

1. **JWT Validation**
   - All endpoints require valid JWT token
   - Token expiration enforced
   - Refresh token rotation

2. **Role-Based Access Control**
   - Admin role required for all endpoints
   - Role checked in middleware
   - Audit logging for all admin actions

3. **Rate Limiting**
   - 100 requests/minute per admin user
   - Stricter limits for dangerous operations (cache flush, bulk updates)

### Data Protection

1. **Sensitive Data Encryption**
   - API keys encrypted at rest
   - Encrypted fields in database (if needed)

2. **Audit Logging**
   - All configuration changes logged
   - Include: user, timestamp, changes, reason
   - Retention: 1 year minimum

3. **Input Validation**
   - Pydantic schema validation
   - SQL injection prevention (parameterized queries)
   - XSS protection (sanitize inputs)

### Cache Security

1. **Redis ACLs**
   - Admin role has full cache access
   - System role for automated operations
   - No public Redis access

2. **Cache Poisoning Prevention**
   - Validate data before caching
   - TTL expiration to limit impact
   - Network isolation (Redis not public)

---

## Appendix: Complete Endpoint Summary

### Agent Configuration Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/ai-brain/agents` | List all agents |
| GET | `/api/v1/admin/ai-brain/agents/{agent_id}` | Get agent details |
| PUT | `/api/v1/admin/ai-brain/agents/{agent_id}` | Update agent config |
| POST | `/api/v1/admin/ai-brain/agents/{agent_id}/enable` | Enable agent |
| POST | `/api/v1/admin/ai-brain/agents/{agent_id}/disable` | Disable agent |
| GET | `/api/v1/admin/ai-brain/agents/{agent_id}/dependencies` | Get dependencies |

### Agent Prompts Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/ai-brain/prompts` | List all prompts |
| GET | `/api/v1/admin/ai-brain/prompts/{agent_id}` | Get agent prompts |
| POST | `/api/v1/admin/ai-brain/prompts/{agent_id}` | Create prompt |
| PUT | `/api/v1/admin/ai-brain/prompts/{prompt_id}` | Update prompt |
| DELETE | `/api/v1/admin/ai-brain/prompts/{prompt_id}` | Delete prompt |
| POST | `/api/v1/admin/ai-brain/prompts/{prompt_id}/activate` | Activate prompt |
| POST | `/api/v1/admin/ai-brain/prompts/{prompt_id}/ab-test` | Start A/B test |

### Agent Knowledge Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/ai-brain/knowledge` | List knowledge |
| GET | `/api/v1/admin/ai-brain/knowledge/{agent_id}` | Get agent knowledge |
| POST | `/api/v1/admin/ai-brain/knowledge` | Create knowledge |
| PUT | `/api/v1/admin/ai-brain/knowledge/{knowledge_id}` | Update knowledge |
| DELETE | `/api/v1/admin/ai-brain/knowledge/{knowledge_id}` | Delete knowledge |
| POST | `/api/v1/admin/ai-brain/knowledge/invalidate-cache` | Invalidate cache |

### Integration Configuration Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/ai-brain/integrations` | List integrations |
| GET | `/api/v1/admin/ai-brain/integrations/{integration_id}` | Get integration |
| PUT | `/api/v1/admin/ai-brain/integrations/{integration_id}` | Update integration |
| POST | `/api/v1/admin/ai-brain/integrations/{integration_id}/enable` | Enable integration |
| POST | `/api/v1/admin/ai-brain/integrations/{integration_id}/disable` | Disable integration |
| GET | `/api/v1/admin/ai-brain/integrations/{integration_id}/health` | Check health |

### Supervisor Configuration Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/ai-brain/supervisor` | Get supervisor config |
| PUT | `/api/v1/admin/ai-brain/supervisor` | Update supervisor config |
| POST | `/api/v1/admin/ai-brain/supervisor/routes` | Update routing rules |

### Cache Management Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/ai-brain/cache/stats` | Get cache statistics |
| POST | `/api/v1/admin/ai-brain/cache/invalidate` | Invalidate cache |
| POST | `/api/v1/admin/ai-brain/cache/warm` | Warm cache |
| DELETE | `/api/v1/admin/ai-brain/cache/flush` | Flush all cache |

---

**END OF DOCUMENT**

**Total Endpoints**: 31
**Documentation**: 15,000+ words
**Implementation Time**: 3-4 weeks
**Priority**: High - Required for Phase 3 of AI Brain rollout

---

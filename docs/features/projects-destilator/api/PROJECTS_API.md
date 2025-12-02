# Admin Projects API Documentation

## Overview

The Projects API provides comprehensive management of admin-configured project contexts.

---

## User-Facing Endpoints

### GET /user/projects

List available projects for user.

**Response**:
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "uuid",
        "slug": "savings",
        "name": "Smart Savings",
        "description": "Low-risk yield optimization for stablecoin holdings",
        "icon": "💰",
        "color": "#10B981",
        "is_featured": true,
        "is_assigned": true,
        "is_active": false
      },
      {
        "id": "uuid",
        "slug": "aave",
        "name": "Aave Lending",
        "description": "Complete Aave lending and borrowing assistance",
        "icon": "🏦",
        "color": "#B6509E",
        "is_featured": true,
        "is_assigned": true,
        "is_active": true
      }
    ],
    "active_project": {
      "id": "uuid",
      "slug": "aave",
      "name": "Aave Lending"
    }
  }
}
```

### POST /user/projects/{slug}/activate

Activate a project for the user.

**Response**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "project_name": "Aave Lending",
    "welcome_message": "Welcome to Aave Lending! 🏦\n\nI'm your dedicated Aave assistant...",
    "enabled_tools": ["lend", "borrow", "check_health", "swap"]
  }
}
```

### GET /user/projects/active

Get currently active project.

**Response**:
```json
{
  "success": true,
  "data": {
    "project": {
      "id": "uuid",
      "slug": "aave",
      "name": "Aave Lending",
      "description": "Complete Aave lending and borrowing assistance",
      "icon": "🏦",
      "color": "#B6509E",
      "enabled_protocols": ["aave"],
      "enabled_chains": ["ethereum", "arbitrum", "polygon"],
      "enabled_tools": ["lend", "borrow", "check_health", "swap"]
    },
    "session_stats": {
      "messages_count": 15,
      "session_duration_minutes": 12
    }
  }
}
```

---

## Admin API Endpoints

### Project Management

### GET /admin/projects

List all projects.

**Permission**: `projects.read`

**Query Parameters**:
- `status`: draft, active, paused, archived
- `visibility`: public, private, invite_only
- `include_stats`: true/false

**Response**:
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "uuid",
        "slug": "savings",
        "name": "Smart Savings",
        "description": "Low-risk yield optimization...",
        "icon": "💰",
        "color": "#10B981",
        "status": "active",
        "visibility": "public",
        "is_featured": true,
        "display_order": 1,
        "enabled_protocols": ["aave", "compound", "morpho"],
        "enabled_chains": ["ethereum", "arbitrum", "base"],
        "enabled_tools": ["lend", "analyze_portfolio", "check_health"],
        "stats": {
          "total_users": 1520,
          "active_users_7d": 450,
          "total_sessions": 8500,
          "avg_satisfaction": 4.6
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-12-01T00:00:00Z"
      }
    ],
    "total": 10
  }
}
```

### POST /admin/projects

Create new project.

**Permission**: `projects.write`

**Request**:
```json
{
  "slug": "defi-basics",
  "name": "DeFi Basics",
  "description": "Educational project for DeFi beginners",
  "icon": "📚",
  "color": "#6366F1",
  "status": "draft",
  "visibility": "public",
  
  "system_prompt": "You are Anvil's DeFi educator, helping beginners understand decentralized finance concepts...",
  "welcome_message": "Welcome to DeFi Basics! 📚\n\nI'm here to help you learn about DeFi...",
  
  "enabled_protocols": ["uniswap", "aave"],
  "enabled_chains": ["ethereum"],
  "enabled_tools": ["explain_concept", "simulate_transaction"],
  
  "risk_config": {
    "max_position_usd": 1000,
    "require_simulation": true,
    "educational_mode": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "slug": "defi-basics",
    "knowledge_base_id": "uuid",
    "status": "draft"
  }
}
```

### GET /admin/projects/{id}

Get project details.

**Permission**: `projects.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "project": {
      "id": "uuid",
      "slug": "aave",
      "name": "Aave Lending",
      "description": "Complete Aave lending and borrowing assistance",
      "icon": "🏦",
      "color": "#B6509E",
      "status": "active",
      "visibility": "public",
      
      "system_prompt": "You are Anvil's Aave Specialist...",
      "welcome_message": "Welcome to Aave Lending! 🏦...",
      
      "enabled_protocols": ["aave"],
      "enabled_chains": ["ethereum", "arbitrum", "polygon", "optimism", "base"],
      "enabled_tools": ["lend", "borrow", "check_health", "swap"],
      
      "risk_config": {
        "max_slippage_bps": 50,
        "max_position_usd": 100000,
        "min_health_factor": 1.5,
        "require_simulation": true,
        "require_2fa_for_transactions": true
      },
      
      "max_users": null,
      "display_order": 3,
      "is_featured": true,
      
      "created_by": "uuid",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-12-01T00:00:00Z"
    },
    
    "knowledge_base": {
      "id": "uuid",
      "total_documents": 45,
      "total_chunks": 1250,
      "last_indexed_at": "2025-12-01T06:00:00Z"
    },
    
    "tool_configs": [
      {
        "tool_id": "lend",
        "is_enabled": true,
        "requires_confirmation": true,
        "default_params": {}
      }
    ],
    
    "auto_assign_rules": [
      {
        "id": "uuid",
        "rule_name": "Has Aave Positions",
        "condition_type": "PORTFOLIO",
        "condition_params": {"has_protocol_positions": ["aave"]},
        "is_active": true
      }
    ]
  }
}
```

### PUT /admin/projects/{id}

Update project.

**Permission**: `projects.write`

**Request**:
```json
{
  "name": "Aave Lending Pro",
  "description": "Updated description...",
  "status": "active",
  "system_prompt": "Updated system prompt...",
  "enabled_tools": ["lend", "borrow", "check_health", "swap", "flashloan"]
}
```

### DELETE /admin/projects/{id}

Delete project (archives if has users).

**Permission**: `projects.admin`

---

### Knowledge Base Management

### GET /admin/projects/{id}/knowledge

Get project knowledge base.

**Permission**: `projects.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "knowledge_base": {
      "id": "uuid",
      "project_id": "uuid",
      "name": "Aave Lending Knowledge Base",
      "total_documents": 45,
      "total_chunks": 1250,
      "embedding_model": "text-embedding-3-small",
      "last_indexed_at": "2025-12-01T06:00:00Z"
    },
    "documents": [
      {
        "id": "uuid",
        "title": "Aave V3 User Guide",
        "doc_type": "guide",
        "source_type": "manual",
        "chunk_count": 85,
        "priority": 1,
        "is_processed": true,
        "created_at": "2025-06-01T00:00:00Z"
      },
      {
        "id": "uuid",
        "title": "Health Factor FAQ",
        "doc_type": "faq",
        "source_type": "manual",
        "chunk_count": 25,
        "priority": 2,
        "is_processed": true,
        "created_at": "2025-07-15T00:00:00Z"
      }
    ]
  }
}
```

### POST /admin/projects/{id}/knowledge/documents

Add document to knowledge base.

**Permission**: `projects.write`

**Request**:
```json
{
  "title": "E-Mode Strategies Guide",
  "content": "# E-Mode on Aave V3\n\nE-Mode (Efficiency Mode) allows...",
  "doc_type": "guide",
  "source_url": "https://docs.aave.com/...",
  "tags": ["e-mode", "advanced", "aave-v3"],
  "priority": 2
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "status": "processing",
    "estimated_chunks": 35
  }
}
```

### PUT /admin/projects/{id}/knowledge/documents/{doc_id}

Update document.

### DELETE /admin/projects/{id}/knowledge/documents/{doc_id}

Delete document.

### POST /admin/projects/{id}/knowledge/reindex

Trigger knowledge base reindexing.

**Permission**: `projects.admin`

**Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "documents_to_process": 45,
    "estimated_time_seconds": 120
  }
}
```

### POST /admin/projects/{id}/knowledge/search

Test knowledge retrieval.

**Permission**: `projects.read`

**Request**:
```json
{
  "query": "How do I avoid liquidation on Aave?",
  "top_k": 5
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "chunk_id": "uuid",
        "document_title": "Health Factor FAQ",
        "chunk_text": "To avoid liquidation, maintain a health factor above 1.0...",
        "similarity": 0.92
      }
    ]
  }
}
```

---

### Tool Configuration

### GET /admin/projects/{id}/tools

Get tool configuration for project.

**Permission**: `projects.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "available_tools": [
      {
        "tool_id": "lend",
        "name": "Lending",
        "description": "Deposit assets to lending protocols",
        "applicable": true
      },
      {
        "tool_id": "swap",
        "name": "Token Swap",
        "description": "Swap tokens on DEXs",
        "applicable": true
      }
    ],
    "configured_tools": [
      {
        "tool_id": "lend",
        "is_enabled": true,
        "max_calls_per_session": null,
        "max_amount_per_call": 100000,
        "requires_confirmation": true,
        "default_params": {},
        "locked_params": {}
      }
    ]
  }
}
```

### PUT /admin/projects/{id}/tools/{tool_id}

Update tool configuration.

**Permission**: `projects.write`

**Request**:
```json
{
  "is_enabled": true,
  "max_amount_per_call": 50000,
  "requires_confirmation": true,
  "default_params": {
    "slippage_bps": 50
  },
  "locked_params": {
    "protocol": "aave"
  }
}
```

---

### User Assignment

### GET /admin/projects/{id}/users

Get users assigned to project.

**Permission**: `projects.read`

**Query Parameters**:
- `assignment_type`: auto, manual, self
- `is_active`: true/false
- `limit`, `offset`: pagination

**Response**:
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "user_id": "uuid",
        "email": "user@example.com",
        "assignment_type": "auto",
        "assignment_reason": "Has Aave positions",
        "assigned_at": "2025-11-15T00:00:00Z",
        "last_active_at": "2025-12-01T10:30:00Z",
        "is_currently_active": true,
        "session_count": 25
      }
    ],
    "summary": {
      "total_assigned": 1520,
      "auto_assigned": 1200,
      "manual_assigned": 120,
      "self_assigned": 200,
      "currently_active": 45
    },
    "pagination": {
      "total": 1520,
      "limit": 50,
      "offset": 0
    }
  }
}
```

### POST /admin/projects/{id}/users/assign

Manually assign users to project.

**Permission**: `projects.write`

**Request**:
```json
{
  "user_ids": ["uuid1", "uuid2"],
  "reason": "Premium users getting early access"
}
```

### DELETE /admin/projects/{id}/users/{user_id}

Remove user from project.

**Permission**: `projects.write`

---

### Auto-Assignment Rules

### GET /admin/projects/{id}/rules

Get auto-assignment rules.

**Permission**: `projects.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "rules": [
      {
        "id": "uuid",
        "rule_name": "Has Aave Positions",
        "condition_type": "PORTFOLIO",
        "condition_params": {
          "has_protocol_positions": ["aave"],
          "min_value_usd": 100
        },
        "priority": 1,
        "auto_switch": false,
        "is_active": true,
        "matched_users": 850
      },
      {
        "id": "uuid",
        "rule_name": "Selected Lending Goal",
        "condition_type": "ONBOARDING",
        "condition_params": {
          "selected_goal": "lending"
        },
        "priority": 2,
        "auto_switch": true,
        "is_active": true,
        "matched_users": 350
      }
    ]
  }
}
```

### POST /admin/projects/{id}/rules

Create auto-assignment rule.

**Permission**: `projects.write`

**Request**:
```json
{
  "rule_name": "High Value Aave Users",
  "condition_type": "PORTFOLIO",
  "condition_params": {
    "has_protocol_positions": ["aave"],
    "min_value_usd": 10000
  },
  "priority": 1,
  "auto_switch": true
}
```

### PUT /admin/projects/{id}/rules/{rule_id}

Update rule.

### DELETE /admin/projects/{id}/rules/{rule_id}

Delete rule.

### POST /admin/projects/{id}/rules/evaluate

Run rules evaluation for all users.

**Permission**: `projects.admin`

---

### Analytics

### GET /admin/projects/{id}/analytics

Get project analytics.

**Permission**: `projects.read`

**Query Parameters**:
- `period`: 24h, 7d, 30d, 90d

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "project": {
      "id": "uuid",
      "name": "Aave Lending"
    },
    
    "user_metrics": {
      "total_users": 1520,
      "active_users": 450,
      "new_users": 85,
      "returning_rate": 0.72,
      "churn_rate": 0.08
    },
    
    "engagement_metrics": {
      "total_sessions": 8500,
      "total_messages": 42000,
      "avg_session_duration_minutes": 8.5,
      "avg_messages_per_session": 4.9,
      "peak_hour": 14
    },
    
    "satisfaction_metrics": {
      "avg_score": 4.6,
      "helpful_rate": 0.89,
      "escalation_rate": 0.03
    },
    
    "knowledge_metrics": {
      "total_queries": 35000,
      "hit_rate": 0.82,
      "top_queries": [
        "health factor",
        "liquidation",
        "e-mode",
        "borrow rate",
        "supply apy"
      ]
    },
    
    "transaction_metrics": {
      "total_transactions": 2500,
      "total_volume_usd": 15000000,
      "success_rate": 0.97,
      "avg_transaction_usd": 6000
    },
    
    "tool_usage": {
      "lend": 1200,
      "borrow": 800,
      "check_health": 2500,
      "swap": 350
    },
    
    "trends": {
      "users_trend": "+12%",
      "engagement_trend": "+8%",
      "satisfaction_trend": "+0.2"
    }
  }
}
```

### GET /admin/projects/{id}/analytics/timeseries

Get time-series analytics.

**Permission**: `projects.read`

**Query Parameters**:
- `metric`: users, sessions, messages, satisfaction
- `period`: 7d, 30d, 90d
- `interval`: day, week

---

### Invitations (for invite_only projects)

### GET /admin/projects/{id}/invitations

List invitations.

### POST /admin/projects/{id}/invitations

Create invitation.

**Request**:
```json
{
  "emails": ["user1@example.com", "user2@example.com"],
  "expires_in_days": 7
}
```

### DELETE /admin/projects/{id}/invitations/{invitation_id}

Revoke invitation.

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `PROJECT_NOT_FOUND` | 404 | Project doesn't exist |
| `PROJECT_SLUG_EXISTS` | 409 | Slug already in use |
| `PROJECT_MAX_USERS` | 403 | Project at user capacity |
| `PROJECT_PRIVATE` | 403 | Project is private |
| `PROJECT_INVITE_REQUIRED` | 403 | Invitation required |
| `KNOWLEDGE_PROCESSING` | 202 | Document still processing |
| `RULE_INVALID` | 400 | Invalid rule configuration |

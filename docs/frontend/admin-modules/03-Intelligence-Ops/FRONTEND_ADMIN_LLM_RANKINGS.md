# Admin Module: LLM Rankings

> **Technical Specification**: `FRONTEND_ADMIN_LLM_RANKINGS`
> **Backend Controller**: `admin/llm/rankings.py`
> **Base URL**: `/api/admin/llm/rankings`

## 📖 Overview
The **LLM Rankings** submodule enables administrators to view and manage model rankings for different agent types. Rankings determine which models are selected for specific agents based on performance metrics (success rate, latency, cost).

### Key Capabilities
1. **Ranking View**: View current model rankings per agent type.
2. **Weight Configuration**: Customize ranking weight profiles for agents.
3. **Ranking Recalculation**: Force recalculation of rankings based on latest performance data.
4. **Ranking Overrides**: Create manual overrides to force specific models for agents.

---

## 🔌 API Endpoints

### 1. Get Rankings
**GET** `/api/admin/llm/rankings`
View current rankings per agent type.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `agent_type` | `str` | No | Filter by agent type (e.g., "swap_agent"). |

**Response (`RankingResponse`)**:
```json
{
  "success": true,
  "data": {
    "rankings": [
      {
        "agent_type": "swap_agent",
        "models": [
          {
            "rank": 1,
            "model_id": "uuid",
            "model_name": "gemini-1.5-pro",
            "provider": "vertex_ai",
            "ranking_score": 0.8945,
            "success_rate": 0.985,
            "avg_latency_ms": 1100,
            "avg_cost_per_request": 0.0072,
            "total_requests": 8000,
            "has_override": false
          }
        ]
      }
    ],
    "last_recalculated_at": "2025-12-01T09:00:00Z"
  }
}
```

### 2. Update Ranking Weights
**PUT** `/api/admin/llm/rankings/weights`
Update ranking weight profiles for agents.

**Request Body (`UpdateWeightsRequest`)**:
```json
{
  "agent_type": "swap_agent",
  "weights": {
    "success_weight": 0.55,
    "latency_weight": 0.30,
    "cost_weight": 0.10,
    "recency_weight": 0.05
  }
}
```

**Response (`RankingResponse`)**:
```json
{
  "success": true,
  "data": {
    "agent_type": "swap_agent",
    "weights_updated": true
  }
}
```

### 3. Recalculate Rankings
**POST** `/api/admin/llm/rankings/recalculate`
Force ranking recalculation.

**Request Body (`RecalculateRequest`)**:
```json
{
  "agent_type": "swap_agent"
}
```

**Response (`RankingResponse`)**:
```json
{
  "success": true,
  "data": {
    "recalculated_count": 9,
    "agent_types_affected": ["swap_agent"],
    "duration_ms": 150
  }
}
```

### 4. Create Ranking Override
**POST** `/api/admin/llm/rankings/override`
Manually set model priority for agent.

**Request Body (`RankingOverrideRequest`)**:
```json
{
  "agent_type": "swap_agent",
  "model_id": "uuid",
  "override_score": 0.95,
  "reason": "Testing new model",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response (`RankingResponse`)**:
```json
{
  "success": true,
  "data": {
    "override_id": "uuid",
    "agent_type": "swap_agent",
    "model_id": "uuid",
    "override_score": 0.95,
    "created": true
  }
}
```

---

## 🎨 UI/UX Guidelines

### Rankings View
- **Agent Type Selector**: Dropdown to filter by agent type.
- **Ranking Table**: Table showing ranked models with:
  - **Rank**: Position number (1, 2, 3...)
  - **Model Name**: Model display name
  - **Provider**: Provider badge
  - **Ranking Score**: Visual score bar (0-1 scale)
  - **Metrics**: Success rate, avg latency, avg cost
  - **Total Requests**: Request count
  - **Override Badge**: Indicator if model has manual override
- **Color Coding**: 
  - Green for high-ranking models (rank 1-3)
  - Yellow for mid-ranking models (rank 4-6)
  - Grey for low-ranking models (rank 7+)
- **Last Recalculated**: Display timestamp of last recalculation.

### Weight Configuration
- **Weight Sliders**: Interactive sliders for each weight component:
  - Success weight
  - Latency weight
  - Cost weight
  - Recency weight
- **Total Validation**: Ensure weights sum to 1.0 (show warning if not).
- **Preview**: Show preview of how weights affect ranking scores.
- **Save Button**: Save button with confirmation.

### Recalculation
- **Trigger Button**: "Recalculate Rankings" button.
- **Confirmation Modal**: Confirm before triggering recalculation.
- **Progress Indicator**: Show progress during recalculation.
- **Results Display**: Show results after recalculation (affected models, duration).

### Ranking Overrides
- **Create Override Form**: Form to create new override:
  - Agent type selector
  - Model selector
  - Override score input
  - Reason textarea
  - Expiration date picker (optional)
- **Override List**: List of active overrides with:
  - Agent type
  - Model name
  - Override score
  - Reason
  - Expiration date
  - Remove button
- **Override Badge**: Visual indicator in rankings table for overridden models.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Weight Changes**: Require confirmation before updating weight profiles.
- **Override Management**: Log all override creations and removals for audit.

---

## 📝 Notes

- Rankings are automatically recalculated periodically based on performance data.
- Manual overrides take precedence over calculated rankings.
- Weight profiles can be customized per agent type for fine-tuned model selection.

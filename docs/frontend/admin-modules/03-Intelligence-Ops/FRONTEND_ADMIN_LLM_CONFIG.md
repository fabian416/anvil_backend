# Admin Module: LLM Configuration

> **Technical Specification**: `FRONTEND_ADMIN_LLM_CONFIG`
> **Backend Controller**: `admin/llm/models.py`
> **Base URL**: `/api/admin/llm/models`

## 📖 Overview
The **LLM Configuration** module allows admins to manage the AI models available to the platform. This includes enabling/disabling specific models, adjusting "Carousel Position" (frontend display order), and monitoring performance/costs per model.

### Key Capabilities
1.  **Model Registry**: View all integrated models (GPT-4, Claude 3, etc.).
2.  **Feature Toggles**: Enable or disable models globally.
3.  **Pricing Config**: View cost rates (Input/Output).
4.  **Performance Insights**: Track latency and success rates per model.

---

## 🔌 API Endpoints

### 1. List Models
**GET** `/api/admin/llm/models`
View all models with their configuration.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `provider_id` | `UUID` | No | Filter by provider (e.g., OpenAI, Anthropic). |
| `is_enabled` | `bool` | No | Filter by status. |
| `tier` | `str` | No | Filter by tier (`premium`, `standard`, `economy`). |

**Response (`ModelListResponse`)**:
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "uuid",
        "model_id": "gpt-4-turbo",
        "display_name": "GPT-4 Turbo",
        "is_enabled": true,
        "context_window": 128000,
        "carousel_position": 1,
        "tier": "premium",
        "circuit_breaker_state": "closed"
      }
    ],
    "total": 12
  }
}
```

### 2. Update Model
**PUT** `/api/admin/llm/models/{model_id}`
Modify model settings.

**Request Body (`UpdateModelRequest`)**:
```json
{
  "is_enabled": true,
  "carousel_position": 2,
  "cost_per_1k_input": 0.01,
  "cost_per_1k_output": 0.03
}
```

**Response**: `200 OK`

### 3. Model Performance
**GET** `/api/admin/llm/models/{model_id}/performance`
Get specific metrics for a model.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `period` | `str` | No | `24h`, `7d`, `30d` (Default: `24h`). |

**Response (`ModelPerformanceResponse`)**:
```json
{
  "data": {
    "model_id": "gpt-4-turbo",
    "metrics": {
      "success_rate": 0.99,
      "avg_latency_ms": 1200,
      "p95_latency_ms": 2500,
      "total_cost_usd": 150.00
    }
  }
}
```

---

## 🎨 UI/UX Guidelines

### Model Cards
- Display models as cards or a table.
- **Toggle Switch**: Prominent "Enabled/Disabled" toggle for quick action.
- **Status Indicators**: Show "Circuit Breaker" status (Open = Red, Closed = Green).

### Cost Display
- Display costs in specific decimal precision (e.g., `$0.00125`).
- Use tooltips to explain "Per 1K Tokens".

# Admin Module: LLM Circuit Breakers

> **Technical Specification**: `FRONTEND_ADMIN_LLM_CIRCUIT_BREAKERS`
> **Backend Controller**: `admin/llm/circuit_breakers.py`
> **Base URL**: `/api/admin/llm/circuit-breakers`

## 📖 Overview
**Circuit Breakers** are automated safety mechanisms that stop traffic to a failing model (e.g., if OpenAI is down) to prevent cascading failures. This module allows admins to monitor these states and manually reset them.

### Key Capabilities
1.  **State Monitoring**: View if breakers are Open (Blocking), Closed (Normal), or Half-Open (Testing).
2.  **Manual Reset**: Force a breaker to close if the external provider has recovered.

---

## 🔌 API Endpoints

### 1. List Circuit Breakers
**GET** `/api/admin/llm/circuit-breakers`

**Response (`CircuitBreakerResponse`)**:
```json
{
  "data": {
    "circuit_breakers": [
      {
        "id": "uuid",
        "entity_name": "gpt-4",
        "state": "closed",
        "failure_count": 0,
        "config": {
          "failure_threshold": 5,
          "timeout_seconds": 60
        }
      },
      {
        "id": "uuid",
        "entity_name": "claude-3-opus",
        "state": "open",
        "last_failure_at": "2023-10-27T10:00:00Z"
      }
    ],
    "summary": { "closed": 5, "open": 1 }
  }
}
```

### 2. Reset Circuit Breaker
**POST** `/api/admin/llm/circuit-breakers/{breaker_id}/reset`
Force the state to `closed`.

**Response**:
```json
{
  "data": {
    "previous_state": "open",
    "new_state": "closed"
  }
}
```

---

## 🎨 UI/UX Guidelines

### State Indicators
- **Closed (Green)**: System is healthy. Traffic is flowing.
- **Open (Red)**: System is failing. Traffic is blocked.
- **Half-Open (Yellow)**: System is recovering. Limited traffic allowed.

### Actions
- **Reset Button**: Only available when state is `open` or `half-open`. Should have a tooltip: "Forces traffic to resume to this model."

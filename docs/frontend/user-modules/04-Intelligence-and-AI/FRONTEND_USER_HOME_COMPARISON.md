# FRONTEND_USER_COMPARISON_MAIN

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/comparison/router.py`

## 1. Module Overview
The **Comparison** module enables side-by-side analysis of DeFi protocols across dimensions like risk, yield, and security.

**Base URL**: `/api/v1/user/comparison`

---

## 2. Endpoints

### 2.1 Compare Protocols
**POST** `/api/v1/user/comparison/protocols`

Generates a comparison matrix.

**Request Body (`CompareProtocolsRequest`):**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `protocol_ids` | `list[str]` | **Yes** | 2-5 protocol UUIDs. |
| `dimensions` | `list[str]` | No | `risk`, `yield`, `security`. |

**Response (200 OK):**
```json
{
  "protocols": {
    "aave": { "yield": 5.2, "risk_score": 90 },
    "compound": { "yield": 4.8, "risk_score": 92 }
  },
  "winner": "aave",
  "reason": "Higher yield with comparable safety."
}
```

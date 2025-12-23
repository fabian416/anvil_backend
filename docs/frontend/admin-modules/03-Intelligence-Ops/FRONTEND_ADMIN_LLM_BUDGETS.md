# Admin Module: LLM Budgets

> **Technical Specification**: `FRONTEND_ADMIN_LLM_BUDGETS`
> **Backend Controller**: `admin/llm/budgets.py`
> **Base URL**: `/api/admin/llm/budgets`

## 📖 Overview
The **LLM Budgets** module protects the platform from runaway AI costs. Admins can define spending limits (Daily/Weekly/Monthly) and configure alert thresholds.

### Key Capabilities
1.  **Budget Creation**: Define soft or hard limits on spending.
2.  **Monitoring**: Real-time tracking of budget utilization (%).
3.  **Alerting**: Configure Slack/Email notifications when thresholds are breached.

---

## 🔌 API Endpoints

### 1. List Budgets
**GET** `/api/admin/llm/budgets`
View all active budgets.

**Response (`BudgetResponse`)**:
```json
{
  "data": {
    "budgets": [
      {
        "id": "uuid",
        "name": "Global Daily Limit",
        "budget_type": "daily",
        "budget_amount_usd": 500.00,
        "current_spend_usd": 125.00,
        "percentage_used": 25.0,
        "is_hard_limit": true
      }
    ]
  }
}
```

### 2. Create Budget
**POST** `/api/admin/llm/budgets`

**Request Body (`CreateBudgetRequest`)**:
```json
{
  "name": "Research Team Monthly",
  "budget_type": "monthly",
  "budget_amount_usd": 2000.00,
  "warning_threshold_percent": 80,
  "critical_threshold_percent": 95,
  "is_hard_limit": false,
  "notify_emails": ["admin@anvil.com"],
  "notify_slack_channel": "#alerts-llm"
}
```

### 3. Update Budget
**PUT** `/api/admin/llm/budgets/{budget_id}`

**Request Body (`UpdateBudgetRequest`)**:
```json
{
  "budget_amount_usd": 2500.00,
  "is_hard_limit": true
}
```

### 4. Delete Budget
**DELETE** `/api/admin/llm/budgets/{budget_id}`
Remove a budget configuration.

---

## 🎨 UI/UX Guidelines

### Progress Bars
- Visualize Budget Usage as a progress bar.
- **Color Coding**:
    - < 80%: Green
    - 80-95%: Orange (Warning)
    - > 95%: Red (Critical)

### Forms
- **Hard Limit Warning**: If "Hard Limit" is selected, show a warning: "This will block all AI requests once the limit is reached."

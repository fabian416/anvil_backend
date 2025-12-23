# 03 - Intelligence Ops

> **User Journey Stage**: The Brain Tuning
> **Goal**: Configure and optimize the AI infrastructure.

## 📖 Overview
The control center for the LLM Gateway. This is where you configure *how* the AI behaves and *how much* it costs.

## 🧩 Modules
1.  **LLM Config (`FRONTEND_ADMIN_LLM_CONFIG.md`)**:
    - Enable/Disable models (GPT-4, Claude).
    - Manage provider settings.
2.  **Budgets (`FRONTEND_ADMIN_LLM_BUDGETS.md`)**:
    - Set spending limits to prevent "Bill Shock".
3.  **Circuit Breakers (`FRONTEND_ADMIN_LLM_CIRCUIT_BREAKERS.md`)**:
    - Monitor reliability and reset failed providers.

## 🎨 UX Guidelines
- **Visual Feedback**: Use color (Green/Red) heavily to indicate State (Open/Closed, Enabled/Disabled).
- **Transparency**: Always show the estimated cost impact of changes.

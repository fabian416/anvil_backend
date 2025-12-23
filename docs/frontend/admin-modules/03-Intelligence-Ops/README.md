# 03 - Intelligence Ops

> **User Journey Stage**: The Brain Tuning
> **Goal**: Configure and optimize the AI infrastructure.

## 📖 Overview
The control center for the LLM Gateway. This is where you configure *how* the AI behaves and *how much* it costs.

## 🧩 Submodules
1.  **LLM Config (`FRONTEND_ADMIN_LLM_CONFIG.md`)**:
    - Enable/Disable models (GPT-4, Claude).
    - Manage provider settings.

2.  **Budgets (`FRONTEND_ADMIN_LLM_BUDGETS.md`)**:
    - Set spending limits to prevent "Bill Shock".

3.  **Circuit Breakers (`FRONTEND_ADMIN_LLM_CIRCUIT_BREAKERS.md`)**:
    - Monitor reliability and reset failed providers.

4.  **Rankings (`FRONTEND_ADMIN_LLM_RANKINGS.md`)**:
    - View model rankings per agent type.
    - Configure ranking weights.
    - Recalculate rankings.
    - Create ranking overrides.

5.  **Telemetry (`FRONTEND_ADMIN_LLM_TELEMETRY.md`)**:
    - View LLM orchestration metrics.
    - Analyze request volume, latency, and costs.
    - Monitor performance by provider, model, and agent.

6.  **Agent Management (`FRONTEND_ADMIN_AGENTS_MAIN.md`)**:
    - View all available AI agents.
    - Monitor agent status (active/inactive).
    - View agent types and descriptions.

7.  **Distillation Management (`FRONTEND_ADMIN_DISTILLATION_MAIN.md`)**:
    - Manage static response templates.
    - Configure distillation settings.
    - Manage cache (invalidate, view stats).
    - View distillation telemetry.

8.  **Distillation Validation (`FRONTEND_ADMIN_DISTILLATION_VALIDATION.md`)**:
    - Review validation responses.
    - Approve/reject validation responses.
    - View validation analytics.

## 🎨 UX Guidelines
- **Visual Feedback**: Use color (Green/Red) heavily to indicate State (Open/Closed, Enabled/Disabled).
- **Transparency**: Always show the estimated cost impact of changes.

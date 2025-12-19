# Multi-LLM Strategy & Configuration

## 1. Initial Configuration (Default)

This configuration is inserted into `agent_model_configs` on system initialization.

### Trading Agent (High Reliability)
1.  **Priority 1**: Bedrock / Claude 3.5 Sonnet
    -   *Reason*: Best-in-class reasoning and tool use.
    -   *Cost*: High.
2.  **Priority 2**: Vertex / Gemini 1.5 Pro
    -   *Reason*: Strong fallback, huge context window.

### Research Agent (High Volume / Analysis)
1.  **Priority 1**: Vertex / Gemini 1.5 Flash
    -   *Reason*: Extremely fast, cheap, large context for reading whitepapers.
    -   *Cost*: Low.
2.  **Priority 2**: DeepInfra / Llama 3 70B
    -   *Reason*: Open source alternative, very cheap.

### Risk Agent (Mathematical Precision)
1.  **Priority 1**: Bedrock / Claude 3.5 Sonnet.

## 2. Caching Strategy (24 Hours)

-   **Key**: `sys:config:agent_models:{agent_type}`
-   **Value**: JSON list of models sorted by priority.
-   **Refresh**:
    -   Automatic: Every 24 hours via Celery Beat.
    -   Manual: Admin API `POST /api/v1/admin/config/refresh`.

## 3. Analytics Pipeline

1.  **Ingest**: `LLMRequestLog` created on every call.
2.  **Process**: `AggregationTask` runs every minute.
3.  **Output**: Update `AgentPerformanceStats` rows.
4.  **View**: Admin Dashboard queries `AgentPerformanceStats`.

## 4. Cost Controls

-   **Rate Limits**: Per user/minute limits configured in `SystemConfig`.
-   **Cost Alerts**: Using `llm_cost_alerts` table. If `daily_spend > $50`, switch all Priority 1 models to Priority 2 automatically.

# AI Infrastructure Specification: Multi-LLM & Telemetry

**Status**: DRAFT
**Owner**: CTO
**Date**: 2025-11-27

---

## 1. Executive Summary
This specification defines the architecture for a robust **Multi-LLM Gateway** supporting **Vertex AI**, **Bedrock**, and **DeepInfra**. It introduces a dynamic configuration system where agents select models based on **priority** and **cost**, backed by a 24-hour caching layer. It also defines the **Telemetry & Analytics** pipeline to track costs, latency, and success rates, driving a real-time "Agent Leaderboard".

## 2. Library Integration Strategy

### 2.1 Competitive Programmer Handbook (Kernel)
-   **Algorithm**: `SegmentTree` (from `libs/competitive-programmer-handbook-python/src/algorithms/range_queries.py`).
-   **Application**: **Real-time Latency Analytics**.
    -   We will use a **Min/Max Segment Tree** to track the latency of the last N requests for each provider.
    -   **Why?**: Allows `O(log N)` queries for "Max latency in the last 5 minutes" to trigger Circuit Breakers instantly without scanning DB rows.

### 2.2 Python Patterns (Blueprint)
-   **Pattern**: `Chain of Responsibility` (from `libs/python-patterns/patterns/behavioral/chain_of_responsibility.py`).
-   **Application**: **Retry & Fallback Logic**.
    -   `PrimaryProviderHandler` -> `SecondaryProviderHandler` -> `FallbackProviderHandler`.
    -   Each handler attempts generation; if it fails (timeout/5xx), it passes to the next.
-   **Pattern**: `Strategy` (from `libs/python-patterns/patterns/behavioral/strategy.py`).
    -   **Application**: **Provider Adapters**. `VertexStrategy`, `BedrockStrategy`, `DeepInfraStrategy` implementing a common `LLMProvider` interface.

### 2.3 Python Toon (Utility)
-   **Application**: **Telemetry Compression**.
    -   When persisting full prompt/response logs to `llm_conversations`, we will serialize the `prompt_text` using `python-toon` if it exceeds 4KB. This reduces storage costs by ~40%.

---

## 3. Multi-LLM Architecture

### 3.1 Supported Providers
1.  **Vertex AI** (Google): Gemini Pro/Flash (Primary for Reasoning).
2.  **Amazon Bedrock**: Claude 3.5 Sonnet (Primary for Coding/Logic), Titan (Fallback).
3.  **DeepInfra**: Llama 3 70B / Mixtral (Cost-effective Fallback).

### 3.2 Configuration Model
We introduce `AgentModelConfig` to decouple Agents from specific Models.

-   **Init Configuration**: Loaded from DB at startup, cached for 24 hours (Redis).
-   **Structure**:
    ```json
    {
        "agent_type": "TRADING",
        "models": [
            { "provider": "BEDROCK", "model": "anthropic.claude-3-sonnet", "priority": 1, "cost_input": 0.003 },
            { "provider": "VERTEX", "model": "gemini-1.5-pro", "priority": 2, "cost_input": 0.00125 }
        ]
    }
    ```

---

## 4. Telemetry & Dashboard

### 4.1 Metrics Tracked
-   **Process Count**: Total requests processed.
-   **Success Rate**: % of 200 OK responses.
-   **Latency**: Avg, P95, P99 time elapsed.
-   **Cost**: Total USD spent per agent/provider.
-   **Canceled**: User cancellations or timeouts.

### 4.2 The "Board" (Agent Stats)
A dedicated table `agent_performance_stats` updated via Celery tasks after every interaction.

-   **Update Logic**:
    1.  Request completes.
    2.  Celery task `update_agent_stats` fires.
    3.  Updates rolling averages in Redis (immediate view).
    4.  Persists to DB table (historical view).

---

## 5. Retry System (Chain of Responsibility)

The `LLMGateway` uses a chain:

1.  **Check Circuit Breaker**: Is the priority 1 provider healthy? (Stats from Segment Tree).
2.  **Attempt 1**: Call Priority 1.
3.  **Failure**: If 5xx or Timeout -> Log Error -> Pass to Next.
4.  **Attempt 2**: Call Priority 2.
5.  **Final Failure**: Raise `LLMGenerationError`.

---

## 6. Implementation Roadmap

### Phase 1: Persistence Layer
-   [ ] Create `AgentModelConfig` table.
-   [ ] Create `AgentPerformanceStats` table.
-   [ ] Update `LLMProvider` enum.
-   [ ] Create Alembic migrations.

### Phase 2: Domain Logic
-   [ ] Implement `LLMProviderFactory` (Strategy).
-   [ ] Implement `RetryHandlerChain` (Chain of Resp).
-   [ ] Implement `StatsAggregator` (using Segment Tree).

### Phase 3: Integration
-   [ ] Connect `Agno` agents to use this Gateway instead of direct API calls.

# Master Implementation Roadmap: From MVP to Production

**Status**: Active / In Progress
**Owner**: CTO
**Date**: 2025-11-27

---

## Executive Summary

This document outlines the complete 7-Phase trajectory for the **Anvil Backend DeFi Multi-Agent System**. It bridges the gap between our strategic architectural decisions and the daily engineering tasks.

We leverage our internal library ecosystem (`libs/`) as force multipliers:
-   **Agent Squad**: Orchestration Brain.
-   **Agno**: High-Performance Execution Hands.
-   **Competitive Programmer Handbook**: Quant Engine Kernel.
-   **Python Toon**: Data Compression Utility.
-   **Python Patterns**: Design Blueprint.

---

## ✅ Phase 1: Core Domain Logic (The Brain)
**Status**: Completed

### Objective
Establish the hexagonal ports, adapters, and interactors that form the nervous system of the Chat feature.

### Key Implementations
1.  **LLM Gateway**: Implemented `LLMGatewayImpl` using the **Strategy Pattern** (Provider Factory) and **Chain of Responsibility** (Retry Handler) from `libs/python-patterns`.
    *   *Providers*: DeepInfra (Implemented), Vertex/Bedrock (Stubbed).
2.  **Agent Gateway**: Implemented `AgentGatewayImpl` wrapping `libs/agent-squad` for intent routing.
3.  **Chat Interactors**: Built `SendMessage` and `CreateConversation` commands.
4.  **Storage**: Created `AnvilSquadStorage` to adapt our SQL repositories to the Squad interface.

---

## ✅ Phase 2: Specialized Agents (The Hands)
**Status**: Completed

### Objective
Create the specialized workers that perform the actual analysis and execution.

### Key Implementations
1.  **AnvilAgent**: Base wrapper around `libs/agno` agents.
2.  **Trading Agent**: Equipped with `HyperliquidTools` (currently mocked) for perp trading.
3.  **Risk Agent**: Integrated **Algorithmic Kernels** from `libs/competitive-programmer-handbook-python`:
    *   `ConvexHull` (Geometry) for portfolio risk visualization.
    *   `BellmanFord` (Graph) for arbitrage cycle detection.

---

## ✅ Phase 3: Async Pipeline (The Nervous System)
**Status**: Completed

### Objective
Decouple the user-facing API from the slow LLM/Blockchain operations using Celery.

### Key Implementations
1.  **Processing Task**: `process_agent_response` handles the heavy lifting of context hydration and agent execution.
2.  **Telemetry**: `update_agent_stats` aggregates performance metrics into the dashboard tables.
3.  **Context Optimization**: Planned usage of `libs/python-toon` for compressing historical context in the task payload.

---

## ✅ Phase 4: Hardening & Integration (The Shield)
**Status**: Completed

### Objective
Verify the wiring and ensure the system is robust.

### Key Implementations
1.  **Integration Tests**: `tests/app/integration/chat/test_chat_flow.py` verifies the full loop (Interactor -> Repo -> Task Queue).
2.  **Entity Hardening**: Fixed `dataclass` instantiation issues in Domain Entities.

---

## 🚀 Phase 5: Real-World Connectivity (The Nerves)
**Status**: Next Priority

### Objective
Replace mocks with real API connections to breathe life into the agents.

### Specs & Tasks

#### 5.1 Hyperliquid Integration
-   **Library**: `hyperliquid-python-sdk` (External).
-   **Task**: Update `src/app/infrastructure/agents/tools/hyperliquid.py`.
-   **Spec**:
    -   Implement `get_positions`: Call SDK `info.user_state(address)`.
    -   Implement `create_order`: Construct the *exact* dict required for EIP-712 signing. **DO NOT SIGN** on backend.
    -   **Safety**: Wrap in `libs/python-patterns` **Circuit Breaker** to handle API downtime.

#### 5.2 RPC & Aave Integration
-   **Library**: `web3.py` (External).
-   **Task**: Create `src/app/infrastructure/external/aave_service.py`.
-   **Spec**:
    -   Configure `Alchemy/Infura` provider from `config.toml`.
    -   Use `PoolDataProvider` contract to fetch User Reserve Data (Health Factor, Collateral).
    -   **Performance**: Use `libs/competitive-programmer-handbook-python` **Segment Tree** (`SumSegmentTree`) to aggregate historical APY rates efficiently if fetching blocks.

#### 5.3 LLM Provider Keys
-   **Task**: Update `config/local/config.toml` (template) and `src/app/infrastructure/factories/ai/llm_provider_factory.py`.
-   **Spec**:
    -   Inject `DEEPINFRA_API_KEY` and `BEDROCK_CREDENTIALS` from environment.
    -   Verify `DeepInfraStrategy` actually returns text from Llama 3.

---

## 🧠 Phase 6: Intelligence Engineering (The Mind)
**Status**: Planned

### Objective
Maximize the IQ of our agents through prompt engineering and knowledge injection.

### Specs & Tasks

#### 6.1 System Prompts & Guardrails
-   **Library**: `libs/agno` (System Message configs).
-   **Task**: Create `src/app/domain/prompts/trading.py` and `risk.py`.
-   **Spec**:
    -   **Trading**: "You are an execution engine. You do not give financial advice. You only output JSON payloads for valid trade requests."
    -   **Risk**: "You are a pessimist. You calculate Value-at-Risk (VaR). You reject leverage > 5x."
    -   **Validation**: Use `libs/python-toon` to validate that agent outputs match expected schema structure tokens.

#### 6.2 RAG Knowledge Base
-   **Library**: `libs/agno` (Knowledge).
-   **Task**: Implement `src/app/infrastructure/agents/knowledge/defi_docs.py`.
-   **Spec**:
    -   **Ingest**: Uniswap V3 Whitepaper, Aave V3 Technical Paper.
    -   **Store**: `PgVector` (using our main Postgres instance).
    -   **Retrieve**: Configure Agno `Knowledge` to query this table on "Explain" intents.

#### 6.3 Classifier Training
-   **Library**: `libs/agent-squad` (Classifier).
-   **Task**: Enhance `AgentGatewayImpl`.
-   **Spec**:
    -   Provide 50 generic DeFi query examples ("Ape into PEPE", "What is impermanent loss?", "Bridge to Base").
    -   Configure `ZeroShotClassifier` or fine-tune a lightweight BERT model if latency is too high.

---

## ⚙️ Phase 7: Operational Readiness (The Body)
**Status**: Planned

### Objective
Prepare the infrastructure for production load and security.

### Specs & Tasks

#### 7.1 Infrastructure as Code
-   **Task**: Update `config/local/docker-compose.yaml`.
-   **Spec**:
    -   Add `redis:alpine` service (for Celery Broker).
    -   Ensure `postgres` service has `pgvector` extension enabled.

#### 7.2 Security Audit
-   **Library**: `libs/python-patterns` (Reference for Secure Design).
-   **Task**: Static Analysis & Manual Review.
-   **Spec**:
    -   **Input Guard**: Use **KMP Algorithm** (`libs/competitive-programmer-handbook-python`) to scan all user inputs for prompt injection patterns (e.g., "Ignore previous instructions").
    -   **Sanitization**: Ensure `ContextSerializer` strips PII before sending to LLM.

#### 7.3 Load Testing & Telemetry
-   **Task**: Verify Dashboard.
-   **Spec**:
    -   Spam `POST /messages`.
    -   Verify `agent_performance_stats` table populates.
    -   Verify `update_agent_stats` Celery task computes correct Averages using **Segment Tree** logic for windowed aggregation.

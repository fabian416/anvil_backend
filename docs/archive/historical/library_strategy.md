# Library Integration Strategy & Implementation Roadmap

**From the Desk of the CTO**

This document defines the strategic adoption plan for our internal library ecosystem. We are moving from "vendored code" to "integrated capability". Each library has been selected to solve a specific high-value problem in our DeFi architecture.

---

## 1. Agent Squad (`libs/agent-squad`)

### Status: **ADOPT**
**Role:** The "Brain" - Orchestration Layer.

### Strategic Use Case
We will use Agent Squad solely for **Intent Routing** and **Multi-Agent Coordination**. It sits between the User API and the specialized execution agents. It is responsible for understanding *what* the user wants and delegating it to the correct worker.

### Implementation Requirements
1.  **Adapter Wrapper**: Do not use the raw library in controllers. Wrap `AgentSquad` in a `AgentGatewayImpl` service adapter.
2.  **Custom Storage**: Implement `AnvilChatStorage` that persists conversation state to our PostgreSQL `conversations` and `messages` tables.
3.  **Custom Classifier**: Implement a classifier optimized for DeFi intent (Trading vs. Research vs. Risk).

### Roadmap
- [ ] **Phase 1 (Foundation)**: Create `AgentGatewayImpl` and the `AnvilChatStorage` adapter. Connect to DB.
- [ ] **Phase 2 (Routing)**: Implement the `DeFiIntentClassifier`.
- [ ] **Phase 3 (Wiring)**: Wire up the `SendMessage` interactor to use this Gateway.

---

## 2. Agno (`libs/agno`)

### Status: **ADOPT**
**Role:** The "Hands" - Execution Runtime.

### Strategic Use Case
Agno is our high-performance runtime for **Tool Execution** and **RAG**. While Squad routes the message, Agno agents actually *do* the work (calling 1inch, fetching prices, querying whitepapers).

### Implementation Requirements
1.  **MCP Integration**: Implement `MCPTools` to connect Agno agents to our internal MCP servers (DeFi Data, etc.).
2.  **Knowledge Base**: Configure `PgVector` knowledge base for Protocol Whitepaper RAG.
3.  **Telemetry**: Hook Agno's telemetry into our `ai_telemetry` database tables (`agent_executions`).

### Roadmap
- [ ] **Phase 1 (Runtime)**: Create base `AnvilAgent` class configured with our LLM settings.
- [ ] **Phase 2 (Tools)**: Implement `DeFiMCPTools` wrapper.
- [ ] **Phase 3 (Knowledge)**: Set up the RAG pipeline for one protocol (e.g., Aave).

---

## 3. Competitive Programmer Handbook (`libs/competitive-programmer-handbook-python`)

### Status: **ADOPT (Kernel)**
**Role:** The "Quant Engine" - Algorithmic Core.

### Strategic Use Case
We use this as a **Reference Kernel**. We do not import the library directly; we *port* specific optimized algorithms into `src/app/application/common/algorithms/`. This ensures we own the performance-critical logic.

### Implementation Requirements
1.  **Graph Engine**: Port `Dijkstra` and `Bellman-Ford` for Smart Routing and Arbitrage.
2.  **Portfolio Math**: Port `Knapsack` (DP) for yield allocation.
3.  **Geometry**: Port `Convex Hull` for risk visualization.

### Roadmap
- [x] **Phase 1**: Port Graph and DP algorithms (Completed).
- [ ] **Phase 2**: Integrate `Dijkstra` into `SwapRouteInteractor`.
- [ ] **Phase 3**: Integrate `Knapsack` into `PortfolioOptimizationInteractor`.

---

## 4. Python Toon (`libs/python-toon`)

### Status: **ADOPT (Utility)**
**Role:** The "Compression Layer" - Data Serialization.

### Strategic Use Case
Used exclusively for **Context Optimization**. When we feed large datasets (transaction history, market tickers) into the LLM context window, we serialize them to TOON to save 30-50% tokens/cost.

### Implementation Requirements
1.  **Serializer Service**: Create `ContextSerializer` service that abstracts `toon.encode`.
2.  **Entity Mapping**: Ensure all Domain Entities (`Transaction`, `Wallet`) have a `to_dict()` method compatible with TOON serialization.

### Roadmap
- [ ] **Phase 1**: Implement `ContextSerializer`.
- [ ] **Phase 2**: Update `AgentGateway` to use TOON for historical context injection.

---

## 5. Python Patterns (`libs/python-patterns`)

### Status: **REFERENCE ONLY**
**Role:** The "Blueprint" - Design Standards.

### Strategic Use Case
**Do NOT import this library.** Use it as a style guide. When implementing a Factory, Builder, or Strategy, check this library to ensure the implementation follows standard Pythonic patterns.

### Implementation Requirements
1.  **Code Reviews**: PRs involving complex design patterns must reference the corresponding pattern in this library to justify the implementation choice.

### Roadmap
- [ ] **Continuous**: Used during code review and architectural design phases.

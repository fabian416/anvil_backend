# Complex Multi-Agent Workflow Sequence Diagram

This document illustrates the sequence of operations when a user sends a complex request that requires coordination across multiple specialized AI agents.

## Example Scenario

**User Request:** "Create a balanced DeFi portfolio with $10,000, optimize for yield while managing risk"

This request triggers a complex workflow involving:
- **Research Agent**: Protocol discovery
- **Risk Analyzer Agent**: Risk assessment
- **DeFi Yield Agent**: Yield optimization
- **Portfolio Agent**: Allocation strategy
- **Chat Agent**: Final aggregation

---

## High-Level Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│   Client    │────▶│  FastAPI Router │────▶│  SendGuestMessage Cmd   │
└─────────────┘     └─────────────────┘     └───────────┬─────────────┘
                                                        │
                                                        ▼
                    ┌───────────────────────────────────────────────┐
                    │         SupervisorCoordinator                  │
                    │  ┌─────────────────────────────────────────┐  │
                    │  │  LLM Planning (Gemini/DeepInfra)        │  │
                    │  │  - Analyzes user intent                 │  │
                    │  │  - Creates WorkflowPlan                 │  │
                    │  │  - Determines agent dependencies        │  │
                    │  └─────────────────────────────────────────┘  │
                    └───────────────────┬───────────────────────────┘
                                        │
                    ┌───────────────────▼───────────────────┐
                    │         Agent Executor                 │
                    │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
                    │  │Rsrch│ │Risk │ │Yield│ │Port │ ... │
                    │  └─────┘ └─────┘ └─────┘ └─────┘     │
                    └───────────────────────────────────────┘
```

---

## Detailed Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    
    participant Client
    participant Router as FastAPI Router<br/>/api/v1/guest/chat
    participant Cmd as SendGuestMessage<br/>Command
    participant Security as Security Filter<br/>(Harmful Content)
    participant Supervisor as SupervisorCoordinator
    participant LLM as LLM Planner<br/>(Gemini 2.0)
    participant Executor as AgentExecutor
    participant Research as Research Agent
    participant Risk as RiskAnalyzer Agent
    participant Yield as DeFiYield Agent
    participant Portfolio as Portfolio Agent
    participant Chat as Chat Agent<br/>(Aggregator)
    participant MCP as MCP Servers<br/>(DeFiLlama, Aave)
    participant DB as Database

    Note over Client,DB: Phase 1: Request Initialization
    
    Client->>Router: POST /api/v1/guest/chat<br/>{"content": "Create balanced DeFi portfolio..."}
    Router->>Cmd: execute(content, ip_address, language)
    
    Note over Cmd,Security: Phase 2: Security & Validation
    
    Cmd->>Security: check_harmful_content(content)
    Security-->>Cmd: ✅ Safe (no harmful patterns)
    
    Cmd->>DB: get_or_create_guest_user(ip)
    DB-->>Cmd: GuestUser(id, ip, created_at)
    
    Cmd->>DB: get_or_create_conversation(user_id)
    DB-->>Cmd: GuestConversation(id, user_id)
    
    Cmd->>DB: save_user_message(content)
    
    Note over Cmd,LLM: Phase 3: Workflow Planning (LLM-based)
    
    Cmd->>Supervisor: create_workflow_plan(message, context, agents)
    Supervisor->>LLM: plan_workflow(prompt, max_agents=5)
    
    Note right of LLM: LLM analyzes:<br/>- User intent (portfolio creation)<br/>- Required data (protocols, yields)<br/>- Risk considerations<br/>- Optimal agent sequence
    
    LLM-->>Supervisor: WorkflowPlan JSON
    
    Note over Supervisor: WorkflowPlan:<br/>Task 0: research (depends: [])<br/>Task 1: risk_analyzer (depends: [0])<br/>Task 2: defi_yield (depends: [0])<br/>Task 3: portfolio (depends: [1,2])<br/>Task 4: chat (depends: [0,1,2,3])
    
    Supervisor-->>Cmd: WorkflowPlan(tasks=5, est_time=50s)
    
    Note over Cmd,Chat: Phase 4: Parallel & Sequential Agent Execution
    
    Cmd->>Supervisor: execute_workflow(plan, context)
    
    rect rgb(240, 248, 255)
        Note over Supervisor,Research: Step 1: Research Agent (no dependencies)
        Supervisor->>Executor: execute_agent(RESEARCH, message)
        Executor->>Research: process(message, context)
        Research->>MCP: query_defillama(top_protocols)
        MCP-->>Research: protocols_data[]
        Research->>MCP: query_aave(lending_rates)
        MCP-->>Research: aave_data{}
        Research-->>Executor: AgentResponse(protocols, sources)
        Executor-->>Supervisor: Task 0 COMPLETED
    end
    
    rect rgb(255, 248, 240)
        Note over Supervisor,Yield: Step 2: Risk + Yield Agents (parallel, depend on Task 0)
        
        par Risk Analysis
            Supervisor->>Executor: execute_agent(RISK_ANALYZER, context)
            Executor->>Risk: analyze_risks(protocols)
            Risk->>MCP: get_tvl_history()
            Risk->>MCP: get_audit_status()
            MCP-->>Risk: risk_data{}
            Risk-->>Executor: AgentResponse(risk_scores)
            Executor-->>Supervisor: Task 1 COMPLETED
        and Yield Analysis
            Supervisor->>Executor: execute_agent(DEFI_YIELD, context)
            Executor->>Yield: analyze_yields(protocols)
            Yield->>MCP: get_apy_rates()
            Yield->>MCP: get_reward_tokens()
            MCP-->>Yield: yield_data{}
            Yield-->>Executor: AgentResponse(yield_opportunities)
            Executor-->>Supervisor: Task 2 COMPLETED
        end
    end
    
    rect rgb(240, 255, 240)
        Note over Supervisor,Portfolio: Step 3: Portfolio Agent (depends on Tasks 1,2)
        Supervisor->>Executor: execute_agent(PORTFOLIO, context)
        Executor->>Portfolio: optimize_allocation(risk_scores, yields)
        
        Note right of Portfolio: Calculates:<br/>- Risk-adjusted returns<br/>- Diversification strategy<br/>- Rebalancing thresholds
        
        Portfolio-->>Executor: AgentResponse(allocation_plan)
        Executor-->>Supervisor: Task 3 COMPLETED
    end
    
    rect rgb(255, 240, 255)
        Note over Supervisor,Chat: Step 4: Chat Agent (aggregates all results)
        Supervisor->>Executor: execute_agent(CHAT, all_results)
        Executor->>Chat: aggregate_and_format(results[])
        
        Note right of Chat: Aggregates:<br/>- Protocol recommendations<br/>- Risk warnings<br/>- Yield expectations<br/>- Allocation breakdown<br/>- Single coherent response
        
        Chat-->>Executor: AgentResponse(final_summary)
        Executor-->>Supervisor: Task 4 COMPLETED
    end
    
    Note over Cmd,DB: Phase 5: Response & Persistence
    
    Supervisor-->>Cmd: (response, sources[], timings[])
    
    Cmd->>DB: save_assistant_message(response)
    
    Cmd-->>Router: GuestMessageResult
    Router-->>Client: 200 OK<br/>{routing, enrichment, agent_message}
```

---

## WorkflowPlan Data Structure

```json
{
  "tasks": [
    {
      "agent_type": "research",
      "task_description": "Find top DeFi protocols with highest TVL and best yields",
      "depends_on": [],
      "status": "completed",
      "execution_time_ms": 3200
    },
    {
      "agent_type": "risk_analyzer",
      "task_description": "Assess smart contract risks and protocol stability",
      "depends_on": [0],
      "status": "completed",
      "execution_time_ms": 2800
    },
    {
      "agent_type": "defi_yield",
      "task_description": "Analyze current APY rates and reward opportunities",
      "depends_on": [0],
      "status": "completed",
      "execution_time_ms": 2500
    },
    {
      "agent_type": "portfolio",
      "task_description": "Create optimal allocation balancing risk and yield",
      "depends_on": [1, 2],
      "status": "completed",
      "execution_time_ms": 1800
    },
    {
      "agent_type": "chat",
      "task_description": "Aggregate results into coherent recommendation",
      "depends_on": [0, 1, 2, 3],
      "status": "completed",
      "execution_time_ms": 1500
    }
  ],
  "execution_order": [0, 1, 2, 3, 4],
  "estimated_time_seconds": 50
}
```

---

## Agent Types Reference

### Core Agents (12)
| Agent | Purpose | Example Trigger |
|-------|---------|-----------------|
| `chat` | General conversation, off-topic handling | "Hello", "What can you do?" |
| `knowledge` | Educational content, Anvil features | "What is DeFi?", "How does staking work?" |
| `hunter_ai` | Market sentiment, price predictions | "BTC price prediction", "Market sentiment" |
| `research` | Protocol analysis, deep research | "Analyze Aave protocol" |
| `execution` | Transaction execution (Privy wallet) | "Swap 100 USDC for ETH" |
| `risk_analyzer` | Risk assessment, scoring | "Risk of lending on Compound" |
| `portfolio` | Portfolio optimization | "Optimize my portfolio" |
| `tax_optimizer` | Tax-loss harvesting | "Tax implications of selling" |
| `defi_yield` | Yield farming, APY analysis | "Best stablecoin yields" |
| `security_auditor` | Smart contract security | "Is this contract safe?" |
| `gas_optimizer` | Gas fee optimization | "Best time to transact" |
| `guest_auth` | Auth prompts for restricted features | (Auto-triggered for guests) |

### Enterprise Agents (8)
| Agent | Purpose |
|-------|---------|
| `compliance_monitor` | AML/KYC, regulatory compliance |
| `multisig_coordinator` | Multi-sig treasury management |
| `alert_monitoring` | Real-time alerts, anomaly detection |
| `crisis_manager` | Emergency response, circuit breaker |
| `bridge_crosschain` | L2, cross-chain operations |
| `lending_borrowing` | Leverage, collateral optimization |
| `nft_asset_manager` | NFT portfolio, valuation |
| `dao_governance` | Voting, proposals, delegation |

---

## Dependency Graph Visualization

```
                    ┌─────────────────┐
                    │   User Request  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Task 0:        │
                    │  RESEARCH       │ ◀── No dependencies
                    │  (3.2s)         │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
     ┌─────────────────┐    │     ┌─────────────────┐
     │  Task 1:        │    │     │  Task 2:        │
     │  RISK_ANALYZER  │◀───┴────▶│  DEFI_YIELD     │  Parallel execution
     │  (2.8s)         │          │  (2.5s)         │
     └────────┬────────┘          └────────┬────────┘
              │                            │
              └──────────────┬─────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Task 3:        │
                    │  PORTFOLIO      │ ◀── Depends on [1,2]
                    │  (1.8s)         │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Task 4:        │
                    │  CHAT           │ ◀── Aggregator (depends on all)
                    │  (1.5s)         │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Final Response │
                    │  Total: ~11.8s  │
                    └─────────────────┘
```

---

## Error Handling Flow

```mermaid
sequenceDiagram
    participant Supervisor
    participant Executor
    participant Agent
    participant Fallback as Fallback Agent

    Supervisor->>Executor: execute_agent(RISK_ANALYZER)
    Executor->>Agent: process(message)
    
    alt Success
        Agent-->>Executor: AgentResponse
        Executor-->>Supervisor: Task COMPLETED
    else Timeout (>30s)
        Agent--xExecutor: TimeoutError
        Executor->>Fallback: execute_agent(CHAT, "summarize available data")
        Fallback-->>Executor: Partial AgentResponse
        Executor-->>Supervisor: Task COMPLETED (partial)
    else Agent Error
        Agent--xExecutor: AgentExecutionError
        Note over Executor: Mark task as FAILED
        Executor-->>Supervisor: Task FAILED
        Note over Supervisor: Continue with<br/>remaining tasks
    end
```

---

## MCP Server Integration

The agents communicate with external data sources through MCP (Model Context Protocol) servers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Executor                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐         ┌─────────┐          ┌─────────┐
│DeFiLlama│         │  Aave   │          │CoinGecko│
│Port 8082│         │Port 8085│          │Port 8084│
├─────────┤         ├─────────┤          ├─────────┤
│• TVL    │         │• Rates  │          │• Prices │
│• Proto  │         │• Health │          │• Markets│
│• Yields │         │• Reserve│          │• OHLCV  │
└─────────┘         └─────────┘          └─────────┘
    │                     │                     │
    └─────────────────────┼─────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    Response Data      │
              │  (aggregated sources) │
              └───────────────────────┘
```

**Available MCP Servers:**
- Port 8081: 1inch DEX Aggregator
- Port 8082: DeFiLlama Analytics
- Port 8083: The Graph Subgraphs
- Port 8084: CoinGecko Market Data
- Port 8085: Aave Lending Protocol
- Port 8086: Portfolio Tracker
- Port 8087: Perplexity Research
- Port 8088: Morpho Lending
- Port 8089: Curve Finance
- Port 8090: Hyperliquid Perps
- Port 8091: LayerZero Bridge

---

## Response Structure

```json
{
  "routing": {
    "handler": "agent_squad_supervisor",
    "intent": "complex_workflow",
    "confidence": 0.95,
    "language": "en",
    "workflow_type": "multi_agent"
  },
  "enrichment": {
    "agents_used": ["research", "risk_analyzer", "defi_yield", "portfolio", "chat"],
    "execution_time_ms": 11800,
    "task_count": 5,
    "parallel_execution": true
  },
  "agent_message": {
    "content": "Based on my analysis of the DeFi ecosystem...\n\n**Recommended Portfolio Allocation:**\n- 40% Aave USDC lending (5.2% APY, Low Risk)\n- 30% Curve 3pool (8.1% APY, Medium Risk)\n- 20% GMX GLP (15% APY, Higher Risk)\n- 10% Reserve for gas/opportunities\n\n**Risk Assessment:**...",
    "sources": [
      {"type": "mcp_server", "name": "DeFiLlama", "data_type": "protocol_tvl"},
      {"type": "mcp_server", "name": "Aave", "data_type": "lending_rates"},
      {"type": "api", "name": "CoinGecko", "data_type": "price_data"}
    ]
  }
}
```

---

## Performance Metrics

| Metric | Single Agent | Multi-Agent (5) |
|--------|--------------|-----------------|
| Avg Response Time | 2-4s | 8-15s |
| LLM Calls | 1 | 2 (plan + aggregate) |
| MCP Queries | 1-3 | 5-12 |
| Parallel Efficiency | N/A | 40-60% time saved |

---

## Related Documentation

- [Agent Squad Architecture](./adr-002-agent-squad-llm-consolidation.md)
- [Prompt Injection Prevention](./prompt-injection-architecture.md)
- [Intent Detection](./INTENT_DETECTION_FIX_ANALYSIS.md)
- [Messaging System](./messaging-system-architecture.md)

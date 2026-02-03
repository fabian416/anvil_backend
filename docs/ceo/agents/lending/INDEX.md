# Lending Workflow Specification - Complete Index

> **Project:** Anvil DeFi Chat - Lending Integration with Morpho & Aave
> **Methodology:** MIT Systems Thinking + Stanford Design Thinking + First Principles Analysis
> **Agents:** @backend-engineer + @prompt-engineer + @code-review-waltz + @smart-agent-router
> **Status:** ✅ Specification Complete - LENDING_BORROWING Agent Added
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains **14 comprehensive documents** totaling **8,500+ lines** covering the complete lending workflow implementation for Morpho (port 8088) and Aave (port 8085) integration.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Architecture** | architecture.md, implementation_plan.md, database_schema.md | System design and implementation roadmap |
| **Agent Design** | agent_prompts.md, knowledge_base.md, shortcuts_update.md | AI agent configuration and knowledge |
| **Enterprise Agent** | LENDING_BORROWING_AGENT.md | Aave health factor monitoring agent |
| **Quality Assurance** | code_review_checklist.md, risk_analysis.md, integration_patterns.md | Review guidelines and best practices |
| **Coordination** | agent_coordination.md, workflow_diagrams.md, context_awareness.md | Multi-agent orchestration |
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |

---

## 🏦 Enterprise Agent: LENDING_BORROWING

### [LENDING_BORROWING_AGENT.md](./LENDING_BORROWING_AGENT.md) - Aave Health Factor Agent
**Lines:** ~350 | **Priority:** High | **NEW**

Enterprise-tier agent for advanced lending position monitoring:

**Key Features:**
- Real-time Aave V3 health factor monitoring
- Collateral breakdown with asset values
- Borrow rate comparison across protocols (Aave, Compound, Spark)
- Liquidation risk assessment
- Leverage strategy guidance

**Distinction from LENDING_WORKFLOW:**
| Feature | LENDING_WORKFLOW | LENDING_BORROWING |
|---------|------------------|-------------------|
| Type | Multi-step workflow | Single-step query |
| Primary Protocol | Morpho | Aave V3 |
| Purpose | Deposit tokens | Health monitoring |
| Health Factor | Secondary | Primary feature |

**Supervisor Routing:**
- "what's my health factor" → LENDING_BORROWING
- "check my Aave position" → LENDING_BORROWING
- "deposit USDC" → LENDING_WORKFLOW

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Lines:** ~1,029 | **Priority:** Critical | **Read First**

Complete hexagonal architecture specification following the codebase's established patterns:

**Key Contents:**
- **Domain Layer**: `LendingPosition`, `HealthFactor`, `LendingService` entities
- **Application Layer**: Supply/Borrow/Leverage commands and health check queries
- **Infrastructure Layer**: Aave/Morpho MCP adapters with balance checking
- **Presentation Layer**: Lending endpoints and shortcuts integration
- **User Context Awareness**: Guest vs authenticated user flows
- **Multi-Agent Coordination**: Market Scanner → Risk Guardian → Executor patterns

**Critical Sections:**
- Section 2.1: Domain Modeling (entities, value objects, services)
- Section 3.2: CQRS Pattern Implementation (commands vs queries)
- Section 4.3: MCP Adapter Integration (Aave 9 tools, Morpho 6 tools)
- Section 5.4: User Context Service (authentication awareness)

---

### 2. [implementation_plan.md](./implementation_plan.md) - 7-Week Implementation Roadmap
**Lines:** ~826 | **Priority:** Critical | **Action Plan**

Detailed implementation timeline with milestones, dependencies, and deliverables:

**Phases:**
1. **Week 1**: Domain modeling and ports definition
2. **Week 2**: MCP adapter integration (Aave + Morpho)
3. **Week 3**: User context awareness implementation
4. **Week 4**: Balance validation flow before transaction execution
5. **Week 5**: Knowledge agent updates and prompt engineering
6. **Week 6**: Supervisor configuration for authenticated users
7. **Week 7**: Testing, documentation, and deployment

**Key Milestones:**
- Week 2 End: All 15 MCP tools integrated
- Week 4 End: Balance checking prevents all invalid transactions
- Week 6 End: Knowledge agent correctly handles lending queries in 4 languages

---

### 3. [database_schema.md](./database_schema.md) - PostgreSQL Database Design
**Lines:** ~675 | **Priority:** High | **Database Structure**

Complete database schema with 8 tables for lending operations:

**Core Tables:**
- `lending_positions`: User positions across protocols (collateral, debt, health factor)
- `lending_supplies`: Supply transactions with APY tracking
- `lending_borrows`: Borrow transactions with interest rate mode
- `lending_transactions`: Transaction history with status tracking
- `user_lending_preferences`: Risk tolerance and auto-repay thresholds
- `lending_health_checks`: Health factor monitoring history
- `leverage_loop_executions`: Multi-step leverage loop tracking
- `lending_alerts`: User notifications for critical events

**Views:**
- `user_lending_summary`: Aggregated position data per user
- `protocol_comparison`: APY comparison across Aave/Morpho

**Migrations:**
- Alembic migration templates included
- Performance optimizations (indexes, partitioning)
- Security: Row-level security policies

---

## 🤖 Agent Design Documents

### 4. [agent_prompts.md](./agent_prompts.md) - Optimized Agent Prompts
**Lines:** ~942 | **Priority:** High | **Prompt Engineering**

Optimized prompts for 4 specialized lending agents with temperature tuning:

**Agents:**
1. **Market Scanner Agent** (Temperature: 0.3)
   - Analyzes Aave/Morpho rates across protocols
   - Provides structured APY comparisons
   - Few-shot examples for rate queries

2. **Risk Guardian Agent** (Temperature: 0.2)
   - Monitors health factors and liquidation risks
   - Exact classification: SAFE >2.0, CAUTION 1.5-2.0, DANGER 1.1-1.5, CRITICAL <1.1
   - Chain-of-thought reasoning for risk assessment

3. **Executor Agent** (Temperature: 0.1)
   - Executes transactions with balance checks
   - Gas availability verification (minimum 0.01 ETH)
   - Rejects transactions resulting in HF < 1.2

4. **Optimizer Agent** (Temperature: 0.4)
   - Optimizes yield across protocols
   - Strategies: Yield Farming, Loop Protocol, Cross-Protocol Arbitrage
   - Risk-tolerance mapping

**Key Features:**
- Few-shot examples (2-3 per agent)
- Embedded safety checks
- Structured output formats
- User context variable integration

---

### 5. [knowledge_base.md](./knowledge_base.md) - Agent Knowledge Injection
**Lines:** ~746 | **Priority:** High | **Knowledge Configuration**

Structured knowledge base for context-aware agent responses:

**Knowledge Categories:**
1. **Protocol Comparison**: Aave vs Morpho characteristics
2. **Risk Classification**: LTV risk levels (Ultra Safe → Liquidatable)
3. **Health Factor Interpretation**: HF classification with colors and actions
4. **User Context Awareness**: Guest, authenticated, premium tier responses
5. **Balance Awareness**: Sufficient vs insufficient balance flows
6. **Multi-Language Support**: Lending terminology in en/es/pt/zh

**Critical Notes:**
- Use "supply" (not "borrow") for Anvil's lending feature terminology
- Guest users: Educational content only, no execution
- Authenticated users: Actionable recommendations with balance checks
- Premium users: Advanced features (auto-repay, leverage strategies)

---

### 6. [shortcuts_update.md](./shortcuts_update.md) - Shortcuts Configuration
**Lines:** ~935 | **Priority:** High | **User Interface**

Configuration for 6 lending shortcut flows with multi-language support:

**Shortcuts:**
1. **"Check my lending position"**: LENDING_HEALTH_CHECK → Risk Guardian (single-step)
2. **"Supply ETH to earn yield"**: LENDING_SUPPLY → Market Scanner → Executor (multi-step)
3. **"Borrow USDC"**: LENDING_BORROW → Risk Guardian → Executor (multi-step)
4. **"Loop ETH for leverage"**: LENDING_LOOP → Optimizer → Risk → Executor (multi-step)
5. **"What's the best yield?"**: LENDING_COMPARE → Market Scanner (single-step)
6. **"Show my lending positions"**: LENDING_POSITION → Risk Guardian (single-step)

**Each Shortcut Includes:**
- Pattern matching with parameter extraction
- Multi-language support (en, es, pt, zh)
- Agent routing configuration
- Safety checks and balance verification
- Example conversations with expected responses

**Implementation:**
- Update `GET /api/v1/public/chat/shortcuts` endpoint
- Add lending shortcuts to response
- Integrate with intent detector for routing

---

## ✅ Quality Assurance Documents

### 7. [code_review_checklist.md](./code_review_checklist.md) - Review Guidelines
**Lines:** ~1,200+ | **Priority:** Critical | **Quality Standards**

Comprehensive code review checklist covering 8 critical areas:

**Sections:**
1. **Hexagonal Architecture Compliance**: Domain, application, infrastructure, presentation layers
2. **CQRS Pattern Implementation**: Command-query separation, gateway usage
3. **Error Handling & Edge Cases**: Input validation, transaction failures, multi-sig interruptions
4. **Security Considerations**: Wallet signature validation, authorization, rate limiting
5. **Performance Optimization**: MCP call caching (60s market data, 30s health factor)
6. **Testing Strategy**: 90% domain coverage, 70% adapter coverage, E2E lending flows

**Testing Requirements:**
- Unit tests: Domain entities, value objects, services
- Integration tests: MCP adapters, database repositories
- E2E tests: Supply flow, borrow flow, leverage loop, liquidation scenario

---

### 8. [risk_analysis.md](./risk_analysis.md) - Technical Risk Assessment
**Lines:** ~1,500+ | **Priority:** Critical | **Risk Mitigation**

Comprehensive risk analysis covering 7 failure scenarios:

**High-Priority Risks:**
1. **Transaction Failures**: Insufficient balance (HIGH), gas estimation errors (MEDIUM)
2. **Health Factor Errors**: Stale price data (CRITICAL - 10s cache max)
3. **Multi-Signature Workflows**: Partial signatures (MEDIUM - 5min timeout)
4. **MCP Server Failures**: Aave downtime (HIGH - fallback to direct web3)
5. **Liquidation Risks**: Flash crashes (CRITICAL - monitor every 5min)

**Mitigation Strategies:**
- Pre-transaction balance validation
- Force price refresh for borrow operations
- 3-attempt retry strategy with exponential backoff
- Multi-oracle validation (Chainlink + Uniswap TWAP)
- Circuit breaker for MCP server failures

**Risk Matrix:**
- CRITICAL: Liquidation risk, oracle failures → Immediate action
- HIGH: Transaction failures, MCP downtime → Fallback systems
- MEDIUM: Multi-sig timeouts, rate limiting → Retry mechanisms
- LOW: Precision loss → Use Decimal type

---

### 9. [integration_patterns.md](./integration_patterns.md) - MCP Integration Patterns
**Lines:** ~1,400+ | **Priority:** High | **Integration Architecture**

Best practices for integrating Aave and Morpho MCP servers:

**Integration Patterns:**
1. **Aave MCP Adapter**: 9 tools (get_market_data, supply_asset, borrow_asset, etc.)
2. **Morpho MCP Adapter**: 6 tools (morpho_get_vaults, morpho_get_user_positions, etc.)
3. **Cross-Protocol Comparison**: Parallel fetch from both protocols
4. **Balance Validation**: Web3 adapter for ERC20 balanceOf checks
5. **Transaction Monitoring**: Celery task polls tx status every 30s
6. **Event-Driven Architecture**: Domain events (PositionCreated, HealthFactorCritical)

**Caching Strategy:**
- Redis multi-level cache
- Market data: 60s TTL
- User positions: 30s TTL
- Health factors: 10s TTL (critical data)

**Testing Patterns:**
- Mock MCP client for unit tests
- Integration tests with real MCP servers (testnet)
- E2E tests with real transactions (testnet)

---

## 🔄 Coordination Documents

### 10. [agent_coordination.md](./agent_coordination.md) - Multi-Agent Orchestration
**Lines:** TBD | **Priority:** High | **Workflow Coordination**

Multi-agent workflow orchestration and state management:

**Key Topics:**
- **Routing Strategy**: Explicit chaining (not semantic routing) for financial operations
- **Agent Team Composition**: Market Scanner, Risk Guardian, Executor
- **State Management**: `LendingWorkflowState` enum with Redis persistence
- **Error Propagation**: Custom error hierarchy with retry logic
- **Timeout Handling**: Agent-level (10s-30s) and workflow-level (120s)
- **Coordination Patterns**: Sequential, event-driven, queue-based, iterative

**Workflow Types:**
1. Sequential: Supply flow (Market Scanner → Risk → Executor)
2. Event-Driven: Health monitoring via pub/sub
3. Queue-Based: Celery tasks for transaction execution
4. Iterative: Leverage loops with supply→borrow→swap cycles

---

### 11. [workflow_diagrams.md](./workflow_diagrams.md) - Visual Workflow Diagrams
**Lines:** TBD | **Priority:** Medium | **Visual Documentation**

Mermaid diagrams for 5 core lending workflows:

**Diagrams:**
1. **Supply Workflow**: User Input → Balance Check → Market Scanner → Risk Guardian → Quote → Confirmation → Executor → Success
2. **Borrow Workflow**: User Input → Collateral Check → Risk Assessment → Borrow Calculation → Approval → Execution → Monitor
3. **Leverage Loop**: Supply → Health Check → Borrow → Swap → Loop (repeat) → Final Position
4. **Health Check**: Position Query → Health Factor Calculation → Risk Evaluation → Notification
5. **Auto-Repay**: Health Monitor → Trigger → Partial Repay Calculation → Execution → Update

**Each Diagram Includes:**
- Agent responsibilities
- Data flow arrows
- Decision points
- Error paths
- Integration touchpoints

---

### 12. [context_awareness.md](./context_awareness.md) - User Context Integration
**Lines:** TBD | **Priority:** High | **Personalization**

Context-aware behavior based on user authentication and portfolio state:

**User Flows:**
1. **Guest User**: Educational responses, no execution, signup CTA
2. **Authenticated User**: Balance validation, real-time positions, execution enabled
3. **Premium User**: Auto-repay access, advanced strategies, priority queue

**Context Variables:**
```python
{
  "is_authenticated": bool,
  "wallet_address": str | None,
  "balance": dict,  # {asset: amount}
  "risk_profile": "conservative" | "moderate" | "aggressive",
  "tier": "free" | "premium",
  "portfolio_state": "empty" | "starter" | "established",
}
```

**Response Templates:**
- Balance-aware recommendations
- Risk-based messaging
- Portfolio-state responses

---

### 13. [README.md](./README.md) - Getting Started Guide
**Lines:** ~370 | **Priority:** High | **Overview**

Quick start guide and navigation hub for all specifications.

**Contents:**
- Overview of lending workflow
- Document structure explanation
- Quick links to key sections
- Implementation priority guide
- Key decisions summary

---

## 🎯 Implementation Priorities

### Phase 1: Core Architecture (Weeks 1-2)
**Documents to Review:**
1. architecture.md - Complete domain modeling
2. database_schema.md - Set up database tables
3. implementation_plan.md - Follow Phase 1-2 tasks

**Deliverables:**
- Domain entities: LendingPosition, HealthFactor, CollateralAsset
- Ports: ILendingProtocolGateway, IBalanceChecker
- Adapters: AaveMcpAdapter, MorphoMcpAdapter
- Database migrations

---

### Phase 2: MCP Integration (Weeks 3-4)
**Documents to Review:**
1. integration_patterns.md - MCP integration best practices
2. risk_analysis.md - Understand failure scenarios
3. code_review_checklist.md - Follow security guidelines

**Deliverables:**
- Aave MCP adapter with 9 tools
- Morpho MCP adapter with 6 tools
- Balance validation before transactions
- Transaction monitoring with Celery

---

### Phase 3: Agent Configuration (Weeks 5-6)
**Documents to Review:**
1. agent_prompts.md - Configure agent prompts
2. knowledge_base.md - Inject lending knowledge
3. shortcuts_update.md - Add lending shortcuts
4. context_awareness.md - Implement user context

**Deliverables:**
- 4 agent prompts configured (Market Scanner, Risk Guardian, Executor, Optimizer)
- Knowledge base injected into agents
- 6 lending shortcuts added to API
- User context service integrated

---

### Phase 4: Testing & Deployment (Week 7)
**Documents to Review:**
1. code_review_checklist.md - Run complete review
2. risk_analysis.md - Verify mitigation strategies
3. agent_coordination.md - Test multi-agent workflows
4. workflow_diagrams.md - Validate flows

**Deliverables:**
- 90% domain test coverage
- 70% integration test coverage
- E2E tests for supply, borrow, leverage loops
- Production deployment checklist

---

## 📊 Key Metrics & Success Criteria

### Technical Metrics
- **Test Coverage**: >90% domain, >70% integration
- **Response Time**: <500ms for health checks, <2s for transaction quotes
- **Cache Hit Rate**: >80% for market data
- **Error Rate**: <0.1% for MCP calls
- **Health Factor Monitoring**: Every 5 minutes for positions with HF < 1.5

### Business Metrics
- **User Engagement**: Lending shortcuts usage tracking
- **Transaction Success Rate**: >95% for valid transactions
- **Balance Check Prevention**: 100% of insufficient balance transactions blocked
- **Multi-Language Support**: All 4 languages (en, es, pt, zh) tested

### Security Metrics
- **Authorization**: 100% of transactions require valid wallet signature
- **Balance Validation**: 100% pre-flight checks before MCP calls
- **Rate Limiting**: Max 10 lending queries per minute per user
- **Health Factor Alerts**: 100% of HF < 1.1 positions trigger alerts

---

## 🔗 Cross-References

### Related Specifications
- **Swap System**: `/home/ubuntu/anvil_backend/docs/ceo/SWAP_SYSTEM_SPEC.md`
- **Chat System**: `/home/ubuntu/anvil_backend/docs/ceo/CHAT_ARCHITECTURE.md`
- **Deployment**: `/home/ubuntu/anvil_backend/docs/ceo/deployment-dockerization-spec.md`

### Codebase Integration Points
- **MCP Servers**: `src/app/infrastructure/mcp/servers/aave_mcp.py`, `src/app/infrastructure/mcp/servers/morpho_mcp.py`
- **Domain Entities**: `src/app/domain/entities/`
- **Application Commands**: `src/app/application/chat/commands/`
- **Controllers**: `src/app/presentation/http/controllers/chat/`
- **Knowledge Agent**: `anvil_knowledge/agents/`
- **Supervisor Config**: `anvil_knowledge/supervisor/`

---

## 🚀 Next Actions

1. **Review All Specifications** (1-2 days)
   - Read architecture.md, implementation_plan.md, database_schema.md
   - Review agent_prompts.md, knowledge_base.md, shortcuts_update.md
   - Study code_review_checklist.md, risk_analysis.md, integration_patterns.md

2. **Team Alignment Meeting** (1 day)
   - Present specifications to development team
   - Clarify ambiguities and answer questions
   - Get sign-off on architecture and implementation plan

3. **Begin Implementation** (7 weeks)
   - Follow implementation_plan.md timeline
   - Weekly progress reviews
   - Continuous testing and code review

4. **Documentation Updates** (ongoing)
   - Keep specifications updated as implementation progresses
   - Document any deviations from the plan
   - Add learnings and optimization insights

---

## 📝 Document Maintenance

**Last Updated:** 2026-01-27
**Created By:** @backend-engineer + @prompt-engineer + @code-review-waltz + @smart-agent-router
**Methodology:** MIT Systems Thinking + Stanford Design Thinking + First Principles Analysis
**Review Frequency:** Weekly during implementation, monthly after deployment
**Change Log:** Track major specification updates in this section

---

## 🤝 Contributing

When updating these specifications:
1. Follow the established methodology (cto.md)
2. Maintain hexagonal architecture principles
3. Keep multi-language support in mind
4. Update cross-references between documents
5. Add examples and code snippets where helpful
6. Run specifications through code review before finalizing

---

**For questions or clarifications, refer to the README.md in this directory or consult the development team lead.**

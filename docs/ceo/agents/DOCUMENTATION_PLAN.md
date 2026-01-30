# Agent Documentation Plan

**Version**: 1.0
**Date**: 2026-01-29
**Methodology**: CTO First Principles Analysis (as per cto.md)
**Status**: Planning Phase

---

## Executive Summary

This document outlines the systematic plan to document all 25 agents in the Anvil DeFi Chat system, following the same comprehensive methodology used for `docs/ceo/agents/lending/`.

---

## Current Documentation Status

### ✅ Fully Documented Agents (25) - 100% COMPLETE

| Agent | Directory | Status | Files |
|-------|-----------|--------|-------|
| **LENDING_WORKFLOW** | `/docs/ceo/agents/lending/` | ✅ Complete | 44 files |
| **LENDING_BORROWING** | `/docs/ceo/agents/lending/LENDING_BORROWING_AGENT.md` | ✅ Complete | 1 file |
| **MONEY_MARKET_WORKFLOW** | `/docs/ceo/agents/money_market/` | ✅ Complete | 10 files |
| **TRANSFER_WORKFLOW** | `/docs/ceo/agents/transfer/` | ✅ Complete | 6 files |
| **SWAP_WORKFLOW** | `/docs/ceo/agents/swap/` | ✅ Complete | 5 files |
| **BUY_WORKFLOW** | `/docs/ceo/agents/buy/` | ✅ Complete | 5 files |
| **PORTFOLIO** | `/docs/ceo/agents/portfolio/` | ✅ Complete | 5 files |
| **WALLET** | `/docs/ceo/agents/wallet/` | ✅ Complete | 5 files |
| **KNOWLEDGE** | `/docs/ceo/agents/knowledge/` | ✅ Complete | 5 files |
| **EXECUTION** | `/docs/ceo/agents/execution/` | ✅ Complete | 5 files |
| **RISK_ANALYZER** | `/docs/ceo/agents/risk_analyzer/` | ✅ Complete | 5 files |
| **DEFI_YIELD** | `/docs/ceo/agents/defi_yield/` | ✅ Complete | 5 files |
| **RESEARCH** | `/docs/ceo/agents/research/` | ✅ Complete | 5 files |
| **GAS_OPTIMIZER** | `/docs/ceo/agents/gas_optimizer/` | ✅ Complete | 5 files |
| **CHAT** | `/docs/ceo/agents/chat/` | ✅ Complete | 5 files |
| **COMPLIANCE_MONITOR** | `/docs/ceo/agents/compliance_monitor/` | ✅ Complete | 5 files |
| **GUEST_AUTH** | `/docs/ceo/agents/guest_auth/` | ✅ Complete | 5 files |
| **TAX_OPTIMIZER** | `/docs/ceo/agents/tax_optimizer/` | ✅ Complete | 5 files |
| **SECURITY_AUDITOR** | `/docs/ceo/agents/security_auditor/` | ✅ Complete | 5 files |
| **ALERT_MONITORING** | `/docs/ceo/agents/alert_monitoring/` | ✅ Complete | 5 files |
| **CRISIS_MANAGER** | `/docs/ceo/agents/crisis_manager/` | ✅ Complete | 5 files |
| **MULTISIG_COORDINATOR** | `/docs/ceo/agents/multisig_coordinator/` | ✅ Complete | 5 files |
| **HUNTER_AI** | `/docs/ceo/agents/hunter/` | ✅ Complete | 6 files |
| **TRANSACTION_HISTORY** | `/docs/ceo/agents/activity/` | ✅ Complete | 5 files |
| **ULTRA** (Flash Loans, Arbitrage, MEV) | `/docs/ceo/agents/ultra/` | ✅ Complete | 6 files |

### ✅ All Agents Documented (0 remaining)

#### Core User-Facing Agents (8)

| Agent | Type | Priority | Complexity |
|-------|------|----------|------------|
| ~~CHAT~~ | ~~General conversation~~ | ~~P2~~ | ~~Low~~ (✅ Complete) |
| ~~GUEST_AUTH~~ | ~~Authentication for guests~~ | ~~P2~~ | ~~Low~~ (✅ Complete) |
| ~~RESEARCH~~ | ~~Deep protocol analysis~~ | ~~P1~~ | ~~High~~ (✅ Complete) |
| ~~EXECUTION~~ | ~~Transaction execution~~ | ~~P1~~ | ~~High~~ (✅ Complete) |
| ~~RISK_ANALYZER~~ | ~~Risk assessment~~ | ~~P1~~ | ~~High~~ (✅ Complete) |
| ~~TAX_OPTIMIZER~~ | ~~Tax-loss harvesting~~ | ~~P2~~ | ~~Medium~~ (✅ Complete) |
| ~~DEFI_YIELD~~ | ~~Yield farming~~ | ~~P1~~ | ~~Medium~~ (✅ Complete) |

#### Authenticated User Agents (0)

All authenticated user agents are now documented.

#### Workflow Agents (0)

All workflow agents are now documented.

#### Enterprise Agents (6)

| Agent | Type | Priority | Complexity |
|-------|------|----------|------------|
| ~~COMPLIANCE_MONITOR~~ | ~~AML/KYC compliance~~ | ~~P2~~ | ~~High~~ (✅ Complete) |
| ~~MULTISIG_COORDINATOR~~ | ~~Multi-sig treasury~~ | ~~P3~~ | ~~High~~ (✅ Complete) |
| ~~ALERT_MONITORING~~ | ~~Real-time alerts~~ | ~~P2~~ | ~~Medium~~ (✅ Complete) |
| ~~CRISIS_MANAGER~~ | ~~Emergency response~~ | ~~P3~~ | ~~High~~ (✅ Complete) |
| **BRIDGE_CROSSCHAIN** | Cross-chain ops | P2 | High |
| **NFT_ASSET_MANAGER** | NFT portfolio | P3 | Medium |
| **DAO_GOVERNANCE** | DAO voting | P3 | Medium |
| ~~GAS_OPTIMIZER~~ | ~~Gas optimization~~ | ~~P2~~ | ~~Low~~ (✅ Complete) |
| ~~SECURITY_AUDITOR~~ | ~~Contract security~~ | ~~P2~~ | ~~Medium~~ (✅ Complete) |

---

## Documentation Template

Each agent documentation should follow this structure (as per `docs/ceo/agents/lending/`):

### Required Files

```
docs/ceo/agents/{agent_name}/
├── README.md           # Overview, features, quick start
├── INDEX.md            # Navigation, status tracking
├── architecture.md     # Hexagonal architecture design
├── implementation.md   # Code references, key methods
├── shortcuts.md        # Chat patterns, multi-language
└── [additional files]  # Agent-specific documentation
```

### README.md Template

```markdown
# {Agent Name} Specification

**Version**: 1.0
**Date**: {date}
**Status**: {Implementation Status}
**Agent Type**: {Core | Enterprise | Workflow}
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview
{Brief description of agent purpose}

## Document Structure
{List of files with descriptions}

## Quick Start
{For developers and QA}

## Key Features
{Feature list with status}

## Architecture Principles
{Hexagonal layers diagram}

## API Endpoints (if applicable)
{Endpoint table}

## Chat Integration
{Tool types and patterns}

## Example Conversations
{2-3 conversation examples}

## Configuration
{Default parameters}

## Testing Checklist
{Unit, Integration, E2E tests}

## Related Documentation
{Links to related specs}

## Changelog
{Version history}
```

### architecture.md Template

```markdown
# {Agent Name} Architecture

## Executive Summary
{Key components and purpose}

## Hexagonal Architecture Layers
{Layer diagram}

## Domain Layer
{Entities, Value Objects, Enums}

## Application Layer
{Services, Commands, Queries}

## Infrastructure Layer
{Adapters, Clients, APIs}

## Presentation Layer
{Controllers, Routes}

## Data Flow
{Step-by-step flow diagram}

## Error Handling
{Error types and handling}

## Logging
{Debug and production logging}

## Testing
{Test file locations and patterns}

## Performance
{Targets and metrics}

## Dependencies
{Required packages}
```

---

## Implementation Phases

### Phase 1: High-Priority Workflows (P0-P1)

**Duration**: 3-4 days
**Agents**: 7

| Order | Agent | Est. Time | Reason | Status |
|-------|-------|-----------|--------|--------|
| 1 | **SWAP_WORKFLOW** | 4h | Most used workflow | ✅ Complete |
| 2 | **BUY_WORKFLOW** | 3h | Fiat on-ramp, user acquisition | ✅ Complete |
| 3 | **PORTFOLIO** | 3h | Core feature for authenticated users | ✅ Complete |
| 4 | **WALLET** | 2h | Complements portfolio | ✅ Complete |
| 5 | **KNOWLEDGE** | 3h | Educational, high visibility | ✅ Complete |
| 6 | **EXECUTION** | 3h | Critical for all transactions | ✅ Complete |
| 7 | **RISK_ANALYZER** | 3h | Safety-critical component | ✅ Complete |
| 8 | **DEFI_YIELD** | 2h | Yield farming analysis | ✅ Complete |

### Phase 2: Core Agents (P2)

**Duration**: 2-3 days
**Agents**: 7

| Order | Agent | Est. Time | Reason |
|-------|-------|-----------|--------|
| 9 | **RESEARCH** | 3h | Deep analysis, complex | ✅ Complete |
| 10 | **CHAT** | 2h | General fallback | ✅ Complete |
| 11 | **GUEST_AUTH** | 2h | Signup prompts | ✅ Complete |
| 12 | **TAX_OPTIMIZER** | 2h | Premium feature | ✅ Complete |
| 13 | **GAS_OPTIMIZER** | 2h | Gas timing | ✅ Complete |
| 14 | **SECURITY_AUDITOR** | 2h | Contract analysis | ✅ Complete |
| 15 | **ALERT_MONITORING** | 2h | Real-time alerts | ✅ Complete |

### Phase 3: Enterprise Agents (P3)

**Duration**: 2-3 days
**Agents**: 5

| Order | Agent | Est. Time | Reason |
|-------|-------|-----------|--------|
| 16 | **COMPLIANCE_MONITOR** | 3h | AML/KYC | ✅ Complete |
| 17 | **BRIDGE_CROSSCHAIN** | 3h | Cross-chain ops |
| 18 | **MULTISIG_COORDINATOR** | 2h | Treasury management | ✅ Complete |
| 19 | **CRISIS_MANAGER** | 2h | Emergency response | ✅ Complete |
| 20 | **NFT_ASSET_MANAGER** | 2h | NFT portfolio |
| 21 | **DAO_GOVERNANCE** | 2h | DAO voting |

---

## Per-Agent Documentation Checklist

For each agent, complete:

- [ ] **README.md** - Overview and quick start
- [ ] **INDEX.md** - Navigation and status
- [ ] **architecture.md** - Hexagonal design
- [ ] **implementation.md** - Code references
- [ ] **shortcuts.md** - Chat patterns

### Additional Documentation (if applicable)

- [ ] **api_reference.md** - For agents with REST endpoints
- [ ] **data_sources.md** - For data-driven agents (Hunter, Research)
- [ ] **safety_analysis.md** - For safety-critical agents (Risk, Execution)
- [ ] **integration_patterns.md** - For MCP-integrated agents

---

## Research Steps Per Agent

Following CTO methodology (cto.md):

### 1. First Principles Analysis

```
- What is the agent's core purpose?
- What problem does it solve for users?
- What are the fundamental constraints?
- What are the success criteria?
```

### 2. Codebase Investigation

```bash
# Find agent implementation
grep -r "class {AgentName}Agent" src/

# Find DI registration
grep -r "provide_{agent_name}" src/app/setup/ioc/

# Find supervisor routing
grep -r "{agent_type}" src/app/domain/services/agent_squad/

# Find shortcuts
grep -r "{agent_type}" anvil_knowledge/
```

### 3. Design Thinking

```
- Who are the users?
- What are their needs?
- How does the agent address those needs?
- What are the edge cases?
```

### 4. Systems Thinking

```
- How does this agent interact with others?
- What are the dependencies?
- What data flows through the agent?
- What are the failure modes?
```

---

## Quality Criteria

Each agent documentation must meet:

### Completeness

- [ ] All 5 core files present
- [ ] Code references with file paths
- [ ] Example conversations
- [ ] Error handling documented
- [ ] Multi-language support noted

### Accuracy

- [ ] Verified against codebase
- [ ] Method signatures correct
- [ ] Dependencies listed
- [ ] Routing rules accurate

### Consistency

- [ ] Follows lending/ structure
- [ ] Same markdown formatting
- [ ] Similar level of detail
- [ ] Cross-references valid

---

## Next Immediate Actions

1. **Start with SWAP_WORKFLOW** (highest usage, well-understood)
   - Read `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py`
   - Check routing in `authenticated_supervisor.py`
   - Review shortcuts configuration
   - Create documentation structure

2. **Then BUY_WORKFLOW** (similar pattern, simpler)
   - Read `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py`
   - Document fiat on-ramp flow
   - Note Stripe integration points

3. **Proceed through P1 agents** in order

---

## Related Documentation

- [CTO Methodology](../../cto.md) - First Principles Analysis
- [Lending Documentation](./lending/) - Reference implementation
- [Architecture Patterns](../../steering/structure.md) - Hexagonal architecture
- [Agent Squad Config](../../AGENT_SQUAD_VERTEX_DEEPINFRA.md) - Agent configuration

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial documentation plan |
| 1.1 | 2026-01-29 | Completed SWAP_WORKFLOW documentation (5 files) |
| 1.2 | 2026-01-29 | Completed BUY_WORKFLOW documentation (5 files) |
| 1.3 | 2026-01-29 | Completed PORTFOLIO documentation (5 files) |
| 1.4 | 2026-01-29 | Completed WALLET documentation (5 files) |
| 1.5 | 2026-01-29 | Completed KNOWLEDGE documentation (5 files) |
| 1.6 | 2026-01-29 | Completed EXECUTION documentation (5 files) |
| 1.7 | 2026-01-29 | Completed RISK_ANALYZER documentation (5 files) |
| 1.8 | 2026-01-29 | Completed DEFI_YIELD documentation (5 files) |
| 1.9 | 2026-01-29 | Completed RESEARCH documentation (5 files) |
| 1.10 | 2026-01-29 | Completed GAS_OPTIMIZER documentation (5 files) |
| 1.11 | 2026-01-29 | Completed CHAT documentation (5 files) |
| 1.12 | 2026-01-29 | Completed GUEST_AUTH documentation (5 files) |
| 1.13 | 2026-01-29 | Completed TAX_OPTIMIZER documentation (5 files) |
| 1.14 | 2026-01-29 | Completed SECURITY_AUDITOR documentation (5 files) |
| 1.15 | 2026-01-29 | Completed ALERT_MONITORING documentation (5 files) |
| 1.16 | 2026-01-29 | Completed CRISIS_MANAGER documentation (5 files) |
| 1.17 | 2026-01-29 | Completed COMPLIANCE_MONITOR documentation (5 files) |
| 1.18 | 2026-01-29 | Completed MULTISIG_COORDINATOR documentation (5 files) - **100% COMPLETE** |

---

**End of Documentation Plan**

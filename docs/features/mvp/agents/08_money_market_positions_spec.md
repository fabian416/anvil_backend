# Money Market “My Positions” + Withdraw Specification

**Version**: 1.0  
**Date**: 2026-02-02  
**Status**: 📋 SPEC (Not Implemented)  
**Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
**Recallium**: Enabled. Memory #1856

---

## Implementation Status

| Phase | Component | Status |
|-------|-----------|--------|
| Phase 1 | Problem decomposition & gap analysis | 📋 Spec complete |
| Phase 2 | Solution options & trade-offs | 📋 Spec complete |
| Phase 3 | Risk & validation design | 📋 Spec complete |
| Phase 4 | Implementation (workflow, routing, execute) | ⏳ Pending |

---

## Executive Summary

This spec defines the **“see my positions in money market”** experience (list supply positions + withdraw) for the unified chat flow. It applies CTO methodology to choose where this flow lives (extend MoneyMarketWorkflow vs reuse LendingWorkflow) and how it integrates with existing execute and gateway infrastructure.

**Scope**: Supply positions on **Aave** and **Morpho** (and Compound only if a position API exists). Flow: list positions (numbered) → user selects by number → amount or max → confirm → build tx via existing gateways → `execute_data` / execute endpoint.

---

## Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 User Need

- **User says**: “Show my money market positions”, “My lendings in money market”, “Withdraw from money market”, “What am I earning in money market?”
- **Expected**: See a numbered list of supply positions (protocol, asset, amount, APY) and be able to choose one to withdraw (amount or max) with confirmation, then execute via existing execute flow.

### 1.2 Current State

| Component | Current behavior |
|-----------|------------------|
| **LendingWorkflowAgent** | Implements “my lendings” + withdraw: `_handle_withdraw_request` → `_fetch_user_positions` (Morpho + Aave) → `_show_position_selection` (numbered) → `_ask_withdraw_amount` → `_show_withdraw_confirmation` → `_handle_withdraw_execute` (MorphoGateway / AaveGateway → `execute_data`). No “money market” branding or routing. |
| **MoneyMarketWorkflowAgent** | Only **rate comparison**: parse request → fetch data → compare → select protocol for **deposit**. No “my positions” or withdraw. |
| **AuthenticatedSupervisor** | “Compare rates” / “money market” → **money_market_workflow**. Lending deposit/withdraw (including “my lendings”) → **lending_workflow**. No routing for “my money market positions” or “withdraw from money market”. |

### 1.3 Gap vs “My Lendings”

- **Semantic**: “Money market” and “lending” are the same underlying supply positions (Aave + Morpho). “My money market positions” is a naming/UX variant of “my lendings”.
- **Functional**: LendingWorkflow already has positions + withdraw; MoneyMarketWorkflow has neither.
- **Routing**: No intent/phrases that send “money market positions” or “withdraw from money market” to the right workflow.

### 1.4 Root Cause

- **Primary**: MoneyMarketWorkflow was designed only for rate comparison (deposit path); positions + withdraw were never added there, while LendingWorkflow already implements the full flow.
- **Secondary**: Supervisor and knowledge layer do not map “money market positions” / “withdraw from money market” to the existing lending positions + withdraw flow.

### 1.5 Solution Space Mapping

**Invariants:**

- Reuse existing execute flow: `execute_data` → user sign → POST `/execute` (no new execution path).
- Reuse existing gateways: MorphoGateway, AaveGateway (and Compound only if position API exists).
- Conversation → message → agent response → execute data flow must be preserved.

**Degrees of freedom:**

- **Where** to implement “money market positions + withdraw”: extend MoneyMarketWorkflow vs route to LendingWorkflow vs new dedicated workflow.
- **How** to distinguish “money market” from “lending” in UX: same flow with different intent/labels vs separate flows.

**Hard constraints:**

- Must not duplicate position-fetch or tx-building logic; must use existing MCP/gateways and execute endpoint.
- Must support at least Aave + Morpho supply positions; Compound only if a position API is available.

---

## Phase 2: Solution Generation & Trade-off Analysis

### 2.1 Solution Options

**Option A: Extend MoneyMarketWorkflow with positions + withdraw**

- Add to MoneyMarketWorkflowAgent: fetch positions (Morpho + Aave), show numbered list, amount/max, confirm, build tx via existing gateways, set `execute_data`.
- Supervisor: route “money market positions” / “withdraw from money market” to **money_market_workflow**.
- Pros: Single place for “money market” UX (rates + positions + withdraw).  
- Cons: Duplicates logic already in LendingWorkflow (position fetch, selection, withdraw confirmation, execute_data shape).

**Option B: Route “money market positions” to LendingWorkflow (recommended)**

- Keep positions + withdraw only in LendingWorkflow. Add intents/phrases so that “my money market positions”, “withdraw from money market”, “what am I earning in money market” route to **lending_workflow** with the same flow as “my lendings” + withdraw.
- Pros: No duplication; one implementation for supply positions + withdraw; reuse existing MCP tools and execute integration.  
- Cons: “Money market” and “lending” are presented as the same flow (acceptable for MVP).

**Option C: New “MoneyMarketPositionsWorkflow”**

- New small workflow that only lists positions and delegates withdraw to the same execute path (could call LendingWorkflow’s helpers or gateways).
- Pros: Clear separation of “money market” product name.  
- Cons: Extra workflow to maintain; still needs to reuse gateways and execute flow; more surface for bugs.

### 2.2 Trade-off Matrix

| Solution | Consistency with existing code | Implementation cost | UX clarity | Risk |
|----------|--------------------------------|----------------------|------------|------|
| **A – Extend MoneyMarket** | Low (duplicate logic) | High | High (“money market” in one place) | Medium (two code paths for same ops) |
| **B – Route to Lending** | High (single flow) | Low | Medium (same as “my lendings”) | Low |
| **C – New workflow** | Medium (reuse gateways only) | Medium | High | Medium |

**Selected: Option B (route “money market positions” to LendingWorkflow)**

**Rationale:**

- Same underlying data and actions (supply positions on Aave/Morpho + withdraw). One flow reduces bugs and maintenance.
- Implementation is limited to supervisor + knowledge layer (intents/phrases); no new workflow or duplicate position/withdraw logic.
- MVP can treat “money market” and “lending” as the same flow; later we can add a thin “money market” label in responses without a second workflow.

### 2.3 Constraint Priority

1. **Correctness**: Reuse existing position fetch and withdraw execution; no new execute path.
2. **Consistency**: One source of truth for positions + withdraw (LendingWorkflow).
3. **Discoverability**: Users saying “money market positions” or “withdraw from money market” must hit this flow via routing.

---

## Phase 3: Risk Assessment & Validation Design

### 3.1 Assumptions

- “Money market positions” is defined as **supply positions** on Aave and Morpho (and Compound only if position API exists). No separate “money market” table; same as lending supplies.
- Execute payload and gateway contracts stay as today; this spec only adds routing and intent coverage.

### 3.2 Risks

| Risk | Mitigation |
|------|-------------|
| Users expect “money market” to be a different product | Document that money market = lending supply positions; optional: add response copy that says “Money market (lending) positions” in the agent reply. |
| Phrases not covered | Add patterns in knowledge/shortcuts for “money market positions”, “withdraw from money market”, “what am I earning in money market”, multi-language. |
| Compound | Include only when a position API is available; otherwise Aave + Morpho only. |

### 3.3 Success Criteria

- User says “show my money market positions” or equivalent → routed to lending_workflow → sees numbered list of supply positions (Aave + Morpho).
- User selects position and requests withdraw (amount or max) → same confirm → execute_data → execute endpoint as current “my lendings” withdraw.
- No new execute endpoint or new gateway; only routing and intent changes.

### 3.4 Validation

- **Acceptance**: Manual or automated tests that trigger “money market positions” and “withdraw from money market” and assert routing to LendingWorkflow and correct execute_data.
- **Regression**: Existing “my lendings” + withdraw flows unchanged.

---

## Phase 4: Implementation Outline

### 4.1 Definition of “Money Market Positions”

- **In scope**: Supply (lend) positions on **Aave** and **Morpho**. Optional: **Compound** if a position API exists.
- **Out of scope (for this spec)**: Borrow positions, collateral positions, or protocols without a position API in the stack.

### 4.2 Flow (Reuse LendingWorkflow)

1. User sends message like “my money market positions” or “withdraw from money market”.
2. Supervisor routes to **lending_workflow** (new intent/phrase mapping).
3. LendingWorkflowAgent:
   - Fetches user positions via existing `_fetch_user_positions` (Morpho + Aave).
   - Shows numbered list (`_show_position_selection`).
   - If user intent is withdraw: `_ask_withdraw_amount` → `_show_withdraw_confirmation` → `_handle_withdraw_execute` (build tx via MorphoGateway or AaveGateway, then `execute_data`).
4. Frontend/execute: unchanged; same POST `/execute` and execute payload as current lending withdraw.

### 4.3 Routing Changes

**AuthenticatedSupervisor** (or equivalent routing layer):

- Add detection for “money market positions”, “withdraw from money market”, “what am I earning in money market” (and localized variants).
- Route these to **lending_workflow** (same as “my lendings” / “withdraw from lending”).

**Knowledge / Shortcuts** (e.g. `shortcuts.json` or intent config):

- Add intent(s) or patterns, e.g. `MONEY_MARKET_POSITIONS` and/or extend `LENDING_POSITION` / `LENDING_WITHDRAW` with money-market phrases:
  - EN: “my money market positions”, “money market positions”, “withdraw from money market”, “what am I earning in money market”
  - ES/PT/ZH: equivalent phrases as per product.
- Set agent to `LENDING_WORKFLOW` and reuse existing action (e.g. position list + withdraw).

### 4.4 Execute Payload

- No change. Reuse existing withdraw `execute_data` shape produced by LendingWorkflowAgent (provider, protocol, chain, amount, market_id/asset_address, etc.) and existing execute endpoint behavior.

### 4.5 Implementation Checklist

- [ ] Add “money market positions” / “withdraw from money market” (and variants) to supervisor routing → lending_workflow.
- [ ] Add or extend intents/patterns in knowledge/shortcuts for money market positions and withdraw; agent = LENDING_WORKFLOW.
- [ ] Optionally: add response copy in LendingWorkflowAgent when triggered by money-market intent (e.g. “Money market (lending) positions”) for UX.
- [ ] Document “money market = supply positions on Aave/Morpho” in product/glossary if needed.
- [ ] Acceptance test: “my money market positions” → list; select + withdraw → execute.

---

## Recallium Summary (store this for recall)

**Feature**: Money market “my positions” + withdraw.  
**Decision**: Route “my money market positions” and “withdraw from money market” to **LendingWorkflow** (no new workflow; reuse existing positions + withdraw and execute flow).  
**Scope**: Aave + Morpho supply positions; Compound only if position API exists.  
**Implementation**: Supervisor + knowledge/shortcuts add money-market phrases → LENDING_WORKFLOW; no new execute path or gateways.  
**Spec**: `docs/features/mvp/agents/08_money_market_positions_spec.md`

---

## References

- CTO methodology: `cto.md`
- Lending positions + withdraw: `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`
- Money market (rates only): `src/app/infrastructure/adapters/agent_squad/agents/workflows/money_market_workflow_agent.py`
- Supervisor routing: `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- Morpho withdraw spec: `07_morpho_withdraw_implementation_spec.md`

# Money Market “My Positions” + Withdraw Specification

**Version**: 1.2  
**Date**: 2026-02-02  
**Status**: ✅ Option A Implemented (Aave + Compound only; Compound withdraw + Hunter sentiment enrichment)  
**Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
**Recallium**: Enabled. Memory #1856

---

## Implementation Status

| Phase | Component | Status |
|-------|-----------|--------|
| Phase 1 | Problem decomposition & gap analysis | 📋 Spec complete |
| Phase 2 | Solution options & trade-offs | 📋 Spec complete |
| Phase 3 | Risk & validation design | 📋 Spec complete |
| Phase 4 | **Option A** Implementation | ✅ Complete |
| 4.1 | MoneyMarketWorkflowAgent positions + withdraw flow | ✅ 310b03a4 |
| 4.2 | Supervisor route to money_market_workflow | ✅ bad0d0a7 |
| 4.3 | Shortcuts MONEY_MARKET_POSITIONS intent | ✅ d5513d7d |
| 4.4 | Money market = **Aave + Compound only** (Morpho removed) | ✅ |
| 4.5 | **Compound withdraw** (gateway + client + workflow) | ✅ |
| 4.6 | **Enrichment**: Hunter sentiment on positions list, withdraw confirm, ready-to-withdraw | ✅ |

---

## Executive Summary

This spec defines the **“see my positions in money market”** experience (list supply positions + withdraw) for the unified chat flow. It applies CTO methodology to choose where this flow lives (extend MoneyMarketWorkflow vs reuse LendingWorkflow) and how it integrates with existing execute and gateway infrastructure.

**Scope**: Supply positions on **Aave** and **Compound** only (no Morpho). Flow: list positions (numbered) → user selects by number → amount or max → confirm → build tx via AaveGateway or CompoundGateway → `execute_data` / execute endpoint. **Compound withdraw** is implemented (Comet `withdraw(address,uint256)`).

---

## Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 User Need

- **User says**: “Show my money market positions”, “My lendings in money market”, “Withdraw from money market”, “What am I earning in money market?”
- **Expected**: See a numbered list of supply positions (protocol, asset, amount, APY) and be able to choose one to withdraw (amount or max) with confirmation, then execute via existing execute flow.

### 1.2 Current State

| Component | Current behavior |
|-----------|------------------|
| **LendingWorkflowAgent** | Implements “my lendings” + withdraw (Morpho + Aave). Separate flow from money market. |
| **MoneyMarketWorkflowAgent** | **Rate comparison** (Aave + Compound) + **positions + withdraw** (Aave + Compound): `_fetch_user_positions_mm`, `_handle_positions_withdraw_execute` using AaveGateway and CompoundGateway. |
| **AuthenticatedSupervisor** | “Money market positions” / “withdraw from money market” → **money_market_workflow**. “Compare rates” / “money market” → **money_market_workflow**. |

### 1.3 Gap vs “My Lendings”

- **Semantic**: “Money market” is supply positions on Aave + Compound (distinct from LendingWorkflow which uses Morpho + Aave for “my lendings”).
- **Functional**: MoneyMarketWorkflow now has positions + withdraw for Aave + Compound only.
- **Routing**: No intent/phrases that send “money market positions” or “withdraw from money market” to the right workflow.

### 1.4 Root Cause

- **Primary**: MoneyMarketWorkflow was designed only for rate comparison (deposit path); positions + withdraw were never added there, while LendingWorkflow already implements the full flow.
- **Secondary**: Supervisor and knowledge layer do not map “money market positions” / “withdraw from money market” to the existing lending positions + withdraw flow.

### 1.5 Solution Space Mapping

**Invariants:**

- Reuse existing execute flow: `execute_data` → user sign → POST `/execute` (no new execution path).
- Reuse existing gateways: AaveGateway, CompoundGateway (money market uses Aave + Compound only).
- Conversation → message → agent response → execute data flow must be preserved.

**Degrees of freedom:**

- **Where** to implement “money market positions + withdraw”: extend MoneyMarketWorkflow vs route to LendingWorkflow vs new dedicated workflow.
- **How** to distinguish “money market” from “lending” in UX: same flow with different intent/labels vs separate flows.

**Hard constraints:**

- Must not duplicate position-fetch or tx-building logic; must use existing MCP/gateways and execute endpoint.
- Money market supports **Aave + Compound** supply positions and withdraw (both gateways implement build_withdraw).

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

- “Money market positions” is defined as **supply positions** on Aave and Compound only (no Morpho in this flow). Compound supports list + withdraw via Comet `withdraw(address,uint256)`.
- Execute payload and gateway contracts stay as today; this spec only adds routing and intent coverage.

### 3.2 Risks

| Risk | Mitigation |
|------|-------------|
| Users expect “money market” to be a different product | Document that money market = lending supply positions; optional: add response copy that says “Money market (lending) positions” in the agent reply. |
| Phrases not covered | Add patterns in knowledge/shortcuts for “money market positions”, “withdraw from money market”, “what am I earning in money market”, multi-language. |
| Compound | Implemented: position API + withdraw (CompoundGateway.build_withdraw_supply_transaction, Comet withdraw). |

### 3.3 Success Criteria

- User says “show my money market positions” or equivalent → routed to money_market_workflow → sees numbered list of supply positions (Aave + Compound).
- User selects position and requests withdraw (amount or max) → confirm → execute_data (Aave or Compound tx) → execute endpoint.
- No new execute endpoint or new gateway; only routing and intent changes.

### 3.4 Validation

- **Acceptance**: Manual or automated tests that trigger “money market positions” and “withdraw from money market” and assert routing to LendingWorkflow and correct execute_data.
- **Regression**: Existing “my lendings” + withdraw flows unchanged.

---

## Phase 4: Implementation Outline

### 4.1 Definition of “Money Market Positions”

- **In scope**: Supply (lend) positions on **Aave** and **Compound** only. Both support list + withdraw (AaveGateway, CompoundGateway `build_withdraw_supply_transaction`; Compound uses Comet `withdraw(address,uint256)`).
- **Out of scope (for this spec)**: Morpho (not used in money market flow), borrow positions, or protocols without position + withdraw in the stack.

### 4.2 Flow (Option A: MoneyMarketWorkflow)

1. User sends message like “my money market positions” or “withdraw from money market”.
2. Supervisor routes to **money_market_workflow** (intent MONEY_MARKET_POSITIONS).
3. MoneyMarketWorkflowAgent:
   - Fetches user positions via `_fetch_user_positions_mm` (Aave + Compound only, Base).
   - Shows numbered list (`_show_position_selection_mm`).
   - If user selects and requests withdraw: `_ask_withdraw_amount_mm` → `_show_withdraw_confirmation_mm` → `_handle_positions_withdraw_execute` (build tx via AaveGateway or CompoundGateway, then `execute_data`).
4. Frontend/execute: unchanged; same execute payload and POST `/execute` as lending withdraw.

### 4.3 Routing Changes

**AuthenticatedSupervisor**:

- Detection for “money market positions”, “withdraw from money market”, “what am I earning in money market” (and localized variants, including typo-tolerant “possitions”).
- Route these to **money_market_workflow**.

**Knowledge / Shortcuts** (`shortcuts.json`):

- Intent `MONEY_MARKET_POSITIONS`, agent `MONEY_MARKET_WORKFLOW`.
- Patterns for “my money market positions”, “money market positions”, “withdraw from money market”, etc. (EN/ES/PT).

### 4.4 Execute Payload

- Reuse existing withdraw `execute_data` shape (action_type=withdraw, provider=aave|compound, chain, amount, asset_symbol, asset_address, tx_to, tx_data, tx_value) and existing execute endpoint behavior.

### 4.5 Implementation Checklist (Option A implemented)

- [x] Add “money market positions” / “withdraw from money market” (and variants) to supervisor routing → money_market_workflow.
- [x] Add MONEY_MARKET_POSITIONS intent in shortcuts; agent = MONEY_MARKET_WORKFLOW.
- [x] Money market = **Aave + Compound only** (Morpho removed from positions and rate comparison).
- [x] **Compound withdraw**: CompoundGateway `build_withdraw_supply_transaction`, CompoundClient `build_withdraw_transaction` (Comet `withdraw(address,uint256)`), workflow branch in `_handle_positions_withdraw_execute`.
- [ ] Acceptance test: “my money market positions” → list (Aave + Compound); select + withdraw → execute (Aave or Compound).

### 4.6 Enrichment (Hunter sentiment + more data)

- **Optional, best-effort**: Money market responses can be enriched with Hunter sentiment for the position asset (e.g. USDC, USD).
- **Port**: `AssetSentimentProvider` (`get_sentiment(asset_symbol) → dict | None`); implementation: `AssetSentimentService` (news sentiment, 5s timeout).
- **Flow**: MoneyMarketWorkflowAgent accepts optional `sentiment_provider`; at three response points (positions list, withdraw confirm, “ready to withdraw”) it calls `_enrich_with_sentiment`: appends a short line (e.g. “📊 **Sentiment:** bullish (score 72)”) and sets `state.data["sentiment_analysis"]`. Base workflow passes this into response `metadata["sentiment_analysis"]`; supervisor and conversations router expose it in `enrichment.sentiment_analysis` for the client.
- **Shape of sentiment_analysis**: `{ "score": 0–100, "classification": "bullish"|"bearish"|"neutral", "token_symbol": "USDC" }` (or `None` if unavailable).
- **DI**: `AssetSentimentService` provided in `AgentSquadInfrastructureProvider`; injected into `MoneyMarketWorkflowAgent` as `sentiment_provider`. If sentiment fetch fails or times out, the workflow response is unchanged (no blocking).

---

## Recallium Summary (store this for recall)

**Feature**: Money market “my positions” + withdraw.  
**Decision**: Option A implemented — extend **MoneyMarketWorkflow** with positions + withdraw; route “my money market positions” and “withdraw from money market” to **money_market_workflow**.  
**Scope**: **Aave + Compound only** (no Morpho). Both protocols: list positions and withdraw (AaveGateway, CompoundGateway `build_withdraw_supply_transaction`; Compound uses Comet `withdraw(address,uint256)`).  
**Implementation**: Supervisor + shortcuts MONEY_MARKET_POSITIONS → MONEY_MARKET_WORKFLOW; `_fetch_user_positions_mm` (Aave + Compound); `_handle_positions_withdraw_execute` (Aave + Compound build tx → execute_data).  
**Spec**: `docs/features/mvp/agents/08_money_market_positions_spec.md`

---

## References

- CTO methodology: `cto.md`
- Money market (positions + withdraw, Aave + Compound): `src/app/infrastructure/adapters/agent_squad/agents/workflows/money_market_workflow_agent.py`
- Compound gateway (build_withdraw_supply_transaction): `src/app/domain/ports/compound_gateway.py`
- Compound client (build_withdraw_transaction, Comet withdraw): `src/app/infrastructure/adapters/external/compound_client.py`
- Compound adapter: `src/app/infrastructure/adapters/external/compound_adapter.py`
- Supervisor routing: `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- Lending workflow (separate flow): `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`

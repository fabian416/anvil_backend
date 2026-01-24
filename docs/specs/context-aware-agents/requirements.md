# Context-Aware Agent Responses Specification

> **Spec Version:** 1.0  
> **Status:** Draft  
> **Created:** 2026-01-23  
> **Author:** Engineering Team

## Executive Summary

This specification defines a system for **context-aware agent responses** that adapt based on user portfolio state (empty, active, high-value). The goal is to provide relevant, actionable guidance instead of generic responses.

---

## 1. Problem Analysis (First Principles)

### 1.1 Current State

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Request ─────► Authenticated Supervisor                    │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────────┐                        │
│                      │  UserDataService │                        │
│                      │  - Wallet        │                        │
│                      │  - Portfolio     │ ◄── Data fetched but   │
│                      │  - Transactions  │     NOT used for       │
│                      └────────┬─────────┘     routing decisions  │
│                               │                                  │
│                               ▼                                  │
│                      ┌──────────────────┐                        │
│                      │  Agent Routing   │ ◄── Generic routing    │
│                      │  (LLM-based)     │     ignores balance    │
│                      └────────┬─────────┘                        │
│                               │                                  │
│                               ▼                                  │
│                      ┌──────────────────┐                        │
│                      │  Agent Response  │ ◄── Same response      │
│                      │  (Generic)       │     regardless of      │
│                      └──────────────────┘     user state         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Identified Issues

| Issue | Impact | Example |
|-------|--------|---------|
| **Generic empty state responses** | Users get irrelevant suggestions | Empty portfolio: "Try swap" (can't swap without tokens) |
| **No balance validation in workflows** | Failed transactions | Swap 1 ETH when user has 0 ETH |
| **Missing onboarding flow** | Poor UX for new users | No guided first-purchase flow |
| **No portfolio-aware recommendations** | Missed optimization opportunities | User with 100% ETH not advised to diversify |

### 1.3 Root Cause

The `UserDataContext` is fetched but only used for:
1. Display in agent context strings
2. LLM prompt injection

It is **NOT** used for:
1. Routing decisions
2. Response template selection
3. Workflow pre-validation
4. Personalized recommendations

---

## 2. Proposed Solution

### 2.1 User State Classification

```python
class UserPortfolioState(Enum):
    """User portfolio states for context-aware routing."""
    
    EMPTY = "empty"           # No holdings, $0 value
    STARTER = "starter"       # < $100 value, 1-2 tokens
    ACTIVE = "active"         # $100-$10,000, 3+ tokens
    WHALE = "whale"           # > $10,000 value
    
    @classmethod
    def from_portfolio(cls, portfolio: PortfolioSummary | None) -> "UserPortfolioState":
        if not portfolio or portfolio.total_value_usd == 0:
            return cls.EMPTY
        if portfolio.total_value_usd < 100:
            return cls.STARTER
        if portfolio.total_value_usd < 10000:
            return cls.ACTIVE
        return cls.WHALE
```

### 2.2 Architecture Enhancement

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROPOSED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Request ─────► Authenticated Supervisor                    │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────────┐                        │
│                      │  UserDataService │                        │
│                      └────────┬─────────┘                        │
│                               │                                  │
│                               ▼                                  │
│                      ┌──────────────────┐                        │
│                      │ UserStateClassifier│ ◄── NEW: Classify    │
│                      │ - EMPTY           │     user state        │
│                      │ - STARTER         │                       │
│                      │ - ACTIVE          │                       │
│                      │ - WHALE           │                       │
│                      └────────┬─────────┘                        │
│                               │                                  │
│                               ▼                                  │
│                      ┌──────────────────┐                        │
│                      │ Context-Aware    │ ◄── NEW: State-based   │
│                      │ Routing & Prompts│     prompt selection   │
│                      └────────┬─────────┘                        │
│                               │                                  │
│                               ▼                                  │
│              ┌────────────────┼────────────────┐                 │
│              ▼                ▼                ▼                 │
│       ┌───────────┐    ┌───────────┐    ┌───────────┐           │
│       │ Onboarding│    │ Standard  │    │ Advanced  │           │
│       │ Response  │    │ Response  │    │ Response  │           │
│       │ (EMPTY)   │    │ (ACTIVE)  │    │ (WHALE)   │           │
│       └───────────┘    └───────────┘    └───────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Design

### 3.1 Response Templates by State

#### EMPTY State (New Users)

```python
EMPTY_STATE_RESPONSES = {
    "portfolio": {
        "message": """**Welcome to Anvil! 🚀**

Your portfolio is ready to grow.

**Start here:**
→ "buy 100 USD of ETH" - Purchase your first crypto
→ "what is ETH" - Learn about Ethereum first

Once you have crypto, you can swap, earn yield, and more!""",
        "suggested_actions": ["buy", "learn"],
    },
    "wallet": {
        "message": """**Your Wallet:** `{address}`

Ready to receive crypto! Here's how to start:
→ "buy 100 USD of ETH" - Purchase crypto directly
→ Or transfer from another wallet to this address""",
    },
    "activity": {
        "message": """**No Activity Yet**

Make your first purchase to see activity here:
→ "buy 100 USD of ETH" """,
    },
    "swap": {
        "message": """**You need crypto to swap!**

Get started:
→ "buy 100 USD of ETH" - Then you can swap to other tokens""",
        "block_workflow": True,  # Don't start swap workflow
    },
}
```

#### ACTIVE State (Regular Users)

```python
ACTIVE_STATE_RESPONSES = {
    "portfolio": {
        "message": """**Your Portfolio:** ${total_value:,.2f}

**Holdings:**
{holdings_list}

**Suggestions:**
{personalized_suggestions}""",
    },
    "swap": {
        "pre_validate": True,  # Check balance before workflow
        "insufficient_balance_message": """**Insufficient {token}**

You have {available} {token}, but need {required} {token}.

Options:
→ "swap {available} {token} to {to_token}" - Swap what you have
→ "buy {shortfall} USD of {token}" - Buy more first""",
    },
}
```

### 3.2 Workflow Pre-Validation

```python
async def validate_workflow_prerequisites(
    workflow_type: str,
    params: dict,
    user_context: UserDataContext,
) -> tuple[bool, str | None]:
    """
    Validate user can perform workflow before starting.
    
    Returns:
        (is_valid, error_message)
    """
    state = UserPortfolioState.from_portfolio(user_context.portfolio)
    
    if workflow_type == "swap":
        # Check if user has the from_token
        from_token = params.get("from_token", "").upper()
        amount = params.get("amount", 0)
        
        if state == UserPortfolioState.EMPTY:
            return False, EMPTY_STATE_RESPONSES["swap"]["message"]
        
        # Check specific balance
        holding = _find_holding(user_context.portfolio, from_token)
        if not holding or holding.amount < amount:
            return False, f"Insufficient {from_token}. You have {holding.amount if holding else 0}."
    
    if workflow_type == "lending":
        # Similar validation
        pass
    
    return True, None
```

### 3.3 Supervisor Prompt Enhancement

```python
def _build_state_aware_prompt(
    self,
    user_state: UserPortfolioState,
    conversation_context: ConversationContext,
) -> str:
    """Build prompt with state-aware instructions."""
    
    base_prompt = self._get_base_prompt()
    
    state_instructions = {
        UserPortfolioState.EMPTY: """
⚠️ USER HAS EMPTY PORTFOLIO - SPECIAL HANDLING:
- DO NOT suggest swap/transfer/yield (user has no tokens)
- ALWAYS suggest "buy" as the first action
- Be encouraging and educational
- Guide toward first purchase
""",
        UserPortfolioState.STARTER: """
⚠️ USER IS NEW (< $100 portfolio):
- Suggest small, safe operations
- Explain gas costs relative to their balance
- Prioritize education alongside actions
""",
        UserPortfolioState.ACTIVE: """
✅ USER HAS ACTIVE PORTFOLIO:
- Full feature access
- Provide optimization suggestions
- Consider diversification in recommendations
""",
        UserPortfolioState.WHALE: """
✅ HIGH-VALUE USER (> $10k):
- Full feature access
- Consider gas optimization
- Suggest advanced strategies (yield, DeFi)
- Be mindful of slippage on large trades
""",
    }
    
    return f"{base_prompt}\n\n{state_instructions[user_state]}"
```

---

## 4. Implementation Plan

### Phase 1: State Classification (1-2 days)

| Task | File | Priority |
|------|------|----------|
| Create `UserPortfolioState` enum | `src/app/domain/enums/user_portfolio_state.py` | P0 |
| Add classifier method to `UserDataContext` | `src/app/application/chat/services/user_data_service.py` | P0 |
| Add state to supervisor context | `src/app/domain/services/agent_squad/authenticated_supervisor.py` | P0 |

### Phase 2: Response Templates (2-3 days)

| Task | File | Priority |
|------|------|----------|
| Create response templates module | `src/app/infrastructure/adapters/agent_squad/response_templates.py` | P1 |
| Update PortfolioAgent for state-aware responses | `src/app/infrastructure/adapters/agent_squad/agents/portfolio_agent.py` | P1 |
| Update WalletAgent | `src/app/infrastructure/adapters/agent_squad/agents/wallet_agent.py` | P1 |
| Update TransactionHistoryAgent | `src/app/infrastructure/adapters/agent_squad/agents/transaction_history_agent.py` | P1 |

### Phase 3: Workflow Validation (2-3 days)

| Task | File | Priority |
|------|------|----------|
| Create validation service | `src/app/application/chat/services/workflow_validator.py` | P1 |
| Integrate into SwapWorkflow | `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py` | P1 |
| Integrate into LendingWorkflow | `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py` | P2 |
| Integrate into BuyWorkflow | `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py` | P2 |

### Phase 4: Supervisor Enhancement (1-2 days)

| Task | File | Priority |
|------|------|----------|
| Add state-aware prompt building | `authenticated_supervisor.py` | P1 |
| Add workflow pre-validation hook | `authenticated_supervisor.py` | P1 |
| Update routing for empty users | `authenticated_supervisor.py` | P2 |

---

## 5. Trade-off Analysis

### Option A: Agent-Level State Handling (Selected)
```
✅ Pros:
- Each agent handles its own state logic
- Easier to customize per-agent behavior
- Incremental implementation possible

❌ Cons:
- Duplicated logic across agents
- Harder to maintain consistency
```

### Option B: Supervisor-Level State Routing
```
✅ Pros:
- Centralized state handling
- Consistent behavior
- Single point of change

❌ Cons:
- Less flexibility per-agent
- Supervisor becomes more complex
```

### Option C: Middleware Layer
```
✅ Pros:
- Clean separation
- Reusable across supervisor types

❌ Cons:
- Additional abstraction layer
- More files to maintain
```

**Decision: Hybrid approach**
- State classification at supervisor level
- Response templates at agent level
- Workflow validation as reusable service

---

## 6. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Empty user → first purchase rate | Unknown | > 30% |
| Failed workflow starts (insufficient balance) | ~5% | < 1% |
| User satisfaction (empty portfolio queries) | Low | High |
| Time to first transaction (new users) | > 5 min | < 2 min |

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| State classification errors | Wrong response type | Add fallback to generic responses |
| Performance overhead | Slower responses | Cache user state per session |
| Breaking existing flows | Regression | Comprehensive test coverage |
| Over-personalization | Feels creepy | Keep suggestions helpful, not intrusive |

---

## 8. Testing Strategy

### Unit Tests
```python
def test_user_state_classification():
    # EMPTY
    assert UserPortfolioState.from_portfolio(None) == UserPortfolioState.EMPTY
    assert UserPortfolioState.from_portfolio(PortfolioSummary(total_value_usd=0)) == UserPortfolioState.EMPTY
    
    # STARTER
    assert UserPortfolioState.from_portfolio(PortfolioSummary(total_value_usd=50)) == UserPortfolioState.STARTER
    
    # ACTIVE
    assert UserPortfolioState.from_portfolio(PortfolioSummary(total_value_usd=5000)) == UserPortfolioState.ACTIVE
    
    # WHALE
    assert UserPortfolioState.from_portfolio(PortfolioSummary(total_value_usd=50000)) == UserPortfolioState.WHALE
```

### Integration Tests
```python
async def test_empty_user_swap_blocked():
    """Empty users should not be able to start swap workflow."""
    response = await send_message("swap 1 ETH to USDC", user_with_empty_portfolio)
    assert "buy" in response.lower()
    assert "insufficient" in response.lower() or "need crypto" in response.lower()
```

---

## Appendix: Agent Inventory

### Agents Using User Balance Context

| Agent | Uses Portfolio | Uses Wallet | Uses Transactions | State-Aware |
|-------|---------------|-------------|-------------------|-------------|
| `PortfolioAgent` | ✅ | ✅ | ❌ | 🔄 Needs update |
| `WalletAgent` | ❌ | ✅ | ❌ | 🔄 Needs update |
| `TransactionHistoryAgent` | ❌ | ❌ | ✅ | 🔄 Needs update |
| `SwapWorkflowAgent` | ❌ | ✅ | ❌ | 🔄 Needs validation |
| `LendingWorkflowAgent` | ❌ | ❌ | ❌ | 🔄 Needs validation |
| `BuyWorkflowAgent` | ❌ | ❌ | ❌ | ✅ Already for empty users |
| `HunterAIAgent` | ❌ | ❌ | ❌ | ➖ Not needed |
| `GasOptimizerAgent` | ❌ | ❌ | ❌ | ➖ Not needed |

### Current Data Flow

```
AuthenticatedSupervisorCoordinator
    │
    ├── load_user_data(user_id)
    │       │
    │       └── UserDataService.get_user_context()
    │               │
    │               ├── WalletRepository.get_wallets()
    │               ├── PortfolioRepository.get_portfolio()
    │               └── TransactionRepository.get_recent()
    │
    ├── UserDataContext stored in self._user_data_context
    │
    └── Passed to agents via conversation_context.user_metadata
            │
            └── Each agent extracts via _extract_user_context()
```

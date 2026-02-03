# Context Management Gap Analysis - Lending Workflow

**Date**: 2026-01-27
**Author**: Context Manager Agent
**Status**: Gap Analysis Complete

---

## 1. Current Context Management Architecture

### 1.1 UserContextService Implementation

**Location**: `src/app/application/chat/services/user_context_service.py`

The `UserContextService` provides pre-computed user context for context-aware agent responses:

```python
class UserContextService:
    """
    Service for managing user context awareness data.

    This service:
    1. Creates context for new users during privy-login
    2. Updates context periodically via Celery task
    3. Provides context for authenticated supervisor
    """
```

**Current Capabilities**:
- Creates context records during user registration (privy-login)
- Updates context periodically via Celery background task
- Aggregates data from chat_messages, chat_conversations, wallets
- Provides `UserContextAware` entity for supervisor injection

**Data Sources Aggregated**:
| Source | Data | Implementation Status |
|--------|------|----------------------|
| Chat Messages | message_count, messages_7d, messages_30d | Implemented |
| Chat Conversations | session_count, conversation_count | Implemented |
| Wallets | wallet_count, primary_address, provider | Implemented |
| Wallet Balances | total_balance_usd, chain_breakdown | Implemented via `WalletBalancePort` |
| Execution History | swap_count, buy_count, lending_count | Implemented via message metadata |

### 1.2 Context Variables Available Today

**UserContextAware Entity** (`src/app/domain/chat/entities/user_context_aware.py`):

| Variable | Type | Description | Available |
|----------|------|-------------|-----------|
| `is_authenticated` | bool | Derived from entity existence | Yes (implicit) |
| `wallet_address` | str | `primary_wallet_address` | Yes |
| `portfolio_state` | str | empty/starter/active/whale | Yes |
| `total_balance_usd` | Decimal | Total USD balance | Yes |
| `activity_level` | str | new/active/returning/inactive | Yes |
| `user_type` | str | new_user/casual/trader/yield_farmer | Yes |
| `has_connected_wallet` | bool | Wallet connection status | Yes |
| `wallet_total_usd` | Decimal | Wallet-specific balance | Yes |
| `wallet_chain_breakdown` | dict | Balance per chain | Yes |
| `primary_chain` | str | Most used chain | Yes |
| `swap_count` | int | Total swaps | Yes |
| `lending_count` | int | Total lending ops | Yes |
| `execution_success_rate` | Decimal | Success percentage | Yes |

**WorkflowAgent UserContext** (`src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py`):

```python
@dataclass
class UserContext:
    user_id: int | None = None
    wallet_address: str | None = None
    language: str = "en"
    is_authenticated: bool = False
    preferences: dict[str, Any] = field(default_factory=dict)
    portfolio_state: str = "unknown"
    total_balance_usd: float = 0.0
    has_connected_wallet: bool = False
```

### 1.3 State Management Patterns

**Workflow State** (for multi-step workflows):
```python
@dataclass
class WorkflowState:
    step: str = WorkflowStep.PARSE_REQUEST.value
    data: dict[str, Any] = field(default_factory=dict)
    confirmed: bool = False
    cancelled: bool = False
    execute_data: dict[str, Any] | None = None
    error: str | None = None
```

**Conversation Context** (`src/app/domain/value_objects/agent_squad/conversation_context.py`):
```python
@dataclass(frozen=True)
class ConversationContext:
    conversation_history: list[dict] = field(default_factory=list)
    user_metadata: dict = field(default_factory=dict)
    session_metadata: dict = field(default_factory=dict)
```

**Redis-backed Storage** (`src/app/infrastructure/adapters/agent_squad/context_storage_redis.py`):
- Keys: `conversation:{id}:messages`, `conversation:{id}:metadata`
- TTL: 24 hours
- Serialization: JSON

### 1.4 Session Handling

**ConversationStateManager** (`src/app/application/chat/services/conversation_state_manager.py`):
- Flow timeout: 5 minutes
- Off-topic threshold: 2 consecutive messages
- Cancellation keyword detection (multilingual)
- Automatic state cleanup on timeout/cancellation

---

## 2. Context Gap Matrix

| Context Variable | Specified | Current | Gap | Priority | Notes |
|------------------|-----------|---------|-----|----------|-------|
| `is_authenticated` | Yes | Yes | None | - | Implicit from UserContextAware |
| `wallet_address` | Yes | Yes | None | - | `primary_wallet_address` |
| `balance` (dict) | Yes | Partial | **P0** | Critical | Only `total_balance_usd` available, not per-token breakdown |
| `risk_profile` | Yes | **No** | **P0** | Critical | Not computed or stored |
| `tier` | Yes | **No** | **P1** | High | Subscription tier not in context |
| `portfolio_state` | Yes | Yes | None | - | Works correctly |
| `health_factor` | Required | **No** | **P0** | Critical | Required for lending approval flow |
| `pending_transactions` | Required | **No** | **P0** | Critical | No tracking of pending signature requests |
| `token_balances` | Required | **No** | **P0** | Critical | Per-token balance not available in context |
| `gas_estimates` | Required | **No** | **P1** | High | Not included in execute_data |

### 2.1 Critical Gaps Identified

#### GAP-1: No Risk Profile
**Current**: No `risk_profile` variable exists
**Impact**: Cannot provide risk-appropriate recommendations
**Fix**: Add `risk_tolerance` calculation to `UserContextAware` based on:
- Historical leverage usage
- Execution patterns
- Lending position sizes

#### GAP-2: No Subscription Tier
**Current**: `subscription_tier` exists in `AuthenticatedContext` but not in `UserContextAware`
**Impact**: Cannot differentiate premium features or rate limits
**Fix**: Propagate tier from authentication to context service

#### GAP-3: Missing Per-Token Balance
**Current**: Only `total_balance_usd` available
**Impact**: Cannot validate if user has sufficient balance for specific token
**Fix**: Add `token_balances: dict[str, Decimal]` to workflow context

#### GAP-4: No Health Factor Tracking
**Current**: No existing lending position awareness
**Impact**: Cannot show health factor impact for new deposits
**Fix**: Integrate with Aave/Morpho to fetch user positions

#### GAP-5: No Pending Transaction State
**Current**: No Redis-backed pending transaction storage
**Impact**: Cannot persist approval flow state across Privy modal
**Fix**: Add pending transaction store with 5-minute TTL

---

## 3. Multi-Agent Context Flow Gaps

### 3.1 Current State Passing Between Agents

```
User Message
    |
    v
[Intent Detector] --> Detects "deposit 1000 USDC"
    |
    v
[Authenticated Supervisor]
    |  - set_user_context(user_id, wallet_address, portfolio_summary)
    |  - set_context_aware(UserContextAware)
    |
    v
[Lending Workflow Agent]
    |  - _extract_user_context(conversation_context)
    |  - Creates UserContext with portfolio_state, total_balance_usd
    |
    v
[WorkflowState] --> Persisted in message metadata
    |
    v
[Response] --> execute_data for frontend
```

### 3.2 Identified Flow Gaps

| Gap | Description | Impact |
|-----|-------------|--------|
| **Context Serialization** | `UserContextAware` not fully serialized to workflow agents | Agents get partial data |
| **Cross-Agent State** | No explicit state handoff between Market Scanner -> Risk -> Executor | Each agent refetches data |
| **State Cleanup** | Cleanup only on timeout/cancellation, not on completion | Memory leak potential |
| **Redis Key Collision** | No namespace isolation for different workflow types | Potential data corruption |

### 3.3 Missing Context Preservation

**Problem**: Context is rebuilt for each agent invocation rather than preserved

**Current Flow**:
```python
# AuthenticatedSupervisor
if self._context_aware:
    conversation_context.user_metadata["portfolio_state"] = self._context_aware.portfolio_state
    conversation_context.user_metadata["total_balance_usd"] = float(self._context_aware.total_balance_usd or 0)
```

**Gap**: Only 3 fields injected. Missing:
- `lending_count`
- `execution_success_rate`
- `primary_chain`
- `wallet_chain_breakdown`
- `user_type`

### 3.4 State Cleanup Issues

**Current Cleanup Locations**:
1. `ConversationStateManager.clear_flow_state()` - Clears pending intents
2. `ContextStorageRedis` - TTL-based expiration (24 hours)

**Missing Cleanup**:
- No cleanup on workflow completion
- No cleanup on transaction execution
- No cleanup on error states
- No explicit session invalidation

---

## 4. User Approval Context Requirements

### 4.1 Transaction Preview Must Include

| Data | Current Status | Gap |
|------|---------------|-----|
| Asset amounts | Yes (in execute_data) | None |
| USD values | Partial (vault_apy) | Need USD equivalent of deposit |
| Health factor impact | **Missing** | P0 - Critical |
| Gas estimates | **Missing** | P1 - High |
| Risk warnings | **Missing** | P0 - Critical |

### 4.2 Required execute_data Structure for Lending

Current `execute_data` from `LendingWorkflowAgent`:
```python
{
    "action_type": "deposit",
    "provider": "morpho",
    "protocol": "morpho",
    "chain": chain,
    "vault_address": vault_data.get("address"),
    "asset_address": vault_data.get("asset_address"),
    "asset_symbol": vault_data.get("asset_symbol"),
    "amount": amount,
    "slippage": 0.5,
    "vault_name": vault_data.get("name"),
    "supply_apy": vault_data.get("apy"),
}
```

**Required Additions**:
```python
{
    # ... existing fields ...

    # Balance validation (P0)
    "user_token_balance": str,  # User's current balance of the token
    "has_sufficient_balance": bool,  # Pre-validated

    # Health factor (P0)
    "current_health_factor": float | None,  # Before operation
    "projected_health_factor": float | None,  # After operation
    "health_factor_impact": str,  # "safe" | "warning" | "liquidation_risk"

    # Gas estimation (P1)
    "gas_estimate_gwei": int,
    "gas_estimate_usd": float,

    # Risk warnings (P0)
    "risk_warnings": list[str],  # e.g., ["Smart contract risk", "APY may vary"]

    # Protocol comparison (P2)
    "alternative_protocols": list[dict],  # Other options with APY
}
```

### 4.3 Balance Validation Results

**Current**: Balance check in `_handle_execute`:
```python
if user_context.needs_funding_recommendation:
    # Shows helpful message to buy crypto
    response = self._build_insufficient_balance_message(...)
```

**Gap**: Only checks `total_balance_usd`, not specific token balance.

**Required**:
```python
# Check specific token balance
token_balance = user_context.token_balances.get(asset.upper(), Decimal("0"))
if token_balance < Decimal(amount):
    # Insufficient specific token
    pass
```

### 4.4 Context Persistence Through Approval Flow

**Current Flow**:
```
1. User: "deposit 1000 USDC"
2. Agent: Shows quote, generates execute_data
3. Frontend: Opens Privy modal
4. User: Approves in wallet
5. Frontend: Calls /execute with execute_data
6. --- Context Lost Here ---
7. Backend: Executes transaction
```

**Gap**: No persistence between steps 2-7

**Required**: Redis-backed pending transaction store
```python
# Key: pending_tx:{conversation_id}:{action_id}
# TTL: 5 minutes
# Value: {
#     "execute_data": {...},
#     "user_context_snapshot": {...},
#     "created_at": timestamp,
#     "expires_at": timestamp,
# }
```

---

## 5. Context-Aware Response Gaps

### 5.1 Guest User Responses

**Current**: `GuestContext` provides rate limits and feature flags
**Gap**: Guest users receive educational-only responses, but no explicit differentiation in lending workflow

**Required Response Pattern**:
```python
if not user_context.is_authenticated:
    return """
    To start earning yield on your crypto, you'll need to:
    1. Connect a wallet (supports MetaMask, WalletConnect, etc.)
    2. Fund your wallet with the token you want to deposit

    Once connected, try: "deposit 1000 USDC into Morpho"
    """
```

### 5.2 Authenticated User Responses

**Current**: Full workflow with execute_data
**Gap**: No differentiation by experience level

**Required**:
- New users: Include explanations of DeFi concepts
- Experienced users: Skip explanations, show data only
- Power users: Allow advanced parameters (slippage, specific vault selection)

### 5.3 Premium User Responses

**Current**: Not differentiated
**Gap**: Premium features not highlighted

**Required**:
- Advanced analytics (historical APY, TVL trends)
- Priority execution queue
- Lower gas estimates (batch optimization)

### 5.4 Balance-Insufficient Responses

**Current**: Shows "buy crypto" recommendation
**Good Implementation**: Already context-aware

**Gap**: Doesn't suggest alternatives (smaller amount, different asset)

**Enhanced Response**:
```python
"""
Your USDC balance ($50) is less than the requested deposit ($1000).

Options:
1. Deposit your available balance: "deposit 50 USDC"
2. Buy more USDC: "buy 950 USDC"
3. Try a different asset: "deposit ETH" (Balance: $500)
"""
```

---

## 6. Revised Context Management Architecture

### 6.1 Enhanced UserContextService

**Additions Required**:

```python
@dataclass
class UserContextAware:
    # ... existing fields ...

    # NEW: Risk Profile (P0)
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    max_acceptable_health_factor: float = 1.5

    # NEW: Subscription Tier (P1)
    subscription_tier: str = "free"  # free, premium, enterprise

    # NEW: Token Balances (P0)
    # Populated on-demand for active workflows
    token_balances: dict[str, Decimal] = field(default_factory=dict)

    # NEW: Active Positions (P0)
    lending_positions: list[dict] = field(default_factory=list)
    current_health_factor: float | None = None
```

### 6.2 Context Injection Strategy

**Layer 1: Presentation Layer** (Router)
```python
# Get or create UserContextAware
context_aware = await user_context_service.get_context(chat_user_id)
if not context_aware:
    context_aware = await user_context_service.create_for_new_user(chat_user_id, ...)
```

**Layer 2: Application Layer** (Supervisor)
```python
# Inject full context
supervisor.set_context_aware(context_aware)
supervisor.set_user_context(
    user_id=str(user.id),
    wallet_address=context_aware.primary_wallet_address,
    portfolio_summary={
        "total_value_usd": float(context_aware.total_balance_usd),
        "token_balances": context_aware.token_balances,
        "health_factor": context_aware.current_health_factor,
    },
    preferences={
        "risk_tolerance": context_aware.risk_tolerance,
        "language": context_aware.detected_language,
    }
)
```

**Layer 3: Infrastructure Layer** (Workflow Agent)
```python
# Extract complete context
user_context = self._extract_user_context(conversation_context)

# Now available:
# - user_context.token_balances
# - user_context.risk_tolerance
# - user_context.current_health_factor
```

### 6.3 State Management Improvements

**1. Workflow State Versioning**
```python
@dataclass
class WorkflowState:
    version: int = 1  # For migration handling
    step: str = WorkflowStep.PARSE_REQUEST.value
    data: dict[str, Any] = field(default_factory=dict)
    # ... existing fields ...

    # NEW: Context snapshot
    context_snapshot: dict | None = None  # Frozen at workflow start

    # NEW: Timestamps
    started_at: datetime | None = None
    last_updated_at: datetime | None = None
```

**2. Redis Key Namespacing**
```python
# Current
f"conversation:{id}:messages"

# Improved
f"anvil:conv:{id}:messages"
f"anvil:conv:{id}:workflow:{workflow_name}"
f"anvil:conv:{id}:pending_tx:{action_id}"
```

**3. Explicit Cleanup**
```python
async def complete_workflow(
    conversation_id: ConversationId,
    workflow_name: str,
    result: str,  # "success" | "cancelled" | "error"
) -> None:
    # Clear workflow state
    await self._redis.delete(f"anvil:conv:{conversation_id}:workflow:{workflow_name}")

    # Clear pending transactions
    keys = await self._redis.keys(f"anvil:conv:{conversation_id}:pending_tx:*")
    if keys:
        await self._redis.delete(*keys)
```

### 6.4 Session Cleanup Mechanisms

**1. Timeout-based Cleanup** (Existing)
- 5-minute timeout for workflow flows
- 24-hour TTL for conversation messages

**2. Event-based Cleanup** (NEW - Required)
- On workflow completion
- On transaction execution (success or failure)
- On user logout
- On conversation deletion

**3. Scheduled Cleanup** (NEW - Required)
```python
# Celery task: cleanup_stale_workflows
# Run every 15 minutes
async def cleanup_stale_workflows():
    # Find workflows older than 30 minutes
    # Delete associated Redis keys
    pass
```

---

## 7. Implementation Priority

### P0 (Critical - Before Launch)
1. [ ] Add `token_balances` to workflow context
2. [ ] Add `risk_warnings` to execute_data
3. [ ] Add `health_factor_impact` calculation
4. [ ] Implement pending transaction Redis store
5. [ ] Add specific token balance validation

### P1 (High - Sprint 1)
1. [ ] Add `subscription_tier` propagation
2. [ ] Add gas estimation to execute_data
3. [ ] Implement context snapshot in WorkflowState
4. [ ] Add event-based cleanup

### P2 (Medium - Sprint 2)
1. [ ] Add `risk_tolerance` calculation
2. [ ] Add alternative protocol suggestions
3. [ ] Implement Redis key namespacing
4. [ ] Add scheduled cleanup task

### P3 (Nice to Have)
1. [ ] Advanced user experience differentiation
2. [ ] Historical APY trends in execute_data
3. [ ] Batch transaction optimization

---

## 8. Hexagonal Architecture Compliance

### Domain Layer (Context-Independent)
- `UserContextAware` entity - No external dependencies
- `WorkflowState` dataclass - Pure data structure
- Business rules for risk/tier calculation

### Application Layer (Context Service)
- `UserContextService` - Orchestrates context aggregation
- `ConversationStateManager` - Manages flow state
- Application services for context injection

### Infrastructure Layer (Persistence via Ports)
- `UserContextRepository` - PostgreSQL persistence
- `ContextStorageRedis` - Redis state storage
- `WalletBalancePort` - Balance fetching

### Presentation Layer (Context Injection)
- Router injects context into supervisor
- Response formatting based on context
- Error handling with context-aware messages

---

## Appendix A: File References

| Component | File Path |
|-----------|-----------|
| UserContextService | `src/app/application/chat/services/user_context_service.py` |
| UserContextAware | `src/app/domain/chat/entities/user_context_aware.py` |
| BaseWorkflowAgent | `src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py` |
| LendingWorkflowAgent | `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py` |
| AuthenticatedSupervisor | `src/app/domain/services/agent_squad/authenticated_supervisor.py` |
| ConversationStateManager | `src/app/application/chat/services/conversation_state_manager.py` |
| ContextStorageRedis | `src/app/infrastructure/adapters/agent_squad/context_storage_redis.py` |
| ConversationContext | `src/app/domain/value_objects/agent_squad/conversation_context.py` |
| UserContextRepository | `src/app/domain/chat/ports/user_context_repository.py` |
| LendingHandler | `src/app/application/chat/handlers/lending_handler.py` |

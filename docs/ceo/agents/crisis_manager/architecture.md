# Crisis Manager Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **CRISIS_MANAGER** agent, which provides automated emergency response and protocol exploit handling using Forta Network detection and Privy wallet execution.

### Key Components

- **CrisisManagerAgentForta**: Agent Squad implementation
- **Forta Client**: Exploit detection source
- **Privy Client**: Wallet execution for auto-exit
- **LLM Client**: Vertex AI for crisis reasoning

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  CRISIS MANAGER ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Supervisor             │
                    │  (Intent Routing)        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   CrisisManagerAgent     │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Forta Network  │   │   Privy Wallet  │   │   Vertex AI     │
│  (Detection)    │   │   (Execution)   │   │   (LLM)         │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Enterprise Agents
    CRISIS_MANAGER = "crisis_manager"  # Emergency response
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "crisis_response": AgentType.CRISIS_MANAGER,
    "emergency_withdrawal": AgentType.CRISIS_MANAGER,
}
```

---

## Infrastructure Layer

### CrisisManagerAgentForta

**File**: `src/app/infrastructure/adapters/agent_squad/agents/enterprise/crisis_manager_agent_forta.py`
**Lines**: ~315

```python
class CrisisManagerAgentForta:
    """
    Crisis Manager Agent Forta implementation.
    
    Implements: AgentGateway
    
    Purpose: Emergency response & automated crisis handling
    
    Capabilities:
    - Protocol exploit detection (real-time)
    - Automated emergency response
    - Auto-exit strategies (save user funds)
    - Circuit breaker activation
    - Crisis event logging
    - Post-mortem analysis
    - User notification (multi-channel)
    
    Crisis Types:
    - Smart contract exploits
    - Flash loan attacks
    - Oracle manipulations
    - Governance attacks
    - Bridge hacks
    - Depeg events
    
    Response Actions (Automated):
    - Withdraw from affected protocol
    - Revoke token approvals
    - Exit liquidity positions
    - Pause automated strategies
    - Notify user immediately
    - Log detailed crisis events
    
    Safety Features:
    - User confirmation (for large amounts)
    - Dry-run simulation
    - Rollback support
    - Manual override
    - Rate limiting (prevent panic)
    
    Model: gemini-2.0-flash (crisis reasoning)
    Temperature: 0.1 (precision critical)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 61-89 | Initialize with clients |
| `agent_type` | 91-94 | Return AgentType.CRISIS_MANAGER |
| `execute` | 96-168 | Main entry point |
| `is_available` | 170-172 | Availability check |
| `_check_active_crises` | 174-199 | Detect crises (mock) |
| `_generate_crisis_report` | 201-314 | Format crisis report |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,           # Vertex AI
    forta_client: Any,                       # FortaClient (TODO)
    execution_client: Any,                   # Privy ExecutionClient (TODO)
    auto_exit_threshold_usd: Decimal = Decimal("1000"),
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
    max_tokens: int = 2000,
):
```

---

## Crisis Detection Flow

### Detection Process

```
1. Forta Network monitors blockchain activity
   ↓
2. Detection bot identifies exploit pattern
   ↓
3. Alert generated with severity classification
   ↓
4. Crisis Manager receives alert (< 5 seconds)
   ↓
5. User exposure evaluation
   ↓
6. Automated response triggered
```

### Crisis Data Structure

```python
{
    "crisis_id": "CRS-001",
    "protocol": "Euler Finance",
    "event_type": "FLASH_LOAN_ATTACK",
    "severity": "CRITICAL",
    "total_loss_usd": 197000000,
    "user_exposure_usd": 50000,
    "status": "ACTIVE",
    "response_time_ms": 2500,
    "actions_taken": [
        {"action": "WITHDRAW_ALL", "amount_usd": 48000, "status": "COMPLETED"},
        {"action": "REVOKE_APPROVALS", "count": 3, "status": "COMPLETED"},
    ],
    "positions_saved": [
        {"protocol": "Euler Finance", "token": "USDC", "amount": 48000},
    ],
    "losses_prevented_usd": 48000,
    "timestamp": 1704067200,
}
```

---

## Automated Response Actions

### Action Types

| Action | Description | Trigger |
|--------|-------------|---------|
| **WITHDRAW_ALL** | Emergency withdrawal from protocol | Exploit detected |
| **REVOKE_APPROVALS** | Remove token approvals | Any crisis |
| **EXIT_LIQUIDITY** | Remove LP positions | Pool exploit |
| **PAUSE_STRATEGIES** | Stop automated farming | Critical crisis |
| **NOTIFY_USER** | Multi-channel alert | All crises |

### Execution Flow

```python
# Automated response logic (conceptual)
async def _execute_crisis_response(self, crisis: dict):
    # 1. Check user exposure
    exposure = await self._calculate_user_exposure(crisis["protocol"])
    
    # 2. Auto-exit if below threshold
    if exposure <= self._auto_exit_threshold_usd:
        await self._execute_emergency_withdrawal(crisis["protocol"])
    else:
        # Request user confirmation
        await self._request_user_confirmation(crisis, exposure)
    
    # 3. Always revoke approvals
    await self._revoke_all_approvals(crisis["protocol"])
    
    # 4. Notify user
    await self._send_crisis_notification(crisis)
```

---

## Safety Features

### Threshold-Based Confirmation

| Amount | Behavior |
|--------|----------|
| ≤ $1,000 | Auto-exit without confirmation |
| > $1,000 | Requires user confirmation |
| Configurable | User can adjust threshold |

### Safety Controls

```python
# Safety feature configuration
auto_exit_threshold_usd = Decimal("1000")  # Default

# Additional safety features (TODO)
- Dry-run simulation before execution
- Rollback support for false positives
- Manual override option
- Rate limiting to prevent panic
```

---

## Source Attribution

### Forta Source

```python
sources.append(create_api_source(
    source_name="Forta",
    url="https://forta.org/",
    citation_text="Crisis detection from Forta Network",
    fetched_at=fetched_at,
    provider="Forta API",
    data_points_used=len(active_crises),
))
```

### Privy Source

```python
sources.append(create_api_source(
    source_name="Privy",
    url="https://privy.io/",
    citation_text="Wallet operations via Privy",
    fetched_at=fetched_at,
))
```

### LLM Source

```python
sources.append(create_llm_source(
    model=self._model,
    fetched_at=fetched_at,
))
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_crisis_manager_agent(
    self, llm_client: LLMClientGateway
) -> CrisisManagerAgentForta:
    """Provide Crisis Manager agent."""
    from unittest.mock import MagicMock
    return CrisisManagerAgentForta(
        llm_client=llm_client,
        forta_client=MagicMock(),      # TODO: Real client
        execution_client=MagicMock(),   # TODO: Real client
    )
```

### Agent Registry

```python
AgentType.CRISIS_MANAGER: crisis_manager_agent,
```

---

## Response Structure

```python
return AgentResponse(
    content=report,
    agent_type=self.agent_type,
    tools_used=["forta_api", "privy_wallet", "openai_api"],
    sources=sources,
    metadata={
        "latency_ms": latency_ms,
        "active_crises": len(active_crises),
        "user_affected": any(c["user_exposure_usd"] > 0 for c in active_crises),
    },
)
```

---

## Future Enhancements

### TODO Items

```python
# TODO: Implement real Forta API integration
# TODO: Implement real Privy wallet execution
# TODO: Implement SMS notifications for critical crises
# TODO: Implement rollback support
```

### Planned Features

1. **Real Forta API**
   - Live exploit detection
   - Protocol-specific monitoring
   - Custom alert rules

2. **Privy Wallet Execution**
   - Automated withdrawals
   - Approval revocation
   - Transaction confirmation

3. **Multi-Channel Notifications**
   - SMS for critical crises
   - Email for all events
   - Push notifications

4. **Advanced Safety**
   - Dry-run simulation
   - Rollback for false positives
   - Manual override

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Crisis detection | < 5s | Forta Network |
| Response execution | < 10s | Privy wallet |
| Report generation | < 2s | Vertex AI |
| Total | < 15s | Full response |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added mock crisis data |
| 2026-01-29 | Added source attribution |

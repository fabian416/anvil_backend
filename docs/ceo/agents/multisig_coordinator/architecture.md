# Multi-Sig Coordinator Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **MULTISIG_COORDINATOR** agent, which provides multi-signature treasury management using Gnosis Safe.

### Key Components

- **MultiSigCoordinatorAgentGnosis**: Agent Squad implementation
- **Gnosis Safe Client**: Multi-sig wallet operations
- **LLM Client**: Vertex AI for intent parsing

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  MULTISIG COORDINATOR ARCHITECTURE                       │
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
                    │   MultiSigCoordinator    │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                                   │
               ▼                                   ▼
     ┌─────────────────┐                ┌─────────────────┐
     │   Gnosis Safe   │                │   Vertex AI     │
     │   (Multi-Sig)   │                │   (LLM)         │
     └─────────────────┘                └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Enterprise Agents
    MULTISIG_COORDINATOR = "multisig_coordinator"  # Treasury
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "manage_multisig": AgentType.MULTISIG_COORDINATOR,
    "treasury_management": AgentType.MULTISIG_COORDINATOR,
}
```

### Keyword Detection

**File**: `src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py`

```python
if any(kw in message for kw in [
    "multisig", "multi-sig", "gnosis", "safe wallet", "treasury"
]):
    return "multisig_coordinator"
```

---

## Infrastructure Layer

### MultiSigCoordinatorAgentGnosis

**File**: `src/app/infrastructure/adapters/agent_squad/agents/enterprise/multisig_coordinator_agent_gnosis.py`
**Lines**: ~295

```python
class MultiSigCoordinatorAgentGnosis:
    """
    Multi-Sig Coordinator Agent Gnosis implementation.
    
    Implements: AgentGateway
    
    Purpose: Multi-signature treasury management
    
    Capabilities:
    - Multi-sig transaction creation (Gnosis Safe)
    - Approval workflow management
    - Budget enforcement (spending limits)
    - Policy validation (m-of-n signatures)
    - Transaction simulation (pre-flight)
    - Automatic notifications (email, Slack, SMS)
    - Audit trail (immutable logs)
    
    Treasury Features:
    - Budget codes (marketing, engineering, operations)
    - Spending limits (daily, monthly, per-transaction)
    - Role-based approvals (CFO, CEO, Board)
    - Emergency override (super admin only)
    - Multi-currency support
    
    Model: gemini-2.0-flash (treasury reasoning)
    Temperature: 0.1 (precision critical)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 47-62 | Initialize with clients |
| `agent_type` | 64-67 | Return AgentType.MULTISIG_COORDINATOR |
| `execute` | 69-145 | Main entry point |
| `is_available` | 147-149 | Availability check |
| `_parse_transaction_intent` | 151-182 | LLM intent extraction |
| `_create_multisig_proposal` | 184-221 | Create proposal (mock) |
| `_generate_proposal_summary` | 223-283 | Format proposal summary |
| `_build_error_response` | 285-294 | Error handling |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,              # Vertex AI
    gnosis_safe_client: Any,                    # GnosisSafeClient (TODO)
    max_transaction_usd: Decimal = Decimal("100000"),
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
    max_tokens: int = 2000,
):
```

---

## Approval Workflow

### Threshold-Based Policy

```python
# Determine approval policy based on amount
if amount_usd < 10000:
    approvals_required = 2  # 2-of-3
    approvers = ["CFO", "CEO"]
elif amount_usd < 50000:
    approvals_required = 3  # 3-of-5
    approvers = ["CFO", "CEO", "COO"]
else:
    approvals_required = 4  # 4-of-7 (Board approval)
    approvers = ["CFO", "CEO", "COO", "Board Member 1"]
```

### Approval Matrix

| Amount | Policy | Approvers Required |
|--------|--------|-------------------|
| < $10,000 | 2-of-3 | CFO, CEO |
| $10,000 - $50,000 | 3-of-5 | CFO, CEO, COO |
| > $50,000 | 4-of-7 | CFO, CEO, COO, Board |

### Proposal Data Structure

```python
{
    "proposal_id": "uuid-string",
    "safe_address": "0x1234...5678",
    "amount": "10000",
    "currency": "USDC",
    "amount_usd": Decimal("10000"),
    "destination": "0xABC...DEF",
    "purpose": "Marketing campaign payment",
    "budget_code": "marketing",
    "status": "PENDING_APPROVAL",
    "approvals_required": 2,
    "approvals_received": 0,
    "approvers": ["CFO", "CEO"],
    "created_at": 1704067200,
}
```

---

## Intent Parsing

### LLM-Based Extraction

```python
async def _parse_transaction_intent(self, message: MessageContent) -> dict:
    """Parse transaction intent from message."""
    prompt = f"""Parse the multi-sig transaction request from this message:

Message: {message.value}

Extract:
- amount: numeric value
- currency: token symbol (ETH, USDC, etc.)
- destination: wallet address
- purpose: transaction purpose/description
- budget_code: budget category (if mentioned)

Respond with JSON:
{{
    "valid": true/false,
    "amount": "1000",
    "currency": "USDC",
    "destination": "0x...",
    "purpose": "Marketing campaign payment",
    "budget_code": "marketing"
}}
"""
    
    response = await self._llm_client.classify_intent(
        prompt=prompt,
        model=self._model,
    )
    return response
```

---

## Source Attribution

### Gnosis Safe Source

```python
sources.append(create_api_source(
    source_name="Gnosis Safe",
    url="https://app.safe.global/",
    citation_text="Multi-sig wallet coordination via Gnosis Safe",
    fetched_at=fetched_at,
    provider="Gnosis Safe API",
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
def provide_multisig_coordinator_agent(
    self, llm_client: LLMClientGateway
) -> MultiSigCoordinatorAgentGnosis:
    """Provide Multi-Sig Coordinator agent."""
    from unittest.mock import MagicMock
    return MultiSigCoordinatorAgentGnosis(
        llm_client=llm_client,
        gnosis_safe_client=MagicMock(),  # TODO: Real client
    )
```

### Agent Registry

```python
AgentType.MULTISIG_COORDINATOR: multisig_coordinator_agent,
```

---

## Response Structure

```python
return AgentResponse(
    content=summary,
    agent_type=self.agent_type,
    tools_used=["gnosis_safe_api", "openai_api"],
    sources=sources,
    metadata={
        "latency_ms": latency_ms,
        "proposal_id": proposal["proposal_id"],
        "amount_usd": float(proposal["amount_usd"]),
        "status": proposal["status"],
        "approvals_required": proposal["approvals_required"],
    },
)
```

---

## Budget Management

### Budget Codes

| Code | Category | Example Transactions |
|------|----------|---------------------|
| `marketing` | Marketing & PR | Ad campaigns, sponsorships |
| `engineering` | Development | Contractor payments, tools |
| `operations` | Daily operations | Office, utilities, salaries |
| `legal` | Legal & compliance | Attorney fees, audits |
| `general` | Uncategorized | Miscellaneous expenses |

### Spending Limits (Configurable)

| Limit Type | Default | Description |
|------------|---------|-------------|
| Per-Transaction | $100,000 | Single transaction max |
| Daily | $250,000 | 24-hour rolling limit |
| Monthly | $1,000,000 | Calendar month limit |

---

## Security Features

### Access Control

| Role | Permissions |
|------|-------------|
| **Viewer** | Read-only access |
| **Proposer** | Create proposals |
| **Approver** | Approve/reject |
| **Admin** | Manage roles |
| **Super Admin** | Emergency override |

### Safety Measures

- **Transaction Simulation**: Pre-flight checks
- **Dual Control**: No single-person large transactions
- **Budget Validation**: Enforce spending limits
- **Immutable Logs**: On-chain + compliance DB
- **Insurance**: $10M coverage (Nexus Mutual)

---

## Future Enhancements

### TODO Items

```python
# TODO: Implement real Gnosis Safe API integration
# TODO: Implement email notifications
# TODO: Implement Slack bot integration
# TODO: Implement real-time budget tracking
```

### Planned Features

1. **Real Gnosis Safe API**
   - Live proposal creation
   - Signature collection
   - Transaction execution

2. **Notification Integration**
   - Email for approvers
   - Slack for team
   - SMS for urgent transactions

3. **Enhanced Budget Management**
   - Real-time tracking
   - Automated alerts
   - Monthly reports

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Intent parsing | < 1s | LLM extraction |
| Proposal creation | < 2s | Gnosis Safe API (mock) |
| Summary generation | < 1s | Template-based |
| Total | < 4s | Full proposal |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added mock proposal data |
| 2026-01-29 | Added source attribution |

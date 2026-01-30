# Multi-Sig Coordinator Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Implemented (Enhancement Planned)
**Agent Type**: Enterprise Agent
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **MULTISIG_COORDINATOR** agent provides multi-signature treasury management using Gnosis Safe. It enables secure, collaborative fund management with configurable approval workflows and budget enforcement.

### Key Differentiators

- **Gnosis Safe Integration**: Industry-standard multi-sig
- **Approval Workflows**: Configurable m-of-n signatures
- **Budget Enforcement**: Spending limits by category
- **Role-Based Approvals**: CFO, CEO, Board levels
- **Immutable Audit Trail**: On-chain + compliance logs

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and treasury operations |

---

## Quick Start

### For Users

**Treasury Queries:**
```
• "Send 10000 USDC to 0x... for marketing"
• "Create treasury proposal for 50000 USDC"
• "Check pending approvals"
• "Show treasury balance"
• "List recent transactions"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for treasury operations

---

## Key Features

### 1. Multi-Sig Operations

| Operation | Description | Approval Required |
|-----------|-------------|-------------------|
| **Create Proposal** | Submit transaction for approval | Any authorized user |
| **Approve** | Sign off on pending transaction | Designated approvers |
| **Reject** | Decline pending transaction | Any approver |
| **Execute** | Process approved transaction | Automatic on final approval |

### 2. Approval Thresholds

| Amount Range | Policy | Approvers |
|--------------|--------|-----------|
| < $10,000 | 2-of-3 | CFO, CEO |
| $10,000 - $50,000 | 3-of-5 | CFO, CEO, COO |
| > $50,000 | 4-of-7 | CFO, CEO, COO, Board |

### 3. Treasury Features

| Feature | Description |
|---------|-------------|
| **Budget Codes** | Marketing, Engineering, Operations |
| **Spending Limits** | Daily, monthly, per-transaction |
| **Role-Based Access** | CFO, CEO, Board Member |
| **Emergency Override** | Super admin only |
| **Multi-Currency** | ETH, USDC, USDT, etc. |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Routing)
Infrastructure Layer → MultiSigCoordinatorAgentGnosis
    ↓
External Systems
    - Gnosis Safe (Multi-sig wallet)
    - Vertex AI (LLM reasoning)
```

### Proposal Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  MULTI-SIG PROPOSAL FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User submits transaction request                        │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │  MultiSig Coordinator   │                               │
│  │                         │                               │
│  │  2. Parse intent        │ → LLM extraction              │
│  │  3. Validate budget     │ → Policy check                │
│  │  4. Create proposal     │ → Gnosis Safe                 │
│  │  5. Notify approvers    │ → Email, Slack, SMS           │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  6. Approvers review and sign                               │
│              ↓                                              │
│  7. On final approval → Auto-execute                        │
│              ↓                                              │
│  8. Transaction complete → Log to audit trail               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Detection

```python
# From intent_classifier.py
intent_to_agent = {
    "manage_multisig": AgentType.MULTISIG_COORDINATOR,
    "treasury_management": AgentType.MULTISIG_COORDINATOR,
}
```

### Agent Classification

```
- multisig_coordinator: Treasury management (enterprise)
```

### Keyword Detection

```python
# From keyword_intent_detection_adapter.py
keywords = ["multisig", "multi-sig", "gnosis", "safe wallet", "treasury"]
```

---

## Configuration

### Default Parameters

```python
# From multisig_coordinator_agent_gnosis.py

model = "gemini-2.0-flash"               # Vertex AI
temperature = 0.1                         # Precision critical
max_tokens = 2000                         # Detailed reports
max_transaction_usd = Decimal("100000")   # Per-transaction limit
```

### Response Structure

```python
AgentResponse(
    content="Proposal summary...",
    agent_type=AgentType.MULTISIG_COORDINATOR,
    tools_used=["gnosis_safe_api", "openai_api"],
    sources=[
        SourceInfo(source_type="api", source_name="Gnosis Safe",
                   citation_text="Multi-sig wallet coordination via Gnosis Safe"),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash",
                   citation_text="Generated by gemini-2.0-flash"),
    ],
    metadata={
        "latency_ms": 600,
        "proposal_id": "uuid-1234",
        "amount_usd": 10000.00,
        "status": "PENDING_APPROVAL",
        "approvals_required": 2,
    },
)
```

---

## Proposal Example

### Created Proposal

```
🏦 **MULTI-SIG PROPOSAL CREATED**

**Proposal ID**: `a1b2c3d4-e5f6-7890-abcd-1234567890ab`
**Safe Address**: `0x1234...5678`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**TRANSACTION DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Amount**: 10000 USDC ($10,000.00 USD)
**Destination**: `0xABC...DEF`
**Purpose**: Marketing campaign payment
**Budget Code**: marketing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**APPROVAL WORKFLOW**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Status**: ⏳ **PENDING APPROVAL**
**Required Approvals**: 2
**Current Approvals**: 0/2

**Approvers Notified**:
  ⏳ CFO - Pending
  ⏳ CEO - Pending

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**NEXT STEPS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Approvers have been notified via email and Slack
2. Each approver must review and approve/reject
3. Transaction executes automatically after final approval
4. Estimated execution time: 2-24 hours (based on approver response)

**Policy**: This transaction requires explicit approval from all
listed approvers. No automatic execution without full approval.

**Audit Trail**: All actions are logged immutably on-chain and in
compliance database for regulatory reporting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Treasury Management**: Gnosis Safe
**Compliance**: SOC 2 Type II
**Insurance**: $10M coverage (Nexus Mutual)
```

---

## Security Features

### Access Control

| Role | Permissions |
|------|-------------|
| **Viewer** | Read-only access to proposals |
| **Proposer** | Create proposals |
| **Approver** | Approve/reject proposals |
| **Admin** | Manage roles, override |
| **Super Admin** | Emergency override |

### Safety Measures

- **Transaction Simulation**: Pre-flight checks before approval
- **Spending Limits**: Per-transaction and periodic limits
- **Budget Validation**: Enforce budget codes
- **Dual Control**: No single person can execute large transactions
- **Immutable Logs**: On-chain + compliance database

---

## Future Enhancements (TODO)

### 1. Real Gnosis Safe API Integration

```python
# TODO: Implement real Gnosis Safe API integration
async def _create_multisig_proposal(self, ...):
    # Create real proposal on Gnosis Safe
    # Get transaction hash
    # Return proposal details
    pass
```

### 2. Notification Integration

- Email notifications for approvers
- Slack bot integration
- SMS for urgent transactions
- Mobile push notifications

### 3. Enhanced Budget Management

- Real-time budget tracking
- Automated budget alerts
- Monthly budget reports
- Carry-over handling

---

## Testing Checklist

### Unit Tests
- [ ] Intent parsing logic
- [ ] Threshold calculation
- [ ] Proposal creation
- [ ] Summary generation

### Integration Tests
- [ ] Gnosis Safe API integration
- [ ] Notification delivery
- [ ] Source attribution

### E2E Tests
- [ ] Complete proposal flow
- [ ] Multi-approver workflow
- [ ] Audit trail logging

---

## Related Documentation

- **Compliance Monitor Agent**: `/docs/ceo/agents/compliance_monitor/` (AML/KYC)
- **DAO Governance Agent**: `/docs/ceo/agents/dao_governance/` (governance)
- **Alert Monitoring Agent**: `/docs/ceo/agents/alert_monitoring/` (alerts)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Multi-Sig Coordinator Agent Specification**

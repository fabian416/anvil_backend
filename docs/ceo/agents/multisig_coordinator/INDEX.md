# Multi-Sig Coordinator Agent - Complete Index

> **Project:** Anvil DeFi Chat - Treasury Management
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Implemented (Enhancement Planned)
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **MULTISIG_COORDINATOR** agent, Anvil's system for multi-signature treasury management using Gnosis Safe.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and treasury operations |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Gnosis Safe integration
- Approval workflow logic
- Budget enforcement

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Proposal summary generation

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Treasury queries and operations:

**Key Contents:**
- Proposal creation
- Approval workflows
- Budget management

---

## 🎯 Implementation Status

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Intent Parsing | ✅ | LLM-based extraction |
| Proposal Creation | ✅ | Mock Gnosis Safe |
| Threshold Logic | ✅ | Amount-based approvers |
| Source Attribution | ✅ | Gnosis Safe + LLM |

### Planned Enhancements (TODO)

| Feature | Status | Description |
|---------|--------|-------------|
| Real Gnosis Safe API | 🔲 | Live proposals |
| Email Notifications | 🔲 | Approver alerts |
| Slack Integration | 🔲 | Team notifications |
| Budget Tracking | 🔲 | Real-time limits |

---

## 📊 Approval Reference

### Amount Thresholds

| Amount | Policy | Approvers |
|--------|--------|-----------|
| < $10K | 2-of-3 | CFO, CEO |
| $10K-$50K | 3-of-5 | CFO, CEO, COO |
| > $50K | 4-of-7 | CFO, CEO, COO, Board |

### Proposal Statuses

| Status | Description | Next Step |
|--------|-------------|-----------|
| **PENDING_APPROVAL** | Awaiting signatures | Approvers review |
| **PARTIALLY_APPROVED** | Some signatures received | More approvals needed |
| **APPROVED** | All signatures received | Auto-execute |
| **REJECTED** | Declined by approver | Proposal cancelled |
| **EXECUTED** | Transaction complete | Archived |

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI for intent parsing
- **Gnosis Safe Client**: Multi-sig operations (TODO)

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/enterprise/multisig_coordinator_agent_gnosis.py`
- `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_multisig_coordinator_agent)

**Domain Layer:**
- `src/app/domain/enums/agent_type.py` (AgentType.MULTISIG_COORDINATOR)

**Intent Classification:**
- `src/app/domain/services/agent_squad/intent_classifier.py`
- `src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py`

---

## 🏦 Treasury Operations

### Complete Flow

```
1. User submits transaction request
   ↓
2. LLM parses intent (amount, destination, purpose)
   ↓
3. Validate against budget policy
   ↓
4. Determine approval threshold
   ↓
5. Create Gnosis Safe proposal
   ↓
6. Notify required approvers
   ↓
7. Collect signatures (m-of-n)
   ↓
8. Execute on final approval
   ↓
9. Log to audit trail
```

### Budget Codes

| Code | Category | Monthly Limit |
|------|----------|---------------|
| `marketing` | Marketing & PR | $100,000 |
| `engineering` | Development | $200,000 |
| `operations` | Daily operations | $150,000 |
| `legal` | Legal & compliance | $50,000 |
| `general` | Uncategorized | $25,000 |

---

## 📝 Document Maintenance

**Last Updated:** 2026-01-29
**Review Frequency:** Monthly

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**For questions or clarifications, refer to the README.md in this directory.**

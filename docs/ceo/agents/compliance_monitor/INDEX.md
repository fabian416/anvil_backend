# Compliance Monitor Agent - Complete Index

> **Project:** Anvil DeFi Chat - AML/KYC Compliance
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Implemented (Enhancement Planned)
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **COMPLIANCE_MONITOR** agent, Anvil's system for AML/KYC compliance and regulatory screening using Chainalysis.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and compliance checks |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Chainalysis integration
- OFAC sanctions checking
- Risk scoring logic

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Screening report generation

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Compliance queries and screening types:

**Key Contents:**
- Wallet screening queries
- Compliance check patterns
- Risk assessment examples

---

## 🎯 Implementation Status

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Address Extraction | ✅ | LLM-based extraction |
| Risk Scoring | ✅ | 0-100 scale |
| Report Generation | ✅ | Detailed reports |
| Source Attribution | ✅ | Chainalysis + OFAC + LLM |

### Planned Enhancements (TODO)

| Feature | Status | Description |
|---------|--------|-------------|
| Real Chainalysis API | 🔲 | Live screening |
| Transaction Monitoring | 🔲 | Continuous monitoring |
| Enhanced PEP Database | 🔲 | Real-time updates |
| Audit Trail Logging | 🔲 | 7-year storage |

---

## 📊 Risk Score Reference

### Score Thresholds

| Score | Level | Decision |
|-------|-------|----------|
| 0-29 | 🟢 LOW | APPROVED |
| 30-59 | 🟡 MEDIUM | APPROVED (monitored) |
| 60-79 | 🟠 HIGH | MANUAL_REVIEW |
| 80-100 | 🔴 CRITICAL | BLOCKED |

### Compliance Checks

| Check | Description | Weight |
|-------|-------------|--------|
| OFAC Sanctions | SDN list verification | High |
| PEP Check | Political exposure | Medium |
| Mixer Exposure | Tornado Cash, etc. | High |
| High-Risk Sources | Known bad actors | High |

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI for address extraction
- **Chainalysis Client**: Wallet screening (TODO)
- **OFAC API**: Sanctions verification

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/enterprise/compliance_monitor_agent_chainalysis.py`
- `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_compliance_monitor_agent)

**Domain Layer:**
- `src/app/domain/enums/agent_type.py` (AgentType.COMPLIANCE_MONITOR)
- `src/app/domain/value_objects/wallet_address.py`

**Intent Classification:**
- `src/app/domain/services/agent_squad/intent_classifier.py`
- `src/app/infrastructure/adapters/chat/keyword_intent_detection_adapter.py`

---

## 🔍 Screening Process

### Complete Flow

```
1. User submits wallet address for screening
   ↓
2. LLM extracts Ethereum address from message
   ↓
3. Chainalysis API screens wallet
   ↓
4. OFAC sanctions list check
   ↓
5. PEP database check
   ↓
6. Calculate risk score (0-100)
   ↓
7. Make decision: APPROVED / REVIEW / BLOCKED
   ↓
8. Generate compliance report
   ↓
9. Log to compliance_screening_logs
```

### Decision Matrix

| Risk Score | OFAC Status | Decision |
|------------|-------------|----------|
| < 60 | Clear | APPROVED |
| 60-79 | Clear | MANUAL_REVIEW |
| ≥ 80 | Clear | BLOCKED |
| Any | Sanctioned | BLOCKED |

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

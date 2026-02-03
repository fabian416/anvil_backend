# Tax Optimizer Agent - Complete Index

> **Project:** Anvil DeFi Chat - Tax Optimization
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Implemented (Enhancement Planned)
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **TAX_OPTIMIZER** agent, Anvil's system for tax-loss harvesting, capital gains analysis, and tax optimization strategies.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and tax strategies |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- LLM-based tax reasoning
- System prompt design
- Source attribution

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Future enhancement TODOs

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Tax optimization queries and strategies:

**Key Contents:**
- Capital gains queries
- Tax-loss harvesting examples
- Cost basis selection
- Wash sale warnings

---

## 🎯 Implementation Status

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| LLM Tax Reasoning | ✅ | Vertex AI analysis |
| Capital Gains Analysis | ✅ | ST/LT calculation |
| Tax-Loss Harvesting | ✅ | Opportunity identification |
| Wash Sale Compliance | ✅ | 30-day rule warnings |
| Cost Basis Methods | ✅ | FIFO/LIFO/HIFO |
| Source Attribution | ✅ | Database + LLM sources |

### Planned Enhancements (TODO)

| Feature | Status | Description |
|---------|--------|-------------|
| Transaction History | 🔲 | Real transaction data |
| Real-Time Calculation | 🔲 | Live gain/loss |
| Tax Report Generation | 🔲 | Form 8949, Schedule D |
| Multi-Jurisdiction | 🔲 | EU, UK, other |

---

## 📊 Tax Concepts Reference

### Capital Gains Rates (US)

| Type | Holding Period | Tax Rate |
|------|----------------|----------|
| Short-term | ≤ 365 days | 10% - 37% |
| Long-term | > 365 days | 0%, 15%, 20% |

### Cost Basis Methods

| Method | Description |
|--------|-------------|
| FIFO | First In, First Out |
| LIFO | Last In, First Out |
| HIFO | Highest In, First Out |

### Key Rules

- **Wash Sale**: 30-day window before/after sale
- **Long-term threshold**: > 365 days holding
- **Loss carryover**: Unused losses carry forward

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI for tax reasoning
- **Database**: Transaction history source

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/tax_optimizer_agent.py`
- `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_tax_optimizer_agent)

**Domain Layer:**
- `src/app/domain/enums/agent_type.py` (AgentType.TAX_OPTIMIZER)

**Intent Classification:**
- `src/app/domain/services/agent_squad/intent_classifier.py`

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

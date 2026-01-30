# Crisis Manager Agent - Complete Index

> **Project:** Anvil DeFi Chat - Emergency Response
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Implemented (Enhancement Planned)
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **CRISIS_MANAGER** agent, Anvil's system for automated emergency response and protocol exploit handling.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and crisis types |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Forta Network integration
- Privy wallet execution
- Auto-exit logic

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Crisis report generation

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Crisis queries and response actions:

**Key Contents:**
- Crisis status queries
- Emergency withdrawal
- Auto-exit configuration
- Historical lookups

---

## 🎯 Implementation Status

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Crisis Detection | 🔲 Mock | Forta API pending |
| Report Generation | ✅ | Detailed crisis reports |
| Action Logging | ✅ | Track automated actions |
| Source Attribution | ✅ | Forta + Privy + LLM |

### Planned Enhancements (TODO)

| Feature | Status | Description |
|---------|--------|-------------|
| Real Forta API | 🔲 | Live exploit detection |
| Privy Execution | 🔲 | Automated withdrawals |
| SMS Notifications | 🔲 | Critical alert SMS |
| Rollback Support | 🔲 | Undo false positives |

---

## 📊 Crisis Reference

### Severity Levels

| Severity | Icon | Response |
|----------|------|----------|
| Critical | 🔴 | Immediate auto-exit |
| High | 🟠 | User notification + recommendation |
| Medium | 🟡 | Monitoring + alert |
| Low | 🟢 | Logged for review |

### Crisis Types

| Type | Severity | Example |
|------|----------|---------|
| Flash Loan Attack | Critical | Euler exploit |
| Reentrancy | Critical | DAO hack |
| Oracle Manipulation | Critical | bZx attack |
| Bridge Hack | Critical | Ronin bridge |
| Depeg Event | High | UST collapse |

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI for crisis reasoning
- **Forta Client**: Exploit detection (TODO)
- **Privy Client**: Wallet execution (TODO)

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/enterprise/crisis_manager_agent_forta.py`
- `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_crisis_manager_agent)

**Domain Layer:**
- `src/app/domain/enums/agent_type.py` (AgentType.CRISIS_MANAGER)

**Intent Classification:**
- `src/app/domain/services/agent_squad/intent_classifier.py`

---

## 🚨 Crisis Response Process

### Automated Response Flow

```
1. Forta detects exploit (< 5 seconds)
   ↓
2. Crisis Manager evaluates user exposure
   ↓
3. Auto-exit if exposure > threshold
   ↓
4. Revoke token approvals
   ↓
5. Notify user via all channels
   ↓
6. Generate detailed crisis report
   ↓
7. Funds secured in user's wallet
```

### Safety Thresholds

| Amount | Behavior |
|--------|----------|
| < $1,000 | Auto-exit (no confirmation) |
| ≥ $1,000 | Requires user confirmation |
| Any | Revoke approvals (immediate) |

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

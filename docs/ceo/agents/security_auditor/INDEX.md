# Security Auditor Agent - Complete Index

> **Project:** Anvil DeFi Chat - Smart Contract Security
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Implemented (Enhancement Planned)
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **SECURITY_AUDITOR** agent, Anvil's system for smart contract security analysis and vulnerability detection.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and vulnerabilities |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- LLM-based security reasoning
- System prompt design
- Vulnerability classification

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

Security analysis queries and patterns:

**Key Contents:**
- Protocol safety checks
- Contract address analysis
- Vulnerability explanations
- Audit status queries

---

## 🎯 Implementation Status

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| LLM Security Reasoning | ✅ | Vertex AI analysis |
| Vulnerability Detection | ✅ | Pattern recognition |
| Security Scoring | ✅ | 0-100 rating |
| Source Attribution | ✅ | LLM sources |

### Planned Enhancements (TODO)

| Feature | Status | Description |
|---------|--------|-------------|
| Slither Integration | 🔲 | Static analysis |
| Mythril Integration | 🔲 | Symbolic execution |
| Audit Database | 🔲 | Third-party audits |
| Bytecode Analysis | 🔲 | On-chain verification |

---

## 📊 Vulnerability Reference

### Severity Classifications

| Severity | Score Impact | Examples |
|----------|--------------|----------|
| Critical | -30 to -50 | Reentrancy, Oracle manipulation |
| High | -20 to -30 | Integer overflow, Access control |
| Medium | -10 to -20 | Front-running, DOS |
| Low | -5 to -10 | Gas optimization |

### Common Vulnerabilities

| Type | Category | Detection |
|------|----------|-----------|
| Reentrancy | Critical | Call before state update |
| Access Control | Critical | Missing permission checks |
| Oracle Manipulation | Critical | Price feed exploitation |
| Integer Overflow | High | Unchecked arithmetic |
| Front-running | Medium | MEV susceptibility |

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI for security reasoning

### Future Dependencies

- **Slither**: Static analysis tool
- **Mythril**: Symbolic execution
- **Audit Database**: Trail of Bits, OpenZeppelin reports

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/security_auditor_agent_slither.py`
- `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_security_auditor_agent)

**Domain Layer:**
- `src/app/domain/enums/agent_type.py` (AgentType.SECURITY_AUDITOR)

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

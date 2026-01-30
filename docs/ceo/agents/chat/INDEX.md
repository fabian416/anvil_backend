# Chat Agent - Complete Index

> **Project:** Anvil DeFi Chat - Foundational Conversation
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **CHAT** agent, Anvil's foundational conversational system handling greetings, creative writing, off-topic queries, and response aggregation.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Conversation patterns and flows |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Greeting detection logic
- Off-topic handling
- Response aggregation
- Restricted feature detection

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Message building
- System prompts

---

### 3. [shortcuts.md](./shortcuts.md) - Conversation Patterns
**Priority:** High | **User Interface**

Conversation flows and patterns:

**Key Contents:**
- Greeting patterns
- Creative writing examples
- Off-topic handling
- Aggregation patterns

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Greeting Handling | ✅ | Brief, warm responses |
| Creative Writing | ✅ | Poems, stories about crypto |
| Off-Topic Handling | ✅ | Polite decline and redirect |
| Response Aggregation | ✅ | Multi-agent combination |
| Restricted Features | ✅ | Auth prompts for guests |
| Fallback Agent | ✅ | Default when no specialist |
| Multi-Language | ✅ | EN, ES, PT greetings |
| Source Attribution | ✅ | LLM source tracking |

### Message Types

| Type | Handling |
|------|----------|
| Greeting | Brief response, no history |
| Creative | Full LLM generation |
| Off-topic | Supervisor instruction |
| Aggregation | Higher token limit |
| Restricted | Custom auth message |

---

## 📊 Key Metrics

### Performance Targets

- **Standard response**: < 1000ms
- **Aggregation**: < 2000ms (more content)
- **Greeting**: < 500ms (simpler)

### Token Limits

- **Standard**: 1000 tokens
- **Aggregation**: 3000 tokens (3x)

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI / DeepInfra
- **Supervisor**: Routing logic
- **All Agents**: For aggregation

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/chat_agent.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_chat_agent)

**Supervisor Routing:**
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/services/agent_squad/guest_supervisor.py`
- `src/app/domain/services/agent_squad/supervisor_coordinator.py`

---

## 🚀 Conversation Journey

### Greeting Flow

```
1. User says: "hi"
   → Supervisor routes to chat

2. ChatAgent detects greeting
   → is_greeting = True

3. Use greeting prompt
   → Brief, conversational

4. NO history used
   → Prevents context bleeding

5. Return brief response
   → "Hi! How can I help you today?"
```

### Off-Topic Flow

```
1. User says: "make a cake"
   → Supervisor routes to chat with instruction

2. ChatAgent receives instruction
   → [SYSTEM INSTRUCTION: Decline off-topic politely]

3. Build instruction messages
   → Extract instruction, original message

4. Generate polite decline
   → Redirect to DeFi topics
```

### Aggregation Flow

```
1. User says: "what is DeFi? also check gas prices"
   → Supervisor routes to knowledge + gas_optimizer

2. Both agents complete
   → knowledge: DeFi explanation
   → gas_optimizer: Current prices

3. Chat agent receives aggregation task
   → Message contains both agent responses

4. Combine responses
   → Deduplicate, preserve data, single disclaimer

5. Return coherent summary
   → All info, well-structured
```

---

## 🔑 Critical Rules

### Greeting Rules

```python
# CRITICAL: Brief responses only

# GOOD:
"Hi! How can I help you today?"
"Hello! What would you like to know?"

# BAD (too verbose):
"Hello! Welcome to Anvil! Anvil is a decentralized finance platform..."
"Hi! Anvil is a comprehensive DeFi platform that allows users to..."
```

### Off-Topic Rules

```python
# Politely decline, redirect to DeFi

# Response pattern:
"I'm specialized in DeFi and crypto assistance. 
I can't help with [topic], but I can help you with 
swaps, staking, lending, and other DeFi operations."
```

### Aggregation Rules

```python
# CRITICAL: Preserve real-time data

# MUST include:
- All APY values from DeFiLlama
- All prices from CoinGecko/Hunter AI
- All specific protocol names
- All unique data points

# Filter out:
- Repeated disclaimers
- Authentication prompts (unless asked)
- Duplicate general information
```

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

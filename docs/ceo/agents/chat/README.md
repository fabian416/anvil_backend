# Chat Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Foundational)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **CHAT** agent is Anvil's foundational conversational agent, handling greetings, general conversation, creative writing about crypto, off-topic query handling, multi-agent response aggregation, and serving as the fallback agent when no specialized agent is appropriate.

### Key Differentiators

- **Fallback Agent**: Default when no specialist matches
- **Greetings Handler**: Warm, brief responses to "hi", "hello", etc.
- **Creative Writing**: Poems, stories, analogies about crypto topics
- **Off-Topic Handler**: Politely declines non-crypto queries
- **Response Aggregator**: Combines multi-agent responses into coherent summaries
- **Auth Prompts**: Restricted feature detection for guest users

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and conversation flows |

---

## Quick Start

### For Users

**Greetings:**
```
• "Hi" → "Hi! How can I help you today?"
• "Hello" → "Hello! What would you like to know?"
• "Hola" → "¡Hola! ¿En qué puedo ayudarte?"
```

**Creative Requests:**
```
• "Write a poem about gas fees"
• "Tell me a story about Bitcoin"
• "Explain DeFi like I'm 5"
```

**Off-Topic (Declined):**
```
• "How to make a cake" → Politely redirects to DeFi
• "Best GPU for gaming" → Specialized in crypto only
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for conversation patterns

---

## Key Features

### 1. Greeting Handling

| Input | Response Style |
|-------|----------------|
| "hi", "hello", "hey" | Brief, warm greeting |
| "hola", "buenos dias" | Spanish greeting |
| "oi", "olá" | Portuguese greeting |
| "how are you" | Friendly, short response |

**Critical Rule**: Greetings get brief responses (1-2 sentences), NO platform descriptions.

### 2. Creative Writing

| Request | Capability |
|---------|------------|
| "Write a poem about gas fees" | ✅ Full creative writing |
| "Story about Bitcoin" | ✅ Narrative creation |
| "Explain DeFi simply" | ✅ Analogies and metaphors |
| "Poem about current BTC price" | ✅ Incorporates real data |

### 3. Off-Topic Handling

| Query Type | Response |
|------------|----------|
| Cooking recipes | "I'm specialized in DeFi..." |
| General knowledge | Politely redirect to crypto |
| Entertainment | Cannot help, suggest DeFi topics |
| Prompt injection | Block and redirect |

### 4. Response Aggregation

When multiple agents provide responses, CHAT combines them:

- **Preserve real-time data**: APY values, TVL, prices
- **Deduplicate**: Remove repeated disclaimers
- **Filter auth prompts**: Don't show login prompts for info queries
- **Single disclaimer**: One "not financial advice" at end
- **Complete summary**: Include ALL specific data points

### 5. Restricted Feature Detection

For guest users asking about authenticated features:

| Feature | Response |
|---------|----------|
| "my portfolio" | Custom registration message |
| "my balance" | Wallet access required |
| "my transactions" | Account required |
| "buy crypto" | Account + verification required |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → ChatAgent
    ↓ (LLM Client)
External Systems
    - Vertex AI (gemini-2.0-flash)
```

### Chat Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      CHAT AGENT FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Message: "hi"                                         │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: greeting       │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │     ChatAgent           │                               │
│  │                         │                               │
│  │  1. Detect greeting     │ → Yes                         │
│  │  2. Use greeting prompt │ → Brief, warm                 │
│  │  3. NO history          │ → Prevent context bleed       │
│  │  4. Return brief        │ → "Hi! How can I help?"       │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  Response: "Hi! How can I help you today?"                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Classification

```python
# From intent_classifier.py

INTENT_AGENT_MAP = {
    "general_chat": AgentType.CHAT,
}

# Fallback default
fallback_agent = AgentType.CHAT
```

### Routing Examples

```python
# Greetings
"hi" → chat (single task: "Greet warmly")
"hello" → chat (single task: "Greet warmly")
"hola" → chat (single task: "Greet warmly in Spanish")

# Creative requests
"write a poem about gas fees" → chat (creative writing)
"poem about gas + current price" → gas_optimizer → chat (sequential)

# Off-topic
"make a cake" → chat (task: "Decline off-topic politely")
"best GPU for gaming" → chat (task: "Decline off-topic politely")

# Multi-agent aggregation
"what is DeFi? also check gas prices" → knowledge + gas_optimizer + chat (aggregator)
```

---

## Example Conversations

### Greeting

```
User: "hi"

Agent: "Hi! How can I help you today?"
```

### Creative Writing

```
User: "Write a poem about gas fees"

Agent:
Oh gas fees, how you rise and fall,
Like crypto markets, serving us all.
When demand is high, you spike with glee,
Making transactions cost a hefty fee.

But wait till night when networks rest,
That's when gas prices are at their best.
Layer 2 solutions, Arbitrum and Base,
Offer cheaper paths at lightning pace.

So hodler, trader, DeFi fan,
Optimize your gas whenever you can!
```

### Off-Topic Handling

```
User: "How to make a cake"

Agent: "I'm specialized in DeFi and crypto assistance. I can't help with 
cooking recipes, but I can help you with swaps, lending, and other DeFi 
operations. What would you like to know about DeFi?"
```

### Response Aggregation

```
User: "what type of swaps can I do? also check BTC price"

[Hunter AI response]: "BTC: $92,506..."
[Knowledge response]: "Anvil supports swaps via Hyperliquid Spot..."

Agent (aggregated):
## Swap Types Available on Anvil

Anvil supports token swaps via **Hyperliquid Spot** for meme tokens:
- Supported: PURR, TRUMP, PEPE, HFUN, MOG, and 50+ tokens
- Zero gas fees, 0.02% trading fee
- Sub-second execution

## Current BTC Price
**Bitcoin (BTC)**: $92,506

*This is not financial advice.*
```

---

## Configuration

### Default Parameters

```python
# From chat_agent.py

model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.7           # Balanced creativity
max_tokens = 1000           # Standard (3000 for aggregation)
```

### Response Structure

```python
AgentResponse(
    content="Hi! How can I help you today?",
    agent_type=AgentType.CHAT,
    tools_used=[],  # No external tools
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
    ],
    metadata={
        "tokens_used": 50,
        "latency_ms": 500,
        "model": "gemini-2.0-flash",
        "provider": "vertex_ai",
    },
)
```

---

## Use Cases

### Primary Use Cases

1. **Greetings**: Warm, brief welcome
2. **Creative writing**: Poems, stories about crypto
3. **Off-topic handling**: Politely redirect non-crypto queries
4. **Fallback**: When no specialized agent matches
5. **Aggregation**: Combine multi-agent responses
6. **Auth prompts**: Restricted feature detection for guests

### Special Behaviors

| Scenario | Behavior |
|----------|----------|
| Greeting | Brief response, NO history used |
| Aggregation | Higher token limit (3000) |
| Off-topic | Follow supervisor instruction exactly |
| Restricted feature | Use custom auth messages |

---

## Testing Checklist

### Unit Tests
- [ ] Greeting detection
- [ ] Off-topic handling
- [ ] Aggregation logic
- [ ] Restricted feature detection
- [ ] Message building

### Integration Tests
- [ ] LLM response generation
- [ ] Source attribution
- [ ] Multi-language greetings

### E2E Tests
- [ ] Complete conversation flow
- [ ] Multi-agent aggregation
- [ ] Guest auth prompts

---

## Related Documentation

- **Knowledge Agent**: `/docs/ceo/agents/knowledge/` (educational content)
- **Guest Auth**: `/docs/ceo/agents/guest_auth/` (auth prompts for guests)
- **Supervisor**: Routing logic in `authenticated_supervisor.py`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added greeting handling |
| 1.0 | 2026-01-29 | Added off-topic handling |
| 1.0 | 2026-01-29 | Added response aggregation |

---

**End of Chat Agent Specification**

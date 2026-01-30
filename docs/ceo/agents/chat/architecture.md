# Chat Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **CHAT** agent, Anvil's foundational conversational system handling greetings, creative writing, off-topic queries, response aggregation, and serving as the fallback agent.

### Key Components

- **ChatAgent**: Agent Squad implementation
- **Greeting Detection**: Brief, warm responses
- **Off-Topic Handling**: Polite decline and redirect
- **Response Aggregation**: Multi-agent combination
- **Restricted Feature Detection**: Auth prompts for guests

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CHAT AGENT ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Supervisor Coordinator  │
                    │  (Routing Logic)         │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      ChatAgent           │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      Vertex AI LLM       │
                    │  (gemini-2.0-flash)      │
                    └──────────────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    CHAT = "chat"  # General conversation, fallback
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
INTENT_AGENT_MAP = {
    "general_chat": AgentType.CHAT,
}

# Fallback default
fallback_agent = AgentType.CHAT
```

---

## Infrastructure Layer

### ChatAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/chat_agent.py`
**Lines**: ~575

```python
class ChatAgent:
    """
    Chat Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: General conversation, fallback agent
    
    Capabilities:
    - Answer general questions
    - Provide DeFi information
    - Guide users to specialist agents
    - Maintain friendly, helpful tone
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.7 (balanced creativity)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 60-173 | Main entry point |
| `is_available()` | 175-178 | Availability check |
| `_build_messages()` | 180-272 | Build LLM messages |
| `_is_restricted_feature_query()` | 274-291 | Detect auth-required features |
| `_detect_restricted_feature()` | 293-311 | Identify specific feature |
| `_get_custom_message()` | 313-339 | Get auth prompt message |
| `_build_instruction_messages()` | 341-372 | Handle off-topic instructions |
| `_get_greeting_prompt()` | 374-403 | Brief greeting prompt |
| `_get_system_prompt()` | 405-574 | Full system prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    model: str = "gemini-2.0-flash",
    temperature: float = 0.7,           # Balanced creativity
    max_tokens: int = 1000,
):
```

---

## Greeting Detection Logic

### Detection Patterns

```python
# From _build_messages()

is_greeting = any([
    message_lower in ["hi", "hello", "hey", "hola", "holi", "hey there"],
    message_lower.startswith(("hi ", "hello ", "hey ", "hola ")),
    "how are you" in message_lower,
    "good morning" in message_lower or "good afternoon" in message_lower,
])
```

### Greeting Prompt

```python
def _get_greeting_prompt(self) -> str:
    return """You are a friendly DeFi assistant for Anvil. 

When users greet you (hi, hello, hola, hey, etc.):
- Respond naturally and conversationally with a BRIEF greeting ONLY
- DO NOT provide platform descriptions, feature lists, or explanations
- Keep it to 1-2 sentences maximum - JUST a greeting and offer to help
- Be personable, warm, and brief

Example GOOD responses:
- "Hi! How can I help you today?"
- "Hello! What would you like to know?"

Example BAD responses:
- "Hello! Welcome to Anvil! Anvil is a decentralized finance platform..."
"""
```

### No History for Greetings

```python
# CRITICAL: Greetings don't use conversation history

if is_greeting:
    # ✨ NO HISTORY - respond only to the greeting
    # Prevents context bleeding from previous messages
    messages.append({
        "role": "user",
        "content": message.value,
    })
```

---

## Off-Topic Handling

### Supervisor Instruction Format

```
[SYSTEM INSTRUCTION: Decline off-topic politely, I specialize in DeFi]

User message: "make a cake"
```

### Instruction Parsing

```python
def _build_instruction_messages(self, message_value: str) -> list[dict]:
    # Parse instruction format
    instruction_match = re.search(r'\[SYSTEM INSTRUCTION: ([^\]]+)\]', message_value)
    instruction = instruction_match.group(1) if instruction_match else "Respond naturally"
    
    # Extract original user message
    user_match = re.search(r'User message: ["\']?([^"\']+)["\']?', message_value)
    original_message = user_match.group(1) if user_match else message_value
    
    system_prompt = f"""You are Anvil's AI assistant...
    
**YOUR INSTRUCTION:** {instruction}

**CRITICAL RULES:**
1. Follow the instruction above EXACTLY
2. If the instruction says "decline off-topic", politely tell the user you can't help
3. Be friendly but firm - redirect to DeFi topics
4. Keep response SHORT (2-3 sentences max)
"""
```

---

## Response Aggregation

### Detection

```python
# Detect aggregation task

is_aggregation = (
    "aggregate" in message.value.lower() or
    "agent response" in message.value.lower() or
    len(message.value) > 2000  # Long messages likely contain multiple responses
)
```

### Token Limit Adjustment

```python
# Use higher token limit for aggregation tasks
max_tokens = self._max_tokens * 3 if is_aggregation else self._max_tokens
# 3000 for aggregation, 1000 for normal
```

### Aggregation Instructions

```python
# Special instructions for aggregation

content = f"""You are aggregating responses from multiple specialist agents. 

IMPORTANT INSTRUCTIONS:
1. **PRESERVE REAL-TIME DATA**: Include APY, TVL, prices prominently
2. **FILTER OUT AUTHENTICATION MESSAGES**: Don't show login prompts for info queries
3. **PRESERVE SPECIFIC DETAILS**: Keep aggregator names, protocols, chains
4. **Deduplicate**: Remove repeated disclaimers
5. **Single disclaimer**: ONE "not financial advice" at the end
6. **Complete summary**: Include ALL specific data points

Agent Responses to Aggregate:
{message.value}
"""
```

---

## Restricted Feature Detection

### Detection Logic

```python
def _is_restricted_feature_query(self, message: str) -> bool:
    message_lower = message.lower()
    restricted_keywords = [
        # Balance
        "my balance", "what's my balance", "check my balance",
        # Activity
        "my transactions", "transaction history", "my activity",
        # Receive
        "my address", "wallet address", "receive crypto",
        # Buy
        "buy crypto", "purchase bitcoin", "buy with card",
        # Send
        "send crypto", "transfer tokens", "send to wallet",
        # Portfolio
        "my portfolio", "my holdings", "list my tokens",
    ]
    return any(kw in message_lower for kw in restricted_keywords)
```

### Feature-to-Message Mapping

```python
feature_to_reason = {
    "balance": "wallet_access",
    "activity": "transaction_history",
    "receive": "wallet_address",
    "buy": "buy_crypto",
    "send": "send_crypto",
    "portfolio": "portfolio_access",
}
```

---

## System Prompt (Full)

The full system prompt includes:

1. **Aggregation instructions**: Preserve real-time data, deduplicate
2. **Anvil is REAL**: Not simulated or hypothetical
3. **Restricted features**: Custom auth messages for each feature
4. **Anvil knowledge base**: Supported features, swap types, lending
5. **Swap capabilities**: Hyperliquid Spot, meme tokens only
6. **Creative writing**: CAN write poems, stories about crypto
7. **Off-topic handling**: Decline non-crypto queries politely
8. **Shortcuts**: Common user commands

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_chat_agent(self, llm_client: LLMClientGateway) -> ChatAgent:
    """Provide Chat agent."""
    return ChatAgent(llm_client=llm_client)
```

---

## Source Attribution

```python
# From execute() method

sources = [
    SourceInfo(
        source_type=SourceType.LLM,
        source_name=model_name,
        citation_text=f"Generated by {model_name}",
        fetched_at=datetime.now(UTC),
        provider="Vertex AI" if "gemini" in model_name.lower() else "DeepInfra",
        relevance_score=1.0,
        metadata={"model": model_name},
    )
]
```

---

## Testing

### Test Cases

```python
# Greeting detection
def test_greeting_detection():
    assert is_greeting("hi") == True
    assert is_greeting("hello") == True
    assert is_greeting("what is defi") == False

# Off-topic handling
def test_off_topic_handling():
    response = await agent.execute(
        message=MessageContent("[SYSTEM INSTRUCTION: Decline]\n\nUser message: make cake")
    )
    assert "specialized in DeFi" in response.content

# Aggregation
def test_aggregation_token_limit():
    # Long message triggers aggregation mode
    assert is_aggregation(message_2500_chars) == True

# Restricted feature
def test_restricted_feature_detection():
    assert is_restricted("my portfolio") == True
    assert is_restricted("what is defi") == False
```

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Standard | < 1000ms | LLM call |
| Greeting | < 500ms | Simpler prompt |
| Aggregation | < 2000ms | More content |
| Restricted | < 100ms | No LLM call |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added greeting handling |
| 2026-01-29 | Added off-topic handling |
| 2026-01-29 | Added response aggregation |
| 2026-01-29 | Added restricted feature detection |

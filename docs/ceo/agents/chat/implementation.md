# Chat Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.CHAT
│   └── services/
│       └── agent_squad/
│           ├── intent_classifier.py      # Intent classification
│           ├── authenticated_supervisor.py # Routing rules
│           ├── guest_supervisor.py       # Guest routing
│           └── supervisor_coordinator.py  # Base coordinator
│
├── infrastructure/
│   └── adapters/
│       └── agent_squad/
│           └── agents/
│               └── chat_agent.py         # Main agent
│
├── application/
│   └── guest/
│       └── i18n/
│           └── translations.py           # Auth messages
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. ChatAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/chat_agent.py`
**Lines**: ~575

#### Class Definition

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

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 34-53 | Initialize with LLM client |
| `agent_type` | 55-58 | Return AgentType.CHAT |
| `execute` | 60-173 | Main entry point |
| `is_available` | 175-178 | Always returns True |
| `_build_messages` | 180-272 | Build LLM messages |
| `_is_restricted_feature_query` | 274-291 | Detect auth-required features |
| `_detect_restricted_feature` | 293-311 | Identify specific feature |
| `_get_custom_message` | 313-339 | Get auth prompt |
| `_build_instruction_messages` | 341-372 | Handle supervisor instructions |
| `_get_greeting_prompt` | 374-403 | Brief greeting prompt |
| `_get_system_prompt` | 405-574 | Full system prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.7,
    max_tokens: int = 1000,
):
    self._llm_client = llm_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_chat_agent(self, llm_client: LLMClientGateway) -> ChatAgent:
    """Provide Chat agent."""
    return ChatAgent(llm_client=llm_client)
```

---

## Execute Method Implementation

### Main Flow

```python
# Lines 60-173
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    start_time = time.time()
    
    # Build messages for LLM
    messages = self._build_messages(message, conversation_context)
    
    # Check if this is a restricted feature query (for guest users)
    is_restricted_query = self._is_restricted_feature_query(message.value)
```

### Restricted Feature Handling

```python
# Lines 76-117
if is_restricted_query:
    # Use custom messages directly (no LLM call needed)
    restricted_feature = self._detect_restricted_feature(message.value)
    custom_message = self._get_custom_message(restricted_feature, conversation_context)
    
    # Return response directly with custom message
    return AgentResponse(
        content=custom_message,
        agent_type=self.agent_type,
        tools_used=["auth_detection"],
        sources=sources,
        metadata={
            "tokens_used": 0,  # No LLM call
            "restricted_feature": restricted_feature,
        },
    )
```

### Aggregation Detection

```python
# Lines 119-134
is_aggregation = (
    "aggregate" in message.value.lower() or
    "agent response" in message.value.lower() or
    len(message.value) > 2000
)

# Use higher token limit for aggregation tasks
max_tokens = self._max_tokens * 3 if is_aggregation else self._max_tokens
```

### LLM Call

```python
# Lines 129-135
response = await self._llm_client.chat(
    messages=messages,
    model=self._model,
    temperature=self._temperature,
    max_tokens=max_tokens,
)
```

---

## Message Building

### _build_messages Method

```python
# Lines 180-272
def _build_messages(
    self,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> list[dict]:
    message_value = message.value
    message_lower = message_value.lower().strip()
    
    # Check for supervisor instruction (off-topic handling)
    has_instruction = message_value.startswith("[SYSTEM INSTRUCTION:")
    if has_instruction:
        return self._build_instruction_messages(message_value)
```

### Greeting Detection

```python
# Lines 196-205
is_greeting = any([
    message_lower in ["hi", "hello", "hey", "hola", "holi", "hey there"],
    message_lower.startswith(("hi ", "hello ", "hey ", "hola ")),
    "how are you" in message_lower,
    "good morning" in message_lower or "good afternoon" in message_lower,
])

# Use conversational prompt for greetings, standard prompt for others
system_prompt = self._get_greeting_prompt() if is_greeting else self._get_system_prompt()
```

### Aggregation Handling

```python
# Lines 214-248
is_aggregation = (
    "agent response" in message.value.lower() or
    "from hunter ai" in message.value.lower() or
    len(message.value) > 5000
)

if is_aggregation:
    messages.append({
        "role": "user",
        "content": f"""You are aggregating responses from multiple specialist agents. 

IMPORTANT INSTRUCTIONS:
1. **PRESERVE REAL-TIME DATA**: Include APY, TVL, prices prominently
2. **FILTER OUT AUTHENTICATION MESSAGES**: Don't show login prompts for info queries
3. **Deduplicate**: Remove repeated disclaimers
...
Agent Responses to Aggregate:
{message.value}
"""
    })
```

### Greeting (No History)

```python
# Lines 249-255
elif is_greeting:
    # ✨ GREETING: NO HISTORY - respond only to the greeting
    # This prevents context bleeding from previous messages
    messages.append({
        "role": "user",
        "content": message.value,
    })
```

### Normal Conversation

```python
# Lines 256-270
else:
    # Normal conversation flow
    # Add conversation history (last 5 messages)
    history = conversation_context.last_n_messages(5)
    for msg in history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": message.value,
    })
```

---

## Restricted Feature Detection

### Detection Method

```python
# Lines 274-291
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

### Feature Identification

```python
# Lines 293-311
def _detect_restricted_feature(self, message: str) -> str:
    message_lower = message.lower()
    
    if any(kw in message_lower for kw in ["my balance", "what's my balance"]):
        return "balance"
    elif any(kw in message_lower for kw in ["my transactions", "transaction history"]):
        return "activity"
    elif any(kw in message_lower for kw in ["my address", "wallet address"]):
        return "receive"
    elif any(kw in message_lower for kw in ["buy crypto", "purchase bitcoin"]):
        return "buy"
    elif any(kw in message_lower for kw in ["send crypto", "transfer tokens"]):
        return "send"
    elif any(kw in message_lower for kw in ["my portfolio", "my holdings"]):
        return "portfolio"
    else:
        return "general"
```

### Custom Auth Message

```python
# Lines 313-339
def _get_custom_message(self, feature: str, context: ConversationContext) -> str:
    # Get language from context
    language = context.user_metadata.get("language", "en")
    
    from app.application.guest.i18n.translations import (
        get_registration_message, get_cta_message
    )
    
    feature_to_reason = {
        "balance": "wallet_access",
        "activity": "transaction_history",
        "receive": "wallet_address",
        "buy": "buy_crypto",
        "send": "send_crypto",
        "portfolio": "portfolio_access",
    }
    
    reason = feature_to_reason.get(feature, "execute_action")
    messages = get_registration_message(reason, language)
    message = messages.get(language, messages.get("en", ""))
    
    cta = get_cta_message(language)
    
    return f"{message}\n\n👉 {cta}"
```

---

## Supervisor Instruction Handling

```python
# Lines 341-372
def _build_instruction_messages(self, message_value: str) -> list[dict]:
    import re
    
    # Extract instruction
    instruction_match = re.search(r'\[SYSTEM INSTRUCTION: ([^\]]+)\]', message_value)
    instruction = instruction_match.group(1) if instruction_match else "Respond naturally"
    
    # Extract original user message
    user_match = re.search(r'User message: ["\']?([^"\']+)["\']?', message_value)
    original_message = user_match.group(1) if user_match else message_value
    
    system_prompt = f"""You are Anvil's AI assistant, specialized in DeFi and cryptocurrency.

**YOUR INSTRUCTION:** {instruction}

**CRITICAL RULES:**
1. Follow the instruction above EXACTLY
2. If the instruction says "decline off-topic", politely tell user you can't help
3. Be friendly but firm - redirect to DeFi topics
4. Keep response SHORT (2-3 sentences max)
"""
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": original_message},
    ]
```

---

## System Prompts

### Greeting Prompt

```python
# Lines 374-403
def _get_greeting_prompt(self) -> str:
    return """You are a friendly DeFi assistant for Anvil. 

When users greet you (hi, hello, hola, hey, etc.):
- Respond naturally with a BRIEF greeting ONLY
- DO NOT provide platform descriptions or feature lists
- Keep it to 1-2 sentences maximum
- Be personable, warm, and brief

Example GOOD responses:
- "Hi! How can I help you today?"
- "Hello! What would you like to know?"

Example BAD responses:
- "Hello! Welcome to Anvil! Anvil is a decentralized finance platform..."
"""
```

### Full System Prompt (Key Sections)

```python
# Lines 405-574
def _get_system_prompt(self) -> str:
    return """You are Anvil's AI assistant...

**WHEN AGGREGATING MULTIPLE AGENT RESPONSES:**
- PRESERVE REAL-TIME DATA from DeFiLlama
- Deduplicate information
- Remove redundancy
- Single disclaimer at end

**CRITICAL: ANVIL IS A REAL PLATFORM**
- NOT simulated or hypothetical
- REAL swaps, REAL lending, REAL prices

**RESTRICTED FEATURES AUTHENTICATION REQUIREMENT**
- Portfolio: Custom auth message
- Balance: Wallet access required
- Activity: Account required
...

**SWAP CAPABILITIES (HYPERLIQUID SPOT ONLY)**
- Only meme tokens supported (PURR, TRUMP, PEPE, etc.)
- NOT supported: ETH, BTC, SOL

**CRITICAL: CREATIVE WRITING ABOUT CRYPTO**
- CAN write poems, stories, analogies about crypto/DeFi
- Be creative and engaging

**CRITICAL: OFF-TOPIC QUERY HANDLING**
- Politely decline non-DeFi topics
- Redirect to DeFi topics
"""
```

---

## Response Structure

### AgentResponse

```python
# Lines 161-173
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=[],  # Chat agent doesn't use external tools
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
        "finish_reason": response.get("finish_reason"),
        "provider": response.get("provider", provider),
    },
)
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_chat_agent.py -v

# All chat tests
pytest tests/ -k chat -v
```

### Test Cases

```python
# Greeting detection
def test_greeting_detection():
    agent = ChatAgent(mock_llm)
    messages = agent._build_messages(
        MessageContent("hi"),
        mock_context
    )
    # Should use greeting prompt, no history

# Off-topic handling
def test_off_topic_handling():
    messages = agent._build_instruction_messages(
        "[SYSTEM INSTRUCTION: Decline off-topic]\n\nUser message: make cake"
    )
    assert "YOUR INSTRUCTION: Decline off-topic" in messages[0]["content"]

# Restricted feature detection
def test_restricted_feature():
    assert agent._is_restricted_feature_query("my portfolio") == True
    assert agent._is_restricted_feature_query("what is defi") == False

# Aggregation mode
def test_aggregation_detection():
    long_message = "Agent response: " + "x" * 3000
    assert "aggregate" in long_message.lower() or len(long_message) > 2000
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Standard | < 1000ms | LLM call |
| Greeting | < 500ms | Simpler prompt |
| Aggregation | < 2000ms | 3x tokens |
| Restricted | < 100ms | No LLM call |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added greeting handling |
| 2026-01-29 | Added off-topic handling |
| 2026-01-29 | Added response aggregation |

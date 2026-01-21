# Prompt Injection Architecture

> **Comprehensive Documentation of Prompt Engineering in Guest/Message and Conversations/Message Systems**
> 
> **CEO Review Document** - Based on CTO Engineering Methodology: First Principles, Design Thinking, Systems Thinking

## Executive Summary

This document provides a **complete analysis of prompt injection points** throughout the Anvil messaging system. The architecture has been simplified to use **pure LLM-based routing** without intent classification, following the CEO directive.

**Key Findings:**
- **2 Primary Prompt Injection Points**: Supervisor Coordinator (routing), Agents (execution)
- **18 Agent-Specific Prompts**: Each agent has tailored system prompts
- **Dynamic Context Injection**: Prompts adapt based on conversation history, knowledge base, and API data
- **Security Considerations**: Input sanitization, harmful content blocking, and prompt injection prevention

**Architecture Change**: The Distillation Engine no longer uses LLM-based intent classification. All routing is done by the Supervisor Coordinator.

---

## Table of Contents

1. [Prompt Injection Overview](#prompt-injection-overview)
2. [Supervisor Coordinator Prompts](#supervisor-coordinator-prompts)
3. [Agent Squad Prompts](#agent-squad-prompts)
4. [Context Injection Mechanisms](#context-injection-mechanisms)
5. [Off-Topic Handling](#off-topic-handling)
6. [Security & Prompt Injection Prevention](#security--prompt-injection-prevention)
7. [Prompt Engineering Best Practices](#prompt-engineering-best-practices)
8. [Implementation Details](#implementation-details)
9. [Future Enhancements](#future-enhancements)

---

## Prompt Injection Overview

### Architecture Flow (LLM-Based Routing)

```
User Message
    ↓
[1] Security Check (Pattern-based, NO LLM)
    ↓
[2] Supervisor Coordinator (LLM Prompt: Workflow Planning + Routing)
    ↓
[3] Agent Orchestrator (Parallel Execution)
    ↓
[4] Individual Agents (LLM Prompts: Agent-specific system prompts)
    ↓
[5] Response Aggregation (LLM Prompt: CHAT agent aggregation)
    ↓
Final Response
```

### Prompt Injection Points

| Component | Prompt Type | LLM Used | Purpose | Location |
|-----------|------------|----------|---------|----------|
| **Security Check** | None (Pattern-based) | N/A | Block harmful content | `send_guest_message.py` |
| **Supervisor Coordinator** | Workflow Planning | Vertex AI / DeepInfra | Route to agents, plan workflows | `supervisor_coordinator.py:_build_planning_prompt()` |
| **CHAT Agent** | System + Aggregation + Instruction | Vertex AI / DeepInfra | Conversation, off-topic handling, aggregation | `chat_agent.py` |
| **KNOWLEDGE Agent** | System + Knowledge Context | Vertex AI / DeepInfra | Educational queries, Anvil knowledge | `knowledge_agent.py` |
| **HUNTER_AI Agent** | System + Market Data | Vertex AI / DeepInfra | Market sentiment, price data | `hunter_ai_agent.py` |
| **DEFI_YIELD Agent** | System + APY Data | Vertex AI / DeepInfra | Yield farming, APY analysis | `defi_yield_agent.py` |
| **RISK_ANALYZER Agent** | System + Protocol Data | Vertex AI / DeepInfra | Risk assessment, TVL analysis | `risk_analyzer_agent.py` |
| **GAS_OPTIMIZER Agent** | System + Gas Data | Vertex AI / DeepInfra | Gas price optimization | `gas_optimizer_agent.py` |
| **GUEST_AUTH Agent** | Rule-based (No LLM) | N/A | Registration prompts | `guest_auth_agent.py` |

---

## Supervisor Coordinator Prompts

### Overview

The Supervisor Coordinator is the **primary routing brain**. It uses a highly optimized LLM prompt to:

1. **Understand user request** semantically (no intent classification)
2. **Detect off-topic** queries and route appropriately
3. **Select agents** based on query content
4. **Create task dependencies** for multi-agent workflows

### Optimized Planning Prompt

**File**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

**Method**: `_build_planning_prompt()`

**Prompt Structure** (Optimized for speed and accuracy):

```python
def _build_planning_prompt(
    self,
    message: MessageContent,
    conversation_context: ConversationContext,
    available_agents: list[AgentType],
) -> str:
    """
    Build optimized workflow planning prompt for LLM.
    
    Prompt Engineering Techniques Used:
    - Clear role definition
    - Structured output format with examples
    - Decision tree for routing
    - Few-shot examples for common patterns
    - Concise guidelines (reduced from ~100 lines to ~40)
    """
    agents_str = ", ".join([agent.value for agent in available_agents])
    
    # Build conversation history context (keep minimal)
    context_section = ""
    if conversation_context.conversation_history:
        recent = conversation_context.conversation_history[-3:]  # Last 3 only
        if recent:
            context_section = "\n<context>\n"
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")[:150]
                if content:
                    context_section += f"{role}: {content}\n"
            context_section += "</context>\n"
    
    return f"""You are a DeFi workflow router. Route to the correct agent. JSON only.

<request>{message.value}</request>
{context_section}
<agents>{agents_str}</agents>

<rules>
1. OFF-TOPIC FIRST: If NOT about crypto/DeFi/blockchain/Web3, use "chat" + "Decline off-topic politely"
   Examples: cooking, recipes, weather, sports, general knowledge → OFF-TOPIC
   
2. CRYPTO TOPICS:
   - Prices → "hunter_ai"
   - DeFi education → "knowledge"  
   - Yield/APY → "defi_yield"
   - Risk/TVL → "risk_analyzer"
   - Gas → "gas_optimizer"
   - Wallet (balance/send/receive) → "guest_auth"
   - Greetings → "chat"
</rules>

<examples>
"hola" → {{"tasks":[{{"agent_type":"chat","task_description":"Greet warmly","depends_on":[]}}]}}
"btc price" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get BTC price","depends_on":[]}}]}}
"what is defi" → {{"tasks":[{{"agent_type":"knowledge","task_description":"Explain DeFi","depends_on":[]}}]}}
"make a cake" → {{"tasks":[{{"agent_type":"chat","task_description":"Decline off-topic politely, I only help with DeFi","depends_on":[]}}]}}
"how to cook pasta" → {{"tasks":[{{"agent_type":"chat","task_description":"Decline off-topic politely, I specialize in crypto","depends_on":[]}}]}}
"weather today" → {{"tasks":[{{"agent_type":"chat","task_description":"Decline off-topic politely, redirect to DeFi topics","depends_on":[]}}]}}
"my balance" → {{"tasks":[{{"agent_type":"guest_auth","task_description":"Handle restricted feature","depends_on":[]}}]}}
"best yield farms" → {{"tasks":[{{"agent_type":"defi_yield","task_description":"Find best yield opportunities","depends_on":[]}}]}}
</examples>

{{"tasks":[{{"agent_type":"...","task_description":"...","depends_on":[]}}]}}"""
```

### Prompt Engineering Techniques

1. **XML Tags**: `<request>`, `<context>`, `<agents>`, `<rules>`, `<examples>`
   - Better structure for LLM parsing
   - Clear separation of concerns

2. **Few-Shot Examples**: 8 concrete examples covering:
   - Greetings (multilingual)
   - Price queries
   - DeFi education
   - Off-topic (cooking, weather)
   - Restricted features
   - Yield queries

3. **Decision Tree Rules**: Numbered, prioritized rules
   - **Rule 1**: Off-topic detection (FIRST priority)
   - **Rule 2**: Crypto topics routing

4. **Concise Format**: ~40 lines vs original ~100 lines
   - Faster LLM processing
   - Lower token usage

### Response Parsing

```python
response = await self._llm_client.plan_workflow(
    prompt=prompt,
    max_agents=self._max_agents,
)

# Parse workflow plan
tasks = []
for task_data in response.get("tasks", []):
    agent_type_str = task_data.get("agent_type") or task_data.get("agent", "chat")
    agent_type = AgentType[agent_type_str.upper()]  # Enum validation
    
    task = AgentTask(
        agent_type=agent_type,
        task_description=task_data.get("task_description", ""),
        depends_on=task_data.get("depends_on", []),
    )
    tasks.append(task)
```

---

## Agent Squad Prompts

### Common Pattern

All agents follow a similar prompt injection pattern:

```python
class SomeAgent:
    def _get_system_prompt(self, context: str = "") -> str:
        """Get system prompt for agent."""
        base_prompt = """[Agent-specific system prompt]"""
        
        if context:
            base_prompt += f"\n\n{context}"
        
        return base_prompt
    
    def _build_messages(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> list[dict]:
        """Build messages for LLM API."""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
        ]
        
        # Add conversation history
        history = conversation_context.last_n_messages(5)
        for msg in history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message.value,  # ← USER INPUT INJECTED HERE
        })
        
        return messages
```

### CHAT Agent - Special Handling

**File**: `src/app/infrastructure/adapters/agent_squad/agents/chat_agent.py`

The CHAT agent has special handling for **off-topic queries** and **aggregation**:

#### Off-Topic Instruction Handling

When the Supervisor detects off-topic and creates a task with "decline" in the description:

```python
def _build_messages(self, message: MessageContent, conversation_context: ConversationContext) -> list[dict]:
    # Check for supervisor instruction (off-topic handling)
    has_instruction = message.value.startswith("[SYSTEM INSTRUCTION:")
    if has_instruction:
        return self._build_instruction_messages(message.value)
    # ... normal flow ...

def _build_instruction_messages(self, message_value: str) -> list[dict]:
    """Build messages when supervisor provides a specific instruction (e.g., off-topic)."""
    import re
    
    # Extract instruction
    instruction_match = re.search(r'\[SYSTEM INSTRUCTION: ([^\]]+)\]', message_value)
    instruction = instruction_match.group(1) if instruction_match else "Respond naturally"
    
    # Extract original user message
    user_match = re.search(r'User message: ["\']?([^"\']+)["\']?', message_value)
    original_message = user_match.group(1) if user_match else message_value
    
    # Build focused system prompt for instruction handling
    system_prompt = f"""You are Anvil's AI assistant, specialized in DeFi and cryptocurrency.

**YOUR INSTRUCTION:** {instruction}

**CRITICAL RULES:**
1. Follow the instruction above EXACTLY
2. If the instruction says "decline off-topic" or similar, politely tell the user you can't help with that topic
3. Be friendly but firm - redirect to DeFi topics
4. Keep response SHORT (2-3 sentences max)

**Example off-topic response:**
"I'm specialized in DeFi and crypto assistance. I can't help with [topic], but I can help you with swaps, staking, lending, and other DeFi operations. What would you like to know about DeFi?"
"""
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": original_message},
    ]
```

#### Aggregation Mode

For multi-agent workflows, CHAT agent aggregates responses:

```python
if is_aggregation:
    messages.append({
        "role": "user",
        "content": f"""You are aggregating responses from multiple specialist agents.

IMPORTANT INSTRUCTIONS:
1. **PRESERVE REAL-TIME DATA**: Keep APY, TVL, price data prominently
2. **FILTER OUT AUTHENTICATION MESSAGES**: Remove registration prompts unless asked
3. **PRESERVE SPECIFIC DETAILS**: Include aggregator names, protocol names
4. **Deduplicate**: Remove repeated disclaimers
5. **Single disclaimer**: Include ONE "not financial advice" at the end

Agent Responses to Aggregate:
{message.value}
""",
    })
```

### KNOWLEDGE Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/knowledge_agent.py`

**Knowledge Context Injection**:
```python
if knowledge_context:
    base_prompt += f"""
The following information from Anvil's knowledge base is relevant to this query:

{knowledge_context}  # ← Knowledge base JSON data

Use this information to provide accurate responses about Anvil features.
"""
```

### Data Agents (HUNTER_AI, DEFI_YIELD, RISK_ANALYZER, GAS_OPTIMIZER)

These agents inject **real-time API data** into the user message:

```python
# HUNTER_AI example
market_data_context = f"""
**REAL-TIME MARKET DATA FROM COINGECKO:**

BTC:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
"""

user_message = f"""
{message.value}

{market_data_context}

Analyze based on this real-time data.
"""
```

---

## Context Injection Mechanisms

### 1. Conversation History

**All agents** include conversation history:

```python
history = conversation_context.last_n_messages(5)  # Last 5 messages
for msg in history:
    messages.append({
        "role": msg.get("role", "user"),
        "content": msg.get("content", ""),
    })
```

**Supervisor uses last 3** for context-aware routing:
```python
recent = conversation_context.conversation_history[-3:]
```

### 2. Knowledge Base

**KNOWLEDGE Agent** loads JSON files from `anvil_knowledge/features/`:
- `overview.json`, `swap.json`, `portfolio.json`, `wallet.json`, etc.

### 3. API Data

**Data injection pattern**:
```python
# Fetch API data
api_data = await api_client.fetch_data(...)

# Format as context
formatted_data = f"""
**REAL-TIME DATA FROM {API_NAME}:**
{format_data(api_data)}
"""

# Inject into user message
enhanced_message = f"{original_message}\n\n{formatted_data}"
```

### 4. Supervisor Instructions

**Off-topic handling** uses instruction injection:

```python
# In supervisor_coordinator.py
if "decline" in task_desc_lower or "off-topic" in task_desc_lower:
    message_content = MessageContent(
        f"[SYSTEM INSTRUCTION: {task.task_description}]\n\nUser message: \"{original_message}\""
    )
```

---

## Off-Topic Handling

### Detection Flow

```
1. User sends: "how to bake bread?"
       ↓
2. Supervisor LLM detects off-topic
       ↓
3. Creates task: {"agent_type": "chat", "task_description": "Decline off-topic politely, I only help with DeFi"}
       ↓
4. Supervisor detects "decline" in task_description
       ↓
5. Builds enhanced message: "[SYSTEM INSTRUCTION: Decline off-topic...]\n\nUser message: how to bake bread?"
       ↓
6. CHAT Agent parses instruction and declines politely
       ↓
7. Response: "I'm specialized in DeFi and crypto assistance. I can't help with baking, but I can help you with swaps, staking, lending..."
```

### Implementation

**Supervisor Detection** (`supervisor_coordinator.py`):
```python
task_desc_lower = task.task_description.lower()

if "decline" in task_desc_lower or "off-topic" in task_desc_lower or "politely" in task_desc_lower:
    logger.info(f"🚫 OFF-TOPIC detected: {task.task_description}")
    message_content = MessageContent(
        f"[SYSTEM INSTRUCTION: {task.task_description}]\n\nUser message: \"{original_message}\""
    )
```

**CHAT Agent Handling** (`chat_agent.py`):
```python
has_instruction = message.value.startswith("[SYSTEM INSTRUCTION:")
if has_instruction:
    return self._build_instruction_messages(message.value)
```

---

## Security & Prompt Injection Prevention

### Security Check (Pattern-Based)

**Location**: `send_guest_message.py:execute()`

```python
# ONLY security check - no intent classification
harmful_patterns = [
    "launder", "money laundering",
    "avoid kyc", "bypass kyc",
    "exploit", "rug pull",
    "doxx", "hack", "steal",
]

content_lower = content.lower()
is_harmful = any(pattern in content_lower for pattern in harmful_patterns)

if not is_harmful:
    # Route to LLM-based supervisor
    result = await self._process_with_llm_supervisor(...)
```

### Input Validation

**Length Limits**:
```python
MAX_MESSAGE_LENGTH = 500  # Characters

if len(content) > MAX_MESSAGE_LENGTH:
    raise ValueError("Message too long")
```

**Pydantic Validation**:
```python
class GuestChatRequest(BaseModel):
    content: str = Field(..., max_length=500)
    language: str = Field(default="en", pattern="^(en|es|pt|zh)$")
```

### Output Validation

**Agent Type Whitelist**:
```python
try:
    agent_type = AgentType[agent_type_str.upper()]  # Enum validation
except KeyError:
    agent_type = AgentType.CHAT  # Fallback to safe default
```

### Recommended Enhancements

#### 1. Input Sanitization

```python
def sanitize_user_input(content: str) -> str:
    """Sanitize user input to prevent prompt injection."""
    patterns_to_remove = [
        r"ignore (previous|all) (instructions|prompts?)",
        r"system:",
        r"assistant:",
        r"\[INST\]",
    ]
    
    sanitized = content
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()
```

#### 2. Prompt Injection Detection

```python
def detect_prompt_injection(content: str) -> bool:
    """Detect potential prompt injection attempts."""
    injection_patterns = [
        r"ignore (previous|all) (instructions|prompts?)",
        r"forget (everything|all|previous)",
        r"new (instructions|prompt|task)",
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in injection_patterns)
```

---

## Prompt Engineering Best Practices

### Current Practices

1. **Clear Role Definition**:
   ```
   You are a DeFi workflow router.
   ```

2. **Structured Output Format**:
   ```
   {"tasks":[{"agent_type":"...","task_description":"...","depends_on":[]}]}
   ```

3. **Few-Shot Examples**: 8 concrete examples for common patterns

4. **Prioritized Rules**: Numbered rules with clear hierarchy

5. **XML Tags**: `<request>`, `<rules>`, `<examples>` for structure

### Prompt Optimization Results

**Before** (v1.0):
- ~100 lines
- Verbose guidelines
- No examples
- Average response time: ~14s

**After** (v2.0):
- ~40 lines
- Concise rules
- 8 examples
- Average response time: ~6s
- **~60% faster**

---

## Implementation Details

### Guest/Message Prompt Flow

```
1. User Message Received
   ↓
2. Security Check (Pattern-based, NO LLM)
   ↓
3. Supervisor Coordinator
   ├─ _build_planning_prompt()  ← PROMPT INJECTION POINT 1
   ├─ llm_client.plan_workflow(prompt)
   └─ Parse workflow plan
   ↓
4. Agent Orchestration (Parallel)
   ├─ For each agent task:
   │  ├─ Check for off-topic instruction
   │  ├─ Agent._build_messages()  ← PROMPT INJECTION POINT 2
   │  ├─ llm_client.chat(messages)
   │  └─ Collect AgentResponse
   └─ If multiple agents:
      └─ CHAT agent aggregation  ← PROMPT INJECTION POINT 3
   ↓
5. Response Aggregation
   ↓
6. Return Final Response
```

### Prompt Injection Code Locations

| Component | File | Method | Purpose |
|-----------|------|--------|---------|
| **Supervisor Coordinator** | `supervisor_coordinator.py` | `_build_planning_prompt()` | LLM-based routing |
| **CHAT Agent** | `chat_agent.py` | `_build_messages()` | Conversation, off-topic |
| **CHAT Agent** | `chat_agent.py` | `_build_instruction_messages()` | Off-topic handling |
| **KNOWLEDGE Agent** | `knowledge_agent.py` | `_get_system_prompt()` | Education, knowledge |
| **HUNTER_AI Agent** | `hunter_ai_agent.py` | `execute()` | Market data |
| **DEFI_YIELD Agent** | `defi_yield_agent.py` | `execute()` | APY data |
| **RISK_ANALYZER Agent** | `risk_analyzer_agent.py` | `execute()` | Risk analysis |
| **GAS_OPTIMIZER Agent** | `gas_optimizer_agent.py` | `execute()` | Gas prices |

---

## Future Enhancements

### Planned Improvements

1. **Prompt Versioning System**:
   - Track prompt versions in database
   - A/B testing framework
   - Rollback capabilities

2. **Prompt Template Management**:
   - External prompt files (YAML/JSON)
   - Version control for prompts
   - Prompt diff tracking

3. **Enhanced Prompt Injection Detection**:
   - Real-time detection
   - Automatic sanitization
   - Alert system

4. **Prompt Metrics**:
   - Track prompt performance
   - Response quality scoring
   - Token usage optimization

---

## Conclusion

The Anvil messaging system uses **strategic prompt injection** across two primary components:

1. **Supervisor Coordinator**: LLM-based workflow planning and routing
2. **Agent Squad**: 18 specialized agents with domain-specific prompts

**Key Strengths**:
- Simplified architecture (no intent classification)
- Optimized prompts (~60% faster)
- Comprehensive off-topic handling
- Security checks before LLM routing

**Security Status**: ✅ **Good** with recommended enhancements
- Pattern-based security check
- Input validation
- Output validation (agent type whitelist)
- Recommended: Additional prompt injection detection

---

## References

- **Supervisor Coordinator**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`
- **Agent Implementations**: `src/app/infrastructure/adapters/agent_squad/agents/`
- **Guest Message Handler**: `src/app/application/guest/commands/send_guest_message.py`
- **Test Results**: `docs/output/guest_input.csv`

---

*Document Version: 2.0*  
*Last Updated: 2026-01-21*  
*Author: Anvil Engineering Team*  
*Review Status: CEO Review Pending*

**Changelog**:
- **v2.0** (2026-01-21): Major rewrite for LLM-based routing
  - Removed Distillation Engine LLM prompts (now rule-based only)
  - Updated Supervisor prompt to optimized version
  - Added off-topic handling documentation
  - Added security check documentation
  - Updated prompt injection points
- **v1.0** (2026-01-20): Initial version with intent classification

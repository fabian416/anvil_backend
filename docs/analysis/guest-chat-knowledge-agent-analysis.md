# Guest Chat Knowledge Agent Analysis

## Current Guest Chat Flow

### 1. Entry Point
**File:** `src/app/application/guest/commands/send_guest_message.py`

**Flow:**
```
User Message → Guest Message Handler
  ↓
1. Simple Info Query Check (Fast Path)
   - Pattern: "what is X?", "what are X?"
   - Bypasses workflow planning
   - Directly routes to ChatAgent
   ↓
2. Distillation Engine Check
   - Educational responses for tokens (BTC, ETH, etc.)
   - Static responses from educational_responses.py
   ↓
3. Intent Detection
   - Classifies intent (PROTOCOL_SEARCH, HUNTER_SENTIMENT, etc.)
   - Maps to appropriate agent
   ↓
4. SupervisorCoordinator (Complex Workflows)
   - Multi-agent task planning
   - Workflow orchestration
   ↓
5. Agent Execution
   - Routes to specific agent (ChatAgent, HunterAI, Research, etc.)
   - Returns response
```

### 2. Knowledge Handling Mechanisms

#### A. ChatAgent (Current Primary Handler)
**File:** `src/app/infrastructure/adapters/agent_squad/agents/chat_agent.py`

**Capabilities:**
- General conversation
- Anvil knowledge base (embedded in system prompt)
- Educational information about DeFi/crypto
- Guides users to specialist agents

**System Prompt Includes:**
- Anvil platform features
- Swap types (1inch, LiFi, Hyperliquid, MoonPay)
- Multi-chain support
- Restricted features handling

**Limitations:**
- Knowledge is static (in system prompt)
- No dynamic knowledge retrieval
- Limited to what's in the prompt

#### B. Distillation Engine
**File:** `src/app/domain/services/distillation/engine.py`

**Purpose:**
- Educational responses for common tokens
- Static knowledge base
- Pattern matching for "what is X?" queries

**Coverage:**
- Common tokens (BTC, ETH, USDC, etc.)
- Basic DeFi concepts
- Multi-language support

#### C. Knowledge Injector
**File:** `src/app/application/chat/services/knowledge_injector.py`

**Purpose:**
- Dynamically injects knowledge from JSON files
- Intent-based knowledge selection
- Token-efficient compression

**Knowledge Files:**
- `anvil_knowledge/features/overview.json`
- `anvil_knowledge/features/hunter_ai.json`
- `anvil_knowledge/features/ultra.json`
- `anvil_knowledge/features/swap.json`

**Usage:**
- Currently used in authenticated chat
- NOT currently used in guest chat

#### D. Educational Responses
**File:** `src/app/infrastructure/distillation/educational_responses.py`

**Purpose:**
- Static educational responses for tokens
- Multi-language support (en, es, pt, zh)
- Pattern matching fallback

### 3. Intent Classification

**File:** `src/app/domain/services/agent_squad/intent_classifier.py`

**Knowledge-Related Intents:**
- `anvil_knowledge` → Routes to `AgentType.CHAT`
- `general_question` → Routes to `AgentType.CHAT`

**Current Mapping:**
```python
INTENT_AGENT_MAP = {
    "anvil_knowledge": AgentType.CHAT,
    "general_question": AgentType.CHAT,
    # ... other intents
}
```

### 4. Guest Chat Specifics

**Fast Path (Simple Queries):**
```python
# Line 356-412 in send_guest_message.py
if is_simple_info_query:
    # Directly route to ChatAgent
    # Bypasses workflow planning
    # Faster response time
```

**Real Handler Intents:**
```python
REAL_HANDLER_INTENTS = {
    ChatIntent.PROTOCOL_SEARCH,
    ChatIntent.RISK_ASSESSMENT,
    ChatIntent.HUNTER_SENTIMENT,
    # ... other intents
    # Note: GENERAL_CONVERSATION is NOT in this list
    # Falls back to demo response
}
```

**Informational Query Fallback:**
```python
# Line 1912-2024
def _check_informational_query(self, content: str, language: str):
    # Pattern matching for "what is X?"
    # Returns educational response if found
    # Multi-language support
```

## Current Limitations

### 1. Knowledge Fragmentation
- Knowledge spread across multiple systems
- ChatAgent system prompt (static)
- Distillation engine (static responses)
- Educational responses (static)
- Knowledge injector (not used in guest chat)

### 2. No Dedicated Knowledge Agent
- All knowledge queries route to ChatAgent
- ChatAgent handles too many responsibilities
- No specialized knowledge retrieval
- No dynamic knowledge updates

### 3. Limited Knowledge Base Access
- Knowledge injector not used in guest chat
- JSON knowledge files not accessible
- Static responses only

### 4. No Knowledge Context Awareness
- Doesn't track what user has learned
- No progressive knowledge building
- No personalized knowledge recommendations

## Proposed Solution: Knowledge Anvil Agent

### Benefits

1. **Dedicated Knowledge Handling**
   - Specialized agent for educational queries
   - Focused system prompt
   - Better knowledge retrieval

2. **Dynamic Knowledge Access**
   - Access to JSON knowledge files
   - Integration with KnowledgeInjector
   - Real-time knowledge updates

3. **Better User Experience**
   - More accurate knowledge responses
   - Context-aware answers
   - Progressive learning support

4. **Separation of Concerns**
   - ChatAgent: General conversation
   - KnowledgeAgent: Educational/knowledge queries
   - Clear routing boundaries

### Implementation Plan

1. **Create KnowledgeAgent**
   - New agent class
   - Specialized system prompt
   - Knowledge injector integration

2. **Add to AgentType Enum**
   - `KNOWLEDGE = "knowledge"`

3. **Update Intent Classification**
   - `anvil_knowledge` → `AgentType.KNOWLEDGE`
   - `general_question` → `AgentType.KNOWLEDGE`

4. **Update Guest Chat Flow**
   - Route knowledge queries to KnowledgeAgent
   - Keep ChatAgent for general conversation

5. **Integration Points**
   - Guest chat fast path
   - SupervisorCoordinator workflow planning
   - Intent classifier

## Next Steps

1. ✅ Analysis complete
2. ⏳ Create KnowledgeAgent implementation
3. ⏳ Add to AgentType enum
4. ⏳ Update intent classification
5. ⏳ Integrate into guest chat flow
6. ⏳ Test with guest chat endpoint

# Prompt Injection Architecture

> **Comprehensive Documentation of Prompt Engineering in Guest/Message and Conversations/Message Systems**
> 
> **CEO Review Document** - Based on CTO Engineering Methodology: First Principles, Design Thinking, Systems Thinking

## Executive Summary

This document provides a **complete analysis of prompt injection points** throughout the Anvil messaging system. It details where, how, and why prompts are constructed and injected into LLM calls across three critical components:

1. **Distillation Engine** - Query optimization and routing
2. **Supervisor Coordinator** - Multi-agent workflow planning
3. **Agent Squad** - 18 specialized agents with domain-specific prompts

**Key Findings:**
- **3 Primary Prompt Injection Points**: Distillation, Supervisor, Agents
- **18 Agent-Specific Prompts**: Each agent has tailored system prompts
- **Dynamic Context Injection**: Prompts adapt based on conversation history, knowledge base, and API data
- **Security Considerations**: Input sanitization and prompt injection prevention

---

## Table of Contents

1. [Prompt Injection Overview](#prompt-injection-overview)
2. [Distillation Engine Prompts](#distillation-engine-prompts)
3. [Supervisor Coordinator Prompts](#supervisor-coordinator-prompts)
4. [Agent Squad Prompts](#agent-squad-prompts)
5. [Prompt Construction Patterns](#prompt-construction-patterns)
6. [Context Injection Mechanisms](#context-injection-mechanisms)
7. [Security & Prompt Injection Prevention](#security--prompt-injection-prevention)
8. [Prompt Engineering Best Practices](#prompt-engineering-best-practices)
9. [Implementation Details](#implementation-details)
10. [Future Enhancements](#future-enhancements)

---

## Prompt Injection Overview

### Architecture Flow

```
User Message
    ↓
[1] Distillation Engine (Rule-based, NO LLM prompts)
    ↓
[2] Supervisor Coordinator (LLM Prompt: Workflow Planning)
    ↓
[3] Agent Orchestrator
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
| **Distillation Engine** | None (Rule-based) | N/A | Intent classification, complexity assessment, entity extraction | `src/app/domain/services/distillation/` |
| **Supervisor Coordinator** | Workflow Planning | Vertex AI / DeepInfra | Plan multi-agent workflows | `supervisor_coordinator.py:_build_planning_prompt()` |
| **CHAT Agent** | System + Aggregation | Vertex AI / DeepInfra | General conversation, response aggregation | `chat_agent.py:_get_system_prompt()` |
| **KNOWLEDGE Agent** | System + Knowledge Context | Vertex AI / DeepInfra | Educational queries, Anvil knowledge | `knowledge_agent.py:_get_system_prompt()` |
| **HUNTER_AI Agent** | System + Market Data | Vertex AI / DeepInfra | Market sentiment, price predictions | `hunter_ai_agent.py:_get_system_prompt()` |
| **EXECUTION Agent** | System + Transaction Intent | Vertex AI / DeepInfra | Transaction parsing, swap quotes | `execution_agent_privy.py:_parse_transaction_intent()` |
| **DEFI_YIELD Agent** | System + APY Data | Vertex AI / DeepInfra | Yield farming, APY analysis | `defi_yield_agent.py:_get_system_prompt()` |
| **RISK_ANALYZER Agent** | System + Protocol Data | Vertex AI / DeepInfra | Risk assessment, TVL analysis | `risk_analyzer_agent.py:_get_system_prompt()` |
| **GAS_OPTIMIZER Agent** | System + Gas Data | Vertex AI / DeepInfra | Gas price optimization | `gas_optimizer_agent.py:_get_system_prompt()` |
| **Other Agents** | System (varies) | Vertex AI / DeepInfra | Domain-specific tasks | `agents/*.py:_get_system_prompt()` |

---

## Distillation Engine Prompts

### Overview

**Updated**: The Distillation Engine now uses **hybrid classification**:
- **Rule-based patterns** (fast, ~90% accuracy) - for common, clear queries
- **LLM-based classification** (Vertex AI with DeepInfra fallback) - for ambiguous/complex queries

This hybrid approach provides:
- **Speed**: Rule-based patterns for fast classification of common queries
- **Accuracy**: LLM-based classification for ambiguous queries that don't match patterns
- **Context-awareness**: Uses conversation history for better intent detection
- **Cost-efficiency**: Only uses LLM when rule-based patterns fail

### IntentClassifier

**File**: `src/app/domain/services/distillation/intent_classifier.py`

**Method**: `async classify(text: str, conversation_history: Optional[List[Dict]] = None) -> Tuple[Intent, float]`

**Approach**: **Hybrid classification** (rule-based + LLM)

**Classification Flow**:
```
1. Try rule-based patterns (fast, high confidence)
   ↓ (if match found)
   Return intent with 0.95 confidence
   
   ↓ (if no match)
2. Use LLM classification (Vertex AI with DeepInfra fallback)
   ↓
   Build classification prompt with conversation history
   ↓
   Call llm_client.classify_intent(prompt, model="gemini-2.0-flash")
   ↓
   Parse JSON response: {intent, confidence, reasoning}
   ↓
   Return intent if confidence >= 0.85, else UNCLEAR
```

**Rule-Based Patterns** (First Tier):
```python
INTENT_PATTERNS = {
    Intent.PRICE_CHECK: [
        r"\b(price|cost|worth|value) of (\w+|ETH|BTC|USDC)",
        r"what('s| is) (\w+|ETH|BTC) (price|worth|trading at)",
        # ... more patterns
    ],
    # ... 20+ intent categories
}
```

**LLM-Based Classification** (Second Tier):
- **Trigger**: When no rule-based pattern matches
- **LLM Client**: `LLMClientGateway` (Vertex AI primary, DeepInfra fallback)
- **Model**: `gemini-2.0-flash` (fast, cost-effective)
- **Fallback**: Automatic fallback to DeepInfra if Vertex AI fails

**Prompt Injection**:
```python
def _build_classification_prompt(
    self,
    text: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Build classification prompt with conversation history context.
    
    Prompt Structure:
    1. Role definition
    2. Available intent categories
    3. User query (injected)
    4. Conversation history (injected for context)
    5. Classification instructions
    6. Examples
    7. Output format (JSON)
    """
    # Build context from conversation history
    context_section = ""
    if conversation_history:
        context_section = "\n\n**Conversation History (for context):**\n"
        for msg in conversation_history[-3:]:  # Last 3 messages
            context_section += f"- {msg['role']}: {msg['content'][:200]}\n"
    
    prompt = f"""Classify the user's intent from this DeFi/crypto query.

**Available Intent Categories:**
[... intent categories ...]

**User Query:**
{text}  # ← USER INPUT INJECTED HERE
{context_section}  # ← CONVERSATION HISTORY INJECTED HERE

**Classification Instructions:**
[... instructions ...]

**Examples:**
[... examples ...]

**Respond with ONLY valid JSON:**
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}
"""
    return prompt
```

**LLM Call**:
```python
response = await self._llm_client.classify_intent(
    prompt=prompt,  # ← Prompt with user input + conversation history
    model="gemini-2.0-flash",  # Fast Vertex AI model
)
# LLMClientWithFallback automatically handles fallback to DeepInfra if needed
```

**Response Parsing**:
```python
if isinstance(response, dict):
    intent_str = response.get("intent", "unclear")
    confidence = float(response.get("confidence", 0.5))
    
    # Map string intent to Intent enum
    intent = Intent(intent_str.lower())
    return intent, confidence
```

### ComplexityAssessor

**File**: `src/app/domain/services/distillation/complexity_assessor.py`

**Method**: `assess(text: str, intent: Intent) -> ComplexityLevel`

**Approach**: Rule-based scoring (no LLM prompts)

**Scoring Factors**:
- Token count
- Question count
- Requires calculation
- Requires comparison
- Multi-step indicators
- Requires tools
- Requires context

**No Prompt Injection**: Algorithmic complexity scoring, no LLM calls

### EntityExtractor

**File**: `src/app/domain/services/distillation/entity_extractor.py`

**Method**: `extract(text: str) -> ExtractedEntities`

**Approach**: Regex-based entity extraction (no LLM prompts)

**Extraction Methods**:
- `_extract_tokens()`: Token symbol matching
- `_extract_protocols()`: Protocol name matching
- `_extract_chains()`: Blockchain name matching
- `_extract_amounts()`: Numeric amount extraction
- `_extract_addresses()`: Ethereum address extraction
- `_extract_time_refs()`: Time reference extraction

**No Prompt Injection**: Pattern matching, no LLM calls

### Summary: Distillation Engine

**Prompt Injection**: ✅ **HYBRID** (Rule-based + LLM with conversation history)

**Classification Strategy**:
1. **First Tier**: Rule-based patterns (fast, ~90% accuracy)
   - No LLM calls for common queries
   - Instant classification
   - High confidence (0.95)

2. **Second Tier**: LLM-based classification (for ambiguous queries)
   - Uses Vertex AI (`gemini-2.0-flash`) with DeepInfra fallback
   - Includes conversation history for context
   - Helps Supervisor Coordinator route correctly
   - Only used when rule-based patterns fail

**Rationale**:
- **Speed**: Rule-based patterns for fast classification of common queries
- **Accuracy**: LLM for ambiguous queries that don't match patterns
- **Context-awareness**: Conversation history improves intent detection
- **Cost-efficiency**: LLM only used when needed (ambiguous queries)
- **Reliability**: Rule-based fallback ensures deterministic results

**Benefits**:
- Better routing for complex/ambiguous queries
- Context-aware classification (uses conversation history)
- Automatic fallback (Vertex AI → DeepInfra)
- Cost-effective (LLM only for ambiguous queries)

**Trade-offs**:
- Slightly higher latency for ambiguous queries (LLM call)
- Additional LLM API costs for ambiguous queries (minimal due to fast model)
- Requires LLM client availability (gracefully degrades to rule-based if unavailable)

---

## Supervisor Coordinator Prompts

### Overview

The Supervisor Coordinator uses **LLM prompts** to plan multi-agent workflows. This is the **primary prompt injection point** for workflow orchestration.

### Prompt Injection Point

**File**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`

**Method**: `_build_planning_prompt()`

**LLM Call**: `llm_client.plan_workflow(prompt=prompt, max_agents=max_agents)`

### Prompt Structure

```python
def _build_planning_prompt(
    self,
    message: MessageContent,
    conversation_context: ConversationContext,
    available_agents: list[AgentType],
) -> str:
    """Build workflow planning prompt for LLM."""
    agents_str = ", ".join([agent.value for agent in available_agents])
    
    return f"""
You are a workflow supervisor coordinating multiple AI agents.

User Request:
{message.value}

Available Agents:
{agents_str}

Create a workflow plan with multiple agent tasks.

Respond with JSON:
{{
    "tasks": [
        {{
            "agent_type": "agent_name",
            "task_description": "what this agent should do",
            "depends_on": [0, 1]  // Task indices that must complete first
        }},
        ...
    ],
    "reasoning": "why this workflow makes sense"
}}

Guidelines:
- **CRITICAL: RESTRICTED FEATURES FOR GUEST USERS**
  * [Detailed guidelines for guest authentication...]
  
- **CRITICAL: OFF-TOPIC QUERY DETECTION**
  * [Guidelines for off-topic handling...]
  
- **Simple informational queries** → Create 1-task workflow
- **Price queries** → Use "hunter_ai" agent
- **Multi-intent queries** → Create separate tasks
- **Multi-agent queries** → Break down into subtasks
- [Extensive guidelines for agent selection...]
"""
```

### Prompt Components

**1. Role Definition**:
```
You are a workflow supervisor coordinating multiple AI agents.
```

**2. User Input Injection**:
```python
User Request:
{message.value}  # ← USER INPUT INJECTED HERE
```

**3. Available Agents**:
```python
Available Agents:
{agents_str}  # ← Dynamic agent list
```

**4. Output Format**:
```json
{
    "tasks": [...],
    "reasoning": "..."
}
```

**5. Guidelines** (Extensive, ~200 lines):
- Restricted features handling
- Off-topic query detection
- Agent selection rules
- Workflow patterns
- Dependency management
- Aggregation requirements

### Security Considerations

**User Input Injection**: `{message.value}` is injected directly into the prompt.

**Risk**: Prompt injection attacks could manipulate workflow planning.

**Mitigation**:
- Input length limits (MAX_MESSAGE_LENGTH = 500)
- Output validation (JSON schema validation)
- Agent type whitelist (only valid AgentType enum values)
- Task description sanitization

### Prompt Engineering Details

**Model**: `gemini-2.0-flash` (Vertex AI) or fallback to DeepInfra

**Temperature**: Not explicitly set (uses LLM client default, typically 0.7)

**Max Tokens**: Not explicitly set (uses LLM client default)

**Response Format**: JSON with strict schema

**Error Handling**: Falls back to CHAT agent if parsing fails

### Example Prompt (Full)

```python
"""
You are a workflow supervisor coordinating multiple AI agents.

User Request:
what type of swaps i can make? what is the price?

Available Agents:
chat, guest_auth, knowledge, hunter_ai, research, execution, risk_analyzer, portfolio, tax_optimizer, defi_yield, security_auditor, gas_optimizer

Create a workflow plan with multiple agent tasks.

[... 200+ lines of guidelines ...]

Guidelines:
- **CRITICAL: RESTRICTED FEATURES FOR GUEST USERS**
  * These features require wallet connection and authentication...
  
- **Simple informational queries** (e.g., "what is btc?") → Create 1-task workflow with "chat" agent_type
  
- **Price queries** (e.g., "what is the price of btc?") → Create 1-task workflow with "hunter_ai" agent_type
  
- **Multi-intent queries** (e.g., "price of btc and eth, and explain swaps") → Create separate tasks:
  * ONE "hunter_ai" task for ALL price queries
  * ONE "knowledge" task for informational/Anvil knowledge queries
  
- **CRITICAL**: For multi-agent workflows (3+ agents), ALWAYS add a final "chat" task that:
  * Has agent_type: "chat"
  * Has task_description: "Aggregate and summarize the results from all previous agents..."
  * Has depends_on: [list of all previous task indices]
"""
```

### Response Parsing

**File**: `supervisor_coordinator.py:create_workflow_plan()`

**Parsing Logic**:
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

### Overview

Each of the **18 specialized agents** has its own **system prompt** that defines:
- Agent role and capabilities
- Response style and format
- Domain-specific knowledge
- Tool usage instructions
- Safety guidelines

### Prompt Injection Pattern

**Common Pattern** (all agents):
```python
class SomeAgent:
    def _get_system_prompt(self, context: str = "") -> str:
        """Get system prompt for agent."""
        base_prompt = """[Agent-specific system prompt]"""
        
        # Inject dynamic context
        if context:
            base_prompt += f"\n\n{context}"
        
        return base_prompt
    
    def _build_messages(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        additional_context: str = "",
    ) -> list[dict]:
        """Build messages for LLM API."""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(additional_context),
            }
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

### Agent-Specific Prompts

#### 1. CHAT Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/chat_agent.py`

**Method**: `_get_system_prompt() -> str`

**Prompt Length**: ~400 lines

**Key Sections**:
- Role definition: "You are Anvil's AI assistant"
- Aggregation instructions (for multi-agent responses)
- Anvil knowledge base
- Restricted features handling
- Response style guidelines
- Off-topic handling

**Dynamic Context Injection**:
- None (static prompt)

**User Input Injection**:
```python
messages.append({
    "role": "user",
    "content": message.value,  # ← Direct injection
})
```

**Special Aggregation Mode**:
When aggregating multiple agent responses:
```python
if is_aggregation:
    messages.append({
        "role": "user",
        "content": f"""You are aggregating responses from multiple specialist agents.

IMPORTANT INSTRUCTIONS:
1. **PRESERVE REAL-TIME DATA**: [...]
2. **FILTER OUT AUTHENTICATION MESSAGES**: [...]
3. **PRESERVE SPECIFIC DETAILS**: [...]
[... 12 detailed instructions ...]

Agent Responses to Aggregate:
{message.value}  # ← Multiple agent responses injected here
""",
    })
```

#### 2. KNOWLEDGE Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/knowledge_agent.py`

**Method**: `_get_system_prompt(knowledge_context: str = "") -> str`

**Prompt Length**: ~500 lines

**Key Sections**:
- Role: "Anvil's Knowledge Assistant"
- Knowledge areas (Anvil Platform, DeFi Concepts, Cryptocurrencies, Blockchain)
- Critical instructions (ANSWER ONLY CURRENT QUESTION, NO TOPIC MIXING)
- Language consistency (respond in same language as question)
- Spanish terminology (lending vs borrowing)
- Off-topic handling
- NFT handling (on-topic)

**Dynamic Context Injection**:
```python
if knowledge_context:
    base_prompt += f"""
The following information from Anvil's knowledge base is relevant to this query:

{knowledge_context}  # ← Knowledge base JSON data injected here

Use this information to provide accurate, detailed responses about Anvil features and capabilities.
"""
```

**Knowledge Context Source**:
- `KnowledgeInjector.get_knowledge_for_intent()` loads JSON files from `anvil_knowledge/features/`
- Files: `overview.json`, `swap.json`, `portfolio.json`, `wallet.json`, etc.
- Context includes: feature_name, description, supported_aggregators, supported_tokens, features, etc.

**User Input Injection**:
```python
# Conversation history (filtered for relevance)
history = conversation_context.last_n_messages(2)  # Reduced from 5 to avoid topic mixing
for msg in history:
    messages.append({
        "role": msg.get("role", "user"),
        "content": msg.get("content", ""),
    })

# Current message
messages.append({
    "role": "user",
    "content": message.value + "\n\nCRITICAL: Answer ONLY this specific question. Do NOT include information about other topics.",  # ← User input + instruction suffix
})
```

#### 3. HUNTER_AI Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/hunter_ai_agent.py`

**Method**: `_get_system_prompt() -> str` (implied, not explicitly defined)

**Prompt Injection**: Market data context injected into user message

**Market Data Context**:
```python
if self._coingecko_client:
    tokens = self._extract_tokens(message.value)
    prices = await self._coingecko_client.get_prices_bulk(tokens)
    
    market_data_context = f"""
**REAL-TIME MARKET DATA FROM COINGECKO:**

{tokens[0].upper()}:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
- Market Cap: ${price.market_cap / 1e9:.2f}B
[... more price data ...]
"""
```

**User Message Construction**:
```python
user_message = f"""
{message.value}

{market_data_context}  # ← Real-time API data injected here

Analyze the market sentiment and provide price predictions based on this real-time data.
"""
```

**LLM Call**:
```python
response = await self._llm_client.chat(
    messages=[
        {"role": "system", "content": "[Hunter AI system prompt]"},
        {"role": "user", "content": user_message},  # ← Contains user input + market data
    ],
    model=self._model,
    temperature=self._temperature,
)
```

#### 4. EXECUTION Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/execution_agent_privy.py`

**Method**: `_parse_transaction_intent()` - Separate prompt for intent parsing

**Transaction Intent Parsing Prompt**:
```python
prompt = f"""Parse the transaction intent from this message. Extract the action and token details.

Message: {message.value}  # ← USER INPUT INJECTED HERE

CRITICAL: You MUST respond with valid JSON only. No markdown, no explanations, just JSON.

Identify and extract:
- action: MUST be one of "swap", "transfer", "approve", "wrap", "unwrap"
- from_token: Token symbol (e.g., "ETH", "USDC", "BTC")
- to_token: Token symbol (if swap)
- amount: Numeric amount as string
- recipient: Wallet address (if transfer, otherwise null)

Examples:
- "swap 1 ETH for USDC" → {{"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "1.0"}}
[... more examples ...]

Respond with ONLY valid JSON (no markdown code blocks, no explanations):
{{
    "action": "swap",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0",
    "confidence": 0.95
}}
"""
```

**LLM Call**:
```python
response = await self._llm_client.classify_intent(
    prompt=prompt,  # ← Prompt with user input
    model=self._model,
)
```

**Response Building Prompt** (for informational queries):
```python
async def _build_execution_response(...) -> str:
    # Check if informational query
    is_informational_query = (
        not from_token or not to_token or
        any(kw in message_lower for kw in ["what type", "what types", "what can"])
    )
    
    if is_informational_query:
        # Return predefined informational response (no LLM call)
        return """**Token Swaps on Anvil**

Anvil supports token swaps through multiple DEX aggregators:
[... predefined content ...]
"""
```

#### 5. DEFI_YIELD Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/defi_yield_agent.py`

**Prompt Injection**: APY data from DeFiLlama API

**APY Data Context**:
```python
if defi_llama_client:
    yields = await defi_llama_client.get_protocol_yields(...)
    
    yield_data_context = "\n\n**REAL-TIME APY DATA FROM DEFILLAMA:**\n\n"
    yield_data_context += "| Protocol | Pool | Chain | APY (%) | TVL | Risk Score |\n"
    yield_data_context += "|----------|------|-------|---------|-----|------------|\n"
    
    for yield_data in top_yields:
        yield_data_context += f"| {yield_data.protocol} | {yield_data.pool} | {yield_data.chain} | {yield_data.apy:.2f}% | ${yield_data.tvl_usd:,.0f} | {risk_score} |\n"
```

**System Prompt**:
```python
def _get_system_prompt(self) -> str:
    return """You are Anvil's DeFi Yield Agent, specialized in yield farming and APY optimization.

**YOUR ROLE:**
- Find best yield opportunities across DeFi protocols
- Compare APY rates (Aave, Compound, Curve, Convex, Morpho)
- Analyze liquidity pools
- Calculate impermanent loss
- Recommend yield farming strategies
- Suggest auto-compounding opportunities

**CRITICAL: PRESERVE REAL-TIME DATA**
- If you see sections marked "**REAL-TIME APY DATA FROM DEFILLAMA:**", you MUST include this data prominently
- DO NOT remove or summarize this real-time data - it is the PRIMARY source of accurate APY information
- Format the data as a markdown table for readability
- Preserve all specific numbers, APY values, and protocol names

**RESPONSE FORMAT:**
1. Start with real-time APY data table (if available)
2. Provide analysis and recommendations
3. Include risk considerations
4. End with disclaimer

**IMPORTANT:**
- Use real APY data from DeFiLlama when available
- Compare multiple protocols
- Consider TVL, risk, and impermanent loss
- Provide actionable recommendations
"""
```

**User Message with APY Data**:
```python
user_message = f"""
{message.value}

{yield_data_context}  # ← Real-time APY data injected here

Analyze these yield opportunities and provide recommendations based on this real-time data.
"""
```

#### 6. RISK_ANALYZER Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/risk_analyzer_agent.py`

**Prompt Injection**: Protocol TVL data from DeFiLlama API

**Protocol Data Context**:
```python
if defi_llama_client:
    protocol_tvl = await defi_llama_client.get_protocol_tvl(protocol_filter)
    
    risk_data_context = "\n\n**PROTOCOL DATA FROM DEFILLAMA:**\n"
    risk_data_context += f"**{protocol_filter.upper()} Protocol:**\n"
    risk_data_context += f"- Total TVL: ${protocol_tvl.tvl:,.0f}\n"
    risk_data_context += f"- Size: Very Large (Lower risk due to scale)\n"
    risk_data_context += f"- Chain Distribution: {len(protocol_tvl.chain_tvls)} chains\n"
```

**System Prompt**:
```python
def _get_system_prompt(self) -> str:
    return """You are Anvil's Risk Analyzer Agent, specialized in DeFi protocol risk assessment.

**YOUR ROLE:**
- Assess protocol risk (0-100 scale)
- Analyze smart contract risk
- Calculate liquidation risk
- Assess impermanent loss
- Evaluate concentration risk
- Analyze market volatility
- Assess counterparty risk

**CRITICAL: PRESERVE REAL-TIME DATA**
- If you see sections marked "**PROTOCOL DATA FROM DEFILLAMA:**", you MUST include this data prominently
- DO NOT remove or summarize this real-time data
- Use TVL data to inform risk scoring
- Consider protocol size, chain distribution, and historical data

**RISK SCORING SCALE:**
- 0-20: Very Low Risk (Large TVL, audited, established)
- 21-40: Low Risk (Moderate TVL, some audits)
- 41-60: Moderate Risk (Smaller TVL, limited audits)
- 61-80: High Risk (Very small TVL, unaudited)
- 81-100: Very High Risk (Experimental, high volatility)

**RESPONSE FORMAT:**
1. Protocol overview with TVL data
2. Risk score (0-100) with breakdown
3. Risk factors analysis
4. Recommendations
5. Disclaimer
"""
```

#### 7. GAS_OPTIMIZER Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/gas_optimizer_agent.py`

**Prompt Injection**: Real-time gas price data from Web3Client

**Gas Data Context**:
```python
if web3_client:
    gas_prices = await web3_client.get_gas_prices()
    
    gas_data_context = f"""
**REAL-TIME GAS PRICE DATA:**

Current Ethereum Gas Prices:
- Slow: {gas_prices.slow} gwei (estimated {gas_prices.slow_time} minutes)
- Standard: {gas_prices.standard} gwei (estimated {gas_prices.standard_time} minutes)
- Fast: {gas_prices.fast} gwei (estimated {gas_prices.fast_time} minutes)

Recommended: {recommended_tier} ({recommended_gwei} gwei)
"""
```

**System Prompt**:
```python
def _get_system_prompt(self) -> str:
    return """You are Anvil's Gas Optimizer Agent, specialized in gas fee optimization.

**YOUR ROLE:**
- Analyze current gas prices
- Recommend optimal transaction timing
- Suggest Layer 2 alternatives
- Calculate gas cost estimates
- Provide gas optimization strategies

**CRITICAL: USE REAL-TIME DATA**
- Always use real-time gas price data when available
- Consider network congestion
- Factor in transaction urgency
- Compare Layer 1 vs Layer 2 costs

**GAS PRICE TIERS:**
- Slow: Lowest cost, longest wait
- Standard: Balanced cost and speed
- Fast: Higher cost, faster confirmation

**RESPONSE FORMAT:**
1. Current gas prices (real-time data)
2. Recommended tier based on urgency
3. Cost estimates
4. Layer 2 alternatives (if applicable)
5. Optimization tips
"""
```

### Other Agents

**GUEST_AUTH Agent**:
- **Prompt**: Minimal (uses predefined messages from translation service)
- **LLM Usage**: Optional (can use LLM for feature detection, but primarily rule-based)

**RESEARCH Agent**:
- **Prompt**: Research-focused system prompt
- **Context Injection**: Perplexity search results

**PORTFOLIO Agent**:
- **Prompt**: Portfolio management system prompt
- **Context Injection**: GraphRAG results, database queries

**TAX_OPTIMIZER Agent**:
- **Prompt**: Tax optimization system prompt
- **Context Injection**: Transaction history, database queries

**SECURITY_AUDITOR Agent**:
- **Prompt**: Security analysis system prompt
- **Context Injection**: Slither analysis results, smart contract code

---

## Prompt Construction Patterns

### Pattern 1: Static System Prompt

**Used By**: Most agents (CHAT, KNOWLEDGE, DEFI_YIELD, RISK_ANALYZER, etc.)

**Structure**:
```python
def _get_system_prompt(self) -> str:
    return """[Static prompt content - 200-500 lines]
"""
```

**Characteristics**:
- Defined at class level
- No dynamic content (except optional context injection)
- Consistent across all requests
- Easy to maintain and version

### Pattern 2: Dynamic Context Injection

**Used By**: KNOWLEDGE agent, DEFI_YIELD agent, RISK_ANALYZER agent

**Structure**:
```python
def _get_system_prompt(self, context: str = "") -> str:
    base_prompt = """[Base system prompt]"""
    
    if context:
        base_prompt += f"\n\n{context}"  # ← Dynamic context injected
    
    return base_prompt
```

**Context Sources**:
- Knowledge base JSON files
- API responses (DeFiLlama, CoinGecko, 1inch)
- Database queries
- GraphRAG results

### Pattern 3: User Message Enhancement

**Used By**: HUNTER_AI, DEFI_YIELD, RISK_ANALYZER, GAS_OPTIMIZER

**Structure**:
```python
# Fetch real-time data
api_data = await fetch_api_data(...)

# Enhance user message with API data
enhanced_message = f"""
{message.value}

{api_data}  # ← API data injected into user message
"""
```

**Rationale**:
- Keeps system prompt focused on role/capabilities
- Injects real-time data into user message
- Allows LLM to process data in context of user query

### Pattern 4: Multi-Stage Prompts

**Used By**: EXECUTION agent

**Structure**:
```python
# Stage 1: Intent parsing
intent_prompt = f"""Parse transaction intent...
Message: {message.value}
"""

intent_response = await llm_client.classify_intent(intent_prompt)

# Stage 2: Response building (with parsed intent)
response_prompt = f"""Build execution response...
Intent: {intent_response}
Swap Quote: {swap_quote_context}
"""
```

**Rationale**:
- Separates intent parsing from response generation
- Allows for structured data extraction
- Enables validation between stages

### Pattern 5: Aggregation Prompts

**Used By**: CHAT agent (when aggregating multiple agent responses)

**Structure**:
```python
if is_aggregation:
    aggregation_prompt = f"""You are aggregating responses from multiple specialist agents.

IMPORTANT INSTRUCTIONS:
1. **PRESERVE REAL-TIME DATA**: [...]
2. **FILTER OUT AUTHENTICATION MESSAGES**: [...]
[... 12 detailed instructions ...]

Agent Responses to Aggregate:
{message.value}  # ← Contains all agent responses
"""
```

**Rationale**:
- Special handling for multi-agent workflows
- Preserves critical data (APY, TVL, prices)
- Filters out noise (auth messages, duplicates)

---

## Context Injection Mechanisms

### 1. Knowledge Base Injection

**Component**: `KnowledgeInjector`

**File**: `src/app/application/chat/services/knowledge_injector.py`

**Flow**:
```
User Query → Intent Detection → Knowledge File Selection → JSON Load → Context Formatting → Prompt Injection
```

**Knowledge Files**:
- `anvil_knowledge/features/overview.json`
- `anvil_knowledge/features/swap.json`
- `anvil_knowledge/features/portfolio.json`
- `anvil_knowledge/features/wallet.json`
- `anvil_knowledge/features/lending_morpho.json`
- `anvil_knowledge/features/gas_optimizer.json`
- `anvil_knowledge/features/risk_analyzer.json`

**Injection Point**:
```python
# In KnowledgeAgent._get_system_prompt()
if knowledge_context:
    base_prompt += f"""
The following information from Anvil's knowledge base is relevant to this query:

{knowledge_context}  # ← JSON data formatted as text

Use this information to provide accurate, detailed responses about Anvil features and capabilities.
"""
```

**Context Format**:
```python
def _format_knowledge_context(self, knowledge_dict: dict) -> str:
    context_parts = []
    
    if "feature_name" in knowledge_dict:
        context_parts.append(f"Feature: {knowledge_dict['feature_name']}")
    
    if "supported_aggregators" in knowledge_dict:
        context_parts.append("\n**Supported Aggregators:**")
        for agg in knowledge_dict["supported_aggregators"]:
            context_parts.append(f"- {agg['name']}: {agg['description']}")
    
    # ... more formatting ...
    
    return "\n".join(context_parts)
```

### 2. API Data Injection

**Components**: HUNTER_AI, DEFI_YIELD, RISK_ANALYZER, GAS_OPTIMIZER

**Flow**:
```
User Query → API Call (CoinGecko/DeFiLlama/Web3) → Data Formatting → User Message Enhancement
```

**Injection Pattern**:
```python
# Fetch API data
api_data = await api_client.fetch_data(...)

# Format as context
formatted_data = format_api_data(api_data)  # Markdown tables, structured text

# Inject into user message
enhanced_message = f"""
{original_user_message}

{formatted_data}  # ← API data injected here
"""
```

**Examples**:

**HUNTER_AI** (CoinGecko):
```python
market_data_context = f"""
**REAL-TIME MARKET DATA FROM COINGECKO:**

BTC:
- Current Price: $89,433.00
- 24h Change: -3.84%
- Market Cap: $1.76T
"""
```

**DEFI_YIELD** (DeFiLlama):
```python
yield_data_context = """
**REAL-TIME APY DATA FROM DEFILLAMA:**

| Protocol | Pool | Chain | APY (%) | TVL |
|----------|------|-------|---------|-----|
| Aave | USDC | Ethereum | 4.25% | $2.5B |
| Morpho | USDC | Ethereum | 5.10% | $1.2B |
"""
```

**RISK_ANALYZER** (DeFiLlama):
```python
risk_data_context = """
**PROTOCOL DATA FROM DEFILLAMA:**

**AAVE Protocol:**
- Total TVL: $12,500,000,000
- Size: Very Large (Lower risk due to scale)
- Chain Distribution: 5 chains
```

### 3. Conversation History Injection

**Component**: All agents

**Flow**:
```
Conversation Context → Last N Messages → Message Array Construction
```

**Injection Pattern**:
```python
def _build_messages(
    self,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> list[dict]:
    messages = [
        {"role": "system", "content": self._get_system_prompt()}
    ]
    
    # Inject conversation history
    history = conversation_context.last_n_messages(5)  # Last 5 messages
    for msg in history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),  # ← Previous messages injected
        })
    
    # Inject current message
    messages.append({
        "role": "user",
        "content": message.value,  # ← Current user input
    })
    
    return messages
```

**History Filtering** (KNOWLEDGE agent):
```python
# For simple questions, reduce history to avoid topic mixing
is_simple_question = message.value.lower().startswith(("what is", "que es"))

if not is_simple_question:
    history = conversation_context.last_n_messages(1)  # Only last message
    # Filter for relevance
    for msg in history:
        if len(history) == 1 or any(word in msg_lower for word in current_lower.split()[:3]):
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
```

### 4. Multi-Agent Response Injection

**Component**: CHAT agent (aggregation mode)

**Flow**:
```
Multiple Agent Responses → Aggregation Message Construction → CHAT Agent Prompt
```

**Injection Pattern**:
```python
# In SupervisorCoordinator._build_aggregation_message()
parts = [
    "Aggregate and summarize the following responses from specialist agents.",
    "Remove duplicates, create a coherent single response...",
    "",
    "Agent Responses:",
    "",
]

for task in other_tasks:
    if isinstance(task.result, AgentResponse):
        content = task.result.content
    parts.append(f"--- Response from {task.agent_type.value.upper()} Agent ---")
    parts.append(content)  # ← Agent response injected
    parts.append("")

aggregation_message = "\n".join(parts)

# Pass to CHAT agent
chat_agent_message = MessageContent(aggregation_message)
```

**CHAT Agent Processing**:
```python
# CHAT agent detects aggregation mode
is_aggregation = "agent response" in message.value.lower()

if is_aggregation:
    messages.append({
        "role": "user",
        "content": f"""You are aggregating responses from multiple specialist agents.

[... aggregation instructions ...]

Agent Responses to Aggregate:
{message.value}  # ← All agent responses injected here
""",
    })
```

---

## Security & Prompt Injection Prevention

### Threat Model

**Attack Vectors**:
1. **User Input Injection**: Malicious user input in `message.value`
2. **Context Injection**: Manipulated conversation history
3. **Knowledge Base Injection**: Compromised JSON knowledge files
4. **API Data Injection**: Manipulated API responses (less likely)

### Current Mitigations

#### 1. Input Length Limits

**Location**: `send_guest_message.py`, `conversations_router.py`

**Implementation**:
```python
MAX_MESSAGE_LENGTH = 500  # Characters

if len(content) > MAX_MESSAGE_LENGTH:
    raise ValueError("Message too long")
```

**Effectiveness**: ⚠️ **Limited** - Prevents extremely long prompts but not injection

#### 2. Input Sanitization

**Location**: Message validation (implicit in Pydantic schemas)

**Implementation**:
```python
class GuestChatRequest(BaseModel):
    content: str = Field(..., max_length=500)  # Pydantic validation
    language: str = Field(default="en", pattern="^(en|es|pt|zh)$")
```

**Effectiveness**: ⚠️ **Limited** - Validates length/format but doesn't sanitize content

#### 3. Output Validation

**Location**: Supervisor Coordinator response parsing

**Implementation**:
```python
# Validate agent type (whitelist)
try:
    agent_type = AgentType[agent_type_str.upper()]  # Enum validation
except KeyError:
    agent_type = AgentType.CHAT  # Fallback to safe default
```

**Effectiveness**: ✅ **Good** - Prevents invalid agent types

#### 4. JSON Schema Validation

**Location**: Supervisor Coordinator, Execution Agent

**Implementation**:
```python
# Supervisor response must be valid JSON
response = await llm_client.plan_workflow(prompt=prompt, ...)

# Validate structure
if not isinstance(response, dict):
    raise ValueError("Invalid response format")

tasks = response.get("tasks", [])
if not isinstance(tasks, list):
    raise ValueError("Invalid tasks format")
```

**Effectiveness**: ✅ **Good** - Prevents malformed workflow plans

### Recommended Enhancements

#### 1. Input Sanitization

**Proposed**:
```python
def sanitize_user_input(content: str) -> str:
    """Sanitize user input to prevent prompt injection."""
    # Remove prompt injection patterns
    patterns_to_remove = [
        r"ignore (previous|all) (instructions|prompts?)",
        r"system:",
        r"assistant:",
        r"user:",
        r"\[INST\]",
        r"\[/INST\]",
    ]
    
    sanitized = content
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    # Escape special characters if needed
    # (depends on LLM provider)
    
    return sanitized.strip()
```

#### 2. Prompt Delimiters

**Proposed**:
```python
def _build_planning_prompt(self, message: MessageContent, ...) -> str:
    # Use clear delimiters
    return f"""
You are a workflow supervisor coordinating multiple AI agents.

=== USER REQUEST (DO NOT MODIFY) ===
{message.value}
=== END USER REQUEST ===

Available Agents:
{agents_str}

[... rest of prompt ...]
"""
```

#### 3. Role-Based Prompt Separation

**Proposed**:
```python
# Separate system and user roles clearly
messages = [
    {
        "role": "system",
        "content": system_prompt,  # Never includes user input
    },
    {
        "role": "user",
        "content": user_message,  # User input in separate message
    }
]
```

**Current Status**: ✅ **Already implemented** - All agents use role separation

#### 4. Prompt Injection Detection

**Proposed**:
```python
def detect_prompt_injection(content: str) -> bool:
    """Detect potential prompt injection attempts."""
    injection_patterns = [
        r"ignore (previous|all) (instructions|prompts?)",
        r"forget (everything|all|previous)",
        r"new (instructions|prompt|task)",
        r"system:",
        r"assistant:",
        r"\[INST\]",
    ]
    
    content_lower = content.lower()
    for pattern in injection_patterns:
        if re.search(pattern, content_lower):
            return True
    
    return False

# Usage
if detect_prompt_injection(message.value):
    logger.warning("Potential prompt injection detected")
    # Reject or sanitize
```

---

## Prompt Engineering Best Practices

### Current Practices

#### 1. Clear Role Definition

**Example** (KNOWLEDGE agent):
```
You are Anvil's Knowledge Assistant, a specialized educational agent for DeFi and crypto knowledge.
```

**Benefit**: LLM understands its role and constraints

#### 2. Explicit Instructions

**Example** (KNOWLEDGE agent):
```
**CRITICAL: ANSWER ONLY THE CURRENT QUESTION**
- Answer ONLY the user's current question - do NOT include information about topics from previous messages
- Do NOT repeat or summarize previous conversation topics unless explicitly asked
```

**Benefit**: Prevents topic mixing and duplication

#### 3. Structured Guidelines

**Example** (Supervisor Coordinator):
```
Guidelines:
- **CRITICAL: RESTRICTED FEATURES FOR GUEST USERS**
  * [Detailed rules...]
- **Simple informational queries** → Create 1-task workflow
- **Price queries** → Use "hunter_ai" agent
```

**Benefit**: Clear decision tree for LLM

#### 4. Example-Driven Learning

**Example** (EXECUTION agent):
```
Examples:
- "swap 1 ETH for USDC" → {"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "1.0"}
- "I want to swap 0.5 ETH to USDC" → {"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "0.5"}
```

**Benefit**: LLM learns from examples

#### 5. Output Format Specification

**Example** (Supervisor Coordinator):
```
Respond with JSON:
{
    "tasks": [
        {
            "agent_type": "agent_name",
            "task_description": "what this agent should do",
            "depends_on": [0, 1]
        }
    ],
    "reasoning": "why this workflow makes sense"
}
```

**Benefit**: Structured, parseable output

### Recommended Improvements

#### 1. Prompt Versioning

**Proposed**:
```python
PROMPT_VERSION = "v2.1"  # Track prompt versions

def _get_system_prompt(self) -> str:
    return f"""You are Anvil's Knowledge Assistant (Prompt Version: {PROMPT_VERSION}).

[... prompt content ...]
"""
```

**Benefit**: Track prompt changes, A/B testing

#### 2. Prompt Templates

**Proposed**:
```python
# Store prompts in separate files
PROMPT_TEMPLATES = {
    "knowledge_base": load_prompt_template("prompts/knowledge_agent.txt"),
    "supervisor_planning": load_prompt_template("prompts/supervisor_planning.txt"),
}

def _get_system_prompt(self) -> str:
    template = PROMPT_TEMPLATES["knowledge_base"]
    return template.format(
        knowledge_context=knowledge_context,
        # ... other variables
    )
```

**Benefit**: Easier maintenance, version control

#### 3. Prompt Testing

**Proposed**:
```python
# Unit tests for prompts
def test_knowledge_agent_prompt():
    agent = KnowledgeAgent(...)
    prompt = agent._get_system_prompt()
    
    assert "Anvil's Knowledge Assistant" in prompt
    assert "CRITICAL: ANSWER ONLY THE CURRENT QUESTION" in prompt
    assert len(prompt) < 10000  # Reasonable length
```

**Benefit**: Ensure prompt quality, catch regressions

#### 4. Prompt Metrics

**Proposed**:
```python
# Track prompt performance
prompt_metrics = {
    "prompt_version": "v2.1",
    "prompt_length": len(prompt),
    "instruction_count": prompt.count("**"),
    "example_count": prompt.count("Example:"),
    "response_quality_score": calculate_quality(response),
}
```

**Benefit**: Data-driven prompt optimization

---

## Implementation Details

### Guest/Message Prompt Flow

**File**: `src/app/application/guest/commands/send_guest_message.py`

**Flow**:
```
1. User Message Received
   ↓
2. Intent Detection (Rule-based, NO prompts)
   ↓
3. Distillation Pass (Rule-based, NO prompts)
   ↓
4. Supervisor Coordinator
   ├─ _build_planning_prompt()  ← PROMPT INJECTION POINT 1
   ├─ llm_client.plan_workflow(prompt)
   └─ Parse workflow plan
   ↓
5. Agent Orchestration
   ├─ For each agent task:
   │  ├─ Agent._get_system_prompt()  ← PROMPT INJECTION POINT 2
   │  ├─ Agent._build_messages()  ← PROMPT INJECTION POINT 3
   │  ├─ llm_client.chat(messages)
   │  └─ Collect AgentResponse
   └─ If multiple agents:
      └─ CHAT agent aggregation  ← PROMPT INJECTION POINT 4
   ↓
6. Response Aggregation
   ↓
7. Return Final Response
```

### Conversations/Message Prompt Flow

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Flow**: **IDENTICAL** to guest/message (same structure)

**Differences**:
- User authentication (JWT) instead of IP-based
- Conversation ownership verification
- Enhanced rate limits
- Wallet address context

**Prompt Injection Points**: **SAME** as guest/message

### Prompt Injection Code Locations

| Component | File | Method | Line Range |
|-----------|------|--------|------------|
| **Supervisor Coordinator** | `supervisor_coordinator.py` | `_build_planning_prompt()` | 582-674 |
| **CHAT Agent** | `chat_agent.py` | `_get_system_prompt()` | 311-310 |
| **CHAT Agent** | `chat_agent.py` | `_build_messages()` | 178-242 |
| **KNOWLEDGE Agent** | `knowledge_agent.py` | `_get_system_prompt()` | 352-500 |
| **KNOWLEDGE Agent** | `knowledge_agent.py` | `_build_messages()` | 308-350 |
| **HUNTER_AI Agent** | `hunter_ai_agent.py` | `execute()` | 56-330 |
| **EXECUTION Agent** | `execution_agent_privy.py` | `_parse_transaction_intent()` | 285-348 |
| **DEFI_YIELD Agent** | `defi_yield_agent.py` | `execute()` | 65-330 |
| **RISK_ANALYZER Agent** | `risk_analyzer_agent.py` | `execute()` | 66-286 |
| **GAS_OPTIMIZER Agent** | `gas_optimizer_agent.py` | `execute()` | 65-250 |

### Prompt Construction Examples

#### Example 1: Supervisor Planning Prompt

**Input**:
```python
message = MessageContent("what type of swaps i can make? what is the price?")
available_agents = [AgentType.KNOWLEDGE, AgentType.HUNTER_AI, AgentType.CHAT]
```

**Generated Prompt**:
```
You are a workflow supervisor coordinating multiple AI agents.

User Request:
what type of swaps i can make? what is the price?

Available Agents:
knowledge, hunter_ai, chat

Create a workflow plan with multiple agent tasks.

[... 200+ lines of guidelines ...]

Guidelines:
- **Multi-intent queries** (e.g., "price of btc and eth, and explain swaps") → Create separate tasks:
  * ONE "hunter_ai" task for ALL price queries
  * ONE "knowledge" task for informational/Anvil knowledge queries
  * **IMPORTANT**: For "what type of swaps" or "what swaps can I make" → Use "knowledge" agent (informational), NOT "execution" agent
```

**LLM Response**:
```json
{
    "tasks": [
        {
            "agent_type": "knowledge",
            "task_description": "Explain the different types of swaps available in DeFi",
            "depends_on": []
        },
        {
            "agent_type": "hunter_ai",
            "task_description": "Provide the current price of the tokens involved in the swap",
            "depends_on": [0]
        },
        {
            "agent_type": "chat",
            "task_description": "Aggregate and summarize the results from all previous agents",
            "depends_on": [0, 1]
        }
    ],
    "reasoning": "User asked two questions: swap types (informational) and prices (data). Knowledge agent handles swap types, Hunter AI handles prices, Chat agent aggregates."
}
```

#### Example 2: Knowledge Agent Prompt

**Input**:
```python
message = MessageContent("what type of swaps i can make?")
knowledge_context = """
Feature: Token Swap
Description: Execute instant token swaps across multiple DEX aggregators

Supported Aggregators:
- 1inch: Leading DEX aggregator with smart routing across 100+ liquidity sources (Chains: Ethereum, Polygon, Arbitrum, Optimism, Base)
- Hyperliquid: High-performance perpetual futures exchange with sub-second execution (Chains: Hyperliquid L1)
- UniswapX: Uniswap's Dutch auction-based swap protocol with automatic routing (Chains: Ethereum, Polygon, Arbitrum, Optimism)
- LiFi: Cross-chain bridge and swap aggregator for seamless multi-chain swaps (Chains: Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche, BSC)

Supported Tokens:
Major tokens: BTC, WBTC, ETH, USDC, USDT, DAI, SOL, MATIC, AVAX, LINK
Total: 100+ tokens across multiple chains
"""
```

**Generated Messages**:
```python
[
    {
        "role": "system",
        "content": """You are Anvil's Knowledge Assistant, a specialized educational agent for DeFi and crypto knowledge.

**YOUR ROLE:**
- Provide accurate, educational information about DeFi, crypto, blockchain, and Web3
- Explain Anvil platform features and capabilities
[... 400+ lines of system prompt ...]

The following information from Anvil's knowledge base is relevant to this query:

Feature: Token Swap
Description: Execute instant token swaps across multiple DEX aggregators

Supported Aggregators:
- 1inch: Leading DEX aggregator...
- Hyperliquid: High-performance...
[... knowledge context ...]

Use this information to provide accurate, detailed responses about Anvil features and capabilities.
"""
    },
    {
        "role": "user",
        "content": "what type of swaps i can make?\n\nCRITICAL: Answer ONLY this specific question. Do NOT include information about other topics."
    }
]
```

#### Example 3: Hunter AI Prompt with Market Data

**Input**:
```python
message = MessageContent("what is the price of BTC?")
tokens = ["bitcoin"]
prices = {
    "bitcoin": PriceData(
        usd=89433.00,
        usd_24h_change=-3.84,
        market_cap=1760000000000,
        volume_24h=25000000000,
    )
}
```

**Generated Messages**:
```python
[
    {
        "role": "system",
        "content": """[Hunter AI system prompt - market sentiment analysis]"""
    },
    {
        "role": "user",
        "content": """what is the price of BTC?

**REAL-TIME MARKET DATA FROM COINGECKO:**

BITCOIN:
- Current Price: $89,433.00
- 24h Change: -3.84%
- Market Cap: $1.76T
- 24h Volume: $25.00B

Analyze the market sentiment and provide price predictions based on this real-time data.
"""
    }
]
```

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

3. **Prompt Injection Detection**:
   - Real-time detection of injection attempts
   - Automatic sanitization
   - Alert system for security team

4. **Prompt Optimization**:
   - Automated prompt testing
   - Performance metrics tracking
   - LLM response quality scoring

5. **Context Compression**:
   - Summarize long conversation history
   - Compress knowledge base context
   - Optimize token usage

### Architecture Evolution

**Current**: Prompts embedded in code
**Future**: External prompt management system

**Proposed Structure**:
```
prompts/
├── v1/
│   ├── supervisor_planning.txt
│   ├── chat_agent.txt
│   ├── knowledge_agent.txt
│   └── ...
├── v2/
│   ├── supervisor_planning.txt
│   └── ...
└── active/
    └── [symlinks to current versions]
```

**Benefits**:
- Easier prompt updates (no code changes)
- Version control for prompts
- A/B testing capabilities
- Prompt analytics

---

## Conclusion

The Anvil messaging system uses **strategic prompt injection** across three primary components:

1. **Distillation Engine**: Rule-based (no prompts) - Fast, cost-effective
2. **Supervisor Coordinator**: LLM-based workflow planning - Intelligent orchestration
3. **Agent Squad**: 18 specialized agents with domain-specific prompts - Expert responses

**Key Strengths**:
- Clear separation of concerns
- Dynamic context injection (knowledge base, API data)
- Comprehensive prompt engineering
- Security considerations (input validation, output parsing)

**Areas for Improvement**:
- Enhanced prompt injection detection
- Prompt versioning and management
- Automated prompt testing
- Context compression for efficiency

**Security Status**: ⚠️ **Needs Enhancement**
- Current mitigations are basic (length limits, output validation)
- Recommended: Input sanitization, prompt injection detection, prompt delimiters

---

## References

- **Supervisor Coordinator**: `src/app/domain/services/agent_squad/supervisor_coordinator.py`
- **Agent Implementations**: `src/app/infrastructure/adapters/agent_squad/agents/`
- **Knowledge Injector**: `src/app/application/chat/services/knowledge_injector.py`
- **Distillation Engine**: `src/app/domain/services/distillation/engine.py`
- **Guest Message Handler**: `src/app/application/guest/commands/send_guest_message.py`
- **Conversations Router**: `src/app/presentation/http/controllers/chat/conversations_router.py`
- **CTO Methodology**: `cto.md`

---

*Document Version: 1.0*  
*Last Updated: 2026-01-20*  
*Author: Anvil Engineering Team*  
*Review Status: CEO Review Pending*

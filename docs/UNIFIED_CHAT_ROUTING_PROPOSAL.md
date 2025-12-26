# Unified Chat Routing - Intelligent Message Routing Proposal

This document explains all existing chat endpoints and proposes a unified routing architecture that intelligently routes user messages to the appropriate backend based on detected intent.

---

## Table of Contents

1. [Current Endpoints Overview](#1-current-endpoints-overview)
2. [Unified Routing Proposal](#2-unified-routing-proposal)
3. [Implementation Architecture](#3-implementation-architecture)
4. [Benefits](#4-benefits)
5. [Migration Strategy](#5-migration-strategy)

---

## 1. Current Endpoints Overview

### 1.1 Regular Chat Endpoint

**Endpoint**: `POST /api/v1/user/chat/conversations/{conversation_id}/messages`

**Implementation**: `src/app/application/chat/commands/send_message.py`

**Purpose**: Traditional chat with conversation history and tool integration.

**Features**:
- ✅ **Persistent conversation history** (database-stored)
- ✅ **Tool integration** (Hunter AI, ULTRA tools)
- ✅ **Context awareness** (full conversation history)
- ✅ **WebSocket broadcasting** (real-time updates)
- ✅ **Single agent** (ChatAgentOpenAI)
- ✅ **Keyword-based tool detection**

**Current Tool Detection Logic**:
```python
# Detects keywords in user message:
# - "sentiment", "social", "buzz" → Hunter Sentiment Analysis
# - "predict", "forecast", "future" → Hunter Price Prediction
# - "risk", "safe", "risky" → Hunter Risk Analysis
# - "buy", "sell", "trade" → Hunter Trading Signals
# - "pattern", "chart", "technical" → Hunter Pattern Recognition
# - "flash loan", "borrow" → ULTRA Flash Loans
# - "arbitrage", "opportunity" → ULTRA Arbitrage Discovery
# - "mev", "front-run" → ULTRA MEV Protection
```

**Flow**:
```
User Message → Save to DB
            → Agent Gateway (LLM)
            → Keyword Detection
            → Execute Tools (if detected)
            → Combine Response + Tool Results
            → Save Agent Message
            → WebSocket Broadcast
            → Return Response
```

**Use Cases**:
- General Q&A about crypto/DeFi
- Multi-turn conversations
- Token analysis with Hunter AI
- Arbitrage discovery with ULTRA

---

### 1.2 Agent Squad Message Endpoint

**Endpoint**: `POST /api/v1/user/chat/agent-squad/messages`

**Implementation**: `src/app/application/agent_squad/commands/send_agent_squad_message.py`

**Purpose**: Intent-based routing to 18 specialized AI agents.

**Features**:
- ✅ **Intent classification** (LLM-powered)
- ✅ **18 specialist agents** (yield, risk, security, gas, etc.)
- ✅ **Stateless** (no conversation history)
- ✅ **Force agent selection** (optional)
- ✅ **Telemetry tracking** (tokens, latency)

**Agent Types**:
1. **chat** - General conversation
2. **hunter_ai** - Market sentiment & predictions
3. **research** - Deep protocol analysis
4. **execution** - Transaction execution
5. **risk_analyzer** - Risk assessment
6. **portfolio** - Portfolio optimization
7. **tax_optimizer** - Tax strategies
8. **defi_yield** - Yield farming
9. **security_auditor** - Smart contract security
10. **gas_optimizer** - Gas optimization
11. **compliance_monitor** - AML/KYC (enterprise)
12. **multisig_coordinator** - Multi-sig treasury (enterprise)
13. **alert_monitoring** - Real-time alerts (enterprise)
14. **crisis_manager** - Emergency response (enterprise)
15. **bridge_crosschain** - Cross-chain operations (advanced)
16. **lending_borrowing** - Leverage strategies (advanced)
17. **nft_asset_manager** - NFT portfolio (advanced)
18. **dao_governance** - DAO governance (advanced)

**Flow**:
```
User Message → Intent Classifier (LLM)
            → Agent Selection (based on intent)
            → Specialist Agent Processing
            → Return Response + Metadata
```

**Use Cases**:
- "What's the best yield for USDC?" → **defi_yield**
- "Is Aave safe?" → **risk_analyzer**
- "Optimize gas for Uniswap" → **gas_optimizer**
- "What's ETH sentiment?" → **hunter_ai**

---

### 1.3 Agent Squad Supervisor Endpoint

**Endpoint**: `POST /api/v1/user/chat/agent-squad/supervisor`

**Implementation**: `src/app/application/agent_squad/commands/execute_supervisor_workflow.py`

**Purpose**: Multi-agent orchestration for complex tasks.

**Features**:
- ✅ **Task decomposition** (breaks complex tasks into subtasks)
- ✅ **Multi-agent coordination** (supervisor orchestrates multiple agents)
- ✅ **Parallel execution** (agents work simultaneously)
- ✅ **Result aggregation** (combines outputs)
- ✅ **Dependency management** (respects task dependencies)

**Flow**:
```
Complex Task → Supervisor Analyzes Task
            → Breaks into Subtasks
            → Assigns Subtasks to Specialist Agents
            → Agents Execute in Parallel (where possible)
            → Supervisor Aggregates Results
            → Returns Comprehensive Response
```

**Example**:
```json
{
  "complex_task": "Create a balanced $50k DeFi portfolio on Ethereum"
}
```

**Supervisor Workflow**:
1. **Research Agent**: Find top protocols (Aave, Uniswap, Curve)
2. **Risk Agent**: Assess risks for each protocol
3. **Portfolio Agent**: Create allocation strategy (40% Aave, 30% Uniswap, 30% Curve)
4. **Gas Optimizer**: Estimate gas costs for deployment
5. **Chat Agent**: Summarize and explain strategy

**Use Cases**:
- Complex portfolio creation
- Multi-protocol strategy analysis
- Cross-chain migration planning
- Comprehensive risk assessments

---

### 1.4 List Agents Endpoint

**Endpoint**: `GET /api/v1/user/chat/agent-squad/agents`

**Implementation**: `src/app/application/agent_squad/queries/get_enabled_agents.py`

**Purpose**: List all available agents based on user's subscription tier.

**Response**:
```json
{
  "agents": [
    {
      "agent_type": "chat",
      "name": "Chat Agent",
      "description": "General conversation and Q&A",
      "model": "gpt-4o-mini",
      "temperature": 0.7,
      "enabled": true,
      "is_enterprise": false
    }
  ],
  "total": 18,
  "core_agents": 10,
  "enterprise_agents": 8
}
```

**Subscription Tiers**:
- **Free**: 5 agents (chat, hunter_ai, research, portfolio, gas_optimizer)
- **Pro**: 10 agents (all core agents)
- **Enterprise**: 18 agents (all agents)

---

### 1.5 GraphRAG Search Protocols Endpoint

**Endpoint**: `POST /api/v1/user/chat/search-protocols`

**Implementation**: `src/app/application/chat/graph_search_handler.py`

**Purpose**: Search DeFi protocols using GraphRAG hybrid search.

**Features**:
- ✅ **Hybrid search** (semantic embeddings + knowledge graph)
- ✅ **Natural language queries** (extracts intent from message)
- ✅ **User preference filtering** (risk tolerance, chains, categories)
- ✅ **Relevance explanations** (why each protocol matched)
- ✅ **Contextual recommendations** (suggestions based on results)

**Request**:
```json
{
  "conversation_id": "abc-123",
  "query": "Find low-risk staking protocols on Ethereum with high TVL",
  "user_preferences": {
    "risk_tolerance": "conservative",
    "preferred_chains": ["Ethereum"],
    "preferred_categories": ["Staking"]
  },
  "limit": 5
}
```

**Response**:
```json
{
  "results": [
    {
      "protocol_id": "lido-v2",
      "protocol_name": "Lido V2",
      "similarity_score": 0.95,
      "risk_score": 2.1,
      "risk_level": "LOW",
      "tvl": 9500000000,
      "apy": 3.8,
      "audit_count": 12,
      "description": "Liquid staking protocol for Ethereum",
      "category": "Staking",
      "chain": "Ethereum",
      "why_relevant": "Staking protocol as requested; Deployed on Ethereum; Low-risk as preferred; High TVL ($9.5B); Well audited (12 audits)"
    }
  ],
  "search_context": "Found 5 protocols that are low-risk, staking, on Ethereum.",
  "recommendations": [
    "All protocols meet your criteria - review details before selecting"
  ]
}
```

**Use Cases**:
- Protocol discovery
- Finding protocols by category/chain/risk
- User-specific recommendations

---

### 1.6 GraphRAG Risk Analysis Endpoint

**Endpoint**: `POST /api/v1/user/chat/analyze-risk`

**Implementation**: `src/app/application/chat/risk_insights_handler.py` (inferred)

**Purpose**: Comprehensive risk analysis for specific protocol and operation.

**Request**:
```json
{
  "conversation_id": "abc-123",
  "protocol_name": "Aave V3",
  "operation_type": "supply",
  "amount_usd": 50000
}
```

**Response**:
```json
{
  "risk_analysis": {
    "protocol_id": "aave-v3",
    "protocol_name": "Aave V3",
    "risk_score": 2.5,
    "risk_level": "LOW",
    "confidence": 0.92,
    "contributing_factors": [
      {
        "factor": "Smart Contract Risk",
        "impact": 0.8,
        "description": "12+ audits, battle-tested for 3+ years",
        "is_critical": false
      },
      {
        "factor": "Liquidity Risk",
        "impact": 0.3,
        "description": "High TVL ($8.5B) provides deep liquidity",
        "is_critical": false
      }
    ],
    "recommendations": [
      "Consider diversifying across multiple protocols",
      "Monitor utilization rates to ensure liquidity"
    ],
    "should_warn": false,
    "warning_message": null
  },
  "alternatives": [
    {
      "protocol_id": "compound-v3",
      "protocol_name": "Compound V3",
      "similarity_score": 0.89,
      "risk_score": 2.8,
      "risk_level": "LOW",
      "tvl": 3200000000,
      "apy": 4.2,
      "why_better": "Similar risk profile with slightly higher APY"
    }
  ],
  "contextual_message": "Aave V3 is a low-risk protocol for your $50k supply operation. Consider alternatives for diversification."
}
```

**Use Cases**:
- Pre-transaction risk assessment
- Protocol safety validation
- Finding safer alternatives

---

### 1.7 GraphRAG Similar Protocols Endpoint

**Endpoint**: `POST /api/v1/user/chat/similar-protocols`

**Implementation**: `src/app/application/chat/graph_search_handler.py`

**Purpose**: Find protocols similar to a given protocol.

**Request**:
```json
{
  "conversation_id": "abc-123",
  "protocol_name": "Uniswap",
  "limit": 5
}
```

**Response**:
```json
{
  "base_protocol": {
    "protocol_id": "uniswap-v3",
    "protocol_name": "Uniswap V3",
    "risk_score": 2.1,
    "risk_level": "LOW",
    "tvl": 5500000000,
    "category": "DEX"
  },
  "similar_protocols": [
    {
      "protocol_id": "sushiswap",
      "protocol_name": "SushiSwap",
      "similarity_score": 0.91,
      "risk_score": 2.8,
      "risk_level": "LOW",
      "tvl": 1800000000,
      "why_similar": "High semantic match; DEX protocol as requested; Deployed on Ethereum; High TVL ($1.8B)"
    }
  ]
}
```

**Use Cases**:
- Finding protocol alternatives
- Migration planning
- Portfolio diversification

---

## 2. Unified Routing Proposal

### 2.1 The Vision

**Create a single intelligent chat endpoint** that automatically routes messages to the appropriate backend based on detected intent:

```
POST /api/v1/user/chat/conversations/{conversation_id}/messages
```

**Smart Routing Logic**:
```
User Message → Intent Detector
            → Route to appropriate handler:
               - GraphRAG Search (protocol discovery)
               - GraphRAG Risk Analysis (risk assessment)
               - GraphRAG Similar Protocols (find alternatives)
               - Agent Squad (specialist tasks)
               - Supervisor Workflow (complex multi-step)
               - Regular Chat (general conversation)
            → Process with selected handler
            → Save to conversation history
            → Return unified response
```

---

### 2.2 Intent Classification

**Use AI-powered intent classification** to detect user intent and route accordingly.

#### Intent Categories

**1. PROTOCOL_SEARCH** → GraphRAG Search
```
Patterns:
- "find protocols for..."
- "search for DEXs..."
- "what protocols offer..."
- "show me staking protocols..."
- "low-risk lending on Ethereum"

Example: "Find low-risk staking protocols on Ethereum"
→ Routes to: GraphRAG Search Protocols
```

**2. RISK_ASSESSMENT** → GraphRAG Risk Analysis
```
Patterns:
- "is [protocol] safe?"
- "analyze risk of [protocol]"
- "should I use [protocol]?"
- "how risky is [protocol]?"
- "risk assessment for [protocol]"

Example: "Is Aave safe for supplying $50k?"
→ Routes to: GraphRAG Risk Analysis
```

**3. SIMILAR_PROTOCOLS** → GraphRAG Similar Protocols
```
Patterns:
- "similar to [protocol]"
- "alternatives to [protocol]"
- "protocols like [protocol]"
- "what's similar to [protocol]?"
- "competitors of [protocol]"

Example: "What's similar to Uniswap?"
→ Routes to: GraphRAG Similar Protocols
```

**4. SPECIALIST_TASK** → Agent Squad
```
Patterns:
- "best yield for [token]" → defi_yield agent
- "optimize gas for..." → gas_optimizer agent
- "tax implications..." → tax_optimizer agent
- "security audit..." → security_auditor agent
- "portfolio strategy..." → portfolio agent

Example: "What's the best USDC yield on Arbitrum?"
→ Routes to: Agent Squad (defi_yield agent)
```

**5. COMPLEX_WORKFLOW** → Supervisor
```
Patterns:
- "create a portfolio..."
- "comprehensive analysis..."
- "build a strategy..."
- "plan migration from..."
- Multiple-step instructions

Example: "Create a balanced $50k DeFi portfolio"
→ Routes to: Supervisor Workflow
```

**6. GENERAL_CONVERSATION** → Regular Chat
```
Patterns:
- General questions
- Educational content
- Explanations
- Follow-up questions
- Casual chat

Example: "What is impermanent loss?"
→ Routes to: Regular Chat (with conversation history)
```

---

### 2.3 Unified Response Format

**Standardized response structure** that works for all handlers:

```typescript
interface UnifiedChatResponse {
  // Standard fields (always present)
  user_message: MessageResponse
  agent_message: MessageResponse

  // Routing metadata
  routing: {
    intent: string              // Detected intent
    confidence: number          // 0-1
    handler: string             // Which handler processed it
    agent_used?: string         // If Agent Squad, which agent
  }

  // Optional enrichment data (based on handler)
  enrichment?: {
    // For GraphRAG handlers
    protocols?: ProtocolSearchResult[]
    risk_analysis?: RiskAnalysis
    similar_protocols?: SimilarProtocolInfo[]

    // For Agent Squad
    tools_used?: string[]
    tokens_consumed?: number
    latency_ms?: number

    // For Supervisor
    workflow_tasks?: WorkflowTaskResponse[]
    agents_involved?: string[]
  }
}
```

**Example Responses**:

**1. GraphRAG Search Response**:
```json
{
  "user_message": {
    "id": "msg-001",
    "content": "Find low-risk staking protocols on Ethereum",
    "role": "user"
  },
  "agent_message": {
    "id": "msg-002",
    "content": "I found 5 low-risk staking protocols on Ethereum:\n\n1. **Lido V2** - 3.8% APY, $9.5B TVL...",
    "role": "assistant"
  },
  "routing": {
    "intent": "PROTOCOL_SEARCH",
    "confidence": 0.95,
    "handler": "graphrag_search"
  },
  "enrichment": {
    "protocols": [
      {
        "protocol_id": "lido-v2",
        "protocol_name": "Lido V2",
        "similarity_score": 0.95,
        "risk_score": 2.1,
        "risk_level": "LOW",
        "tvl": 9500000000,
        "apy": 3.8
      }
    ]
  }
}
```

**2. Agent Squad Response**:
```json
{
  "user_message": {
    "id": "msg-003",
    "content": "What's the best USDC yield on Arbitrum?",
    "role": "user"
  },
  "agent_message": {
    "id": "msg-004",
    "content": "🌾 Best USDC Yields on Arbitrum:\n\n1. Aave V3 - 5.2% APY...",
    "role": "assistant"
  },
  "routing": {
    "intent": "SPECIALIST_TASK",
    "confidence": 0.92,
    "handler": "agent_squad",
    "agent_used": "defi_yield"
  },
  "enrichment": {
    "tools_used": ["aave_api", "gmx_api", "curve_api"],
    "tokens_consumed": 450,
    "latency_ms": 1850
  }
}
```

**3. Regular Chat Response**:
```json
{
  "user_message": {
    "id": "msg-005",
    "content": "What is impermanent loss?",
    "role": "user"
  },
  "agent_message": {
    "id": "msg-006",
    "content": "Impermanent loss (IL) is a phenomenon that occurs when...",
    "role": "assistant"
  },
  "routing": {
    "intent": "GENERAL_CONVERSATION",
    "confidence": 0.88,
    "handler": "regular_chat"
  }
}
```

---

## 3. Implementation Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Chat Router (FastAPI)                  │
│  POST /api/v1/user/chat/conversations/{id}/messages    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           UnifiedChatOrchestrator (NEW)                 │
│                                                         │
│  1. Intent Detection (LLM-powered)                      │
│  2. Route to appropriate handler                        │
│  3. Process with handler                                │
│  4. Save to conversation history                        │
│  5. Return unified response                             │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
┌──────────────┐ ┌─────────┐ ┌──────────┐ ┌─────────────┐
│   GraphRAG   │ │  Agent  │ │Supervisor│ │Regular Chat │
│   Handlers   │ │  Squad  │ │ Workflow │ │   Handler   │
│              │ │         │ │          │ │             │
│ - Search     │ │18 agents│ │Multi-task│ │Single agent │
│ - Risk       │ │         │ │          │ │+ Tools      │
│ - Similar    │ │         │ │          │ │             │
└──────────────┘ └─────────┘ └──────────┘ └─────────────┘
```

---

### 3.2 Intent Detector Service

**New Service**: `src/app/application/chat/services/intent_detector.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ChatIntent(Enum):
    """Chat intent types."""
    PROTOCOL_SEARCH = "protocol_search"
    RISK_ASSESSMENT = "risk_assessment"
    SIMILAR_PROTOCOLS = "similar_protocols"
    SPECIALIST_TASK = "specialist_task"
    COMPLEX_WORKFLOW = "complex_workflow"
    GENERAL_CONVERSATION = "general_conversation"

@dataclass
class IntentDetectionResult:
    """Intent detection result."""
    intent: ChatIntent
    confidence: float  # 0-1
    extracted_entities: dict  # Protocol names, tokens, amounts, etc.
    reasoning: str  # Why this intent was chosen

class IntentDetectorService:
    """
    Detect user intent from chat messages.

    Uses LLM-powered classification with keyword fallbacks.
    """

    def __init__(self, llm_client: LLMClientGateway):
        self._llm_client = llm_client

    async def detect_intent(
        self,
        message: str,
        conversation_history: Optional[list[Message]] = None,
    ) -> IntentDetectionResult:
        """
        Detect intent from user message.

        Args:
            message: User message
            conversation_history: Previous messages (for context)

        Returns:
            Intent detection result with confidence and entities
        """
        # Try LLM-powered classification first
        try:
            result = await self._llm_classify_intent(message, conversation_history)
            if result.confidence > 0.7:
                return result
        except Exception as e:
            # Fallback to keyword-based detection
            pass

        # Keyword-based fallback (fast, reliable)
        return self._keyword_classify_intent(message)

    async def _llm_classify_intent(
        self,
        message: str,
        conversation_history: Optional[list[Message]],
    ) -> IntentDetectionResult:
        """
        Use LLM to classify intent.

        Provides higher accuracy but slower and costs tokens.
        """
        # Build classification prompt
        system_prompt = """
        You are an intent classifier for a DeFi chat interface.

        Classify the user's message into ONE of these intents:
        1. PROTOCOL_SEARCH - User wants to find/search for protocols
        2. RISK_ASSESSMENT - User wants risk analysis for a protocol
        3. SIMILAR_PROTOCOLS - User wants alternatives to a protocol
        4. SPECIALIST_TASK - User needs specialist agent (yield, gas, security, etc.)
        5. COMPLEX_WORKFLOW - User needs multi-step analysis or strategy
        6. GENERAL_CONVERSATION - General questions, education, chat

        Extract entities: protocol names, token symbols, amounts, chains, etc.

        Return JSON:
        {
          "intent": "INTENT_NAME",
          "confidence": 0.95,
          "entities": {...},
          "reasoning": "Why this intent?"
        }
        """

        # Add conversation context
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{m.role}: {m.content}"
                for m in conversation_history[-3:]  # Last 3 messages
            ])

        user_prompt = f"""
        Previous context:
        {context}

        Current message: {message}

        Classify the intent.
        """

        # Call LLM
        response = await self._llm_client.generate(
            model="gpt-4o-mini",  # Fast, cheap for classification
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistent classification
            response_format={"type": "json_object"},
        )

        # Parse JSON response
        import json
        data = json.loads(response)

        return IntentDetectionResult(
            intent=ChatIntent(data["intent"].lower()),
            confidence=data["confidence"],
            extracted_entities=data.get("entities", {}),
            reasoning=data.get("reasoning", ""),
        )

    def _keyword_classify_intent(self, message: str) -> IntentDetectionResult:
        """
        Keyword-based intent classification (fast fallback).
        """
        message_lower = message.lower()

        # Protocol search patterns
        if any(kw in message_lower for kw in [
            "find protocol", "search protocol", "show protocol",
            "list protocol", "what protocols", "which protocol",
            "protocol for", "protocols that", "protocols with"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.PROTOCOL_SEARCH,
                confidence=0.85,
                extracted_entities=self._extract_search_entities(message),
                reasoning="Message contains protocol search keywords",
            )

        # Risk assessment patterns
        if any(kw in message_lower for kw in [
            "is it safe", "how safe", "risk", "risky",
            "analyze risk", "risk analysis", "should i use",
            "is [protocol] safe", "safe to use"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.RISK_ASSESSMENT,
                confidence=0.85,
                extracted_entities=self._extract_risk_entities(message),
                reasoning="Message contains risk assessment keywords",
            )

        # Similar protocols patterns
        if any(kw in message_lower for kw in [
            "similar to", "alternative to", "like [protocol]",
            "protocols like", "competitors", "alternatives",
            "what else is", "other options"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SIMILAR_PROTOCOLS,
                confidence=0.85,
                extracted_entities=self._extract_protocol_name(message),
                reasoning="Message contains similarity/alternative keywords",
            )

        # Specialist task patterns (yield, gas, security, etc.)
        if any(kw in message_lower for kw in [
            "best yield", "highest apy", "optimize gas",
            "gas optimization", "security audit", "audit contract",
            "tax implications", "portfolio strategy", "rebalance"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SPECIALIST_TASK,
                confidence=0.80,
                extracted_entities=self._extract_specialist_entities(message),
                reasoning="Message contains specialist task keywords",
            )

        # Complex workflow patterns
        if any(kw in message_lower for kw in [
            "create portfolio", "build strategy", "comprehensive analysis",
            "plan migration", "multi-step", "analyze and recommend",
            "compare and suggest"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.COMPLEX_WORKFLOW,
                confidence=0.80,
                extracted_entities={},
                reasoning="Message contains complex workflow keywords",
            )

        # Default: General conversation
        return IntentDetectionResult(
            intent=ChatIntent.GENERAL_CONVERSATION,
            confidence=0.70,
            extracted_entities={},
            reasoning="No specific intent detected, defaulting to general chat",
        )

    def _extract_search_entities(self, message: str) -> dict:
        """Extract entities for protocol search."""
        entities = {}

        # Extract chain
        chains = ["ethereum", "arbitrum", "polygon", "base", "optimism"]
        for chain in chains:
            if chain in message.lower():
                entities["chain"] = chain.capitalize()

        # Extract category
        categories = ["dex", "lending", "staking", "bridge", "yield"]
        for cat in categories:
            if cat in message.lower():
                entities["category"] = cat.capitalize()

        # Extract risk preference
        if any(kw in message.lower() for kw in ["low-risk", "safe", "conservative"]):
            entities["risk_preference"] = "low"
        elif any(kw in message.lower() for kw in ["high-risk", "risky", "aggressive"]):
            entities["risk_preference"] = "high"

        return entities

    def _extract_risk_entities(self, message: str) -> dict:
        """Extract entities for risk assessment."""
        entities = {}

        # Extract protocol name (simple heuristic)
        import re
        protocol_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', message)
        if protocol_match:
            entities["protocol_name"] = protocol_match.group(1)

        # Extract amount
        amount_match = re.search(r'\$?([\d,]+)k?', message)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'k' in message.lower():
                amount *= 1000
            entities["amount_usd"] = amount

        # Extract operation
        operations = ["supply", "borrow", "swap", "stake", "bridge"]
        for op in operations:
            if op in message.lower():
                entities["operation_type"] = op

        return entities

    def _extract_protocol_name(self, message: str) -> dict:
        """Extract protocol name from message."""
        import re
        protocol_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', message)
        if protocol_match:
            return {"protocol_name": protocol_match.group(1)}
        return {}

    def _extract_specialist_entities(self, message: str) -> dict:
        """Extract entities for specialist tasks."""
        entities = {}

        # Extract token symbol
        import re
        token_match = re.search(
            r'\b(BTC|ETH|UNI|AAVE|LINK|MATIC|SOL|AVAX|ARB|OP|USDC|USDT|DAI)\b',
            message.upper()
        )
        if token_match:
            entities["token_symbol"] = token_match.group(1)

        # Extract chain
        chains = ["ethereum", "arbitrum", "polygon", "base", "optimism"]
        for chain in chains:
            if chain in message.lower():
                entities["chain"] = chain.capitalize()

        return entities
```

---

### 3.3 Unified Chat Orchestrator

**New Command**: `src/app/application/chat/commands/send_message_unified.py`

```python
from uuid import UUID
from typing import Optional

from app.domain.chat.entities.message import Message
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.application.chat.services.intent_detector import (
    IntentDetectorService,
    ChatIntent,
)
# Import existing handlers
from app.application.chat.graph_search_handler import ChatGraphSearchHandler
from app.application.chat.risk_insights_handler import ChatRiskInsightsHandler
from app.application.agent_squad.commands.send_agent_squad_message import (
    SendAgentSquadMessage,
)
from app.application.agent_squad.commands.execute_supervisor_workflow import (
    ExecuteSupervisorWorkflow,
)
from app.application.chat.commands.send_message import SendMessage

class UnifiedChatOrchestrator:
    """
    Orchestrates unified chat routing with intelligent intent detection.

    Routes messages to:
    - GraphRAG handlers (search, risk, similar)
    - Agent Squad (specialist tasks)
    - Supervisor (complex workflows)
    - Regular chat (general conversation)
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        intent_detector: IntentDetectorService,
        graphrag_search: ChatGraphSearchHandler,
        graphrag_risk: ChatRiskInsightsHandler,
        agent_squad: SendAgentSquadMessage,
        supervisor: ExecuteSupervisorWorkflow,
        regular_chat: SendMessage,
    ):
        self._conversation_repo = conversation_repo
        self._intent_detector = intent_detector
        self._graphrag_search = graphrag_search
        self._graphrag_risk = graphrag_risk
        self._agent_squad = agent_squad
        self._supervisor = supervisor
        self._regular_chat = regular_chat

    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        content: str,
    ) -> dict:
        """
        Execute unified chat routing.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: User message

        Returns:
            Unified response with routing metadata and enrichment
        """
        # Get conversation history for context
        conversation = await self._conversation_repo.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        messages = await self._conversation_repo.get_messages(
            conversation_id=conversation_id,
            limit=10,
        )

        # Detect intent
        intent_result = await self._intent_detector.detect_intent(
            message=content,
            conversation_history=messages,
        )

        # Route based on intent
        if intent_result.intent == ChatIntent.PROTOCOL_SEARCH:
            return await self._handle_protocol_search(
                user_id, conversation_id, content, intent_result
            )

        elif intent_result.intent == ChatIntent.RISK_ASSESSMENT:
            return await self._handle_risk_assessment(
                user_id, conversation_id, content, intent_result
            )

        elif intent_result.intent == ChatIntent.SIMILAR_PROTOCOLS:
            return await self._handle_similar_protocols(
                user_id, conversation_id, content, intent_result
            )

        elif intent_result.intent == ChatIntent.SPECIALIST_TASK:
            return await self._handle_specialist_task(
                user_id, conversation_id, content, intent_result
            )

        elif intent_result.intent == ChatIntent.COMPLEX_WORKFLOW:
            return await self._handle_complex_workflow(
                user_id, conversation_id, content, intent_result
            )

        else:  # GENERAL_CONVERSATION
            return await self._handle_general_conversation(
                user_id, conversation_id, content, intent_result
            )

    async def _handle_protocol_search(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle protocol search intent."""
        # Extract search parameters from entities
        entities = intent_result.extracted_entities

        # Perform GraphRAG search
        search_results = await self._graphrag_search.search_protocols_from_chat(
            message=content,
            user_preferences={
                "risk_tolerance": entities.get("risk_preference", "moderate"),
                "preferred_chains": [entities["chain"]] if "chain" in entities else [],
                "preferred_categories": [entities["category"]] if "category" in entities else [],
            },
            conversation_id=conversation_id,
        )

        # Format response message
        response_content = self._format_search_results(search_results)

        # Save to conversation history
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": user_msg,
            "agent_message": agent_msg,
            "routing": {
                "intent": "PROTOCOL_SEARCH",
                "confidence": intent_result.confidence,
                "handler": "graphrag_search",
            },
            "enrichment": {
                "protocols": [
                    {
                        "protocol_id": r.protocol_id,
                        "protocol_name": r.protocol_name,
                        "similarity_score": r.similarity_score,
                        "risk_score": r.risk_score,
                        "tvl": r.tvl,
                    }
                    for r in search_results.results
                ]
            }
        }

    async def _handle_risk_assessment(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle risk assessment intent."""
        entities = intent_result.extracted_entities

        # Perform risk analysis
        risk_insights = await self._graphrag_risk.get_protocol_risk_from_chat(
            protocol_name=entities.get("protocol_name", ""),
            conversation_id=conversation_id,
            operation_type=entities.get("operation_type"),
            amount_usd=entities.get("amount_usd"),
        )

        # Format response
        response_content = self._format_risk_analysis(risk_insights)

        # Save to conversation
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": user_msg,
            "agent_message": agent_msg,
            "routing": {
                "intent": "RISK_ASSESSMENT",
                "confidence": intent_result.confidence,
                "handler": "graphrag_risk",
            },
            "enrichment": {
                "risk_analysis": {
                    "risk_score": risk_insights.risk_analysis.risk_score,
                    "risk_level": risk_insights.risk_analysis.risk_level,
                    "confidence": risk_insights.risk_analysis.confidence,
                }
            }
        }

    async def _handle_similar_protocols(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle similar protocols intent."""
        entities = intent_result.extracted_entities
        protocol_name = entities.get("protocol_name", "")

        # Find base protocol
        base_search = await self._graphrag_search.search_protocols_from_chat(
            message=protocol_name,
            conversation_id=conversation_id,
        )

        if not base_search.results:
            # Fallback to general chat
            return await self._handle_general_conversation(
                user_id, conversation_id,
                f"I couldn't find the protocol '{protocol_name}'",
                intent_result
            )

        base_protocol = base_search.results[0]

        # Find similar protocols
        similar_search = await self._graphrag_search.search_protocols_from_chat(
            message=f"protocols similar to {protocol_name}",
            conversation_id=conversation_id,
        )

        # Filter out base protocol
        similar_protocols = [
            r for r in similar_search.results
            if r.protocol_id != base_protocol.protocol_id
        ][:5]

        # Format response
        response_content = self._format_similar_protocols(
            base_protocol, similar_protocols
        )

        # Save to conversation
        user_msg, agent_msg = await self._save_messages(
            conversation_id, content, response_content
        )

        return {
            "user_message": user_msg,
            "agent_message": agent_msg,
            "routing": {
                "intent": "SIMILAR_PROTOCOLS",
                "confidence": intent_result.confidence,
                "handler": "graphrag_similar",
            },
            "enrichment": {
                "base_protocol": {
                    "protocol_id": base_protocol.protocol_id,
                    "protocol_name": base_protocol.protocol_name,
                },
                "similar_protocols": [
                    {
                        "protocol_id": p.protocol_id,
                        "protocol_name": p.protocol_name,
                        "similarity_score": p.similarity_score,
                    }
                    for p in similar_protocols
                ]
            }
        }

    async def _handle_specialist_task(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle specialist task intent (Agent Squad)."""
        # Execute Agent Squad routing
        result = await self._agent_squad.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            force_agent=None,  # Let intent classifier choose
        )

        return {
            "user_message": {"id": result["user_message_id"], "content": content},
            "agent_message": {"id": result["agent_message_id"], "content": result["content"]},
            "routing": {
                "intent": "SPECIALIST_TASK",
                "confidence": intent_result.confidence,
                "handler": "agent_squad",
                "agent_used": result["agent_type"],
            },
            "enrichment": {
                "tools_used": result.get("tools_used", []),
                "tokens_consumed": result.get("tokens_used"),
                "latency_ms": result.get("latency_ms"),
            }
        }

    async def _handle_complex_workflow(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle complex workflow intent (Supervisor)."""
        # Execute Supervisor workflow
        result = await self._supervisor.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            complex_task=content,
            max_agents=5,
        )

        return {
            "user_message": {"content": content},
            "agent_message": {"content": result.get("final_response", "")},
            "routing": {
                "intent": "COMPLEX_WORKFLOW",
                "confidence": intent_result.confidence,
                "handler": "supervisor",
            },
            "enrichment": {
                "workflow_tasks": result.get("tasks", []),
                "agents_involved": result.get("agents_used", []),
                "total_latency_ms": result.get("total_latency_ms"),
            }
        }

    async def _handle_general_conversation(
        self, user_id, conversation_id, content, intent_result
    ) -> dict:
        """Handle general conversation intent (Regular Chat)."""
        # Execute regular chat
        user_msg, agent_msg = await self._regular_chat.execute(
            user_id=user_id,
            conversation_id=conversation_id,
            content=content,
        )

        return {
            "user_message": user_msg,
            "agent_message": agent_msg,
            "routing": {
                "intent": "GENERAL_CONVERSATION",
                "confidence": intent_result.confidence,
                "handler": "regular_chat",
            },
        }

    async def _save_messages(
        self, conversation_id: UUID, user_content: str, agent_content: str
    ) -> tuple[Message, Message]:
        """Save user and agent messages to conversation."""
        # Create and save user message
        user_message = Message.create_user_message(
            conversation_id=conversation_id,
            content=user_content,
        )
        await self._conversation_repo.add_message(user_message)

        # Create and save agent message
        agent_message = Message.create_agent_message(
            conversation_id=conversation_id,
            content=agent_content,
        )
        await self._conversation_repo.add_message(agent_message)

        return user_message, agent_message

    def _format_search_results(self, search_results) -> str:
        """Format GraphRAG search results as markdown."""
        if not search_results.results:
            return "I couldn't find any protocols matching your criteria."

        output = f"{search_results.search_explanation}\n\n"

        for i, protocol in enumerate(search_results.results, 1):
            output += f"**{i}. {protocol.protocol_name}**\n"
            output += f"- TVL: ${protocol.tvl/1e9:.1f}B\n"
            output += f"- Risk: {protocol.risk_level} ({protocol.risk_score:.1f}/10)\n"
            output += f"- Category: {protocol.category}\n"
            output += f"- Chain: {protocol.chain}\n"
            if protocol.apy:
                output += f"- APY: {protocol.apy:.1f}%\n"
            output += f"- Why relevant: {protocol.why_relevant}\n\n"

        if search_results.recommendations:
            output += "**Recommendations:**\n"
            for rec in search_results.recommendations:
                output += f"- {rec}\n"

        return output

    def _format_risk_analysis(self, risk_insights) -> str:
        """Format risk analysis as markdown."""
        ra = risk_insights.risk_analysis

        output = f"**Risk Analysis: {ra.protocol_name}**\n\n"
        output += f"- Risk Score: {ra.risk_score:.1f}/10 ({ra.risk_level})\n"
        output += f"- Confidence: {ra.confidence*100:.0f}%\n\n"

        if ra.contributing_factors:
            output += "**Contributing Factors:**\n"
            for factor in ra.contributing_factors:
                critical = "⚠️ CRITICAL" if factor.is_critical else ""
                output += f"- **{factor.factor}** {critical}\n"
                output += f"  - Impact: {factor.impact:.1f}/10\n"
                output += f"  - {factor.description}\n\n"

        if ra.recommendations:
            output += "**Recommendations:**\n"
            for rec in ra.recommendations:
                output += f"- {rec}\n"

        if ra.should_warn and ra.warning_message:
            output += f"\n⚠️ **Warning:** {ra.warning_message}\n"

        if risk_insights.alternatives:
            output += "\n**Safer Alternatives:**\n"
            for alt in risk_insights.alternatives[:3]:
                output += f"- {alt.protocol_name} (Risk: {alt.risk_level})\n"
                output += f"  - {alt.why_better}\n"

        return output

    def _format_similar_protocols(self, base, similar_list) -> str:
        """Format similar protocols as markdown."""
        output = f"**Similar to {base.protocol_name}:**\n\n"

        for i, protocol in enumerate(similar_list, 1):
            output += f"**{i}. {protocol.protocol_name}**\n"
            output += f"- Similarity: {protocol.similarity_score*100:.0f}%\n"
            output += f"- TVL: ${protocol.tvl/1e9:.1f}B\n"
            output += f"- Risk: {protocol.risk_level}\n"
            output += f"- Why similar: {protocol.why_relevant}\n\n"

        return output
```

---

### 3.4 Updated Router

**Update**: `src/app/presentation/http/controllers/chat/router.py`

```python
@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=UnifiedChatResponse,  # NEW: Unified response
    dependencies=[Security(bearer_scheme)],
)
@inject
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_user: FromDishka[CurrentUserService],
    orchestrator: FromDishka[UnifiedChatOrchestrator],  # NEW: Use orchestrator
) -> UnifiedChatResponse:
    """
    Send a message with intelligent routing.

    Features:
    - Automatic intent detection
    - Routes to GraphRAG, Agent Squad, Supervisor, or Regular Chat
    - Unified response format
    - Conversation history maintained

    Examples:
    - "Find low-risk staking on Ethereum" → GraphRAG Search
    - "Is Aave safe?" → GraphRAG Risk Analysis
    - "Similar to Uniswap?" → GraphRAG Similar Protocols
    - "Best USDC yield?" → Agent Squad (defi_yield)
    - "Create portfolio" → Supervisor Workflow
    - "What is DeFi?" → Regular Chat
    """
    user = await current_user.get_current_user()

    # Execute unified routing
    result = await orchestrator.execute(
        user_id=user.id,
        conversation_id=conversation_id,
        content=request.content,
    )

    return UnifiedChatResponse(**result)
```

---

## 4. Benefits

### 4.1 User Experience

**1. Seamless Integration**
- Users don't need to choose between endpoints
- Natural conversation flow
- Single endpoint for all chat needs

**2. Intelligent Routing**
- Automatic detection of user intent
- Best handler selected automatically
- Faster responses (right tool for the job)

**3. Consistent Experience**
- Unified response format
- All messages saved to conversation history
- Context preserved across different handlers

**4. Backward Compatible**
- Existing specialized endpoints still work
- Progressive migration possible
- No breaking changes

---

### 4.2 Developer Experience

**1. Maintainability**
- Centralized routing logic
- Easy to add new handlers
- Clear separation of concerns

**2. Observability**
- Routing metadata in every response
- Easy to debug intent classification
- Track which handlers are most used

**3. Flexibility**
- Can override intent detection
- Force specific handlers if needed
- Easy to A/B test routing strategies

**4. Code Reuse**
- All existing handlers unchanged
- Orchestrator composes existing services
- DRY principle maintained

---

### 4.3 Performance

**1. Optimal Routing**
- GraphRAG handlers (fastest, no LLM)
- Agent Squad (fast, single LLM call)
- Supervisor (slower, multi-agent)
- Regular Chat (moderate, single agent + tools)

**2. Cost Efficiency**
- Intent classification: ~100 tokens ($0.00001)
- Routes to cheapest handler that can solve the task
- GraphRAG 50x cheaper than LLM chat

**3. Scalability**
- Intent detection can be cached
- Handlers scale independently
- Can route to different services/instances

---

## 5. Migration Strategy

### 5.1 Phase 1: Implement Core (Week 1)

**Tasks**:
1. Create `IntentDetectorService`
2. Create `UnifiedChatOrchestrator`
3. Add unified response schema
4. Wire up dependency injection

**Testing**:
- Unit tests for intent detection
- Integration tests for orchestrator
- End-to-end tests for each route

**Deployment**:
- Feature flag: `unified_routing_enabled = false` (default off)
- Deploy to staging
- Monitor performance

---

### 5.2 Phase 2: Beta Testing (Week 2)

**Tasks**:
1. Enable for internal users only
2. Collect routing metrics
3. Tune intent classification
4. Fix edge cases

**Metrics to Track**:
- Intent classification accuracy (% correct routes)
- Response latency by handler
- Error rates by intent type
- User satisfaction (feedback)

**Rollout**:
- 10% of users → unified routing
- 90% of users → old endpoints
- Gradual increase based on metrics

---

### 5.3 Phase 3: Full Rollout (Week 3)

**Tasks**:
1. Enable unified routing for all users
2. Keep old endpoints for backward compatibility
3. Update frontend to use unified endpoint
4. Update documentation

**Monitoring**:
- Dashboard for routing metrics
- Alerts for classification failures
- Performance SLOs by handler

**Deprecation Plan**:
- Old endpoints marked as deprecated (6 months)
- Migration guide for API consumers
- Sunset timeline communicated

---

### 5.4 Phase 4: Optimization (Week 4+)

**Tasks**:
1. Fine-tune intent classification model
2. Add caching for common intents
3. Optimize handler selection logic
4. A/B test routing strategies

**Advanced Features**:
- Multi-intent handling (combine handlers)
- Learning from user corrections
- Personalized routing (user preferences)
- Proactive suggestions based on intent

---

## 6. Example Conversations

### Example 1: Protocol Discovery

**User**: "Find low-risk staking protocols on Ethereum with high TVL"

**Intent Detection**:
```json
{
  "intent": "PROTOCOL_SEARCH",
  "confidence": 0.95,
  "entities": {
    "chain": "Ethereum",
    "category": "Staking",
    "risk_preference": "low"
  }
}
```

**Routing**: GraphRAG Search → Search Protocols Handler

**Response**:
```
Found 5 protocols that are low-risk, staking, on Ethereum.

1. **Lido V2**
- TVL: $9.5B
- Risk: LOW (2.1/10)
- Category: Staking
- Chain: Ethereum
- APY: 3.8%
- Why relevant: Staking protocol as requested; Deployed on Ethereum; Low-risk as preferred; High TVL ($9.5B); Well audited (12 audits)

[... more protocols ...]

**Recommendations:**
- All protocols meet your criteria - review details before selecting
```

---

### Example 2: Risk Assessment

**User**: "Is it safe to supply $50k to Aave V3?"

**Intent Detection**:
```json
{
  "intent": "RISK_ASSESSMENT",
  "confidence": 0.92,
  "entities": {
    "protocol_name": "Aave V3",
    "operation_type": "supply",
    "amount_usd": 50000
  }
}
```

**Routing**: GraphRAG Risk → Risk Analysis Handler

**Response**:
```
**Risk Analysis: Aave V3**

- Risk Score: 2.5/10 (LOW)
- Confidence: 92%

**Contributing Factors:**
- **Smart Contract Risk**
  - Impact: 0.8/10
  - 12+ audits, battle-tested for 3+ years

- **Liquidity Risk**
  - Impact: 0.3/10
  - High TVL ($8.5B) provides deep liquidity

**Recommendations:**
- Consider diversifying across multiple protocols
- Monitor utilization rates to ensure liquidity

**Safer Alternatives:**
- Compound V3 (Risk: LOW)
  - Similar risk profile with slightly higher APY
```

---

### Example 3: Similar Protocols

**User**: "What's similar to Uniswap?"

**Intent Detection**:
```json
{
  "intent": "SIMILAR_PROTOCOLS",
  "confidence": 0.89,
  "entities": {
    "protocol_name": "Uniswap"
  }
}
```

**Routing**: GraphRAG Similar → Similar Protocols Handler

**Response**:
```
**Similar to Uniswap V3:**

1. **SushiSwap**
- Similarity: 91%
- TVL: $1.8B
- Risk: LOW
- Why similar: High semantic match; DEX protocol as requested; Deployed on Ethereum; High TVL ($1.8B)

2. **Curve Finance**
- Similarity: 82%
- TVL: $4.2B
- Risk: LOW
- Why similar: DEX protocol as requested; Deployed on Ethereum; High TVL ($4.2B); Well audited (15 audits)

[... more protocols ...]
```

---

### Example 4: Specialist Task

**User**: "What's the best USDC yield on Arbitrum right now?"

**Intent Detection**:
```json
{
  "intent": "SPECIALIST_TASK",
  "confidence": 0.94,
  "entities": {
    "token_symbol": "USDC",
    "chain": "Arbitrum"
  }
}
```

**Routing**: Agent Squad → DeFi Yield Agent

**Response**:
```
🌾 Best USDC Yields on Arbitrum:

1. **Aave V3 Supply** - 5.2% APY
   - Risk: LOW
   - TVL: $1.2B
   - Well audited (8+ audits)

2. **GMX V2 Liquidity** - 12.8% APY
   - Risk: MEDIUM
   - TVL: $450M
   - Higher rewards, more volatility

3. **Curve 3pool** - 3.8% APY
   - Risk: LOW
   - TVL: $800M
   - Stable, low IL risk

**Recommendation:** Aave V3 for safety, GMX for higher returns if you can accept medium risk.
```

---

### Example 5: Complex Workflow

**User**: "Create a balanced $50k DeFi portfolio for me"

**Intent Detection**:
```json
{
  "intent": "COMPLEX_WORKFLOW",
  "confidence": 0.88,
  "entities": {
    "amount_usd": 50000
  }
}
```

**Routing**: Supervisor → Multi-Agent Workflow

**Response**:
```
I've created a comprehensive $50k DeFi portfolio strategy for you:

**Portfolio Allocation:**

1. **40% ($20k) - Aave V3 USDC Supply**
   - 4.2% APY
   - Risk: LOW (2.5/10)
   - Provides stable yield base

2. **30% ($15k) - Uniswap V3 ETH/USDC LP**
   - ~12% APY (fees + rewards)
   - Risk: MEDIUM (4.2/10)
   - Higher returns with managed risk

3. **30% ($15k) - Lido stETH**
   - 3.8% APY
   - Risk: LOW (2.1/10)
   - ETH exposure with yield

**Estimated Annual Return:** ~6.8% APY
**Overall Risk Score:** 2.9/10 (LOW)

**Gas Estimates:**
- Total deployment: ~$45 (current gas prices)
- Optimized transaction batching

**Next Steps:**
1. Review allocation breakdown
2. Check current APYs (may vary)
3. Execute transactions via our platform
```

---

## 7. Conclusion

### Summary

This proposal outlines a **unified chat routing architecture** that:

✅ **Intelligently routes** user messages to the appropriate backend (GraphRAG, Agent Squad, Supervisor, or Regular Chat)

✅ **Provides seamless UX** - single endpoint for all chat needs, no manual routing

✅ **Maintains conversation history** - all responses saved to conversation thread

✅ **Delivers optimal performance** - routes to fastest/cheapest handler for each task

✅ **Ensures backward compatibility** - existing specialized endpoints remain functional

✅ **Enables future enhancements** - easy to add new handlers and routing strategies

### Key Components

1. **IntentDetectorService** - LLM-powered intent classification with keyword fallbacks
2. **UnifiedChatOrchestrator** - Routes to appropriate handler based on detected intent
3. **Unified Response Format** - Standardized response with routing metadata and enrichment
4. **Existing Handlers** - Reuses all existing services (no changes required)

### Implementation Timeline

- **Phase 1 (Week 1)**: Implement core components
- **Phase 2 (Week 2)**: Beta testing with 10% of users
- **Phase 3 (Week 3)**: Full rollout to all users
- **Phase 4 (Week 4+)**: Optimization and advanced features

### Next Steps

1. **Review and approve** this proposal
2. **Create implementation tasks** in project management system
3. **Assign developers** to Phase 1 implementation
4. **Set up monitoring** for routing metrics
5. **Begin development** of IntentDetectorService

---

**Generated**: 2025-12-26
**Status**: Proposal - Awaiting Approval
**Estimated Effort**: 3-4 weeks (1 senior engineer)
**Impact**: High (improves UX, performance, maintainability)

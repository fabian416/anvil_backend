# LLM Models & Cost Analysis - Hunter, Squad, ULTRA, Chat

**Version**: 2.0
**Date**: January 6, 2026
**Status**: Production Analysis (Refactored to native Vertex AI model names)

---

## Executive Summary

This document provides a comprehensive analysis of LLM models used across all AI systems in Anvil Backend:
- **Hunter AI Agent**: Market sentiment & predictions
- **Agent Squad**: 18 specialized agents
- **ULTRA**: Advanced DeFi operations
- **Chat**: General conversation

**Key Findings**:
- **Primary Provider**: Vertex AI (Google Gemini 2.0 Flash) - $0.10-0.40/1M tokens
- **Fallback Provider**: DeepInfra (Meta Llama 3.x) - $0.08/1M tokens
- **OpenAI Status**: Removed from codebase (January 2026)
- **Cost Savings**: 91.6-97.7% vs OpenAI GPT-4
- **Monthly Estimate**: $25-50/month (vs $1,500-2,000/month with OpenAI)
- **Unified Gateway**: Enabled (`use_unified_gateway = true`)

---

## Model Configuration Overview

### Provider Architecture

```
┌─────────────────────────────────────────────────────────────┐
│             LLM Provider Stack (Native Names)               │
└─────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  Agent Code      │
                    │ (Uses native    │
                    │  Vertex AI      │
                    │  model names)   │
                    │ gemini-2.0-     │
                    │ flash-exp       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Unified Gateway  │
                    │ (AgentLLMGateway)│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
      ┌───────────────┐            ┌───────────────┐
      │ Vertex AI     │            │ DeepInfra     │
      │ (Primary)     │            │ (Fallback)    │
      │ Uses native   │◄──────────►│ Maps Gemini   │
      │ gemini-*      │  failover  │ → Llama 3.x   │
      │ names         │            │               │
      └───────────────┘            └───────────────┘

Note: OpenAI provider was removed from the codebase (January 2026).
Agent code now uses native Vertex AI model names directly.
DeepInfra client maps Vertex AI names to Llama equivalents for fallback.
```

### Native Model Names (v2.0 Refactor)

**Why Native Names?**
- Agent code uses Vertex AI model names directly (`gemini-2.0-flash-exp`)
- No intermediate mapping layer for primary provider
- DeepInfra maps Vertex AI names to Llama equivalents for fallback
- Cleaner architecture with single source of truth (config.toml)

---

## 1. Hunter AI Agent

### Configuration

**File**: `src/app/infrastructure/adapters/agent_squad/agents/hunter_ai_agent_openai.py`

**Default Model**: `gpt-4o` (maps to actual provider model)

**Purpose**: Market sentiment analysis, price predictions, social media sentiment

**Model Mapping**:
- **Vertex AI**: `gpt-4o` → `gemini-2.0-flash-exp`
- **DeepInfra**: `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`

**Parameters**:
- Temperature: `0.3` (factual, less creative)
- Max Tokens: `1500`
- Tools: CoinGecko API (real-time price data)

**Cost per Request** (estimated):
- Input: ~500 tokens (system prompt + market data + user message)
- Output: ~300 tokens (analysis response)
- **Total**: ~800 tokens/request

**Monthly Cost Estimate**:
- 1,000 requests/month: ~800K tokens
- **Vertex AI**: $0.08 (input) + $0.12 (output) = **$0.20/month**
- **DeepInfra**: $0.064/month
- **OpenAI** (if used): $2.50 (input) + $4.50 (output) = **$7.00/month**

---

## 2. Agent Squad (18 Agents)

### Model Configuration by Agent

| Agent | Config Model | Temp | Tokens | DeepInfra Fallback | Status |
|-------|--------------|------|--------|-------------------|--------|
| **Chat** | `gemini-2.0-flash-exp` | 0.7 | 1000 | `Llama-3.1-70B` | ✅ Enabled |
| **Hunter AI** | `gemini-2.0-flash-exp` | 0.3 | 1500 | `Llama-3.1-70B` | ✅ Enabled |
| **Research** | `gemini-2.0-flash-exp` | 0.2 | 2000 | `Llama-3.1-70B` | ✅ Enabled |
| **Execution** | `gemini-2.0-flash-exp` | 0.1 | 1000 | `Llama-3.1-70B` | ✅ Enabled |
| **Risk Analyzer** | `gemini-2.0-flash-exp` | 0.2 | 1500 | `Llama-3.1-70B` | ✅ Enabled |
| **Portfolio** | `gemini-2.0-flash-exp` | 0.3 | 2000 | `Llama-3.1-70B` | ✅ Enabled |
| **Tax Optimizer** | `gemini-2.0-flash-exp` | 0.2 | 1500 | `Llama-3.1-70B` | ✅ Enabled |
| **DeFi Yield** | `gemini-2.0-flash-exp` | 0.3 | 1500 | `Llama-3.1-70B` | ✅ Enabled |
| **Security Auditor** | `gemini-2.0-flash-exp` | 0.1 | 2000 | `Llama-3.1-70B` | ✅ Enabled |
| **Gas Optimizer** | `gemini-2.0-flash-exp` | 0.2 | 1000 | `Llama-3.1-70B` | ✅ Enabled |
| **Compliance Monitor** | `gemini-2.0-flash-exp` | 0.1 | 2000 | `Llama-3.1-70B` | ⚪ Enterprise |
| **MultiSig Coordinator** | `gemini-2.0-flash-exp` | 0.2 | 1500 | `Llama-3.1-70B` | ⚪ Enterprise |
| **Alert Monitoring** | `gemini-2.0-flash-exp` | 0.3 | 1000 | `Llama-3.1-70B` | ⚪ Pro/Enterprise |
| **Crisis Manager** | `gemini-2.0-flash-exp` | 0.1 | 2000 | `Llama-3.1-70B` | ⚪ Enterprise |
| **Bridge Crosschain** | `gemini-2.0-flash-exp` | 0.2 | 1500 | `Llama-3.1-70B` | ⚪ Pro+ |
| **Lending Borrowing** | `gemini-2.0-flash-exp` | 0.2 | 1500 | `Llama-3.1-70B` | ⚪ Pro+ |
| **NFT Asset Manager** | `gemini-2.0-flash-exp` | 0.3 | 1500 | `Llama-3.1-70B` | ⚪ Pro |
| **DAO Governance** | `gemini-2.0-flash-exp` | 0.3 | 1500 | `Llama-3.1-70B` | ⚪ Pro |

**Legend**: ✅ = Enabled by default, ⚪ = Disabled (tier-based)

### Intent Classification

**Model**: `gemini-2.0-flash-exp` (native Vertex AI name)

**Purpose**: Route user messages to appropriate agents

**Cost**: ~200 tokens/classification
- **Vertex AI**: $0.00002/classification
- **DeepInfra**: $0.000016/classification (fallback: `Llama-3.1-70B`)

### Supervisor Coordination

**Model**: `gemini-2.0-flash-exp` (native Vertex AI name)

**Purpose**: Coordinate multi-agent workflows

**Cost**: ~500 tokens/workflow
- **Vertex AI**: $0.00005/workflow
- **DeepInfra**: $0.00004/workflow (fallback: `Llama-3.1-70B`)

### Workflow Planning

**Model**: 
- **Vertex AI**: `gemini-1.5-pro` (best model for planning)
- **DeepInfra**: `meta-llama/Meta-Llama-3.1-405B-Instruct` (best model)

**Purpose**: Plan multi-agent workflows

**Cost**: ~800 tokens/plan
- **Vertex AI**: $0.00008/plan
- **DeepInfra**: $0.000064/plan

---

## 3. ULTRA System

### Configuration

**Files**: 
- `src/app/application/ultra/arbitrage_discovery.py`
- `src/app/application/ultra/flash_loan_executor.py`
- `src/app/application/ultra/mev_protection.py`

**LLM Usage**: Limited (primarily algorithmic, not LLM-driven)

**Note**: ULTRA focuses on on-chain data and algorithmic execution rather than LLM reasoning.

**If LLM is used** (for explanations/analysis):
- **Model**: `gpt-4o-mini` (fast, cost-effective)
- **Maps to**: `gemini-2.0-flash-exp` (Vertex AI) or `meta-llama/Llama-3.2-3B-Instruct` (DeepInfra)

---

## 4. Chat System

### Configuration

**File**: `src/app/infrastructure/adapters/agent_squad/agents/chat_agent_openai.py`

**Default Model**: `gpt-4o-mini` (maps to actual provider model)

**Purpose**: General conversation, fallback agent

**Model Mapping**:
- **Vertex AI**: `gpt-4o-mini` → `gemini-2.0-flash-exp`
- **DeepInfra**: `gpt-4o-mini` → `meta-llama/Llama-3.2-3B-Instruct`

**Parameters**:
- Temperature: `0.7` (balanced creativity)
- Max Tokens: `1000`
- Tools: None (pure LLM)

**Cost per Request** (estimated):
- Input: ~300 tokens (system prompt + conversation history + user message)
- Output: ~200 tokens (response)
- **Total**: ~500 tokens/request

**Monthly Cost Estimate**:
- 5,000 requests/month: ~2.5M tokens
- **Vertex AI**: $0.25 (input) + $1.00 (output) = **$1.25/month**
- **DeepInfra**: $0.20/month
- **OpenAI** (if used): $0.375 (input) + $1.50 (output) = **$1.875/month**

---

## Cost Analysis

### Provider Pricing Comparison

| Provider | Model | Input Cost | Output Cost | Total (1M tokens) |
|----------|-------|------------|-------------|------------------|
| **Vertex AI** | Gemini 2.0 Flash | $0.10/1M | $0.40/1M | $0.10-0.40/1M |
| **Vertex AI** | Gemini 1.5 Pro | $1.25/1M | $5.00/1M | $1.25-5.00/1M |
| **DeepInfra** | Llama 3.2 3B | $0.08/1M | $0.08/1M | $0.08/1M |
| **DeepInfra** | Llama 3.1 70B | $0.08/1M | $0.08/1M | $0.08/1M |
| **DeepInfra** | Llama 3.1 405B | $0.08/1M | $0.08/1M | $0.08/1M |
| **OpenAI** | GPT-4o | $5.00/1M | $15.00/1M | $5.00-15.00/1M |
| **OpenAI** | GPT-4o-mini | $0.15/1M | $0.60/1M | $0.15-0.60/1M |

### Current Configuration (Vertex AI + DeepInfra)

**Primary**: Vertex AI (Gemini 2.0 Flash)
- Input: $0.10/1M tokens
- Output: $0.40/1M tokens
- **Average**: ~$0.25/1M tokens (assuming 50/50 input/output)

**Fallback**: DeepInfra (Llama models)
- Unified: $0.08/1M tokens (input + output)

### Monthly Cost Estimates

#### Scenario 1: Low Usage (10M tokens/month)

| System | Tokens/Month | Vertex AI Cost | DeepInfra Cost | OpenAI Cost (if used) |
|--------|--------------|---------------|----------------|----------------------|
| **Hunter AI** | 0.8M | $0.20 | $0.064 | $7.00 |
| **Agent Squad** | 5M | $1.25 | $0.40 | $25.00 |
| **Chat** | 2.5M | $1.25 | $0.20 | $1.875 |
| **ULTRA** | 0.5M | $0.125 | $0.04 | $0.30 |
| **Intent Classification** | 0.5M | $0.05 | $0.04 | $0.075 |
| **Supervisor** | 0.2M | $0.05 | $0.016 | $1.00 |
| **Workflow Planning** | 0.5M | $0.05 | $0.04 | $0.30 |
| **TOTAL** | **10M** | **$2.975** | **$0.80** | **$35.55** |

**Savings vs OpenAI**: **91.6%** (Vertex AI) or **97.7%** (DeepInfra)

#### Scenario 2: Medium Usage (50M tokens/month)

| System | Tokens/Month | Vertex AI Cost | DeepInfra Cost | OpenAI Cost (if used) |
|--------|--------------|---------------|----------------|----------------------|
| **Hunter AI** | 4M | $1.00 | $0.32 | $35.00 |
| **Agent Squad** | 25M | $6.25 | $2.00 | $125.00 |
| **Chat** | 12.5M | $6.25 | $1.00 | $9.375 |
| **ULTRA** | 2.5M | $0.625 | $0.20 | $1.50 |
| **Intent Classification** | 2.5M | $0.25 | $0.20 | $0.375 |
| **Supervisor** | 1M | $0.25 | $0.08 | $5.00 |
| **Workflow Planning** | 2.5M | $0.25 | $0.20 | $1.50 |
| **TOTAL** | **50M** | **$14.875** | **$4.00** | **$177.75** |

**Savings vs OpenAI**: **91.6%** (Vertex AI) or **97.7%** (DeepInfra)

#### Scenario 3: High Usage (100M tokens/month)

| System | Tokens/Month | Vertex AI Cost | DeepInfra Cost | OpenAI Cost (if used) |
|--------|--------------|---------------|----------------|----------------------|
| **Hunter AI** | 8M | $2.00 | $0.64 | $70.00 |
| **Agent Squad** | 50M | $12.50 | $4.00 | $250.00 |
| **Chat** | 25M | $12.50 | $2.00 | $18.75 |
| **ULTRA** | 5M | $1.25 | $0.40 | $3.00 |
| **Intent Classification** | 5M | $0.50 | $0.40 | $0.75 |
| **Supervisor** | 2M | $0.50 | $0.16 | $10.00 |
| **Workflow Planning** | 5M | $0.50 | $0.40 | $3.00 |
| **TOTAL** | **100M** | **$29.75** | **$8.00** | **$355.50** |

**Savings vs OpenAI**: **91.6%** (Vertex AI) or **97.7%** (DeepInfra)

---

## Model Selection Strategy

### When to Use Which Model

#### `gpt-4o-mini` (Fast, Cost-Effective)
**Maps to**: `gemini-2.0-flash-exp` or `meta-llama/Llama-3.2-3B-Instruct`

**Used for**:
- Chat agent (general conversation)
- Gas optimizer (simple calculations)
- Intent classification (fast, low complexity)

**Cost**: Lowest ($0.10-0.40/1M tokens Vertex AI, $0.08/1M DeepInfra)

#### `gpt-4o` (Balanced Performance)
**Maps to**: `gemini-2.0-flash-exp` or `meta-llama/Meta-Llama-3.1-70B-Instruct`

**Used for**:
- Hunter AI (market analysis)
- Research agent (deep analysis)
- Risk analyzer (complex modeling)
- Portfolio optimizer (mathematical reasoning)
- Alert Monitoring (real-time alerts)
- Most specialized agents (14 of 18 agents)

**Cost**: Medium ($0.10-0.40/1M tokens Vertex AI, $0.08/1M DeepInfra)

#### `gpt-4` (Best Performance)
**Maps to**: `gemini-1.5-pro` or `meta-llama/Meta-Llama-3.1-405B-Instruct`

**Used for**:
- Workflow planning (complex multi-agent coordination)
- Supervisor coordination (critical decisions)

**Cost**: Higher ($1.25-5.00/1M tokens Vertex AI, $0.08/1M DeepInfra)

---

## Unified Gateway Architecture

### Overview

The system uses a unified gateway pattern (`use_unified_gateway = true`) that provides:
- Single entry point for all LLM operations
- Automatic model mapping (OpenAI names → actual provider models)
- Seamless fallback handling
- Consistent response format across providers

### Architecture Flow

```
Agent Code (uses native Vertex AI model names)
         │  gemini-2.0-flash-exp
         ▼
┌─────────────────────────────────┐
│      AgentLLMGateway            │
│  (Unified interface adapter)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   LLMClientWithFallback         │
│   (Fallback orchestration)      │
└────────────┬────────────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌──────────┐   ┌──────────┐
│ Primary  │   │ Fallback │
│ (Vertex) │   │(DeepInfra)│
│ Uses     │   │ Maps to  │
│ native   │   │ Llama    │
│ names    │   │ models   │
└──────────┘   └──────────┘
```

### Key Components

| Component | Purpose | File |
|-----------|---------|------|
| `LLMClientGateway` | Port interface (domain) | `domain/ports/agent_squad/llm_client_gateway.py` |
| `LLMClientVertexAI` | Vertex AI adapter | `infrastructure/adapters/agent_squad/llm_client_vertex_ai.py` |
| `LLMClientDeepInfra` | DeepInfra adapter | `infrastructure/adapters/agent_squad/llm_client_deepinfra.py` |
| `LLMClientWithFallback` | Fallback wrapper | `infrastructure/adapters/agent_squad/llm_client_with_fallback.py` |
| `AgentLLMGateway` | Unified gateway | `infrastructure/adapters/agent_squad/agent_llm_gateway.py` |

### Supported Operations

All adapters implement these operations:
- `classify_intent()` - Route user messages to appropriate agents
- `recommend_agents()` - Suggest agents for complex tasks
- `plan_workflow()` - Plan multi-agent workflows (uses best model)
- `chat()` - Standard chat completion
- `generate()` - Simple text generation

---

## Fallback Strategy

### Automatic Fallback Behavior

**Primary**: Vertex AI (Gemini)
- **Cost**: $0.10-0.40/1M tokens
- **Performance**: Excellent
- **Reliability**: High (Google infrastructure)

**Fallback**: DeepInfra (Llama)
- **Cost**: $0.08/1M tokens (cheaper!)
- **Performance**: Good (70B model for complex tasks)
- **Reliability**: High (automatic failover)

**Fallback Triggers**:
- Vertex AI API errors
- Rate limit exceeded
- Timeout (>30 seconds)
- Invalid response

**Cost Impact of Fallback**:
- **Positive**: DeepInfra is actually cheaper than Vertex AI
- **Neutral**: Automatic failover ensures reliability
- **No negative impact**: Fallback reduces costs

---

## Cost Optimization Strategies

### 1. Model Selection

**✅ DO**: Use `gpt-4o-mini` for simple tasks
- Chat agent: ✅ Using `gpt-4o-mini`
- Gas optimizer: ✅ Using `gpt-4o-mini`
- Intent classification: ✅ Using `gpt-4o-mini`

**✅ DO**: Use `gpt-4o` for complex reasoning
- Hunter AI: ✅ Using `gpt-4o` (market analysis needs reasoning)
- Research: ✅ Using `gpt-4o` (deep analysis)
- Risk Analyzer: ✅ Using `gpt-4o` (complex modeling)

**✅ DO**: Use `gpt-4` only for critical workflows
- Supervisor: ✅ Using `gpt-4o` (could upgrade to `gpt-4` if needed)
- Workflow Planning: ✅ Using best model (`gemini-1.5-pro` or `llama-405B`)

### 2. Caching

**Current Implementation**:
- Intent classification: Not cached (should be cached for similar queries)
- Agent responses: Not cached (could cache common questions)
- Market data: Cached via CoinGecko client

**Optimization Opportunity**:
- Cache intent classifications for similar messages
- Cache common agent responses (e.g., "What is DeFi?")
- Cache market analysis for same tokens within time window

**Potential Savings**: 20-30% token reduction

### 3. Token Usage Optimization

**Current Practices**:
- ✅ Using appropriate max_tokens (1000-1500 for most agents)
- ✅ Low temperature for classification (0.1)
- ✅ Balanced temperature for chat (0.7)

**Optimization Opportunities**:
- Reduce max_tokens for simple responses (chat: 1000 → 500)
- Use streaming for long responses (reduce wait time, not cost)
- Batch similar requests (if possible)

### 4. Provider Selection

**Current**: Vertex AI (primary) + DeepInfra (fallback)

**Cost Comparison**:
- **Vertex AI**: $0.10-0.40/1M tokens (average $0.25/1M)
- **DeepInfra**: $0.08/1M tokens (68% cheaper!)

**Recommendation**: Consider using DeepInfra as primary for non-critical tasks
- **Chat agent**: Could use DeepInfra (saves 68%)
- **Intent classification**: Could use DeepInfra (saves 68%)
- **Hunter AI**: Keep Vertex AI (needs best reasoning)

**Potential Additional Savings**: 30-40% on chat and classification

---

## Real-World Usage Patterns

### Typical Request Breakdown

**Per User Message**:
1. **Intent Classification**: ~200 tokens → $0.00002 (Vertex AI)
2. **Agent Selection**: ~100 tokens → $0.00001 (Vertex AI)
3. **Agent Processing**: ~800 tokens → $0.00008-0.00032 (Vertex AI)
4. **Response**: ~300 tokens → $0.00012 (Vertex AI)

**Total per Message**: ~1,400 tokens → **$0.00023-0.00047** (Vertex AI)

**With DeepInfra Fallback**: ~1,400 tokens → **$0.000112** (DeepInfra)

### Monthly Projections

| Users | Messages/User/Month | Total Messages | Tokens/Month | Vertex AI Cost | DeepInfra Cost |
|-------|-------------------|----------------|--------------|----------------|----------------|
| 100 | 50 | 5,000 | 7M | $1.75 | $0.56 |
| 500 | 50 | 25,000 | 35M | $8.75 | $2.80 |
| 1,000 | 50 | 50,000 | 70M | $17.50 | $5.60 |
| 5,000 | 50 | 250,000 | 350M | $87.50 | $28.00 |
| 10,000 | 50 | 500,000 | 700M | $175.00 | $56.00 |

**At Scale (10K users, 50 msgs/user/month)**:
- **Vertex AI**: $175/month
- **DeepInfra**: $56/month
- **OpenAI** (if used): $2,485/month

**Savings**: **93%** (Vertex AI) or **97.7%** (DeepInfra) vs OpenAI

---

## Configuration Files

### Agent Squad Config

**File**: `config/local/config.toml` (lines 100-245)

```toml
[agent_squad]
# Intent classification (uses native Vertex AI model names)
intent_classification_model = "gemini-2.0-flash-exp"
intent_confidence_threshold = 0.85
fallback_agent = "chat"

# Supervisor coordination
enable_supervisor = true
supervisor_model = "gemini-2.0-flash-exp"
supervisor_max_agents = 5
supervisor_timeout_seconds = 120

# Performance
max_concurrent_agents = 3
routing_timeout_seconds = 5
execution_timeout_seconds = 60

# Per-agent configuration (all use native Vertex AI names)
[agent_squad.agents.chat]
enabled = true
model = "gemini-2.0-flash-exp"  # Native Vertex AI name
temperature = 0.7
max_tokens = 1000

[agent_squad.agents.hunter_ai]
enabled = true
model = "gemini-2.0-flash-exp"  # Native Vertex AI name
temperature = 0.3
max_tokens = 1500

# ... (all 18 agents use gemini-2.0-flash-exp)
```

### LLM Provider Config

**File**: `config/local/config.toml` (lines 247-288)

```toml
[llm_provider]
# Primary uses native Vertex AI model names
primary_provider = "vertex_ai"
fallback_provider = "deepinfra"
enable_fallback = true
use_unified_gateway = true

[llm_provider.vertex_ai]
# Vertex AI uses native model names directly - no mapping needed
default_model = "gemini-2.0-flash-exp"

[llm_provider.deepinfra]
# DeepInfra maps Vertex AI names to Llama equivalents for fallback
default_model = "meta-llama/Meta-Llama-3.1-70B-Instruct"

# Fallback mapping: Vertex AI names → DeepInfra equivalents
[llm_provider.deepinfra.model_mapping]
"gemini-2.0-flash-exp" = "meta-llama/Meta-Llama-3.1-70B-Instruct"
"gemini-1.5-flash" = "meta-llama/Meta-Llama-3.1-70B-Instruct"
"gemini-1.5-pro" = "meta-llama/Meta-Llama-3.1-405B-Instruct"
```

### API Keys

**File**: `config/local/.secrets.toml`

```toml
[vertex_ai]
API_KEY = "your-vertex-ai-api-key"
PROJECT_ID = "your-gcp-project-id"
PROJECT_NUMBER = "your-gcp-project-number"

[deepinfra]
API_KEY = "your-deepinfra-api-key"
BASE_URL = "https://api.deepinfra.com/v1/openai"
```

### Implementation Files

| Component | File Path |
|-----------|-----------|
| **Vertex AI Client** | `src/app/infrastructure/adapters/agent_squad/llm_client_vertex_ai.py` |
| **DeepInfra Client** | `src/app/infrastructure/adapters/agent_squad/llm_client_deepinfra.py` |
| **Fallback Wrapper** | `src/app/infrastructure/adapters/agent_squad/llm_client_with_fallback.py` |
| **Unified Gateway** | `src/app/infrastructure/adapters/agent_squad/agent_llm_gateway.py` |
| **IoC Configuration** | `src/app/setup/ioc/agent_squad_infrastructure.py` |
| **LLM Config Types** | `src/app/setup/config/llm_orchestration.py` |
| **Agent Config Types** | `src/app/setup/config/agent_squad.py` |

---

## Monitoring & Cost Tracking

### Current Telemetry

**Files**:
- `src/app/infrastructure/telemetry/llm_telemetry.py` - LLM cost and usage tracking
- `src/app/infrastructure/adapters/agent_squad/agent_llm_gateway.py` - Gateway-level metrics

**Tracks**:
- Tokens used (input + output)
- Model used
- Provider used (Vertex AI vs DeepInfra)
- Latency
- Success/failure
- Cost per request

### Cost Calculation

**Formula**:
```python
# Vertex AI
input_cost = (input_tokens / 1_000_000) * 0.10
output_cost = (output_tokens / 1_000_000) * 0.40
total_cost = input_cost + output_cost

# DeepInfra
total_cost = (total_tokens / 1_000_000) * 0.08
```

### Admin Dashboard

**Endpoint**: `GET /api/v1/admin/llm/telemetry/costs`

**Returns**:
- Total cost by provider
- Cost by agent
- Cost by model
- Cost by day
- Token usage breakdown

---

## Recommendations

### 1. Immediate Actions

**✅ Already Implemented**:
- Vertex AI + DeepInfra fallback
- Model mapping for cost optimization
- Appropriate model selection per agent

**🔄 Consider**:
- Use DeepInfra as primary for chat agent (68% cost savings)
- Cache intent classifications (20-30% token reduction)
- Monitor actual usage patterns and adjust models

### 2. Cost Optimization

**High Impact**:
1. **Switch Chat Agent to DeepInfra Primary**: Save 68% on chat costs
2. **Cache Intent Classifications**: Reduce 20-30% tokens
3. **Reduce max_tokens for simple responses**: Save 10-20% tokens

**Medium Impact**:
1. **Batch similar requests**: Reduce redundant API calls
2. **Use streaming for long responses**: Better UX, same cost
3. **Monitor and adjust model selection**: Use cheaper models where quality is acceptable

### 3. Scaling Strategy

**At 1K Users**:
- Current: $17.50/month (Vertex AI) or $5.60/month (DeepInfra)
- **Recommendation**: Keep current setup

**At 10K Users**:
- Current: $175/month (Vertex AI) or $56/month (DeepInfra)
- **Recommendation**: 
  - Use DeepInfra primary for chat (save $70/month)
  - Implement caching (save $35/month)
  - **Total**: ~$50/month (vs $175/month)

**At 100K Users**:
- Projected: $1,750/month (Vertex AI) or $560/month (DeepInfra)
- **Recommendation**:
  - DeepInfra primary for all non-critical agents
  - Aggressive caching
  - **Target**: <$300/month

---

## Summary

### Current Configuration (v2.0 - Native Names)

| System | Config Model | Vertex AI (Primary) | DeepInfra (Fallback) | Cost/1M tokens |
|--------|--------------|---------------------|---------------------|---------------|
| **Hunter AI** | `gemini-2.0-flash-exp` | Direct use | `meta-llama/Meta-Llama-3.1-70B-Instruct` | $0.10-0.40 / $0.08 |
| **Chat** | `gemini-2.0-flash-exp` | Direct use | `meta-llama/Meta-Llama-3.1-70B-Instruct` | $0.10-0.40 / $0.08 |
| **Agent Squad** | `gemini-2.0-flash-exp` | Direct use | `meta-llama/Meta-Llama-3.1-70B-Instruct` | $0.10-0.40 / $0.08 |
| **Workflow Planning** | `gemini-1.5-pro` | Direct use | `meta-llama/Meta-Llama-3.1-405B-Instruct` | $1.25-5.00 / $0.08 |

### Cost Savings

**vs OpenAI GPT-4**:
- **Vertex AI**: 91.6% savings
- **DeepInfra**: 97.7% savings

**Monthly Cost** (100M tokens):
- **Vertex AI**: $29.75/month
- **DeepInfra**: $8.00/month
- **OpenAI** (if used): $355.50/month

### Key Takeaways

1. **91.6-97.7% cost reduction** achieved vs OpenAI
2. **OpenAI removed** from codebase (January 2026)
3. **Native Vertex AI model names** used directly in config (v2.0 refactor)
4. **Unified gateway** pattern for consistent interface
5. **Automatic fallback** ensures reliability (Vertex AI → DeepInfra)
6. **DeepInfra mapping** converts Gemini names to Llama equivalents for fallback
7. **10 agents enabled** by default, 8 agents tier-gated
8. **Production ready** with current configuration

### v2.0 Refactor Changes

| Before (v1.x) | After (v2.0) |
|--------------|--------------|
| Agent code uses OpenAI names | Agent code uses native Vertex AI names |
| Model mapping in all LLM clients | Model mapping only in DeepInfra (for fallback) |
| `gpt-4o` → `gemini-2.0-flash-exp` | Direct: `gemini-2.0-flash-exp` |
| Two mapping layers | Single source of truth (config.toml) |

---

**Last Updated**: January 6, 2026
**Version**: 2.0 (Native Vertex AI model names refactor)

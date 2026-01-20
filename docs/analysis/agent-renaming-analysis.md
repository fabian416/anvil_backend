# Agent Renaming Analysis: Remove "OpenAI" Suffix

## Problem Statement

Multiple agent files and classes use "openai" or "OpenAI" in their names, but they **no longer use OpenAI**. They use:
- **Vertex AI** (Gemini models) as primary provider
- **DeepInfra** (Llama models) as fallback

The "openai" suffix is **confusing and misleading** because:
1. OpenAI was removed from the codebase
2. Agents use unified `LLMClientGateway` which supports Vertex AI and DeepInfra
3. The naming suggests dependency on OpenAI, which doesn't exist
4. New developers might think OpenAI is still in use

## Current State Analysis

### Files with "openai" suffix (8 files):

1. `chat_agent_openai.py` → `ChatAgentOpenAI`
2. `guest_auth_agent_openai.py` → `GuestAuthAgentOpenAI`
3. `hunter_ai_agent_openai.py` → `HunterAIAgentOpenAI`
4. `portfolio_agent_openai.py` → `PortfolioAgentOpenAI`
5. `risk_analyzer_agent_openai.py` → `RiskAnalyzerAgentOpenAI`
6. `defi_yield_agent_openai.py` → `DefiYieldAgentOpenAI`
7. `gas_optimizer_agent_openai.py` → `GasOptimizerAgentOpenAI`
8. `tax_optimizer_agent_openai.py` → `TaxOptimizerAgentOpenAI`

### What they actually use:

- **LLMClientGateway**: Unified interface for LLM providers
- **Vertex AI**: Primary provider (Gemini models)
- **DeepInfra**: Fallback provider (Llama models)
- **No OpenAI dependency**: OpenAI was completely removed

## Proposed Solution

### Naming Convention

Remove "openai" suffix and use generic naming:
- `*_agent_openai.py` → `*_agent.py`
- `*AgentOpenAI` → `*Agent`

### New Names:

1. `chat_agent_openai.py` → `chat_agent.py` (`ChatAgentOpenAI` → `ChatAgent`)
2. `guest_auth_agent_openai.py` → `guest_auth_agent.py` (`GuestAuthAgentOpenAI` → `GuestAuthAgent`)
3. `hunter_ai_agent_openai.py` → `hunter_ai_agent.py` (`HunterAIAgentOpenAI` → `HunterAIAgent`)
4. `portfolio_agent_openai.py` → `portfolio_agent.py` (`PortfolioAgentOpenAI` → `PortfolioAgent`)
5. `risk_analyzer_agent_openai.py` → `risk_analyzer_agent.py` (`RiskAnalyzerAgentOpenAI` → `RiskAnalyzerAgent`)
6. `defi_yield_agent_openai.py` → `defi_yield_agent.py` (`DefiYieldAgentOpenAI` → `DefiYieldAgent`)
7. `gas_optimizer_agent_openai.py` → `gas_optimizer_agent.py` (`GasOptimizerAgentOpenAI` → `GasOptimizerAgent`)
8. `tax_optimizer_agent_openai.py` → `tax_optimizer_agent.py` (`TaxOptimizerAgentOpenAI` → `TaxOptimizerAgent`)

## Impact Analysis

### Files to Update:

1. **Agent files** (8 files): Rename files and classes
2. **`__init__.py`**: Update imports
3. **IOC providers** (`agent_squad_infrastructure.py`): Update imports and type hints
4. **Any other imports**: Search and update all references

### Risk Assessment:

- **Low Risk**: These are internal implementation details
- **Breaking Changes**: None (if all imports updated correctly)
- **Testing Required**: Verify all agents still work after renaming

## Implementation Plan

### Phase 1: Analysis & Planning ✅
- [x] Identify all files with "openai" suffix
- [x] Analyze actual LLM provider usage
- [x] Create renaming plan

### Phase 2: File Renaming ✅
- [x] Rename 8 agent files (using git mv to preserve history)
- [x] Update class names in each file
- [x] Update docstrings/comments

### Phase 3: Update Imports ✅
- [x] Update `agents/__init__.py`
- [x] Update `agent_squad_infrastructure.py`
- [x] Update `agent_gateway.py` docstring
- [x] Update tools_used references (openai_api → llm_gateway)

### Phase 4: Verification ✅
- [x] Run syntax checks (all files compile)
- [x] Verify no broken imports
- [x] All old class names removed

## Benefits

1. **Clarity**: Names reflect actual implementation (unified LLM gateway)
2. **Accuracy**: No misleading "openai" references
3. **Maintainability**: Easier for new developers to understand
4. **Consistency**: Matches naming pattern of other agents (e.g., `research_agent_perplexity.py`, `execution_agent_privy.py`)

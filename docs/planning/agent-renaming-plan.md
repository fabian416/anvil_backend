# Agent Renaming Plan: Remove "OpenAI" Suffix

## Problem Analysis (CTO Methodology - Phase 1)

### Root Cause
- Agents use "OpenAI" in names but **don't use OpenAI**
- They use **Vertex AI (Gemini)** and **DeepInfra (Llama)** via unified `LLMClientGateway`
- OpenAI was completely removed from the codebase
- Naming is **misleading and confusing** for developers

### Current State
- 8 agent files with `_openai` suffix
- 8 classes with `OpenAI` suffix
- All use `LLMClientGateway` (Vertex AI/DeepInfra)
- No OpenAI dependencies

## Solution Design (CTO Methodology - Phase 2)

### Naming Convention
Remove provider-specific suffix, use generic agent naming:
- `*_agent_openai.py` → `*_agent.py`
- `*AgentOpenAI` → `*Agent`

### Files to Rename

| Old Name | New Name | Class Old | Class New |
|----------|----------|-----------|-----------|
| `chat_agent_openai.py` | `chat_agent.py` | `ChatAgentOpenAI` | `ChatAgent` |
| `guest_auth_agent_openai.py` | `guest_auth_agent.py` | `GuestAuthAgentOpenAI` | `GuestAuthAgent` |
| `hunter_ai_agent_openai.py` | `hunter_ai_agent.py` | `HunterAIAgentOpenAI` | `HunterAIAgent` |
| `portfolio_agent_openai.py` | `portfolio_agent.py` | `PortfolioAgentOpenAI` | `PortfolioAgent` |
| `risk_analyzer_agent_openai.py` | `risk_analyzer_agent.py` | `RiskAnalyzerAgentOpenAI` | `RiskAnalyzerAgent` |
| `defi_yield_agent_openai.py` | `defi_yield_agent.py` | `DefiYieldAgentOpenAI` | `DefiYieldAgent` |
| `gas_optimizer_agent_openai.py` | `gas_optimizer_agent.py` | `GasOptimizerAgentOpenAI` | `GasOptimizerAgent` |
| `tax_optimizer_agent_openai.py` | `tax_optimizer_agent.py` | `TaxOptimizerAgentOpenAI` | `TaxOptimizerAgent` |

## Risk Assessment (CTO Methodology - Phase 3)

### Risks
- **Low**: Internal refactoring, no API changes
- **Medium**: Many import statements to update
- **Mitigation**: Systematic search and replace

### Files Requiring Updates
1. `agents/__init__.py` - Import statements
2. `agent_squad_infrastructure.py` - Provider methods and type hints
3. Individual agent files - Class names and docstrings
4. Any test files (if they exist)

## Implementation Steps

### Step 1: Rename Files
Use `git mv` to preserve history:
```bash
git mv chat_agent_openai.py chat_agent.py
# ... repeat for all 8 files
```

### Step 2: Update Class Names
In each renamed file:
- Change class name: `ChatAgentOpenAI` → `ChatAgent`
- Update docstrings: Remove "OpenAI" references
- Update comments

### Step 3: Update Imports
- `agents/__init__.py`: Update all imports
- `agent_squad_infrastructure.py`: Update imports and type hints

### Step 4: Verification
- Syntax check all files
- Verify imports work
- Test agent execution

## Benefits
1. **Clarity**: Names reflect actual implementation
2. **Accuracy**: No misleading provider references
3. **Consistency**: Matches other agents (e.g., `research_agent_perplexity.py`)
4. **Maintainability**: Easier for new developers

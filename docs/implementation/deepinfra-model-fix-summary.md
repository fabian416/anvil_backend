# DeepInfra Model Configuration Fix

## Problem
DeepInfra API was returning `404: model_not_found` errors because agents were using `gpt-4o` and `gpt-4o-mini` models which don't exist on DeepInfra.

## Solution
Replaced all OpenAI model references with DeepInfra-compatible Meta Llama models:

### Model Mappings
- **`gpt-4o`** → **`meta-llama/Meta-Llama-3.1-70B-Instruct`** (for complex reasoning)
- **`gpt-4o-mini`** → **`meta-llama/Meta-Llama-3.1-8B-Instruct`** (for fast, cost-effective)

### Files Updated

**Core Agents:**
- ✅ `hunter_ai_agent_openai.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `chat_agent_openai.py` - `gpt-4o-mini` → `meta-llama/Meta-Llama-3.1-8B-Instruct`
- ✅ `portfolio_agent_openai.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `risk_analyzer_agent_openai.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `defi_yield_agent_openai.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `tax_optimizer_agent_openai.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `gas_optimizer_agent_openai.py` - `gpt-4o-mini` → `meta-llama/Meta-Llama-3.1-8B-Instruct`
- ✅ `research_agent_perplexity.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `security_auditor_agent_slither.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `execution_agent_privy.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`

**Enterprise Agents:**
- ✅ `crisis_manager_agent_forta.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `alert_monitoring_agent_forta.py` - `gpt-4o-mini` → `meta-llama/Meta-Llama-3.1-8B-Instruct`
- ✅ `compliance_monitor_agent_chainalysis.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `multisig_coordinator_agent_gnosis.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`

**Advanced Agents:**
- ✅ `lending_borrowing_agent_aave.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `nft_asset_manager_agent_opensea.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `bridge_crosschain_agent_axelar.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`
- ✅ `dao_governance_agent_snapshot.py` - `gpt-4o` → `meta-llama/Meta-Llama-3.1-70B-Instruct`

**Domain Services:**
- ✅ `intent_classifier.py` - `gpt-4o-mini` → `meta-llama/Meta-Llama-3.1-8B-Instruct`
- ✅ `agent_squad_domain.py` (IOC) - `gpt-4o-mini` → `meta-llama/Meta-Llama-3.1-8B-Instruct`

## Result
✅ **SupervisorCoordinator is now working successfully!**
- Logs show: "✅ Agent Squad Supervisor handled query successfully"
- No more `model_not_found` errors
- All agents now use DeepInfra-compatible models

## Model Selection Rationale
- **70B models** for complex reasoning tasks (hunter_ai, portfolio, risk_analyzer, etc.)
- **8B models** for fast, cost-effective tasks (chat, gas_optimizer, alert_monitoring, intent classification)

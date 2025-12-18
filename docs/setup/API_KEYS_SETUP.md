# Agent Squad API Keys Setup Guide

**Document**: API Keys Configuration  
**Date**: December 1, 2025  
**Status**: Phase 7 - API Integration  
**Priority**: P0 - Required for Production

---

## 📋 **Overview**

Agent Squad integrates with 15+ external APIs to provide real-time DeFi data, compliance screening, and advanced features. This guide covers how to obtain and configure API keys for each service.

---

## 🎯 **Quick Start**

### **1. Copy Environment Template**
```bash
cp config/local/.env.example config/local/.env
```

### **2. Required for Basic Functionality**
```bash
# Minimum required keys for LLM providers
VERTEX_AI_PROJECT_ID=your-gcp-project-id  # ✅ Required - Primary LLM provider

# Authentication (choose ONE method):
# Option 1: API Key (✅ Recommended - Simplest)
VERTEX_AI_API_KEY=AIzaSy...  # Get from Google Cloud Console > Credentials

# Option 2: Service account JSON file path
VERTEX_AI_CREDENTIALS_PATH=/path/to/credentials.json

# Option 3: Standard Google Cloud env var
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Option 4: Application Default Credentials (if running on GCP)
# No env var needed - uses metadata service automatically

DEEPINFRA_API_KEY=...  # ✅ Recommended - Fallback LLM provider
```

### **3. Recommended for Production**
```bash
# Add these for real data
COINGECKO_API_KEY=...  # Price data
ONEINCH_API_KEY=...    # Swap quotes
THEGRAPH_API_KEY=...   # DeFi protocol data
```

---

## 🔑 **API Keys by Category**

### **Week 1: LLM Provider APIs**

#### **1. Google Vertex AI** ⭐ **PRIMARY PROVIDER (REQUIRED)**
- **Purpose**: Primary LLM provider for all agent capabilities, distillation engine
- **Get from**: https://console.cloud.google.com/vertex-ai
- **Pricing**: 
  - Gemini 1.5 Flash: ~$0.00001875/1K chars (fast, cheap)
  - Gemini 1.5 Pro: ~$0.00125/1K chars (complex reasoning)
- **Environment Variables**: 
  - `VERTEX_AI_PROJECT_ID` ✅ **Required** - Your GCP project ID
  - **Authentication** (choose ONE method):
    - `VERTEX_AI_API_KEY` ✅ **Recommended** - API key from Google Cloud Console (simplest method)
    - `VERTEX_AI_CREDENTIALS_PATH` - Path to service account JSON (alternative)
    - `GOOGLE_APPLICATION_CREDENTIALS` - Standard Google Cloud env var (alternative)
    - **Application Default Credentials** - Automatic if running on GCP Compute/Cloud Run (no env var needed)
- **Feature Flag**: N/A (always required as primary)

**Important**: Vertex AI does **NOT** use API keys like other services. It requires:
- **Service Account JSON file** (contains private key, client email, project ID, etc.)
- **OR** Application Default Credentials (if running on GCP)

**Important**: Vertex AI does **NOT** use API keys like other services (OpenAI, DeepInfra, etc.). It requires:
- **Service Account JSON file** (contains private key, client email, project ID, etc.)
- **OR** Application Default Credentials (if running on GCP)

**If you have an "API key" for Vertex AI**, it's likely:
- A **service account JSON file** that you downloaded from Google Cloud Console
- This file contains credentials, not a simple string key
- You need to save this JSON file and reference it by **file path**, not as an environment variable string

**Note**: `VERTEX_AI_CREDENTIALS_PATH` is **NOT strictly required**. The code supports multiple authentication methods:
- If `credentials_path` is provided → uses that JSON file
- If not provided → uses `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to JSON file
- If neither → uses Application Default Credentials (automatic on GCP)

**Example**: If you have a JSON file at `/home/user/vertex-credentials.json`:
```bash
export VERTEX_AI_PROJECT_ID="your-project-id"
export VERTEX_AI_CREDENTIALS_PATH="/home/user/vertex-credentials.json"
# OR
export GOOGLE_APPLICATION_CREDENTIALS="/home/user/vertex-credentials.json"
```

**Setup** (API Key Method - Recommended):

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable **Vertex AI API**:
   - Go to **APIs & Services** → **Enable APIs**
   - Search for "Vertex AI API" and enable it
4. Create API Key:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **API Key**
   - Copy the API key (starts with `AIza...`)
   - (Optional) Restrict the API key to Vertex AI API only for security

**Alternative Setup** (Service Account JSON - for advanced use):

1. Follow steps 1-3 above
2. Create a Service Account:
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: `anvil-vertex-ai`
   - Grant role: **Vertex AI User**
3. Create and download JSON key:
   - Click on the service account
   - Go to **Keys** tab → **Add Key** → **Create new key**
   - Select JSON format
   - Save the file securely (e.g., `/path/to/vertex-ai-credentials.json`)

**Important Note**: Vertex AI does **NOT** use traditional API keys like other services. It uses:
- **Service Account JSON file** (recommended for local development)
- **Application Default Credentials** (automatic on GCP environments)

If you have a service account JSON file, that's what you need - not an API key string.

**Configuration**:

**Option 1: Using API Key** (✅ Recommended - Simplest):
```bash
# Environment variables
export VERTEX_AI_PROJECT_ID="your-gcp-project-id"
export VERTEX_AI_API_KEY="AIzaSy..."  # Your API key from Google Cloud Console
```

```toml
# config/local/.secrets.toml
[vertex_ai]
PROJECT_ID = "your-gcp-project-id"
API_KEY = "AIzaSy..."  # Your API key
```

**Option 2: Using Service Account JSON** (for advanced use):
```bash
# Environment variables
export VERTEX_AI_PROJECT_ID="your-gcp-project-id"
export VERTEX_AI_CREDENTIALS_PATH="/path/to/vertex-ai-credentials.json"
```

```toml
# config/local/.secrets.toml
[vertex_ai]
PROJECT_ID = "your-gcp-project-id"
CREDENTIALS_PATH = "/path/to/vertex-ai-credentials.json"
```

**Option 3: Using GOOGLE_APPLICATION_CREDENTIALS** (standard Google Cloud approach):
```bash
export VERTEX_AI_PROJECT_ID="your-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/vertex-ai-credentials.json"
```

**Option 4: Application Default Credentials** (if running on GCP):
```bash
# No credentials needed - uses metadata service automatically
export VERTEX_AI_PROJECT_ID="your-gcp-project-id"
```

**Config File**:
```toml
# config/local/config.toml
[distillation]
provider = "vertex_ai"
fallback_provider = "deepinfra"
```

**Available Models**:
- `gemini-1.5-flash` - Fast inference, distillation (recommended)
- `gemini-1.5-pro` - Complex reasoning tasks
- `gemini-1.0-pro` - General purpose

**Used By**: All 18 agents (primary), distillation engine, LLM orchestration carousel

---

#### **2. DeepInfra** 🟡 **FALLBACK PROVIDER (RECOMMENDED)**
- **Purpose**: Fallback LLM provider, open-source models (Llama, Mixtral, Qwen)
- **Get from**: https://deepinfra.com/
- **Pricing**: Pay-as-you-go (~$0.0001-0.001/1K tokens, very cost-effective)
- **Environment Variable**: `DEEPINFRA_API_KEY`
- **Feature Flag**: `distillation.fallback_provider = "deepinfra"`

**Setup**:
1. Sign up at https://deepinfra.com/
2. Navigate to API Keys section
3. Create new API key
4. Add to `config/local/.secrets.toml`:
   ```toml
   [deepinfra]
   DEEPINFRA_API_KEY = "..."
   ```

**Available Models**:
- `meta-llama/Llama-3.2-3B-Instruct` - Fast, efficient
- `meta-llama/Llama-3.1-70B-Instruct` - High quality
- `mistralai/Mixtral-8x7B-Instruct` - Mixture of experts
- `Qwen/Qwen2.5-7B-Instruct` - Multilingual

**Used By**: Fallback for all agents, distillation fallback, LLM orchestration carousel

---

#### **3. OpenAI** 🟠 **OPTIONAL FALLBACK**
- **Purpose**: Optional fallback LLM provider (GPT-4 for complex tasks)
- **Get from**: https://platform.openai.com/api-keys
- **Pricing**: Pay-as-you-go (~$0.01-0.03/1K tokens for GPT-4)
- **Environment Variable**: `OPENAI_API_KEY` (optional)
- **Feature Flag**: `llm_orchestration.fallback_providers = ["openai"]`

**Setup**:
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create new API key
4. Add to `config/local/.secrets.toml`:
   ```toml
   [openai]
   OPENAI_API_KEY = "sk-proj-..."
   ```

**Note**: OpenAI is **not required** for basic functionality. Vertex AI + DeepInfra provide full coverage. OpenAI is only needed if you want GPT-4 as an additional fallback option.

**Used By**: Optional fallback in LLM orchestration carousel

---

### **Week 2: DeFi Data APIs**

#### **4. CoinGecko** 🟡 **RECOMMENDED**
- **Purpose**: Real-time cryptocurrency prices, market data
- **Get from**: https://www.coingecko.com/en/api/pricing
- **Pricing**: 
  - Free: 10-50 calls/min
  - Pro: $129/month (500 calls/min)
- **Environment Variable**: `COINGECKO_API_KEY` (optional)
- **Feature Flag**: `agent_squad.external_apis.enable_coingecko = true`

**Setup**:
1. Sign up at https://www.coingecko.com/
2. Go to API Pricing page
3. Get API key (free tier available)
4. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   COINGECKO_API_KEY = "CG-..."
   ```

**Used By**: Hunter AI, Portfolio, Risk Analyzer agents

---

#### **5. 1inch DEX Aggregator** 🟡 **RECOMMENDED**
- **Purpose**: Multi-DEX swap quotes, optimal routing
- **Get from**: https://portal.1inch.dev/
- **Pricing**:
  - Free: 1 req/sec
  - Pro: $49/month (10 req/sec)
- **Environment Variable**: `ONEINCH_API_KEY`
- **Feature Flag**: `agent_squad.external_apis.enable_1inch = true`

**Setup**:
1. Sign up at https://portal.1inch.dev/
2. Create new API key
3. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   ONEINCH_API_KEY = "..."
   ```

**Used By**: Execution, Hunter AI agents

---

#### **6. Hyperliquid** ✨ **NEW**
- **Purpose**: Perpetual futures trading, liquidation data
- **Get from**: Hyperliquid Dashboard > API Keys
- **Pricing**: Free for market data, trading requires account
- **Environment Variables**: 
  - `HYPERLIQUID_API_KEY`
  - `HYPERLIQUID_API_SECRET` (for trading)
- **Feature Flag**: `agent_squad.external_apis.enable_hyperliquid = true`

**Setup**:
1. Create account at https://app.hyperliquid.xyz/
2. Go to Settings > API Keys
3. Create API key (trading permissions optional)
4. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   HYPERLIQUID_API_KEY = "..."
   HYPERLIQUID_API_SECRET = "..."  # Only for trading
   ```

**Used By**: Execution, Hunter AI, Risk Analyzer agents

---

#### **7. DeFiLlama** ✅ **FREE**
- **Purpose**: Protocol TVL, yield data, 15k+ protocols
- **Get from**: N/A (public API)
- **Pricing**: Free, no limits
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_defillama = true`

**Setup**: No setup required - just enable feature flag

**Used By**: Research, DeFi Yield, Risk Analyzer agents

---

#### **8. The Graph** 🟡 **RECOMMENDED**
- **Purpose**: GraphQL queries for Uniswap, Aave, other protocols
- **Get from**: https://thegraph.com/studio/
- **Pricing**:
  - Free: 100k queries/month
  - Growth: $99/month (3M queries)
- **Environment Variable**: `THEGRAPH_API_KEY`
- **Feature Flag**: 
  - `agent_squad.external_apis.enable_uniswap = true`
  - `agent_squad.external_apis.enable_aave = true`

**Setup**:
1. Sign up at https://thegraph.com/studio/
2. Create API key
3. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   THEGRAPH_API_KEY = "..."
   ```

**Used By**: Execution, DeFi Yield, Lending/Borrowing agents

---

#### **9. Curve Finance** ✅ **FREE**
- **Purpose**: Stablecoin swap data, pool APY
- **Get from**: N/A (public API)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_curve = true`

**Used By**: DeFi Yield, Execution agents

---

### **Week 3: Enterprise & Security APIs**

#### **10. Chainalysis** 🔴 **ENTERPRISE ONLY**
- **Purpose**: AML/KYC screening, sanctions compliance
- **Get from**: https://www.chainalysis.com/contact/
- **Pricing**: ~$20k/year (enterprise license)
- **Environment Variable**: `CHAINALYSIS_API_KEY`
- **Feature Flag**: `agent_squad.external_apis.enable_chainalysis = false`

**Setup**:
1. Contact Chainalysis sales
2. Negotiate enterprise license
3. Receive API credentials
4. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   CHAINALYSIS_API_KEY = "..."
   ```

**Required For**: Compliance Monitor agent (production only)

---

#### **11. TRM Labs** 🔴 **ENTERPRISE ONLY**
- **Purpose**: Alternative to Chainalysis for AML/KYC
- **Get from**: https://www.trmlabs.com/contact
- **Pricing**: Enterprise pricing
- **Environment Variable**: `TRM_LABS_API_KEY`
- **Feature Flag**: `agent_squad.external_apis.enable_trm_labs = false`

**Used By**: Compliance Monitor agent (alternative to Chainalysis)

---

#### **12. Forta Network** 🟡 **RECOMMENDED**
- **Purpose**: Real-time security alerts, anomaly detection
- **Get from**: https://app.forta.network/
- **Pricing**: Free tier, Pro for advanced features
- **Environment Variable**: `FORTA_API_KEY`
- **Feature Flag**: `agent_squad.external_apis.enable_forta = true`

**Setup**:
1. Sign up at https://app.forta.network/
2. Create API key
3. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   FORTA_API_KEY = "..."
   ```

**Used By**: Alert Monitoring, Crisis Manager agents

---

#### **13. Twilio** 🟠 **OPTIONAL**
- **Purpose**: SMS/voice alerts for critical events
- **Get from**: https://console.twilio.com/
- **Pricing**: Pay-as-you-go (~$0.0075/SMS)
- **Environment Variables**:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_PHONE_NUMBER`
- **Feature Flag**: `agent_squad.external_apis.enable_twilio = false`

**Setup**:
1. Sign up at https://www.twilio.com/
2. Get Account SID and Auth Token
3. Purchase phone number
4. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   TWILIO_ACCOUNT_SID = "AC..."
   TWILIO_AUTH_TOKEN = "..."
   TWILIO_PHONE_NUMBER = "+1..."
   ```

**Used By**: Alert Monitoring, Crisis Manager agents

---

### **Week 4: Advanced APIs**

#### **14. Privy** 🟡 **RECOMMENDED**
- **Purpose**: Embedded wallet, user authentication
- **Get from**: Privy Dashboard > Settings > API Keys
- **Pricing**:
  - Free: up to 1000 MAU
  - Pro: $99/month (unlimited)
- **Environment Variables**:
  - `PRIVY_APP_ID`
  - `PRIVY_APP_SECRET`
- **Feature Flag**: `agent_squad.external_apis.enable_privy = false`

**Setup**: Already configured in main Privy section

**Used By**: Execution agent

---

#### **15. OpenSea API** 🟠 **OPTIONAL**
- **Purpose**: NFT market data, valuations
- **Get from**: https://docs.opensea.io/
- **Pricing**: Free tier (rate limited)
- **Environment Variable**: `OPENSEA_API_KEY`
- **Feature Flag**: `agent_squad.external_apis.enable_opensea = false`

**Setup**:
1. Sign up at https://opensea.io/
2. Request API key
3. Add to `.secrets.toml`:
   ```toml
   [external_apis]
   OPENSEA_API_KEY = "..."
   ```

**Used By**: NFT Asset Manager agent

---

#### **16. Axelar Network** ✅ **FREE**
- **Purpose**: Cross-chain messaging, asset bridging
- **Get from**: N/A (public RPC)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_axelar = true`

**Used By**: Bridge & Cross-Chain agent

---

#### **17. LayerZero** ✅ **FREE**
- **Purpose**: Omnichain interoperability
- **Get from**: N/A (public)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_layerzero = true`

**Used By**: Bridge & Cross-Chain agent

---

#### **18. Snapshot** ✅ **FREE**
- **Purpose**: DAO governance, voting
- **Get from**: N/A (public GraphQL API)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_snapshot = true`

**Used By**: DAO Governance agent

---

## 💰 **Cost Breakdown**

### **Development/Testing** (~$5-20/month)
```
✅ Free APIs:
- DeFiLlama (protocol data)
- Curve (stablecoin data)
- Snapshot (DAO governance)
- Axelar/LayerZero (bridging)

💰 Required LLM Providers:
- Vertex AI Gemini Flash: ~$5-15/month (low usage)
- DeepInfra: ~$0-5/month (fallback only)

Total: ~$5-20/month
```

### **Production - Basic** (~$400-500/month)
```
All Free APIs +
💰 LLM Providers:
- Vertex AI Gemini Flash/Pro: ~$50-150/month (depending on usage)
- DeepInfra: ~$10-30/month (fallback usage)

📊 DeFi Data APIs:
- 1inch Pro: $49/month
- CoinGecko Pro: $129/month
- The Graph Growth: $99/month
- Forta Pro: $50/month
- Twilio (5k SMS): $37.50/month

Total: ~$424-550/month
```

### **Production - Enterprise** ($2,330/month)
```
Basic APIs +
- Chainalysis: $1,667/month (~$20k/year)
- OpenSea Pro: $200/month
- Privy Pro: $99/month

Total: ~$2,330/month
```

---

## 🚀 **Quick Setup Commands**

### **1. Copy Templates**
```bash
# Copy environment template
cp config/local/.env.example config/local/.env

# Edit secrets file
vim config/local/.secrets.toml
```

### **2. Add Required Keys**
```bash
# Minimum for testing (LLM providers)
export VERTEX_AI_PROJECT_ID="your-gcp-project-id"

# Authentication (choose ONE method):
# Method 1: Direct path (for distillation config)
export VERTEX_AI_CREDENTIALS_PATH="/path/to/credentials.json"

# Method 2: Standard Google Cloud env var (for orchestrator)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Method 3: If running on GCP, no credentials needed (uses ADC)

export DEEPINFRA_API_KEY="..."  # Recommended fallback

# Recommended for production (DeFi data)
export COINGECKO_API_KEY="CG-..."
export ONEINCH_API_KEY="..."
export THEGRAPH_API_KEY="..."
```

### **3. Enable Feature Flags**
Edit `config/local/config.toml`:
```toml
[agent_squad.external_apis]
enable_coingecko = true
enable_1inch = true
enable_defillama = true
enable_hyperliquid = true
```

### **4. Verify Setup**
```bash
# Check environment variables
env | grep -E "(VERTEX_AI|DEEPINFRA|COINGECKO|ONEINCH)"

# Test Vertex AI connection
python -c "from app.infrastructure.llm.providers.vertex_ai_adapter import VertexAIAdapter; import asyncio; print('Vertex AI configured')"

# Test DeepInfra connection
python -c "from app.infrastructure.adapters.ai.llm.deepinfra import DeepInfraStrategy; print('DeepInfra configured')"
```

---

## 🔒 **Security Best Practices**

1. **Never commit API keys**
   - `.secrets.toml` is in `.gitignore`
   - Use environment variables in production

2. **Rotate keys regularly**
   - Change keys every 90 days
   - Revoke unused keys

3. **Use environment-specific keys**
   - Development: Free tier keys
   - Staging: Separate paid keys
   - Production: Enterprise keys with monitoring

4. **Monitor usage**
   - Set up billing alerts
   - Track API call counts
   - Watch for anomalies

5. **Rate limiting**
   - Implement client-side rate limiting
   - Cache API responses (Redis)
   - Use webhooks where available

---

## ❓ **Troubleshooting**

### **"API key not found" error**
```bash
# Check if Vertex AI project ID is set
echo $VERTEX_AI_PROJECT_ID

# Check authentication method (choose one):
echo $VERTEX_AI_CREDENTIALS_PATH  # For distillation
echo $GOOGLE_APPLICATION_CREDENTIALS  # For orchestrator

# Verify credentials file exists
test -f "$VERTEX_AI_CREDENTIALS_PATH" && echo "Credentials file exists" || echo "Credentials file not found"

# Check if DeepInfra key is set
echo $DEEPINFRA_API_KEY

# Check TOML file
cat config/local/.secrets.toml | grep -E "(VERTEX_AI|DEEPINFRA|COINGECKO)"
```

### **"Authentication failed" error for Vertex AI**
- **Local Development**: Ensure `VERTEX_AI_CREDENTIALS_PATH` or `GOOGLE_APPLICATION_CREDENTIALS` points to valid JSON file
- **GCP Environment**: Verify Application Default Credentials are configured
- **Service Account**: Ensure the service account has "Vertex AI User" role
- **Project ID**: Verify `VERTEX_AI_PROJECT_ID` matches your GCP project

### **"Rate limit exceeded" error**
- Upgrade to paid tier
- Implement caching (Redis)
- Reduce request frequency

### **"Authentication failed" error**
- Verify key is correct
- Check key hasn't expired
- Ensure key has required permissions

---

## 📚 **Additional Resources**

- **API Documentation**: `docs/specs/integrations/PHASE7_API_INTEGRATION_PLAN.md`
- **Feature Flags**: `config/local/config.toml`
- **Environment Template**: `config/local/.env.example`
- **Secrets File**: `config/local/.secrets.toml` (not tracked in git)

---

**Last Updated**: December 1, 2025  
**Next Review**: After Week 2 APIs implementation

---

## 📝 **LLM Provider Architecture**

### **Provider Priority**
1. **Vertex AI (Primary)** - Google Gemini models, fast and cost-effective
2. **DeepInfra (Fallback)** - Open-source models (Llama, Mixtral), very cheap
3. **OpenAI (Optional)** - GPT-4 available as additional fallback

### **Why Vertex AI + DeepInfra?**
- **Cost Efficiency**: Vertex AI Gemini Flash is ~10x cheaper than GPT-4
- **Performance**: Gemini 1.5 Pro matches GPT-4 quality at lower cost
- **Reliability**: DeepInfra provides excellent fallback with open-source models
- **Flexibility**: Multi-provider orchestration ensures high availability

### **Configuration Reference**
See `docs/setup/API_INTEGRATIONS_CONFIGURATION.md` for detailed LLM provider setup.

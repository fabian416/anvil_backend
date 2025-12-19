# 🔌 API Integrations Configuration Guide

**Document**: Complete API Integration Setup  
**Date**: December 6, 2025  
**Version**: 2.0  
**Status**: ✅ Enterprise-Grade Implementation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [LLM Provider APIs](#llm-provider-apis)
4. [DeFi Data APIs](#defi-data-apis)
5. [Security & Compliance APIs](#security--compliance-apis)
6. [Communication APIs](#communication-apis)
7. [Wallet & Authentication APIs](#wallet--authentication-apis)
8. [Blockchain RPC Endpoints](#blockchain-rpc-endpoints)
9. [NFT & Governance APIs](#nft--governance-apis)
10. [Monitoring & Analytics APIs](#monitoring--analytics-apis)
11. [Configuration Reference](#configuration-reference)
12. [Cost Estimation](#cost-estimation)
13. [Troubleshooting](#troubleshooting)

---

## Overview

Anvil Backend integrates with **30+ external APIs** to power the 18-agent DeFi platform. This guide provides step-by-step instructions for configuring each integration.

### Configuration Files

| File | Purpose |
|------|---------|
| `config/{env}/config.toml` | Feature flags and non-sensitive settings |
| `config/{env}/.secrets.toml` | API keys and sensitive credentials |
| `config/{env}/export.toml` | Environment variable mappings |

---

## Quick Start

### 1. Copy the secrets template
```bash
cp config/local/.secrets.toml.example config/local/.secrets.toml
chmod 600 config/local/.secrets.toml
```

### 2. Add minimum required keys
```toml
# config/local/.secrets.toml

[llm]
OPENAI_API_KEY = "sk-proj-your-key-here"
```

### 3. Start the server
```bash
make start
```

---

## LLM Provider APIs

### 1. Google Vertex AI ⭐ PRIMARY PROVIDER

| Property | Value |
|----------|-------|
| **Purpose** | Primary LLM provider, distillation, fast inference |
| **URL** | https://console.cloud.google.com/vertex-ai |
| **Pricing** | Gemini 1.5 Flash: ~$0.00001875/1K chars, Gemini 1.5 Pro: ~$0.00125/1K chars |
| **Required** | ⭐ Primary (Recommended) |

**Setup Instructions:**

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable **Vertex AI API**:
   - Go to **APIs & Services** → **Enable APIs**
   - Search for "Vertex AI API" and enable it
4. Create a Service Account:
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: `anvil-vertex-ai`
   - Grant role: **Vertex AI User**
5. Create and download JSON key:
   - Click on the service account
   - Go to **Keys** tab → **Add Key** → **Create new key**
   - Select JSON format
   - Save the file securely (e.g., `/path/to/vertex-ai-credentials.json`)

**Configuration:**
```toml
# config/local/.secrets.toml
[vertex_ai]
PROJECT_ID = "your-gcp-project-id"
CREDENTIALS_PATH = "/path/to/vertex-ai-credentials.json"

# config/local/config.toml
[distillation]
provider = "vertex_ai"
fallback_provider = "deepinfra"

[distillation.vertex_ai]
project_id = "your-gcp-project-id"
location = "us-central1"
model = "gemini-1.5-flash"

[llm_orchestration]
default_provider = "vertex_ai"
fallback_providers = ["openai", "anthropic", "deepinfra"]
```

**Environment Variables:**
- `VERTEX_AI_PROJECT_ID`
- `VERTEX_AI_CREDENTIALS_PATH`
- `GOOGLE_APPLICATION_CREDENTIALS` (alternative)

**Available Models:**
| Model | Use Case | Speed | Cost |
|-------|----------|-------|------|
| `gemini-1.5-flash` | Fast inference, distillation | ⚡ Fastest | 💰 Cheapest |
| `gemini-1.5-pro` | Complex reasoning | Medium | Medium |
| `gemini-1.0-pro` | General purpose | Fast | Low |

**Used By:** Distillation engine, all 18 agents (primary), LLM orchestration carousel

---

### 2. OpenAI ⭐ FALLBACK PROVIDER

| Property | Value |
|----------|-------|
| **Purpose** | Fallback LLM, GPT-4 for complex tasks |
| **URL** | https://platform.openai.com/api-keys |
| **Pricing** | Pay-as-you-go (~$0.01-0.03/1K tokens for GPT-4) |
| **Required** | ⚠️ Recommended as fallback |

**Setup Instructions:**

1. Create account at https://platform.openai.com/
2. Navigate to **API Keys** → **Create new secret key**
3. Copy the key (starts with `sk-proj-`)

**Configuration:**
```toml
# config/local/.secrets.toml
[llm]
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxxxxxxxxx"
```

**Environment Variable:** `OPENAI_API_KEY`

**Used By:** Fallback for all agents, intent classification, supervisor coordination

---

### 4. Anthropic (Claude)

| Property | Value |
|----------|-------|
| **Purpose** | Alternative LLM provider, secondary fallback |
| **URL** | https://console.anthropic.com/settings/keys |
| **Pricing** | ~$0.015/1K input, $0.075/1K output (Claude 3.5 Sonnet) |
| **Required** | 🟡 Optional fallback |

**Setup Instructions:**

1. Create account at https://console.anthropic.com/
2. Go to **Settings** → **API Keys**
3. Create new key

**Configuration:**
```toml
# config/local/.secrets.toml
[llm]
ANTHROPIC_API_KEY = "sk-ant-api03-xxxxxxxxxxxxxxxxxxxx"
```

**Environment Variable:** `ANTHROPIC_API_KEY`

---

### 5. Google AI Studio (Alternative)

| Property | Value |
|----------|-------|
| **Purpose** | Alternative to Vertex AI for simple use cases |
| **URL** | https://aistudio.google.com/app/apikey |
| **Pricing** | Free tier: 60 QPM, Pro: Pay-as-you-go |
| **Required** | 🟡 Optional (use Vertex AI instead) |

> **Note:** For production, use **Vertex AI** (Section 1) instead. Google AI Studio is simpler but has rate limits.

**Setup Instructions:**

1. Go to https://aistudio.google.com/
2. Click **Get API Key** → **Create API key**
3. Select or create a Google Cloud project

**Configuration:**
```toml
# config/local/.secrets.toml
[llm]
GOOGLE_API_KEY = "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Environment Variable:** `GOOGLE_API_KEY`

---

### 7. xAI (Grok)

| Property | Value |
|----------|-------|
| **Purpose** | Real-time data, alternative LLM |
| **URL** | https://x.ai/ |
| **Pricing** | Contact for pricing |
| **Required** | 🟡 Optional |

**Configuration:**
```toml
[llm]
XAI_API_KEY = "xai-xxxxxxxxxxxxxxxxxxxx"
```

---

### 8. DeepInfra

| Property | Value |
|----------|-------|
| **Purpose** | Fast inference, Llama models, cost-effective |
| **URL** | https://deepinfra.com/dash/api_keys |
| **Pricing** | ~$0.0003/1K tokens (Llama 3.2) |
| **Required** | ⚠️ Recommended for distillation fallback |

**Setup Instructions:**

1. Create account at https://deepinfra.com/
2. Go to **Dashboard** → **API Keys**
3. Create new key

**Configuration:**
```toml
[llm]
DEEPINFRA_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Environment Variable:** `DEEPINFRA_API_KEY`

---

### 9. Perplexity

| Property | Value |
|----------|-------|
| **Purpose** | Real-time web search, research agent |
| **URL** | https://www.perplexity.ai/settings/api |
| **Pricing** | $0.20/1K tokens (Pro) |
| **Required** | 🟡 Optional (enhances Research agent) |

**Setup Instructions:**

1. Create account at https://www.perplexity.ai/
2. Go to **Settings** → **API**
3. Generate API key

**Configuration:**
```toml
[llm]
PERPLEXITY_API_KEY = "pplx-xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_perplexity = true
```

---

## DeFi Data APIs

### 10. 1inch DEX Aggregator

| Property | Value |
|----------|-------|
| **Purpose** | DEX aggregation, swap quotes, optimal routing |
| **URL** | https://portal.1inch.dev/ |
| **Pricing** | Free: 1 req/sec, Pro: $49/mo (10 req/sec) |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://portal.1inch.dev/
2. Create new project
3. Generate API key

**Configuration:**
```toml
# config/local/.secrets.toml
[external_apis]
ONEINCH_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_1inch = true
```

**Used By:** Execution agent, Hunter AI agent

---

### 8. CoinGecko

| Property | Value |
|----------|-------|
| **Purpose** | Price data, market caps, token info |
| **URL** | https://www.coingecko.com/en/api/pricing |
| **Pricing** | Free: 10-50 calls/min, Pro: $129/mo |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://www.coingecko.com/
2. Go to **Developer Dashboard**
3. Get Demo API key (free) or subscribe to Pro

**Configuration:**
```toml
[external_apis]
COINGECKO_API_KEY = "CG-xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_coingecko = true
```

**Used By:** Hunter AI, Portfolio, Risk Analyzer agents

---

### 9. DeFiLlama ✅ FREE

| Property | Value |
|----------|-------|
| **Purpose** | Protocol TVL, yield data, 15k+ protocols |
| **URL** | https://defillama.com/docs/api |
| **Pricing** | Free, no limits |
| **Required** | ✅ Yes (no key needed) |

**Configuration:**
```toml
# No API key required - just enable the feature flag
[agent_squad.external_apis]
enable_defillama = true
```

**Used By:** Research, DeFi Yield, Risk Analyzer agents

---

### 10. The Graph

| Property | Value |
|----------|-------|
| **Purpose** | GraphQL queries for Uniswap, Aave, etc. |
| **URL** | https://thegraph.com/studio/ |
| **Pricing** | Free: 100k queries/mo, Growth: $99/mo |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://thegraph.com/studio/
2. Create new API key
3. Add billing for production

**Configuration:**
```toml
[external_apis]
THEGRAPH_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flags:**
```toml
[agent_squad.external_apis]
enable_uniswap = true
enable_aave = true
enable_curve = true
```

**Used By:** DeFi Yield, Lending/Borrowing, Execution agents

---

### 11. Hyperliquid

| Property | Value |
|----------|-------|
| **Purpose** | Perpetual futures, liquidation data |
| **URL** | https://app.hyperliquid.xyz/ |
| **Pricing** | Free for market data |
| **Required** | 🟡 Optional |

**Setup Instructions:**

1. Create account at https://app.hyperliquid.xyz/
2. Go to **Settings** → **API Keys**
3. Create read-only key (or trading key if needed)

**Configuration:**
```toml
[external_apis]
HYPERLIQUID_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
HYPERLIQUID_API_SECRET = "xxxxxxxxxxxxxxxxxxxx"  # Only for trading
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_hyperliquid = true
```

---

### 12. Etherscan

| Property | Value |
|----------|-------|
| **Purpose** | Transaction data, contract verification, gas prices |
| **URL** | https://etherscan.io/apis |
| **Pricing** | Free: 5 calls/sec, Pro: $199/mo |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://etherscan.io/register
2. Go to **API Keys** → **Add**
3. Create new key

**Configuration:**
```toml
[external_apis]
ETHERSCAN_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_gas_oracle = true
```

**Used By:** Gas Optimizer, Security Auditor agents

---

### 13. Blocknative

| Property | Value |
|----------|-------|
| **Purpose** | Mempool monitoring, gas estimation |
| **URL** | https://www.blocknative.com/gas-platform |
| **Pricing** | Free tier available, Pro: Contact sales |
| **Required** | 🟡 Optional (enhances Gas Optimizer) |

**Setup Instructions:**

1. Sign up at https://www.blocknative.com/
2. Create API key in dashboard

**Configuration:**
```toml
[external_apis]
BLOCKNATIVE_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

---

## Security & Compliance APIs

### 14. Chainalysis 🔴 ENTERPRISE

| Property | Value |
|----------|-------|
| **Purpose** | AML/KYC screening, sanctions compliance |
| **URL** | https://www.chainalysis.com/contact/ |
| **Pricing** | ~$20k/year (enterprise license) |
| **Required** | 🔴 Enterprise only |

**Setup Instructions:**

1. Contact Chainalysis sales team
2. Negotiate enterprise license
3. Receive API credentials after contract

**Configuration:**
```toml
[external_apis]
CHAINALYSIS_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_chainalysis = true  # Only enable with valid license
```

**Used By:** Compliance Monitor agent

---

### 15. TRM Labs 🔴 ENTERPRISE

| Property | Value |
|----------|-------|
| **Purpose** | Alternative AML/KYC provider |
| **URL** | https://www.trmlabs.com/contact |
| **Pricing** | Enterprise pricing |
| **Required** | 🔴 Enterprise only |

**Configuration:**
```toml
[external_apis]
TRM_LABS_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_trm_labs = true
```

---

### 16. Forta Network

| Property | Value |
|----------|-------|
| **Purpose** | Real-time security alerts, threat detection |
| **URL** | https://app.forta.network/ |
| **Pricing** | Free tier, Pro for advanced |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://app.forta.network/
2. Navigate to **API** section
3. Generate API key

**Configuration:**
```toml
[external_apis]
FORTA_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_forta = true
```

**Used By:** Alert Monitoring, Crisis Manager, Security Auditor agents

---

### 17. Slither (Local)

| Property | Value |
|----------|-------|
| **Purpose** | Smart contract static analysis |
| **URL** | https://github.com/crytic/slither |
| **Pricing** | Free (open source) |
| **Required** | 🟡 Optional |

**Setup Instructions:**

```bash
# Install via pip
pip install slither-analyzer

# Or use Docker
docker pull trailofbits/slither
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_slither = true
```

**Used By:** Security Auditor agent

---

## Communication APIs

### 18. Twilio

| Property | Value |
|----------|-------|
| **Purpose** | SMS/voice alerts for critical events |
| **URL** | https://console.twilio.com/ |
| **Pricing** | ~$0.0075/SMS |
| **Required** | 🟡 Optional |

**Setup Instructions:**

1. Sign up at https://www.twilio.com/
2. Get Account SID and Auth Token from dashboard
3. Purchase a phone number

**Configuration:**
```toml
[external_apis]
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxx"
TWILIO_PHONE_NUMBER = "+1234567890"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_twilio = true
```

**Used By:** Alert Monitoring, Crisis Manager agents

---

### 19. Mailgun

| Property | Value |
|----------|-------|
| **Purpose** | Transactional emails, notifications |
| **URL** | https://app.mailgun.com/ |
| **Pricing** | Free: 5k emails/mo, Flex: $0.80/1k emails |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://www.mailgun.com/
2. Verify domain
3. Get API key from **API Keys** section

**Configuration:**
```toml
[mailgun]
DOMAIN = "mg.yourdomain.com"
API_KEY = "key-xxxxxxxxxxxxxxxxxxxx"
FROM_EMAIL = "noreply@yourdomain.com"
ENABLED = true
```

---

## Wallet & Authentication APIs

### 20. Privy

| Property | Value |
|----------|-------|
| **Purpose** | Embedded wallets, user authentication |
| **URL** | https://dashboard.privy.io/ |
| **Pricing** | Free: 1k MAU, Pro: $99/mo |
| **Required** | ⚠️ Recommended |

**Setup Instructions:**

1. Sign up at https://privy.io/
2. Create new app in dashboard
3. Get App ID and App Secret

**Configuration:**
```toml
# config/local/config.toml
[privy]
APP_ID = "your-app-id"
BASE_URL = "https://auth.privy.io"
EMBEDDED_WALLET_ENABLED = true

# config/local/.secrets.toml
[privy]
APP_SECRET = "xxxxxxxxxxxxxxxxxxxx"
VERIFICATION_KEY = "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_privy = true
```

**Used By:** Execution agent, wallet operations

---

### 21. Gnosis Safe

| Property | Value |
|----------|-------|
| **Purpose** | Multi-signature wallet operations |
| **URL** | https://safe.global/ |
| **Pricing** | Free |
| **Required** | 🟡 Optional |

**Configuration:**
```toml
[agent_squad.external_apis]
enable_gnosis_safe = true
```

**Used By:** Multisig Coordinator agent

---

## Blockchain RPC Endpoints

### 22. Ethereum Mainnet

| Provider | URL | Free Tier |
|----------|-----|-----------|
| Alchemy | https://www.alchemy.com/ | 300M CU/mo |
| Infura | https://infura.io/ | 100k req/day |
| QuickNode | https://www.quicknode.com/ | Limited |

**Configuration:**
```toml
[rpc]
ETH_MAINNET_RPC = "https://eth-mainnet.g.alchemy.com/v2/your-api-key"
```

---

### 23. Polygon

**Configuration:**
```toml
[rpc]
POLYGON_RPC = "https://polygon-mainnet.g.alchemy.com/v2/your-api-key"
```

---

### 24. Arbitrum

**Configuration:**
```toml
[rpc]
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/your-api-key"
```

---

### 25. Optimism

**Configuration:**
```toml
[rpc]
OPTIMISM_RPC = "https://opt-mainnet.g.alchemy.com/v2/your-api-key"
```

---

### 26. Base

**Configuration:**
```toml
[rpc]
BASE_RPC = "https://base-mainnet.g.alchemy.com/v2/your-api-key"
```

---

## NFT & Governance APIs

### 27. OpenSea

| Property | Value |
|----------|-------|
| **Purpose** | NFT market data, valuations |
| **URL** | https://docs.opensea.io/ |
| **Pricing** | Free tier available |
| **Required** | 🟡 Optional |

**Setup Instructions:**

1. Go to https://docs.opensea.io/
2. Request API key
3. Wait for approval

**Configuration:**
```toml
[external_apis]
OPENSEA_API_KEY = "xxxxxxxxxxxxxxxxxxxx"
```

**Feature Flag:**
```toml
[agent_squad.external_apis]
enable_opensea = true
```

**Used By:** NFT Asset Manager agent

---

### 28. Snapshot ✅ FREE

| Property | Value |
|----------|-------|
| **Purpose** | DAO governance, voting |
| **URL** | https://docs.snapshot.org/ |
| **Pricing** | Free |
| **Required** | 🟡 Optional |

**Configuration:**
```toml
[agent_squad.external_apis]
enable_snapshot = true
```

**Used By:** DAO Governance agent

---

### 29. Axelar ✅ FREE

| Property | Value |
|----------|-------|
| **Purpose** | Cross-chain messaging |
| **URL** | https://axelar.network/ |
| **Pricing** | Free (gas fees only) |
| **Required** | 🟡 Optional |

**Configuration:**
```toml
[agent_squad.external_apis]
enable_axelar = true
```

**Used By:** Bridge & Cross-Chain agent

---

### 30. LayerZero ✅ FREE

| Property | Value |
|----------|-------|
| **Purpose** | Omnichain interoperability |
| **URL** | https://layerzero.network/ |
| **Pricing** | Free |
| **Required** | 🟡 Optional |

**Configuration:**
```toml
[agent_squad.external_apis]
enable_layerzero = true
```

**Used By:** Bridge & Cross-Chain agent

---

## Monitoring & Analytics APIs

### 31. Sentry

| Property | Value |
|----------|-------|
| **Purpose** | Error tracking, performance monitoring |
| **URL** | https://sentry.io/ |
| **Pricing** | Free: 5k errors/mo, Team: $26/mo |
| **Required** | ⚠️ Recommended for production |

**Setup Instructions:**

1. Sign up at https://sentry.io/
2. Create new project (Python/FastAPI)
3. Get DSN from project settings

**Configuration:**
```toml
[sentry]
DSN = "https://xxx@xxx.ingest.sentry.io/xxx"
ENVIRONMENT = "local"  # or "production"
TRACES_SAMPLE_RATE = 0.1  # 10% sampling
```

---

### 32. Vertex AI (Google Cloud)

| Property | Value |
|----------|-------|
| **Purpose** | Distillation engine, fast inference |
| **URL** | https://console.cloud.google.com/vertex-ai |
| **Pricing** | Pay-as-you-go |
| **Required** | 🟡 Optional |

**Setup Instructions:**

1. Enable Vertex AI API in Google Cloud Console
2. Create service account with Vertex AI User role
3. Download JSON credentials

**Configuration:**
```toml
[vertex_ai]
PROJECT_ID = "your-project-id"
CREDENTIALS_PATH = "/path/to/service-account.json"

[distillation.vertex_ai]
project_id = "your-project-id"
location = "us-central1"
model = "gemini-1.5-flash"
```

---

## Configuration Reference

### Complete .secrets.toml Template

```toml
# ============================================================================
# ANVIL BACKEND - SECRETS CONFIGURATION
# ============================================================================

# PostgreSQL
[postgres]
USER = "anvil_user"
PASSWORD = "your-secure-password"

# Redis
[redis]
PASSWORD = "your-redis-password"

# Security
[security.auth]
JWT_SECRET = "your-64-char-secret-here"
JWT_ALGORITHM = "HS256"

[security.cookies]
SECURE = false  # true in production

[security.password]
PEPPER = "your-64-char-pepper-here"

# LLM API Keys
[llm]
OPENAI_API_KEY = "sk-proj-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "AIza..."
XAI_API_KEY = "xai-..."
DEEPINFRA_API_KEY = "..."
PERPLEXITY_API_KEY = "pplx-..."

# External APIs
[external_apis]
ONEINCH_API_KEY = "..."
COINGECKO_API_KEY = "CG-..."
THEGRAPH_API_KEY = "..."
ETHERSCAN_API_KEY = "..."
BLOCKNATIVE_API_KEY = "..."
HYPERLIQUID_API_KEY = "..."
HYPERLIQUID_API_SECRET = "..."
FORTA_API_KEY = "..."
CHAINALYSIS_API_KEY = "..."
TRM_LABS_API_KEY = "..."
OPENSEA_API_KEY = "..."
TWILIO_ACCOUNT_SID = "AC..."
TWILIO_AUTH_TOKEN = "..."
TWILIO_PHONE_NUMBER = "+1..."

# Privy
[privy]
APP_ID = "..."
APP_SECRET = "..."
VERIFICATION_KEY = "..."

# Stripe
[stripe]
STRIPE_API_KEY = "sk_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."
STRIPE_PUBLIC_KEY = "pk_..."

# Mailgun
[mailgun]
DOMAIN = "mg.yourdomain.com"
API_KEY = "key-..."

# RPC Endpoints
[rpc]
ETH_MAINNET_RPC = "https://eth-mainnet.g.alchemy.com/v2/..."
POLYGON_RPC = "https://polygon-mainnet.g.alchemy.com/v2/..."
ARBITRUM_RPC = "https://arb-mainnet.g.alchemy.com/v2/..."
OPTIMISM_RPC = "https://opt-mainnet.g.alchemy.com/v2/..."
BASE_RPC = "https://base-mainnet.g.alchemy.com/v2/..."

# Sentry
[sentry]
DSN = "https://...@sentry.io/..."
ENVIRONMENT = "local"
TRACES_SAMPLE_RATE = 0.1
```

---

## Cost Estimation

### Development (Free Tier)
| Service | Cost |
|---------|------|
| OpenAI | ~$5-20/mo (testing) |
| Free APIs | $0 |
| **Total** | **~$5-20/mo** |

### Production - Basic
| Service | Cost |
|---------|------|
| OpenAI | ~$100-500/mo |
| 1inch Pro | $49/mo |
| CoinGecko Pro | $129/mo |
| The Graph | $99/mo |
| Alchemy Growth | $49/mo |
| Sentry Team | $26/mo |
| **Total** | **~$450-850/mo** |

### Production - Enterprise
| Service | Cost |
|---------|------|
| All Basic | ~$500/mo |
| Chainalysis | ~$1,700/mo |
| OpenSea Pro | $200/mo |
| Privy Pro | $99/mo |
| Enterprise RPC | ~$500/mo |
| **Total** | **~$3,000/mo** |

---

## Troubleshooting

### Common Issues

**1. "API key not found"**
```bash
# Check if key is loaded
PYTHONPATH=src python -c "
from app.setup.config.loader import load_full_config, ValidEnvs
config = load_full_config(ValidEnvs.LOCAL)
print(config.get('llm', {}).get('OPENAI_API_KEY', 'NOT SET'))
"
```

**2. "Rate limit exceeded"**
- Enable caching in Redis
- Upgrade to paid tier
- Implement request queuing

**3. "Authentication failed"**
- Verify key format is correct
- Check key hasn't expired
- Ensure key has required permissions

**4. "Connection timeout"**
- Check network connectivity
- Verify API endpoint is correct
- Increase timeout settings

### Verify All APIs

```bash
# Run API verification script
PYTHONPATH=src python -c "
from app.setup.config.loader import load_full_config, ValidEnvs

config = load_full_config(ValidEnvs.LOCAL)

print('=== LLM API Keys ===')
llm = config.get('llm', {})
for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']:
    status = '✅' if llm.get(key) else '❌'
    print(f'{status} {key}')

print('\n=== External APIs ===')
apis = config.get('external_apis', {})
for key in ['ONEINCH_API_KEY', 'COINGECKO_API_KEY', 'THEGRAPH_API_KEY']:
    status = '✅' if apis.get(key) else '❌'
    print(f'{status} {key}')
"
```

---

## Related Documentation

- [API Keys Setup (Quick Reference)](./API_KEYS_SETUP.md)
- [Feature Flags Reference](../FEATURE_FLAGS_IMPLEMENTATION.md)
- [Security Guide](../security/05_security_compliance.md)
- [Secrets Template](../../config/local/.secrets.toml.example)

---

**Last Updated**: December 6, 2025  
**Maintainer**: Anvil Backend Team

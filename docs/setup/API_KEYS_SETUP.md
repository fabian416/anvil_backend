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
# Minimum required keys
OPENAI_API_KEY=sk-...  # ✅ Required for all agents
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

### **Week 1: DeFi Data APIs**

#### **1. OpenAI** ✅ **REQUIRED**
- **Purpose**: Powers all agent LLM capabilities
- **Get from**: https://platform.openai.com/api-keys
- **Pricing**: Pay-as-you-go (~$0.002/1K tokens)
- **Environment Variable**: `OPENAI_API_KEY`
- **Feature Flag**: N/A (always required)

**Setup**:
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create new API key
4. Add to `config/local/.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-...
   ```

---

#### **2. CoinGecko** 🟡 **RECOMMENDED**
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

#### **3. 1inch DEX Aggregator** 🟡 **RECOMMENDED**
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

#### **4. Hyperliquid** ✨ **NEW**
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

#### **5. DeFiLlama** ✅ **FREE**
- **Purpose**: Protocol TVL, yield data, 15k+ protocols
- **Get from**: N/A (public API)
- **Pricing**: Free, no limits
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_defillama = true`

**Setup**: No setup required - just enable feature flag

**Used By**: Research, DeFi Yield, Risk Analyzer agents

---

#### **6. The Graph** 🟡 **RECOMMENDED**
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

#### **7. Curve Finance** ✅ **FREE**
- **Purpose**: Stablecoin swap data, pool APY
- **Get from**: N/A (public API)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_curve = true`

**Used By**: DeFi Yield, Execution agents

---

### **Week 2: Enterprise & Security APIs**

#### **8. Chainalysis** 🔴 **ENTERPRISE ONLY**
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

#### **9. TRM Labs** 🔴 **ENTERPRISE ONLY**
- **Purpose**: Alternative to Chainalysis for AML/KYC
- **Get from**: https://www.trmlabs.com/contact
- **Pricing**: Enterprise pricing
- **Environment Variable**: `TRM_LABS_API_KEY`
- **Feature Flag**: `agent_squad.external_apis.enable_trm_labs = false`

**Used By**: Compliance Monitor agent (alternative to Chainalysis)

---

#### **10. Forta Network** 🟡 **RECOMMENDED**
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

#### **11. Twilio** 🟠 **OPTIONAL**
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

### **Week 3: Advanced APIs**

#### **12. Privy** 🟡 **RECOMMENDED**
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

#### **13. OpenSea API** 🟠 **OPTIONAL**
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

#### **14. Axelar Network** ✅ **FREE**
- **Purpose**: Cross-chain messaging, asset bridging
- **Get from**: N/A (public RPC)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_axelar = true`

**Used By**: Bridge & Cross-Chain agent

---

#### **15. LayerZero** ✅ **FREE**
- **Purpose**: Omnichain interoperability
- **Get from**: N/A (public)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_layerzero = true`

**Used By**: Bridge & Cross-Chain agent

---

#### **16. Snapshot** ✅ **FREE**
- **Purpose**: DAO governance, voting
- **Get from**: N/A (public GraphQL API)
- **Pricing**: Free
- **Environment Variable**: None required
- **Feature Flag**: `agent_squad.external_apis.enable_snapshot = true`

**Used By**: DAO Governance agent

---

## 💰 **Cost Breakdown**

### **Development/Testing** ($0/month)
```
✅ Free APIs only:
- DeFiLlama (protocol data)
- Curve (stablecoin data)
- Snapshot (DAO governance)
- Axelar/LayerZero (bridging)
- Gnosis Safe (multi-sig)

Total: $0/month
```

### **Production - Basic** ($364/month)
```
All Free APIs +
- 1inch Pro: $49/month
- CoinGecko Pro: $129/month
- The Graph Growth: $99/month
- Forta Pro: $50/month
- Twilio (5k SMS): $37.50/month

Total: $364.50/month
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
# Minimum for testing
export OPENAI_API_KEY="sk-proj-..."

# Recommended for production
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
env | grep -E "(OPENAI|COINGECKO|ONEINCH)"

# Test API client
python -c "from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient; import asyncio; client = CoinGeckoClient(); print(asyncio.run(client.get_price('ethereum')))"
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
# Check if key is set
echo $OPENAI_API_KEY

# Check TOML file
cat config/local/.secrets.toml | grep COINGECKO
```

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

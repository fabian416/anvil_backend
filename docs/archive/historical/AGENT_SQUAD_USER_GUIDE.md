# Agent Squad User Guide

**Document**: AgentSquad-UserGuide  
**Date**: December 1, 2025  
**Version**: 1.0  
**Audience**: End Users

---

## 🤖 Welcome to Agent Squad

Agent Squad is your intelligent DeFi co-pilot, featuring **18 specialist AI agents** that understand your needs and execute complex financial tasks automatically.

---

## 🎯 Quick Start

### 1. Start a Conversation

```
POST /api/v1/chat/conversations
Authorization: Bearer <your_token>

{
  "title": "My DeFi Portfolio"
}
```

### 2. Send a Message

```
POST /api/v1/chat/agent-squad/messages?conversation_id=<id>
Authorization: Bearer <your_token>

{
  "content": "What's the market sentiment for Bitcoin?"
}
```

### 3. Get Response

The system automatically:
- ✅ Classifies your intent (30+ categories)
- ✅ Routes to the best specialist agent (18 agents)
- ✅ Preserves conversation context
- ✅ Tracks performance metrics

---

## 🤖 Available Agents (18)

### Core User Agents (10) - All Tiers

**1. Chat Agent** 💬
- General conversation
- DeFi education
- Specialist referrals

**2. Hunter AI Agent** 📊
- Market sentiment analysis
- Price predictions
- Social media sentiment

**3. Research Agent** 🔍
- Deep protocol analysis
- Tokenomics breakdown
- Protocol comparisons

**4. Execution Agent** ⚡
- Token swaps (1inch, Uniswap)
- Transaction execution
- Safety: $10k limit, user confirmation

**5. Risk Analyzer Agent** ⚠️
- Risk scoring (0-100)
- Liquidation risk
- Protocol security

**6. Portfolio Agent** 📈
- Portfolio optimization (MPT)
- Rebalancing recommendations
- Sharpe ratio maximization

**7. Tax Optimizer Agent** 💰
- Tax-loss harvesting
- Capital gains calculation
- Tax-efficient strategies

**8. DeFi Yield Agent** 🌾
- Yield farming opportunities
- APY comparison
- Impermanent loss calculation

**9. Security Auditor Agent** 🔒
- Smart contract security
- Vulnerability detection
- Audit summaries

**10. Gas Optimizer Agent** ⛽
- Gas price tracking
- Optimal timing
- Layer 2 recommendations

---

### Enterprise Agents (8) - Enterprise Tier Only

**11. Compliance Monitor Agent** 🏛️
- AML/KYC screening
- OFAC sanction checks
- Risk scoring (automatic blocking)
- **Revenue**: Enterprise tier ($2,000+/month)

**12. Multi-Sig Coordinator Agent** 🏦
- Multi-sig treasury management
- Approval workflows
- Budget enforcement
- **Revenue**: Enterprise tier

**13. Alert Monitoring Agent** 🚨
- Real-time security alerts
- Anomaly detection
- Multi-channel notifications (SMS, email, push)
- **Revenue**: Pro tier ($100/month)

**14. Crisis Manager Agent** 🆘
- Emergency response (<5s)
- Auto-exit strategies
- Protocol exploit detection
- **Revenue**: Enterprise tier

**15. Bridge Crosschain Agent** 🌉
- Layer 2 bridging
- Cross-chain transfers
- Cost comparison
- **Revenue**: Pro tier

**16. Lending Borrowing Agent** 💵
- Leverage optimization
- Health factor monitoring
- Auto-rebalancing
- **Revenue**: Pro tier

**17. NFT Asset Manager Agent** 🖼️
- NFT portfolio tracking
- Rarity analysis
- Floor price monitoring
- **Revenue**: Pro tier

**18. DAO Governance Agent** 🗳️
- Proposal tracking
- Voting reminders
- Delegation management
- **Revenue**: Basic tier ($20/month)

---

## 💡 Example Conversations

### Example 1: Market Research

**You**: "What's the market sentiment for Ethereum today?"

**Hunter AI Agent** (2.3 seconds):
```
📊 ETHEREUM MARKET SENTIMENT

Sentiment Score: 75/100 (Bullish)

Key Drivers:
• ETF approval rumors (bullish)
• Strong on-chain metrics (bullish)
• Technical breakout (bullish)

Social Media:
• Twitter: 78/100 (positive)
• Reddit: 72/100 (positive)

Recommendation: BULLISH (short-term)

*Not financial advice*
```

---

### Example 2: Risk Analysis

**You**: "What's the risk of using Aave?"

**Risk Analyzer Agent** (1.8 seconds):
```
⚠️ AAVE RISK ASSESSMENT

Overall Risk: 🟢 LOW (28/100)

Risk Breakdown:
• Smart Contract: 15/100 (audited, battle-tested)
• Liquidation: 25/100 (conservative LTV)
• Oracle: 20/100 (Chainlink, redundant)
• Governance: 30/100 (decentralized, active)

Recommendation: Low risk for experienced users

Caution: Always monitor health factor
```

---

### Example 3: Transaction Execution

**You**: "Swap 1 ETH for USDC"

**Execution Agent** (2.1 seconds):
```
⚡ TRANSACTION READY

From: 1.0 ETH
To: ~2,500 USDC (estimated)

Route: 1inch (best price)
Gas: ~$8.50
Slippage: 0.5%

⚠️ CONFIRMATION REQUIRED

Reply "confirm" to proceed
```

---

### Example 4: Multi-Agent Workflow

**You**: "Create a balanced DeFi portfolio with 10k USDC"

**Supervisor** (8.5 seconds):

Uses 4 agents in sequence:
1. Research Agent → Find top protocols
2. Risk Analyzer → Assess risks
3. Portfolio Agent → Create allocation
4. Chat Agent → Summarize

```
📊 BALANCED DEFI PORTFOLIO

Allocation:
• 40% Aave USDC (4.5% APY, Low Risk)
• 30% Compound ETH (6.2% APY, Medium Risk)
• 20% Curve 3pool (8.5% APY, Low Risk)
• 10% Cash Reserve (safety buffer)

Expected Return: 5.8% APY
Risk Score: 32/100 (Low)
Sharpe Ratio: 1.82

Next Steps: Ready to execute? Reply "confirm"
```

---

## 🔐 Security & Privacy

### Your Data
- ✅ Encrypted at rest (PostgreSQL)
- ✅ Encrypted in transit (TLS/HTTPS)
- ✅ GDPR compliant
- ✅ No data sharing (your data stays private)

### Transaction Safety
- ✅ User confirmation required
- ✅ Transaction limits ($10k default)
- ✅ Simulation before execution
- ✅ Slippage protection
- ✅ 2FA support

### Compliance
- ✅ AML/KYC screening (Enterprise tier)
- ✅ OFAC sanction checks
- ✅ Regulatory reporting
- ✅ 7-year audit trails

---

## 💳 Pricing Tiers

### Free Tier
- 1 agent (Chat only)
- 10 messages/day
- Basic support

### Basic Tier - $20/month
- 3 agents (Chat, Hunter AI, Research)
- 500 messages/month
- Email support

### Pro Tier - $100/month
- 14 agents (all core + 4 advanced)
- Unlimited messages
- Priority support
- Advanced features

### Enterprise Tier - $2,000+/month
- All 18 agents
- Compliance & regulatory
- Multi-sig treasury
- Crisis management
- Dedicated support
- Custom integrations

---

## 🆘 Support

### Help Center
- Documentation: docs.anvil.com
- Video tutorials: youtube.com/anvil
- FAQ: anvil.com/faq

### Contact
- Email: support@anvil.com
- Discord: discord.gg/anvil
- Twitter: @AnvilDeFi

---

## 🚀 Tips & Best Practices

### 1. Be Specific
❌ "What's the market?"  
✅ "What's the market sentiment for Bitcoin today?"

### 2. Use Context
The system remembers your conversation history:
- "Tell me about Aave"
- "What are the risks?" ← Context-aware

### 3. Multi-Agent Workflows
For complex tasks, use the supervisor:
```
POST /api/v1/chat/agent-squad/supervisor

{
  "content": "Create a tax-optimized portfolio",
  "max_agents": 5
}
```

### 4. Force Specific Agents
If you know which agent you need:
```
POST /api/v1/chat/agent-squad/messages

{
  "content": "Analyze protocol risks",
  "force_agent": "risk_analyzer"
}
```

---

**Ready to get started?** Create your first conversation and let Agent Squad handle the complexity! 🚀

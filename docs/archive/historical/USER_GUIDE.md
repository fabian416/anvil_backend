# Anvil AI Chat - User Guide

**Welcome to Anvil AI Chat!** 🤖

Your intelligent assistant for DeFi operations, powered by specialized AI agents.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [What Can Anvil Do?](#what-can-anvil-do)
3. [Using the Chat Interface](#using-the-chat-interface)
4. [Agent Capabilities](#agent-capabilities)
5. [Example Conversations](#example-conversations)
6. [Tips & Best Practices](#tips--best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing Anvil Chat

1. **Web Interface**: Navigate to [app.anvil.com](https://app.anvil.com)
2. **Login**: Use your email and password
3. **Start Chatting**: Type your question in the chat box!

### First-Time Setup

No setup required! Just start asking questions.

The AI will:
- ✅ Automatically understand your intent
- ✅ Route your question to the right expert agent
- ✅ Use specialized tools to get accurate data
- ✅ Provide clear, actionable responses

---

## What Can Anvil Do?

Anvil has **4 specialized AI agents**, each an expert in their domain:

### 🔄 Trading Agent (1inch)
**What it does**: Helps with token swaps and DEX trading

**Examples**:
- "Swap 1 ETH for USDC"
- "What's the current price of WBTC?"
- "Compare routes for swapping DAI to USDC"
- "How much gas will this swap cost?"

### 💰 Lending Agent (Aave)
**What it does**: Manages lending, borrowing, and collateral

**Examples**:
- "Supply 1000 USDC to Aave"
- "What's my health factor?"
- "How much can I borrow against my ETH?"
- "Am I at risk of liquidation?"
- "What are the current Aave rates?"

### 📊 Analytics Agent (DeFiLlama)
**What it does**: Provides protocol research and market data

**Examples**:
- "What's the TVL of Uniswap?"
- "Find the best yield opportunities for stablecoins"
- "Compare Aave vs Compound"
- "What protocols are trending this week?"

### 💼 Portfolio Agent
**What it does**: Tracks your assets and positions

**Examples**:
- "Show me my portfolio"
- "What's my ETH balance?"
- "List all my DeFi positions"
- "What's my total portfolio value?"
- "Am I well-diversified?"

---

## Using the Chat Interface

### Basic Usage

1. **Type your question** in the chat box
2. **Press Enter** or click Send
3. **Watch the progress** as the AI works:
   - 💭 "Thinking..." - Processing your request
   - 🎯 "Routing to Trading Agent" - Selected the right expert
   - 🔧 "Using tool: get_swap_quote" - Fetching real data
4. **See the response** stream in real-time

### Understanding the Interface

#### Status Indicators
- 🟢 **Connected**: You're online and ready
- 🟡 **Processing**: AI is working on your request
- 🔴 **Disconnected**: Connection lost (will auto-reconnect)

#### Message Types
- **Your messages**: Appear on the right (or highlighted)
- **AI responses**: Appear on the left
- **Progress updates**: Show what the AI is doing
- **Tool calls**: Show when real data is being fetched

#### Real-Time Streaming
The AI streams responses token-by-token, just like ChatGPT, so you see the answer as it's being generated!

---

## Agent Capabilities

### Trading Agent (1inch)

#### Available Tools:
1. **get_swap_quote**: Get swap quotes across multiple DEXes
2. **get_token_price**: Check current token prices
3. **execute_swap**: Execute token swaps
4. **get_liquidity_sources**: See available DEXes
5. **estimate_gas**: Estimate gas costs
6. **get_supported_chains**: Check chain availability
7. **compare_routes**: Compare different swap routes

#### Safety Features:
- ✅ Always shows quotes before suggesting swaps
- ✅ Warns about price impact > 1%
- ✅ Calculates gas costs
- ✅ Requires explicit confirmation for executions
- ✅ Never executes without your approval

#### Supported Chains:
- Ethereum
- Polygon
- Arbitrum
- Optimism
- Avalanche
- BSC

---

### Lending Agent (Aave)

#### Available Tools:
1. **get_market_data**: Current lending/borrowing rates
2. **get_user_positions**: Your Aave positions
3. **supply_asset**: Supply assets to earn yield
4. **borrow_asset**: Borrow against collateral
5. **repay_debt**: Repay borrowed assets
6. **withdraw**: Withdraw supplied assets
7. **calculate_health_factor**: Check liquidation risk
8. **get_available_to_borrow**: Max borrowing capacity
9. **get_liquidation_risk**: Analyze liquidation scenarios

#### Safety Features:
- ✅ Always checks health factor before suggesting borrows
- ✅ Warns if health factor < 1.5
- ✅ Explains liquidation risk clearly
- ✅ Recommends conservative collateral ratios
- ✅ Shows both supply and borrow APYs

#### Health Factor Guide:
- **2.0+**: Safe ✅
- **1.5-2.0**: Moderate ⚠️
- **1.0-1.5**: Risky ⚠️⚠️
- **< 1.0**: Liquidation! 🚨

---

### Analytics Agent (DeFiLlama)

#### Available Tools:
1. **get_protocol_tvl**: Protocol TVL and history
2. **get_yields**: Yield farming opportunities
3. **get_protocol_fees**: Protocol revenue/fees
4. **compare_protocols**: Side-by-side comparison
5. **get_trending_protocols**: Growth leaders
6. **get_stablecoin_data**: Stablecoin market analysis
7. **get_chain_tvl**: TVL by blockchain
8. **search_protocols**: Find protocols

#### What You'll Learn:
- 📈 TVL (Total Value Locked) trends
- 💹 Best yield opportunities
- 💰 Protocol revenues
- 🔥 Trending protocols
- 🏦 Stablecoin adoption
- ⛓️ Multi-chain analysis

#### Risk Awareness:
- ⚠️ High APY = Higher risk
- ✅ Established protocols (Aave, Uniswap) are safer
- ⚠️ New protocols may have unaudited contracts
- ✅ Higher TVL generally means more trust

---

### Portfolio Agent

#### Available Tools:
1. **get_user_balance**: Token balances across chains
2. **get_user_positions**: All DeFi positions
3. **get_portfolio_summary**: Complete portfolio overview

#### What It Tracks:
- 💵 Token balances (all chains)
- 🏦 Lending positions (Aave, Compound)
- 💧 Liquidity positions (Uniswap, Curve)
- 📊 Staking positions
- 💰 Total USD value
- 🎯 Asset allocation
- ⚖️ Diversification analysis

#### Insights Provided:
- Total portfolio value in USD
- Largest holdings
- Concentration risk warnings
- Diversification recommendations
- Idle assets (could earn yield)

---

## Example Conversations

### Example 1: Simple Swap

**You**: "Swap 1 ETH for USDC on Ethereum"

**AI**:
```
💭 Processing your request...
🎯 Routing to Trading Agent (confidence: 95%)
🔧 Using tool: get_swap_quote

Based on 1inch DEX aggregator, here's the best route:

From: 1 ETH
To: ~2,500 USDC (at current price)
Route: Uniswap V3 (best price)
Price Impact: 0.12%
Gas Estimate: 150,000 gas (~$15)
Total You'll Receive: ~2,485 USDC (after gas)

⚠️ IMPORTANT: This is a quote only. To execute this swap, 
you'll need to connect your wallet and explicitly confirm 
the transaction. Never share your private keys!
```

---

### Example 2: Health Factor Check

**You**: "Am I safe? What's my health factor?"

**AI**:
```
💭 Processing your request...
🎯 Routing to Lending Agent (confidence: 92%)
🔧 Using tool: calculate_health_factor

Great question! Let me check your Aave position...

Your Current Status:
✅ Health Factor: 2.35 (SAFE)
💰 Total Collateral: $10,000 (5 ETH at $2,000 each)
💸 Total Debt: $4,000 (4,000 USDC borrowed)
📊 Utilization: 40%

You're in a safe position! Here's why:
• Your HF is well above 1.5 (recommended minimum)
• You're only using 40% of your borrowing capacity
• If ETH drops to $1,702, your HF would hit 2.0
• If ETH drops to $1,362, your HF would hit 1.5

Recommendation: Consider your goals:
• Want to borrow more? You can safely borrow another $1,500 USDC
• Want to be extra safe? Repay some debt or add collateral
```

---

### Example 3: Finding Yields

**You**: "Find me the best yield opportunities for stablecoins"

**AI**:
```
💭 Processing your request...
🎯 Routing to Analytics Agent (confidence: 89%)
🔧 Using tool: get_yields

Here are the top 10 stablecoin yield opportunities:

1. Curve 3pool (USDC/USDT/DAI) - Ethereum
   APY: 8.5% | TVL: $1.2B | Risk: Low ✅
   
2. Aave V3 USDC Supply - Polygon
   APY: 6.2% | TVL: $450M | Risk: Low ✅
   
3. Convex Tricrypto - Ethereum
   APY: 12.3% | TVL: $890M | Risk: Medium ⚠️
   IL Risk: Yes (mixed assets)
   
4. Stargate USDC - Arbitrum
   APY: 7.8% | TVL: $320M | Risk: Medium ⚠️
   Bridge Risk: Cross-chain

[... more results ...]

Recommendation for beginners:
Start with #1 or #2 for low risk and good yields!
```

---

### Example 4: Portfolio Overview

**You**: "Show me my complete portfolio"

**AI**:
```
💭 Processing your request...
🎯 Routing to Portfolio Agent (confidence: 98%)
🔧 Using tool: get_portfolio_summary

Here's your complete DeFi portfolio across all chains:

💰 Total Value: $25,450 USD

📊 Asset Breakdown:
• ETH: 5.0 ($10,000) - 39%
• USDC: 8,000 ($8,000) - 31%
• WBTC: 0.15 ($6,000) - 24%
• DAI: 1,200 ($1,200) - 5%
• Other: $250 - 1%

🏦 DeFi Positions:
• Aave V3 (Ethereum):
  - Supplied: 5 ETH ($10,000)
  - Borrowed: 4,000 USDC
  - Net Position: +$6,000
  
• Uniswap V3 (Arbitrum):
  - LP Position: USDC/ETH
  - Value: $2,500
  - Fees Earned: $45 (last 30 days)

⚖️ Diversification Analysis:
• Asset Concentration: Good ✅ (no single asset >40%)
• Chain Distribution: Concentrated ⚠️ (90% on Ethereum)
• Position Types: Well-diversified ✅

💡 Recommendations:
1. Consider moving some assets to L2s for lower gas costs
2. Your idle USDC could earn 6%+ on Aave
3. Great diversification across assets!
```

---

## Tips & Best Practices

### Getting Better Responses

#### ✅ DO:
- Be specific: "Swap 1 ETH for USDC" vs "I want to trade"
- Mention chains: "on Ethereum" vs unspecified
- Ask follow-ups: "How much gas?" after getting a quote
- Request explanations: "Why is the APY so high?"

#### ❌ DON'T:
- Be too vague: "What should I do?"
- Skip context: Agent can't see your previous questions
- Expect financial advice: AI provides data, not recommendations
- Share private keys: NEVER share sensitive information

---

### Understanding Agent Routing

The AI automatically routes your question to the right agent:

**Keywords that trigger Trading Agent:**
- swap, trade, exchange, buy, sell, price, quote, DEX, route, liquidity

**Keywords that trigger Lending Agent:**
- lend, borrow, supply, withdraw, repay, collateral, health factor, liquidation, Aave

**Keywords that trigger Analytics Agent:**
- TVL, protocol, yield, APY, compare, trending, fees, revenue, DeFiLlama, data

**Keywords that trigger Portfolio Agent:**
- balance, portfolio, positions, holdings, assets, my, show me, total value

---

### Safety Reminders

#### 🔒 Security:
- ✅ AI NEVER asks for private keys
- ✅ AI NEVER executes transactions automatically
- ✅ Always verify transaction details in your wallet
- ✅ Use hardware wallets for large amounts

#### ⚠️ Risk Awareness:
- DeFi involves smart contract risk
- High yields often mean higher risk
- Always DYOR (Do Your Own Research)
- Never invest more than you can afford to lose

#### 📚 Education:
- Ask "Explain [concept]" to learn
- Request "Why?" to understand reasoning
- Use "What are the risks?" before acting
- Stay informed about protocol updates

---

## Troubleshooting

### "Connection lost" Error

**Solution**: The AI will automatically reconnect. Just wait a few seconds.

---

### "No response" / Slow Response

**Possible causes**:
1. High server load
2. Complex query requiring multiple tool calls
3. Network issues

**Solutions**:
- Wait 30-60 seconds
- Try rephrasing your question
- Refresh the page if stuck

---

### "Invalid token" Error

**Solution**: Your session expired. Please log in again.

---

### Agent Selected Wrong Expert

**Example**: Asked about yields, got Trading Agent

**Solution**: Be more specific:
- Instead of: "What's the best opportunity?"
- Try: "What are the best yield farming opportunities for stablecoins?"

---

### Tool Call Failed

**Example**: "Error: Tool 'get_swap_quote' failed"

**Possible causes**:
1. Temporary API issue (1inch, Aave, etc.)
2. Invalid parameters
3. Chain not supported

**Solutions**:
- Rephrase and try again
- Specify supported chain (Ethereum, Polygon, etc.)
- Wait a moment and retry

---

## Frequently Asked Questions

### Q: Can the AI execute transactions for me?
**A**: No. The AI provides quotes and information but NEVER executes transactions. You must always confirm in your wallet.

### Q: Is my conversation private?
**A**: Yes. Your chat history is private and only accessible to you.

### Q: Can I use this without connecting a wallet?
**A**: Yes! You can ask questions, get quotes, and research protocols without connecting a wallet. You'll only need a wallet to execute actual transactions.

### Q: What chains does Anvil support?
**A**: Trading: 6 chains (ETH, Polygon, Arbitrum, Optimism, Avalanche, BSC)  
Lending: 5 chains (ETH, Polygon, Arbitrum, Optimism, Avalanche)  
Analytics: 10+ chains  
Portfolio: 6 chains

### Q: How accurate are the prices?
**A**: Prices are fetched in real-time from 1inch DEX aggregator, Aave, and DeFiLlama APIs. They're accurate within seconds but can change before you execute.

### Q: Can I trust the APY numbers?
**A**: APYs are fetched from DeFiLlama and are current. However, they can fluctuate. Always verify on the protocol's website before depositing.

### Q: What if I disagree with the AI's answer?
**A**: The AI provides data-driven responses but may not always be perfect. Always verify critical information, especially for large amounts.

---

## Getting Help

### In-App Support
- Click the "?" icon for context-specific help
- Use "Help" command in chat for quick tips

### Documentation
- Full API docs: [docs.anvil.com/api](https://docs.anvil.com/api)
- Video tutorials: [anvil.com/learn](https://anvil.com/learn)

### Community
- Discord: [discord.gg/anvil](https://discord.gg/anvil)
- Twitter: [@AnvilDeFi](https://twitter.com/AnvilDeFi)

### Contact
- Email: support@anvil.com
- Response time: 24-48 hours

---

## What's Next?

### Explore Features:
- Try all 4 agents
- Compare different protocols
- Track your portfolio
- Learn about DeFi concepts

### Learn DeFi:
- Ask "Explain [concept]" to learn
- Start small and experiment
- Join community discussions
- Read protocol documentation

### Stay Safe:
- Always verify before executing
- Start with small amounts
- Use hardware wallets
- Keep learning!

---

**Happy DeFi-ing with Anvil!** 🚀

---

**Last Updated**: December 2, 2024  
**Version**: 2.0  
**Feedback**: We'd love to hear from you! support@anvil.com

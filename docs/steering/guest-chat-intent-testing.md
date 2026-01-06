# Guest Chat Intent Testing Guide

**Version**: 1.0
**Date**: January 6, 2026
**Endpoint**: `POST /api/v1/guest/chat`

---

## Overview

This document provides test inputs for each `ChatIntent` to verify the guest chat routing system.

### Request Format

```bash
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "YOUR_TEST_MESSAGE",
    "language": "en"
  }'
```

---

## DeFi Shortcut Intents

### 1. LENDING
**Handler**: `lending_handler` (Morpho, Aave, Compound)

| Test Input | Expected Entities |
|------------|------------------|
| `"earn usdc on morpho"` | - |
| `"deposit 1000 usdc into morpho vault"` | capital: 1000 |
| `"deposit usdc on base morpho"` | chain: Base |
| `"lend my usdc on aave"` | - |
| `"supply eth to aave"` | - |
| `"show me morpho vaults on base"` | chain: Base |
| `"what's the best apy on morpho"` | - |

```bash
# Test LENDING
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "deposit 1000 usdc into morpho vault", "language": "en"}'
```

---

### 2. MONEY_MARKET
**Handler**: `money_market_handler` (Rate comparison)

| Test Input | Expected Entities |
|------------|------------------|
| `"compare lending rates"` | - |
| `"compare aave vs compound vs morpho"` | - |
| `"which protocol has the best supply apy"` | - |
| `"money market comparison"` | - |

```bash
# Test MONEY_MARKET
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "compare aave vs compound vs morpho", "language": "en"}'
```

---

### 3. SWAP
**Handler**: `swap_handler` (1inch, UniswapX, Hyperliquid)

| Test Input | Expected Entities |
|------------|------------------|
| `"swap eth for usdc"` | - |
| `"exchange 1 eth to usdc"` | - |
| `"trade btc for eth"` | - |
| `"convert usdc to eth"` | - |
| `"i want to swap my tokens"` | - |

```bash
# Test SWAP
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "swap eth for usdc", "language": "en"}'
```

---

### 4. BALANCE
**Handler**: `balance_handler`

| Test Input | Expected Entities |
|------------|------------------|
| `"show my balance"` | - |
| `"what's my balance"` | - |
| `"how much usdc do i have"` | - |
| `"check my wallet balance"` | - |

```bash
# Test BALANCE
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show my balance", "language": "en"}'
```

---

### 5. PORTFOLIO
**Handler**: `portfolio_handler`

| Test Input | Expected Entities |
|------------|------------------|
| `"show my portfolio"` | - |
| `"what's in my portfolio"` | - |
| `"list all my assets"` | - |
| `"enumerate my holdings"` | - |

```bash
# Test PORTFOLIO
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show my portfolio", "language": "en"}'
```

---

### 6. ACTIVITY
**Handler**: `activity_handler`

| Test Input | Expected Entities |
|------------|------------------|
| `"show my activity"` | - |
| `"transaction history"` | - |
| `"show my transactions"` | - |
| `"what transactions have i made"` | - |
| `"recent activity"` | - |

```bash
# Test ACTIVITY
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show my transactions", "language": "en"}'
```

---

### 7. RECEIVE
**Handler**: `receive_handler`

| Test Input | Expected Entities |
|------------|------------------|
| `"receive crypto"` | - |
| `"show my address"` | - |
| `"i want to receive funds"` | - |
| `"show qr code"` | - |
| `"deposit address"` | - |
| `"how do i receive tokens"` | - |

```bash
# Test RECEIVE
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show my address", "language": "en"}'
```

---

## Hunter AI Intents

### 8. HUNTER_SENTIMENT
**Handler**: `hunter_ai`

| Test Input | Expected Entities |
|------------|------------------|
| `"what's the eth sentiment on twitter and reddit?"` | token_symbol: ETH |
| `"show me btc social media sentiment from last 7 days"` | token_symbol: BTC |

```bash
# Test HUNTER_SENTIMENT
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what'\''s the eth sentiment on twitter and reddit?", "language": "en"}'
```

---

### 9. HUNTER_PRICE_PREDICTION
**Handler**: `hunter_ai`

| Test Input | Expected Entities |
|------------|------------------|
| `"predict btc price for next 7 days"` | token_symbol: BTC |
| `"forecast eth price for next 30 days"` | token_symbol: ETH |

```bash
# Test HUNTER_PRICE_PREDICTION
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "predict btc price for next 7 days", "language": "en"}'
```

---

### 10. HUNTER_RISK_SIGNALS
**Handler**: `hunter_ai`

| Test Input | Expected Entities |
|------------|------------------|
| `"show risk signals for eth"` | token_symbol: ETH |

```bash
# Test HUNTER_RISK_SIGNALS
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show risk signals for eth", "language": "en"}'
```

---

### 11. HUNTER_TRADING_SIGNALS
**Handler**: `hunter_ai`

| Test Input | Expected Entities |
|------------|------------------|
| `"should i buy sol now? give me trading signals"` | token_symbol: SOL |
| `"what are the entry and exit signals for btc?"` | token_symbol: BTC |

```bash
# Test HUNTER_TRADING_SIGNALS
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "should i buy sol now? give me trading signals", "language": "en"}'
```

---

### 12. HUNTER_PATTERNS
**Handler**: `hunter_ai`

| Test Input | Expected Entities |
|------------|------------------|
| `"what chart patterns do you see for btc?"` | token_symbol: BTC |
| `"detect technical formations for eth"` | token_symbol: ETH |

```bash
# Test HUNTER_PATTERNS
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what chart patterns do you see for btc?", "language": "en"}'
```

---

### 13. HUNTER_PORTFOLIO
**Handler**: `hunter_ai`

| Test Input | Expected Entities |
|------------|------------------|
| `"optimize my portfolio with btc, eth, and sol for moderate risk"` | token_symbol: BTC |
| `"create a conservative crypto portfolio for me"` | - |
| `"build an aggressive high-risk portfolio"` | - |

```bash
# Test HUNTER_PORTFOLIO
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "optimize my portfolio with btc, eth, and sol for moderate risk", "language": "en"}'
```

---

## ULTRA Intents (DeFi Automation)

### 14. ULTRA_ARBITRAGE
**Handler**: `ultra`

| Test Input | Expected Entities |
|------------|------------------|
| `"find arbitrage opportunities with $10,000 capital"` | capital: 10000 |
| `"search for cross-chain arbitrage with $5k"` | capital: 5000 |
| `"find dex arbitrage opportunities"` | - |

```bash
# Test ULTRA_ARBITRAGE
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "find arbitrage opportunities with $10,000 capital", "language": "en"}'
```

---

### 15. ULTRA_FLASH_LOANS
**Handler**: `ultra`

| Test Input | Expected Entities |
|------------|------------------|
| `"best flash loan protocol for 100k usdc"` | capital: 100000 |
| `"i need a flash loan for leveraged trading"` | - |

```bash
# Test ULTRA_FLASH_LOANS
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "best flash loan protocol for 100k usdc", "language": "en"}'
```

---

### 16. ULTRA_MEV_PROTECTION
**Handler**: `ultra`

| Test Input | Expected Entities |
|------------|------------------|
| `"execute arb-001 with flashbots protection"` | - |
| `"send this transaction privately to avoid mev"` | - |

```bash
# Test ULTRA_MEV_PROTECTION
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "send this transaction privately to avoid mev", "language": "en"}'
```

---

### 17. ULTRA_AUTO_EXECUTOR
**Handler**: `ultra`

| Test Input | Expected Entities |
|------------|------------------|
| `"start trading bot"` | - |
| `"stop trading bot"` | - |
| `"show bot status"` | - |
| `"configure bot with 2% profit threshold"` | - |

```bash
# Test ULTRA_AUTO_EXECUTOR
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "start trading bot", "language": "en"}'
```

---

## GraphRAG Intents

### 18. PROTOCOL_SEARCH
**Handler**: `graphrag_search`

| Test Input | Expected Entities |
|------------|------------------|
| `"show me high-yield lending protocols on ethereum"` | chain: Ethereum |
| `"find defi staking protocols with low risk"` | - |
| `"list dex protocols on polygon and arbitrum"` | chain: Polygon |

```bash
# Test PROTOCOL_SEARCH
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me high-yield lending protocols on ethereum", "language": "en"}'
```

---

### 19. RISK_ASSESSMENT
**Handler**: `graphrag_search`

| Test Input | Expected Entities |
|------------|------------------|
| `"is aave safe to use? what are the risks?"` | protocol_name: Aave |
| `"compare security risks between uniswap and curve"` | protocol_name: Uniswap |

```bash
# Test RISK_ASSESSMENT
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "is aave safe to use? what are the risks?", "language": "en"}'
```

---

### 20. SIMILAR_PROTOCOLS
**Handler**: `graphrag_search`

| Test Input | Expected Entities |
|------------|------------------|
| `"what protocols are similar to uniswap?"` | protocol_name: Uniswap |
| `"find lending platforms like compound"` | protocol_name: Compound |

```bash
# Test SIMILAR_PROTOCOLS
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what protocols are similar to uniswap?", "language": "en"}'
```

---

## Agent Squad Intents

### 21. SPECIALIST_TASK
**Handler**: `agent_orchestrator`

| Test Input | Suggested Agent |
|------------|-----------------|
| `"analyze eth/usdc liquidity depth on uniswap v3"` | research |
| `"audit this smart contract for vulnerabilities"` | security_auditor |
| `"optimize my gas usage for this transaction"` | gas_optimizer |
| `"help me with tax optimization for my crypto"` | tax_optimizer |
| `"bridge my tokens from ethereum to arbitrum"` | bridge_crosschain |

```bash
# Test SPECIALIST_TASK
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "analyze eth/usdc liquidity depth on uniswap v3", "language": "en"}'
```

---

### 22. COMPLEX_WORKFLOW
**Handler**: `agent_orchestrator`

| Test Input | Expected Entities |
|------------|------------------|
| `"create a complete defi investment strategy for $50k with risk analysis"` | capital: 50000 |
| `"plan a complete yield farming operation from start to finish"` | - |

```bash
# Test COMPLEX_WORKFLOW
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "create a complete defi investment strategy for $50k with risk analysis", "language": "en"}'
```

---

## General Conversation

### 23. GENERAL_CONVERSATION
**Handler**: `general_chat`

| Test Input | Confidence |
|------------|------------|
| `"hello! what can you help me with?"` | 0.95 |
| `"what features do you offer?"` | 0.95 |
| `"random unclear message xyz"` | 0.65 |

```bash
# Test GENERAL_CONVERSATION
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello! what can you help me with?", "language": "en"}'
```

---

## Quick Test Script

```bash
#!/bin/bash
# test-all-intents.sh

BASE_URL="http://localhost:8080/api/v1/guest/chat"

declare -A TESTS=(
  ["LENDING"]="deposit 1000 usdc into morpho vault"
  ["MONEY_MARKET"]="compare aave vs compound vs morpho"
  ["SWAP"]="swap eth for usdc"
  ["BALANCE"]="show my balance"
  ["PORTFOLIO"]="show my portfolio"
  ["ACTIVITY"]="show my transactions"
  ["RECEIVE"]="show my address"
  ["HUNTER_SENTIMENT"]="what's the eth sentiment on twitter?"
  ["HUNTER_PRICE_PREDICTION"]="predict btc price for next 7 days"
  ["HUNTER_RISK_SIGNALS"]="show risk signals for eth"
  ["HUNTER_TRADING_SIGNALS"]="should i buy sol now?"
  ["HUNTER_PATTERNS"]="what chart patterns for btc?"
  ["HUNTER_PORTFOLIO"]="optimize my portfolio"
  ["ULTRA_ARBITRAGE"]="find arbitrage opportunities"
  ["ULTRA_FLASH_LOANS"]="best flash loan protocol"
  ["ULTRA_MEV_PROTECTION"]="send privately to avoid mev"
  ["ULTRA_AUTO_EXECUTOR"]="start trading bot"
  ["PROTOCOL_SEARCH"]="find lending protocols on ethereum"
  ["RISK_ASSESSMENT"]="is aave safe?"
  ["SIMILAR_PROTOCOLS"]="protocols similar to uniswap"
  ["SPECIALIST_TASK"]="audit this smart contract"
  ["COMPLEX_WORKFLOW"]="create complete defi strategy"
  ["GENERAL_CONVERSATION"]="hello what can you help with"
)

for intent in "${!TESTS[@]}"; do
  echo "Testing: $intent"
  curl -s -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"${TESTS[$intent]}\", \"language\": \"en\"}" | jq '.intent'
  echo "---"
done
```

---

## Response Format

```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "AI response text",
  "intent": "lending",
  "confidence": 0.92,
  "handler": "lending_handler",
  "entities": {
    "capital": 1000,
    "chain": "Base"
  },
  "metadata": {
    "processing_time_ms": 150,
    "model": "gemini-2.0-flash-exp"
  }
}
```

---

## Multi-Language Support

The guest chat supports: `en`, `es`, `pt`, `zh`

```bash
# Spanish
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "muéstrame mi balance", "language": "es"}'

# Portuguese
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "mostrar meu saldo", "language": "pt"}'

# Chinese
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "显示我的余额", "language": "zh"}'
```

---

## Intent → Handler Mapping Summary

| Intent | Handler | Category |
|--------|---------|----------|
| `LENDING` | `lending_handler` | DeFi Shortcut |
| `MONEY_MARKET` | `money_market_handler` | DeFi Shortcut |
| `SWAP` | `swap_handler` | DeFi Shortcut |
| `BALANCE` | `balance_handler` | DeFi Shortcut |
| `PORTFOLIO` | `portfolio_handler` | DeFi Shortcut |
| `ACTIVITY` | `activity_handler` | DeFi Shortcut |
| `RECEIVE` | `receive_handler` | DeFi Shortcut |
| `HUNTER_*` | `hunter_ai` | Hunter AI |
| `ULTRA_*` | `ultra` | ULTRA |
| `PROTOCOL_SEARCH` | `graphrag_search` | GraphRAG |
| `RISK_ASSESSMENT` | `graphrag_search` | GraphRAG |
| `SIMILAR_PROTOCOLS` | `graphrag_search` | GraphRAG |
| `SPECIALIST_TASK` | `agent_orchestrator` | Agent Squad |
| `COMPLEX_WORKFLOW` | `agent_orchestrator` | Agent Squad |
| `GENERAL_CONVERSATION` | `general_chat` | Fallback |

---

**Last Updated**: January 6, 2026

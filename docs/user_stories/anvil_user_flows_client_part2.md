# 🎯 Anvil User Flows - CLIENT Users Part 2 (Mobile App)

## Continuation of CLIENT User Flows

---

## 6. Perpetual Trading (Hyperliquid)

### Flow: Open Long Position on ETH with 5x Leverage

**User Goal:** Open a 5x leveraged long position on ETH-USD on Hyperliquid

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to Perpetuals Trading                          │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Trade" → "Perpetuals" tab

UI Display: Perpetuals Trading Screen
  - Market selector: ETH-USD, BTC-USD, SOL-USD
  - Price chart with technical indicators
  - Current price: $2,450.00
  - 24h change: +2.3% ⬆️
  - Order entry panel
  - Open positions section (empty)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Configure Position via AI Chat                          │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps AI chat bubble

User Input: "I want to go long on ETH with $50 at 5x leverage. Is this a good idea?"

Frontend Action:
  → POST /api/v1/user/chat/message

Request:
{
  "message": "I want to go long on ETH with $50 at 5x leverage. Is this a good idea?",
  "session_id": "session_perp123"
}

Backend Process:
  1. Create conversation record
     
     DB INSERT: llm_conversations
     {
       user_id: 12345,
       session_id: "session_perp123",
       provider: "vertex",
       model_name: "gemini-1.5-flash",
       prompt_text: "I want to go long on ETH...",
       status: "success"
     }
  
  2. Create agent execution (risk assessment)
     
     DB INSERT: agent_executions
     {
       user_id: 12345,
       conversation_id: [conv_id],
       agent_type: "risk",
       workflow_type: "analysis",
       status: "running",
       input_params: {
         "asset": "ETH-USD",
         "position_size": 50,
         "leverage": 5,
         "side": "long"
       }
     }
  
  3. Execute risk analysis tasks
     
     Task 1: Calculate position metrics
     - Position size: $50 × 5 = $250 notional
     - Margin required: $50
     - Liquidation price calculation
     
     DB INSERT: agent_tasks
     {
       execution_id: [exec_id],
       task_name: "calculate_position_metrics",
       task_type: "research",
       status: "completed",
       output_data: {
         "notional_value": 250.0,
         "margin": 50.0,
         "size_eth": 0.102,
         "entry_price": 2450.00,
         "liquidation_price": 1960.00,
         "liquidation_distance_pct": 20.0
       }
     }
     
     Task 2: Market analysis
     - Check ETH trend (bullish/bearish)
     - Check funding rate
     - Check volatility
     
     Tool Usage: price_feed, market_data
     
     DB INSERT: agent_tools_usage
     {
       execution_id: [exec_id],
       tool_name: "price_feed",
       input_params: {"symbol": "ETH-USD"},
       output_result: {
         "price": 2450.00,
         "trend": "bullish",
         "rsi": 58,
         "funding_rate": 0.01
       }
     }
     
     Task 3: Risk assessment
     - Position risk: Medium (5x leverage)
     - Liquidation risk: 20% price drop would liquidate
     - Recommendation: Consider lower leverage for beginners
  
  4. LLM generates response
     
     Vertex AI generates analysis with recommendations
     
     DB UPDATE: llm_conversations
     SET response_text = "Analysis: ETH is currently bullish...",
         input_tokens = 680,
         output_tokens = 320,
         cost_usd = 0.00008,
         latency_ms: 1240
     
     DB UPDATE: agent_executions
     SET status = "completed",
         total_cost_usd = 0.00008

Response: 200 OK
{
  "success": true,
  "data": {
    "ai_response": "Analysis: ETH is currently bullish with RSI at 58. Here's what your position would look like:\n\n📊 Position Details:\n- Notional value: $250 (5x leverage)\n- Margin: $50\n- Size: 0.102 ETH\n- Entry price: ~$2,450\n- Liquidation price: ~$1,960 (20% drop)\n\n⚠️ Risk Assessment: MEDIUM\n- A 20% price drop would liquidate your position\n- Funding rate: 0.01% per hour\n- Current trend: Bullish, but volatile\n\n💡 Recommendation: Consider starting with 3x leverage if this is your first perpetual trade. This gives you more breathing room (13% to liquidation vs 20%).\n\nWould you like to proceed with 5x or adjust to 3x?",
    "position_preview": {
      "notional_value": 250.0,
      "margin": 50.0,
      "leverage": 5.0,
      "size_eth": 0.102,
      "entry_price": 2450.00,
      "liquidation_price": 1960.00,
      "liquidation_distance_pct": 20.0,
      "funding_rate": 0.01
    }
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: User Reviews and Confirms                               │
└─────────────────────────────────────────────────────────────────┘

UI Display: AI Response with Position Preview Card
  - AI explanation (scrollable)
  - Position preview card:
    - Margin: $50
    - Leverage: 5x
    - Notional: $250
    - Size: 0.102 ETH
    - Entry: ~$2,450
    - Liquidation: $1,960 (20% ⬇️)
  - "Open Position" button (green)
  - "Adjust Leverage" button
  - "Cancel" button

User Action: After reading AI analysis, taps "Open Position"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Final Confirmation Modal                                │
└─────────────────────────────────────────────────────────────────┘

UI Display: Confirmation Modal
  - ⚠️ "High Risk Warning"
  - "You're opening a leveraged position. You could lose your entire margin ($50) if the price moves against you."
  - Position summary
  - Checkboxes:
    [x] I understand the risks of leveraged trading
    [x] I understand I could be liquidated at $1,960
  - "Confirm & Open Position" button (red, requires both checkboxes)
  - "Go Back" button

User Action: Checks both boxes, taps "Confirm & Open Position"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Execute Position Opening on Hyperliquid                 │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/perpetuals/open
  → Authorization: Bearer [access_token]

Request:
{
  "symbol": "ETH-USD",
  "side": "long",
  "leverage": 5.0,
  "margin": "50",
  "size": "0.102"
}

Backend Process:
  1. Validate balance
     
     Check chain_addresses for Hyperliquid chain
     Must have sufficient USDC for margin
  
  2. Submit order to Hyperliquid
     
     Hyperliquid API Call:
     POST /exchange
     {
       "action": {
         "type": "order",
         "orders": [{
           "asset": "ETH",
           "isBuy": true,
           "sz": 0.102,
           "limitPx": 2455, // slight slippage
           "orderType": { "limit": { "tif": "Ioc" }}
         }],
         "grouping": "na"
       },
       "signature": "...",
       "vaultAddress": null
     }
     
     Response from Hyperliquid:
     {
       "status": "ok",
       "response": {
         "data": {
           "statuses": [{
             "filled": {
               "avgPx": "2450.50",
               "totalSz": "0.102",
               "oid": "hyperliquid_order_123"
             }
           }]
         }
       }
     }
  
  3. Create position record
     
     DB INSERT: hyperliquid_positions
     {
       user_id: 12345,
       wallet_id: 67890,
       symbol: "ETH-USD",
       side: "long",
       leverage: 5.0,
       size: 0.102,
       entry_price: 2450.50,
       mark_price: 2450.50,
       liquidation_price: 1960.40,
       unrealized_pnl: 0.00,
       realized_pnl: 0.00,
       margin: 50.0,
       funding_rate: 0.01,
       status: "open",
       hyperliquid_order_id: "hyperliquid_order_123",
       opened_at: NOW(),
       created_at: NOW()
     }
  
  4. Create transaction record
     
     DB INSERT: transactions
     {
       user_id: 12345,
       wallet_id: 67890,
       type: 0 (SWAP - perpetual entry),
       chain: "hyperliquid",
       asset_in: "USDC",
       amount_in: 50.0,
       asset_out: "ETH-USD",
       amount_out: 0.102,
       tx_hash: "hyperliquid_order_123",
       status: 1 (SUCCESS),
       created_at: NOW()
     }
  
  5. Update balance
     
     DB UPDATE: chain_addresses
     SET balance_usd = balance_usd - 50.0
     WHERE wallet_id = 67890
     AND chain = "hyperliquid"

Response: 200 OK
{
  "success": true,
  "data": {
    "position_id": 301,
    "status": "open",
    "entry_price": 2450.50,
    "size": 0.102,
    "margin": 50.0,
    "liquidation_price": 1960.40
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Position Opened - Real-Time Monitoring                  │
└─────────────────────────────────────────────────────────────────┘

UI Display: Position Opened Success
  - "Position Opened! 🚀"
  - Entry price: $2,450.50
  - "Monitor Position" button

User Action: Taps "Monitor Position"

UI Display: Perpetuals Screen → Open Positions Section

Position Card:
┌─────────────────────────────────────────┐
│ ETH-USD LONG 5x                         │
├─────────────────────────────────────────┤
│ Size: 0.102 ETH ($250.00)              │
│ Entry: $2,450.50                        │
│ Mark: $2,455.00 ⬆️ (+0.18%)            │
│ Margin: $50.00                          │
│ Leverage: 5x                            │
│                                         │
│ PnL: +$0.46 (+0.92%) 🟢                │
│                                         │
│ Liq. Price: $1,960.40 (19.8% ⬇️)       │
│ Distance: Safe ✅                       │
│                                         │
│ [Close Position] [Add Margin]          │
└─────────────────────────────────────────┘

DB INSERT: notifications
{
  user_id: 12345,
  type: "position_opened",
  channel: "push",
  title: "Position Opened",
  message: "ETH-USD Long 5x at $2,450.50",
  priority: "medium"
}

✅ SUCCESS CRITERIA:
  - Position opened on Hyperliquid
  - Position record created in database
  - Real-time PnL displayed
  - Liquidation monitoring active
  - User can see position in UI
```

**Real-Time Position Monitoring (Background Job)**

```
┌─────────────────────────────────────────────────────────────────┐
│ BACKGROUND JOB: Update Position Prices & Check Liquidations     │
└─────────────────────────────────────────────────────────────────┘

Job: Monitor Hyperliquid Positions
Runs: Every 30 seconds

Process:
  1. Query open positions
     
     SELECT * FROM hyperliquid_positions
     WHERE status = 'open'
  
  2. For each position, fetch current market price
     
     Hyperliquid API: /info
     GET https://api.hyperliquid.xyz/info
     {
       "type": "l2Book",
       "coin": "ETH"
     }
     
     Current mark price: $2,460.00
  
  3. Calculate unrealized PnL
     
     For long position:
     unrealized_pnl = (mark_price - entry_price) × size
     = (2460.00 - 2450.50) × 0.102
     = +$0.969
     
     PnL percentage = (unrealized_pnl / margin) × 100
     = (0.969 / 50.0) × 100
     = +1.94%
  
  4. Check liquidation distance
     
     distance_to_liq = (mark_price - liquidation_price) / mark_price × 100
     = (2460 - 1960.40) / 2460 × 100
     = 20.31%
  
  5. Update position
     
     DB UPDATE: hyperliquid_positions
     SET mark_price = 2460.00,
         unrealized_pnl = 0.969
     WHERE id = 301
  
  6. Check if liquidation warning needed
     
     IF distance_to_liq < 5% THEN
       → Send urgent warning notification
     ELSE IF distance_to_liq < 10% THEN
       → Send high priority warning
     END IF
     
     Current: 20.31% - Safe ✅

User's app updates in real-time via WebSocket:
  - PnL: +$0.97 (+1.94%) 🟢
  - Mark price: $2,460.00
  - Liquidation distance: 20.31%
```

**Liquidation Alert Example**

```
Scenario: Price drops to $2,100 (-14.3%)

Background Job detects:
  distance_to_liq = (2100 - 1960.40) / 2100 = 6.65%
  
Action:
  DB INSERT: notifications
  {
    user_id: 12345,
    type: "liquidation_warning",
    channel: "push",
    title: "⚠️ LIQUIDATION WARNING",
    message: "Your ETH-USD position is 6.7% from liquidation! Current price: $2,100. Liquidation: $1,960. Consider adding margin or closing.",
    priority: "urgent",
    data_json: {
      "position_id": 301,
      "current_price": 2100,
      "liquidation_price": 1960.40,
      "distance_pct": 6.65
    }
  }

Notification sent immediately (urgent priority):
  - Push notification
  - Email
  - SMS (if configured)

User receives all 3 channels to ensure they see it!
```

**Total Time:** ~2-3 minutes to open, continuous monitoring  
**Database Tables Affected:** `hyperliquid_positions`, `transactions`, `llm_conversations`, `agent_executions`, `notifications`  
**External Services:** Hyperliquid API, Privy (signing if needed)

---

## 7. AI Chat & Recommendations

### Flow: Ask AI for Investment Recommendations

**User Goal:** Get personalized investment recommendations based on portfolio

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Open AI Chat                                            │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps floating AI chat bubble (any screen)

UI Display: Chat Interface
  - Chat history (if any previous messages)
  - Message input field with microphone icon
  - Suggested prompts:
    - "What's my portfolio performance?"
    - "Should I buy more ETH?"
    - "Find me a safe earning opportunity"
    - "What's happening in crypto today?"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: User Asks for Recommendations                           │
└─────────────────────────────────────────────────────────────────┘

User Input: "Based on my portfolio, what should I invest in next?"

UI Display: 
  - User message appears (right-aligned bubble)
  - AI thinking indicator (3 animated dots)

Frontend Action:
  → POST /api/v1/user/chat/message
  → Authorization: Bearer [access_token]

Request:
{
  "message": "Based on my portfolio, what should I invest in next?",
  "session_id": "session_invest123",
  "context": {
    "include_portfolio": true,
    "include_market_data": true
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Backend Multi-Agent Workflow                            │
└─────────────────────────────────────────────────────────────────┘

Backend Process:
  
  1. Log conversation
     
     DB INSERT: llm_conversations
     {
       user_id: 12345,
       session_id: "session_invest123",
       provider: "vertex",
       model_name: "gemini-1.5-flash",
       prompt_text: "Based on my portfolio, what should I invest in next?",
       status: "success"
     }
  
  2. Create agent execution
     
     DB INSERT: agent_executions
     {
       user_id: 12345,
       conversation_id: [conv_id],
       agent_type: "research",
       workflow_type: "analysis",
       status: "running",
       input_params: {
         "request_type": "investment_recommendations",
         "include_portfolio": true
       }
     }
  
  3. Task 1: Analyze Current Portfolio
     
     DB INSERT: agent_tasks
     {
       execution_id: [exec_id],
       task_name: "analyze_portfolio",
       task_type: "research",
       status: "running"
     }
     
     Query user's holdings:
     - SELECT * FROM chain_addresses WHERE wallet_id = 67890
     - SELECT * FROM earn_positions WHERE user_id = 12345 AND status = 'active'
     - SELECT * FROM hyperliquid_positions WHERE user_id = 12345 AND status = 'open'
     
     Portfolio Analysis Result:
     {
       "total_value_usd": 120.35,
       "assets": {
         "ETH": {"amount": 0.0204, "value_usd": 50.00, "pct": 41.5},
         "USDC": {"amount": 30, "value_usd": 30.00, "pct": 24.9}
       },
       "earn_positions": {
         "aave_usdc": {"value": 70.06, "pct": 58.2, "apy": 4.2}
       },
       "perp_positions": {
         "eth_long_5x": {"value": 50.0, "pnl": 0.97, "pct": 41.5}
       },
       "risk_profile": "medium",
       "diversification_score": 3.5/10, // Concentrated in ETH
       "yield_exposure": 58.2%
     }
     
     DB UPDATE: agent_tasks
     SET status = "completed",
         output_data = {...portfolio_analysis}
  
  4. Task 2: Market Research
     
     DB INSERT: agent_tasks
     {
       execution_id: [exec_id],
       task_name: "market_research",
       task_type: "research",
       status: "running"
     }
     
     Tool Usage: price_feed, market_data
     
     DB INSERT: agent_tools_usage (multiple)
     - Tool: price_feed → Get BTC, SOL, USDC prices
     - Tool: market_data → Get trending tokens
     - Tool: defi_protocols → Get top APYs
     
     Market Research Result:
     {
       "trending": ["BTC", "SOL", "MATIC"],
       "prices": {
         "BTC": 43250.00,
         "SOL": 98.50,
         "MATIC": 0.85
       },
       "top_yields": [
         {"protocol": "compound", "asset": "USDT", "apy": 5.8},
         {"protocol": "curve", "asset": "3pool", "apy": 6.2}
       ],
       "market_sentiment": "bullish"
     }
  
  5. Task 3: Generate Recommendations
     
     Based on:
     - Portfolio too concentrated in ETH (82% exposure counting perp)
     - Good yield allocation (58%)
     - Missing BTC exposure
     - Could diversify to reduce risk
     
     Recommendation Strategy:
     1. Close or reduce ETH perp to lock profits
     2. Buy some BTC for diversification
     3. Consider higher-yield opportunity (Compound USDT)
     4. Keep USDC buffer for opportunities
  
  6. LLM Generates Personalized Response
     
     Vertex AI Call with context:
     model.generateContent({
       systemInstruction: "You are a helpful crypto investment advisor...",
       contents: {
         role: "user",
         parts: [{
           text: "Portfolio: {...analysis_data}, Market: {...market_data}, Generate recommendations"
         }]
       }
     })
     
     DB UPDATE: llm_conversations
     SET response_text = "Great question! I've analyzed your portfolio...",
         input_tokens = 1850,
         output_tokens: 650,
         cost_usd = 0.00012,
         latency_ms = 2340
     
     DB UPDATE: agent_executions
     SET status = "completed",
         total_tasks = 3,
         completed_tasks = 3,
         total_cost_usd = 0.00012,
         execution_time_ms = 2340

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: AI Response with Actionable Recommendations             │
└─────────────────────────────────────────────────────────────────┘

Response: 200 OK
{
  "success": true,
  "data": {
    "ai_response": "Great question! I've analyzed your portfolio and here's what I found:\n\n📊 Current Portfolio:\n• Total value: $120.35\n• ETH exposure: 82% (including perpetual) ⚠️ High!\n• Yield farming: 58% in Aave\n• Cash (USDC): 25%\n\n✅ What's Working:\n• Your Aave position is earning solid 4.2% APY\n• Your ETH perp is up 1.94% - nice!\n• Good cash buffer\n\n⚠️ Areas to Improve:\n• Heavy concentration in ETH (risk!)\n• Missing diversification\n\n💡 My Recommendations:\n\n1️⃣ **Lock in ETH Profits** (Priority: High)\n   Take profit on your leveraged ETH position. You're up $0.97. Close it and reallocate.\n   \n2️⃣ **Buy Bitcoin** (Priority: High)\n   Invest $25-30 in BTC for diversification. BTC is at $43,250 and trending up.\n   \n3️⃣ **Upgrade Your Yield** (Priority: Medium)\n   Compound offers 5.8% APY on USDT vs your 4.2% on Aave. Consider moving $20-30.\n   \n4️⃣ **Keep USDC Buffer** (Priority: High)\n   Maintain $15-20 in cash for opportunities and gas fees.\n\nWant me to help you execute any of these?",
    "recommendations": [
      {
        "id": 1,
        "action": "close_position",
        "title": "Close ETH Perpetual",
        "description": "Lock in +$0.97 profit",
        "priority": "high",
        "estimated_outcome": "+$0.97",
        "executable": true
      },
      {
        "id": 2,
        "action": "buy",
        "title": "Buy Bitcoin",
        "description": "Diversify with $25-30 BTC",
        "priority": "high",
        "estimated_cost": "$25-30",
        "executable": true
      },
      {
        "id": 3,
        "action": "earn",
        "title": "Move to Compound",
        "description": "Upgrade yield from 4.2% → 5.8%",
        "priority": "medium",
        "estimated_apy_increase": "+1.6%",
        "executable": true
      }
    ],
    "portfolio_score": 6.5,
    "risk_level": "medium-high"
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: User Sees AI Response with Action Buttons               │
└─────────────────────────────────────────────────────────────────┘

UI Display: AI Response (left-aligned bubble)
  - Full text explanation (scrollable)
  - 
  - Actionable recommendation cards:
    
    Card 1:
    ┌────────────────────────────────────┐
    │ 1️⃣ Close ETH Perpetual   [HIGH]  │
    ├────────────────────────────────────┤
    │ Lock in +$0.97 profit              │
    │                                    │
    │ [Close Position →]                 │
    └────────────────────────────────────┘
    
    Card 2:
    ┌────────────────────────────────────┐
    │ 2️⃣ Buy Bitcoin          [HIGH]   │
    ├────────────────────────────────────┤
    │ Diversify with $25-30 BTC          │
    │                                    │
    │ [Buy BTC →]                        │
    └────────────────────────────────────┘
    
    Card 3:
    ┌────────────────────────────────────┐
    │ 3️⃣ Move to Compound    [MEDIUM]  │
    ├────────────────────────────────────┤
    │ Upgrade yield 4.2% → 5.8%          │
    │                                    │
    │ [Learn More →]                     │
    └────────────────────────────────────┘

User Action Options:
  1. Tap action button → Execute recommendation
  2. Ask follow-up question
  3. Dismiss and think about it

Example Follow-up:
User: "Why is BTC better than more ETH?"

AI explains diversification benefits, correlation, etc.

✅ SUCCESS CRITERIA:
  - AI analyzes portfolio comprehensively
  - Recommendations are personalized and actionable
  - User can execute recommendations directly from chat
  - Conversation is natural and helpful
```

**Total Time:** ~3-5 seconds per message  
**Database Tables Affected:** `llm_conversations`, `agent_executions`, `agent_tasks`, `agent_tools_usage`  
**External Services:** Vertex AI, market data APIs

---

## 8. Subscription Upgrade Flow

### Flow: Upgrade from Free to Pro

**User Goal:** Upgrade to Pro plan for unlimited AI conversations

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Hit Free Plan Limit                                     │
└─────────────────────────────────────────────────────────────────┘

Context: User has sent 10 messages today (free plan limit)

User Action: Tries to send 11th message

Backend Check:
  SELECT COUNT(*) FROM llm_conversations
  WHERE user_id = 12345
  AND DATE(created_at) = CURDATE()
  
  Result: 10 messages (limit reached)

Response: 200 OK (with limit warning)
{
  "success": false,
  "error": {
    "code": "DAILY_LIMIT_REACHED",
    "message": "You've reached your daily limit of 10 conversations",
    "upgrade_available": true
  }
}

UI Display: Upgrade Prompt Modal
  - "Daily Limit Reached"
  - "You've used all 10 free conversations today"
  - 
  - Pro Benefits:
    ✓ Unlimited AI conversations
    ✓ Priority support
    ✓ Advanced analytics
    ✓ Early access to new features
  
  - Pricing: $9.99/month
  - "Start 7-Day Free Trial" button (primary)
  - "Upgrade to Pro" button (if trial used)
  - "Maybe Later" link

User Action: Taps "Start 7-Day Free Trial"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Subscription Checkout                                   │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/subscription/create-checkout
  → Authorization: Bearer [access_token]

Request:
{
  "plan": "pro",
  "trial_enabled": true
}

Backend Process:
  1. Get or create Stripe customer
     
     Check if user has stripe_customer_id:
     SELECT stripe_customer_id FROM subscriptions
     WHERE user_id = 12345
     
     If none exists:
     Stripe API Call:
     customer = stripe.customers.create({
       email: "john.doe@example.com",
       name: "John Doe",
       metadata: {
         user_id: 12345,
         uid: "usr_xyz123"
       }
     })
     
     stripe_customer_id: "cus_stripe123"
  
  2. Create Stripe subscription with trial
     
     Stripe API Call:
     subscription = stripe.subscriptions.create({
       customer: "cus_stripe123",
       items: [{
         price: "price_pro_monthly_999" // Stripe price ID
       }],
       trial_period_days: 7,
       payment_behavior: "default_incomplete",
       metadata: {
         user_id: 12345,
         plan: "pro"
       },
       expand: ['latest_invoice.payment_intent']
     })
     
     Response:
     {
       "id": "sub_stripe456",
       "status": "trialing",
       "trial_end": 1700524800, // 7 days from now
       "latest_invoice": {
         "payment_intent": {
           "client_secret": "pi_secret_abc123"
         }
       }
     }
  
  3. Create subscription record
     
     DB INSERT: subscriptions
     {
       user_id: 12345,
       stripe_subscription_id: "sub_stripe456",
       stripe_customer_id: "cus_stripe123",
       plan: "pro",
       status: "trialing",
       price_monthly: 9.99,
       billing_cycle_start: NOW(),
       billing_cycle_end: NOW() + INTERVAL 1 MONTH,
       trial_end: NOW() + INTERVAL 7 DAY,
       created_at: NOW()
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "subscription_id": 501,
    "stripe_subscription_id": "sub_stripe456",
    "client_secret": "pi_secret_abc123",
    "status": "trialing",
    "trial_end": "2025-11-23T14:30:00Z"
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Payment Method Setup (Stripe Elements)                  │
└─────────────────────────────────────────────────────────────────┘

UI Display: Payment Method Screen
  - "Add Payment Method"
  - "Your trial starts now. You won't be charged until Nov 23."
  - 
  - Stripe Elements form:
    - Card number field
    - Expiry field
    - CVC field
    - ZIP code field
  
  - "Start Free Trial" button
  - Terms: "By continuing, you agree to be charged $9.99/month after trial"

User Input:
  - Card: 4242 4242 4242 4242
  - Expiry: 12/26
  - CVC: 123
  - ZIP: 10001

User Action: Taps "Start Free Trial"

Frontend Action:
  → stripe.confirmCardSetup(client_secret, {
      payment_method: {
        card: cardElement,
        billing_details: {
          name: "John Doe"
        }
      }
    })

Stripe Process:
  → Validates card (no charge yet)
  → Attaches payment method to subscription
  → Returns success

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Trial Activated                                         │
└─────────────────────────────────────────────────────────────────┘

Backend Process:
  1. Update subscription status
     
     DB UPDATE: subscriptions
     SET status = "trialing"
     WHERE id = 501
  
  2. Create audit log
     
     DB INSERT: audit_logs
     {
       actor_user_id: 12345,
       action: "subscription_started",
       entity: "subscription",
       entity_id: 501,
       payload_json: {
         "plan": "pro",
         "status": "trialing",
         "trial_end": "2025-11-23T14:30:00Z"
       }
     }
  
  3. Send confirmation notification
     
     DB INSERT: notifications
     {
       user_id: 12345,
       type: "subscription_trial_started",
       channel: "email",
       title: "Welcome to Anvil Pro!",
       message: "Your 7-day trial has started. Enjoy unlimited AI conversations!",
       priority: "low"
     }

UI Display: Success Screen
  - "🎉 Welcome to Pro!"
  - "Your 7-day free trial is active"
  - "Trial ends: November 23, 2025"
  - "You'll be charged $9.99/month after trial"
  - 
  - Pro badge icon
  - "Start Chatting" button

User Action: Taps "Start Chatting"

Returns to chat interface → Can now send unlimited messages!

✅ SUCCESS CRITERIA:
  - Subscription created with trial
  - Payment method saved (no charge yet)
  - User can now send unlimited messages
  - Trial end date tracked
```

**Trial End - Automatic Billing (7 days later)**

```
┌─────────────────────────────────────────────────────────────────┐
│ DAY 7: Automatic Subscription Billing                           │
└─────────────────────────────────────────────────────────────────┘

Stripe Automatic Process:
  1. Trial period ends (Nov 23, 2025)
  2. Stripe automatically attempts first payment
  3. Charges card on file: $9.99
  4. Creates invoice: inv_stripe789
  5. Sends webhook: invoice.paid

Webhook Handler:
  POST https://api.anvil.com/webhooks/stripe
  
  Event: invoice.paid
  
  Backend Process:
    1. Update subscription
       
       DB UPDATE: subscriptions
       SET status = "active",
           billing_cycle_start = NOW(),
           billing_cycle_end = NOW() + INTERVAL 1 MONTH
       WHERE stripe_subscription_id = "sub_stripe456"
    
    2. Record payment
       
       DB INSERT: subscription_payments
       {
         subscription_id: 501,
         user_id: 12345,
         stripe_invoice_id: "inv_stripe789",
         amount: 9.99,
         status: "paid",
         billing_reason: "subscription_cycle",
         paid_at: NOW(),
         created_at: NOW()
       }
    
    3. Send receipt notification
       
       DB INSERT: notifications
       {
         user_id: 12345,
         type: "subscription_renewed",
         channel: "email",
         title: "Subscription Renewed",
         message: "Your Pro subscription has been renewed for $9.99",
         priority: "low"
       }

User receives email with:
  - Receipt for $9.99
  - Next billing date: Dec 23, 2025
  - Manage subscription link
```

**Total Time:** ~2-3 minutes  
**Database Tables Affected:** `subscriptions`, `subscription_payments`, `notifications`, `audit_logs`  
**External Services:** Stripe (subscription + payment processing)

---

## 9. Portfolio Management

### Flow: View Complete Portfolio Overview

**User Goal:** Check overall portfolio performance and holdings

```
┌─────────────────────────────────────────────────────────────────┐
│ Portfolio Dashboard - Complete View                             │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Home" tab

Frontend Action:
  → GET /api/v1/user/dashboard
  → Authorization: Bearer [access_token]

Backend Process:
  Execute stored procedure: sp_get_user_dashboard(12345)
  
  Returns:
  1. User profile
  2. All chain balances
  3. Recent transactions
  4. Active positions (earn + perpetuals)

Response: 200 OK
{
  "success": true,
  "data": {
    "summary": {
      "total_value_usd": 171.32,
      "24h_change_usd": +2.14,
      "24h_change_pct": +1.27,
      "all_time_pnl": +21.32,
      "all_time_pnl_pct": +14.21
    },
    "balances": {
      "arbitrum": {
        "total_usd": 50.35,
        "assets": [
          {"asset": "ETH", "amount": 0.0204, "value_usd": 50.35}
        ]
      },
      "base": {"total_usd": 0},
      "hyperliquid": {"total_usd": 50.97}
    },
    "earn_positions": [
      {
        "protocol": "aave",
        "asset": "USDC",
        "value": 70.06,
        "rewards": 0.06,
        "apy": 4.2
      }
    ],
    "perp_positions": [
      {
        "symbol": "ETH-USD",
        "side": "long",
        "value": 50.97,
        "pnl": +0.97,
        "pnl_pct": +1.94
      }
    ],
    "recent_activity": [
      {"type": "position_opened", "time": "2h ago"},
      {"type": "earn_deposit", "time": "5h ago"},
      {"type": "swap", "time": "6h ago"}
    ]
  }
}

UI Display: Portfolio Dashboard

┌─────────────────────────────────────────────┐
│ Portfolio                                    │
│ $171.32                                      │
│ +$2.14 (1.27%) today 🟢                     │
│                                              │
│ All-Time: +$21.32 (14.21%) 📈              │
├─────────────────────────────────────────────┤
│ Asset Allocation                             │
│ ┌─────┐                                      │
│ │█████│ Earning (41%) - $70.06              │
│ │███  │ Spot (29%) - $50.35                 │
│ │███  │ Perpetuals (30%) - $50.97           │
│ └─────┘                                      │
├─────────────────────────────────────────────┤
│ Holdings                                     │
│                                              │
│ USDC (Aave)  70.06 USDC    $70.06  [4.2%]  │
│ ETH (Spot)   0.0204 ETH    $50.35           │
│ ETH-USD 5x   0.102 ETH     $50.97  [+1.94%] │
├─────────────────────────────────────────────┤
│ Recent Activity               [View All →]   │
│                                              │
│ 🔵 ETH-USD Long Opened        2h ago        │
│ 💰 Deposited 50 USDC to Aave  5h ago        │
│ 🔄 Swapped 50 USDC → ETH      6h ago        │
└─────────────────────────────────────────────┘

Quick Actions:
[Trade] [Earn] [Fund] [Withdraw]
```

---

## 10. Notifications & Alerts

### All Notification Types

```
┌─────────────────────────────────────────────────────────────────┐
│ Notification System - Complete Flow                             │
└─────────────────────────────────────────────────────────────────┘

NOTIFICATION TYPES:

1. Transaction Notifications
   - transaction_confirmed (medium priority)
   - transaction_failed (medium priority)
   - transaction_pending_long (low priority)

2. Trading Notifications
   - position_opened (medium)
   - position_closed (medium)
   - liquidation_warning (urgent) ⚠️
   - liquidation_alert (urgent) 🚨

3. Earning Notifications
   - earn_deposit_completed (medium)
   - earn_withdrawal_completed (medium)
   - auto_save_executed (medium)
   - rewards_milestone (low)

4. Subscription Notifications
   - subscription_trial_started (low)
   - subscription_renewed (low)
   - subscription_payment_failed (high)
   - subscription_canceled (medium)

5. System Notifications
   - kyc_approved (medium)
   - kyc_rejected (medium)
   - system_maintenance (high)
   - security_alert (urgent)

DELIVERY FLOW:

Step 1: Create notification
  DB INSERT: notifications
  {
    user_id: 12345,
    type: "liquidation_warning",
    channel: "push",
    title: "⚠️ LIQUIDATION WARNING",
    message: "Your ETH position is 6% from liquidation",
    priority: "urgent",
    status: "pending"
  }

Step 2: Notification worker picks up (runs every minute)
  SELECT * FROM notifications
  WHERE status = 'pending'
  ORDER BY
    CASE priority
      WHEN 'urgent' THEN 1
      WHEN 'high' THEN 2
      WHEN 'medium' THEN 3
      WHEN 'low' THEN 4
    END,
    created_at ASC
  LIMIT 100

Step 3: Send via appropriate channel
  
  For push notifications (FCM):
    FCM.send({
      token: user.fcm_token,
      notification: {
        title: "⚠️ LIQUIDATION WARNING",
        body: "Your ETH position is 6% from liquidation"
      },
      data: {
        type: "liquidation_warning",
        position_id: "301",
        click_action: "OPEN_POSITION_DETAIL"
      }
    })
  
  For email (SendGrid):
    sendgrid.send({
      to: "john.doe@example.com",
      from: "notifications@anvil.com",
      subject: "⚠️ LIQUIDATION WARNING",
      template_id: "liquidation_warning_template",
      dynamic_data: {...}
    })
  
  For SMS (Twilio):
    twilio.messages.create({
      to: "+1234567890",
      from: "+1-ANVIL",
      body: "⚠️ Your ETH position is near liquidation. Check Anvil now."
    })

Step 4: Update notification status
  DB UPDATE: notifications
  SET status = 'sent',
      sent_at = NOW()
  WHERE id = [notification_id]

Step 5: User interacts with notification
  User opens app from push notification
  
  Frontend tracks:
    → POST /api/v1/user/notifications/{id}/read
  
  DB UPDATE: notifications
  SET read_at = NOW()
  WHERE id = [notification_id]

In-App Notification Center:
  User Action: Taps notification bell icon
  
  UI Display:
    - Unread count badge
    - List of notifications (newest first)
    - Group by: Today, Yesterday, This Week, Older
    - Filter by type
    - "Mark all as read" button
```

---

## Summary: CLIENT User Flows

**Total Flows Covered:** 10

1. **Onboarding & Authentication** ✅
   - Privy integration, wallet creation, profile setup
   - Time: 2-3 minutes

2. **Wallet Setup & Funding** ✅
   - Stripe payment, on-chain purchase, balance update
   - Time: 3-5 minutes

3. **Token Swap Flow** ✅
   - AI-powered quote, DEX execution, confirmation
   - Time: 1-2 minutes

4. **Yield Farming (Earn) Flow** ✅
   - Risk analysis, Aave deposit, position monitoring
   - Time: 1-2 minutes

5. **Recurring Savings Setup** ✅
   - Schedule configuration, projections, auto-execution
   - Time: 2 minutes setup + automatic

6. **Perpetual Trading (Hyperliquid)** ✅
   - Position opening, real-time PnL, liquidation monitoring
   - Time: 2-3 minutes + continuous monitoring

7. **AI Chat & Recommendations** ✅
   - Portfolio analysis, personalized recommendations
   - Time: 3-5 seconds per message

8. **Subscription Upgrade Flow** ✅
   - Trial activation, payment setup, automatic billing
   - Time: 2-3 minutes

9. **Portfolio Management** ✅
   - Complete dashboard, real-time updates
   - Time: instant

10. **Notifications & Alerts** ✅
    - Multi-channel delivery, priority routing
    - Time: instant to 1 minute

**Total Database Tables Used:** All 27 tables engaged across flows

**External Integrations:**
- Privy (wallet + auth)
- Stripe (payments)
- 1inch/0x (DEX aggregation)
- Hyperliquid (perpetuals)
- Aave/Compound (yield farming)
- Vertex AI / Bedrock (AI)
- FCM / SendGrid / Twilio (notifications)

---

**Next:** ADMIN and AUDITOR user flows in separate documents

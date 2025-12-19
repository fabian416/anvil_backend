# 🎯 Anvil User Flows - CLIENT Users (Mobile App)

## User Type: CLIENT (role=2)
**Platform:** Mobile App (iOS/Android)  
**Access Level:** Personal wallet, trading, DeFi operations, AI assistant  
**Primary Use Cases:** Trading, saving, earning, portfolio management

---

## Table of Contents

1. [Onboarding & Authentication](#1-onboarding--authentication)
2. [Wallet Setup & Funding](#2-wallet-setup--funding)
3. [Token Swap Flow](#3-token-swap-flow)
4. [Yield Farming (Earn) Flow](#4-yield-farming-earn-flow)
5. [Recurring Savings Setup](#5-recurring-savings-setup)
6. [Perpetual Trading (Hyperliquid)](#6-perpetual-trading-hyperliquid)
7. [AI Chat & Recommendations](#7-ai-chat--recommendations)
8. [Subscription Upgrade Flow](#8-subscription-upgrade-flow)
9. [Portfolio Management](#9-portfolio-management)
10. [Notifications & Alerts](#10-notifications--alerts)

---

## 1. Onboarding & Authentication

### Flow: New User Registration

**User Goal:** Create account and access Anvil app

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: App Launch & Welcome Screen                             │
└─────────────────────────────────────────────────────────────────┘

User Action: Opens Anvil app
UI Display: 
  - Welcome screen with logo
  - "Get Started" button
  - "Sign In" button

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Initiate Sign Up                                        │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Get Started"
UI Display: 
  - Email input field
  - "Continue with Email" button
  - Social login options (Google, Apple)

User Input: Enters email (e.g., "john.doe@example.com")
User Action: Taps "Continue with Email"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Privy Authentication                                    │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → Calls Privy SDK: privy.login({ email: "john.doe@example.com" })

Privy Action:
  → Sends magic link to email
  → Displays "Check your email" screen

UI Display:
  - "Magic link sent to john.doe@example.com"
  - "Open email and click the link"
  - Countdown timer (5 minutes)

User Action: Opens email, clicks magic link

Privy Action:
  → Validates magic link
  → Creates Privy user account
  → Generates Privy DID (did:privy:clk1abc...)
  → Creates embedded wallet with MPC
  → Returns authentication token

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Backend User Creation                                   │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/auth/privy
  
Request:
{
  "privy_token": "eyJhbGc...",
  "privy_user_id": "did:privy:clk1abc..."
}

Backend Process:
  1. Validate Privy token with Privy API
  2. Check if user exists (by privy_user_id)
  3. If new user:
     
     DB INSERT: users
     {
       uid: "usr_xyz123" (UUID),
       privy_user_id: "did:privy:clk1abc...",
       email: "john.doe@example.com",
       role: 2 (CLIENT),
       status: 0 (INACTIVE - pending profile completion),
       kyc_status: 'none',
       created_at: NOW()
     }
     
     DB INSERT: wallets
     {
       user_id: [new_user_id],
       privy_wallet_id: "0xprivy123...",
       address: "0x1234...5678" (from Privy),
       provider: "privy",
       default_chain: "arbitrum",
       status: 1 (ACTIVE)
     }
     
     DB INSERT: chain_addresses (3 records)
     {
       wallet_id: [new_wallet_id],
       chain: "arbitrum",
       address: "0x1234...5678",
       is_active: TRUE
     }
     {
       wallet_id: [new_wallet_id],
       chain: "base",
       address: "0x1234...5678",
       is_active: TRUE
     }
     {
       wallet_id: [new_wallet_id],
       chain: "hyperliquid",
       address: "hype1234...5678",
       is_active: TRUE
     }
  
  4. Generate Anvil JWT token
  5. Return response

Response: 200 OK
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600,
    "user": {
      "id": 12345,
      "uid": "usr_xyz123",
      "email": "john.doe@example.com",
      "role": 2,
      "status": 0
    },
    "wallet": {
      "address": "0x1234...5678",
      "default_chain": "arbitrum"
    }
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Profile Setup                                           │
└─────────────────────────────────────────────────────────────────┘

UI Display: Profile completion screen
  - First name field
  - Last name field
  - Phone number field (optional)
  - "Continue" button

User Input:
  - First name: "John"
  - Last name: "Doe"
  - Phone: "+1234567890"

User Action: Taps "Continue"

Frontend Action:
  → PATCH /api/v1/user/profile
  → Authorization: Bearer [access_token]

Request:
{
  "firstname": "John",
  "lastname": "Doe",
  "phone": "+1234567890"
}

Backend Process:
  DB UPDATE: users
  SET firstname = "John",
      lastname = "Doe",
      phone = "+1234567890",
      status = 1 (ACTIVE)
  WHERE id = 12345

Response: 200 OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Terms & Conditions                                      │
└─────────────────────────────────────────────────────────────────┘

UI Display:
  - Terms of Service text
  - Privacy Policy link
  - "I agree to the Terms" checkbox
  - "Accept and Continue" button

User Action: Checks box, taps "Accept and Continue"

Frontend Action:
  → PATCH /api/v1/user/profile
  → Authorization: Bearer [access_token]

Request:
{
  "terms_accepted_at": "2025-11-16T14:30:00Z"
}

Backend Process:
  DB UPDATE: users
  SET terms_accepted_at = NOW()
  WHERE id = 12345

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Home Dashboard (First View)                            │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → GET /api/v1/wallet/balances
  → Authorization: Bearer [access_token]

Backend Process:
  1. Query chain_addresses for user's wallet
  2. Fetch real-time balances from blockchain RPCs
  3. Calculate total portfolio value

Response: 200 OK
{
  "success": true,
  "data": {
    "total_usd": 0.00,
    "chains": [
      {
        "chain": "arbitrum",
        "total_usd": 0.00,
        "balances": []
      },
      {
        "chain": "base",
        "total_usd": 0.00,
        "balances": []
      },
      {
        "chain": "hyperliquid",
        "total_usd": 0.00,
        "balances": []
      }
    ]
  }
}

UI Display: Home Dashboard
  - Welcome message: "Welcome, John!"
  - Portfolio balance: $0.00
  - Empty state: "Get started by funding your wallet"
  - "Fund Wallet" button (primary CTA)
  - Navigation tabs: Home, Trade, Earn, Activity, Profile
  - AI chat bubble (floating action button)

✅ SUCCESS CRITERIA:
  - User record created in database
  - Wallet created with Privy
  - User status = ACTIVE
  - User can access home dashboard
```

**Total Time:** ~2-3 minutes  
**Database Tables Affected:** `users`, `wallets`, `chain_addresses`  
**External Services:** Privy (authentication + wallet creation)

---

## 2. Wallet Setup & Funding

### Flow: First-Time Wallet Funding (Fiat to Crypto)

**User Goal:** Deposit $100 USD to buy USDC on Arbitrum

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Initiate Funding                                        │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Fund Wallet" on home screen

UI Display: Funding Options Screen
  - Card/Bank transfer (via Stripe)
  - Crypto transfer (manual deposit)
  - Selected: Card/Bank transfer

User Action: Taps "Fund with Card"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Funding Amount Selection                                │
└─────────────────────────────────────────────────────────────────┘

UI Display:
  - Quick amount buttons: $50, $100, $250, $500, Custom
  - Asset selector: USDC, ETH, USDT
  - Chain selector: Arbitrum, Base
  - Fee breakdown display
  - "Continue" button

User Input:
  - Amount: $100
  - Asset: USDC
  - Chain: Arbitrum

Fee Calculation Display:
  - Amount: $100.00
  - Stripe fee (2.9% + $0.30): $3.20
  - Network fee: ~$0.50
  - Total: $103.70
  - You receive: ~100 USDC

User Action: Taps "Continue"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Create Stripe Payment Intent                            │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/funding/create
  → Authorization: Bearer [access_token]

Request:
{
  "amount_fiat": 103.70,
  "asset": "USDC",
  "chain": "arbitrum",
  "payment_method": "card"
}

Backend Process:
  1. Validate user status and limits
  2. Create Stripe PaymentIntent
     
     Stripe API Call:
     stripe.paymentIntents.create({
       amount: 10370, // cents
       currency: 'usd',
       customer: user.stripe_customer_id,
       metadata: {
         user_id: 12345,
         asset: 'USDC',
         chain: 'arbitrum'
       }
     })
  
  3. Create funding transaction record
     
     DB INSERT: funding_transactions
     {
       user_id: 12345,
       wallet_id: 67890,
       stripe_payment_intent_id: "pi_stripe123",
       amount_fiat: 103.70,
       asset: "USDC",
       chain: "arbitrum",
       payment_method: "card",
       status: "pending",
       fee_stripe: 3.20,
       fee_network: 0.50,
       created_at: NOW()
     }
  
  4. Return client secret for Stripe

Response: 200 OK
{
  "success": true,
  "data": {
    "funding_transaction_id": 789,
    "stripe_client_secret": "pi_stripe123_secret_abc",
    "amount_fiat": 103.70,
    "expected_crypto": 100.0,
    "asset": "USDC"
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Stripe Payment UI                                       │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → Initialize Stripe Elements with client_secret
  → Display Stripe payment form

UI Display: Stripe Payment Form
  - Card number field
  - Expiry date field
  - CVC field
  - Billing ZIP code
  - "Pay $103.70" button

User Input:
  - Card: 4242 4242 4242 4242
  - Expiry: 12/26
  - CVC: 123
  - ZIP: 10001

User Action: Taps "Pay $103.70"

Frontend Action:
  → stripe.confirmCardPayment(client_secret, {
      payment_method: { card: cardElement }
    })

Stripe Process:
  → Processes payment
  → 3D Secure verification (if required)
  → Payment succeeds
  → Webhook sent to backend

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Stripe Webhook Processing                               │
└─────────────────────────────────────────────────────────────────┘

Stripe Webhook: payment_intent.succeeded
→ POST https://api.anvil.com/webhooks/stripe

Backend Process:
  1. Verify webhook signature
  2. Extract payment intent ID
  3. Update funding transaction
     
     DB UPDATE: funding_transactions
     SET status = "processing",
         stripe_status = "succeeded"
     WHERE stripe_payment_intent_id = "pi_stripe123"
  
  4. Initiate on-chain purchase
     a. Get USDC quote on Arbitrum (via 1inch/0x)
     b. Calculate expected USDC amount (~100 USDC)
     c. Execute swap: USD → USDC
     d. Send USDC to user's wallet address

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: On-Chain Transaction Execution                          │
└─────────────────────────────────────────────────────────────────┘

Backend Process:
  1. Get DEX quote
     
     API Call to 1inch:
     GET https://api.1inch.dev/swap/v5.2/42161/quote
     params: {
       src: USDT_ADDRESS (temporary stable),
       dst: USDC_ADDRESS,
       amount: "100000000" (100 USDC in wei)
     }
  
  2. Execute transaction
     
     Web3 Transaction:
     {
       to: "0x1234...USDC_ADDRESS",
       value: 0,
       data: "transfer(recipient, amount)",
       gas: 100000
     }
  
  3. Transaction submitted
     tx_hash: "0xabc123def456..."
  
  4. Create transaction record
     
     DB INSERT: transactions
     {
       user_id: 12345,
       wallet_id: 67890,
       type: 1 (FUND),
       chain: "arbitrum",
       asset_in: "USD",
       amount_in: 103.70,
       asset_out: "USDC",
       amount_out: 100.0,
       tx_hash: "0xabc123def456...",
       status: 0 (PENDING),
       created_at: NOW()
     }
  
  5. Update funding transaction
     
     DB UPDATE: funding_transactions
     SET transaction_hash = "0xabc123def456...",
         amount_crypto = 100.0
     WHERE id = 789

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Transaction Monitoring (Background Job)                 │
└─────────────────────────────────────────────────────────────────┘

Background Job (runs every 30 seconds):
  1. Query pending transactions
     
     SELECT * FROM transactions
     WHERE status = 0 (PENDING)
     AND created_at > NOW() - INTERVAL 1 HOUR
  
  2. Check transaction status on blockchain
     
     Web3 Call:
     eth.getTransactionReceipt("0xabc123def456...")
  
  3. Transaction confirmed! (block: 12345678)
  
  4. Update transaction record
     
     DB UPDATE: transactions
     SET status = 1 (SUCCESS),
         block_number = 12345678,
         confirmed_at = NOW()
     WHERE tx_hash = "0xabc123def456..."
  
  5. Update funding transaction
     
     DB UPDATE: funding_transactions
     SET status = "completed",
         completed_at = NOW()
     WHERE id = 789
  
  6. Refresh wallet balance
     
     DB UPDATE: chain_addresses
     SET balance_usd = 100.00,
         last_balance_update = NOW()
     WHERE wallet_id = 67890
     AND chain = "arbitrum"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: User Notification                                       │
└─────────────────────────────────────────────────────────────────┘

Backend Process:
  DB INSERT: notifications
  {
    user_id: 12345,
    type: "deposit_completed",
    channel: "push",
    title: "Deposit Complete! 🎉",
    message: "100 USDC has been added to your Arbitrum wallet",
    data_json: {
      "transaction_id": 456,
      "amount": "100 USDC",
      "chain": "arbitrum"
    },
    status: "pending",
    priority: "medium",
    created_at: NOW()
  }

Notification Worker (runs every minute):
  1. Pick up pending notification
  2. Send via FCM (Firebase Cloud Messaging)
  3. Update notification status
     
     DB UPDATE: notifications
     SET status = "sent",
         sent_at = NOW()
     WHERE id = [notification_id]

┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: User Sees Updated Balance                               │
└─────────────────────────────────────────────────────────────────┘

User Action: Sees push notification, opens app

Frontend Action:
  → GET /api/v1/wallet/balances
  → Authorization: Bearer [access_token]

Response: 200 OK
{
  "success": true,
  "data": {
    "total_usd": 100.00,
    "chains": [
      {
        "chain": "arbitrum",
        "total_usd": 100.00,
        "balances": [
          {
            "asset": "USDC",
            "amount": "100.0",
            "usd_value": 100.00,
            "price": 1.00
          }
        ]
      }
    ]
  }
}

UI Display: Home Dashboard
  - Portfolio balance: $100.00
  - New badge on Activity tab
  - Recent transaction: "+100 USDC"

✅ SUCCESS CRITERIA:
  - Payment processed successfully
  - USDC received in user's wallet
  - Balance updated in database and UI
  - User notified of successful deposit
```

**Total Time:** ~3-5 minutes (payment + blockchain confirmation)  
**Database Tables Affected:** `funding_transactions`, `transactions`, `chain_addresses`, `notifications`  
**External Services:** Stripe (payment), 1inch/0x (DEX), Arbitrum RPC (blockchain)

---

## 3. Token Swap Flow

### Flow: Swap USDC for ETH

**User Goal:** Swap 50 USDC for ETH on Arbitrum

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to Trade                                       │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Trade" tab in bottom navigation

UI Display: Trade Screen
  - Swap interface (primary)
  - Market view button
  - Recent trades list

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Configure Swap                                          │
└─────────────────────────────────────────────────────────────────┘

UI Display: Swap Interface
  - From: [USDC dropdown] [amount input] [balance: 100 USDC]
  - Swap direction arrow (↓)
  - To: [ETH dropdown] [estimated amount] [balance: 0 ETH]
  - Chain selector: Arbitrum
  - Slippage settings (gear icon)
  - "Get Quote" button

User Input:
  - From asset: USDC
  - Amount: 50
  - To asset: ETH
  - Chain: Arbitrum (default)

Frontend Action (as user types):
  → Debounced quote fetch every 500ms
  → POST /api/v1/user/chat/message (AI-powered quote)

Request:
{
  "message": "Get me a quote to swap 50 USDC for ETH on Arbitrum",
  "session_id": "session_abc123"
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: AI Agent Quote Fetching                                 │
└─────────────────────────────────────────────────────────────────┘

Backend Process:
  1. Log conversation
     
     DB INSERT: llm_conversations
     {
       user_id: 12345,
       session_id: "session_abc123",
       provider: "vertex",
       model_name: "gemini-1.5-flash",
       prompt_text: "Get me a quote to swap 50 USDC for ETH on Arbitrum",
       status: "success",
       created_at: NOW()
     }
  
  2. Create agent execution
     
     DB INSERT: agent_executions
     {
       user_id: 12345,
       conversation_id: [conv_id],
       agent_type: "research",
       workflow_type: "swap",
       status: "pending",
       input_params: {
         "from": "USDC",
         "to": "ETH",
         "amount": 50,
         "chain": "arbitrum"
       },
       created_at: NOW()
     }
  
  3. Execute research agent tasks
     
     Task 1: Get ETH price
     DB INSERT: agent_tasks
     {
       execution_id: [exec_id],
       task_name: "fetch_eth_price",
       task_type: "research",
       status: "running"
     }
     
     Tool Usage: price_feed
     DB INSERT: agent_tools_usage
     {
       execution_id: [exec_id],
       task_id: [task_id],
       tool_name: "price_feed",
       input_params: {"symbol": "ETH"},
       output_result: {"price": 2450.00},
       status: "success"
     }
     
     Task 2: Get DEX quote
     API Call to 1inch:
     GET /swap/v5.2/42161/quote?
       fromTokenAddress=0x...USDC&
       toTokenAddress=0x...ETH&
       amount=50000000
     
     Response:
     {
       "toAmount": "20408163265306", // ~0.0204 ETH
       "estimatedGas": "150000",
       "protocols": [["Uniswap V3"]]
     }
     
     DB UPDATE: agent_tasks
     SET status = "completed",
         output_data = {...quote_data}
     WHERE id = [task_id]
  
  4. Update agent execution
     
     DB UPDATE: agent_executions
     SET status = "completed",
         total_tasks = 2,
         completed_tasks = 2,
         execution_time_ms = 850,
         output_result = {
           "expected_eth": 0.0204,
           "eth_price": 2450.00,
           "rate": "1 USDC = 0.000408 ETH",
           "dex": "1inch",
           "route": "Uniswap V3"
         }
  
  5. LLM generates response
     
     Vertex AI Call:
     model.generateContent({
       prompt: "Format this swap quote for the user: {...}"
     })
     
     DB UPDATE: llm_conversations
     SET response_text = "Great! You'll get approximately 0.0204 ETH...",
         input_tokens = 450,
         output_tokens = 120,
         cost_usd = 0.00003,
         latency_ms = 850

Response: 200 OK
{
  "success": true,
  "data": {
    "ai_response": "Great! You'll get approximately 0.0204 ETH for your 50 USDC...",
    "quote": {
      "from_amount": "50",
      "from_asset": "USDC",
      "to_amount": "0.0204",
      "to_asset": "ETH",
      "rate": "1 USDC = 0.000408 ETH",
      "eth_price_usd": 2450.00,
      "estimated_gas": "0.0002 ETH (~$0.50)",
      "dex_aggregator": "1inch",
      "dex_route": ["Uniswap V3"],
      "slippage": "0.5%",
      "min_received": "0.0203 ETH",
      "execution_time": "~30 seconds"
    }
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: User Reviews Quote                                      │
└─────────────────────────────────────────────────────────────────┘

UI Display: Swap Interface (Updated)
  - From: 50 USDC
  - To: ~0.0204 ETH ($50.00)
  - Rate: 1 USDC = 0.000408 ETH
  - Gas: ~$0.50
  - Minimum received: 0.0203 ETH (0.5% slippage)
  - Route: Uniswap V3 via 1inch
  - "Review Swap" button (enabled, green)

User Action: Taps "Review Swap"

UI Display: Confirmation Modal
  - Swap summary
  - Final amounts
  - Fees breakdown
  - "Confirm Swap" button
  - "Cancel" button

User Action: Taps "Confirm Swap"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Execute Swap Transaction                                │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/trade/swap
  → Authorization: Bearer [access_token]

Request:
{
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "to_amount_min": "0.0203",
  "chain": "arbitrum",
  "slippage": 0.5,
  "dex_aggregator": "1inch"
}

Backend Process:
  1. Validate balance
     
     SELECT balance_usd FROM chain_addresses
     WHERE wallet_id = 67890
     AND chain = "arbitrum"
     
     Result: 100.00 (sufficient)
  
  2. Get fresh quote from 1inch
  
  3. Prepare transaction with Privy
     
     Privy API Call:
     privy.wallet.signTransaction({
       user_id: "did:privy:clk1abc...",
       transaction: {
         to: "0x1inch_router...",
         data: "swap(fromToken, toToken, amount...)",
         gas: 150000
       }
     })
  
  4. Submit to blockchain
     
     tx_hash: "0xswap123def456..."
  
  5. Record transaction
     
     DB INSERT: transactions
     {
       user_id: 12345,
       wallet_id: 67890,
       type: 0 (SWAP),
       chain: "arbitrum",
       asset_in: "USDC",
       amount_in: 50.0,
       asset_out: "ETH",
       amount_out: 0.0204,
       tx_hash: "0xswap123def456...",
       status: 0 (PENDING),
       dex_aggregator: "1inch",
       dex_route: {"protocol": "1inch", "route": ["Uniswap V3"]},
       slippage: 0.5,
       created_at: NOW()
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "transaction_id": 457,
    "tx_hash": "0xswap123def456...",
    "status": "pending",
    "estimated_time": "30 seconds"
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Transaction Confirmation                                │
└─────────────────────────────────────────────────────────────────┘

UI Display: Pending Transaction Screen
  - Animated loader
  - "Swap in progress..."
  - Transaction hash (with block explorer link)
  - Estimated time: ~30 seconds
  - "View in Explorer" button

Background Job (every 30 seconds):
  1. Check transaction status
     
     Web3: eth.getTransactionReceipt("0xswap123...")
     
     Result: {
       status: 1, // success
       blockNumber: 12345680,
       gasUsed: 145000
     }
  
  2. Update transaction
     
     DB UPDATE: transactions
     SET status = 1 (SUCCESS),
         block_number = 12345680,
         confirmed_at = NOW(),
         fee = 0.000145 (ETH),
         fee_usd = 0.35
     WHERE tx_hash = "0xswap123..."
  
  3. Update balances
     
     DB UPDATE: chain_addresses
     SET balance_usd = 50.35, // 50 USDC + 0.35 ETH at $2450
         last_balance_update = NOW()
     WHERE wallet_id = 67890
     AND chain = "arbitrum"
  
  4. Send notification
     
     DB INSERT: notifications
     {
       user_id: 12345,
       type: "transaction_confirmed",
       channel: "push",
       title: "Swap Complete! ✅",
       message: "You received 0.0204 ETH",
       priority: "medium",
       status: "pending"
     }

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Success Screen                                          │
└─────────────────────────────────────────────────────────────────┘

UI Display: Success Screen
  - Checkmark animation
  - "Swap Complete!"
  - From: 50 USDC
  - To: 0.0204 ETH ($50.00)
  - Transaction hash (linked)
  - "View in Portfolio" button
  - "Done" button

User Action: Taps "Done"

Frontend Action:
  → Navigate to Home
  → Refresh balance

UI Display: Home Dashboard (Updated)
  - Portfolio: $100.35
  - Assets:
    - 50 USDC ($50.00)
    - 0.0204 ETH ($50.35)
  - Activity feed shows new swap

✅ SUCCESS CRITERIA:
  - Swap executed successfully
  - User received expected ETH amount
  - Balances updated correctly
  - Transaction visible in activity feed
  - User notified of success
```

**Total Time:** ~1-2 minutes  
**Database Tables Affected:** `transactions`, `chain_addresses`, `llm_conversations`, `agent_executions`, `agent_tasks`, `agent_tools_usage`, `notifications`  
**External Services:** 1inch (DEX aggregator), Privy (transaction signing), Arbitrum RPC

---

## 4. Yield Farming (Earn) Flow

### Flow: Deposit USDC to Aave for Yield

**User Goal:** Deposit 50 USDC into Aave on Arbitrum to earn yield

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to Earn                                        │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Earn" tab

UI Display: Earn Screen
  - "Discover Opportunities" header
  - Protocol cards (Aave, Compound, Curve)
  - Sort by: APY, TVL, Risk
  - Search bar

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Browse Aave Opportunity                                 │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → GET /api/v1/user/earn/opportunities
  → Authorization: Bearer [access_token]
  
Query params:
  ?chain=arbitrum&protocol=aave

Backend Process:
  1. Fetch current APYs from Aave API
  2. Calculate risk scores
  3. Return opportunities

Response: 200 OK
{
  "success": true,
  "data": {
    "opportunities": [
      {
        "protocol": "aave",
        "chain": "arbitrum",
        "asset": "USDC",
        "apy": 4.2,
        "tvl": "125000000",
        "risk_score": "low",
        "description": "Lend USDC and earn interest"
      }
    ]
  }
}

UI Display: Aave Card
  - Logo: Aave
  - Asset: USDC
  - APY: 4.2% ⬆️
  - TVL: $125M
  - Risk: Low
  - Chain: Arbitrum
  - "Earn" button

User Action: Taps "Earn" on Aave USDC card

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Aave Detail View                                        │
└─────────────────────────────────────────────────────────────────┘

UI Display: Aave USDC Detail
  - Current APY: 4.2%
  - APY chart (30-day history)
  - Your deposit: $0
  - Available balance: 50 USDC
  - Total supplied: $125M
  - Utilization rate: 75%
  - Risk assessment: Low (Aave is battle-tested)
  - Amount input field
  - "Review Deposit" button

User Input: Amount = 50 USDC

User Action: Taps "Review Deposit"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: AI Risk Analysis                                        │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/chat/message

Request:
{
  "message": "Analyze the risk of depositing 50 USDC into Aave on Arbitrum",
  "session_id": "session_xyz789"
}

Backend Process:
  1. Create agent execution
     
     DB INSERT: agent_executions
     {
       user_id: 12345,
       agent_type: "risk",
       workflow_type: "earn",
       status: "running",
       input_params: {
         "protocol": "aave",
         "asset": "USDC",
         "amount": 50,
         "chain": "arbitrum"
       }
     }
  
  2. Execute risk agent tasks
     
     Task 1: Check protocol security
     - Aave audit history
     - TVL history
     - Exploit history
     
     Task 2: Check smart contract risk
     - Contract verified
     - Time-locked admin
     - No recent critical issues
     
     Task 3: Check market conditions
     - USDC utilization: 75% (healthy)
     - Liquidation risk: None (stablecoin)
     - APY sustainability: Yes
  
  3. LLM generates risk report
     
     DB INSERT: llm_conversations
     {
       user_id: 12345,
       provider: "vertex",
       model_name: "gemini-1.5-flash",
       prompt_text: "Analyze risk...",
       response_text: "Risk Assessment: LOW. Aave is a well-established...",
       cost_usd: 0.00004
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "risk_assessment": {
      "overall_risk": "low",
      "protocol_security": "excellent",
      "smart_contract_risk": "low",
      "market_risk": "low",
      "recommendation": "Safe to proceed",
      "expected_annual_earnings": "$2.10 (4.2% APY)",
      "estimated_daily_earnings": "$0.0057"
    },
    "ai_summary": "Risk Assessment: LOW. Aave is well-established with $5B+ TVL..."
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Review Deposit                                          │
└─────────────────────────────────────────────────────────────────┘

UI Display: Review Modal
  - Depositing: 50 USDC → Aave
  - Current APY: 4.2%
  - Estimated earnings: $0.0057/day, $2.10/year
  - Risk: Low ✅
  - Gas fee: ~$0.50
  - "Confirm Deposit" button
  - "Cancel" button

User Action: Taps "Confirm Deposit"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Execute Deposit Transaction                             │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/earn/deposit
  → Authorization: Bearer [access_token]

Request:
{
  "protocol": "aave",
  "asset": "USDC",
  "amount": "50",
  "chain": "arbitrum"
}

Backend Process:
  1. Prepare Aave deposit transaction
     
     Contract: Aave V3 Pool (Arbitrum)
     Method: supply(asset, amount, onBehalfOf, referralCode)
     
  2. Sign with Privy
     
     Privy API: signTransaction({
       to: "0xaave_pool_arbitrum...",
       data: "supply(...)",
       gas: 250000
     })
  
  3. Submit to blockchain
     
     tx_hash: "0xearn123abc..."
  
  4. Create earn position record
     
     DB INSERT: earn_positions
     {
       user_id: 12345,
       wallet_id: 67890,
       chain: "arbitrum",
       protocol: "aave",
       asset: "USDC",
       amount_deposited: 50.0,
       current_value: 50.0,
       apy: 4.2,
       current_apy: 4.2,
       status: "active",
       deposit_tx_hash: "0xearn123abc...",
       deposited_at: NOW(),
       created_at: NOW()
     }
  
  5. Create transaction record
     
     DB INSERT: transactions
     {
       user_id: 12345,
       wallet_id: 67890,
       type: 2 (EARN),
       chain: "arbitrum",
       asset_in: "USDC",
       amount_in: 50.0,
       tx_hash: "0xearn123abc...",
       status: 0 (PENDING),
       created_at: NOW()
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "position_id": 101,
    "tx_hash": "0xearn123abc...",
    "status": "pending"
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Transaction Confirmation                                │
└─────────────────────────────────────────────────────────────────┘

UI Display: Pending Screen
  - "Depositing to Aave..."
  - Animated loader
  - Transaction hash (linked)
  - "Usually takes 30-60 seconds"

Background Job:
  1. Monitor transaction
     
     Web3: eth.getTransactionReceipt("0xearn123abc...")
     
     Result: Success (block: 12345685)
  
  2. Update records
     
     DB UPDATE: transactions
     SET status = 1 (SUCCESS),
         confirmed_at = NOW()
     WHERE tx_hash = "0xearn123abc..."
     
     DB UPDATE: earn_positions
     SET status = "active"
     WHERE id = 101
  
  3. Update balance
     
     DB UPDATE: chain_addresses
     SET balance_usd = 50.35, // Only ETH remains
         last_balance_update = NOW()
  
  4. Send notification
     
     DB INSERT: notifications
     {
       user_id: 12345,
       type: "earn_deposit_completed",
       title: "Earning Started! 💰",
       message: "50 USDC is now earning 4.2% APY on Aave",
       priority: "medium"
     }

┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Success & Position Monitoring                           │
└─────────────────────────────────────────────────────────────────┘

UI Display: Success Screen
  - "Deposit Complete!"
  - Amount: 50 USDC
  - Protocol: Aave (Arbitrum)
  - Current APY: 4.2%
  - Earning: $0.0057/day
  - "View Position" button

User Action: Taps "View Position"

UI Display: Earn Tab → Active Positions
  - Aave USDC position card:
    - Deposited: 50 USDC
    - Current value: $50.00
    - Rewards earned: $0.00 (just started)
    - APY: 4.2%
    - Daily earnings: $0.0057
    - "Withdraw" button
    - "Add More" button

✅ SUCCESS CRITERIA:
  - 50 USDC deposited to Aave
  - Position record created and active
  - User earning yield (4.2% APY)
  - Position visible in Earn tab
```

**Hourly Background Job: Update Earn Positions**

```
Job: Update Earn Position Values
Runs: Every hour

Process:
  1. Query active earn positions
     
     SELECT * FROM earn_positions
     WHERE status = 'active'
  
  2. For each position:
     a. Fetch current balance from Aave
        
        Aave API: getReserveData(asset, user)
        
        Response: {
          "balance": "50.0057",
          "apy": 4.3
        }
     
     b. Calculate rewards
        
        rewards_earned = current_balance - amount_deposited
        = 50.0057 - 50.0
        = 0.0057 USDC
     
     c. Update position
        
        DB UPDATE: earn_positions
        SET current_value = 50.0057,
            current_apy = 4.3,
            rewards_earned = 0.0057,
            rewards_earned_usd = 0.0057
        WHERE id = 101

User sees updated earnings in real-time when opening app!
```

**Total Time:** ~1-2 minutes  
**Database Tables Affected:** `earn_positions`, `transactions`, `chain_addresses`, `llm_conversations`, `agent_executions`, `notifications`  
**External Services:** Aave V3 (protocol), Privy (signing), Arbitrum RPC

---

## 5. Recurring Savings Setup

### Flow: Set Up Auto-Save $20 Weekly to Aave

**User Goal:** Automatically save $20 in USDC every Monday to Aave

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to Auto-Save                                   │
└─────────────────────────────────────────────────────────────────┘

User Action: Taps "Earn" → "Auto-Save" button

UI Display: Auto-Save Setup Screen
  - "Save Automatically"header
  - "Build wealth on autopilot"
  - Existing schedules (if any)
  - "+ Create New Schedule" button

User Action: Taps "+ Create New Schedule"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Configure Savings Schedule                              │
└─────────────────────────────────────────────────────────────────┘

UI Display: Schedule Setup Form
  
  1. Amount to Save
     - Input field: "How much?"
     - Currency: USDC
     - Available balance: 50 USDC
  
  2. Frequency
     - Radio buttons:
       [ ] Daily
       [x] Weekly
       [ ] Bi-weekly
       [ ] Monthly
  
  3. Day of Week (if weekly)
     - Dropdown: Monday
  
  4. Destination
     - Radio buttons:
       [x] Aave (Earn 4.2% APY)
       [ ] Just save to wallet
  
  5. Duration (optional)
     - "Save forever" toggle (ON)
     - Or set max executions
  
  - "Review Schedule" button

User Input:
  - Amount: $20
  - Frequency: Weekly
  - Day: Monday
  - Destination: Aave
  - Duration: Forever

User Action: Taps "Review Schedule"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: AI Validation & Projection                              │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/chat/message

Request:
{
  "message": "Validate and project: save $20 USDC weekly to Aave at 4.2% APY",
  "session_id": "session_save123"
}

Backend Process:
  1. Create agent execution
     
     DB INSERT: agent_executions
     {
       user_id: 12345,
       agent_type: "analysis",
       workflow_type: "save",
       status: "running",
       input_params: {
         "amount": 20,
         "frequency": "weekly",
         "destination": "aave",
         "apy": 4.2
       }
     }
  
  2. Analysis agent calculates projections
     
     Projections:
     - Week 1: $20.00
     - Month 1: $80.00
     - Month 6: $480.00 + $5.04 interest = $485.04
     - Year 1: $1,040.00 + $21.84 interest = $1,061.84
     - Year 5: $5,200.00 + $547.20 interest = $5,747.20
  
  3. LLM generates projection report
     
     DB INSERT: llm_conversations
     {
       prompt_text: "Project savings...",
       response_text: "Great plan! In 1 year, you'll have saved...",
       cost_usd: 0.00005
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "projections": {
      "month_1": {"principal": 80.00, "interest": 0.28, "total": 80.28},
      "month_6": {"principal": 480.00, "interest": 5.04, "total": 485.04},
      "year_1": {"principal": 1040.00, "interest": 21.84, "total": 1061.84},
      "year_5": {"principal": 5200.00, "interest": 547.20, "total": 5747.20}
    },
    "ai_summary": "Great plan! By saving $20 weekly at 4.2% APY..."
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Review Schedule                                         │
└─────────────────────────────────────────────────────────────────┘

UI Display: Review Modal
  - Schedule: Every Monday
  - Amount: $20 USDC
  - Destination: Aave (4.2% APY)
  - First execution: Next Monday (Nov 18, 2025)
  - 
  - Projections:
    - 1 month: $80.28
    - 6 months: $485.04
    - 1 year: $1,061.84
    - 5 years: $5,747.20
  
  - Required balance: $20 USDC (you have $50)
  - Gas fees: ~$0.50 per execution
  
  - "Confirm Schedule" button
  - "Edit" button

User Action: Taps "Confirm Schedule"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Create Savings Schedule                                 │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → POST /api/v1/user/save/schedule
  → Authorization: Bearer [access_token]

Request:
{
  "asset": "USDC",
  "amount": "20",
  "frequency": "weekly",
  "day_of_week": 1,
  "destination_protocol": "aave",
  "chain": "arbitrum"
}

Backend Process:
  1. Validate user balance
  2. Calculate next execution
     
     next_execution_at = Next Monday 00:00 UTC
     = 2025-11-18 00:00:00
  
  3. Create schedule
     
     DB INSERT: save_schedules
     {
       user_id: 12345,
       wallet_id: 67890,
       chain: "arbitrum",
       asset: "USDC",
       amount: 20.0,
       frequency: "weekly",
       day_of_week: 1, // Monday
       destination_protocol: "aave",
       status: "active",
       next_execution_at: "2025-11-18 00:00:00",
       total_saved: 0,
       execution_count: 0,
       max_executions: NULL, // forever
       created_at: NOW()
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "schedule_id": 201,
    "status": "active",
    "next_execution": "2025-11-18T00:00:00Z",
    "message": "Auto-save schedule created successfully"
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Success Confirmation                                    │
└─────────────────────────────────────────────────────────────────┘

UI Display: Success Screen
  - "Auto-Save Activated! 🎯"
  - Schedule summary
  - Next save: Monday, Nov 18
  - Calendar icon with reminder
  - "Done" button

DB INSERT: notifications
{
  user_id: 12345,
  type: "save_schedule_created",
  channel: "push",
  title: "Auto-Save Activated!",
  message: "$20 will be saved to Aave every Monday",
  priority: "low"
}

User Action: Taps "Done"

UI Display: Auto-Save Screen
  - Active Schedules section:
    - Weekly Aave Savings card:
      - Every Monday
      - $20 USDC
      - Total saved: $0 (0 executions)
      - Next: Nov 18, 2025
      - Status: Active
      - "Pause" button
      - "Edit" button

✅ SUCCESS CRITERIA:
  - Schedule created and active
  - Next execution scheduled
  - User notified of setup success
  - Schedule visible in Auto-Save screen
```

**Scheduled Execution (Cron Job)**

```
┌─────────────────────────────────────────────────────────────────┐
│ AUTOMATIC EXECUTION (Monday, Nov 18, 2025 00:00 UTC)           │
└─────────────────────────────────────────────────────────────────┘

Cron Job: Execute Scheduled Saves
Runs: Every hour

Process:
  1. Query due schedules
     
     SELECT * FROM save_schedules
     WHERE status = 'active'
     AND next_execution_at <= NOW()
  
  2. Found schedule #201 (user 12345)
  
  3. Check balance
     
     SELECT balance_usd FROM chain_addresses
     WHERE wallet_id = 67890
     AND chain = 'arbitrum'
     
     Result: 30 USDC available ✅
  
  4. Execute save → deposit to Aave
     
     Same process as manual earn deposit:
     a. Prepare Aave supply transaction
     b. Sign with Privy
     c. Submit to blockchain
     d. tx_hash: "0xautosave123..."
  
  5. Create records
     
     DB INSERT: transactions
     {
       user_id: 12345,
       type: 3 (SAVE),
       asset_in: "USDC",
       amount_in: 20.0,
       tx_hash: "0xautosave123...",
       status: 0 (PENDING)
     }
     
     DB INSERT: earn_positions (or update existing)
     {
       user_id: 12345,
       protocol: "aave",
       asset: "USDC",
       amount_deposited: 70.0, // 50 + 20
       current_value: 70.06, // includes previous rewards
       deposit_tx_hash: "0xautosave123..."
     }
  
  6. Update schedule
     
     DB UPDATE: save_schedules
     SET execution_count = 1,
         total_saved = 20.0,
         last_execution_at = NOW(),
         next_execution_at = '2025-11-25 00:00:00' // Next Monday
     WHERE id = 201
  
  7. Send notification
     
     DB INSERT: notifications
     {
       user_id: 12345,
       type: "auto_save_executed",
       channel: "push",
       title: "Auto-Save Complete! 💰",
       message: "$20 USDC saved to Aave. Total: $70",
       priority: "medium"
     }

User wakes up Monday morning to notification!
Sees updated Aave position: $70.06 earning 4.2% APY
```

**Total Time:** ~2 minutes to set up, automatic execution thereafter  
**Database Tables Affected:** `save_schedules`, `earn_positions`, `transactions`, `notifications`  
**External Services:** Aave V3, Privy, Arbitrum RPC

---

*Continuing in next file...*

**Status:** Created Part 1 of CLIENT user flows covering:
1. Onboarding & Authentication ✅
2. Wallet Setup & Funding ✅
3. Token Swap Flow ✅
4. Yield Farming (Earn) Flow ✅
5. Recurring Savings Setup ✅

Shall I continue with the remaining CLIENT flows (6-10)?

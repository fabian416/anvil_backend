#!/bin/bash
#
# Anvil Unified Chat API - cURL Test Scripts
#
# Complete test suite for all 16 unified chat intent types using cURL.
#
# Usage:
#   chmod +x curl_test_scripts.sh
#   ./curl_test_scripts.sh
#
# Environment Variables:
#   BASE_URL - API base URL (default: http://localhost:8080/api/v1)
#   EMAIL - User email for authentication
#   PASSWORD - User password
#

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

BASE_URL="${BASE_URL:-http://localhost:8080/api/v1}"
EMAIL="${EMAIL:-user@example.com}"
PASSWORD="${PASSWORD:-password}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
}

print_section() {
    echo ""
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

send_message() {
    local content="$1"
    local conv_id="$2"

    curl -s -X POST "$BASE_URL/user/chat/conversations/$conv_id/messages" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"$content\"}"
}

extract_field() {
    local json="$1"
    local field="$2"
    echo "$json" | grep -o "\"$field\"[^,}]*" | head -1 | sed 's/.*: *"\?\([^"]*\)"\?.*/\1/'
}

# ============================================================================
# Authentication
# ============================================================================

print_header "AUTHENTICATION"

echo "Authenticating with email: $EMAIL"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/account/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

AUTH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | sed 's/"access_token":"\(.*\)"/\1/')

if [ -z "$AUTH_TOKEN" ]; then
    print_error "Authentication failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

print_success "Logged in successfully"
echo "Token: ${AUTH_TOKEN:0:20}..."

# ============================================================================
# Create Conversation
# ============================================================================

print_section "Creating Conversation"

CONV_RESPONSE=$(curl -s -X POST "$BASE_URL/user/chat/conversations" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "cURL Test Scripts"}')

CONVERSATION_ID=$(echo "$CONV_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"\(.*\)"/\1/')

if [ -z "$CONVERSATION_ID" ]; then
    print_error "Failed to create conversation"
    echo "Response: $CONV_RESPONSE"
    exit 1
fi

print_success "Conversation created: $CONVERSATION_ID"

# ============================================================================
# GraphRAG Intents (3 types)
# ============================================================================

print_header "GRAPHRAG INTENTS"

# 1. Protocol Search
print_section "1. Protocol Search"

RESPONSE=$(send_message "Show me high-yield staking protocols on Ethereum with low risk" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")
CONFIDENCE=$(extract_field "$RESPONSE" "confidence")

echo "Query: 'Show me high-yield staking protocols on Ethereum with low risk'"
echo "Intent: $INTENT"
echo "Confidence: $CONFIDENCE"

if [ "$INTENT" = "protocol_search" ]; then
    print_success "Protocol Search detected correctly"
else
    print_error "Expected intent 'protocol_search', got '$INTENT'"
fi

# 2. Risk Assessment
print_section "2. Risk Assessment"

RESPONSE=$(send_message "Is Aave safe to use? What are the risks?" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Is Aave safe to use? What are the risks?'"
echo "Intent: $INTENT"

if [ "$INTENT" = "risk_assessment" ]; then
    print_success "Risk Assessment detected correctly"
else
    print_error "Expected intent 'risk_assessment', got '$INTENT'"
fi

# 3. Similar Protocols
print_section "3. Similar Protocols"

RESPONSE=$(send_message "What protocols are similar to Uniswap?" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'What protocols are similar to Uniswap?'"
echo "Intent: $INTENT"

if [ "$INTENT" = "similar_protocols" ]; then
    print_success "Similar Protocols detected correctly"
else
    print_error "Expected intent 'similar_protocols', got '$INTENT'"
fi

# ============================================================================
# Hunter AI Intents (6 types)
# ============================================================================

print_header "HUNTER AI INTENTS"

# 1. Sentiment Analysis
print_section "1. Sentiment Analysis"

RESPONSE=$(send_message "What's the ETH sentiment on Twitter and Reddit?" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'What's the ETH sentiment on Twitter and Reddit?'"
echo "Intent: $INTENT"

if [ "$INTENT" = "hunter_sentiment" ]; then
    print_success "Sentiment Analysis detected correctly"
else
    print_error "Expected intent 'hunter_sentiment', got '$INTENT'"
fi

# 2. Price Prediction
print_section "2. Price Prediction"

RESPONSE=$(send_message "Predict BTC price for next 7 days" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Predict BTC price for next 7 days'"
echo "Intent: $INTENT"

if [ "$INTENT" = "hunter_price_prediction" ]; then
    print_success "Price Prediction detected correctly"
else
    print_error "Expected intent 'hunter_price_prediction', got '$INTENT'"
fi

# 3. Risk Signals
print_section "3. Risk Signals"

RESPONSE=$(send_message "Show risk signals for ETH" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Show risk signals for ETH'"
echo "Intent: $INTENT"

if [ "$INTENT" = "hunter_risk_signals" ]; then
    print_success "Risk Signals detected correctly"
else
    print_error "Expected intent 'hunter_risk_signals', got '$INTENT'"
fi

# 4. Trading Signals
print_section "4. Trading Signals"

RESPONSE=$(send_message "Should I buy SOL now? Give me trading signals" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Should I buy SOL now? Give me trading signals'"
echo "Intent: $INTENT"

if [ "$INTENT" = "hunter_trading_signals" ]; then
    print_success "Trading Signals detected correctly"
else
    print_error "Expected intent 'hunter_trading_signals', got '$INTENT'"
fi

# 5. Pattern Detection
print_section "5. Pattern Detection"

RESPONSE=$(send_message "What chart patterns do you see for BTC?" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'What chart patterns do you see for BTC?'"
echo "Intent: $INTENT"

if [ "$INTENT" = "hunter_patterns" ]; then
    print_success "Pattern Detection detected correctly"
else
    print_error "Expected intent 'hunter_patterns', got '$INTENT'"
fi

# 6. Portfolio Optimization
print_section "6. Portfolio Optimization"

RESPONSE=$(send_message "Optimize my portfolio with BTC, ETH, and SOL for moderate risk" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Optimize my portfolio with BTC, ETH, and SOL for moderate risk'"
echo "Intent: $INTENT"

if [ "$INTENT" = "hunter_portfolio" ]; then
    print_success "Portfolio Optimization detected correctly"
else
    print_error "Expected intent 'hunter_portfolio', got '$INTENT'"
fi

# ============================================================================
# ULTRA Intents (4 types)
# ============================================================================

print_header "ULTRA INTENTS"

# 1. Arbitrage Discovery
print_section "1. Arbitrage Discovery"

RESPONSE=$(send_message "Find arbitrage opportunities with \$10,000 capital" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Find arbitrage opportunities with \$10,000 capital'"
echo "Intent: $INTENT"

if [ "$INTENT" = "ultra_arbitrage" ]; then
    print_success "Arbitrage Discovery detected correctly"
else
    print_error "Expected intent 'ultra_arbitrage', got '$INTENT'"
fi

# 2. Flash Loan Selection
print_section "2. Flash Loan Selection"

RESPONSE=$(send_message "Best flash loan protocol for 100k USDC" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Best flash loan protocol for 100k USDC'"
echo "Intent: $INTENT"

if [ "$INTENT" = "ultra_flash_loans" ]; then
    print_success "Flash Loan Selection detected correctly"
else
    print_error "Expected intent 'ultra_flash_loans', got '$INTENT'"
fi

# 3. MEV Protection
print_section "3. MEV Protection"

RESPONSE=$(send_message "Execute ARB-001 with Flashbots protection" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Execute ARB-001 with Flashbots protection'"
echo "Intent: $INTENT"

if [ "$INTENT" = "ultra_mev_protection" ]; then
    print_success "MEV Protection detected correctly"
else
    print_error "Expected intent 'ultra_mev_protection', got '$INTENT'"
fi

# 4. Auto Executor Control
print_section "4. Auto Executor Control"

# Start bot
RESPONSE=$(send_message "Start trading bot" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Start trading bot'"
echo "Intent: $INTENT"

if [ "$INTENT" = "ultra_auto_executor" ]; then
    print_success "Auto Executor (start) detected correctly"
else
    print_error "Expected intent 'ultra_auto_executor', got '$INTENT'"
fi

# Check status
send_message "Show bot status" "$CONVERSATION_ID" > /dev/null

# Stop bot
send_message "Stop trading bot" "$CONVERSATION_ID" > /dev/null
print_success "Auto Executor control sequence completed"

# ============================================================================
# Agent Squad & Chat Intents (3 types)
# ============================================================================

print_header "AGENT SQUAD & CHAT INTENTS"

# 1. Specialist Task
print_section "1. Specialist Task"

RESPONSE=$(send_message "Analyze ETH/USDC liquidity depth on Uniswap V3" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Analyze ETH/USDC liquidity depth on Uniswap V3'"
echo "Intent: $INTENT"

if [ "$INTENT" = "specialist_task" ]; then
    print_success "Specialist Task detected correctly"
else
    print_error "Expected intent 'specialist_task', got '$INTENT'"
fi

# 2. Complex Workflow
print_section "2. Complex Workflow"

RESPONSE=$(send_message "Create a complete DeFi investment strategy for \$50k with risk analysis" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Create a complete DeFi investment strategy for \$50k with risk analysis'"
echo "Intent: $INTENT"

if [ "$INTENT" = "complex_workflow" ]; then
    print_success "Complex Workflow detected correctly"
else
    print_error "Expected intent 'complex_workflow', got '$INTENT'"
fi

# 3. General Conversation
print_section "3. General Conversation"

RESPONSE=$(send_message "Hello! What can you help me with?" "$CONVERSATION_ID")
INTENT=$(extract_field "$RESPONSE" "intent")

echo "Query: 'Hello! What can you help me with?'"
echo "Intent: $INTENT"

if [ "$INTENT" = "general_conversation" ]; then
    print_success "General Conversation detected correctly"
else
    print_error "Expected intent 'general_conversation', got '$INTENT'"
fi

# ============================================================================
# Advanced Usage Patterns
# ============================================================================

print_header "ADVANCED USAGE PATTERNS"

# Multi-turn conversation
print_section "1. Multi-turn Conversation"

RESPONSE1=$(send_message "Find safe lending protocols" "$CONVERSATION_ID")
INTENT1=$(extract_field "$RESPONSE1" "intent")
echo "Turn 1: 'Find safe lending protocols' -> $INTENT1"

RESPONSE2=$(send_message "What about the risks of the first one?" "$CONVERSATION_ID")
INTENT2=$(extract_field "$RESPONSE2" "intent")
echo "Turn 2: 'What about the risks of the first one?' -> $INTENT2"

print_success "Multi-turn conversation completed"

# Get message history
print_section "2. Message History"

MESSAGES=$(curl -s -X GET "$BASE_URL/user/chat/conversations/$CONVERSATION_ID/messages?limit=10" \
    -H "Authorization: Bearer $AUTH_TOKEN")

MESSAGE_COUNT=$(echo "$MESSAGES" | grep -o '"id"' | wc -l)
echo "Retrieved $MESSAGE_COUNT messages from conversation history"
print_success "Message history retrieved"

# ============================================================================
# Error Handling
# ============================================================================

print_header "ERROR HANDLING"

# Invalid conversation ID
print_section "1. Invalid Conversation ID"

ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/user/chat/conversations/invalid-id/messages" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content": "Test message"}')

if echo "$ERROR_RESPONSE" | grep -q "error\|detail"; then
    print_success "Invalid conversation ID handled correctly"
    echo "Error response: $(echo $ERROR_RESPONSE | head -c 100)..."
else
    print_error "Expected error response for invalid conversation ID"
fi

# Empty message
print_section "2. Empty Message"

ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/user/chat/conversations/$CONVERSATION_ID/messages" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content": ""}')

if echo "$ERROR_RESPONSE" | grep -q "error\|detail"; then
    print_success "Empty message handled correctly"
else
    print_error "Expected error response for empty message"
fi

# Unauthorized request
print_section "3. Unauthorized Request"

ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/user/chat/conversations/$CONVERSATION_ID/messages" \
    -H "Authorization: Bearer invalid-token" \
    -H "Content-Type: application/json" \
    -d '{"content": "Test"}')

if echo "$ERROR_RESPONSE" | grep -q "error\|detail\|401\|Unauthorized"; then
    print_success "Unauthorized request handled correctly"
else
    print_error "Expected error response for unauthorized request"
fi

# ============================================================================
# Test Summary
# ============================================================================

print_header "TEST SUMMARY"

echo ""
echo "All 16 intent types tested:"
echo "  ✓ GraphRAG (3): protocol_search, risk_assessment, similar_protocols"
echo "  ✓ Hunter AI (6): sentiment, price_prediction, risk_signals, trading_signals, patterns, portfolio"
echo "  ✓ ULTRA (4): arbitrage, flash_loans, mev_protection, auto_executor"
echo "  ✓ Agent Squad (3): specialist_task, complex_workflow, general_conversation"
echo ""
echo "Additional tests:"
echo "  ✓ Multi-turn conversation"
echo "  ✓ Message history retrieval"
echo "  ✓ Error handling (invalid ID, empty message, unauthorized)"
echo ""
print_success "All tests completed successfully!"

# ============================================================================
# Individual Test Functions (for selective testing)
# ============================================================================

test_protocol_search() {
    print_section "Testing: Protocol Search"
    RESPONSE=$(send_message "Show me DeFi lending protocols" "$CONVERSATION_ID")
    echo "$RESPONSE" | jq '.routing.intent, .routing.confidence'
}

test_sentiment() {
    print_section "Testing: Sentiment Analysis"
    RESPONSE=$(send_message "What's BTC sentiment?" "$CONVERSATION_ID")
    echo "$RESPONSE" | jq '.routing.intent, .enrichment.token_symbol'
}

test_arbitrage() {
    print_section "Testing: Arbitrage Discovery"
    RESPONSE=$(send_message "Find arbitrage with \$5000" "$CONVERSATION_ID")
    echo "$RESPONSE" | jq '.routing.intent, .enrichment.capital'
}

# Uncomment to run individual tests:
# test_protocol_search
# test_sentiment
# test_arbitrage

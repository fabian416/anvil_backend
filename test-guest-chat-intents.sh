#!/bin/bash
# Guest Chat Intent Testing Script
# Based on: docs/steering/guest-chat-intent-testing.md
# Endpoint: POST /api/v1/guest/chat

# Don't exit on error - continue testing all intents
set +e

BASE_URL="http://localhost:8080/api/v1/guest/chat"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test function
test_intent() {
    local intent_name=$1
    local test_message=$2
    local expected_handler=$3
    local expected_intent=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test #${TOTAL_TESTS}: ${intent_name}${NC}"
    echo -e "${BLUE}Message: \"${test_message}\"${NC}"
    echo -e "${BLUE}Expected Intent: ${expected_intent}${NC}"
    echo -e "${BLUE}Expected Handler: ${expected_handler}${NC}"
    
    # Make request
    response=$(curl -s -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"${test_message}\", \"language\": \"en\"}")
    
    # Extract values from response
    detected_intent=$(echo "$response" | jq -r '.routing.intent // "unknown"' 2>/dev/null || echo "unknown")
    detected_handler=$(echo "$response" | jq -r '.routing.handler // "unknown"' 2>/dev/null || echo "unknown")
    confidence=$(echo "$response" | jq -r '.routing.confidence // 0' 2>/dev/null || echo "0")
    has_content=$(echo "$response" | jq -r '.agent_message.content // ""' 2>/dev/null || echo "")
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"${test_message}\", \"language\": \"en\"}")
    
    # Check results (case-insensitive comparison)
    intent_match=false
    handler_match=false
    has_response=false
    
    # Normalize to lowercase for comparison
    detected_intent_lower=$(echo "$detected_intent" | tr '[:upper:]' '[:lower:]')
    expected_intent_lower=$(echo "$expected_intent" | tr '[:upper:]' '[:lower:]')
    detected_handler_lower=$(echo "$detected_handler" | tr '[:upper:]' '[:lower:]')
    expected_handler_lower=$(echo "$expected_handler" | tr '[:upper:]' '[:lower:]')
    
    if [ "$detected_intent_lower" = "$expected_intent_lower" ] || [ "$expected_intent" = "any" ]; then
        intent_match=true
    fi
    
    if [ "$detected_handler_lower" = "$expected_handler_lower" ] || [ "$expected_handler" = "any" ]; then
        handler_match=true
    fi
    
    if [ -n "$has_content" ] && [ "$has_content" != "null" ] && [ ${#has_content} -gt 10 ]; then
        has_response=true
    fi
    
    # Print results
    echo -e "Detected Intent: ${detected_intent}"
    echo -e "Detected Handler: ${detected_handler}"
    echo -e "Confidence: ${confidence}"
    echo -e "Status Code: ${status_code}"
    echo -e "Has Response: ${has_response}"
    
    # Validate
    if [ "$status_code" = "200" ] && [ "$intent_match" = true ] && [ "$handler_match" = true ] && [ "$has_response" = true ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        if [ "$status_code" != "200" ]; then
            echo -e "${RED}  - Status code: ${status_code} (expected 200)${NC}"
        fi
        if [ "$intent_match" = false ]; then
            echo -e "${RED}  - Intent mismatch: got '${detected_intent}', expected '${expected_intent}'${NC}"
        fi
        if [ "$handler_match" = false ]; then
            echo -e "${RED}  - Handler mismatch: got '${detected_handler}', expected '${expected_handler}'${NC}"
        fi
        if [ "$has_response" = false ]; then
            echo -e "${RED}  - No valid response content${NC}"
        fi
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 0  # Return 0 to continue testing even on failure
    fi
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Guest Chat Intent Testing - All Intents                  ║${NC}"
echo -e "${BLUE}║  Endpoint: ${BASE_URL}${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# DeFi Shortcut Intents
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}DeFi Shortcut Intents${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_intent "LENDING" "deposit 1000 usdc into morpho vault" "lending_handler" "LENDING"
test_intent "MONEY_MARKET" "compare aave vs compound" "money_market_handler" "MONEY_MARKET"
test_intent "SWAP" "swap eth for usdc" "swap_handler" "SWAP"
test_intent "BALANCE" "show my balance" "balance_handler" "BALANCE"
test_intent "PORTFOLIO" "show my portfolio" "portfolio_handler" "PORTFOLIO"
test_intent "ACTIVITY" "show my transactions" "activity_handler" "ACTIVITY"
test_intent "RECEIVE" "show my address" "receive_handler" "RECEIVE"

# Hunter AI Intents
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Hunter AI Intents${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_intent "HUNTER_SENTIMENT" "what's the eth sentiment on twitter and reddit?" "hunter_ai" "HUNTER_SENTIMENT"
test_intent "HUNTER_PRICE_PREDICTION" "predict btc price for next 7 days" "hunter_ai" "HUNTER_PRICE_PREDICTION"
test_intent "HUNTER_RISK_SIGNALS" "show risk signals for eth" "hunter_ai" "HUNTER_RISK_SIGNALS"
test_intent "HUNTER_TRADING_SIGNALS" "should i buy sol now? give me trading signals" "hunter_ai" "HUNTER_TRADING_SIGNALS"
test_intent "HUNTER_PATTERNS" "what chart patterns do you see for btc?" "hunter_ai" "HUNTER_PATTERNS"
test_intent "HUNTER_PORTFOLIO" "optimize my portfolio with btc, eth, and sol for moderate risk" "hunter_ai" "HUNTER_PORTFOLIO"

# ULTRA Intents
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}ULTRA Intents (DeFi Automation)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_intent "ULTRA_ARBITRAGE" "find arbitrage opportunities with \$10,000 capital" "ultra" "ULTRA_ARBITRAGE"
test_intent "ULTRA_FLASH_LOANS" "best flash loan protocol for 100k usdc" "ultra" "ULTRA_FLASH_LOANS"
test_intent "ULTRA_MEV_PROTECTION" "send this transaction privately to avoid mev" "ultra" "ULTRA_MEV_PROTECTION"
test_intent "ULTRA_AUTO_EXECUTOR" "start trading bot" "ultra" "ULTRA_AUTO_EXECUTOR"

# GraphRAG Intents
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}GraphRAG Intents${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_intent "PROTOCOL_SEARCH" "show me high-yield lending protocols on ethereum" "graphrag_search" "PROTOCOL_SEARCH"
test_intent "RISK_ASSESSMENT" "is aave safe to use? what are the risks?" "graphrag_search" "RISK_ASSESSMENT"
test_intent "SIMILAR_PROTOCOLS" "what protocols are similar to uniswap?" "graphrag_search" "SIMILAR_PROTOCOLS"

# Agent Squad Intents
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Agent Squad Intents${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_intent "SPECIALIST_TASK" "analyze eth/usdc liquidity depth on uniswap v3" "agent_orchestrator" "SPECIALIST_TASK"
test_intent "COMPLEX_WORKFLOW" "create a complete defi investment strategy for \$50k with risk analysis" "agent_orchestrator" "COMPLEX_WORKFLOW"

# General Conversation
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}General Conversation${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_intent "GENERAL_CONVERSATION" "hello! what can you help me with?" "general_chat" "GENERAL_CONVERSATION"

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Summary                                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

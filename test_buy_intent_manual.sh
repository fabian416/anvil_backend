#!/bin/bash
# Manual test script for buy crypto intent
# Tests that wallet appears in buy intent response

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Buy Crypto Intent Test${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# Configuration
API_BASE="https://testanvilcrypto.ddnsking.com/api/v1"
EMAIL="ops@anvilcrypto.com"
EXPECTED_WALLET="0xc42c83fff8891a368b2579ebd3e964dcef6e0e97"

# Check if token is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No auth token provided${NC}"
    echo -e "\nUsage: $0 <your-jwt-token>"
    echo -e "\nGet your token by:"
    echo -e "  1. Login at https://testanvilcrypto.ddnsking.com"
    echo -e "  2. Open DevTools > Application > Session Storage"
    echo -e "  3. Copy the 'token' value"
    exit 1
fi

TOKEN="$1"

echo -e "${GREEN}✓ Token provided${NC}"
echo -e "User: $EMAIL"
echo -e "Expected wallet: $EXPECTED_WALLET\n"

# Step 1: Create a conversation
echo -e "${YELLOW}Step 1: Creating conversation...${NC}"
CONVERSATION_RESPONSE=$(curl -s -X POST "$API_BASE/conversations" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Buy Crypto Test",
        "language": "en"
    }')

# Extract conversation ID
CONVERSATION_ID=$(echo "$CONVERSATION_RESPONSE" | jq -r '.id')

if [ "$CONVERSATION_ID" == "null" ] || [ -z "$CONVERSATION_ID" ]; then
    echo -e "${RED}✗ Failed to create conversation${NC}"
    echo "Response: $CONVERSATION_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Conversation created: $CONVERSATION_ID${NC}\n"

# Step 2: Send "buy crypto" message
echo -e "${YELLOW}Step 2: Sending 'buy crypto' message...${NC}"
MESSAGE_RESPONSE=$(curl -s -X POST "$API_BASE/conversations/$CONVERSATION_ID/messages" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "I want to buy crypto",
        "language": "en"
    }')

# Save full response for debugging
echo "$MESSAGE_RESPONSE" > /tmp/buy_intent_response.json
echo -e "${GREEN}✓ Full response saved to /tmp/buy_intent_response.json${NC}\n"

# Extract intent
INTENT=$(echo "$MESSAGE_RESPONSE" | jq -r '.routing.intent // "not_found"')
echo -e "Detected intent: ${YELLOW}$INTENT${NC}"

# Check if buy intent was detected
if [[ "$INTENT" =~ ^(buy|BUY)$ ]]; then
    echo -e "${GREEN}✓ Buy intent detected correctly!${NC}\n"
else
    echo -e "${RED}✗ Wrong intent detected: $INTENT (expected: buy)${NC}\n"
fi

# Extract agent message
AGENT_MESSAGE=$(echo "$MESSAGE_RESPONSE" | jq -r '.agent_message.content')

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Agent Response:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "$AGENT_MESSAGE"
echo -e "${YELLOW}========================================${NC}\n"

# Check for wallet in response
if echo "$AGENT_MESSAGE" | grep -q "$EXPECTED_WALLET"; then
    echo -e "${GREEN}✓✓✓ SUCCESS! Wallet found in response!${NC}"
    echo -e "${GREEN}    Wallet: $EXPECTED_WALLET${NC}\n"
elif echo "$AGENT_MESSAGE" | grep -q "0xc42c"; then
    echo -e "${GREEN}✓✓ Wallet prefix found (might be shortened)${NC}\n"
else
    echo -e "${RED}✗✗✗ FAILED: Wallet not found in response${NC}\n"

    # Check enrichment for wallet
    ENRICHMENT_WALLET=$(echo "$MESSAGE_RESPONSE" | jq -r '.enrichment.wallet_address // "not_found"')
    if [ "$ENRICHMENT_WALLET" != "not_found" ]; then
        echo -e "${YELLOW}⚠️  Wallet found in enrichment but not in content:${NC}"
        echo -e "    $ENRICHMENT_WALLET\n"
    fi
fi

# Check for supported assets
if echo "$AGENT_MESSAGE" | grep -qE "(ETH|USDC|BTC)"; then
    echo -e "${GREEN}✓ Supported assets mentioned (ETH/USDC/BTC)${NC}"
else
    echo -e "${RED}✗ Supported assets not mentioned${NC}"
fi

# Check for supported networks
if echo "$AGENT_MESSAGE" | grep -qE "(Base|Ethereum|Polygon|Arbitrum)"; then
    echo -e "${GREEN}✓ Supported networks mentioned${NC}"
else
    echo -e "${RED}✗ Supported networks not mentioned${NC}"
fi

# Check enrichment data
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Enrichment Data:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "$MESSAGE_RESPONSE" | jq '.enrichment'

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Complete!${NC}"
echo -e "${YELLOW}========================================${NC}"

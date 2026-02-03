#!/bin/bash
# Quick Test Script for Buy Workflow Fix
# Tests the buy crypto workflow with authenticated user token

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="https://testanvilcrypto.ddnsking.com/api/v1/conversations"
CONVERSATION_ID="57d4832f-c37e-4938-9b10-15457eae9c40"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJCcWNUWDB0QnNqR2lEZDh3TUZQd3dPQjlETjNESUZUd2JsSkF2TWh5cU5vIiwiZXhwIjoxNzcwMTI3NjY0fQ.8em5ZZmTmw2AQx8awq08l0ZM-UGSLOwgTQa_2M69QNU"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Buy Workflow Fix - Validation Test${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Test 1: Start buy flow
echo -e "${YELLOW}Test 1: Start buy flow${NC}"
echo "Message: 'Buy crypto'"
echo ""

response1=$(curl -s -X POST "$API_URL/$CONVERSATION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Buy crypto",
    "language": "en"
  }')

# Check if buy_workflow agent was used
if echo "$response1" | grep -q '"buy_workflow"'; then
  echo -e "${GREEN}✅ PASS: buy_workflow agent detected${NC}"
else
  echo -e "${RED}❌ FAIL: buy_workflow not found in agents_used${NC}"
fi

# Save response for inspection
echo "$response1" > /tmp/buy_test_step1.json
echo "Response saved to: /tmp/buy_test_step1.json"
echo ""

# Test 2: Select crypto
echo -e "${YELLOW}Test 2: Select crypto${NC}"
echo "Message: 'USDC'"
echo ""

sleep 2  # Brief delay between requests

response2=$(curl -s -X POST "$API_URL/$CONVERSATION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "USDC",
    "language": "en"
  }')

# Check if workflow continues (should ask for amount)
if echo "$response2" | grep -iq "amount\|much"; then
  echo -e "${GREEN}✅ PASS: Workflow proceeded to amount step${NC}"
else
  echo -e "${RED}❌ FAIL: Workflow did not ask for amount${NC}"
fi

echo "$response2" > /tmp/buy_test_step2.json
echo "Response saved to: /tmp/buy_test_step2.json"
echo ""

# Test 3: Provide amount
echo -e "${YELLOW}Test 3: Provide amount (CRITICAL TEST)${NC}"
echo "Message: '100'"
echo ""

sleep 2

response3=$(curl -s -X POST "$API_URL/$CONVERSATION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "100",
    "language": "en"
  }')

# THE CRITICAL CHECK: Should NOT loop back to "which crypto to buy?"
if echo "$response3" | grep -iq "which crypto\|which cryptocurrency"; then
  echo -e "${RED}❌ FAIL: Workflow LOOPED BACK (BUG NOT FIXED)${NC}"
  echo -e "${RED}   Response asks 'which crypto to buy?' again${NC}"
else
  echo -e "${GREEN}✅ PASS: Workflow did NOT loop back${NC}"
fi

# Check for confirmation or execute_data
if echo "$response3" | grep -iq "confirm\|confirm"; then
  echo -e "${GREEN}✅ PASS: Workflow shows confirmation${NC}"
else
  echo -e "${YELLOW}⚠️  WARNING: No confirmation detected${NC}"
fi

# Check for execute_data in response
if echo "$response3" | grep -q '"execute"'; then
  echo -e "${GREEN}✅ PASS: Execute data present in response${NC}"

  # Extract action_type if present
  action_type=$(echo "$response3" | jq -r '.execute.action_type' 2>/dev/null)
  if [ "$action_type" == "fund_wallet" ]; then
    echo -e "${GREEN}✅ PASS: action_type is 'fund_wallet'${NC}"
  fi
else
  echo -e "${YELLOW}⚠️  INFO: Execute data not yet present (may need confirmation)${NC}"
fi

echo "$response3" > /tmp/buy_test_step3.json
echo "Response saved to: /tmp/buy_test_step3.json"
echo ""

# Summary
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Full responses saved to:"
echo "  - /tmp/buy_test_step1.json (Buy crypto)"
echo "  - /tmp/buy_test_step2.json (USDC)"
echo "  - /tmp/buy_test_step3.json (100)"
echo ""
echo "To inspect responses:"
echo "  cat /tmp/buy_test_step3.json | jq '.'"
echo "  cat /tmp/buy_test_step3.json | jq '.routing.agents_used'"
echo "  cat /tmp/buy_test_step3.json | jq '.execute'"
echo ""
echo -e "${YELLOW}Expected Results:${NC}"
echo "  ✅ All 3 steps use buy_workflow agent"
echo "  ✅ Step 3 does NOT loop back to 'which crypto?'"
echo "  ✅ Step 3 shows confirmation or execute button"
echo ""

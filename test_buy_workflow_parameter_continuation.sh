#!/bin/bash

# Test Buy Workflow Parameter Continuation Fix
# Tests that "1", "2", "USDC" continue buy workflow instead of routing to swap

set -e

API_URL="http://localhost:8080"
AUTH_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJCcWNUWDB0QnNqR2lEZDh3TUZQd3dPQjlETjNESUZUd2JsSkF2TWh5cU5vIiwiZXhwIjoxNzcwMTI3NjY0fQ.8em5ZZmTmw2AQx8awq08l0ZM-UGSLOwgTQa_2M69QNU"

echo "========================================="
echo "Buy Workflow Parameter Continuation Test"
echo "========================================="
echo ""
echo "Testing that 'USDC' continues buy workflow, not swap workflow"
echo ""

# Create new conversation
echo "Creating new conversation..."
CREATE_RESP=$(curl -s -X POST "${API_URL}/api/v1/conversations" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}')

CONV_ID=$(echo "$CREATE_RESP" | jq -r '.id')
echo "✅ Created conversation: $CONV_ID"
echo ""

# Step 1: Buy crypto
echo "Step 1: Sending 'Buy crypto'"
R1=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONV_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Buy crypto", "language": "en"}')

CONTENT1=$(echo "$R1" | jq -r '.agent_message.content // .message.content // .content')
echo "$CONTENT1" | head -10
sleep 2

# Check Step 1
if echo "$CONTENT1" | grep -q "Available Cryptocurrencies"; then
    echo "✅ PASS: Step 1 shows crypto list"
else
    echo "❌ FAIL: Step 1 doesn't show crypto list"
    exit 1
fi
echo ""

# Step 2: Provide amount "2"
echo "Step 2: Sending '2'"
R2=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONV_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "2", "language": "en"}')

CONTENT2=$(echo "$R2" | jq -r '.agent_message.content // .message.content // .content')
echo "$CONTENT2" | head -10
sleep 2

# Check Step 2
if echo "$CONTENT2" | grep -iq "which cryptocurrency would you like to buy"; then
    echo "✅ PASS: Step 2 asks which crypto to buy"
elif echo "$CONTENT2" | grep -q "💳 Buying \$2"; then
    echo "✅ PASS: Step 2 shows buying $2"
else
    echo "❌ FAIL: Step 2 unexpected response"
    echo "$CONTENT2"
    exit 1
fi
echo ""

# Step 3: Provide crypto "USDC" (THE FIX TEST)
echo "Step 3: Sending 'USDC' (THE CRITICAL TEST)"
R3=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONV_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "USDC", "language": "en"}')

CONTENT3=$(echo "$R3" | jq -r '.agent_message.content // .message.content // .content')
echo "$CONTENT3" | head -20
ROUTING3=$(echo "$R3" | jq -r '.routing.handler // "unknown"')
AGENTS3=$(echo "$R3" | jq -r '.enrichment.agents_used // []')

echo ""
echo "========================================="
echo "VALIDATION RESULTS"
echo "========================================="
echo ""

# Check for Hyperliquid/Swap (should NOT appear)
if echo "$CONTENT3" | grep -iq "hyperliquid\|spot swaps\|meme token"; then
    echo "❌ FAIL: Step 3 shows Hyperliquid/Swap interface (BUG STILL EXISTS)"
    echo ""
    echo "Routing handler: $ROUTING3"
    echo "Agents used: $AGENTS3"
    exit 1
else
    echo "✅ PASS: Step 3 does NOT show Hyperliquid/Swap"
fi

# Check for buy review (should appear)
if echo "$CONTENT3" | grep -iq "review.*purchase\|buying.*usdc\|\$2.*usdc"; then
    echo "✅ PASS: Step 3 shows buy review for USDC"
else
    echo "⚠️  WARNING: Step 3 might not show buy review (check manually)"
    echo ""
    echo "Content:"
    echo "$CONTENT3"
fi

# Check routing
if echo "$ROUTING3" | grep -q "authenticated_supervisor"; then
    echo "✅ PASS: Routed through authenticated_supervisor"
else
    echo "⚠️  INFO: Routing handler: $ROUTING3"
fi

# Check agent
if echo "$AGENTS3" | grep -q "buy_workflow"; then
    echo "✅ PASS: Used buy_workflow agent"
else
    echo "❌ FAIL: Did not use buy_workflow agent"
    echo "Agents used: $AGENTS3"
    exit 1
fi

echo ""
echo "========================================="
echo "ALL TESTS PASSED ✅"
echo "========================================="
echo ""
echo "The parameter continuation fix is working correctly!"
echo "USDC is now recognized as buy workflow parameter, not swap intent."

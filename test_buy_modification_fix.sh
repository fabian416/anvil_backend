#!/bin/bash

# Test Buy Workflow Modification Fix
# Tests that "change to 200" modifies amount instead of cancelling

set -e

API_URL="http://localhost:8080"
CONVERSATION_ID="57d4832f-c37e-4938-9b10-15457eae9c40"
AUTH_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJCcWNUWDB0QnNqR2lEZDh3TUZQd3dPQjlETjNESUZUd2JsSkF2TWh5cU5vIiwiZXhwIjoxNzcwMTI3NjY0fQ.8em5ZZmTmw2AQx8awq08l0ZM-UGSLOwgTQa_2M69QNU"

echo "================================"
echo "Buy Workflow Modification Test"
echo "================================"
echo ""
echo "Testing that 'change to 200' modifies amount instead of cancelling"
echo ""

# Step 1: Buy crypto
echo "Step 1: Sending 'Buy crypto'"
RESPONSE1=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONVERSATION_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Buy crypto", "language": "en"}')

echo "$RESPONSE1" | jq -r '.content' > /tmp/buy_test_mod_step1.json
echo "✅ Step 1 complete"
echo ""

# Wait for processing
sleep 1

# Step 2: Select USDC
echo "Step 2: Sending 'USDC'"
RESPONSE2=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONVERSATION_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "USDC", "language": "en"}')

echo "$RESPONSE2" | jq -r '.content' > /tmp/buy_test_mod_step2.json
echo "✅ Step 2 complete"
echo ""

# Wait for processing
sleep 1

# Step 3: Enter amount 100
echo "Step 3: Sending '100'"
RESPONSE3=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONVERSATION_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "100", "language": "en"}')

echo "$RESPONSE3" | jq -r '.content' > /tmp/buy_test_mod_step3.json
STEP3_CONTENT=$(echo "$RESPONSE3" | jq -r '.content')
echo "✅ Step 3 complete"
echo ""

# Check that Step 3 shows $100 review
if echo "$STEP3_CONTENT" | grep -q "\$100"; then
    echo "✅ PASS: Step 3 shows \$100 review"
else
    echo "❌ FAIL: Step 3 does not show \$100 review"
    exit 1
fi

# Wait for processing
sleep 1

# Step 4: Modify amount to 200 (THE FIX TEST)
echo "Step 4: Sending 'change to 200'"
RESPONSE4=$(curl -s -X POST "${API_URL}/api/v1/conversations/${CONVERSATION_ID}/messages" \
  -H "Authorization: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content": "change to 200", "language": "en"}')

echo "$RESPONSE4" | jq -r '.content' > /tmp/buy_test_mod_step4.json
STEP4_CONTENT=$(echo "$RESPONSE4" | jq -r '.content')
echo "✅ Step 4 complete"
echo ""

# Validation: Check that modification worked
echo "================================"
echo "VALIDATION RESULTS"
echo "================================"
echo ""

# Check for cancellation (should NOT happen)
if echo "$STEP4_CONTENT" | grep -iq "cancel"; then
    echo "❌ FAIL: Step 4 shows cancellation message (BUG STILL EXISTS)"
    echo ""
    echo "Response content:"
    echo "$STEP4_CONTENT"
    exit 1
else
    echo "✅ PASS: Step 4 did NOT cancel"
fi

# Check that amount was updated to $200
if echo "$STEP4_CONTENT" | grep -q "\$200"; then
    echo "✅ PASS: Step 4 shows updated amount \$200"
else
    echo "❌ FAIL: Step 4 does not show \$200"
    echo ""
    echo "Response content:"
    echo "$STEP4_CONTENT"
    exit 1
fi

# Check that review is shown again
if echo "$STEP4_CONTENT" | grep -iq "review"; then
    echo "✅ PASS: Step 4 shows review confirmation"
else
    echo "⚠️  WARNING: Step 4 may not show review (check manually)"
fi

echo ""
echo "================================"
echo "ALL TESTS PASSED ✅"
echo "================================"
echo ""
echo "The modification fix is working correctly!"
echo ""
echo "Saved responses to:"
echo "  /tmp/buy_test_mod_step1.json"
echo "  /tmp/buy_test_mod_step2.json"
echo "  /tmp/buy_test_mod_step3.json"
echo "  /tmp/buy_test_mod_step4.json"

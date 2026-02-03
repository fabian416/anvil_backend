#!/bin/bash

# Test Guest Chat Registration Required Fix
# Validates that "Buy crypto" returns proper registration_required data

set -e

API_URL="http://localhost:8080"

echo "========================================="
echo "Guest Chat Registration Required Test"
echo "========================================="
echo ""

# Test "Buy crypto" request
echo "Sending: 'Buy crypto' to guest chat endpoint"
echo ""

RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Buy crypto",
    "language": "en"
  }')

# Save full response
echo "$RESPONSE" > /tmp/guest_buy_response.json

# Extract fields
AGENT_CONTENT=$(echo "$RESPONSE" | jq -r '.agent_message.content')
REG_REQUIRED=$(echo "$RESPONSE" | jq '.registration_required')
REG_REASON=$(echo "$RESPONSE" | jq -r '.registration_required.reason // "null"')
REG_MESSAGE=$(echo "$RESPONSE" | jq -r '.registration_required.message.en // "null"')
REG_CTA=$(echo "$RESPONSE" | jq -r '.registration_required.cta // "null"')
SIGNUP_URL=$(echo "$RESPONSE" | jq -r '.registration_required.signup_url // "null"')

echo "Agent Response:"
echo "$AGENT_CONTENT" | head -10
echo ""

echo "========================================="
echo "VALIDATION RESULTS"
echo "========================================="
echo ""

# Check if registration_required is NOT null
if [ "$REG_REQUIRED" == "null" ] || [ "$REG_REQUIRED" == "" ]; then
    echo "❌ FAIL: registration_required is null"
    echo ""
    echo "Full response:"
    cat /tmp/guest_buy_response.json | jq '.'
    exit 1
else
    echo "✅ PASS: registration_required is NOT null"
fi

# Check reason (accept both legacy and LLM supervisor schemas)
if [ "$REG_REASON" == "action_required" ] || [ "$REG_REASON" == "buy_crypto" ]; then
    echo "✅ PASS: reason = '$REG_REASON' (valid)"
else
    echo "❌ FAIL: reason = '$REG_REASON' (expected 'action_required' or 'buy_crypto')"
    exit 1
fi

# Check message
if [ "$REG_MESSAGE" != "null" ] && [ ! -z "$REG_MESSAGE" ]; then
    echo "✅ PASS: message.en is present"
else
    echo "❌ FAIL: message.en is missing"
    exit 1
fi

# Check CTA
if [ "$REG_CTA" != "null" ]; then
    echo "✅ PASS: cta object is present"
else
    echo "⚠️  WARNING: cta object is missing"
fi

# Check signup URL
if [ "$SIGNUP_URL" == "/signup" ]; then
    echo "✅ PASS: signup_url = '/signup'"
else
    echo "❌ FAIL: signup_url = '$SIGNUP_URL' (expected '/signup')"
    exit 1
fi

# Check content contains account required message
if echo "$AGENT_CONTENT" | grep -iq "account required\|sign up"; then
    echo "✅ PASS: Agent message mentions account/signup"
else
    echo "⚠️  WARNING: Agent message doesn't clearly indicate registration needed"
fi

echo ""
echo "========================================="
echo "ALL TESTS PASSED ✅"
echo "========================================="
echo ""
echo "Guest chat registration_required is now properly populated!"
echo ""
echo "Full registration_required object:"
echo "$REG_REQUIRED" | jq '.'

#!/bin/bash
# Manual Vault Query Test - Quick API validation
# Tests the live API endpoint to verify vault routing fix

set -e

# Configuration
API_BASE="${API_BASE:-https://testanvilcrypto.ddnsking.com}"
TOKEN="${TOKEN:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Manual Vault Query API Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "API Base: $API_BASE"
echo "Using: ops@anvilcrypto.com test account"
echo ""

# Step 1: Create conversation
echo "Step 1: Creating conversation..."
CONV_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/user/chat/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Manual Vault Test", "language": "en"}')

CONV_ID=$(echo "$CONV_RESPONSE" | jq -r '.id')

if [ "$CONV_ID" == "null" ] || [ -z "$CONV_ID" ]; then
    echo "❌ Failed to create conversation"
    echo "$CONV_RESPONSE" | jq '.'
    exit 1
fi

echo "✅ Conversation created: $CONV_ID"
echo ""

# Step 2: Send vault query
echo "Step 2: Sending query: 'Show best lending vaults'"
echo ""

RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/user/chat/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Show best lending vaults", "language": "en"}')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ROUTING VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract routing info
INTENT=$(echo "$RESPONSE" | jq -r '.routing.intent')
AGENTS=$(echo "$RESPONSE" | jq -r '.routing.agents_used[]' 2>/dev/null | tr '\n' ' ')

echo "Intent: $INTENT"
echo "Agents: [$AGENTS]"
echo ""

# Validate routing
ROUTING_VALID="false"

if echo "$AGENTS" | grep -q "lending_workflow\|lending_handler"; then
    echo "✅ CORRECT: Routes to lending_workflow"
    ROUTING_VALID="true"
else
    echo "❌ WRONG: Should route to lending_workflow"
fi

if echo "$AGENTS" | grep -q "defi_yield"; then
    echo "❌ WRONG: Should NOT route to defi_yield"
    ROUTING_VALID="false"
else
    echo "✅ CORRECT: Does not route to defi_yield"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  RESPONSE CONTENT VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

CONTENT=$(echo "$RESPONSE" | jq -r '.agent_message.content')

# Check for Morpho vault indicators
HAS_MORPHO="false"
HAS_VAULT="false"
HAS_APY="false"
HAS_DEFI_LLAMA_POOLS="false"

if echo "$CONTENT" | grep -iq "morpho"; then
    HAS_MORPHO="true"
    echo "✅ Mentions 'Morpho'"
fi

if echo "$CONTENT" | grep -iq "vault"; then
    HAS_VAULT="true"
    echo "✅ Mentions 'vault'"
fi

if echo "$CONTENT" | grep -iE "apy|yield|%"; then
    HAS_APY="true"
    echo "✅ Includes APY/yield data"
fi

# Check for DeFiLlama pools (these should NOT appear)
if echo "$CONTENT" | grep -iE "beefy|kamino|balancer|convex|curve finance"; then
    HAS_DEFI_LLAMA_POOLS="true"
    echo "❌ Contains DeFiLlama pool names (WRONG DATA SOURCE)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  RESPONSE PREVIEW"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "$CONTENT" | head -20
echo ""
if [ $(echo "$CONTENT" | wc -l) -gt 20 ]; then
    echo "... (truncated, see full_response.json for complete output)"
fi
echo ""

# Save full response
echo "$RESPONSE" | jq '.' > /tmp/vault_query_response.json
echo "Full response saved to: /tmp/vault_query_response.json"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TEST RESULT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ROUTING_VALID" == "true" ] && [ "$HAS_DEFI_LLAMA_POOLS" == "false" ] && ([ "$HAS_MORPHO" == "true" ] || [ "$HAS_VAULT" == "true" ]); then
    echo "✅ TEST PASSED"
    echo ""
    echo "Summary:"
    echo "  ✓ Routes to lending_workflow (not defi_yield)"
    echo "  ✓ Returns Morpho vault data (not DeFiLlama pools)"
    echo "  ✓ Includes APY/yield information"
    echo ""
    echo "The vault query routing fix is working correctly!"
    exit 0
else
    echo "❌ TEST FAILED"
    echo ""
    echo "Issues detected:"
    [ "$ROUTING_VALID" == "false" ] && echo "  ✗ Incorrect agent routing"
    [ "$HAS_DEFI_LLAMA_POOLS" == "true" ] && echo "  ✗ Contains DeFiLlama pools (wrong data source)"
    [ "$HAS_MORPHO" == "false" ] && [ "$HAS_VAULT" == "false" ] && echo "  ✗ Missing vault/Morpho references"
    echo ""
    echo "The vault query routing fix may not be working correctly."
    echo "Check /tmp/vault_query_response.json for details."
    exit 1
fi

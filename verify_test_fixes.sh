#!/bin/bash
# Test Fixes Verification Script
# Verifies that all targeted test fixes are working correctly

set -e  # Exit on error

echo "=============================================="
echo "Test Fixes Verification"
echo "=============================================="
echo ""

# Activate virtual environment
source .venv/bin/activate

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_path="$2"

    echo "Testing: $test_name"
    echo "----------------------------------------"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if pytest "$test_path" -v --tb=short -q 2>&1 | grep -q "passed"; then
        echo "✅ PASSED"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "❌ FAILED"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo ""
}

# Test 1: Hunter LSTM Price Prediction
run_test "Hunter LSTM Price Prediction" \
    "tests/integration/hunter/test_price_prediction.py::TestPricePredictionIntegration::test_prediction_without_training"

# Test 2: MCP Server Flags (all 21 tests)
run_test "MCP Server Flags (21 tests)" \
    "tests/integration/mcp/test_mcp_flags.py"

# Test 3: MCP Server Retry (all 11 tests)
run_test "MCP Server Retry (11 tests)" \
    "tests/integration/mcp/test_mcp_server_retry.py"

# Summary
echo "=============================================="
echo "Summary"
echo "=============================================="
echo "Total test suites: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ All targeted test fixes are working!"
    exit 0
else
    echo "❌ Some tests are still failing"
    exit 1
fi

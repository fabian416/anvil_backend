#!/bin/bash
#
# P0 Fix Verification Script
#
# Runs all vault pattern tests to verify the fix is working correctly.
#

echo "================================================================================"
echo "P0 FIX VERIFICATION: Vault Pattern Intent Routing"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "${YELLOW}Running P0 Fix Verification...${NC}"
echo ""

# Test 1: P0 Fix Verification (exact query from problem statement)
echo "Test 1: P0 Fix Verification (exact query)"
echo "----------------------------------------"
python3 test_p0_fix.py
TEST1_EXIT=$?
echo ""

# Test 2: Basic Vault Patterns (16 test cases)
echo "Test 2: Basic Vault Patterns (16 test cases)"
echo "--------------------------------------------"
python3 test_vault_patterns.py | tail -5
TEST2_EXIT=$?
echo ""

# Test 3: Comprehensive Vault Patterns (38 test cases)
echo "Test 3: Comprehensive Vault Patterns (38 test cases)"
echo "----------------------------------------------------"
python3 test_vault_patterns_comprehensive.py | tail -5
TEST3_EXIT=$?
echo ""

# Summary
echo "================================================================================"
echo "VERIFICATION SUMMARY"
echo "================================================================================"

if [ $TEST1_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Test 1: P0 Fix Verification - PASSED"
else
    echo -e "${RED}✗${NC} Test 1: P0 Fix Verification - FAILED"
fi

if [ $TEST2_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Test 2: Basic Vault Patterns - PASSED"
else
    echo -e "${RED}✗${NC} Test 2: Basic Vault Patterns - FAILED"
fi

if [ $TEST3_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Test 3: Comprehensive Vault Patterns - PASSED"
else
    echo -e "${RED}✗${NC} Test 3: Comprehensive Vault Patterns - FAILED"
fi

echo "================================================================================"

# Exit with failure if any test failed
if [ $TEST1_EXIT -ne 0 ] || [ $TEST2_EXIT -ne 0 ] || [ $TEST3_EXIT -ne 0 ]; then
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed! P0 fix is working correctly.${NC}"
    exit 0
fi

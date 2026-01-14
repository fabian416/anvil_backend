#!/bin/bash
# Test runner for knowledge injection integration tests
#
# Usage:
#   ./test_knowledge_injection_runner.sh          # Run all tests
#   ./test_knowledge_injection_runner.sh unit     # Run only unit tests
#   ./test_knowledge_injection_runner.sh api      # Run only API tests
#   ./test_knowledge_injection_runner.sh coverage # Run with coverage report

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Knowledge Injection Integration Tests${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get test type from argument (default: all)
TEST_TYPE=${1:-all}

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated. Activating...${NC}"
    source .venv/bin/activate || source env/bin/activate
fi

# Verify knowledge base exists
if [ ! -d "anvil_knowledge/features" ]; then
    echo -e "${RED}✗ Error: Knowledge base directory not found!${NC}"
    echo -e "${YELLOW}  Expected: anvil_knowledge/features/${NC}"
    echo -e "${YELLOW}  Please ensure knowledge base JSON files are present.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Knowledge base found${NC}"

# Count JSON files
JSON_COUNT=$(find anvil_knowledge/features -name "*.json" | wc -l)
echo -e "${GREEN}✓ Found ${JSON_COUNT} knowledge base files${NC}"
echo ""

# Run tests based on type
case "$TEST_TYPE" in
    unit)
        echo -e "${YELLOW}Running unit tests only...${NC}"
        pytest tests/integration/chat/test_knowledge_injection.py -v --tb=short
        ;;

    api)
        echo -e "${YELLOW}Running API integration tests only...${NC}"
        pytest tests/integration/chat/test_knowledge_injection_api.py -v --tb=short
        ;;

    coverage)
        echo -e "${YELLOW}Running all tests with coverage...${NC}"
        pytest tests/integration/chat/test_knowledge_injection*.py \
            --cov=src/app/application/chat/services/knowledge_injector \
            --cov-report=html \
            --cov-report=term \
            -v

        echo ""
        echo -e "${GREEN}✓ Coverage report generated in htmlcov/index.html${NC}"
        ;;

    all|*)
        echo -e "${YELLOW}Running all knowledge injection tests...${NC}"
        echo ""

        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  1. Unit Tests (KnowledgeInjector Class)${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        pytest tests/integration/chat/test_knowledge_injection.py -v --tb=short

        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  2. API Integration Tests (Authenticated & Guest)${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        pytest tests/integration/chat/test_knowledge_injection_api.py -v --tb=short
        ;;
esac

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✓ All tests passed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ✗ Some tests failed!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi

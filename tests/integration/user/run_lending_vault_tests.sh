#!/bin/bash
# Quick runner for Lending Vault Integration Tests
# Tests the complete fix for vault query routing (commits 2351206f, 4ccf3009, 1bc72e1d)

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Lending Vault Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "Run: source .venv/bin/activate"
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "⚠️  pytest not found"
    echo "Run: uv pip install -e '.[test]'"
    exit 1
fi

# Parse arguments
TEST_MODE="${1:-all}"

case "$TEST_MODE" in
    "all")
        echo "Running all 8 lending vault tests..."
        pytest tests/integration/user/test_lending_vaults.py \
            -v \
            -m integration \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    "quick")
        echo "Running quick validation (4 core tests)..."
        pytest tests/integration/user/test_lending_vaults.py \
            -v \
            -m integration \
            --tb=short \
            -W ignore::DeprecationWarning \
            -k "test_user_lending_vault_discovery_best_vaults or \
                test_user_lending_vault_discovery_top_vaults or \
                test_user_lending_vault_discovery_best_morpho_vaults or \
                test_user_lending_vault_vs_yield_routing"
        ;;

    "routing")
        echo "Running routing distinction test (THE critical test)..."
        pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_vs_yield_routing \
            -v \
            -s \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    "discovery")
        echo "Running discovery tests..."
        pytest tests/integration/user/test_lending_vaults.py \
            -v \
            -m integration \
            --tb=short \
            -W ignore::DeprecationWarning \
            -k "discovery"
        ;;

    "workflow")
        echo "Running multi-step workflow test..."
        pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_deposit_workflow \
            -v \
            -s \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    "multilang")
        echo "Running multi-language test..."
        pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_multi_language_spanish \
            -v \
            -s \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    "format")
        echo "Running response format validation..."
        pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_response_format \
            -v \
            -s \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    "comparison")
        echo "Running vault comparison test..."
        pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_comparison \
            -v \
            -s \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    "llm")
        echo "Running with LLM validation (slower)..."
        pytest tests/integration/user/test_lending_vaults.py \
            -v \
            -m llm_validation \
            -s \
            --tb=short \
            -W ignore::DeprecationWarning
        ;;

    *)
        echo "Usage: $0 [MODE]"
        echo ""
        echo "Available modes:"
        echo "  all         - Run all 8 tests (default)"
        echo "  quick       - Run 4 core tests only"
        echo "  routing     - Run THE critical routing distinction test (005)"
        echo "  discovery   - Run vault discovery tests (001-003)"
        echo "  workflow    - Run multi-step workflow test (007)"
        echo "  multilang   - Run Spanish language test (006)"
        echo "  format      - Run response format validation (008)"
        echo "  comparison  - Run vault comparison test (004)"
        echo "  llm         - Run with LLM validation enabled"
        echo ""
        echo "Examples:"
        echo "  $0 all          # Run all tests"
        echo "  $0 quick        # Quick validation"
        echo "  $0 routing      # Test the critical fix"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Tests completed!"
echo ""
echo "Expected routing for vault queries:"
echo "  - Intent: LENDING or SUPERVISOR_WORKFLOW"
echo "  - Agents: ['lending_workflow'] or ['lending_handler']"
echo "  - NOT: ['defi_yield', 'risk_analyzer']"
echo ""
echo "CSV reports: tests/integration/reports/user_lending_vaults_*.csv"
echo ""

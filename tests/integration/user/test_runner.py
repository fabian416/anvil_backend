#!/usr/bin/env python3
"""
User Integration Test Runner.

Runs comprehensive tests for all authenticated user workflows and agents,
generating detailed CSV reports.

Usage:
    # Run all tests
    python -m pytest tests/integration/user/test_runner.py -v

    # Run specific category
    python -m pytest tests/integration/user/test_runner.py -v -k "swap"

    # Run with external server
    TEST_BASE_URL=http://localhost:8080 python -m pytest tests/integration/user/test_runner.py -v
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, UTC
from typing import Any

from httpx import AsyncClient

# Handle both module and standalone execution
try:
    from .conftest import (
        TokenManager,
        TokenInfo,
        CSVReporter,
        TestResult,
        send_message,
        parse_response,
        create_test_result,
        OUTPUT_DIR,
    )
except ImportError:
    # Standalone execution
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from conftest import (
        TokenManager,
        TokenInfo,
        CSVReporter,
        TestResult,
        send_message,
        parse_response,
        create_test_result,
        OUTPUT_DIR,
    )


# ============================================================
# Test Case Definitions
# ============================================================

WORKFLOW_TESTS = [
    # ========== SWAP WORKFLOW ==========
    {
        "test_id": "swap_001",
        "input": "swap 1 ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap",
        "language": "en",
    },
    {
        "test_id": "swap_002",
        "input": "exchange 100 USDC for ETH",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap",
        "language": "en",
    },
    {
        "test_id": "swap_003",
        "input": "convert 0.5 ETH to DAI",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap",
        "language": "en",
    },
    {
        "test_id": "swap_004",
        "input": "swap 500 USDC to WBTC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap",
        "language": "en",
    },
    {
        "test_id": "swap_es_001",
        "input": "quiero cambiar 50 USDC por ETH",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_multilang",
        "language": "es",
    },
    {
        "test_id": "swap_zh_001",
        "input": "我想交换 1 ETH 到 USDC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_multilang",
        "language": "zh",
    },
    # ========== LENDING WORKFLOW ==========
    {
        "test_id": "lend_001",
        "input": "deposit 1000 USDC",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending",
        "language": "en",
    },
    {
        "test_id": "lend_002",
        "input": "lend 0.5 ETH",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending",
        "language": "en",
    },
    {
        "test_id": "lend_003",
        "input": "earn yield on 500 DAI",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending",
        "language": "en",
    },
    {
        "test_id": "lend_004",
        "input": "deposit into morpho",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending",
        "language": "en",
    },
    {
        "test_id": "lend_es_001",
        "input": "depositar 1000 USDC en morpho",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_multilang",
        "language": "es",
    },
    {
        "test_id": "lend_pt_001",
        "input": "depositar 500 USDC",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_multilang",
        "language": "pt",
    },
    # ========== TRANSFER WORKFLOW ==========
    {
        "test_id": "transfer_001",
        "input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer",
        "language": "en",
    },
    {
        "test_id": "transfer_002",
        "input": "transfer 0.5 ETH to my friend",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer",
        "language": "en",
    },
    {
        "test_id": "transfer_003",
        "input": "send ETH",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer",
        "language": "en",
    },
    {
        "test_id": "transfer_004",
        "input": "send 50 USDC",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer",
        "language": "en",
    },
    {
        "test_id": "transfer_es_001",
        "input": "enviar 50 USDC a 0x123456789abcdef0123456789abcdef012345678",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_multilang",
        "language": "es",
    },
    # ========== BUY WORKFLOW ==========
    {
        "test_id": "buy_001",
        "input": "buy $100 of ETH",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy",
        "language": "en",
    },
    {
        "test_id": "buy_002",
        "input": "purchase 50 dollars of USDC",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy",
        "language": "en",
    },
    {
        "test_id": "buy_003",
        "input": "buy crypto",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy",
        "language": "en",
    },
    {
        "test_id": "buy_004",
        "input": "buy BTC with card",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy",
        "language": "en",
    },
    {
        "test_id": "buy_es_001",
        "input": "comprar $200 de BTC",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_multilang",
        "language": "es",
    },
    {
        "test_id": "buy_pt_001",
        "input": "comprar $100 de ETH",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_multilang",
        "language": "pt",
    },
    # ========== MONEY MARKET WORKFLOW ==========
    {
        "test_id": "mm_001",
        "input": "compare USDC rates",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market",
        "language": "en",
    },
    {
        "test_id": "mm_002",
        "input": "best lending rates for ETH",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market",
        "language": "en",
    },
    {
        "test_id": "mm_003",
        "input": "where should I deposit DAI",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market",
        "language": "en",
    },
    {
        "test_id": "mm_004",
        "input": "compare aave compound morpho",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market",
        "language": "en",
    },
    {
        "test_id": "mm_es_001",
        "input": "comparar tasas de USDC",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_multilang",
        "language": "es",
    },
    {
        "test_id": "mm_pt_001",
        "input": "comparar taxas de USDC",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_multilang",
        "language": "pt",
    },
]

AGENT_TESTS = [
    # ========== HUNTER AI ==========
    {
        "test_id": "hunter_001",
        "input": "what is the price of ETH",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
        "language": "en",
    },
    {
        "test_id": "hunter_002",
        "input": "BTC price prediction",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_price",
        "language": "en",
    },
    {
        "test_id": "hunter_003",
        "input": "ethereum sentiment",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_sentiment",
        "language": "en",
    },
    {
        "test_id": "hunter_004",
        "input": "BTC trading signals",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_signals",
        "language": "en",
    },
    {
        "test_id": "hunter_005",
        "input": "crypto market news",
        "expected_agent": "hunter_ai",
        "category": "agent",
        "subcategory": "hunter_news",
        "language": "en",
    },
    # ========== DEFI YIELD ==========
    {
        "test_id": "yield_001",
        "input": "best yield for USDC",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
        "language": "en",
    },
    {
        "test_id": "yield_002",
        "input": "highest APY stablecoins",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
        "language": "en",
    },
    {
        "test_id": "yield_003",
        "input": "yield farming opportunities",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
        "language": "en",
    },
    # ========== PORTFOLIO ==========
    {
        "test_id": "portfolio_001",
        "input": "my portfolio",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
        "language": "en",
    },
    {
        "test_id": "portfolio_002",
        "input": "show my holdings",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
        "language": "en",
    },
    {
        "test_id": "portfolio_003",
        "input": "portfolio breakdown",
        "expected_agent": "portfolio",
        "category": "agent",
        "subcategory": "portfolio",
        "language": "en",
    },
    # ========== WALLET ==========
    {
        "test_id": "wallet_001",
        "input": "my wallets",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
        "language": "en",
    },
    {
        "test_id": "wallet_002",
        "input": "show my wallet balance",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
        "language": "en",
    },
    {
        "test_id": "wallet_003",
        "input": "what tokens do I have",
        "expected_agent": "wallet",
        "category": "agent",
        "subcategory": "wallet",
        "language": "en",
    },
    # ========== TRANSACTION HISTORY ==========
    {
        "test_id": "tx_001",
        "input": "transaction history",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
        "language": "en",
    },
    {
        "test_id": "tx_002",
        "input": "recent activity",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
        "language": "en",
    },
    {
        "test_id": "tx_003",
        "input": "show my transactions",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "transactions",
        "language": "en",
    },
    # ========== RESEARCH ==========
    {
        "test_id": "research_001",
        "input": "tell me about Aave protocol",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
        "language": "en",
    },
    {
        "test_id": "research_002",
        "input": "what is Uniswap",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
        "language": "en",
    },
    {
        "test_id": "research_003",
        "input": "explain DeFi lending",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
        "language": "en",
    },
    # ========== RISK ANALYZER ==========
    {
        "test_id": "risk_001",
        "input": "analyze risk of Aave",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
        "language": "en",
    },
    {
        "test_id": "risk_002",
        "input": "is Compound safe",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
        "language": "en",
    },
]

MULTISTEP_TESTS = [
    # ========== SWAP CONFIRMATION FLOW ==========
    {
        "test_id": "swap_confirm_001",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multistep",
        "subcategory": "swap_confirm",
        "language": "en",
    },
    {
        "test_id": "swap_cancel_001",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "cancel", "expect_cancelled": True},
        ],
        "category": "multistep",
        "subcategory": "swap_cancel",
        "language": "en",
    },
    {
        "test_id": "swap_modify_001",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "change to 2 ETH", "expect_agent": "swap_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multistep",
        "subcategory": "swap_modify",
        "language": "en",
    },
    # ========== LENDING CONFIRMATION FLOW ==========
    {
        "test_id": "lend_confirm_001",
        "steps": [
            {"input": "deposit 1000 USDC", "expect_agent": "lending_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multistep",
        "subcategory": "lending_confirm",
        "language": "en",
    },
    {
        "test_id": "lend_cancel_001",
        "steps": [
            {"input": "deposit 1000 USDC", "expect_agent": "lending_workflow"},
            {"input": "cancel", "expect_cancelled": True},
        ],
        "category": "multistep",
        "subcategory": "lending_cancel",
        "language": "en",
    },
    # ========== MONEY MARKET FLOW ==========
    {
        "test_id": "mm_select_001",
        "steps": [
            {"input": "compare USDC rates", "expect_agent": "money_market_workflow"},
            {"input": "morpho", "expect_agent": "money_market_workflow"},
        ],
        "category": "multistep",
        "subcategory": "money_market_flow",
        "language": "en",
    },
]


# ============================================================
# Test Classes
# ============================================================


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserWorkflows:
    """Tests for authenticated user workflow agents."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter

    @pytest.mark.parametrize("test_case", WORKFLOW_TESTS, ids=lambda t: t["test_id"])
    async def test_workflow(self, test_case: dict[str, Any]):
        """Test workflow routing and response."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
            test_case.get("language", "en"),
        )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )

        self.reporter.add_result(result)

        # Assert basic success
        assert not response_data.get("error"), f"Request failed: {response_data}"

        # Check agent routing
        parsed = parse_response(response_data)
        expected_agent = test_case["expected_agent"]
        actual_agents = parsed.get("agents_used", "")

        assert expected_agent in actual_agents or any(
            kw in parsed.get("content", "").lower()
            for kw in ["swap", "deposit", "lend", "send", "buy", "compare", "rate"]
        ), f"Expected {expected_agent} but got {actual_agents}"


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserAgents:
    """Tests for authenticated user agent queries."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter

    @pytest.mark.parametrize("test_case", AGENT_TESTS, ids=lambda t: t["test_id"])
    async def test_agent(self, test_case: dict[str, Any]):
        """Test agent routing and response."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
            test_case.get("language", "en"),
        )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )

        self.reporter.add_result(result)

        # Assert basic success
        assert not response_data.get("error"), f"Request failed: {response_data}"

        # Check response has content
        parsed = parse_response(response_data)
        assert len(parsed.get("content", "")) > 20, "Response too short"


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserMultiStep:
    """Tests for multi-step conversation flows."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter

    @pytest.mark.parametrize("test_case", MULTISTEP_TESTS, ids=lambda t: t["test_id"])
    async def test_multistep_flow(self, test_case: dict[str, Any]):
        """Test multi-step conversation flow."""
        # Create fresh conversation for each multi-step test
        response = await self.client.post(
            "/api/v1/conversations",
            json={"title": f"MultiStep Test {test_case['test_id']}"},
        )
        assert response.status_code in (200, 201)
        conversation_id = response.json().get("id")

        steps = test_case["steps"]
        total_steps = len(steps)

        for step_num, step in enumerate(steps, 1):
            response_data, response_time_ms = await send_message(
                self.client,
                conversation_id,
                step["input"],
                test_case.get("language", "en"),
            )

            # Create result for this step
            step_test_case = {
                **test_case,
                "input": step["input"],
                "expected_agent": step.get("expect_agent", ""),
                "is_multi_step": True,
                "step_number": step_num,
                "total_steps": total_steps,
                "requires_execute": step.get("expect_execute", False),
            }

            result = create_test_result(
                test_id=f"{test_case['test_id']}_step{step_num}",
                test_case=step_test_case,
                response_data=response_data,
                response_time_ms=response_time_ms,
                conversation_id=conversation_id,
            )

            self.reporter.add_result(result)

            # Validate step expectations
            assert not response_data.get("error"), (
                f"Step {step_num} failed: {response_data}"
            )

            parsed = parse_response(response_data)

            if step.get("expect_execute"):
                # Final step should have execute data
                assert parsed.get("execute_data"), (
                    f"Step {step_num} should have execute_data"
                )

            if step.get("expect_cancelled"):
                # Cancelled flow should indicate cancellation
                assert any(
                    word in parsed.get("content", "").lower()
                    for word in ["cancel", "cancelled", "abort", "exit"]
                ), f"Step {step_num} should indicate cancellation"

            # Small delay between steps
            await asyncio.sleep(0.5)


# ============================================================
# Standalone Runner
# ============================================================


async def run_all_tests():
    """Run all tests and generate reports."""
    import httpx
    import os

    base_url = os.environ.get("TEST_BASE_URL", "http://localhost:8080")
    reporter = CSVReporter(category="all_workflows")

    # Get token
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        token_info = await TokenManager.get_token(client)
        client.headers["Authorization"] = token_info.authorization_header

        # Create conversation
        response = await client.post(
            "/api/v1/conversations",
            json={"title": "Comprehensive Test Run"},
        )

        if response.status_code not in (200, 201):
            print(f"Failed to create conversation: {response.text}")
            return

        conversation_id = response.json().get("id")
        print(f"Using conversation: {conversation_id}")

        # Run workflow tests
        all_tests = WORKFLOW_TESTS + AGENT_TESTS

        for i, test_case in enumerate(all_tests, 1):
            print(f"\n[{i}/{len(all_tests)}] Testing: {test_case['input'][:50]}...")

            try:
                response_data, response_time_ms = await send_message(
                    client,
                    conversation_id,
                    test_case["input"],
                    test_case.get("language", "en"),
                )

                result = create_test_result(
                    test_id=test_case["test_id"],
                    test_case=test_case,
                    response_data=response_data,
                    response_time_ms=response_time_ms,
                    conversation_id=conversation_id,
                )

                reporter.add_result(result)

                print(f"    Status: {result.status}")
                print(f"    Agents: {result.actual_agents}")
                print(f"    Time: {result.response_time_ms}ms")

            except Exception as e:
                print(f"    Error: {e}")
                result = TestResult(
                    test_id=test_case["test_id"],
                    category=test_case.get("category", ""),
                    subcategory=test_case.get("subcategory", ""),
                    input=test_case["input"],
                    status="ERROR",
                    error_message=str(e),
                )
                reporter.add_result(result)

            # Small delay
            await asyncio.sleep(1)

    # Write reports
    csv_path = reporter.write_csv()
    summary_path = reporter.write_summary()
    reporter.print_summary()

    print(f"\nCSV output: {csv_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

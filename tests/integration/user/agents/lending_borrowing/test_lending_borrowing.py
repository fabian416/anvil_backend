"""
Lending Borrowing Agent Tests for Authenticated Users.

Tests health factor queries, position management, and liquidation risk.
This agent handles leverage optimization and collateral management.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ...conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
    create_conversation,
)


LENDING_BORROWING_TESTS = [
    # Health Factor
    {
        "test_id": "lending_health_001",
        "input": "what's my health factor",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_health",
    },
    {
        "test_id": "lending_health_002",
        "input": "check my health factor on Aave",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_health",
    },
    {
        "test_id": "lending_health_003",
        "input": "am I at risk of liquidation",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_health",
    },
    # Positions
    {
        "test_id": "lending_position_001",
        "input": "show my lending positions",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_position",
    },
    {
        "test_id": "lending_position_002",
        "input": "what have I borrowed",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_position",
    },
    {
        "test_id": "lending_position_003",
        "input": "my collateral on Aave",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_position",
    },
    # Liquidation Risk
    {
        "test_id": "lending_liquidation_001",
        "input": "liquidation risk analysis",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_liquidation",
    },
    {
        "test_id": "lending_liquidation_002",
        "input": "how much can I safely borrow",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_liquidation",
    },
    # Leverage Optimization
    {
        "test_id": "lending_leverage_001",
        "input": "optimize my leverage",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_leverage",
    },
    {
        "test_id": "lending_leverage_002",
        "input": "best borrowing strategy",
        "expected_agent": "lending_borrowing",
        "category": "agent",
        "subcategory": "lending_leverage",
    },
]


@pytest.fixture(scope="module")
def lending_borrowing_reporter() -> CSVReporter:
    """Create CSV reporter for lending borrowing agent tests."""
    reporter = CSVReporter(category="agent_lending_borrowing")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestLendingBorrowingAgent:
    """Test Lending Borrowing agent functionality."""

    async def test_lending_borrowing_queries(
        self, authenticated_client, lending_borrowing_reporter
    ):
        """Test lending/borrowing position queries."""
        import asyncio

        for test_case in LENDING_BORROWING_TESTS:
            conv_id = await create_conversation(
                authenticated_client, title=f"Test {test_case['test_id']}"
            )

            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                timeout=90.0,
            )

            parsed = parse_response(response_data)

            expected_agent = test_case.get("expected_agent", "")
            actual_agents = parsed.get("agents_used", "")
            has_error = parsed.get("error", False)

            if has_error:
                status = "FAIL"
            elif expected_agent and expected_agent in actual_agents:
                status = "PASS"
            elif actual_agents:
                status = "PARTIAL"
            else:
                status = "FAIL"

            result = TestResult(
                test_id=test_case["test_id"],
                category=test_case.get("category", ""),
                subcategory=test_case.get("subcategory", ""),
                input=test_case["input"],
                output=parsed.get("content", "")[:500],
                expected_agent=expected_agent,
                actual_agents=actual_agents,
                response_time_ms=response_time,
                user_type="authenticated",
                status=status,
                conversation_id=conv_id,
            )

            lending_borrowing_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
